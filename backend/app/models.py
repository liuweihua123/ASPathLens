"""Pydantic models for API requests and analysis results."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PathNormalizeRequest(BaseModel):
    as_path: str


class PrependedAsn(BaseModel):
    asn: str
    repeat_count: int


class PathNormalizeResponse(BaseModel):
    raw_path: list[str]
    normalized_path: list[str]
    prepending_detected: bool = False
    prepended_asns: list[PrependedAsn] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PathAnalyzeRequest(BaseModel):
    as_path: str
    use_normalized: bool = True


class AsNode(BaseModel):
    asn: str
    org_id: str | None = None
    org_name: str | None = None
    as_name: str | None = None
    country: str | None = None


class PathEdge(BaseModel):
    from_asn: str = Field(alias="from")
    to_asn: str = Field(alias="to")
    relationship: str
    source: str = "as_relationship"
    same_org: bool = False

    model_config = {"populate_by_name": True}


class ValleyFreeResult(BaseModel):
    is_valid: bool | None = None
    violation_index: int | None = None
    violation_pattern: str | None = None
    explanation_zh: str = ""
    explanation_en: str = ""
    uncertain: bool = False


class RouteLeakCandidate(BaseModel):
    is_candidate: bool = False
    candidate_asn: str | None = None
    pattern: str | None = None
    confidence: Literal["high", "medium", "low", "none"] = "none"
    explanation_zh: str = ""
    explanation_en: str = ""


class LeakerLocalization(BaseModel):
    candidate_asn: str | None = None
    candidate_org: str | None = None
    pattern: str | None = None
    confidence: Literal["high", "medium", "low", "none"] = "none"
    reason_zh: str = ""
    reason_en: str = ""
    disclaimer: str = (
        "This is only a candidate localization based on AS relationship patterns, "
        "not a confirmed leaker."
    )


class RiskScoreResult(BaseModel):
    score: int
    level: Literal["normal", "uncertain", "suspicious", "highly suspicious"]
    evidence: list[str] = Field(default_factory=list)
    disclaimer: str = (
        "This score measures AS relationship policy suspiciousness, "
        "not confirmed attack probability."
    )


class RelationshipCoverage(BaseModel):
    total_edges: int
    known_edges: int
    unknown_edges: int
    known_ratio: float
    coverage_level: str
    confidence_note: str = ""


class OrgLevelCheck(BaseModel):
    org_path: list[str]
    compressed_org_path: list[str]
    org_level_less_suspicious: bool = False
    explanation_zh: str = ""
    explanation_en: str = ""


class PathAnalyzeResponse(BaseModel):
    input_path: list[str]
    raw_path: list[str]
    normalized_path: list[str]
    as_nodes: list[AsNode]
    edges: list[dict[str, Any]]
    relationship_sequence: list[str]
    org_path: list[str]
    compressed_org_path: list[str]
    valley_free: ValleyFreeResult
    route_leak_candidate: RouteLeakCandidate
    leaker_localization: LeakerLocalization | None = None
    relationship_coverage: RelationshipCoverage
    risk_score: RiskScoreResult
    org_level: OrgLevelCheck
    dataset_versions: dict[str, str] = Field(default_factory=dict)
    normalization_warnings: list[str] = Field(default_factory=list)


class PathDiffRequest(BaseModel):
    before_path: str
    after_path: str


class DatasetStatusItem(BaseModel):
    dataset_name: str
    version: str | None = None
    file_name: str | None = None
    status: str
    record_count: int | None = None
    parsed_at: str | None = None
    extra: dict[str, Any] = Field(default_factory=dict)