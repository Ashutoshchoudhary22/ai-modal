from code_indexer.embeddings import MockEmbeddingProvider
from code_indexer.hybrid import hybrid_search
from code_indexer.models import Symbol
from code_indexer.vector_store import InMemoryVectorStore


def test_hybrid_search_with_mock_embeddings():
    symbols = [
        Symbol(
            workspace_id="ws",
            file_path="src/auth/service.ts",
            kind="class",
            name="AuthService",
            qualified_name="AuthService",
            start_line=1,
            end_line=10,
        )
    ]
    contents = {"src/auth/service.ts": "export class AuthService {}"}
    store = InMemoryVectorStore()
    provider = MockEmbeddingProvider()
    chunks = provider.embed(["export class AuthService {}"])
    store.upsert("c1", chunks[0], {"relative_path": "src/auth/service.ts"})
    results = hybrid_search(
        "AuthService",
        symbols=symbols,
        file_contents=contents,
        vector_store=store,
        embedding_provider=provider,
    )
    assert results
