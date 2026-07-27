"""AI package.

Houses the Intent Engine, LLM tool-calling orchestration, semantic search
(Sentence Transformers + FAISS), recommendation, queue optimization, ETA
prediction, and RAG-based FAQ components.

Hard rule: code in this package NEVER queries PostgreSQL directly. All
data access happens exclusively through Domain Service tool calls.

Implementation begins in a future milestone.
"""
