#!/usr/bin/env python3
"""
Ingestion Script — Refresh the Local Knowledge Brain.
Crawls the data/knowledge/ directory and indexes all documents into ChromaDB.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KNOWLEDGE_BASE_DIR
from core.knowledge_engine import knowledge_engine

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("ingest")

def main():
    print(f"\n🧠 Sentinal Lee Knowledge Ingestion")
    print(f"───────────────────────────────────")
    print(f"📂 Base Directory: {KNOWLEDGE_BASE_DIR}")
    
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        print(f"Creating knowledge directory...")
        os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
        print(f"Place your PDF, MD, or TXT files in {KNOWLEDGE_BASE_DIR} and run this script again.")
        return

    files_to_index = []
    # Layer 3 Firewall: File type lockdown
    allowed = {".pdf", ".md", ".txt", ".docx"}
    
    for root, _, files in os.walk(KNOWLEDGE_BASE_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in allowed:
                files_to_index.append(os.path.join(root, file))

    if not files_to_index:
        print(f"No valid documents found in {KNOWLEDGE_BASE_DIR}.")
        return

    print(f"Found {len(files_to_index)} documents. Starting indexing...\n")
    
    indexed_count = 0
    for file_path in files_to_index:
        rel_path = os.path.relpath(file_path, KNOWLEDGE_BASE_DIR)
        print(f"Index [{rel_path}]...", end=" ", flush=True)
        
        success = knowledge_engine.ingest_file(file_path)
        if success:
            print("DONE")
            indexed_count += 1
        else:
            print("SKIPPED/FAILED")

    print(f"\n✅ Indexing complete. {indexed_count} files processed.")
    print(f"Lee's semantic brain is now ready to search your documents!")

if __name__ == "__main__":
    main()
