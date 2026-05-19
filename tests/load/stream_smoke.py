import asyncio
import json
import os
import time
from datetime import timedelta

import httpx
from sqlmodel import Session, select

import app.main  # Registers SQLModel relationships.
from app.core.security import create_access_token, get_password_hash
from app.db.session import engine
from app.models.bank import Bank
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User


CONCURRENCY = int(os.getenv("BANKAI_STREAM_CONCURRENCY", "20"))
BASE_URL = os.getenv("BANKAI_BASE_URL", "http://127.0.0.1:8000")
USER_PREFIX = os.getenv("BANKAI_LOAD_USER_PREFIX", "stream-load-")
PROMPT = os.getenv(
    "BANKAI_STREAM_PROMPT",
    "Draft a concise customer care response for a failed transaction complaint. Keep it under six sentences.",
)


async def one(index: int, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    started = time.perf_counter()
    async with httpx.AsyncClient(timeout=220.0) as client:
        session_resp = await client.post(
            f"{BASE_URL}/api/chat/sessions",
            json={"title": f"Stream user {index}"},
            headers=headers,
        )
        if session_resp.status_code != 200:
            return {
                "i": index,
                "phase": "session",
                "status": session_resp.status_code,
                "seconds": round(time.perf_counter() - started, 2),
                "body": session_resp.text[:180],
            }

        session_id = session_resp.json()["id"]
        stream_resp = await client.post(
            f"{BASE_URL}/api/chat/sessions/{session_id}/stream",
            json={
                "message": PROMPT,
                "language": "en",
                "mode": "draft",
                "active_document_ids": [],
            },
            headers=headers,
        )
        elapsed = time.perf_counter() - started
        body = stream_resp.text
        timeout_markers = (
            "AI engine is busy",
            "Error connecting to AI engine",
            "AI engine returned error",
        )
        answer_failed = any(marker in body for marker in timeout_markers)
        return {
            "i": index,
            "phase": "stream",
            "status": stream_resp.status_code,
            "seconds": round(elapsed, 2),
            "bytes": len(stream_resp.content),
            "answer_failed": answer_failed,
        }


def ensure_users_and_tokens() -> list[str]:
    tokens = []
    with Session(engine) as db:
        bank = db.exec(select(Bank).order_by(Bank.id)).first()
        if not bank:
            raise RuntimeError("No bank found")

        for index in range(CONCURRENCY):
            email = f"{USER_PREFIX}{index}@bankai.local"
            user = db.exec(select(User).where(User.email == email)).first()
            if not user:
                user = User(
                    email=email,
                    name=f"Stream Load User {index}",
                    password_hash=get_password_hash("load-test-disabled"),
                    role="staff_user",
                    department="General",
                    bank_id=bank.id,
                    is_active=True,
                )
            user.is_active = True
            db.add(user)
            db.commit()
            db.refresh(user)
            tokens.append(create_access_token(user.id, expires_delta=timedelta(hours=2)))
    return tokens


def cleanup_load_data() -> None:
    with Session(engine) as db:
        users = db.exec(select(User).where(User.email.startswith(USER_PREFIX))).all()
        user_ids = [user.id for user in users if user.id is not None]
        if not user_ids:
            return
        messages = db.exec(select(ChatMessage).where(ChatMessage.user_id.in_(user_ids))).all()
        sessions = db.exec(select(ChatSession).where(ChatSession.user_id.in_(user_ids))).all()
        for message in messages:
            db.delete(message)
        for session in sessions:
            db.delete(session)
        for user in users:
            user.is_active = False
            db.add(user)
        db.commit()
        print(json.dumps({
            "cleanup": True,
            "disabled_users": len(users),
            "deleted_messages": len(messages),
            "deleted_sessions": len(sessions),
        }))


async def main() -> None:
    tokens = ensure_users_and_tokens()
    results = await asyncio.gather(*(one(index, tokens[index]) for index in range(CONCURRENCY)))
    for result in results:
        print(json.dumps(result), flush=True)

    ok = [
        result
        for result in results
        if result.get("status") == 200
        and result.get("phase") == "stream"
        and not result.get("answer_failed")
    ]
    fail = [result for result in results if result not in ok]
    latencies = sorted(result["seconds"] for result in ok)
    if latencies:
        summary = {
            "total": len(results),
            "ok": len(ok),
            "fail": len(fail),
            "p50_seconds": latencies[len(latencies) // 2],
            "p95_seconds": latencies[max(0, int(len(latencies) * 0.95) - 1)],
            "max_seconds": latencies[-1],
        }
    else:
        summary = {"total": len(results), "ok": 0, "fail": len(fail), "failures": fail[:5]}
    print(json.dumps(summary), flush=True)

    if os.getenv("BANKAI_LOAD_CLEANUP", "1") == "1":
        cleanup_load_data()


if __name__ == "__main__":
    asyncio.run(main())
