"""Hybrid retrieval over the chunks of currently active sources."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol, Sequence, cast

from rank_bm25 import BM25Okapi

from core.types import SourceStatus
from corpus.store import ChunkRecord, DatabasePath, list_chunks, list_sources
from infra import db

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_CACHE_DIR = Path("data/embedding-cache")
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


class Encoder(Protocol):
    def encode(self, texts: Sequence[str], **kwargs: object) -> object: ...


@dataclass(frozen=True)
class SearchResult:
    chunk: ChunkRecord
    score: float
    bm25_score: float
    vector_score: float


def tokenize(text: str) -> list[str]:
    """Tokenize Vietnamese text without dropping diacritics."""
    return _TOKEN_RE.findall(unicodedata.normalize("NFC", text).casefold())


def active_chunks(*, database_path: DatabasePath = None) -> list[ChunkRecord]:
    active_ids = {
        source.doc_id for source in list_sources(SourceStatus.ACTIVE, database_path=database_path)
    }
    return [
        chunk for chunk in list_chunks(database_path=database_path) if chunk.doc_id in active_ids
    ]


def active_index_signature(*, database_path: DatabasePath = None) -> str:
    """A cache key that changes as soon as an active source/chunk changes."""
    parts = [
        json.dumps(
            [
                chunk.doc_id,
                chunk.chunk_id,
                chunk.text,
                chunk.domain.value,
                chunk.label.value,
                chunk.conflict_flag,
                chunk.conflict_with,
                chunk.article_no,
                chunk.clause_no,
                chunk.breadcrumb,
            ],
            ensure_ascii=False,
        )
        for chunk in active_chunks(database_path=database_path)
    ]
    parts.extend(
        json.dumps(
            [
                source.doc_id,
                source.content_hash,
                source.effective_from,
                source.effective_to,
                source.applies_to,
                source.cohorts,
                source.transitional_clause,
                [domain.value for domain in source.domains],
            ],
            ensure_ascii=False,
        )
        for source in list_sources(SourceStatus.ACTIVE, database_path=database_path)
    )
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def _rows(value: object) -> list[list[float]]:
    if hasattr(value, "tolist"):
        value = value.tolist()  # type: ignore[union-attr]
    if not isinstance(value, list):
        raise ValueError("Embedding phải là danh sách các vector.")
    rows: list[list[float]] = []
    for row in value:
        if not isinstance(row, list):
            raise ValueError("Mỗi embedding phải là một vector.")
        rows.append([float(cell) for cell in row])
    return rows


def _normalise(scores: Sequence[float]) -> list[float]:
    if not scores:
        return []
    low, high = min(scores), max(scores)
    if low == high:
        return [1.0 if high > 0 else 0.0 for _ in scores]
    return [(score - low) / (high - low) for score in scores]


@dataclass
class HybridIndex:
    chunks: list[ChunkRecord]
    encoder: Encoder
    bm25: BM25Okapi | None
    vectors: list[list[float]]

    @classmethod
    def build(cls, chunks: list[ChunkRecord], encoder: Encoder) -> "HybridIndex":
        if not chunks:
            return cls(chunks, encoder, None, [])
        vectors = _rows(
            encoder.encode(
                [chunk.text for chunk in chunks],
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        )
        return cls(
            chunks,
            encoder,
            BM25Okapi([tokenize(chunk.text) for chunk in chunks]),
            vectors,
        )

    def search(self, query: str, *, top_k: int = 6) -> list[SearchResult]:
        if not self.chunks or top_k <= 0 or self.bm25 is None:
            return []
        bm25 = [float(score) for score in self.bm25.get_scores(tokenize(query))]
        query_vector = _rows(
            self.encoder.encode([query], normalize_embeddings=True, show_progress_bar=False)
        )[0]
        vector = [sum(a * b for a, b in zip(query_vector, row)) for row in self.vectors]
        bm25_normalised, vector_normalised = _normalise(bm25), _normalise(vector)
        results = [
            SearchResult(chunk, (lexical + semantic) / 2, lexical, semantic)
            for chunk, lexical, semantic in zip(
                self.chunks, bm25_normalised, vector_normalised, strict=True
            )
        ]
        return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]


def build_active_index(*, database_path: DatabasePath = None, encoder: Encoder) -> HybridIndex:
    return HybridIndex.build(active_chunks(database_path=database_path), encoder)


@lru_cache(maxsize=1)
def _load_encoder() -> Encoder:
    """Load once; Sentence Transformers stores downloaded model files on disk."""
    from sentence_transformers import SentenceTransformer

    return cast(Encoder, SentenceTransformer(MODEL_NAME, cache_folder=str(EMBEDDING_CACHE_DIR)))


@lru_cache(maxsize=16)
def _cached_index(database_path: str, signature: str) -> HybridIndex:
    del signature
    return build_active_index(database_path=database_path, encoder=_load_encoder())


def search_active(
    query: str, *, top_k: int = 6, database_path: DatabasePath = None
) -> list[SearchResult]:
    """Search active chunks. The changing signature removes downgraded docs immediately."""
    path = str(Path(database_path or db.DEFAULT_DATABASE_PATH).resolve())
    return _cached_index(path, active_index_signature(database_path=database_path)).search(
        query, top_k=top_k
    )
