from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .rules import COMMERCIAL_MODIFIERS, INFO_PATTERNS, SERVICE_PATTERNS, STOP_PATTERNS
from .storage import SQLiteStorage


@dataclass
class SearchUnitRecord:
    unit_type: str
    folder_entity_id: int | None
    branch_entity_id: int | None
    brand_entity_id: int | None
    city_entity_id: int | None
    canonical_slug: str
    priority_score: float


class CatalogAgent:
    def __init__(self, storage: SQLiteStorage, entities: list[dict[str, Any]], relations: list[dict[str, Any]]) -> None:
        self.storage = storage
        self.entities = entities
        self.relations = relations

    def run(self) -> None:
        self.storage.insert_entities(self.entities)
        self.storage.insert_relations(self.relations)


class SearchUnitBuilder:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def run(self) -> list[int]:
        entities = {
            row["entity_id"]: dict(row)
            for row in self.storage.fetchall("select * from entities where seo_enabled = 1")
        }
        relations = [dict(row) for row in self.storage.fetchall("select * from relations")]

        units: list[SearchUnitRecord] = []
        for row in entities.values():
            if row["entity_type"] == "branch":
                units.append(
                    SearchUnitRecord(
                        unit_type="branch",
                        folder_entity_id=row["parent_entity_id"],
                        branch_entity_id=row["entity_id"],
                        brand_entity_id=None,
                        city_entity_id=None,
                        canonical_slug=row["normalized_name"].replace(" ", "-"),
                        priority_score=100.0,
                    )
                )

        for rel in relations:
            if rel["relation_type"] == "branch_has_brand":
                branch = entities.get(rel["left_entity_id"])
                brand = entities.get(rel["right_entity_id"])
                if branch and brand:
                    units.append(
                        SearchUnitRecord(
                            unit_type="branch_brand",
                            folder_entity_id=branch["parent_entity_id"],
                            branch_entity_id=branch["entity_id"],
                            brand_entity_id=brand["entity_id"],
                            city_entity_id=None,
                            canonical_slug=f"{branch['normalized_name'].replace(' ', '-')}/{brand['normalized_name'].replace(' ', '-')}",
                            priority_score=90.0,
                        )
                    )
            if rel["relation_type"] == "branch_has_city":
                branch = entities.get(rel["left_entity_id"])
                city = entities.get(rel["right_entity_id"])
                if branch and city:
                    units.append(
                        SearchUnitRecord(
                            unit_type="branch_city",
                            folder_entity_id=branch["parent_entity_id"],
                            branch_entity_id=branch["entity_id"],
                            brand_entity_id=None,
                            city_entity_id=city["entity_id"],
                            canonical_slug=f"{branch['normalized_name'].replace(' ', '-')}/{city['normalized_name'].replace(' ', '-')}",
                            priority_score=80.0,
                        )
                    )

        self.storage.executemany(
            """
            insert into search_units (
                unit_type, folder_entity_id, branch_entity_id,
                brand_entity_id, city_entity_id, canonical_slug,
                priority_score, status
            ) values (?, ?, ?, ?, ?, ?, ?, 'active')
            """,
            [
                (
                    u.unit_type,
                    u.folder_entity_id,
                    u.branch_entity_id,
                    u.brand_entity_id,
                    u.city_entity_id,
                    u.canonical_slug,
                    u.priority_score,
                )
                for u in units
            ],
        )
        rows = self.storage.fetchall("select search_unit_id from search_units order by search_unit_id")
        return [int(r["search_unit_id"]) for r in rows]


class QueryBuilder:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def _name(self, entity_id: int | None) -> str | None:
        if entity_id is None:
            return None
        rows = self.storage.fetchall("select name from entities where entity_id = ?", (entity_id,))
        return rows[0]["name"] if rows else None

    def run(self) -> int:
        units = [dict(r) for r in self.storage.fetchall("select * from search_units")]
        created = 0
        for unit in units:
            branch_name = self._name(unit["branch_entity_id"])
            brand_name = self._name(unit["brand_entity_id"])
            city_name = self._name(unit["city_entity_id"])
            if not branch_name:
                continue
            base_parts = [branch_name]
            if brand_name:
                base_parts.append(brand_name)
            if city_name:
                base_parts.append(city_name)
            base = " ".join(base_parts)
            queries = [base]
            queries += [f"{base} {modifier}" for modifier in COMMERCIAL_MODIFIERS]
            queries += [f"{branch_name} монтаж", f"{branch_name} своими руками", f"{branch_name} для рабочего стола"]

            rows = [
                (
                    unit["search_unit_id"],
                    q,
                    q.lower().strip(),
                    "template",
                    "primary" if i == 0 else "secondary",
                )
                for i, q in enumerate(dict.fromkeys(queries))
            ]
            self.storage.executemany(
                "insert into query_candidates (search_unit_id, query_text, normalized_query, source, role) values (?, ?, ?, ?, ?)",
                rows,
            )
            created += len(rows)
        return created


