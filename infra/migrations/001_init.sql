CREATE TABLE cases (
  case_id TEXT PRIMARY KEY, trace_id TEXT NOT NULL,
  channel TEXT NOT NULL, sender TEXT, subject TEXT,
  body_raw TEXT, body_clean TEXT, body_masked TEXT,
  language TEXT, received_at TEXT, created_at TEXT NOT NULL,
  status TEXT NOT NULL, corpus_version TEXT NOT NULL,
  injection_suspected INTEGER DEFAULT 0,
  send_deadline TEXT,          -- ISO UTC: thời điểm hết hạn 60s PENDING_SEND; NULL nếu chưa/không áp dụng
  parent_case_id TEXT          -- FK tự tham chiếu: Correction Email trỏ về case gốc đã SENT
);

CREATE TABLE extractions (
  case_id TEXT PRIMARY KEY REFERENCES cases, payload_json TEXT NOT NULL,
  llm_error TEXT, latency_ms INTEGER, prompt_hash TEXT, created_at TEXT
);

CREATE TABLE decisions (
  decision_id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases,
  decision TEXT NOT NULL, escalation_type TEXT, rule_id TEXT NOT NULL,
  reason TEXT NOT NULL, evidence_ids_json TEXT, evidence_status TEXT,
  corpus_version TEXT NOT NULL, is_override INTEGER DEFAULT 0,
  superseded_by TEXT, created_at TEXT NOT NULL
);

CREATE TABLE drafts (
  draft_id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases,
  kind TEXT NOT NULL,            -- 'auto' | 'resume' | 'partial' | 'correction'
  subject TEXT, body TEXT, citations_json TEXT,
  grounded INTEGER, guard_failures_json TEXT, created_at TEXT
);

CREATE TABLE escalations (
  case_id TEXT PRIMARY KEY REFERENCES cases, escalation_type TEXT NOT NULL,
  summary TEXT, facts_json TEXT, basis_json TEXT,
  question TEXT, options_json TEXT, created_at TEXT
);

CREATE TABLE human_decisions (
  id TEXT PRIMARY KEY, case_id TEXT REFERENCES cases,
  actor TEXT NOT NULL, choice TEXT NOT NULL, reason TEXT NOT NULL,
  shown_at TEXT, decided_at TEXT, review_seconds REAL
);

CREATE TABLE sources (
  doc_id TEXT PRIMARY KEY, title TEXT, issuer TEXT,
  source_url TEXT, source_kind TEXT, sha256 TEXT UNIQUE,
  fetched_at TEXT,             -- thời điểm tải về (K1); NULL nếu nạp bằng cách dán text
  is_synthetic INTEGER DEFAULT 0,  -- 1 = dữ liệu giả lập; Slide 4 phải phân định rõ; seed docs mặc định là 1
  published_at TEXT, effective_from TEXT, effective_to TEXT,
  applies_to_json TEXT, cohorts_json TEXT, domains_json TEXT,
  supersedes_json TEXT, superseded_by TEXT, superseded_at TEXT,
  transitional_clause INTEGER DEFAULT 0,
  status TEXT NOT NULL, content_hash TEXT,
  created_at TEXT, activated_at TEXT, activated_by TEXT
);

CREATE TABLE chunks (
  chunk_id TEXT PRIMARY KEY, doc_id TEXT REFERENCES sources,
  article_no TEXT, clause_no TEXT, breadcrumb TEXT NOT NULL,
  text TEXT NOT NULL, domain TEXT NOT NULL,
  label TEXT NOT NULL DEFAULT 'human_only',
  conflict_flag INTEGER DEFAULT 0, conflict_with TEXT,
  ord INTEGER, token_count INTEGER
);

CREATE TABLE corpus_versions (
  corpus_version TEXT PRIMARY KEY, created_at TEXT,
  actor TEXT, note TEXT, active_doc_ids_json TEXT
);

CREATE TABLE audit_events (
  event_id TEXT PRIMARY KEY, case_id TEXT, ts TEXT NOT NULL,
  actor TEXT NOT NULL, action TEXT NOT NULL, rule_id TEXT,
  input_ref TEXT, output_ref TEXT, reason TEXT,
  sources_json TEXT, corpus_version TEXT
);
CREATE INDEX idx_audit_case ON audit_events(case_id);
CREATE INDEX idx_audit_ts ON audit_events(ts);

CREATE TABLE step_latencies (
  case_id TEXT, step TEXT, ms INTEGER, ok INTEGER, ts TEXT
);

CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT, actor TEXT);
-- settings: automation_paused = "0"|"1", current_corpus_version = "cv_xxx"
