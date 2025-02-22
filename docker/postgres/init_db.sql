-- temporal
CREATE USER temporal WITH ENCRYPTED PASSWORD 'temporal';
CREATE DATABASE temporal WITH OWNER temporal;
ALTER USER temporal WITH CREATEDB;

-- pgvector
CREATE SCHEMA vectordb;
SET search_path TO vectordb;

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS ddl_collection (
	ID SERIAL PRIMARY KEY,
	TABLE_NAME VARCHAR(128) NULL,
	DDL_CONTENT VARCHAR NOT NULL,
	EMBEDDING VECTOR(768)
);

CREATE INDEX IF NOT EXISTS ddl_collection_index ON ddl_collection USING hnsw (embedding vector_cosine_ops);