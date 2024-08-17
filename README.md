# sql-helper
SQL helper using LLM and RAG


## Plans for development

LLM:
- platform:
  - OpenAI ChatGPT
  - Meta Llama 3 ?
  - Cohere Command R+ ?
- self serve
  - vLLM ?

RAG:
- database:
  - chromadb (standalone)
  - postgres pgvector
  - duckdb vss extension ?
  - GraphRAG ?
- model:
  - sentence transformers:
    - all-MiniLM-L6-v2
  - OpenAI
    - text-embedding series ? 
- index (VSS algorithm):
  - HNSW
  - IVF-PQ ?

## TODO
- [ ] Implement standalone application with ChromaDB
- [ ] Implement CRUD with an admin page
- [ ] Set a docker environment
- [ ] Implement a vector store for PGVector

## Architecture
![text-to-sql.drawio.png](assets/text-to-sql.drawio.png)