class QueryFilter:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def classify(self, text: str) -> tuple[str, str, float]:
        value = text.lower()
        if any(pattern in value for pattern in STOP_PATTERNS):
            return ("rejected", "irrelevant", 0.99)
        if any(pattern in value for pattern in SERVICE_PATTERNS):
            return ("rejected", "service", 0.95)
        if any(pattern in value for pattern in INFO_PATTERNS):
            return ("rejected", "info", 0.90)
        return ("approved", "commercial", 0.93)

    def run(self) -> int:
        rows = self.storage.fetchall("select candidate_id, query_text from query_candidates")
        decisions = []
        for row in rows:
            status, intent, confidence = self.classify(row["query_text"])
            decisions.append(
                (
                    row["candidate_id"],
                    status,
                    intent,
                    f"classified by rules as {intent}",
                    confidence,
                )
            )
        self.storage.executemany(
            "insert into query_decisions (candidate_id, final_status, intent_type, reason, confidence_score) values (?, ?, ?, ?, ?)",
            decisions,
        )
        return len(decisions)


class MockWordstatClient:
    def get_frequency(self, query: str) -> int:
        digest = hashlib.md5(query.encode("utf-8")).hexdigest()
        return 20 + (int(digest[:6], 16) % 5000)


class FrequencyCollector:
    def __init__(self, storage: SQLiteStorage, client: MockWordstatClient | None = None) -> None:
        self.storage = storage
        self.client = client or MockWordstatClient()

    def run(self, month_key: int) -> int:
        rows = self.storage.fetchall(
            """
            select qc.candidate_id, qc.query_text
            from query_candidates qc
            join query_decisions qd on qd.candidate_id = qc.candidate_id
            where qd.final_status = 'approved'
            """
        )
        data = []
        for row in rows:
            frequency = self.client.get_frequency(row["query_text"])
            data.append((row["candidate_id"], "mock_wordstat", month_key, frequency))
        self.storage.executemany(
            "insert into frequencies (candidate_id, source_name, month_key, frequency_value) values (?, ?, ?, ?)",
            data,
        )
        return len(data)


class BriefAgent:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def run(self) -> int:
        units = [dict(r) for r in self.storage.fetchall("select * from search_units")]
        count = 0
        for unit in units:
            approved_queries = self.storage.fetchall(
                """
                select qc.query_text, coalesce(f.frequency_value, 0) as frequency_value
                from query_candidates qc
                join query_decisions qd on qd.candidate_id = qc.candidate_id
                left join frequencies f on f.candidate_id = qc.candidate_id
                where qc.search_unit_id = ? and qd.final_status = 'approved'
                order by frequency_value desc, qc.candidate_id asc
                limit 5
                """,
                (unit["search_unit_id"],),
            )
            if not approved_queries:
                continue
            main_query = approved_queries[0]["query_text"]
            secondary_queries = [row["query_text"] for row in approved_queries[1:]]
            brief = {
                "search_unit_id": unit["search_unit_id"],
                "unit_type": unit["unit_type"],
                "canonical_slug": unit["canonical_slug"],
                "main_query": main_query,
                "secondary_queries": secondary_queries,
                "content_blocks": ["commercial_intro", "benefits", "faq"],
                "constraints": [
                    "не использовать услуги и монтаж как основной интент",
                    "не добавлять неподтвержденные характеристики",
                ],
            }
            self.storage.save_brief(unit["search_unit_id"], brief)
            count += 1
        return count


class ContentGenerator:
    def __init__(self, storage: SQLiteStorage) -> None:
        self.storage = storage

    def run(self) -> int:
        briefs = self.storage.fetchall("select search_unit_id, brief_json from briefs")
        count = 0
        for row in briefs:
            brief = json.loads(row["brief_json"])
            main_query = brief["main_query"]
            secondary = ", ".join(brief["secondary_queries"])
            seo_text = (
                f"{main_query} — коммерческая посадка, собранная автоматически. "
                f"В тексте учитывается основной интент покупки и уточняющие запросы: {secondary}. "
                f"Контент сформирован по unit_type={brief['unit_type']} и требует редакторской проверки перед публикацией."
            )
            faq_text = (
                f"FAQ по теме '{main_query}'. "
                f"В AEO-блоке стоит раскрыть выбор, наличие, сроки поставки и различия между вариантами."
            )
            self.storage.save_content(row["search_unit_id"], "seo", seo_text, "draft")
            self.storage.save_content(row["search_unit_id"], "aeo", faq_text, "draft")
            count += 2
        return count
