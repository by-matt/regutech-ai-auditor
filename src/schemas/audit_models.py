"""Pydantic v2 schemas for deterministic CoA and pharmacopeia auditing."""

from enum import StrEnum
from pydantic import BaseModel, Field


class OperatorType(StrEnum):
    """Supported mathematical and qualitative operators for quality specs."""

    LTE = "LTE"  # <= Max
    GTE = "GTE"  # >= Min
    BETWEEN = "BETWEEN"  # Min <= x <= Max
    EQ = "EQ"  # Exact string or numeric match
    LT = "LT"  # < Max
    GT = "GT"  # > Min


class FindingStatus(StrEnum):
    """Deterministic status outcome for an individual test parameter."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    UNVERIFIED_SOURCE = "UNVERIFIED_SOURCE"


class OverallVerdict(StrEnum):
    """Executive batch disposition verdict."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"


class ParameterMeasurement(BaseModel):
    """Individual analytical measurement extracted from a Certificate of Analysis."""

    name: str = Field(..., description="Standardized analytical parameter name")
    raw_value: str = Field(..., description="Raw text representation as stated in CoA")
    numeric_value: float | None = Field(
        default=None, description="Parsed numeric value if quantitatively measurable"
    )
    unit: str = Field(default="", description="Measurement unit (e.g., ppm, %, EU/mg)")
    test_method: str | None = Field(
        default=None, description="Analytical test method or monograph chapter reference"
    )
    evidence_quote: str = Field(
        ..., description="Exact textual excerpt from the source document used as evidence"
    )
    page_number: int = Field(default=1, description="Document page number where citation appears")


class SpecificationRule(BaseModel):
    """Acceptance criteria rule derived from pharmacopeia or internal QA monograph."""

    parameter_name: str = Field(..., description="Target parameter to evaluate")
    operator: OperatorType = Field(..., description="Comparison operator")
    min_value: float | None = Field(default=None, description="Minimum acceptable threshold")
    max_value: float | None = Field(default=None, description="Maximum acceptable threshold")
    expected_text: str | None = Field(
        default=None, description="Expected qualitative match (e.g., 'White crystalline powder')"
    )
    unit: str = Field(default="", description="Expected measurement unit")
    warning_ratio: float = Field(
        default=0.85,
        description="Threshold fraction of max limit triggering preventative warnings (e.g. 85%)",
    )
    regulatory_reference: str = Field(
        default="USP / Ph. Eur.", description="Regulatory standard or pharmacopeial monograph"
    )
    is_critical: bool = Field(
        default=True,
        description="Whether this parameter is a critical quality attribute (CQA)",
    )


class AuditFinding(BaseModel):
    """Detailed audit verdict and traceability record for an individual parameter."""

    parameter_name: str
    measured_raw: str
    measured_numeric: float | None
    unit: str
    specification_summary: str
    status: FindingStatus
    deviation_percent: float | None = Field(
        default=None, description="Percentage deviation outside acceptable tolerance"
    )
    is_critical: bool
    evidence_quote: str
    quote_verified: bool = Field(
        ..., description="Strict invariant: True if evidence_quote is a literal substring of CoA"
    )
    rationale: str


class AuditReport(BaseModel):
    """Executive regulatory release dossier for a batch."""

    report_id: str
    batch_id: str
    product_name: str
    specification_name: str
    auditor_timestamp: str
    verdict: OverallVerdict
    total_tests: int
    passed_count: int
    warning_count: int
    failed_count: int
    unverified_count: int
    compliance_score: float = Field(
        ..., description="Percentage of evaluated tests passing without failure (0-100%)"
    )
    findings: list[AuditFinding]
    summary_notes: str
