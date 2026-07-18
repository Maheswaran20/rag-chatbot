from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag import get_qa_chain, build_index

app = FastAPI(title="RAG Chatbot API")

# Allow Streamlit (and anything) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build/load the chain once at startup
qa_chain = get_qa_chain()


class Query(BaseModel):
    question: str


@app.get("/")
def root():
    return {"status": "ok", "message": "RAG API is running"}


@app.post("/reindex")
def reindex():
    global qa_chain
    build_index()
    qa_chain = get_qa_chain()
    return {"status": "reindexed"}


@app.post("/ask")
def ask(query: Query):
    if not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    result = qa_chain.invoke({"query": query.question})
    sources = [
        d.metadata.get("source", "unknown")
        for d in result["source_documents"]
    ]
    return {
        "answer": result["result"],
        "sources": list(set(sources)),
    }