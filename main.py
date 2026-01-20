import streamlit as st
from rag import process_urls, ask_question

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Real Estate Research Tool",
    layout="wide"
)

st.title("🏠 Real Estate Research Tool")

# -------------------------------------------------
# SIDEBAR – URL INGESTION
# -------------------------------------------------
st.sidebar.header("📥 Ingest Data (URLs)")

url1 = st.sidebar.text_input("URL 1")
url2 = st.sidebar.text_input("URL 2")
url3 = st.sidebar.text_input("URL 3")

process_button = st.sidebar.button("Process URLs")

status_placeholder = st.empty()

if process_button:
    urls = [url.strip() for url in (url1, url2, url3) if url.strip()]

    if not urls:
        status_placeholder.error("❌ Please provide at least one valid URL")
    else:
        with st.spinner("Processing URLs. Please wait..."):
            for status in process_urls(urls):
                status_placeholder.info(status)

        status_placeholder.success("✅ URLs processed successfully!")

# -------------------------------------------------
# QUESTION ANSWERING
# -------------------------------------------------
st.divider()
st.header("🔎 Ask a Question")

question = st.text_input(
    "Enter your question about real estate or mortgage rates:"
)

ask_button = st.button("Get Answer")

if ask_button:
    if not question.strip():
        st.warning("⚠️ Please enter a question.")
    else:
        with st.spinner("Generating answer..."):
            answer_placeholder = st.empty()

            # Capture printed output from ask_question
            import io
            import sys

            buffer = io.StringIO()
            sys_stdout = sys.stdout
            sys.stdout = buffer

            ask_question(question)

            sys.stdout = sys_stdout
            answer_text = buffer.getvalue()

            answer_placeholder.markdown("### 📌 Answer")
            answer_placeholder.write(answer_text)
