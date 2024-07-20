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

PEFT
  - Not Applicable
  - LoRa ?

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

Framework
- WEB:
  - streamlit
- API:
  - fastapi

## TODO
- [ ] Set a docker environment
- [ ] Implement a vector store for PGVector
- [ ] Implement a server using FastAPI
- [ ] Implement an admin to handle prompt setting

## Discussion
- Hallucination이 생각보다 자주 발생 (없는 컬럼을 만들어서 답변)
  - temperature을 줄여야할듯
  - prompt 보완
- SQL은 비교적 잘 작성함 (fine tuning은 필요하지 않을듯)
  - 다만 type casting이나 current date 쪽에 취약함
  - prompt 보완

## Architecture
![text-to-sql.drawio.png](assets/text-to-sql.drawio.png)
