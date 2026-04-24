CREATE TABLE IF NOT EXISTS data_table (
    timestamp BIGINT NOT NULL,
    light INTEGER NOT NULL,
    angle INTEGER NOT NULL
);
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
