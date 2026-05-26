from pathlib import Path
import os
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


def require_project_file(name: str) -> Path:
    path = PROJECT / name
    if not path.exists():
        pytest.skip(f"{name} is not present in the backend image")
    return path


def test_core_app_does_not_mount_messenger_routes():
    main_source = (ROOT / "app/main.py").read_text()

    assert "messenger" not in main_source
    assert "/messenger" not in main_source


def test_dedicated_messenger_entrypoint_exists_without_ai_imports():
    source = (ROOT / "app/messenger_main.py").read_text()

    assert "messenger.router" in source
    forbidden = [
        "qdrant",
        "embedding",
        "llm",
        "rag",
        "documents.router",
        "chat.router",
    ]
    assert not any(term in source.lower() for term in forbidden)


def test_dedicated_messenger_entrypoint_registers_model_relationships():
    env = os.environ.copy()
    env.update(
        {
            "JWT_SECRET": "test-secret",
            "SUPER_ADMIN_PASSWORD": "test-password",
            "DATABASE_URL": "sqlite://",
            "MESSENGER_DATABASE_URL": "sqlite://",
        }
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from sqlalchemy.orm import configure_mappers; "
                "import app.messenger_main; "
                "configure_mappers()"
            ),
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout


def test_compose_routes_messenger_as_separate_service():
    compose = require_project_file("docker-compose.yml").read_text()

    assert "messenger-backend:" in compose
    assert "app.messenger_main:app" in compose
    backend_block = compose.split("\n  backend:", 1)[1].split("\n  messenger-backend:", 1)[0]
    assert "MESSENGER_UPLOAD_DIR" not in backend_block
    assert "messenger_upload_data:/app/messenger_uploads" not in backend_block


def test_nginx_routes_messenger_before_core_api():
    nginx = require_project_file("nginx.conf").read_text()

    assert "set $messenger_upstream messenger-backend:8000;" in nginx
    assert nginx.index("location /api/messenger") < nginx.index("location /api {")
