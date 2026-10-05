"""Unit tests for deterministic audit engine and invariant verification."""

from src.data.monographs import (
    SAMPLE_COA_CONFORMING_TEXT,
    SAMPLE_COA_NON_CONFORMING_TEXT,
    SAMPLE_CONFORMING_MEASUREMENTS,
    SAMPLE_NON_CONFORMING_MEASUREMENTS,
    USP_INSULIN_RULES,
)
from src.engine.deterministic_auditor import DeterministicAuditor
from src.parser.document_loader import DocumentLoader
from src.schemas.audit_models import (
    FindingStatus,
    OperatorType,
    OverallVerdict,
    ParameterMeasurement,
    SpecificationRule,
)


def test_exact_quote_substring_invariant() -> None:
    auditor = DeterministicAuditor(strict_verification=True)
    dossier = DocumentLoader.load_text(SAMPLE_COA_CONFORMING_TEXT, "test_coa.txt")

    # 1. Valid quote present in document
    valid_meas = ParameterMeasurement(
        name="Assay (HPLC)",
        raw_value="99.4%",
        numeric_value=99.4,
        unit="%",
        evidence_quote="Assay (HPLC): 99.4%",
        page_number=1,
    )
    rule = SpecificationRule(
        parameter_name="Assay (HPLC)",
        operator=OperatorType.BETWEEN,
        min_value=95.0,
        max_value=105.0,
        unit="%",
    )

    finding_valid = auditor.evaluate_parameter(valid_meas, rule, dossier)
    assert finding_valid.quote_verified is True
    assert finding_valid.status == FindingStatus.PASS

    # 2. Hallucinated / rogue quote NOT in document
    fake_meas = ParameterMeasurement(
        name="Assay (HPLC)",
        raw_value="99.4%",
        numeric_value=99.4,
        unit="%",
        evidence_quote="Invented claim by hallucinating LLM that does not exist in text",
        page_number=1,
    )
    finding_fake = auditor.evaluate_parameter(fake_meas, rule, dossier)
    assert finding_fake.quote_verified is False
    assert finding_fake.status == FindingStatus.UNVERIFIED_SOURCE


def test_numeric_bounds_lte_pass_and_fail() -> None:
    auditor = DeterministicAuditor(strict_verification=False)
    rule = SpecificationRule(
        parameter_name="Heavy Metals (Pb)",
        operator=OperatorType.LTE,
        max_value=10.0,
        unit="ppm",
        warning_ratio=0.80,
    )

    # Pass case
    pass_meas = ParameterMeasurement(
        name="Heavy Metals (Pb)",
        raw_value="2.5 ppm",
        numeric_value=2.5,
        unit="ppm",
        evidence_quote="2.5 ppm",
    )
    finding_pass = auditor.evaluate_parameter(pass_meas, rule)
    assert finding_pass.status == FindingStatus.PASS
    assert finding_pass.deviation_percent == 0.0

    # Fail case (15 ppm vs <= 10 ppm -> +50% deviation)
    fail_meas = ParameterMeasurement(
        name="Heavy Metals (Pb)",
        raw_value="15.0 ppm",
        numeric_value=15.0,
        unit="ppm",
        evidence_quote="15.0 ppm",
    )
    finding_fail = auditor.evaluate_parameter(fail_meas, rule)
    assert finding_fail.status == FindingStatus.FAIL
    assert finding_fail.deviation_percent == 50.0


def test_preventative_warning_alert() -> None:
    auditor = DeterministicAuditor(strict_verification=False)
    rule = SpecificationRule(
        parameter_name="High Molecular Weight Proteins (HMWP)",
        operator=OperatorType.LTE,
        max_value=1.00,
        unit="%",
        warning_ratio=0.85,  # Alert at >= 0.85%
    )

    warn_meas = ParameterMeasurement(
        name="High Molecular Weight Proteins (HMWP)",
        raw_value="0.91%",
        numeric_value=0.91,
        unit="%",
        evidence_quote="0.91%",
    )
    finding_warn = auditor.evaluate_parameter(warn_meas, rule)
    assert finding_warn.status == FindingStatus.WARN


def test_conforming_batch_audit_lifecycle() -> None:
    auditor = DeterministicAuditor(strict_verification=True)
    dossier = DocumentLoader.load_text(SAMPLE_COA_CONFORMING_TEXT, "conforming.txt")

    report = auditor.audit_batch(
        batch_id="INS-2026-X88",
        product_name="Recombinant Human Insulin",
        specification_name="USP Monograph",
        measurements=SAMPLE_CONFORMING_MEASUREMENTS,
        rules=USP_INSULIN_RULES,
        dossier=dossier,
    )

    assert report.verdict == OverallVerdict.APPROVED
    assert report.failed_count == 0
    assert report.unverified_count == 0
    assert report.compliance_score == 100.0


def test_non_conforming_batch_audit_lifecycle() -> None:
    auditor = DeterministicAuditor(strict_verification=True)
    dossier = DocumentLoader.load_text(SAMPLE_COA_NON_CONFORMING_TEXT, "non_conforming.txt")

    report = auditor.audit_batch(
        batch_id="INS-2026-FAIL04",
        product_name="Recombinant Human Insulin",
        specification_name="USP Monograph",
        measurements=SAMPLE_NON_CONFORMING_MEASUREMENTS,
        rules=USP_INSULIN_RULES,
        dossier=dossier,
    )

    assert report.verdict == OverallVerdict.REJECTED
    assert report.failed_count >= 3  # Endotoxins (14.8 > 10), Heavy Metals (16.5 > 10), Bioburden (145 > 100)
    assert report.warning_count >= 1  # HMWP (0.92 >= 0.85)
