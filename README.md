# sql-helper
SQL helper using LLM


## Plans for development

LLM:
- model:
  - Llama 3
  - OpenAI API ?

RAG:
- database:
  - postgres pgvector
  - duckdb vss extension ?
  - chromadb using sqlite or duckdb on the backend ?
  - GraphRAG ?
- model:
  - sentence transformers:
    - all-MiniLM-L6-v2
    - text-embedding-ada-002 ?
    - text-embedding-3-small ? 
- index:
  - HNSW
  - IVF-PQ ?

Framework
- WEB:
  - streamlit
  - mesop ?
- API:
  - fastapi

## TODO
- [ ] Set docker environment