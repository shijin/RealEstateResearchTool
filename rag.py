from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from langchain_groq import ChatGroq
from langchain_community.document_loaders import SeleniumURLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# -------------------------------------------------
# Load environment variables (.env must contain GROQ_API_KEY)
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
# INITIALIZE LLM (LangChain)
# -------------------------------------------------
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.7,
    max_tokens=500
)

# -------------------------------------------------
# INITIALIZE CHROMA (NATIVE)
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
# INGEST URL DATA
# -------------------------------------------------
def process_urls(urls: list[str]):
    yield "Loading web pages..."
    loader = SeleniumURLLoader(urls=urls)
    documents = loader.load()

    yield "Splitting text..."
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " "]
    )

    chunks = splitter.split_documents(documents)

    yield f"Adding {len(chunks)} chunks to Chroma..."
    collection.add(
        documents=[doc.page_content for doc in chunks],
        metadatas=[doc.metadata for doc in chunks],
        ids=[str(uuid4()) for _ in chunks]
    )

    yield "Ingestion completed.\n"

# -------------------------------------------------
# QUERY + GENERATION
# -------------------------------------------------
def ask_question(query: str, k: int = 3):
    print(f"\nQuery: {query}\n")

    results = collection.query(
        query_texts=[query],
        n_results=k
    )

    retrieved_docs = results["documents"][0]

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
    print("Answer:\n")
    print(response.content)
    print("\n" + "-" * 80)


# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    urls = [
        "https://www.cnbc.com/2024/12/21/how-the-federal-reserves-rate-policy-affects-mortgages.html",
        "https://www.cnbc.com/2024/12/20/why-mortgage-rates-jumped-despite-fed-interest-rate-cut.html"
    ]

    process_urls(urls)

    ask_question("How do Federal Reserve interest rates affect 30-year mortgage rates?")
