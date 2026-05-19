from __future__ import annotations

from comp.compiler_tool.models import CompileReport, InterpretationHypothesis, ProofObligation
from comp.compiler_tool.profiles import CompilerProfile, active_rule_families, validate_compiler_profile
from comp.compiler_tool.report_status import with_recomputed_status


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

    return with_recomputed_status(
        CompileReport(
            status="accepted",
            obligations=tuple(obligations),
            can_project_public_row=False,
        )
    )


__all__ = ["compile_with_profile"]
