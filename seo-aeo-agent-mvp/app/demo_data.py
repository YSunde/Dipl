from __future__ import annotations

DEMO_ENTITIES = [
    {"entity_id": 1, "entity_type": "folder", "name": "Кровельные материалы", "normalized_name": "кровельные материалы", "parent_entity_id": None, "seo_enabled": 1, "priority_tier": 1, "attrs_json": "{}"},
    {"entity_id": 2, "entity_type": "branch", "name": "Металлочерепица", "normalized_name": "металлочерепица", "parent_entity_id": 1, "seo_enabled": 1, "priority_tier": 1, "attrs_json": "{}"},
    {"entity_id": 3, "entity_type": "brand", "name": "Grand Line", "normalized_name": "grand line", "parent_entity_id": None, "seo_enabled": 1, "priority_tier": 1, "attrs_json": "{}"},
    {"entity_id": 4, "entity_type": "city", "name": "Вологда", "normalized_name": "вологда", "parent_entity_id": None, "seo_enabled": 1, "priority_tier": 1, "attrs_json": "{}"},
    {"entity_id": 5, "entity_type": "product", "name": "Металлочерепица Grand Line Classic", "normalized_name": "металлочерепица grand line classic", "parent_entity_id": 2, "seo_enabled": 1, "priority_tier": 2, "attrs_json": "{}"},
    {"entity_id": 6, "entity_type": "brand", "name": "Металл Профиль", "normalized_name": "металл профиль", "parent_entity_id": None, "seo_enabled": 1, "priority_tier": 2, "attrs_json": "{}"},
    {"entity_id": 7, "entity_type": "city", "name": "Череповец", "normalized_name": "череповец", "parent_entity_id": None, "seo_enabled": 1, "priority_tier": 2, "attrs_json": "{}"},
]

DEMO_RELATIONS = [
    {"left_entity_id": 1, "right_entity_id": 2, "relation_type": "folder_contains_branch"},
    {"left_entity_id": 2, "right_entity_id": 3, "relation_type": "branch_has_brand"},
    {"left_entity_id": 2, "right_entity_id": 6, "relation_type": "branch_has_brand"},
    {"left_entity_id": 2, "right_entity_id": 5, "relation_type": "branch_has_product"},
    {"left_entity_id": 2, "right_entity_id": 4, "relation_type": "branch_has_city"},
    {"left_entity_id": 2, "right_entity_id": 7, "relation_type": "branch_has_city"},
]
