create table if not exists entities (
    entity_id integer primary key,
    entity_type text not null,
    name text not null,
    normalized_name text not null,
    parent_entity_id integer,
    seo_enabled integer not null default 1,
    priority_tier integer not null default 3,
    attrs_json text
);

create table if not exists relations (
    relation_id integer primary key autoincrement,
    left_entity_id integer not null,
    right_entity_id integer not null,
    relation_type text not null
);

create table if not exists search_units (
    search_unit_id integer primary key autoincrement,
    unit_type text not null,
    folder_entity_id integer,
    branch_entity_id integer,
    brand_entity_id integer,
    city_entity_id integer,
    canonical_slug text,
    priority_score real default 0,
    status text not null default 'active'
);

create table if not exists query_candidates (
    candidate_id integer primary key autoincrement,
    search_unit_id integer not null,
    query_text text not null,
    normalized_query text not null,
    source text not null,
    role text not null default 'primary'
);

create table if not exists query_decisions (
    decision_id integer primary key autoincrement,
    candidate_id integer not null,
    final_status text not null,
    intent_type text not null,
    reason text not null,
    confidence_score real not null
);

create table if not exists frequencies (
    freq_id integer primary key autoincrement,
    candidate_id integer not null,
    source_name text not null,
    month_key integer not null,
    frequency_value integer not null
);

create table if not exists briefs (
    brief_id integer primary key autoincrement,
    search_unit_id integer not null,
    brief_json text not null
);

create table if not exists content_versions (
    content_version_id integer primary key autoincrement,
    search_unit_id integer not null,
    content_type text not null,
    text_body text not null,
    approval_status text not null default 'draft'
);
