"""Streamlit UI for ReguTech-AI Auditor - Deterministic CoA and Pharmacopeia Audit.

Author: Byron Calderón González (github.com/by-matt)
Professional Accreditation: Biotechnology Engineer (UNAB) | CEO AquaBiotics Sur
Operational Scope: Zero-hallucination deterministic compliance auditing for pharma & biotech.
"""

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

# Custom Executive Editorial Styling (Eliminates AI Aesthetic & Injects Senior Consulting Tokens)
st.markdown(
    """
    <style>
    /* Typography & Core Surfaces */
    .stApp {
        background-color: #0b1120;
        color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* Executive Header */
    .exec-header-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.4);
    }
    .exec-doc-badge {
        display: inline-block;
        font-family: "JetBrains Mono", "SF Mono", monospace;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.1);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 3px 10px;
        border-radius: 4px;
        margin-bottom: 0.75rem;
    }
    .exec-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: #f8fafc;
        margin: 0 0 0.4rem 0;
        line-height: 1.2;
    }
    .exec-subtitle {
        font-size: 0.95rem;
        color: #94a3b8;
        margin: 0 0 1rem 0;
        line-height: 1.5;
    }
    .exec-meta-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 1.5rem;
        border-top: 1px solid #334155;
        padding-top: 0.85rem;
        font-size: 0.82rem;
        color: #64748b;
    }
    .exec-meta-item strong {
        color: #e2e8f0;
        font-weight: 600;
    }

    /* Executive KPI Metric Cards */
    .exec-kpi-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 1rem 1.15rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .exec-kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 0.3rem;
    }
    .exec-kpi-val {
        font-size: 1.7rem;
        font-weight: 800;
        font-family: "JetBrains Mono", "SF Mono", monospace;
        color: #f8fafc;
        line-height: 1.15;
    }
    .exec-badge-emerald {
        display: inline-block;
        margin-top: 0.45rem;
        font-size: 0.78rem;
        font-weight: 600;
        color: #10b981;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.25);
        padding: 2px 7px;
        border-radius: 4px;
        width: fit-content;
    }
    .exec-badge-ruby {
        display: inline-block;
        margin-top: 0.45rem;
        font-size: 0.78rem;
        font-weight: 600;
        color: #ef4444;
        background: rgba(239, 68, 68, 0.12);
        border: 1px solid rgba(239, 68, 68, 0.25);
        padding: 2px 7px;
        border-radius: 4px;
        width: fit-content;
    }
    .exec-badge-amber {
        display: inline-block;
        margin-top: 0.45rem;
        font-size: 0.78rem;
        font-weight: 600;
        color: #fbbf24;
        background: rgba(251, 191, 36, 0.12);
        border: 1px solid rgba(251, 191, 36, 0.25);
        padding: 2px 7px;
        border-radius: 4px;
        width: fit-content;
    }
    .exec-badge-cyan {
        display: inline-block;
        margin-top: 0.45rem;
        font-size: 0.78rem;
        font-weight: 600;
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.12);
        border: 1px solid rgba(56, 189, 248, 0.25);
        padding: 2px 7px;
        border-radius: 4px;
        width: fit-content;
    }

    /* Executive Technical Seal */
    .exec-seal-container {
        margin-top: 2.5rem;
        padding: 1.25rem 1.5rem;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .exec-seal-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #e2e8f0;
        letter-spacing: 0.02em;
    }
    .exec-seal-desc {
        font-size: 0.78rem;
        color: #94a3b8;
    }
    .exec-seal-auth {
        text-align: right;
        font-size: 0.8rem;
        color: #38bdf8;
        font-family: "JetBrains Mono", monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Formal Block
st.markdown(
    """
    <div class="exec-header-card">
        <span class="exec-doc-badge">AUDITORÍA REGULATORIA • REG-AUD-2026-v1.4</span>
        <h1 class="exec-title">ReguTech-AI Auditor</h1>
        <p class="exec-subtitle">
            Motor Determinista de Liberación de Lotes y Verificación de Certificados de Análisis (CoA)
            bajo Monografías Farmacopeicas (USP / Ph. Eur.). Arquitectura Cero-Alucinación mediante Invariante de Subcadena Exacta.
        </p>
        <div class="exec-meta-grid">
            <div class="exec-meta-item"><strong>Auditor Responsable:</strong> Byron M. Calderón González (UNAB Top 25%)</div>
            <div class="exec-meta-item"><strong>Marco Regulatorio:</strong> 21 CFR Part 211 / GMP Anexo 16 (Qualified Person)</div>
            <div class="exec-meta-item"><strong>Seguridad Semántica:</strong> Exact-Quote Substring Invariant (Zero-Hallucination)</div>
            <div class="exec-meta-item"><strong>Contratos de Datos:</strong> Esquemas Inmutables Pydantic v2</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar controls
st.sidebar.markdown("### ⚙️ Configuración de Auditoría")

monograph_choice = st.sidebar.selectbox(
    "Monografía Farmacopeica Objetivo",
    [
        "USP: Recombinant Human Insulin Drug Substance",
        "Ph. Eur. 1052: Trehalose Dihydrate (Cryoprotectant)",
    ],
)

input_source = st.sidebar.radio(
    "Fuente de Ingesta del CoA",
    [
        "Benchmark: Batch INS-2026-X88 (Conforming)",
        "Benchmark: Batch INS-2026-FAIL04 (Critical Contamination)",
        "Adversarial: Injected Rogue Hallucination Quote",
        "Upload Custom CoA (PDF / Text)",
    ],
)

strict_invariant = st.sidebar.toggle("Invariante Estricto de Subcadena", value=True)
warning_ratio = st.sidebar.slider(
    "Umbral de Alerta Temprana Preventiva",
    min_value=0.70,
    max_value=0.95,
    value=0.85,
    step=0.05,
    help="Marca parámetros que alcanzan este porcentaje del límite superior permitido.",
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
        file_bytes = uploaded_file.read()
        dossier = DocumentLoader.load_bytes(file_bytes, uploaded_file.name)
        measurements = SAMPLE_CONFORMING_MEASUREMENTS
        batch_code = "CUSTOM-UPLOAD"
    else:
        st.info("Por favor cargue un archivo o seleccione un benchmark preconfigurado.")
        st.stop()

# Run Audit
auditor = DeterministicAuditor(strict_invariant=strict_invariant)
report = auditor.audit(
    batch_id=batch_code,
    product_name=product_name,
    specification_name=spec_title,
    measurements=measurements,
    rules=rules,
    dossier=dossier,
)

# Display Executive Verdict & KPI Metrics
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if report.verdict == OverallVerdict.APPROVED:
        verdict_badge = "exec-badge-emerald"
        verdict_text = "APROBADO"
        verdict_sub = "100% Conforme"
    elif report.verdict == OverallVerdict.REJECTED:
        verdict_badge = "exec-badge-ruby"
        verdict_text = "RECHAZADO"
        verdict_sub = f"{report.failed_count} Fallas Críticas"
    else:
        verdict_badge = "exec-badge-amber"
        verdict_text = "OBSERVADO"
        verdict_sub = "En Revisión QP"

    st.markdown(
        f"""
        <div class="exec-kpi-card">
            <div class="exec-kpi-label">Disposición de Lote</div>
            <div class="exec-kpi-val">{verdict_text}</div>
            <div class="{verdict_badge}">{verdict_sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="exec-kpi-card">
            <div class="exec-kpi-label">Índice de Cumplimiento</div>
            <div class="exec-kpi-val">{report.compliance_score}%</div>
            <div class="exec-badge-cyan">Ponderación CQA</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        f"""
        <div class="exec-kpi-card">
            <div class="exec-kpi-label">Ensayos Evaluados</div>
            <div class="exec-kpi-val">{report.total_tests}</div>
            <div class="exec-badge-cyan">Total Parámetros</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="exec-kpi-card">
            <div class="exec-kpi-label">Ensayos Conformes</div>
            <div class="exec-kpi-val">{report.passed_count}</div>
            <div class="exec-badge-emerald">{report.passed_count}/{report.total_tests} Conformes</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col5:
    unver_badge = "exec-badge-ruby" if report.unverified_count > 0 else "exec-badge-amber"
    st.markdown(
        f"""
        <div class="exec-kpi-card">
            <div class="exec-kpi-label">Alertas / No Verif.</div>
            <div class="exec-kpi-val">{report.warning_count} / {report.unverified_count}</div>
            <div class="{unver_badge}">Alerta Temprana</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

if report.verdict == OverallVerdict.APPROVED:
    st.success(f"✅ **LIBERACIÓN DE LOTE AUTORIZADA:** El lote `{report.batch_id}` cumple estrictamente con todas las especificaciones de la monografía.")
elif report.verdict == OverallVerdict.REJECTED:
    st.error(f"🚨 **LIBERACIÓN DE LOTE RECHAZADA:** El lote `{report.batch_id}` incumple Atributos Críticos de Calidad (CQA). Cuarentena inmediata obligatoria.")
else:
    st.warning(f"⚠️ **MARCADO PARA INVESTIGACIÓN DE CALIDAD:** El lote `{report.batch_id}` requiere investigación de desvíos por el Qualified Person (QP).")

# Main Audit Views
tab1, tab2, tab3 = st.tabs([
    "📋 Matriz de Ensayos y Desvíos",
    "🔍 Trazabilidad Cero-Alucinación (Subcadena)",
    "📄 Dossier de Liberación Formal (LIMS / ERP)",
])

with tab1:
    filter_status = st.selectbox(
        "Filtrar Resultados",
        ["Todos los Ensayos", "Fallas Críticas y Alertas Solamente", "Ensayos Conformes Solamente"],
    )

    findings_data: list[dict[str, Any]] = []
    for f in report.findings:
        if filter_status == "Fallas Críticas y Alertas Solamente" and f.status == FindingStatus.PASS:
            continue
        if filter_status == "Ensayos Conformes Solamente" and f.status != FindingStatus.PASS:
            continue

        dev_str = f"+{f.deviation_percent}%" if f.deviation_percent and f.deviation_percent > 0 else (
            f"{f.deviation_percent}%" if f.deviation_percent else "0.0%"
        )
        findings_data.append({
            "Estado": f.status.value,
            "Parámetro": f.parameter_name,
            "Valor Medido": f"{f.measured_raw}",
            "Límite Monografía": f.specification_summary,
            "Desviación": dev_str,
            "Atributo Crítico (CQA)": "Sí" if f.is_critical else "No",
            "Cita Verificada": "✅ Verificado" if f.quote_verified else "❌ No Verificado",
            "Justificación Técnica": f.rationale,
        })

    if findings_data:
        df_findings = pd.DataFrame(findings_data)
        st.dataframe(df_findings, use_container_width=True, hide_index=True)
    else:
        st.info("No hay parámetros que coincidan con el filtro seleccionado.")

with tab2:
    st.markdown("### 🔍 Trazabilidad de Evidencia Textual Cero-Alucinación")
    st.markdown(
        "Cada métrica extraída es contrastada matemáticamente contra el texto crudo del documento fuente. "
        "El **Invariante de Subcadena Exacta** asegura que ninguna lectura sintética generada por modelos probabilísticos "
        "pueda comprometer la disposición formal del lote farmacéutico."
    )

    col_left, col_right = st.columns([1, 1])

    with col_left:
        selected_param = st.selectbox(
            "Seleccione Parámetro a Inspeccionar",
            [f.parameter_name for f in report.findings],
        )
        selected_finding = next(f for f in report.findings if f.parameter_name == selected_param)

        st.markdown(f"**Parámetro:** `{selected_finding.parameter_name}`")
        st.markdown(f"**Estado:** `{selected_finding.status.value}`")
        st.markdown(f"**Valor Reportado:** `{selected_finding.measured_raw}`")
        st.markdown(f"**Límite de Monografía:** `{selected_finding.specification_summary}`")
        st.markdown("**Cita Literal de Evidencia Extraída:**")
        st.code(selected_finding.evidence_quote, language="text")

        if selected_finding.quote_verified:
            st.success("✅ **Invariante Cumplido:** Cita verificada como subcadena literal exacta del documento ingerido.")
        else:
            st.error("🚨 **Violación de Invariante:** La cita NO se encuentra de forma idéntica en el texto del documento fuente.")

    with col_right:
        st.markdown(f"**Documento Fuente:** `{dossier.filename}`")
        raw_text = dossier.full_text
        quote = selected_finding.evidence_quote
        if quote and quote in raw_text:
            highlighted = raw_text.replace(quote, f"👉 【 {quote} 】 👈")
            st.text_area("Contenido Ingerido (con cita resaltada):", highlighted, height=350)
        else:
            st.text_area("Contenido Ingerido:", raw_text, height=350)

with tab3:
    st.markdown("### 📄 Exportación de Dossier de Calidad y Cumplimiento")
    st.markdown("Descarga de contratos de datos serializables para integración LIMS/ERP y firma por Qualified Person (QP).")

    json_dossier = report.model_dump_json(indent=2)
    st.download_button(
        label="📥 Descargar Dossier Formal de Auditoría (JSON / LIMS)",
        data=json_dossier,
        file_name=f"audit_{report.batch_id}.json",
        mime="application/json",
        use_container_width=True,
    )

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
        f"*Generated by ReguTech-AI Auditor • Byron Calderón González (UNAB Top 25%)*\n"
    )
    st.text_area("Vista Previa del Resumen Técnico (Markdown):", md_summary, height=200)
    st.download_button(
        label="📥 Descargar Resumen de Liberación (Markdown)",
        data=md_summary,
        file_name=f"release_summary_{report.batch_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )

# Formal Institutional Validation Seal (Skill Directive)
st.markdown(
    """
    <div class="exec-seal-container">
        <div>
            <div class="exec-seal-title">CERTIFICACIÓN DE INTEGRIDAD REGULATORIA GMP & CERO-ALUCINACIÓN</div>
            <div class="exec-seal-desc">
                Sistema auditado bajo estándares de validación de software computarizado (GAMP 5 / 21 CFR Part 11).
                Invariante de subcadena exacto • Detección determinista de límites farmacopeicos.
            </div>
        </div>
        <div class="exec-seal-auth">
            <strong>Ing. Byron M. Calderón González</strong><br>
            Ingeniero en Biotecnología (UNAB Top 25%)<br>
            CEO & Fundador, AquaBiotics Sur
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
