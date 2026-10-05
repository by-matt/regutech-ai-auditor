"""Reference monographs and synthetic control CoAs for audit testing."""

from src.schemas.audit_models import (
    OperatorType,
    ParameterMeasurement,
    SpecificationRule,
)

USP_INSULIN_RULES: list[SpecificationRule] = [
    SpecificationRule(
        parameter_name="Appearance",
        operator=OperatorType.EQ,
        expected_text="White or almost white powder",
        unit="",
        regulatory_reference="USP <621>",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Assay (HPLC)",
        operator=OperatorType.BETWEEN,
        min_value=95.0,
        max_value=105.0,
        unit="%",
        warning_ratio=0.96,
        regulatory_reference="USP Monograph: Insulin",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="High Molecular Weight Proteins (HMWP)",
        operator=OperatorType.LTE,
        max_value=1.00,
        unit="%",
        warning_ratio=0.85,
        regulatory_reference="USP <621> SEC-HPLC",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Related Proteins (A21 Deamido)",
        operator=OperatorType.LTE,
        max_value=1.50,
        unit="%",
        warning_ratio=0.85,
        regulatory_reference="USP RP-HPLC",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Bacterial Endotoxins",
        operator=OperatorType.LTE,
        max_value=10.0,
        unit="EU/mg",
        warning_ratio=0.80,
        regulatory_reference="USP <85> LAL Test",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Heavy Metals (Pb)",
        operator=OperatorType.LTE,
        max_value=10.0,
        unit="ppm",
        warning_ratio=0.80,
        regulatory_reference="USP <232> ICP-MS",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Water Content (Karl Fischer)",
        operator=OperatorType.LTE,
        max_value=10.0,
        unit="%",
        warning_ratio=0.85,
        regulatory_reference="USP <921> Method 1c",
        is_critical=False,
    ),
    SpecificationRule(
        parameter_name="Bioburden / Microbial Enumeration",
        operator=OperatorType.LTE,
        max_value=100.0,
        unit="CFU/g",
        warning_ratio=0.80,
        regulatory_reference="USP <61>",
        is_critical=True,
    ),
]

PH_EUR_TREHALOSE_RULES: list[SpecificationRule] = [
    SpecificationRule(
        parameter_name="Appearance",
        operator=OperatorType.EQ,
        expected_text="White crystalline powder",
        unit="",
        regulatory_reference="Ph. Eur. 1052",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Specific Optical Rotation",
        operator=OperatorType.BETWEEN,
        min_value=197.0,
        max_value=201.0,
        unit="deg",
        regulatory_reference="Ph. Eur. 2.2.7",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Assay (HPLC)",
        operator=OperatorType.GTE,
        min_value=98.0,
        unit="%",
        warning_ratio=0.985,
        regulatory_reference="Ph. Eur. 2.2.29",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Heavy Metals",
        operator=OperatorType.LTE,
        max_value=5.0,
        unit="ppm",
        warning_ratio=0.80,
        regulatory_reference="Ph. Eur. 2.4.8",
        is_critical=True,
    ),
    SpecificationRule(
        parameter_name="Bacterial Endotoxins",
        operator=OperatorType.LTE,
        max_value=2.5,
        unit="EU/g",
        warning_ratio=0.80,
        regulatory_reference="Ph. Eur. 2.6.14",
        is_critical=True,
    ),
]

SAMPLE_COA_CONFORMING_TEXT = """CERTIFICATE OF ANALYSIS
Manufacturer: BioPharma Synthesis Labs S.A.
Product: Recombinant Human Insulin Drug Substance
Batch Number: INS-2026-X88
Date of Manufacture: 2026-09-15
Expiry Date: 2028-09-14
Release Specification: USP Monograph Standards

ANALYTICAL TEST RESULTS:
1. Appearance: White or almost white powder | Complies
2. Assay (HPLC): 99.4% (Specification: 95.0% - 105.0%) | Method: USP <621>
3. High Molecular Weight Proteins (HMWP): 0.42% (Specification: <= 1.00%) | Method: SEC-HPLC
4. Related Proteins (A21 Deamido): 0.65% (Specification: <= 1.50%) | Method: RP-HPLC
5. Bacterial Endotoxins: < 0.05 EU/mg (Specification: <= 10.0 EU/mg) | Method: USP <85> Turbidimetric
6. Heavy Metals (Pb): 1.8 ppm (Specification: <= 10.0 ppm) | Method: ICP-MS USP <232>
7. Water Content (Karl Fischer): 6.2% (Specification: <= 10.0%) | Method: USP <921>
8. Bioburden / Microbial Enumeration: < 10 CFU/g (Specification: <= 100 CFU/g) | Method: USP <61>

Quality Assurance Conclusion:
All tested parameters satisfy USP acceptance criteria. Batch INS-2026-X88 meets quality requirements.
Approved by: Dr. E. Vance, Head of QC Release.
"""

