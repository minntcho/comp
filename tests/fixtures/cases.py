from __future__ import annotations

from dataclasses import dataclass

from runtime_env import SiteRecord
from tests.support.builders import make_fragment, make_resources


BASE_DSL = """
module test

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

token SiteToken := site_alias()
token ActivityToken := activity_alias()
token PeriodToken := period_expr()
token AmountToken := number()
token UnitToken := unit_symbol()

parser LineParser on line {
  build ActivityObservation
  bind site from SiteToken
  bind activity_type from ActivityToken
  bind period ? from PeriodToken
  bind raw_amount from AmountToken
  bind raw_unit from UnitToken
}

require valid_period(period)

resolver ActivityObservation {
  commit when true
}

governance ActivityObservation {
  emit row when true
  merge when true
}
""".strip()

AGG_WARNING_DSL = BASE_DSL + "\n\nwarning AggregateRow when true\n"


@dataclass
class Case:
    name: str
    dsl_text: str
    fragments: list
    resources: object
    golden_name: str


COMMON_RESOURCES = make_resources(
    site_records=[
        SiteRecord(site_id="SITE-SEOUL", aliases=["seoul hq"], entity_id="ENT-1"),
    ],
    factor_rows=[
        {
            "factor_id": "FAC-1",
            "activity_type": "electricity",
            "unit": "kwh",
            "factor_unit": "kgco2e/kwh",
            "emission_factor": 0.5,
        }
    ],
    activity_aliases={"electricity": ["electricity"]},
    unit_aliases={"kwh": ["kwh"]},
)


CASES = [
    Case(
        name="semantic_error_blocks_merge",
        dsl_text=BASE_DSL,
        fragments=[
            make_fragment(
                fragment_id="FRG-1",
                text="seoul hq electricity 120 kwh",
            )
        ],
        resources=COMMON_RESOURCES,
        golden_name="semantic_error_blocks_merge.json",
    ),
    Case(
        name="aggregate_warning_calculation_excluded",
        dsl_text=AGG_WARNING_DSL,
        fragments=[
            make_fragment(
                fragment_id="FRG-2",
                text="seoul hq electricity 2025-03 150 kwh",
            )
        ],
        resources=COMMON_RESOURCES,
        golden_name="aggregate_warning_calculation_excluded.json",
    ),
    Case(
        name="happy_path_merge_and_calculate",
        dsl_text=BASE_DSL,
        fragments=[
            make_fragment(
                fragment_id="FRG-3",
                text="seoul hq electricity 2025-03 200 kwh",
            )
        ],
        resources=COMMON_RESOURCES,
        golden_name="happy_path_merge_and_calculate.json",
    ),
]
