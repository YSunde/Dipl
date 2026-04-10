from __future__ import annotations

import json
from pathlib import Path

from .agents import (
    BriefAgent,
    CatalogAgent,
    ContentGenerator,
    FrequencyCollector,
    QueryBuilder,
    QueryFilter,
    SearchUnitBuilder,
)
from .demo_data import DEMO_ENTITIES, DEMO_RELATIONS
from .storage import SQLiteStorage


class SeoAeoOrchestrator:
    def __init__(self, project_root: str) -> None:
        self.project_root = Path(project_root)
        self.storage = SQLiteStorage(
            db_path=str(self.project_root / "seo_agent.db"),
            schema_path=str(self.project_root / "schema.sql"),
        )

    def run(self) -> dict:
        out_dir = self.project_root / "out"
        out_dir.mkdir(exist_ok=True)

        self.storage.init_schema()
        CatalogAgent(self.storage, DEMO_ENTITIES, DEMO_RELATIONS).run()
        unit_ids = SearchUnitBuilder(self.storage).run()
        created_candidates = QueryBuilder(self.storage).run()
        decisions = QueryFilter(self.storage).run()
        frequencies = FrequencyCollector(self.storage).run(month_key=202604)
        briefs = BriefAgent(self.storage).run()
        generated_texts = ContentGenerator(self.storage).run()

        summary = {
            "search_units": len(unit_ids),
            "query_candidates": created_candidates,
            "decisions": decisions,
            "frequencies": frequencies,
            "briefs": briefs,
            "generated_texts": generated_texts,
        }

        content_rows = self.storage.fetchall(
            "select search_unit_id, content_type, text_body, approval_status from content_versions order by search_unit_id, content_type"
        )
        generated_content = [dict(row) for row in content_rows]

        (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "generated_content.json").write_text(json.dumps(generated_content, ensure_ascii=False, indent=2), encoding="utf-8")
        return summary
