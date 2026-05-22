from comp.compiler_tool import (
    ClaimCandidate,
    CheckedClaim,
    ValidationReport,
    CompilerTool,
    EvidenceRef,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    ValidationRequirement,
    UnknownClaim,
    UncheckedArea,
)

TINY_KNOWN_FIELDS = frozenset({"activity", "amount", "unit", "reporting_year"})


def _hypothesis(*, claims, witnesses=()):
    return InterpretationHypothesis(
        hypothesis_id="hyp-1",
        subject_id="draft-1",
        claims=tuple(claims),
        witnesses=tuple(witnesses),
    )


def _claim(field, value, witness_id=None):
    return ClaimCandidate(
        field=field,
        value=value,
        witness_id=witness_id,
        origin="llm_inferred",
    )


def _witness(witness_id, field, *, source="invoice.csv", span="A1"):
    return EvidenceRef(
        witness_id=witness_id,
        field=field,
        source=source,
        span=span,
    )


def test_compiler_tool_contract_model_set_is_exported():
    assert InterpretationHypothesis is not None
    assert ClaimCandidate is not None
    assert EvidenceRef is not None
    assert ValidationReport is not None
    assert CheckedClaim is not None
    assert FailedClaim is not None
    assert UnknownClaim is not None
    assert UncheckedArea is not None
    assert ValidationRequirement is not None
    assert Hazard is not None


def test_friendly_intake_validation_names_are_canonical():
    from comp.compiler_tool import (
        ClaimCandidate,
        EvidenceRef,
        ValidationRequirement,
        evidence_ref_fingerprint,
    )

    claim = ClaimCandidate(field="amount", value=1200, witness_id="w-amount")
    witness = EvidenceRef(
        witness_id="w-amount",
        field="amount",
        source="invoice.csv",
    )
    requirement = ValidationRequirement(
        kind="find_source_witness",
        field="amount",
        reason="missing_source_witness",
    )
    report = ValidationReport(
        status="review_required",
        evidence_refs=(witness,),
        validation_requirements=(requirement,),
        resolved_validation_requirements=(),
    )

    assert type(claim).__name__ == "ClaimCandidate"
    assert type(witness).__name__ == "EvidenceRef"
    assert type(requirement).__name__ == "ValidationRequirement"
    assert report.evidence_refs == (witness,)
    assert report.validation_requirements == (requirement,)
    assert report.resolved_validation_requirements == ()
    assert evidence_ref_fingerprint(witness).dependency_kind == "evidence_witness"


def test_friendly_reference_calculation_report_names_are_canonical():
    from comp.compiler_tool import (
        CalculatedClaim,
        CanonicalReference,
        CalculationTrace,
        ReferenceOption,
        ValidationReport,
    )

    option = ReferenceOption(
        candidate_id="candidate-1",
        reference_id="factor.kr.2024",
        reference_type="emission_factor",
        retrieval_method="profile_rule",
    )
    reference = CanonicalReference(
        binding_id="binding-1",
        claim_id="claim:electricity",
        reference_id="factor.kr.2024",
        reference_type="emission_factor",
    )
    calculated = CalculatedClaim(
        claim_id="claim:co2e",
        field="co2e_kg",
        value=1200,
        unit="kg",
        trace=CalculationTrace(trace_id="trace-1", formula_id="formula:co2e"),
    )
    report = ValidationReport(
        status="accepted",
        reference_options=(option,),
        canonical_references=(reference,),
        calculated_claims=(calculated,),
    )

    assert type(option).__name__ == "ReferenceOption"
    assert type(reference).__name__ == "CanonicalReference"
    assert type(calculated).__name__ == "CalculatedClaim"
    assert type(report).__name__ == "ValidationReport"
    assert report.reference_options == (option,)
    assert report.canonical_references == (reference,)
    assert report.calculated_claims == (calculated,)
    assert option.can_authorize_calculation is False
    assert reference.can_authorize_calculation is True
    assert calculated.can_authorize_public_projection is False


def test_compiler_tool_has_no_domain_known_fields_by_default():
    report = CompilerTool().compile_interpretation(
        _hypothesis(
            claims=(
                _claim("activity", "electricity", "w-activity"),
            ),
            witnesses=(_witness("w-activity", "activity"),),
        )
    )

    assert report.status == "unchecked"
    assert report.checked_claims == ()
    assert report.unchecked_areas == (
        UncheckedArea(field="activity", reason="missing_rule_coverage"),
    )


