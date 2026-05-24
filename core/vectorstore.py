import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

# ── Resolve paths relative to THIS file, not the working directory ──────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", os.path.join(_DATA_DIR, "chroma_db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR",          os.path.join(_DATA_DIR, "uploads"))

os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_embeddings():
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
    )


def build_vectorstore(file_path: str):
    loader      = PyPDFLoader(file_path)
    docs        = loader.load()
    splitter    = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks      = splitter.split_documents(docs)
    embeddings  = get_embeddings()
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
    )
    return vectorstore


def load_vectorstore():
    embeddings = get_embeddings()
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )