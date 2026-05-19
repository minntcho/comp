from __future__ import annotations

from comp.compiler_tool.models import CompileReport, InterpretationHypothesis, ProofObligation
from comp.compiler_tool.profiles import CompilerProfile, active_rule_families, validate_compiler_profile


def compile_with_profile(
    hypothesis: InterpretationHypothesis,
    profile: CompilerProfile,
) -> CompileReport:
    validate_compiler_profile(profile)
    obligations: list[ProofObligation] = []

    for claim in hypothesis.claims:
        for rule in active_rule_families(profile, validate=False):
            if rule.evaluate is None:
                continue
            for result in rule.evaluate(claim, hypothesis, profile):
                if isinstance(result, ProofObligation) and result not in obligations:
                    obligations.append(result)

    return CompileReport(
        status=_status_for(obligations),
        obligations=tuple(obligations),
        can_project_public_row=False,
    )


def _status_for(obligations: list[ProofObligation]) -> str:
    if any(
        obligation.kind == "semantic_judgment_required" and obligation.blocking
        for obligation in obligations
    ):
        return "review_required"
    return "accepted"


__all__ = ["compile_with_profile"]
