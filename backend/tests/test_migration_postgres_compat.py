from pathlib import Path


def test_boolean_migrations_use_postgres_boolean_defaults():
    migration_dir = Path(__file__).resolve().parents[1] / "alembic" / "versions"
    offenders = []
    for path in migration_dir.glob("*.py"):
        text = path.read_text()
        if "sa.Boolean()" not in text:
            continue
        if 'server_default=sa.text("0")' in text or 'server_default=sa.text("1")' in text:
            offenders.append(path.name)

    assert offenders == []
