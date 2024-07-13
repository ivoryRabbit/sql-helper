# sql-helper
SQL helper using LLM and RAG


## Plans for development

LLM:
- model:
  - OpenAI ChatGPT ?
  - Meta Llama 3
  - Cohere Command R+ ?

PEFT
  - Not Applicable
  - LoRa ?

RAG:
- database:
  - postgres pgvector
  - duckdb vss extension ?
  - chromadb using sqlite on the backend ?
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
  - mesop ?
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
  - assistant에 최대한 document를 꼼꼼하게 작성하여 넘겨야할듯
    - 하지만 프롬프트가 길면 오히려 안좋다는 연구결과도 있음
  - chain of thought
- SQL은 매우 잘 작성함 (fine tuning은 필요하지 않을듯)