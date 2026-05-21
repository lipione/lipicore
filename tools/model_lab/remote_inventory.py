#!/usr/bin/env python3
"""Read-only remote inventory helper for LipiCore model servers."""

from __future__ import annotations

import argparse
import shlex
import subprocess
from pathlib import Path


DEFAULT_MODEL_ROOTS = ["/data/models", "/models", "/root/.cache/huggingface", "/home/ubuntu/.cache/huggingface"]
DEFAULT_MODEL_PORTS = [8001, 8002, 8003, 8004, 8005, 30000]


def build_inventory_script(
    *,
    model_roots: list[str] | None = None,
    model_ports: list[int] | None = None,
) -> str:
    roots = " ".join(shlex.quote(root) for root in (model_roots or DEFAULT_MODEL_ROOTS))
    ports = " ".join(str(port) for port in (model_ports or DEFAULT_MODEL_PORTS))
    return f"""#!/usr/bin/env bash
set -u
echo "## host"
hostname || true
uname -a || true
date -Is || true

echo "## os"
if [ -f /etc/os-release ]; then cat /etc/os-release; fi

echo "## cpu_memory_disk"
nproc || true
free -h || true
df -h / /data /data/models 2>/dev/null || true

echo "## gpu"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi || true
  nvidia-smi --query-gpu=index,name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv,noheader,nounits || true
else
  echo "nvidia-smi not found"
fi

echo "## docker"
if command -v docker >/dev/null 2>&1; then
  docker ps --format 'table {{{{.Names}}}}\\t{{{{.Image}}}}\\t{{{{.Status}}}}\\t{{{{.Ports}}}}' || true
  docker images --format 'table {{{{.Repository}}}}\\t{{{{.Tag}}}}\\t{{{{.Size}}}}' | head -80 || true
else
  echo "docker not found"
fi

echo "## model_dirs"
find {roots} -maxdepth 4 -type d 2>/dev/null | sort | head -500 || true

echo "## model_files"
find {roots} -maxdepth 5 -type f \\( -name '*.safetensors' -o -name '*.gguf' -o -name 'config.json' -o -name 'tokenizer.json' \\) 2>/dev/null | sort | head -500 || true

echo "## openai_compatible_model_endpoints"
for port in {ports}; do
  echo "-- port $port --"
  curl -sS --max-time 5 "http://127.0.0.1:$port/v1/models" || true
  echo
done
"""


def build_ssh_command(*, host: str, user: str | None = None, port: int = 22) -> list[str]:
    target = f"{user}@{host}" if user else host
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-p",
        str(port),
        target,
        "bash -s",
    ]


def run_remote_inventory(*, host: str, user: str | None, port: int, output: str | Path) -> int:
    script = build_inventory_script()
    command = build_ssh_command(host=host, user=user, port=port)
    completed = subprocess.run(command, input=script, text=True, capture_output=True, check=False)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(completed.stdout)
    if completed.stderr:
        output_path.with_suffix(output_path.suffix + ".stderr").write_text(completed.stderr)
    return completed.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description="Run read-only inventory on a LipiCore model server over SSH.")
    parser.add_argument("--host", required=True)
    parser.add_argument("--user")
    parser.add_argument("--port", type=int, default=22)
    parser.add_argument("--output", default="reports/model-lab/remote_inventory.txt")
    args = parser.parse_args()
    raise SystemExit(run_remote_inventory(host=args.host, user=args.user, port=args.port, output=args.output))


if __name__ == "__main__":
    main()
