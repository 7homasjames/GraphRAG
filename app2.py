import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("GraphRAG - Knowledge Graph")

tab1, tab2 = st.tabs(["📥 Add Document", "🔎 Query Graph"])

with tab1:
    st.header("Add a Document")
    doc_id = st.text_input("Document ID", placeholder="Enter a unique ID")
    
    uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    
    if st.button("Upload PDF"):
        if doc_id and uploaded_file:
            files = {"file": uploaded_file.getvalue()}
            response = requests.post(f"{API_URL}/add_pdf", files=files, data={"doc_id": doc_id})
            st.success(response.json()["message"])
        else:
            st.error("Please provide an ID and upload a PDF.")

with tab2:
    st.header("Query the Knowledge Graph")
    query = st.text_input("Enter your question")

    if st.button("Search"):
        if query:
            response = requests.get(f"{API_URL}/query", params={"query": query})
            if response.status_code == 200:
                st.write("### Answer:")
                st.write(response.json()["response"])
            else:
                st.error("No relevant information found.")
        else:
            st.error("Please enter a question.")
