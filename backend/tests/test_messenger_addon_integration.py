from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent


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


def test_compose_routes_messenger_as_separate_service():
    compose = (PROJECT / "docker-compose.yml").read_text()

    assert "messenger-backend:" in compose
    assert "app.messenger_main:app" in compose
    backend_block = compose.split("\n  backend:", 1)[1].split("\n  messenger-backend:", 1)[0]
    assert "MESSENGER_UPLOAD_DIR" not in backend_block
    assert "messenger_upload_data:/app/messenger_uploads" not in backend_block


def test_nginx_routes_messenger_before_core_api():
    nginx = (PROJECT / "nginx.conf").read_text()

    assert "set $messenger_upstream messenger-backend:8000;" in nginx
    assert nginx.index("location /api/messenger") < nginx.index("location /api {")
