from __future__ import annotations

import pytest

pytest.importorskip("lark")

from binder import Binder, BindingError
from compiled_spec import CompiledBindAction, CompiledParserInheritAction, CompiledProgramSpec
from lex_ir import LexBuiltinCall, LexUnion
from pipeline_runner import load_program_spec_from_dsl
from rule_ir import LocalVarRef, RuleBinary, SymbolConst
from source_ir import SourceColumnRef, SourceContextRef, SourceFirstOf, SourceTokenRef
from tests.support.builders import GRAMMAR_PATH


LEX_SOURCE_DSL = """
module lex_source_split

dimension amount
unit kwh: amount
activity electricity: amount -> scope2

context site {}
context period {}

frame ActivityObservation {
  site: String
  period: String?
  raw_amount: Number
  raw_unit: String
}

token SiteToken := one_of("alpha") | one_of("beta")
token AmountToken := number()
token UnitToken := one_of("kwh")

parser LineParser on line {
  build ActivityObservation
  bind site from column("site_name") | SiteToken
  inherit period from context.period when frame_type == ActivityObservation
  bind raw_amount from AmountToken
  bind raw_unit from UnitToken
}

inherit site from context.site when frame_type == ActivityObservation

resolver ActivityObservation {
  commit when true
}

governance ActivityObservation {
  emit row when true
  merge when true
}
""".strip()


def _bind_dsl(dsl_text: str):
    return Binder().bind(load_program_spec_from_dsl(grammar_path=GRAMMAR_PATH, dsl_text=dsl_text))


def test_binder_compiles_token_and_source_hosts_into_stage_specific_ir():
    compiled = _bind_dsl(LEX_SOURCE_DSL)

    assert isinstance(compiled, CompiledProgramSpec)

    compiled_token = compiled.compiled_tokens["SiteToken"]
    assert isinstance(compiled_token.primary_ir, LexUnion)
    assert [type(option) for option in compiled_token.primary_ir.options] == [LexBuiltinCall, LexBuiltinCall]

    compiled_parser = compiled.compiled_parsers["LineParser"]
    bind_action = compiled_parser.actions[0]
    assert isinstance(bind_action, CompiledBindAction)
    assert isinstance(bind_action.source_ir, SourceFirstOf)
    assert isinstance(bind_action.source_ir.options[0], SourceColumnRef)
    assert isinstance(bind_action.source_ir.options[1], SourceTokenRef)

    inherit_action = compiled_parser.actions[1]
    assert isinstance(inherit_action, CompiledParserInheritAction)
    assert isinstance(inherit_action.source_ir, SourceContextRef)
    assert isinstance(inherit_action.condition_ir, RuleBinary)
    assert isinstance(inherit_action.condition_ir.left, LocalVarRef)
    assert inherit_action.condition_ir.left.name == "frame_type"
    assert isinstance(inherit_action.condition_ir.right, SymbolConst)
    assert inherit_action.condition_ir.right.name == "ActivityObservation"

    compiled_inherit = compiled.compiled_inherit_rules[0]
    assert isinstance(compiled_inherit.source_ir, SourceContextRef)


def test_binder_rejects_unknown_bare_name_in_token_host():
    bad_dsl = LEX_SOURCE_DSL.replace(
        'token SiteToken := one_of("alpha") | one_of("beta")',
        "token SiteToken := UnknownAlias",
    )
    with pytest.raises(BindingError, match="UnknownAlias"):
        _bind_dsl(bad_dsl)


def test_binder_rejects_unknown_bare_name_in_source_host():
    bad_dsl = LEX_SOURCE_DSL.replace(
        'bind site from column("site_name") | SiteToken',
        'bind site from column("site_name") | SiteTokne',
    )
    with pytest.raises(BindingError, match="SiteTokne"):
        _bind_dsl(bad_dsl)


@pytest.mark.parametrize(
    "bad_dsl, expected",
    [
        (
            LEX_SOURCE_DSL.replace(
                'token SiteToken := one_of("alpha") | one_of("beta")',
                'token SiteToken := missing("site")',
            ),
            "token host",
        ),
        (
            LEX_SOURCE_DSL.replace(
                'bind site from column("site_name") | SiteToken',
                'bind site from missing("site")',
            ),
            "source host",
        ),
    ],
)
def test_binder_rejects_rule_builtins_in_lex_and_source_hosts(bad_dsl: str, expected: str):
    with pytest.raises(BindingError, match=expected):
        _bind_dsl(bad_dsl)
