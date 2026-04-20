from __future__ import annotations

import pytest

pytest.importorskip("lark")

from tests.support.builders import make_fragment, make_resources, run_pipeline_until


DSL = """
module lex_source_stage_semantics

dimension amount
unit kwh: amount
activity electricity: amount -> scope2

frame ActivityObservation {
  site: String
  raw_amount: Number
  raw_unit: String
}

token SiteToken := one_of("alpha") | one_of("beta")
token AmountToken := number()
token UnitToken := one_of("kwh")

parser LineParser on line {
  build ActivityObservation
  bind site from column("site_name") | SiteToken
  bind raw_amount from AmountToken
  bind raw_unit from UnitToken
}

resolver ActivityObservation {
  commit when true
}

governance ActivityObservation {
  emit row when true
  merge when true
}
""".strip()


def test_lex_union_and_source_first_of_are_preserved_end_to_end():
    fragments = [
        make_fragment(
            fragment_id="FRG-1",
            text="alpha beta 10 kwh",
            metadata={"row": {"site_name": "COLUMN-SITE"}},
        )
    ]
    resources = make_resources()

    lex_result = run_pipeline_until(
        dsl_text=DSL,
        fragments=fragments,
        resources=resources,
        pass_name="LexPass",
    )
    site_values = {tok.value for tok in lex_result.artifacts.tokens if tok.token_name == "SiteToken"}
    assert site_values == {"alpha", "beta"}

    parse_result = run_pipeline_until(
        dsl_text=DSL,
        fragments=fragments,
        resources=resources,
        pass_name="ParsePass",
    )
    frame = parse_result.artifacts.frames[0]

    assert frame.slots["site"].resolved_value == "COLUMN-SITE"
    assert frame.slots["raw_amount"].resolved_value == 10
    assert frame.slots["raw_unit"].resolved_value == "kwh"
