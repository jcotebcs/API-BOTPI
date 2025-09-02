-- Migration for provenance & rankings
ALTER TABLE apis ADD COLUMN spec_url TEXT;
ALTER TABLE apis ADD COLUMN spec_hash TEXT;
ALTER TABLE apis ADD COLUMN quality_score REAL DEFAULT 0;
CREATE TABLE IF NOT EXISTS providers (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE, website TEXT, status_page_url TEXT
);
ALTER TABLE apis ADD COLUMN provider_id INTEGER REFERENCES providers(id);
