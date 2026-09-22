CREATE TABLE IF NOT EXISTS source_contents (
  doc_id TEXT PRIMARY KEY REFERENCES sources(doc_id),
  content BLOB NOT NULL,
  extracted_text TEXT NOT NULL DEFAULT '',
  filename TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS case_results (
  case_id TEXT PRIMARY KEY REFERENCES cases(case_id),
  payload_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS case_jobs (
  case_id TEXT PRIMARY KEY REFERENCES cases(case_id),
  actor TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'queued',
  lease_until TEXT
);
