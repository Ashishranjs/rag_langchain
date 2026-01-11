from flask import Flask, render_template, jsonify, request
from flask_cors import CORS   # ✅ NEW
from src.helper import download_hugging_face_embeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.memory import ChatMessageHistory
from dotenv import load_dotenv
from src.prompt import *
import os

app = Flask(__name__)

# ✅ ENABLE CORS (safe for future frontend usage)
CORS(app, origins=["http://localhost:5173", "https://videocalling-rag-frontend.vercel.app"])

load_dotenv()

PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
groq_api_key = os.getenv("GROK_API_KEY")

os.environ["GROK_API_KEY"] = groq_api_key
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# ------------------------------------------------
# Embeddings + Pinecone
# ------------------------------------------------
embeddings = download_hugging_face_embeddings()

index_name = "medical-chatbot"
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)

retriever = docsearch.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

# ------------------------------------------------
# Groq LLM
# ------------------------------------------------
llm = ChatGroq(
    api_key=groq_api_key,
    model='llama-3.1-8b-instant',
    temperature=0.1,
    max_tokens=1024
)

# ------------------------------------------------
# Prompt (WITH MEMORY)
# ------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("placeholder", "{chat_history}"),
    ("human", "{input}")
])

question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)

# ------------------------------------------------
# MEMORY
# ------------------------------------------------
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

rag_chain_with_memory = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

# ------------------------------------------------
# Routes
# ------------------------------------------------
@app.route("/")
def index():
    return render_template("chat.html")

@app.route("/get", methods=["POST"])
def chat():
    data = request.get_json()

    msg = data.get("message")
    user_id = data.get("userId")

    response = rag_chain_with_memory.invoke(
        {"input": msg},
        config={"configurable": {"session_id": user_id}}
    )

    return jsonify({"answer": response["answer"]})

# ------------------------------------------------
# Run
# ------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
