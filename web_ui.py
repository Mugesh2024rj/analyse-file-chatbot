import streamlit as st
import os
import google.generativeai as genai
from pathlib import Path
import tempfile
import shutil

# Page config
st.set_page_config(page_title="RAG Chatbot", page_icon="🤖", layout="wide")

def read_text_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    except:
        return ""

def read_pdf_simple(file_path):
    try:
        import PyPDF2
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                try:
                    text += page.extract_text() + "\n"
                except:
                    continue
        return text
    except:
        return ""

def read_docx_simple(file_path):
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except:
        return ""

def read_excel_simple(file_path):
    try:
        import pandas as pd
        df = pd.read_excel(file_path)
        return f"Excel: {file_path.name}\n\n{df.to_string(index=False)}"
    except:
        return ""

def process_uploaded_file(uploaded_file):
    """Process uploaded file and extract content"""
    handlers = {
        '.txt': read_text_file,
        '.md': read_text_file,
        '.pdf': read_pdf_simple,
        '.docx': read_docx_simple,
        '.xlsx': read_excel_simple,
        '.xls': read_excel_simple,
    }
    
    file_ext = Path(uploaded_file.name).suffix.lower()
    
    if file_ext in handlers:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = Path(tmp_file.name)
        
        # Process the file
        content = handlers[file_ext](tmp_path)
        
        # Clean up
        tmp_path.unlink()
        
        return content
    return None

@st.cache_data
def load_documents():
    documents = {}
    handlers = {
        '.txt': read_text_file,
        '.md': read_text_file,
        '.pdf': read_pdf_simple,
        '.docx': read_docx_simple,
        '.xlsx': read_excel_simple,
        '.xls': read_excel_simple,
    }
    
    directory_path = Path("notes")
    if not directory_path.exists():
        return documents
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in handlers:
            content = handlers[file_path.suffix.lower()](file_path)
            if content.strip():
                documents[file_path.name] = content
    
    return documents

def search_documents(query, documents):
    results = []
    query_lower = query.lower()
    
    for filename, content in documents.items():
        if any(word in content.lower() for word in query_lower.split()):
            results.append((filename, content))
    
    return results[:3]

# Main UI
st.title("🤖 RAG Chatbot")
st.markdown("Ask questions about your documents!")

# Configure API key (replace with your actual API key)
API_KEY = "AIzaSyBsy7vaGmbj2wlOONoiDhNVYLeJqMywU_E"
os.environ["GOOGLE_API_KEY"] = API_KEY
genai.configure(api_key=API_KEY)

# Sidebar
with st.sidebar:
    st.header("📁 Documents")
    
    # File upload section
    st.subheader("📤 Upload Files")
    uploaded_files = st.file_uploader(
        "Choose files to analyze",
        type=['txt', 'md', 'pdf', 'docx', 'xlsx', 'xls'],
        accept_multiple_files=True
    )
    
    # Process uploaded files
    uploaded_docs = {}
    if uploaded_files:
        for uploaded_file in uploaded_files:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                content = process_uploaded_file(uploaded_file)
                if content:
                    uploaded_docs[uploaded_file.name] = content
                    st.success(f"✅ {uploaded_file.name}")
                else:
                    st.error(f"❌ Failed to process {uploaded_file.name}")
    
    # Use only uploaded documents
    documents = uploaded_docs
    
    if documents:
        st.write(f"📚 Uploaded: {len(documents)} files")
        for filename in documents.keys():
            st.write(f"📄 {filename}")
    else:
        st.write("📚 No files uploaded yet")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your documents..."):
    
    if not documents:
        st.error("No documents available. Upload files or add them to the 'notes' folder")
        st.stop()
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Searching documents..."):
            # Search documents
            relevant_docs = search_documents(prompt, documents)
            
            if relevant_docs:
                # Prepare context
                context = "\n\n---\n\n".join([f"From {filename}:\n{content[:1000]}..." 
                                             for filename, content in relevant_docs])
                
                # Create prompt
                full_prompt = f"""Based on these documents, answer the question:

{context}

Question: {prompt}

Answer:"""
                
                try:
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(full_prompt)
                    answer = response.text
                except Exception as e:
                    answer = f"Error: {e}"
            else:
                answer = "No relevant information found in documents."
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})