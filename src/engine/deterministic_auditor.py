"""Deterministic, zero-hallucination regulatory compliance engine."""

from datetime import datetime, UTC
import re
import uuid
from src.parser.document_loader import DocumentContent
from src.schemas.audit_models import (
    AuditFinding,
    AuditReport,
    FindingStatus,
    OperatorType,
    OverallVerdict,
    ParameterMeasurement,
    SpecificationRule,
)


class DeterministicAuditor:
    """Executes closed-loop regulatory verification with mathematical bound guarantees."""

    def __init__(
        self,
        strict_verification: bool = True,
        strict_invariant: bool | None = None,
    ):
        if strict_invariant is not None:
            strict_verification = strict_invariant
        self.strict_verification = strict_verification

    @staticmethod
    def parse_numeric_candidate(raw: str) -> tuple[float | None, str]:
        """Extract numeric value and any boundary operator from a raw string.

        Examples:
            "< 0.05" -> (0.05, "<")
            "99.4%"  -> (99.4, "")
            "0.02 ppm" -> (0.02, "")
        """
        raw_clean = raw.strip()
        match = re.search(r"([<>≤≥]?)\s*([0-9]+(?:\.[0-9]+)?)", raw_clean)
        if match:
            op_symbol = match.group(1)
            val = float(match.group(2))
            return val, op_symbol
        return None, ""

    def evaluate_parameter(
        self,
        measurement: ParameterMeasurement,
        rule: SpecificationRule,
        dossier: DocumentContent | None = None,
    ) -> AuditFinding:
        """Evaluate a single parameter against its pharmacopeial specification."""
        # 1. Verify exact-quote substring invariant
        quote_verified = True
        if dossier is not None:
            quote_verified, _ = dossier.verify_substring(measurement.evidence_quote)

        spec_summary = self._format_spec_summary(rule)

        if not quote_verified and self.strict_verification:
            return AuditFinding(
                parameter_name=rule.parameter_name,
                measured_raw=measurement.raw_value,
                measured_numeric=measurement.numeric_value,
                unit=measurement.unit or rule.unit,
                specification_summary=spec_summary,
                status=FindingStatus.UNVERIFIED_SOURCE,
                deviation_percent=None,
                is_critical=rule.is_critical,
                evidence_quote=measurement.evidence_quote,
                quote_verified=False,
                rationale=(
                    f"Evidence quote '{measurement.evidence_quote}' could not be verified as an "
                    f"exact substring in the source document '{dossier.filename if dossier else 'N/A'}'. "
                    "Flagged for data integrity safeguard."
                ),
            )

        # 2. Check qualitative tests
        if rule.expected_text is not None and rule.operator == OperatorType.EQ:
            raw_meas = measurement.raw_value.lower().strip()
            exp_text = rule.expected_text.lower().strip()
            if exp_text in raw_meas or "conforms" in raw_meas or "complies" in raw_meas:
                status = FindingStatus.PASS
                rationale = f"Qualitative specification satisfied: '{measurement.raw_value}'."
            else:
                status = FindingStatus.FAIL
                rationale = (
                    f"Qualitative non-conformance. Expected: '{rule.expected_text}', "
                    f"Measured: '{measurement.raw_value}'."
                )
            return AuditFinding(
                parameter_name=rule.parameter_name,
                measured_raw=measurement.raw_value,
                measured_numeric=None,
                unit=measurement.unit or rule.unit,
                specification_summary=spec_summary,
                status=status,
                deviation_percent=0.0 if status == FindingStatus.PASS else 100.0,
                is_critical=rule.is_critical,
                evidence_quote=measurement.evidence_quote,
                quote_verified=quote_verified,
                rationale=rationale,
            )

        # 3. Check quantitative numeric tests
        num_val = measurement.numeric_value
        op_sym = ""
        if num_val is None:
            num_val, op_sym = self.parse_numeric_candidate(measurement.raw_value)

        if num_val is None:
            return AuditFinding(
                parameter_name=rule.parameter_name,
                measured_raw=measurement.raw_value,
                measured_numeric=None,
                unit=measurement.unit or rule.unit,
                specification_summary=spec_summary,
                status=FindingStatus.FAIL,
                deviation_percent=None,
                is_critical=rule.is_critical,
                evidence_quote=measurement.evidence_quote,
                quote_verified=quote_verified,
                rationale=f"Failed to parse numeric reading from '{measurement.raw_value}'.",
            )

        status, deviation, rationale = self._evaluate_numeric_bounds(num_val, op_sym, rule)

        return AuditFinding(
            parameter_name=rule.parameter_name,
            measured_raw=measurement.raw_value,
            measured_numeric=num_val,
            unit=measurement.unit or rule.unit,
            specification_summary=spec_summary,
            status=status,
            deviation_percent=deviation,
            is_critical=rule.is_critical,
            evidence_quote=measurement.evidence_quote,
            quote_verified=quote_verified,
            rationale=rationale,
        )

    def _evaluate_numeric_bounds(
        self, val: float, op_sym: str, rule: SpecificationRule
    ) -> tuple[FindingStatus, float | None, str]:
        """Apply deterministic math bounds to test reading."""
        status = FindingStatus.PASS
        deviation: float | None = 0.0
        rationale = "Result conforms strictly with monograph specifications."

        if rule.operator in (OperatorType.LTE, OperatorType.LT):
            assert rule.max_value is not None, "Rule max_value required for LTE/LT"
            limit = rule.max_value

            # If measured as '< X' where X <= limit, it passes
            if op_sym in ("<", "≤") and val <= limit:
                status = FindingStatus.PASS
                rationale = f"Below limit of quantification ({op_sym}{val}) which satisfies <= {limit}."
            elif val > limit:
                status = FindingStatus.FAIL
                deviation = round(((val - limit) / limit) * 100.0, 2)
                rationale = f"Exceeds upper specification limit of {limit} by +{deviation}% (measured: {val})."
            elif val >= limit * rule.warning_ratio:
                status = FindingStatus.WARN
                pct_limit = round((val / limit) * 100.0, 1)
                rationale = (
                    f"Warning: Reading of {val} is at {pct_limit}% of maximum permissible limit "
                    f"({limit}). Preventative trend drift alert."
                )

        elif rule.operator in (OperatorType.GTE, OperatorType.GT):
            assert rule.min_value is not None, "Rule min_value required for GTE/GT"
            limit = rule.min_value
            if val < limit:
                status = FindingStatus.FAIL
                deviation = round(((limit - val) / limit) * 100.0, 2)
                rationale = f"Sub-potent: Below minimum specification limit of {limit} by -{deviation}% (measured: {val})."
            elif val <= limit * (1.0 + (1.0 - rule.warning_ratio)):
                status = FindingStatus.WARN
                rationale = f"Warning: Reading of {val} is close to lower threshold of {limit}."

        elif rule.operator == OperatorType.BETWEEN:
            assert rule.min_value is not None and rule.max_value is not None
            min_lim, max_lim = rule.min_value, rule.max_value
            if val < min_lim:
                status = FindingStatus.FAIL
                deviation = round(((min_lim - val) / min_lim) * 100.0, 2)
                rationale = f"Out of specification: Below range minimum {min_lim} by -{deviation}%."
            elif val > max_lim:
                status = FindingStatus.FAIL
                deviation = round(((val - max_lim) / max_lim) * 100.0, 2)
                rationale = f"Out of specification: Above range maximum {max_lim} by +{deviation}%."
            else:
                band_width = max_lim - min_lim
                safety_buffer = (1.0 - rule.warning_ratio) * band_width
                if val <= min_lim + safety_buffer:
                    status = FindingStatus.WARN
                    rationale = f"Warning: Value {val} approaching lower threshold of range ({min_lim})."
                elif val >= max_lim - safety_buffer:
                    status = FindingStatus.WARN
                    rationale = f"Warning: Value {val} approaching upper ceiling of range ({max_lim})."

        return status, deviation, rationale

    @staticmethod
    def _format_spec_summary(rule: SpecificationRule) -> str:
        """Render concise human-readable monograph spec summary."""
        if rule.operator == OperatorType.LTE:
            return f"≤ {rule.max_value} {rule.unit}".strip()
        if rule.operator == OperatorType.LT:
            return f"< {rule.max_value} {rule.unit}".strip()
        if rule.operator == OperatorType.GTE:
            return f"≥ {rule.min_value} {rule.unit}".strip()
        if rule.operator == OperatorType.GT:
            return f"> {rule.min_value} {rule.unit}".strip()
        if rule.operator == OperatorType.BETWEEN:
            return f"{rule.min_value} - {rule.max_value} {rule.unit}".strip()
        if rule.operator == OperatorType.EQ:
            return str(rule.expected_text or rule.max_value)
        return "Specification defined"

    def audit_batch(
        self,
        batch_id: str,
        product_name: str,
        specification_name: str,
        measurements: list[ParameterMeasurement],
        rules: list[SpecificationRule],
        dossier: DocumentContent | None = None,
    ) -> AuditReport:
        """Run complete audit lifecycle on a batch against a specification ruleset."""
        findings: list[AuditFinding] = []
        rules_by_name = {r.parameter_name.lower(): r for r in rules}

        for m in measurements:
            rule = rules_by_name.get(m.name.lower())
            if not rule:
                # Fuzzy parameter key match
                for r_name, r_obj in rules_by_name.items():
                    if r_name in m.name.lower() or m.name.lower() in r_name:
                        rule = r_obj
                        break

            if rule:
                finding = self.evaluate_parameter(m, rule, dossier)
                findings.append(finding)

        total_tests = len(findings)
        passed = sum(1 for f in findings if f.status == FindingStatus.PASS)
        warns = sum(1 for f in findings if f.status == FindingStatus.WARN)
        fails = sum(1 for f in findings if f.status == FindingStatus.FAIL)
        unverified = sum(1 for f in findings if f.status == FindingStatus.UNVERIFIED_SOURCE)

        # Verdict logic
        critical_failures = any(
            f.is_critical and f.status in (FindingStatus.FAIL, FindingStatus.UNVERIFIED_SOURCE)
            for f in findings
        )
        if critical_failures or fails > 0:
            verdict = OverallVerdict.REJECTED
        elif warns > 0 or unverified > 0:
            verdict = OverallVerdict.FLAGGED_FOR_REVIEW
        else:
            verdict = OverallVerdict.APPROVED

        compliance_score = round(
            ((passed + 0.5 * warns) / max(total_tests, 1)) * 100.0, 1
        )

        notes = (
            f"Audit completed: {passed}/{total_tests} tests fully conforming. "
            f"{fails} critical failures detected. {warns} trend warnings."
        )

        return AuditReport(
            report_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            batch_id=batch_id,
            product_name=product_name,
            specification_name=specification_name,
            auditor_timestamp=datetime.now(UTC).isoformat(),
            verdict=verdict,
            total_tests=total_tests,
            passed_count=passed,
            warning_count=warns,
            failed_count=fails,
            unverified_count=unverified,
            compliance_score=compliance_score,
            findings=findings,
            summary_notes=notes,
        )

    def audit(
        self,
        batch_id: str,
        product_name: str,
        specification_name: str,
        measurements: list[ParameterMeasurement],
        rules: list[SpecificationRule],
        dossier: DocumentContent | None = None,
    ) -> AuditReport:
        """Alias for audit_batch."""
        return self.audit_batch(
            batch_id=batch_id,
            product_name=product_name,
            specification_name=specification_name,
            measurements=measurements,
            rules=rules,
            dossier=dossier,
        )
