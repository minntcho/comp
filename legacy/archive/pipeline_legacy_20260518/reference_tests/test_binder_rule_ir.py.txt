from __future__ import annotations

import pytest

pytest.importorskip("lark")

from binder import Binder, BindingError
from compiled_spec import CompiledProgramSpec
from pipeline_runner import load_program_spec_from_dsl
from rule_ir import (
    FrameSlotRef,
    HasApproval,
    HasDiagnostic,
    LocalVarRef,
    PolicyRef,
    RowFieldRef,
    RuleBinary,
    RuleBuiltinCall,
    SymbolConst,
)
from tests.support.builders import GRAMMAR_PATH


BINDER_DSL = """
module binder_test

dimension amount
unit kwh: amount
activity electricity: amount -> scope2

frame ActivityObservation {
  site: String
  activity_type: String
  period: String?
  raw_amount: Number
  raw_unit: String
}

token AmountToken := number()

parser LineParser on line {
  build ActivityObservation
  bind raw_amount from AmountToken
}

infer raw_unit = kwh when frame_type == ActivityObservation
require status == committed
warning InvalidPeriod when warning.InvalidPeriod

resolver ActivityObservation {
  commit when score >= 0.8 and not missing(raw_amount)
}

governance ActivityObservation {
  emit row when raw_amount > 0
  merge when approval.human_reviewer or policy.auto_merge
  forbid merge when error.InvalidPeriod
}
""".strip()


def _load_program_spec(dsl_text: str = BINDER_DSL):
    return load_program_spec_from_dsl(
        grammar_path=GRAMMAR_PATH,
        dsl_text=dsl_text,
    )


def test_binder_binds_constraint_and_infer_hosts():
    program = _load_program_spec()
    spec = Binder().bind(program)

    assert isinstance(spec, CompiledProgramSpec)

    compiled_require = spec.compiled_constraints[0]
    assert isinstance(compiled_require.condition_ir, RuleBinary)
    assert isinstance(compiled_require.condition_ir.left, LocalVarRef)
    assert compiled_require.condition_ir.left.name == "status"
    assert isinstance(compiled_require.condition_ir.right, SymbolConst)
    assert compiled_require.condition_ir.right.name == "committed"

    compiled_infer = spec.compiled_infer_rules[0]
    assert isinstance(compiled_infer.value_ir, SymbolConst)
    assert compiled_infer.value_ir.name == "kwh"
    assert isinstance(compiled_infer.condition_ir, RuleBinary)
    assert isinstance(compiled_infer.condition_ir.left, LocalVarRef)
    assert compiled_infer.condition_ir.left.name == "frame_type"
    assert isinstance(compiled_infer.condition_ir.right, SymbolConst)
    assert compiled_infer.condition_ir.right.name == "ActivityObservation"


def test_binder_binds_diagnostic_resolver_and_governance_hosts():
    program = _load_program_spec()
    spec = Binder().bind(program)

    compiled_diag = spec.compiled_diagnostics[0]
    assert isinstance(compiled_diag.condition_ir, HasDiagnostic)
    assert compiled_diag.condition_ir.severity == "warning"
    assert compiled_diag.condition_ir.code == "InvalidPeriod"

    compiled_resolver = spec.compiled_resolvers["ActivityObservation"]
    assert isinstance(compiled_resolver.commit_condition_ir, RuleBinary)
    left = compiled_resolver.commit_condition_ir.left
    right = compiled_resolver.commit_condition_ir.right
    assert isinstance(left, RuleBinary)
    assert isinstance(left.left, LocalVarRef)
    assert left.left.name == "score"
    assert isinstance(right, RuleBuiltinCall)
    assert right.name == "missing"
    assert isinstance(right.args[0], FrameSlotRef)
    assert right.args[0].role_name == "raw_amount"

    compiled_governance = spec.compiled_governances["ActivityObservation"]
    assert isinstance(compiled_governance.emit_condition_ir, RuleBinary)
    assert isinstance(compiled_governance.emit_condition_ir.left, RowFieldRef)
    assert compiled_governance.emit_condition_ir.left.field_name == "raw_amount"

    merge_ir = compiled_governance.merge_conditions_ir[0]
    assert isinstance(merge_ir, RuleBinary)
    assert isinstance(merge_ir.left, HasApproval)
    assert merge_ir.left.key == "human_reviewer"
    assert isinstance(merge_ir.right, PolicyRef)
    assert merge_ir.right.key == "auto_merge"

    forbid_ir = compiled_governance.forbid_merge_conditions_ir[0]
    assert isinstance(forbid_ir, HasDiagnostic)
    assert forbid_ir.severity == "error"
    assert forbid_ir.code == "InvalidPeriod"


def test_binder_rejects_lexical_builtin_in_rule_host():
    bad_dsl = """
module bad_rule

dimension amount
unit kwh: amount
activity electricity: amount -> scope2

frame ActivityObservation {
  raw_amount: Number
}

require number() > 0
""".strip()

    with pytest.raises(BindingError):
        Binder().bind(_load_program_spec(bad_dsl))
