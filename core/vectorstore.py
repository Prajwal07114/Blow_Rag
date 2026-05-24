import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain.embeddings.base import Embeddings
from dotenv import load_dotenv
from typing import List
import requests

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

load_dotenv()

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", os.path.join(_DATA_DIR, "chroma_db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR",          os.path.join(_DATA_DIR, "uploads"))

os.makedirs(CHROMA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)


class GeminiEmbeddings(Embeddings):
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.url = f"https://generativelanguage.googleapis.com/v1/models/text-embedding-004:embedContent?key={self.api_key}"

    def _embed(self, text: str, task_type: str) -> List[float]:
        response = requests.post(self.url, json={
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]},
            "taskType": task_type
        })
        response.raise_for_status()
        return response.json()["embedding"]["values"]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t, "RETRIEVAL_DOCUMENT") for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text, "RETRIEVAL_QUERY")


def get_embeddings():
    return GeminiEmbeddings()


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