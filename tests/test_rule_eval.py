from types import SimpleNamespace
from artifacts import CanonicalRowArtifact, ClaimArtifact, PartialFrameArtifact, RoleSlotArtifact
from rule_eval import RuleEvaluator
from rule_ir import FrameSlotRef, HasApproval, LocalVarRef, PolicyRef, RowFieldRef, RuleBinary, RuleBuiltinCall, RuleLiteral, SymbolConst
from runtime_env import RuntimeEnv

def _ctx():
    env = RuntimeEnv(); env.policy_flags["auto_merge"] = True
    c = ClaimArtifact(claim_id="CLM-1", frame_id="FRM-1", fragment_id="FRG-1", parser_name="p", role_name="raw_amount", value=42, extraction_mode="explicit", confidence=0.9, evidence_ids=["pair:raw_amount"])
    s = RoleSlotArtifact(role_name="raw_amount", active_claim_id=c.claim_id, resolved_value=42)
    f = PartialFrameArtifact(frame_id="FRM-1", parser_name="p", frame_type="ActivityObservation", slots={"raw_amount": s})
    r = CanonicalRowArtifact(row_id="ROW-1", frame_id="FRM-1", parser_name="p", frame_type="ActivityObservation", raw_amount=42.0, status="committed")
    return SimpleNamespace(env=env, scope_path=tuple(), column_key=None, row=r, frame=f, claims_by_id={c.claim_id: c}, local_vars={"status": "committed", "score": 0.9}, warning_codes={"AggregateRow"}, error_codes={"InvalidPeriod"}, approvals={"human_reviewer": False})

def test_rule_refs():
    ev, ctx = RuleEvaluator(), _ctx()
    assert ev.eval_bool(RuleBinary(LocalVarRef("status"), "==", SymbolConst("committed")), ctx)
    assert ev.eval_bool(RuleBinary(RowFieldRef("raw_amount"), ">", RuleLiteral(0)), ctx)
    assert ev.eval_bool(RuleBinary(HasApproval("human_reviewer"), "or", PolicyRef("auto_merge")), ctx)

def test_rule_builtins():
    ev, ctx = RuleEvaluator(), _ctx()
    assert ev.eval(RuleBuiltinCall("missing", [FrameSlotRef("raw_amount")]), ctx) is False
    assert ev.eval(RuleBuiltinCall("origin", [FrameSlotRef("raw_amount")]), ctx) == "explicit"
    assert ev.eval(RuleBuiltinCall("evidence", [RuleLiteral("pair")]), ctx) == 1
