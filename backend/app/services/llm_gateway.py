import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from ..core.config import settings


@dataclass(frozen=True)
class ModelProfile:
    key: str
    api_base: str
    model: str
    api_key: str
    max_tokens: int
    timeout_seconds: float


@dataclass(frozen=True)
class ModelLease:
    profile: ModelProfile
    queued_ahead: int


class _AdmissionGate:
    def __init__(self, limit: int):
        self._limit = max(1, limit)
        self._semaphore = asyncio.Semaphore(self._limit)
        self._lock = asyncio.Lock()
        self._active = 0
        self._waiting = 0

    async def snapshot(self) -> dict:
        async with self._lock:
            return {
                "active": self._active,
                "waiting": self._waiting,
                "limit": self._limit,
            }

    async def acquire(self, timeout_seconds: float) -> int:
        async with self._lock:
            queued_ahead = self._waiting
            self._waiting += 1

        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=timeout_seconds)
        except Exception:
            async with self._lock:
                self._waiting = max(0, self._waiting - 1)
            raise

        async with self._lock:
            self._waiting = max(0, self._waiting - 1)
            self._active += 1
        return queued_ahead

    async def release(self) -> None:
        async with self._lock:
            self._active = max(0, self._active - 1)
        self._semaphore.release()


class _RedisAdmissionGate:
    _ACQUIRE_SCRIPT = """
    redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', ARGV[1])
    redis.call('ZREMRANGEBYSCORE', KEYS[2], '-inf', ARGV[2])
    redis.call('ZADD', KEYS[2], ARGV[3], ARGV[5])
    redis.call('EXPIRE', KEYS[1], ARGV[6])
    redis.call('EXPIRE', KEYS[2], ARGV[6])
    local rank = redis.call('ZRANK', KEYS[2], ARGV[5])
    local active = redis.call('ZCARD', KEYS[1])
    if active < tonumber(ARGV[4]) and rank == 0 then
        redis.call('ZREM', KEYS[2], ARGV[5])
        redis.call('ZADD', KEYS[1], ARGV[7], ARGV[5])
        return {1, 0}
    end
    if rank == false then
        rank = 0
    end
    return {0, rank}
    """

    def __init__(self, name: str, limit: int):
        self._name = name
        self._limit = max(1, limit)
        self._active_key = f"llm:gate:{name}:active"
        self._waiting_key = f"llm:gate:{name}:waiting"

    async def snapshot(self) -> dict:
        redis = await _redis_client()
        if redis is None:
            raise RuntimeError("Redis unavailable")

        now = time.time()
        await redis.zremrangebyscore(self._active_key, "-inf", now)
        await redis.zremrangebyscore(
            self._waiting_key,
            "-inf",
            now - settings.LLM_QUEUE_STALE_SECONDS,
        )
        active, waiting = await redis.zcard(self._active_key), await redis.zcard(self._waiting_key)
        return {"active": int(active), "waiting": int(waiting), "limit": self._limit}

    async def acquire(self, timeout_seconds: float) -> tuple[str, int]:
        redis = await _redis_client()
        if redis is None:
            raise RuntimeError("Redis unavailable")

        token = uuid.uuid4().hex
        started = time.monotonic()
        queued_ahead = 0
        ttl_seconds = str(max(60, int(timeout_seconds * 3)))
        try:
            while True:
                now = time.time()
                acquired, queued_ahead = await redis.eval(
                    self._ACQUIRE_SCRIPT,
                    2,
                    self._active_key,
                    self._waiting_key,
                    now,
                    now - settings.LLM_QUEUE_STALE_SECONDS,
                    now,
                    self._limit,
                    token,
                    ttl_seconds,
                    now + timeout_seconds,
                )
                if int(acquired) == 1:
                    return token, int(queued_ahead)
                if time.monotonic() - started >= timeout_seconds:
                    raise asyncio.TimeoutError()
                await asyncio.sleep(0.25)
        except Exception:
            await redis.zrem(self._waiting_key, token)
            raise

    async def release(self, token: str) -> None:
        redis = await _redis_client()
        if redis is not None:
            await redis.zrem(self._active_key, token)


_redis = None
_redis_checked = False
_redis_lock = asyncio.Lock()


async def _redis_client():
    global _redis, _redis_checked
    if _redis_checked:
        return _redis

    async with _redis_lock:
        if _redis_checked:
            return _redis
        try:
            import redis.asyncio as redis

            client = redis.from_url(settings.REDIS_URL, decode_responses=True)
            await client.ping()
            _redis = client
        except Exception:
            _redis = None
        _redis_checked = True
        return _redis


