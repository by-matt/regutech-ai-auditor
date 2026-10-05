"""Streamlit UI for ReguTech-AI Auditor - Deterministic CoA and Pharmacopeia Audit."""

from typing import Any
import pandas as pd
import streamlit as st

from src.data.monographs import (
    PH_EUR_TREHALOSE_RULES,
    SAMPLE_COA_CONFORMING_TEXT,
    SAMPLE_COA_NON_CONFORMING_TEXT,
    SAMPLE_CONFORMING_MEASUREMENTS,
    SAMPLE_NON_CONFORMING_MEASUREMENTS,
    USP_INSULIN_RULES,
)
from src.engine.deterministic_auditor import DeterministicAuditor
from src.parser.document_loader import DocumentContent, DocumentLoader
from src.schemas.audit_models import (
    FindingStatus,
    OverallVerdict,
    ParameterMeasurement,
    SpecificationRule,
)

st.set_page_config(
    page_title="ReguTech-AI Auditor | Biotech & Pharma Compliance",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .badge-pass { background-color: #DCFCE7; color: #166534; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    .badge-fail { background-color: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    .badge-warn { background-color: #FEF3C7; color: #92400E; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    .badge-unverified { background-color: #EDE9FE; color: #5B21B6; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-header">⚖️ ReguTech-AI Auditor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">'
    "Deterministic Zero-Hallucination Regulatory Compliance Engine for Certificates of Analysis (CoA) & GMP Monographs.<br>"
    "<b>Architecture:</b> Exact-Quote Substring Invariant • Pydantic v2 Contracts • Closed-Loop QA Gatekeeper."
    "</div>",
    unsafe_allow_html=True,
)

# Sidebar controls
st.sidebar.header("⚙️ Audit Configuration")

monograph_choice = st.sidebar.selectbox(
    "Target Regulatory Monograph",
    [
        "USP: Recombinant Human Insulin Drug Substance",
        "Ph. Eur. 1052: Trehalose Dihydrate (Cryoprotectant)",
    ],
)

input_source = st.sidebar.radio(
    "CoA Ingestion Source",
    [
        "Benchmark: Batch INS-2026-X88 (Conforming)",
        "Benchmark: Batch INS-2026-FAIL04 (Critical Contamination)",
        "Adversarial: Injected Rogue Hallucination Quote",
        "Upload Custom CoA (PDF / Text)",
    ],
)

strict_invariant = st.sidebar.toggle("Strict Substring Invariant", value=True)
warning_ratio = st.sidebar.slider(
    "Preventative Warning Threshold",
    min_value=0.70,
    max_value=0.95,
    value=0.85,
    step=0.05,
    help="Flags parameters reaching this ratio of permissible upper limit.",
)

# Resolve rules
rules: list[SpecificationRule] = []
spec_title = ""
if "Insulin" in monograph_choice:
    rules = USP_INSULIN_RULES
    spec_title = "USP Monograph: Recombinant Human Insulin Drug Substance"
else:
    rules = PH_EUR_TREHALOSE_RULES
    spec_title = "Ph. Eur. 1052: Trehalose Dihydrate"

# Update warning ratio in rules
for r in rules:
    r.warning_ratio = warning_ratio

# Resolve sample data
dossier: DocumentContent
measurements: list[ParameterMeasurement]
batch_code = "INS-2026-X88"
product_name = "Recombinant Human Insulin Drug Substance"

if input_source == "Benchmark: Batch INS-2026-X88 (Conforming)":
    dossier = DocumentLoader.load_text(SAMPLE_COA_CONFORMING_TEXT, "CoA_INS-2026-X88.txt")
    measurements = SAMPLE_CONFORMING_MEASUREMENTS
    batch_code = "INS-2026-X88"

elif input_source == "Benchmark: Batch INS-2026-FAIL04 (Critical Contamination)":
    dossier = DocumentLoader.load_text(SAMPLE_COA_NON_CONFORMING_TEXT, "CoA_INS-2026-FAIL04.txt")
    measurements = SAMPLE_NON_CONFORMING_MEASUREMENTS
    batch_code = "INS-2026-FAIL04"

elif input_source == "Adversarial: Injected Rogue Hallucination Quote":
    dossier = DocumentLoader.load_text(SAMPLE_COA_CONFORMING_TEXT, "CoA_INS-2026-X88.txt")
    # Clone and inject a fake quote
    measurements = [
        ParameterMeasurement(
            name="Appearance",
            raw_value="White powder",
            numeric_value=None,
            unit="",
            test_method="Visual",
            evidence_quote="Synthetic claim not present in original document",
            page_number=1,
        ),
        *SAMPLE_CONFORMING_MEASUREMENTS[1:],
    ]
    batch_code = "INS-2026-ADV01"

else:
    uploaded_file = st.sidebar.file_uploader("Upload CoA File", type=["pdf", "txt"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".pdf"):
            dossier = DocumentLoader.load_pdf(uploaded_file.getvalue(), uploaded_file.name)
        else:
            raw_txt = uploaded_file.getvalue().decode("utf-8")
            dossier = DocumentLoader.load_text(raw_txt, uploaded_file.name)
        measurements = SAMPLE_CONFORMING_MEASUREMENTS  # Template match
        batch_code = uploaded_file.name.split(".")[0]
    else:
        st.info("👈 Upload a CoA document in the sidebar to begin, or use one of the benchmark controls.")
        dossier = DocumentLoader.load_text(SAMPLE_COA_CONFORMING_TEXT, "CoA_INS-2026-X88.txt")
        measurements = SAMPLE_CONFORMING_MEASUREMENTS

# Run Deterministic Audit
auditor = DeterministicAuditor(strict_verification=strict_invariant)
report = auditor.audit_batch(
    batch_id=batch_code,
    product_name=product_name,
    specification_name=spec_title,
    measurements=measurements,
    rules=rules,
    dossier=dossier,
)

# Display Executive Verdict
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if report.verdict == OverallVerdict.APPROVED:
        st.metric("Batch Disposition", "APPROVED", delta="100% Conforming", delta_color="normal")
    elif report.verdict == OverallVerdict.REJECTED:
        st.metric("Batch Disposition", "REJECTED", delta=f"{report.failed_count} Critical Fails", delta_color="inverse")
    else:
        st.metric("Batch Disposition", "FLAGGED", delta="Under QA Review", delta_color="off")

with col2:
    st.metric("Compliance Score", f"{report.compliance_score}%")

with col3:
    st.metric("Tests Evaluated", f"{report.total_tests}")

with col4:
    st.metric("Passing Tests", f"{report.passed_count}", delta=f"{report.passed_count}/{report.total_tests}")

with col5:
    unver_delta = f"{report.unverified_count} Unverified" if report.unverified_count > 0 else "0 Unverified"
    st.metric("Warnings / Unverified", f"{report.warning_count} Warn", delta=unver_delta, delta_color="inverse" if report.unverified_count > 0 else "off")

if report.verdict == OverallVerdict.APPROVED:
    st.success(f"✅ **BATCH RELEASE AUTHORIZED:** Batch `{report.batch_id}` complies with all monograph specifications.")
elif report.verdict == OverallVerdict.REJECTED:
    st.error(f"🚨 **BATCH RELEASE REJECTED:** Batch `{report.batch_id}` failed critical quality attributes. Immediate quarantine required.")
else:
    st.warning(f"⚠️ **FLAGGED FOR QA INVESTIGATION:** Batch `{report.batch_id}` requires deviation review by Qualified Person (QP).")

st.markdown("---")

# Main Audit Views
tab1, tab2, tab3 = st.tabs(["📋 Audit Findings Matrix", "🔍 Evidence Traceability Inspector", "📄 Export Dossier (LIMS/ERP)"])

with tab1:
    filter_status = st.selectbox(
        "Filter Findings",
        ["All Tests", "Critical Failures & Alerts Only", "Passing Tests Only"],
    )

    findings_data: list[dict[str, Any]] = []
    for f in report.findings:
        if filter_status == "Critical Failures & Alerts Only" and f.status == FindingStatus.PASS:
            continue
        if filter_status == "Passing Tests Only" and f.status != FindingStatus.PASS:
            continue

        dev_str = f"+{f.deviation_percent}%" if f.deviation_percent and f.deviation_percent > 0 else (
            f"{f.deviation_percent}%" if f.deviation_percent else "0.0%"
        )
        findings_data.append({
            "Status": f.status.value,
            "Parameter": f.parameter_name,
            "Measured Value": f"{f.measured_raw}",
            "Monograph Spec": f.specification_summary,
            "Deviation": dev_str,
            "Critical Attribute (CQA)": "Yes" if f.is_critical else "No",
            "Quote Verified": "✅ Verified" if f.quote_verified else "❌ Unverified",
            "Rationale": f.rationale,
        })

    if findings_data:
        df_findings = pd.DataFrame(findings_data)
        st.dataframe(df_findings, use_container_width=True, hide_index=True)
    else:
        st.info("No parameters match the selected filter.")

with tab2:
    st.markdown("### 🔍 Zero-Hallucination Evidence Traceability")
    st.markdown(
        "Every extracted metric is verified against the raw ingested document text. "
        "The **Exact-Quote Substring Invariant** ensures that no hallucinated readings can compromise the batch disposition."
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        selected_param = st.selectbox(
            "Select Parameter to Inspect",
            [f.parameter_name for f in report.findings],
        )
        selected_finding = next(f for f in report.findings if f.parameter_name == selected_param)

        st.markdown(f"**Parameter:** `{selected_finding.parameter_name}`")
        st.markdown(f"**Status:** `{selected_finding.status.value}`")
        st.markdown(f"**Reported Value:** `{selected_finding.measured_raw}`")
        st.markdown(f"**Monograph Limit:** `{selected_finding.specification_summary}`")
        st.markdown("**Evidence Quote:**")
        st.code(selected_finding.evidence_quote, language="text")

        if selected_finding.quote_verified:
            st.success("✅ **Invariant Satisfied:** Quote verified as literal substring of ingested document.")
        else:
            st.error("🚨 **Invariant Violation:** Quote could NOT be matched to ingested document.")

    with col_right:
        st.markdown(f"**Source Document:** `{dossier.filename}`")
        # Highlight evidence in raw text
        raw_text = dossier.full_text
        quote = selected_finding.evidence_quote
        if quote and quote in raw_text:
            highlighted = raw_text.replace(quote, f"👉 【 {quote} 】 👈")
            st.text_area("Ingested Document Content (with target highlighted):", highlighted, height=350)
        else:
            st.text_area("Ingested Document Content:", raw_text, height=350)

with tab3:
    st.markdown("### 📄 Quality Release Dossier Export")
    st.markdown("Download compliant data contracts for LIMS / ERP integration or QA sign-off.")

    json_dossier = report.model_dump_json(indent=2)
    st.download_button(
        label="📥 Download Formal Audit Dossier (JSON / LIMS)",
        data=json_dossier,
        file_name=f"audit_{report.batch_id}.json",
        mime="application/json",
    )

    # Markdown QA summary preview
    md_summary = (
        f"# Certificate of Analysis Audit Release Summary\n\n"
        f"**Batch ID:** {report.batch_id}\n\n"
        f"**Product:** {report.product_name}\n\n"
        f"**Regulatory Specification:** {report.specification_name}\n\n"
        f"**Disposition Verdict:** {report.verdict.value}\n\n"
        f"**Compliance Score:** {report.compliance_score}%\n\n"
        f"**Auditor Signature:** Automated Closed-Loop ReguTech Invariant Auditor\n\n"
        f"**Timestamp (UTC):** {report.auditor_timestamp}\n\n"
        f"## Summary of Findings:\n"
        f"- Total Parameters Tested: {report.total_tests}\n"
        f"- Parameters Passing: {report.passed_count}\n"
        f"- Preventative Warnings: {report.warning_count}\n"
        f"- Critical Specification Failures: {report.failed_count}\n"
        f"- Unverified Evidence Quotes: {report.unverified_count}\n\n"
        f"---\n"
        f"*Generated by ReguTech-AI Auditor • Byron Calderón González*\n"
    )
    st.text_area("Markdown Dossier Preview:", md_summary, height=200)
    st.download_button(
        label="📥 Download QC Release Summary (Markdown)",
        data=md_summary,
        file_name=f"release_summary_{report.batch_id}.md",
        mime="text/markdown",
    )
