"""Unit tests for Pydantic v2 regulatory audit schemas."""

import pytest
from pydantic import ValidationError

from src.schemas.audit_models import (
    OperatorType,
    ParameterMeasurement,
    SpecificationRule,
)


def test_parameter_measurement_valid() -> None:
    measurement = ParameterMeasurement(
        name="Bacterial Endotoxins",
        raw_value="< 0.05 EU/mg",
        numeric_value=0.05,
        unit="EU/mg",
        evidence_quote="Bacterial Endotoxins: < 0.05 EU/mg",
        page_number=1,
    )
    assert measurement.name == "Bacterial Endotoxins"
    assert measurement.numeric_value == 0.05
    assert measurement.evidence_quote == "Bacterial Endotoxins: < 0.05 EU/mg"


def test_parameter_measurement_missing_required() -> None:
    with pytest.raises(ValidationError):
        # Missing evidence_quote
        ParameterMeasurement(
            name="Assay",
            raw_value="99.0%",
        )  # type: ignore[call-arg]


def test_specification_rule_defaults() -> None:
    rule = SpecificationRule(
        parameter_name="Assay (HPLC)",
        operator=OperatorType.GTE,
        min_value=98.0,
        unit="%",
    )
    assert rule.is_critical is True
    assert rule.warning_ratio == 0.85
    assert rule.regulatory_reference == "USP / Ph. Eur."
