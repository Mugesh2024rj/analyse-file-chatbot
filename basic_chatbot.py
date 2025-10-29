# Working RAG Chatbot with Google Gemini
import os
import getpass
import google.generativeai as genai
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Setup Google API
if not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API Key: ")

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-2.5-flash')

# Load documents
print("📚 Loading documents...")
documents = SimpleDirectoryReader("notes").load_data()

# Setup embedding
print("🔧 Setting up embeddings...")
embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.embed_model = embed_model

# Create index
print("🔍 Creating search index...")
index = VectorStoreIndex.from_documents(documents)
retriever = index.as_retriever(similarity_top_k=2)

print("\n🧠 RAG Chatbot ready! Type your questions (type 'quit' to exit)\n")

while True:
    ques = input("You: ").strip()
    if ques.lower() == "quit":
        print("👋 Goodbye!")
        break
    
    try:
        # Retrieve relevant documents
        nodes = retriever.retrieve(ques)
        
        if nodes:
            # Combine retrieved text
            context = "\n".join([node.text for node in nodes])
            
            # Create prompt for Gemini
            prompt = f"""Based on the following context from course notes, answer the question:

Context:
{context}

Question: {ques}

Answer:"""
            
            # Get response from Gemini
            response = model.generate_content(prompt)
            print("🤖:", response.text)
        else:
            print("🤖: I couldn't find relevant information in the notes to answer your question.")
            
    except Exception as e:
        print("⚠️ Error:", e)