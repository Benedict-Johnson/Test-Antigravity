import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Langchain imports
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow frontend to communicate with backend

# --- RAG Setup ---
KNOWLEDGE_BASE_PATH = "data/knowledge_base.txt"
CHROMA_PATH = "chroma_db"

def initialize_rag():
    print("Initializing RAG system...")
    if not os.environ.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY") == "your_api_key_here":
        print("WARNING: Valid GEMINI_API_KEY not found in environment variables.")
        return None

    # 1. Load Document
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        print(f"Error: {KNOWLEDGE_BASE_PATH} not found.")
        return None
    
    loader = TextLoader(KNOWLEDGE_BASE_PATH)
    docs = loader.load()

    # 2. Split Document
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    # 3. Create Embeddings & Vector Store
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    
    # We create an ephemeral in-memory Chroma DB for simplicity, or persist to disk
    vectorstore = Chroma.from_documents(documents=splits, embedding=embeddings, persist_directory=CHROMA_PATH)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 4. Create the Chain
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

    system_prompt = (
        "You are a helpful and polite customer support agent for 'SwiftBite Food Delivery'. "
        "Use the following pieces of retrieved context to answer the user's question. "
        "If you don't know the answer based on the context, politely say that you don't know and "
        "offer to connect them to a human agent. Do not make up information. "
        "Keep your answers concise and helpful.\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)
    
    print("RAG system initialized successfully.")
    return rag_chain

rag_chain = initialize_rag()

@app.route('/api/chat', methods=['POST'])
def chat():
    if not rag_chain:
        return jsonify({"error": "Chatbot is currently unavailable. Please ensure API keys are configured properly in the .env file."}), 500

    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({"error": "Message is required."}), 400

    try:
        response = rag_chain.invoke({"input": user_message})
        return jsonify({"answer": response["answer"]})
    except Exception as e:
        print(f"Error processing message: {e}")
        return jsonify({"error": "An error occurred while processing your request. Please check the backend console."}), 500

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    app.run(debug=True, port=5000)
