# Simple Universal Chatbot - Error-Free Version
import os
import getpass
import google.generativeai as genai
from pathlib import Path

# Setup Google API
os.environ["GOOGLE_API_KEY"] = "AIzaSyBsy7vaGmbj2wlOONoiDhNVYLeJqMywU_E"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

def read_text_file(file_path):
    """Safely read text files"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    except:
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except:
            return ""

def read_pdf_simple(file_path):
    """Simple PDF reader"""
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
        return f"Could not read PDF: {file_path.name}"

def read_docx_simple(file_path):
    """Simple DOCX reader"""
    try:
        from docx import Document
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except:
        return f"Could not read DOCX: {file_path.name}"

def read_excel_simple(file_path):
    """Simple Excel reader"""
    try:
        import pandas as pd
        df = pd.read_excel(file_path)
        return f"Excel file: {file_path.name}\n\n{df.to_string(index=False)}"
    except:
        return f"Could not read Excel: {file_path.name}"

def load_documents_simple(directory):
    """Load documents with error handling"""
    documents = {}
    directory_path = Path(directory)
    
    if not directory_path.exists():
        print(f"Creating directory: {directory}")
        directory_path.mkdir(exist_ok=True)
        return documents
    
    # File handlers
    handlers = {
        '.txt': read_text_file,
        '.md': read_text_file,
        '.pdf': read_pdf_simple,
        '.docx': read_docx_simple,
        '.xlsx': read_excel_simple,
        '.xls': read_excel_simple,
    }
    
    print("📁 Scanning for files...")
    file_count = 0
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file():
            file_ext = file_path.suffix.lower()
            
            if file_ext in handlers:
                print(f"📄 Reading: {file_path.name}")
                content = handlers[file_ext](file_path)
                
                if content and content.strip():
                    documents[file_path.name] = {
                        'content': content,
                        'path': str(file_path),
                        'type': file_ext
                    }
                    file_count += 1
                    print(f"✅ Loaded: {file_path.name}")
                else:
                    print(f"⚠️ Empty or unreadable: {file_path.name}")
    
    print(f"📚 Total files loaded: {file_count}")
    return documents

def search_documents(query, documents, max_results=3):
    """Simple text search in documents"""
    results = []
    query_lower = query.lower()
    
    for filename, doc_data in documents.items():
        content = doc_data['content'].lower()
        if any(word in content for word in query_lower.split()):
            # Calculate simple relevance score
            score = sum(content.count(word) for word in query_lower.split())
            results.append((filename, doc_data, score))
    
    # Sort by relevance and return top results
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:max_results]

# Main execution
print("🚀 Starting Simple Universal Chatbot...")

# Load documents
documents = load_documents_simple("notes")

if not documents:
    print("\n❌ No documents found!")
    print("Please add files to the 'notes' directory.")
    print("Supported formats: TXT, MD, PDF, DOCX, XLSX")
    
    # Create a sample file
    sample_path = Path("notes/sample.txt")
    sample_path.parent.mkdir(exist_ok=True)
    with open(sample_path, 'w') as f:
        f.write("This is a sample document for testing the chatbot.\nYou can ask questions about this content.")
    print(f"✅ Created sample file: {sample_path}")
    
    # Reload documents
    documents = load_documents_simple("notes")

print(f"\n🧠 Chatbot ready with {len(documents)} documents!")
print("📋 File types loaded:", set([doc['type'] for doc in documents.values()]))
print("\nType your questions (type 'quit' to exit)")
print("=" * 50)

while True:
    try:
        question = input("\nYou: ").strip()
        
        if question.lower() in ['quit', 'exit', 'bye']:
            print("👋 Goodbye!")
            break
        
        if not question:
            continue
        
        # Search for relevant documents
        relevant_docs = search_documents(question, documents)
        
        if not relevant_docs:
            print("🤖: I couldn't find relevant information in your documents.")
            continue
        
        # Prepare context from relevant documents
        context_parts = []
        for filename, doc_data, score in relevant_docs:
            context_parts.append(f"From {filename}:\n{doc_data['content'][:1000]}...")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Create prompt
        prompt = f"""Based on the following documents, answer the question:

Documents:
{context}

Question: {question}

Please provide a helpful answer based on the information above."""
        
        # Get response from Gemini
        print("🤖: ", end="", flush=True)
        response = model.generate_content(prompt)
        print(response.text)
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"⚠️ Error: {e}")
        print("Please try again with a different question.")