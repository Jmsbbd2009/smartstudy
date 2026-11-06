from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect
from app.core import config


def test_migrations_round_trip(tmp_path, monkeypatch):
    from dataclasses import replace

    url = "sqlite:///" + str(tmp_path / "migrate.db")
    monkeypatch.setattr(config, "settings", replace(config.settings, database_url=url))
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    tables = inspect(engine).get_table_names()
    assert "reward_transactions" in tables and "device_policies" in tables and len(tables) > 30
    command.downgrade(cfg, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(cfg, "head")
    engine.dispose()
