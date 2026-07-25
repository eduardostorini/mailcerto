from enum import StrEnum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

class CheckStatus(StrEnum):
    SUCCESS = "success"
    INFO = "info"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SKIPPED = "skipped"
    INCONCLUSIVE = "inconclusive"

@dataclass(slots=True)
class CheckResult:
    check_id: str
    category: str
    title: str
    status: CheckStatus
    summary: str
    details: str | None = None
    recommendation: str | None = None
    response_time_ms: float | None = None
    score: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

@dataclass(slots=True)
class AnalysisResult:
    target: str
    target_type: str  # domain, ip, url, etc.
    started_at: datetime
    finished_at: datetime | None = None
    score_general: int = 100
    scores_by_category: dict[str, int] = field(default_factory=dict)
    results: list[CheckResult] = field(default_factory=list)
    success_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    critical_count: int = 0
    info_count: int = 0
