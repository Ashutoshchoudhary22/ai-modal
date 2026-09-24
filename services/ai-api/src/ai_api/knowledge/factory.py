"""Knowledge retriever factory."""

from __future__ import annotations

from ai_api.knowledge.base import KnowledgeRetriever
from ai_api.knowledge.indexer import IndexerKnowledgeRetriever
from ai_api.knowledge.null import NullKnowledgeRetriever
from ai_platform_shared.config import Settings


def create_knowledge_retriever(settings: Settings) -> KnowledgeRetriever:
    if settings.chat_rag_enabled and settings.indexer_url.strip():
        return IndexerKnowledgeRetriever(settings.indexer_url)
    return NullKnowledgeRetriever()
