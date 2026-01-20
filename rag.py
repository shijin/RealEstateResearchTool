from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from langchain_groq import ChatGroq
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# -------------------------------------------------
# Load environment variables
# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# CONFIGURATION
# -------------------------------------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
COLLECTION_NAME = "real_estate"

BASE_DIR = Path(__file__).parent
CHROMA_DIR = BASE_DIR / "resources" / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------
# INITIALIZE LLM (Groq)
# -------------------------------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.7,
    max_tokens=500
)

# -------------------------------------------------
# INITIALIZE CHROMA (NATIVE CLIENT)
# -------------------------------------------------
client = chromadb.Client(
    settings=chromadb.Settings(
        persist_directory=str(CHROMA_DIR),
        anonymized_telemetry=False
    )
)

embedding_fn = embedding_functions.ONNXMiniLM_L6_V2()

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=embedding_fn
)

# -------------------------------------------------
# INGEST URL DATA (CLOUD SAFE)
# -------------------------------------------------
def process_urls(urls: list[str]):
    """
    Fetch URLs using HTTP (cloud-safe), split text,
    and store embeddings in Chroma.
    """
    yield "🌐 Fetching web pages..."
    loader = WebBaseLoader(urls)
    documents = loader.load()

    if not documents:
        yield "⚠️ No content could be fetched from the URLs."
        return

    yield "✂️ Splitting text into chunks..."
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )

    chunks = splitter.split_documents(documents)

    yield f"📦 Storing {len(chunks)} chunks in vector database..."
    collection.add(
        documents=[doc.page_content for doc in chunks],
        metadatas=[doc.metadata for doc in chunks],
        ids=[str(uuid4()) for _ in chunks]
    )

    yield "✅ Ingestion completed successfully."

# -------------------------------------------------
# QUERY + GENERATION
# -------------------------------------------------
def ask_question(query: str, k: int = 3):
    """
    Retrieve relevant chunks from Chroma
    and generate answer using Groq LLM.
    """
    results = collection.query(
        query_texts=[query],
        n_results=k
    )

    retrieved_docs = results.get("documents", [[]])[0]

    if not retrieved_docs:
        return "I don't know. No relevant information was found."

    context = "\n\n".join(retrieved_docs)

    prompt = f"""
You are a real estate assistant.

Use the context below to answer the question.
If the answer is not present, say you don't know.

Context:
{context}

Question:
{query}
"""

    response = llm.invoke(prompt)
    return response.content
