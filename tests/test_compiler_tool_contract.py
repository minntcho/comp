from comp.compiler_tool import (
    ClaimHypothesis,
    CheckedClaim,
    CompileReport,
    CompilerTool,
    EvidenceWitness,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    ProofObligation,
    UnknownClaim,
    UncheckedArea,
)


def _hypothesis(*, claims, witnesses=()):
    return InterpretationHypothesis(
        hypothesis_id="hyp-1",
        subject_id="draft-1",
        claims=tuple(claims),
        witnesses=tuple(witnesses),
    )


def _claim(field, value, witness_id=None):
    return ClaimHypothesis(
        field=field,
        value=value,
        witness_id=witness_id,
        origin="llm_inferred",
    )


def _witness(witness_id, field, *, source="invoice.csv", span="A1"):
    return EvidenceWitness(
        witness_id=witness_id,
        field=field,
        source=source,
        span=span,
    )


def test_compiler_tool_contract_model_set_is_exported():
    assert InterpretationHypothesis is not None
    assert ClaimHypothesis is not None
    assert EvidenceWitness is not None
    assert CompileReport is not None
    assert CheckedClaim is not None
    assert FailedClaim is not None
    assert UnknownClaim is not None
    assert UncheckedArea is not None
    assert ProofObligation is not None
    assert Hazard is not None


def test_unsupported_unit_blocks_and_requests_source_witness():
    report = CompilerTool(allowed_units=frozenset({"kwh"})).compile_interpretation(
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
        for obligation in report.obligations
    )
    assert report.can_project_public_row is False


def test_witness_id_must_resolve_to_grounded_matching_witness():
    tool = CompilerTool(allowed_units=frozenset({"kwh"}))

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
            for obligation in report.obligations
        )


def test_unknown_and_unchecked_are_distinct_and_not_pass():
    report = CompilerTool(allowed_units=frozenset({"kwh"})).compile_interpretation(
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
    assert report.can_project_public_row is False


def test_missing_unit_is_review_required_hazard_not_public_projection():
    report = CompilerTool(allowed_units=frozenset({"kwh"})).compile_interpretation(
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
        for obligation in report.obligations
    )
    assert report.can_project_public_row is False


def test_accepted_report_is_not_public_projection_authority():
    report = CompilerTool(allowed_units=frozenset({"kwh"})).compile_interpretation(
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
    assert report.can_project_public_row is False
