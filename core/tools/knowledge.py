"""
Knowledge Tools — Semantic Search across local documents.
Part of the 10-Layer Security Firewall RAG system.
"""
import json
import logging
from core.knowledge_engine import knowledge_engine

logger = logging.getLogger(__name__)

async def search_knowledge(query: str) -> str:
    """
    Perform a semantic search across your local documents.
    Retrieves the most relevant context chunks from PDFs, Markdown, and text.
    """
    try:
        results = knowledge_engine.query(query, n_results=5)
        if not results:
            return json.dumps({
                "status": "success",
                "message": "No relevant local documents found for that query.",
                "results": []
            })
            
        # Format results for the LLM
        formatted = []
        for r in results:
            formatted.append(f"Source: {r['source']}\nContent: {r['content']}")
            
        context = "\n\n---\n\n".join(formatted)
        
        return json.dumps({
            "status": "success",
            "context_found": True,
            "message": f"Found {len(results)} relevant local context chunks.",
            "results": context
        })
    except Exception as e:
        logger.error(f"Knowledge search failed: {e}")
        return json.dumps({"status": "error", "message": f"Security/Engine error: {str(e)}"})
