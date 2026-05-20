from comp.compiler_tool import EvidenceWitness, evidence_witness_fingerprint


def _witness(*, span="1200kWh", text="Seoul office used 1200kWh electricity."):
    return EvidenceWitness(
        witness_id="w-electricity-kwh",
        field="electricity_kwh",
        source="raw-evidence:canonical-working-loop",
        span=span,
        text=text,
    )


def test_evidence_witness_fingerprint_pins_source_span_body():
    fingerprint = evidence_witness_fingerprint(_witness())
    same_fingerprint = evidence_witness_fingerprint(_witness())
    changed_span_fingerprint = evidence_witness_fingerprint(_witness(span="9999kWh"))
    changed_text_fingerprint = evidence_witness_fingerprint(
        _witness(text="Seoul office used 9999kWh electricity.")
    )

    assert fingerprint.dependency_kind == "evidence_witness"
    assert fingerprint.dependency_id == "w-electricity-kwh"
    assert fingerprint.fingerprint.startswith("sha256:")
    assert fingerprint == same_fingerprint
    assert fingerprint != changed_span_fingerprint
    assert fingerprint != changed_text_fingerprint
