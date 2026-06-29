CREATE TABLE IF NOT EXISTS dataset_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset_name TEXT NOT NULL,
    version TEXT,
    file_name TEXT,
    file_path TEXT,
    status TEXT,
    record_count INTEGER,
    parsed_at TEXT,
    updated_at TEXT,
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS as_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    asn_a TEXT NOT NULL,
    asn_b TEXT NOT NULL,
    relationship TEXT NOT NULL,
    source TEXT,
    UNIQUE(version, asn_a, asn_b)
);

CREATE INDEX IF NOT EXISTS idx_asrel_version_ab ON as_relationships(version, asn_a, asn_b);

CREATE TABLE IF NOT EXISTS as_orgs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    asn TEXT NOT NULL,
    as_name TEXT,
    org_id TEXT,
    org_name TEXT,
    country TEXT,
    UNIQUE(version, asn)
);

CREATE INDEX IF NOT EXISTS idx_as_orgs_version_asn ON as_orgs(version, asn);

CREATE TABLE IF NOT EXISTS organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL,
    org_id TEXT NOT NULL,
    org_name TEXT,
    country TEXT,
    source TEXT,
    UNIQUE(version, org_id)
);

CREATE TABLE IF NOT EXISTS asrank_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key TEXT NOT NULL UNIQUE,
    response_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL UNIQUE,
    report_type TEXT NOT NULL,
    input_json TEXT,
    result_json TEXT,
    markdown_report TEXT,
    created_at TEXT NOT NULL
);