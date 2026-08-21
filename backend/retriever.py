"""Secure retrieval module with role-based metadata filtering."""

import logging
from typing import Optional

import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.config import (
    CHROMA_DIR, CHROMA_COLLECTION_NAME, TOP_K_RETRIEVAL,
    GEMINI_EMBEDDING_MODEL, GOOGLE_API_KEY,
    ROLE_DOCUMENTS,
)

logger = logging.getLogger(__name__)


class SecureRetriever:
    """Retrieves document chunks with RBAC filtering applied at retrieval layer."""

    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.embeddings = None
        if GOOGLE_API_KEY:
            try:
                self.embeddings = GoogleGenerativeAIEmbeddings(
                    model=GEMINI_EMBEDDING_MODEL,
                    google_api_key=GOOGLE_API_KEY,
                )
            except Exception as e:
                logger.warning(f"Could not initialize embeddings: {e}")

    def _get_collection(self):
        try:
            return self.chroma_client.get_collection(CHROMA_COLLECTION_NAME)
        except Exception as e:
            logger.error(f"Could not get collection: {e}")
            return None

    def retrieve(self, query: str, role: str, top_k: int = TOP_K_RETRIEVAL) -> list[dict]:
        """Retrieve document chunks authorized for the given role.

        RBAC is enforced at the retrieval layer — unauthorized documents
        are filtered out before the chunks reach the LLM.
        """
        collection = self._get_collection()
        if not collection:
            logger.warning("No collection found. Documents may not be ingested yet.")
            return []

        # Get documents authorized for this role
        authorized_docs = ROLE_DOCUMENTS.get(role, [])

        if not authorized_docs:
            logger.info(f"No authorized documents for role: {role}")
            return []

        try:
            if self.embeddings:
                query_embedding = self.embeddings.embed_query(query)
                results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k * 3,  # Get more to filter
                )
            else:
                # Without Gemini, use ChromaDB's built-in embedding
                results = collection.query(
                    query_texts=[query],
                    n_results=top_k * 3,
                )

            if not results or not results.get("metadatas") or not results["metadatas"][0]:
                return []

            # Filter by role authorization
            filtered_chunks = []
            for i in range(len(results["metadatas"][0])):
                metadata = results["metadatas"][0][i]
                doc_content = results["documents"][0][i] if results.get("documents") else ""
                doc_id = results["ids"][0][i] if results.get("ids") else ""

                # Check if this chunk's document is authorized for the role
                doc_filename = metadata.get("filename", "")
                if doc_filename in authorized_docs:
                    filtered_chunks.append({
                        "content": doc_content,
                        "metadata": metadata,
                        "id": doc_id,
                        "relevance_score": results["distances"][0][i] if results.get("distances") else 0.0,
                    })

            # Return top_k after filtering
            return filtered_chunks[:top_k]

        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return []

    def retrieve_all_authorized(self, query: str, role: str) -> list[dict]:
        """Retrieve all authorized chunks (no top_k limit) for comprehensive evaluation."""
        return self.retrieve(query, role, top_k=100)


def get_retriever() -> SecureRetriever:
    return SecureRetriever()