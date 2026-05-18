from __future__ import annotations

from comp.compiler_tool.models import (
    CheckedClaim,
    CompileReport,
    FailedClaim,
    InterpretationHypothesis,
    ProofObligation,
)


class CompilerTool:
    def compile_interpretation(self, hypothesis: InterpretationHypothesis) -> CompileReport:
        passed: list[CheckedClaim] = []
        failed: list[FailedClaim] = []
        obligations: list[ProofObligation] = []

        for claim in hypothesis.claims:
            if claim.witness_id is None:
                failed.append(
                    FailedClaim(
                        field=claim.field,
                        value=claim.value,
                        reason="missing_source_witness",
                        origin=claim.origin,
                    )
                )
                obligations.append(
                    ProofObligation(
                        kind="find_source_witness",
                        field=claim.field,
                        acceptable_sources=(
                            "same_fragment",
                            "nearby_header",
                            "table_column_unit",
                        ),
                    )
                )
                continue

            passed.append(
                CheckedClaim(
                    field=claim.field,
                    value=claim.value,
                    witness_id=claim.witness_id,
                )
            )

        if failed:
            return CompileReport(
                status="blocked",
                passed_claims=tuple(passed),
                failed_claims=tuple(failed),
                obligations=tuple(obligations),
                hazards=hypothesis.hazards,
                can_project_public_row=False,
            )

        if hypothesis.hazards:
            return CompileReport(
                status="review_required",
                passed_claims=tuple(passed),
                hazards=hypothesis.hazards,
                can_project_public_row=False,
            )

        return CompileReport(
            status="accepted",
            passed_claims=tuple(passed),
            receipt_preconditions=("commit_receipt",),
            can_project_public_row=False,
        )
