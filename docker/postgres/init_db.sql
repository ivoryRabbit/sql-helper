CREATE SCHEMA vector_store;

SET search_path TO vector_store;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ddl_collection (
	ID SERIAL PRIMARY KEY,
	DOCUMENT VARCHAR NOT NULL,
	QUESTION VARCHAR(256) NULL,
	EMBEDDING VECTOR(768)
);

CREATE INDEX IF NOT EXISTS ddl_collection_index ON ddl_collection USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS doc_collection (
	ID SERIAL PRIMARY KEY,
	DOCUMENT VARCHAR NOT NULL,
	QUESTION VARCHAR(256) NULL,
	EMBEDDING VECTOR(768)
);

CREATE INDEX IF NOT EXISTS doc_collection_index ON doc_collection USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS sql_collection (
	ID SERIAL PRIMARY KEY,
	DOCUMENT VARCHAR NOT NULL,
	QUESTION VARCHAR(256) NULL,
	EMBEDDING VECTOR(768)
);

CREATE INDEX IF NOT EXISTS sql_collection_index ON sql_collection USING hnsw (embedding vector_cosine_ops);