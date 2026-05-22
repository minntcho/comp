from comp.compiler_tool import (
    ValidationReport,
    CanonicalReference,
    RejectedReferenceOption,
    compile_report_to_facts,
)
from comp.judgment import Fact, SubjectRef


def test_compile_report_to_facts_maps_reference_binding_as_provenance_edge():
    subject = SubjectRef("claim", "hyp-1")
    rejected = RejectedReferenceOption(
        candidate_id="cand-market",
        reference_id="factor.kr_residual_mix.2024.market_based",
        reason="attribute_mismatch:method",
        selector_rule_id="ghg.factor_selector.v1",
    )
    binding = CanonicalReference(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id="factor.kr_grid.2024.location_based",
        reference_type="emission_factor",
        selected_candidate_id="cand-location",
        selector_rule_id="ghg.factor_selector.v1",
        source_witness_ids=("span-amount", "ref-factor-row-17"),
        rejected_candidates=(rejected,),
    )
    report = ValidationReport(status="accepted", reference_bindings=(binding,))

    facts = compile_report_to_facts(report, subject)

    assert facts == {
        Fact(
            tag="prov_edge",
            subject=subject,
            key="reference_binding:bind-amount-factor",
            value="factor.kr_grid.2024.location_based",
            witness="cand-location",
            weight=1.0,
            meta=(
                ("authority", "canonical_binding"),
                ("binding_id", "bind-amount-factor"),
                ("claim_id", "hyp-1:amount"),
                ("reference_type", "emission_factor"),
                ("rejected_candidates", (("cand-market", "attribute_mismatch:method"),)),
                ("report_section", "reference_binding"),
                ("report_status", "accepted"),
                ("selector_rule_id", "ghg.factor_selector.v1"),
                ("source_witness_ids", ("span-amount", "ref-factor-row-17")),
            ),
        )
    }
