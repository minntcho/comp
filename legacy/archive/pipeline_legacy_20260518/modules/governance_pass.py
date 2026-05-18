from __future__ import annotations

from dataclasses import dataclass
from itertools import count

from artifacts import CanonicalRowArtifact, CompileArtifacts, GovernanceDecisionArtifact
from compiled_spec import CompiledGovernancePolicy, CompiledProgramSpec
from expr_eval import EvalContext
from rule_eval import RuleEvaluator
from runtime_env import RuntimeEnv


@dataclass
class GovernancePassConfig:
    block_on_any_error: bool = True
    enforce_emit_condition: bool = True
    skip_non_committed_rows: bool = True


class GovernancePass:
    def __init__(self, evaluator: RuleEvaluator | None = None, config: GovernancePassConfig | None = None) -> None:
        self.evaluator = evaluator or RuleEvaluator()
        self.config = config or GovernancePassConfig()
        self._decision_seq = count(1)

    def run(self, spec: CompiledProgramSpec, artifacts: CompileArtifacts, env: RuntimeEnv) -> CompileArtifacts:
        if not isinstance(spec, CompiledProgramSpec):
            raise TypeError("GovernancePass requires CompiledProgramSpec")

        decisions: list[GovernanceDecisionArtifact] = []
        for row in artifacts.rows:
            if self.config.skip_non_committed_rows and row.status != "committed":
                decisions.append(self._decision(row=row, from_status=row.status, to_status=row.status, action="skip", actor="policy_engine", reason_codes=["row_not_committed"], matched_rule_keys=[]))
                continue

            policy = spec.compiled_governances.get(row.frame_type)
            if policy is None:
                decisions.append(self._decision(row=row, from_status=row.status, to_status=row.status, action="hold", actor="policy_engine", reason_codes=["no_governance_policy"], matched_rule_keys=[]))
                continue

            decisions.append(self._apply_policy(row=row, policy=policy, env=env))

        artifacts.merge_log.extend(decisions)
        for d in decisions:
            artifacts.event_log.append({
                "event_id": f"EVT-GOV-{d.decision_id}",
                "record_id": d.row_id,
                "event_type": "MERGED" if d.action == "merge" else "MERGE_HELD" if d.action == "hold" else "SKIPPED",
                "from_status": d.from_status,
                "to_status": d.to_status,
                "actor": d.actor,
                "reason_codes": list(d.reason_codes),
                "matched_rule_keys": list(d.matched_rule_keys),
                "created_at": d.created_at.isoformat() + "Z",
            })
        return artifacts

    def _apply_policy(self, *, row: CanonicalRowArtifact, policy: CompiledGovernancePolicy, env: RuntimeEnv) -> GovernanceDecisionArtifact:
        ctx = self._build_eval_context(row, env)
        from_status = row.status

        if self.config.enforce_emit_condition and policy.emit_condition_ir is not None:
            if not self._safe_eval_bool(policy.emit_condition_ir, ctx):
                return self._decision(row=row, from_status=from_status, to_status=from_status, action="hold", actor="policy_engine", reason_codes=["emit_condition_not_satisfied"], matched_rule_keys=["emit_condition"])

        if self.config.block_on_any_error and row.error_codes:
            return self._decision(row=row, from_status=from_status, to_status=from_status, action="hold", actor="policy_engine", reason_codes=["row_has_error_diagnostics", *row.error_codes], matched_rule_keys=[])

        matched_forbid = [f"forbid_merge:{idx}" for idx, expr in enumerate(policy.forbid_merge_conditions_ir, start=1) if self._safe_eval_bool(expr, ctx)]
        if matched_forbid:
            return self._decision(row=row, from_status=from_status, to_status=from_status, action="hold", actor="policy_engine", reason_codes=["forbid_merge_matched"], matched_rule_keys=matched_forbid)

        matched_merge = [f"merge:{idx}" for idx, expr in enumerate(policy.merge_conditions_ir, start=1) if self._safe_eval_bool(expr, ctx)]
        if matched_merge:
            row.status = "merged"
            actor = self._pick_actor(ctx)
            row.metadata.setdefault("governance_trace", []).append({"action": "merge", "matched_rule_keys": matched_merge, "actor": actor})
            return self._decision(row=row, from_status=from_status, to_status="merged", action="merge", actor=actor, reason_codes=["merge_condition_satisfied"], matched_rule_keys=matched_merge)

        row.metadata.setdefault("governance_trace", []).append({"action": "hold", "reason": "no_merge_rule_matched"})
        return self._decision(row=row, from_status=from_status, to_status=from_status, action="hold", actor="policy_engine", reason_codes=["no_merge_rule_matched"], matched_rule_keys=[])

    def _build_eval_context(self, row: CanonicalRowArtifact, env: RuntimeEnv) -> EvalContext:
        approvals = {}
        if isinstance(env.policy_flags.get("approvals"), dict):
            approvals.update(env.policy_flags["approvals"])
        if isinstance(row.metadata.get("approvals"), dict):
            approvals.update(row.metadata["approvals"])

        return EvalContext(
            env=env,
            text="",
            scope_path=tuple(),
            row=row,
            frame=None,
            claims_by_id={},
            local_vars={
                "row_id": row.row_id,
                "frame_id": row.frame_id,
                "frame_type": row.frame_type,
                "status": row.status,
                "score": row.resolution_score,
                "resolution_score": row.resolution_score,
                "site_id": row.site_id,
                "entity_id": row.entity_id,
                "period": row.period,
                "activity_type": row.activity_type,
                "raw_amount": row.raw_amount,
                "raw_unit": row.raw_unit,
                "standardized_amount": row.standardized_amount,
                "standardized_unit": row.standardized_unit,
                "scope_category": row.scope_category,
                "parser_name": row.parser_name,
            },
            warning_codes=set(row.warning_codes),
            error_codes=set(row.error_codes),
            approvals=approvals,
        )

    def _safe_eval_bool(self, expr, ctx: EvalContext) -> bool:
        try:
            return self.evaluator.eval_bool(expr, ctx)
        except Exception:
            return False

    def _decision(self, *, row: CanonicalRowArtifact, from_status: str, to_status: str, action: str, actor: str, reason_codes: list[str], matched_rule_keys: list[str]) -> GovernanceDecisionArtifact:
        return GovernanceDecisionArtifact(
            decision_id=f"GOV-{next(self._decision_seq):07d}",
            row_id=row.row_id,
            frame_id=row.frame_id,
            from_status=from_status,
            to_status=to_status,
            action=action,
            actor=actor,
            reason_codes=list(reason_codes),
            matched_rule_keys=list(matched_rule_keys),
            metadata={"frame_type": row.frame_type, "warning_codes": list(row.warning_codes), "error_codes": list(row.error_codes)},
        )

    def _pick_actor(self, ctx: EvalContext) -> str:
        if ctx.approvals.get("human_reviewer"):
            return "human_reviewer"
        if ctx.env.policy_flags.get("auto_merge", False):
            return "system"
        return "policy_engine"
