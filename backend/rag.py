import os
from langchain_community.document_loaders import PyPDFDirectoryLoader, DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("..", ".env"))

INDEX_PATH = "faiss_index"
DOCS_DIR = os.path.join("..", "data", "docs")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


def load_documents():
    docs = []
    pdf_loader = PyPDFDirectoryLoader(DOCS_DIR)
    docs.extend(pdf_loader.load())
    txt_loader = DirectoryLoader(DOCS_DIR, glob="**/*.txt", loader_cls=TextLoader)
    docs.extend(txt_loader.load())
    return docs


def build_index():
    docs = load_documents()
    if not docs:
        raise ValueError(f"No documents found in {DOCS_DIR}. Add a PDF or .txt file.")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(INDEX_PATH)
    print(f"Index built: {len(chunks)} chunks from {len(docs)} documents.")
    return vectorstore


def load_index():
    if os.path.exists(INDEX_PATH):
        return FAISS.load_local(INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    return build_index()


def get_qa_chain():
    vectorstore = load_index()
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True,
    )