SAMPLE_COA_NON_CONFORMING_TEXT = """CERTIFICATE OF ANALYSIS
Manufacturer: BioPharma Synthesis Labs S.A.
Product: Recombinant Human Insulin Drug Substance
Batch Number: INS-2026-FAIL04
Date of Manufacture: 2026-09-28
Expiry Date: 2028-09-27
Release Specification: USP Monograph Standards

ANALYTICAL TEST RESULTS:
1. Appearance: White or almost white powder | Complies
2. Assay (HPLC): 97.1% (Specification: 95.0% - 105.0%) | Method: USP <621>
3. High Molecular Weight Proteins (HMWP): 0.92% (Specification: <= 1.00%) | Method: SEC-HPLC
4. Related Proteins (A21 Deamido): 1.10% (Specification: <= 1.50%) | Method: RP-HPLC
5. Bacterial Endotoxins: 14.8 EU/mg (Specification: <= 10.0 EU/mg) | Method: USP <85> Turbidimetric
6. Heavy Metals (Pb): 16.5 ppm (Specification: <= 10.0 ppm) | Method: ICP-MS USP <232>
7. Water Content (Karl Fischer): 7.4% (Specification: <= 10.0%) | Method: USP <921>
8. Bioburden / Microbial Enumeration: 145 CFU/g (Specification: <= 100 CFU/g) | Method: USP <61>

Quality Assurance Observation:
Discrepancy detected during purification step 4. High endotoxin load and bioburden alert.
Status: Under QA Investigation.
"""

SAMPLE_CONFORMING_MEASUREMENTS: list[ParameterMeasurement] = [
    ParameterMeasurement(
        name="Appearance",
        raw_value="White or almost white powder",
        numeric_value=None,
        unit="",
        test_method="Visual Inspection",
        evidence_quote="Appearance: White or almost white powder | Complies",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Assay (HPLC)",
        raw_value="99.4%",
        numeric_value=99.4,
        unit="%",
        test_method="USP <621>",
        evidence_quote="Assay (HPLC): 99.4%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="High Molecular Weight Proteins (HMWP)",
        raw_value="0.42%",
        numeric_value=0.42,
        unit="%",
        test_method="SEC-HPLC",
        evidence_quote="High Molecular Weight Proteins (HMWP): 0.42%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Related Proteins (A21 Deamido)",
        raw_value="0.65%",
        numeric_value=0.65,
        unit="%",
        test_method="RP-HPLC",
        evidence_quote="Related Proteins (A21 Deamido): 0.65%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Bacterial Endotoxins",
        raw_value="< 0.05 EU/mg",
        numeric_value=0.05,
        unit="EU/mg",
        test_method="USP <85>",
        evidence_quote="Bacterial Endotoxins: < 0.05 EU/mg",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Heavy Metals (Pb)",
        raw_value="1.8 ppm",
        numeric_value=1.8,
        unit="ppm",
        test_method="ICP-MS USP <232>",
        evidence_quote="Heavy Metals (Pb): 1.8 ppm",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Water Content (Karl Fischer)",
        raw_value="6.2%",
        numeric_value=6.2,
        unit="%",
        test_method="USP <921>",
        evidence_quote="Water Content (Karl Fischer): 6.2%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Bioburden / Microbial Enumeration",
        raw_value="< 10 CFU/g",
        numeric_value=10.0,
        unit="CFU/g",
        test_method="USP <61>",
        evidence_quote="Bioburden / Microbial Enumeration: < 10 CFU/g",
        page_number=1,
    ),
]

SAMPLE_NON_CONFORMING_MEASUREMENTS: list[ParameterMeasurement] = [
    ParameterMeasurement(
        name="Appearance",
        raw_value="White or almost white powder",
        numeric_value=None,
        unit="",
        test_method="Visual Inspection",
        evidence_quote="Appearance: White or almost white powder | Complies",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Assay (HPLC)",
        raw_value="97.1%",
        numeric_value=97.1,
        unit="%",
        test_method="USP <621>",
        evidence_quote="Assay (HPLC): 97.1%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="High Molecular Weight Proteins (HMWP)",
        raw_value="0.92%",
        numeric_value=0.92,
        unit="%",
        test_method="SEC-HPLC",
        evidence_quote="High Molecular Weight Proteins (HMWP): 0.92%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Related Proteins (A21 Deamido)",
        raw_value="1.10%",
        numeric_value=1.10,
        unit="%",
        test_method="RP-HPLC",
        evidence_quote="Related Proteins (A21 Deamido): 1.10%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Bacterial Endotoxins",
        raw_value="14.8 EU/mg",
        numeric_value=14.8,
        unit="EU/mg",
        test_method="USP <85>",
        evidence_quote="Bacterial Endotoxins: 14.8 EU/mg",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Heavy Metals (Pb)",
        raw_value="16.5 ppm",
        numeric_value=16.5,
        unit="ppm",
        test_method="ICP-MS USP <232>",
        evidence_quote="Heavy Metals (Pb): 16.5 ppm",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Water Content (Karl Fischer)",
        raw_value="7.4%",
        numeric_value=7.4,
        unit="%",
        test_method="USP <921>",
        evidence_quote="Water Content (Karl Fischer): 7.4%",
        page_number=1,
    ),
    ParameterMeasurement(
        name="Bioburden / Microbial Enumeration",
        raw_value="145 CFU/g",
        numeric_value=145.0,
        unit="CFU/g",
        test_method="USP <61>",
        evidence_quote="Bioburden / Microbial Enumeration: 145 CFU/g",
        page_number=1,
    ),
]
