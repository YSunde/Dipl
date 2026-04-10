from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable


class SQLiteStorage:
    def __init__(self, db_path: str, schema_path: str) -> None:
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        schema_sql = self.schema_path.read_text(encoding="utf-8")
        self.conn.executescript(schema_sql)
        self.conn.commit()

    def insert_entities(self, rows: Iterable[dict[str, Any]]) -> None:
        self.conn.executemany(
            """
            insert or replace into entities (
                entity_id, entity_type, name, normalized_name,
                parent_entity_id, seo_enabled, priority_tier, attrs_json
            ) values (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["entity_id"],
                    row["entity_type"],
                    row["name"],
                    row["normalized_name"],
                    row["parent_entity_id"],
                    row["seo_enabled"],
                    row["priority_tier"],
                    row["attrs_json"],
                )
                for row in rows
            ],
        )
        self.conn.commit()

    def insert_relations(self, rows: Iterable[dict[str, Any]]) -> None:
        self.conn.executemany(
            "insert into relations (left_entity_id, right_entity_id, relation_type) values (?, ?, ?)",
            [(row["left_entity_id"], row["right_entity_id"], row["relation_type"]) for row in rows],
        )
        self.conn.commit()

    def fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        return list(self.conn.execute(query, params).fetchall())

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        cur = self.conn.execute(query, params)
        self.conn.commit()
        return cur

    def executemany(self, query: str, rows: Iterable[tuple[Any, ...]]) -> None:
        self.conn.executemany(query, list(rows))
        self.conn.commit()

    def save_brief(self, search_unit_id: int, brief: dict[str, Any]) -> None:
        self.execute(
            "insert into briefs (search_unit_id, brief_json) values (?, ?)",
            (search_unit_id, json.dumps(brief, ensure_ascii=False)),
        )

    def save_content(self, search_unit_id: int, content_type: str, text_body: str, approval_status: str = "draft") -> None:
        self.execute(
            "insert into content_versions (search_unit_id, content_type, text_body, approval_status) values (?, ?, ?, ?)",
            (search_unit_id, content_type, text_body, approval_status),
        )
