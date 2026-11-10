"""Integration test: execute the actual migration in a rollback-only schema."""

import importlib
import uuid

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.db import engine

migration = importlib.import_module(
    "app.alembic.versions.b4a8c2319e02_add_nullable_user_role"
)


def test_upgrade_preserves_users_and_downgrade_is_reversible(monkeypatch):
    schema = f"rbac_migration_{uuid.uuid4().hex}"
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
            connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
            connection.execute(
                text(
                    'CREATE TABLE "user" (id integer PRIMARY KEY, is_superuser boolean NOT NULL)'
                )
            )
            connection.execute(text('INSERT INTO "user" VALUES (1, true), (2, false)'))
            monkeypatch.setattr(
                migration, "op", Operations(MigrationContext.configure(connection))
            )
            migration.upgrade()
            assert connection.execute(
                text('SELECT id, is_superuser, role FROM "user" ORDER BY id')
            ).all() == [(1, True, None), (2, False, None)]
            column = next(
                c
                for c in inspect(connection).get_columns("user", schema=schema)
                if c["name"] == "role"
            )
            assert column["nullable"] is True
            assert column["default"] is None
            for role in ("manager", "member", None):
                connection.execute(
                    text('UPDATE "user" SET role = :role WHERE id = 2'), {"role": role}
                )
            with connection.begin_nested() as savepoint:
                with pytest.raises(IntegrityError):
                    connection.execute(
                        text("UPDATE \"user\" SET role = 'admin' WHERE id = 2")
                    )
                savepoint.rollback()
            migration.downgrade()
            assert {
                c["name"]
                for c in inspect(connection).get_columns("user", schema=schema)
            } == {"id", "is_superuser"}
            assert connection.execute(
                text('SELECT * FROM "user" ORDER BY id')
            ).all() == [(1, True), (2, False)]
            migration.upgrade()
            assert connection.execute(text('SELECT role FROM "user"')).all() == [
                (None,),
                (None,),
            ]
        finally:
            transaction.rollback()
