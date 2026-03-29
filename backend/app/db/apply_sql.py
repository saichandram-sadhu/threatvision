"""Apply raw SQL migration files (split statements for asyncpg)."""

from __future__ import annotations

import re
from pathlib import Path


def _strip_sql_comments(sql: str) -> str:
    out: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        out.append(line)
    return "\n".join(out)


def split_sql_statements(sql: str) -> list[str]:
    """Split DDL into statements safe for asyncpg.execute (no function bodies)."""
    cleaned = _strip_sql_comments(sql)
    parts = re.split(r";\s*\n", cleaned)
    statements: list[str] = []
    for block in parts:
        s = block.strip()
        if not s:
            continue
        if not s.endswith(";"):
            s = s + ";"
        statements.append(s)
    return statements


def load_migration_statements(name: str) -> list[str]:
    path = Path(__file__).resolve().parent / "migrations" / name
    return split_sql_statements(path.read_text(encoding="utf-8"))


def load_all_migration_statements() -> list[str]:
    """Apply every `NNN_*.sql` file in order."""
    root = Path(__file__).resolve().parent / "migrations"
    paths = sorted(root.glob("[0-9][0-9][0-9]_*.sql"))
    statements: list[str] = []
    for path in paths:
        statements.extend(split_sql_statements(path.read_text(encoding="utf-8")))
    return statements