_model_gates = {
    "fast": _AdmissionGate(settings.LLM_A_MAX_CONCURRENCY),
    "deep": _AdmissionGate(settings.LLM_C_MAX_CONCURRENCY),
}
_redis_model_gates = {
    "fast": _RedisAdmissionGate("model:fast", settings.LLM_A_MAX_CONCURRENCY),
    "deep": _RedisAdmissionGate("model:deep", settings.LLM_C_MAX_CONCURRENCY),
}
_user_gates: dict[str, _AdmissionGate] = {}
_redis_user_gates: dict[str, _RedisAdmissionGate] = {}
_user_gates_lock = asyncio.Lock()


def _user_limit(role: str | None) -> int:
    if role in {"super_admin", "bank_admin", "compliance_user"}:
        return settings.LLM_ADMIN_MAX_CONCURRENCY
    return settings.LLM_USER_MAX_CONCURRENCY


async def _user_gate(user_id: int, role: str | None) -> _AdmissionGate:
    key = f"{role or 'user'}:{user_id}"
    async with _user_gates_lock:
        gate = _user_gates.get(key)
        if gate is None:
            gate = _AdmissionGate(_user_limit(role))
            _user_gates[key] = gate
        return gate


async def _redis_user_gate(user_id: int, role: str | None) -> _RedisAdmissionGate:
    key = f"{role or 'user'}:{user_id}"
    safe_key = key.replace(":", "_")
    async with _user_gates_lock:
        gate = _redis_user_gates.get(key)
        if gate is None:
            gate = _RedisAdmissionGate(f"user:{safe_key}", _user_limit(role))
            _redis_user_gates[key] = gate
        return gate


def resolve_model_profile(model_name: str | None = None) -> ModelProfile:
    requested = (model_name or "").strip().lower()
    if requested in {"gemma-4-26b-4bit", "gemma-4-26b", "deep", "analysis"}:
        return ModelProfile(
            key="deep",
            api_base=settings.LLM_C_API_BASE,
            model=settings.LLM_C_MODEL,
            api_key=settings.LLM_C_API_KEY,
            max_tokens=settings.LLM_DEEP_MAX_TOKENS,
            timeout_seconds=420.0,
        )

    return ModelProfile(
        key="fast",
        api_base=settings.LLM_A_API_BASE,
        model=settings.LLM_A_MODEL,
        api_key=settings.LLM_A_API_KEY,
        max_tokens=settings.LLM_FAST_MAX_TOKENS,
        timeout_seconds=300.0,
    )


async def model_status() -> dict:
    if await _redis_client() is not None:
        try:
            return {name: await gate.snapshot() for name, gate in _redis_model_gates.items()}
        except Exception:
            pass
    return {name: await gate.snapshot() for name, gate in _model_gates.items()}


@asynccontextmanager
async def reserve_model(
    *,
    user_id: int,
    role: str | None,
    model_name: str | None = None,
) -> AsyncIterator[ModelLease]:
    profile = resolve_model_profile(model_name)
    if await _redis_client() is not None:
        redis_user_gate = await _redis_user_gate(user_id, role)
        redis_model_gate = _redis_model_gates[profile.key]
        user_token = None
        model_token = None
        try:
            user_token, _ = await redis_user_gate.acquire(settings.LLM_QUEUE_TIMEOUT_SECONDS)
            model_token, queued_ahead = await redis_model_gate.acquire(settings.LLM_QUEUE_TIMEOUT_SECONDS)
            yield ModelLease(profile=profile, queued_ahead=queued_ahead)
        finally:
            if model_token is not None:
                await redis_model_gate.release(model_token)
            if user_token is not None:
                await redis_user_gate.release(user_token)
        return

    user_gate = await _user_gate(user_id, role)
    model_gate = _model_gates[profile.key]
    await user_gate.acquire(settings.LLM_QUEUE_TIMEOUT_SECONDS)
    model_acquired = False
    try:
        queued_ahead = await model_gate.acquire(settings.LLM_QUEUE_TIMEOUT_SECONDS)
        model_acquired = True
        yield ModelLease(profile=profile, queued_ahead=queued_ahead)
    finally:
        if model_acquired:
            await model_gate.release()
        await user_gate.release()
