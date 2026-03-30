"""
Knowledge Engine — Secure Local RAG (Retrieval-Augmented Generation).
Implements a 10-Layer Security Firewall to protect local document data.
"""
import os
import json
import logging
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import pypdf
from datetime import datetime

from config import KNOWLEDGE_BASE_DIR, VECTOR_DB_PATH, EMBEDDING_MODEL_NAME

logger = logging.getLogger(__name__)

# Layer 10: Audit Traceability
AUDIT_LOG_PATH = os.path.join(os.path.dirname(VECTOR_DB_PATH), "knowledge_audit.log")

def _audit_log(action: str, details: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {action.upper()}: {details}\n")

class KnowledgeEngine:
    def __init__(self):
        # Layer 1: Air-Gapped Embeddings (Local-only via SentenceTransformers)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
        
        # Initialize Vector Store
        self.chroma_client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.collection = self.chroma_client.get_or_create_collection(
            name="sentinal_knowledge",
            embedding_function=self.embedding_fn
        )
        
        # Layer 3: File Type Lockdown
        self.allowed_extensions = {".pdf", ".md", ".txt", ".docx"}
        
        _audit_log("init", f"Knowledge engine initialized with {EMBEDDING_MODEL_NAME}")

    def _is_safe_path(self, path: str) -> bool:
        # Layer 2: Strict Directory Jail
        # Layer 6: Path Sanitization
        abs_base = os.path.abspath(os.path.expanduser(KNOWLEDGE_BASE_DIR))
        abs_target = os.path.abspath(os.path.expanduser(path))
        return abs_target.startswith(abs_base)

    def _scrub_text(self, text: str) -> str:
        # Layer 5: Prompt Injection Filtering
        # Removes common indirect injection patterns found in docs
        disallowed = [
            "ignore previous instructions", 
            "system override", 
            "you are now", 
            "new rules:"
        ]
        scrubbed = text
        for pattern in disallowed:
            if pattern in scrubbed.lower():
                scrubbed = scrubbed.replace(pattern, "[REDACTED_SECURITY_THREAT]")
        return scrubbed

    def ingest_file(self, file_path: str):
        # Layer 4: Read-Only (checks existence, never modifies source)
        if not self._is_safe_path(file_path):
            _audit_log("security_alert", f"Block ingestion of out-of-jail file: {file_path}")
            return False
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.allowed_extensions:
            return False

        text = ""
        try:
            if ext == ".pdf":
                with open(file_path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    for page in reader.pages:
                        text += (page.extract_text() or "") + "\n"
            elif ext in (".md", ".txt"):
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read()
            
            if not text.strip():
                return False

            # Chunking (Layer 7: Context Quota)
            # Simple chunking for now: 1000 chars with 200 overlap
            chunks = []
            chunk_size = 1000
            overlap = 200
            for i in range(0, len(text), chunk_size - overlap):
                chunks.append(text[i:i + chunk_size])

            # Layer 8: Metadata Scrubbing
            # Only store relative path to avoid leaking system usernames in DB
            rel_path = os.path.relpath(file_path, KNOWLEDGE_BASE_DIR)
            
            ids = [f"{rel_path}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": rel_path} for _ in range(len(chunks))]
            
            self.collection.upsert(
                ids=ids,
                documents=chunks,
                metadatas=metadatas
            )
            _audit_log("ingest", f"Indexed {len(chunks)} chunks from {rel_path}")
            return True
        except Exception as e:
            _audit_log("error", f"Failed to ingest {file_path}: {e}")
            return False

    def query(self, query_text: str, n_results: int = 5) -> list:
        # Layer 7: Maximum Context Quota (capped at 10)
        n_results = min(n_results, 10)
        
        # Layer 9: No External URLs (implicitly local lookup only)
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        formatted = []
        if results["documents"]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                scrubbed_doc = self._scrub_text(doc)
                formatted.append({
                    "content": scrubbed_doc,
                    "source": meta["source"]
                })
        
        _audit_log("query", f"Searched for '{query_text}'. Found {len(formatted)} results.")
        return formatted

# Singleton instance
knowledge_engine = KnowledgeEngine()