def test_unsupported_unit_blocks_and_requests_source_witness():
    report = CompilerTool(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    ).compile_interpretation(
        _hypothesis(
            claims=(
                _claim("activity", "electricity", "w-activity"),
                _claim("amount", 1200, "w-amount"),
                _claim("unit", "mwh", "w-unit"),
            ),
            witnesses=(
                _witness("w-activity", "activity"),
                _witness("w-amount", "amount"),
                _witness("w-unit", "unit"),
            ),
        )
    )

    assert report.status == "blocked"
    assert [failed.field for failed in report.failed_claims] == ["unit"]
    assert report.failed_claims[0].reason == "unsupported_unit"
    assert any(
        obligation.kind == "find_source_witness" and obligation.field == "unit"
        for obligation in report.validation_requirements
    )
    assert report.can_build_public_output is False


def test_witness_id_must_resolve_to_grounded_matching_witness():
    tool = CompilerTool(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    )

    cases = [
        ((), "missing_source_witness"),
        ((_witness("w-amount", "unit"),), "witness_field_mismatch"),
        ((_witness("w-amount", "amount", source=None, span=None),), "ungrounded_source_witness"),
    ]

    for witnesses, expected_reason in cases:
        report = tool.compile_interpretation(
            _hypothesis(
                claims=(
                    _claim("amount", 1200, "w-amount"),
                    _claim("unit", "kwh", "w-unit"),
                ),
                witnesses=(*witnesses, _witness("w-unit", "unit")),
            )
        )

        assert report.status == "blocked"
        assert report.failed_claims[0].field == "amount"
        assert report.failed_claims[0].reason == expected_reason
        assert any(
            obligation.kind == "find_source_witness" and obligation.field == "amount"
            for obligation in report.validation_requirements
        )


def test_unknown_and_unchecked_are_distinct_and_not_pass():
    report = CompilerTool(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    ).compile_interpretation(
        _hypothesis(
            claims=(
                _claim("reporting_year", None),
                _claim("factor_period_compatibility", "jan-2026-factor"),
                _claim("unit", "kwh", "w-unit"),
            ),
            witnesses=(_witness("w-unit", "unit"),),
        )
    )

    assert report.status == "unchecked"
    assert report.unknowns == (
        UnknownClaim(field="reporting_year", reason="context_required"),
    )
    assert report.unchecked_areas == (
        UncheckedArea(
            field="factor_period_compatibility",
            reason="missing_rule_coverage",
        ),
    )
    assert [claim.field for claim in report.checked_claims] == ["unit"]
    assert report.can_build_public_output is False


def test_missing_unit_is_review_required_hazard_not_public_projection():
    report = CompilerTool(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    ).compile_interpretation(
        _hypothesis(
            claims=(
                _claim("activity", "electricity", "w-activity"),
                _claim("amount", 1200, "w-amount"),
            ),
            witnesses=(
                _witness("w-activity", "activity"),
                _witness("w-amount", "amount"),
            ),
        )
    )

    assert report.status == "review_required"
    assert report.failed_claims == ()
    assert report.hazards == (
        Hazard(kind="missing_unit", field="unit", severity="review"),
    )
    assert any(
        obligation.kind == "find_source_witness" and obligation.field == "unit"
        for obligation in report.validation_requirements
    )
    assert report.can_build_public_output is False


def test_accepted_report_is_not_public_projection_authority():
    report = CompilerTool(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    ).compile_interpretation(
        _hypothesis(
            claims=(
                _claim("activity", "electricity", "w-activity"),
                _claim("amount", 1200, "w-amount"),
                _claim("unit", "kwh", "w-unit"),
            ),
            witnesses=(
                _witness("w-activity", "activity"),
                _witness("w-amount", "amount"),
                _witness("w-unit", "unit"),
            ),
        )
    )

    assert report.status == "accepted"
    assert [claim.field for claim in report.checked_claims] == [
        "activity",
        "amount",
        "unit",
    ]
    assert report.can_build_public_output is False
