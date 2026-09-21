"""Facade đọc corpus; B-01 dùng dữ liệu giả để mở khóa Runtime."""

from datetime import date, datetime

from core.types import ChunkLabel, Domain, EvidenceChunk

CORPUS_VERSION = "stub-v1"
_ACTIVE_DOMAINS = [Domain.CONDUCT_SCORE, Domain.COURSE_WITHDRAWAL, Domain.GRADE_APPEAL]
_EFFECTIVE_FROM = date(2026, 1, 1)
_APPLIES_TO = ["undergraduate"]
_COHORTS = ["K48", "K49", "K50"]


def _chunk(
    chunk_id: str,
    doc_id: str,
    breadcrumb: str,
    text: str,
    domain: Domain,
    *,
    label: ChunkLabel = ChunkLabel.AUTO_ANSWERABLE,
    transitional_clause: bool = False,
) -> EvidenceChunk:
    return EvidenceChunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        breadcrumb=breadcrumb,
        text=text,
        domain=domain,
        label=label,
        score=0.9,
        effective_from=_EFFECTIVE_FROM,
        effective_to=None,
        applies_to=list(_APPLIES_TO),
        cohorts=list(_COHORTS),
        transitional_clause=transitional_clause,
        conflict_flag=False,
    )


# ponytail: static corpus unlocks Runtime; replace with the B-12 active index when available.
_CHUNKS: tuple[EvidenceChunk, ...] = (
    _chunk(
        "rl-2026-d08-k02",
        "RL-2026-3150",
        "QĐ 3150/2026 · Điều 8 · Khoản 2",
        "Điểm rèn luyện được đánh giá theo thang điểm 100 cho từng học kỳ.",
        Domain.CONDUCT_SCORE,
        transitional_clause=True,
    ),
    _chunk(
        "rl-2026-d09-k01",
        "RL-2026-3150",
        "QĐ 3150/2026 · Điều 9 · Khoản 1",
        "Sinh viên tra cứu kết quả điểm rèn luyện trên cổng thông tin đào tạo.",
        Domain.CONDUCT_SCORE,
    ),
    _chunk(
        "rl-2026-d10-k01",
        "RL-2026-3150",
        "QĐ 3150/2026 · Điều 10 · Khoản 1",
        "Kết quả được công bố sau khi hoàn thành quy trình đánh giá của học kỳ.",
        Domain.CONDUCT_SCORE,
    ),
    _chunk(
        "rl-2026-d11-k02",
        "RL-2026-3150",
        "QĐ 3150/2026 · Điều 11 · Khoản 2",
        "Điểm rèn luyện được dùng để đánh giá kết quả rèn luyện của sinh viên.",
        Domain.CONDUCT_SCORE,
    ),
    _chunk(
        "rh-2026-d05-k01",
        "RH-2026-101",
        "QC Rút học phần 2026 · Điều 5 · Khoản 1",
        "Sinh viên được gửi yêu cầu rút học phần trước 17 giờ ngày thứ Sáu của tuần 8.",
        Domain.COURSE_WITHDRAWAL,
    ),
    _chunk(
        "rh-2026-d06-k02",
        "RH-2026-101",
        "QC Rút học phần 2026 · Điều 6 · Khoản 2",
        "Học phí được hoàn 70 phần trăm khi rút học phần trong tuần 4 đến tuần 6.",
        Domain.COURSE_WITHDRAWAL,
    ),
    _chunk(
        "rh-2026-d07-k01",
        "RH-2026-101",
        "QC Rút học phần 2026 · Điều 7 · Khoản 1",
        "Yêu cầu rút học phần được nộp trên cổng dịch vụ sinh viên.",
        Domain.COURSE_WITHDRAWAL,
    ),
    _chunk(
        "rh-2026-d08-k01",
        "RH-2026-101",
        "QC Rút học phần 2026 · Điều 8 · Khoản 1",
        "Sinh viên cần kiểm tra thời khóa biểu trước khi gửi yêu cầu rút học phần.",
        Domain.COURSE_WITHDRAWAL,
    ),
    _chunk(
        "pk-2026-d04-k01",
        "PK-2026-204",
        "HD Phúc khảo 2026 · Điều 4 · Khoản 1",
        "Lệ phí phúc khảo là 150.000 đồng cho mỗi học phần.",
        Domain.GRADE_APPEAL,
    ),
    _chunk(
        "pk-2026-d05-k01",
        "PK-2026-204",
        "HD Phúc khảo 2026 · Điều 5 · Khoản 1",
        "Sinh viên nộp đơn phúc khảo theo biểu mẫu PK-01 trong thời hạn công bố.",
        Domain.GRADE_APPEAL,
    ),
    _chunk(
        "pk-2026-d06-k02",
        "PK-2026-204",
        "HD Phúc khảo 2026 · Điều 6 · Khoản 2",
        "Gia hạn hoặc chấp thuận trường hợp đặc biệt do người có thẩm quyền quyết định.",
        Domain.GRADE_APPEAL,
        label=ChunkLabel.HUMAN_ONLY,
    ),
    _chunk(
        "pk-2026-d07-k01",
        "PK-2026-204",
        "HD Phúc khảo 2026 · Điều 7 · Khoản 1",
        "Kết quả phúc khảo được thông báo theo quy trình của đơn vị phụ trách.",
        Domain.GRADE_APPEAL,
        label=ChunkLabel.HUMAN_ONLY,
    ),
)
_CHUNKS_BY_ID = {chunk.chunk_id: chunk for chunk in _CHUNKS}


def get_corpus_version() -> str:
    return CORPUS_VERSION


def search(
    query: str,
    domains: list[Domain],
    top_k: int = 6,
    at: datetime | None = None,
) -> list[EvidenceChunk]:
    """Trả các chunk stub theo domain cho tới khi B-12 thay bằng retrieval thật."""
    del query, at
    return [chunk for chunk in _CHUNKS if chunk.domain in domains][: max(top_k, 0)]


def get_chunk(chunk_id: str) -> EvidenceChunk | None:
    return _CHUNKS_BY_ID.get(chunk_id)


def is_active(chunk_id: str) -> bool:
    return chunk_id in _CHUNKS_BY_ID


def supported_domains() -> list[Domain]:
    return list(_ACTIVE_DOMAINS)
