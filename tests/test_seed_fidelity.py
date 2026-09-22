"""Bảo vệ tính giả lập và căn cứ đã duyệt của bộ corpus Sprint 1."""

from pathlib import Path

from corpus.seed import SEED_DOCUMENTS_DIRECTORY, ensure_seeded
from infra.db import fetch_all


def test_seed_documents_are_explicitly_fictional_and_keep_legal_units(tmp_path: Path) -> None:
    database_path = tmp_path / "seed.db"
    result = ensure_seeded(database_path=database_path)
    sources = fetch_all("SELECT * FROM sources", database_path=database_path)
    counts = fetch_all(
        "SELECT doc_id, COUNT(*) AS count FROM chunks GROUP BY doc_id",
        database_path=database_path,
    )

    assert result.document_count == 6 and result.chunk_count == 72
    assert {row["count"] for row in counts} == {12}
    assert all(row["is_synthetic"] == 1 and "giả lập" in row["issuer"] for row in sources)
    for path in SEED_DOCUMENTS_DIRECTORY.glob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "DỮ LIỆU GIẢ LẬP — KHÔNG CÓ GIÁ TRỊ PHÁP LÝ" in text
        assert "Căn cứ" in text
        assert "http://" not in text and "https://" not in text


def test_seed_keeps_verify_grounds_and_conflict_scope(tmp_path: Path) -> None:
    database_path = tmp_path / "seed.db"
    ensure_seeded(database_path=database_path)
    sources = {
        row["doc_id"]: row
        for row in fetch_all("SELECT * FROM sources", database_path=database_path)
    }
    chunks = fetch_all("SELECT * FROM chunks", database_path=database_path)
    clause_texts = {
        (row["doc_id"], row["article_no"]): row["text"]
        for row in chunks
        if row["text"].startswith("Khoản 1.")
    }

    assert set(sources) == {
        "RL-2025-2363",
        "RL-2026-3150",
        "RH-2026-101",
        "HP-2026-1",
        "PK-2026-204",
        "QDPQ-2026-01",
    }
    assert sources["RL-2025-2363"]["status"] == "SUPERSEDED"
    assert sources["RL-2025-2363"]["effective_to"] == "2026-07-06"
    assert sources["RL-2026-3150"]["transitional_clause"] == 1
    assert sources["RL-2026-3150"]["effective_from"] == "2026-07-07"
    assert sum(source["status"] == "ACTIVE" for source in sources.values()) == 5
    assert clause_texts["RH-2026-101", "2"] == clause_texts["HP-2026-1", "2"]
    assert "17 giờ 00 thứ Sáu của tuần học thứ 8" in clause_texts["RH-2026-101", "2"]
    assert "70 phần trăm" in clause_texts["RH-2026-101", "3"]
    assert "60 phần trăm" in clause_texts["HP-2026-1", "3"]
    assert "150.000 đồng" in clause_texts["PK-2026-204", "1"]
    assert "Mẫu PK-01" in clause_texts["PK-2026-204", "2"]
    assert "Trưởng phòng Đào tạo quyết định" in clause_texts["PK-2026-204", "3"]
    assert "Hội đồng đào tạo quyết định" in clause_texts["QDPQ-2026-01", "2"]
    assert "thang điểm 100" in clause_texts["RL-2026-3150", "3"]
    assert "sau khi Hội đồng cấp trường phê duyệt" in clause_texts["RL-2026-3150", "4"]
    assert all(row["label"] == "human_only" for row in chunks if row["doc_id"] == "QDPQ-2026-01")
    assert sum(row["label"] == "auto_answerable" for row in chunks) == 42
    assert {(row["doc_id"], row["article_no"]) for row in chunks if row["conflict_flag"]} == {
        ("RH-2026-101", "3"),
        ("HP-2026-1", "3"),
    }
