#!/usr/bin/env python3
"""Apply SQL migrations to the configured MySQL database.

Tracks applied migrations in ``schema_migrations``. Safe to re-run:
already-applied migrations are skipped.

Usage:
    python scripts/db_migrate.py
    python scripts/db_migrate.py --status
    python scripts/db_migrate.py --bootstrap   # run init.sql on empty DB
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INIT_SQL = REPO_ROOT / "infra" / "docker" / "mysql" / "init.sql"
MIGRATIONS_DIR = REPO_ROOT / "infra" / "docker" / "mysql" / "migrations"


def _load_database_url() -> str:
    try:
        from ai_platform_shared.config import get_settings

        return get_settings().database_url
    except Exception:
        import os

        url = os.environ.get("AI_PLATFORM_DATABASE_URL")
        if not url:
            raise SystemExit(
                "Database URL not configured. Set AI_PLATFORM_DATABASE_URL "
                "or install ai-platform-shared."
            ) from None
        return url


def _parse_mysql_url(url: str) -> dict[str, str | int]:
    # mysql+pymysql://user:pass@host:port/db
    match = re.match(
        r"mysql\+pymysql://(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:]+):(?P<port>\d+)/(?P<database>.+)",
        url,
    )
    if not match:
        raise SystemExit(f"Unsupported database URL format: {url}")
    return {
        "user": match.group("user"),
        "password": match.group("password"),
        "host": match.group("host"),
        "port": int(match.group("port")),
        "database": match.group("database"),
    }


def _connect(db: dict[str, str | int], database: str | None = None):
    import pymysql

    return pymysql.connect(
        host=db["host"],
        port=int(db["port"]),
        user=db["user"],
        password=db["password"],
        database=database or str(db["database"]),
        charset="utf8mb4",
        autocommit=False,
    )


def _split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statement = "\n".join(current).strip()
            if statement and statement != ";":
                statements.append(statement)
            current = []
    remainder = "\n".join(current).strip()
    if remainder:
        statements.append(remainder)
    return statements


def _ensure_schema_migrations(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.commit()


def _applied_versions(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def _record_migration(conn, version: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s)",
            (version,),
        )
    conn.commit()


def _table_count(conn) -> int:
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        return len(cur.fetchall())


def bootstrap(conn, db: dict[str, str | int]) -> None:
    if not INIT_SQL.exists():
        raise SystemExit(f"Bootstrap script not found: {INIT_SQL}")
    count = _table_count(conn)
    if count > 0:
        print(f"Database already has {count} tables; skipping bootstrap.")
        return
    print(f"Bootstrapping from {INIT_SQL.name} ...")
    sql = INIT_SQL.read_text(encoding="utf-8")
    sql = sql.replace("USE aiplatform;", f"USE {db['database']};")
    statements = _split_sql_statements(sql)
    with conn.cursor() as cur:
        for statement in statements:
            cur.execute(statement)
    conn.commit()
    print("Bootstrap complete.")
    print("Run pending migrations with: python scripts/db_migrate.py")


def apply_migrations(conn) -> None:
    _ensure_schema_migrations(conn)
    applied = _applied_versions(conn)
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print("No migration files found.")
        return
    for path in migration_files:
        version = path.stem
        if version in applied:
            print(f"  skip  {version} (already applied)")
            continue
        print(f"  apply {version} ...")
        sql = path.read_text(encoding="utf-8")
        db_name = conn.db.decode() if isinstance(conn.db, bytes) else conn.db
        sql = sql.replace("USE aiplatform;", f"USE {db_name};")
        statements = _split_sql_statements(sql)
        with conn.cursor() as cur:
            for statement in statements:
                cur.execute(statement)
        conn.commit()
        _record_migration(conn, version)
        print(f"  done  {version}")


def show_status(conn) -> None:
    count = _table_count(conn)
    print(f"Tables: {count}")
    try:
        _ensure_schema_migrations(conn)
        applied = sorted(_applied_versions(conn))
        print(f"Applied migrations ({len(applied)}):")
        for version in applied:
            print(f"  - {version}")
    except Exception as exc:
        print(f"Could not read schema_migrations: {exc}")
    with conn.cursor() as cur:
        cur.execute("SHOW TABLES LIKE 'provider_model_registry'")
        if cur.fetchone():
            cur.execute("DESCRIBE provider_model_registry")
            print("\nprovider_model_registry columns:")
            for row in cur.fetchall():
                print(f"  {row[0]:25} {row[1]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply AI Platform SQL migrations")
    parser.add_argument("--status", action="store_true", help="Show migration status")
    parser.add_argument(
        "--bootstrap",
        action="store_true",
        help="Run init.sql if the database has no tables",
    )
    args = parser.parse_args(argv)

    db = _parse_mysql_url(_load_database_url())
    conn = _connect(db)
    try:
        if args.status:
            show_status(conn)
            return 0
        if args.bootstrap:
            bootstrap(conn, db)
        apply_migrations(conn)
        show_status(conn)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
