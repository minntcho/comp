# Raw Claim Promotion Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the synthetic raw `ClaimHypothesis` acceptance path behind a focused promotion boundary so raw candidates can become canonical checked claims, reference bindings, and derived claims without gaining receipt authority.

**Architecture:** Add a synthetic scenario promotion module that converts supported raw candidates into compiler artifacts. Keep `comp.compiler_tool`, `comp.judgment`, and `comp.persistence` authority rules unchanged: promotion can build `CompileReport` artifacts, but only `prepare_commit(...)` can mint `CommitReceipt`, and only `project_public_row(..., receipt=...)` can project. Refactor the acceptance scenario to call the promotion module instead of hand-assembling the final report inline.

**Tech Stack:** Python 3.11, dataclasses, pytest, existing `comp.compiler_tool` models and `tests.domain_scenarios` contracts.

---

## File Structure

- Create: `comp/scenarios/synthetic/raw_claim_promotion.py`
  - Owns synthetic-only support profiles and promotion logic.
  - Imports compiler artifact types, but does not import `prepare_commit`, `CommitReceipt`, `project_public_row`, persistence, or agent code.
- Modify: `comp/scenarios/synthetic/__init__.py`
  - Re-export the new support/profile types and `promote_raw_claim_hypothesis`.
- Create: `tests/test_synthetic_raw_claim_promotion.py`
  - Direct unit tests for the new boundary.
- Modify: `tests/domain_scenarios/synthetic_raw_claim_hypothesis_acceptance/scenario.py`
  - Keep scenario ids, expected projection, and contract constants.
  - Replace local hand-built report helpers with a profile plus `promote_raw_claim_hypothesis(...)`.
- Modify: `docs/architecture/domain-scenario-pack-generation.md`
  - Record that raw claim promotion is a scenario/domain layer helper, not receipt authority.
- Modify: `docs/architecture/trust-kernel-hardening.md`
  - Record that promoted reports still cannot authorize public projection.
- Modify: `tests/test_package_smoke.py`
  - Change architecture-doc checked-date validation from one global hard-coded date to a per-doc expected map, then update the two touched docs to `2026-05-21`.

Do not modify these files in this plan:

- `comp/compiler_tool/tool.py`
- `comp/compiler_tool/commit_flow.py`
- `comp/compiler_tool/receipt_builder.py`
- `comp/judgment/commit.py`
- `comp/persistence/replay.py`

Those files are the authority kernel and should not change for this PR.

---

### Task 1: Add Promotion Boundary Tests

**Files:**
- Create: `tests/test_synthetic_raw_claim_promotion.py`
- Read: `tests/domain_scenarios/synthetic_raw_claim_hypothesis_gate/scenario.py`
- Read: `tests/domain_scenarios/synthetic_raw_claim_hypothesis_acceptance/scenario.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_synthetic_raw_claim_promotion.py` with this content:

```python
import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row
from comp.compiler_tool import evidence_witness_fingerprint, prepare_commit
from comp.scenarios.synthetic.raw_claim_promotion import (
    AllocationSupport,
    PromotionClaimIds,
    ReportingPeriodSupport,
    SiteAliasSupport,
    SyntheticRawClaimPromotionProfile,
    UnitConversionSupport,
    promote_raw_claim_hypothesis,
)
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_acceptance.scenario import (
    ALIAS_BINDING_ID,
    ALIAS_OBLIGATION_ID,
    ALLOCATED_ELECTRICITY_CLAIM_ID,
    ALLOCATION_SHARE_CLAIM_ID,
    ALLOCATION_SUPPORT_BINDING_ID,
    ALLOCATION_SUPPORT_OBLIGATION_ID,
    ELECTRICITY_MWH_CLAIM_ID,
    FORMULA_ID,
    GWH_TO_MWH_FACTOR,
    LINE_A_MASS_TON,
    PERIOD_OBLIGATION_ID,
    PROFILE_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    PUBLIC_ROW_ID,
    SCENARIO_ID,
    SUBJECT_ID,
    TOTAL_LINE_MASS_TON,
    UNIT_CONVERSION_BINDING_ID,
    UNIT_CONVERSION_OBLIGATION_ID,
)
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_gate.scenario import (
    raw_claim_hypothesis,
)


def test_promotes_supported_raw_candidates_without_projection_authority():
    report = promote_raw_claim_hypothesis(
        raw_claim_hypothesis(),
        _acceptance_profile(),
    )

    assert report.status == "accepted"
    assert report.can_project_public_row is False
    assert ("site_id", "OCH-01") not in {
        (claim.field, claim.value) for claim in report.checked_claims
    }
    assert {
        (claim.field, claim.value, claim.origin)
        for claim in report.checked_claims
    } >= {
        ("site_id", "ocheong_plant_1", "site_alias_binding"),
        ("period", "2025-03", "reporting_period_policy"),
        ("electricity_gwh", 6.4, "raw_candidate_with_unit_policy"),
        ("line_a_mass_ton", 50000, "physical_allocation_support"),
        ("total_line_mass_ton", 100000, "physical_allocation_support"),
    }
    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in report.reference_bindings
    ) == (
        (
            ALIAS_BINDING_ID,
            "site-alias:OCH-01->ocheong_plant_1",
            "site_alias",
        ),
        (
            UNIT_CONVERSION_BINDING_ID,
            "unit-conversion:GWh_to_MWh",
            "unit_conversion",
        ),
        (
            ALLOCATION_SUPPORT_BINDING_ID,
            "physical-allocation-support:line_a_mass_share",
            "physical_allocation_support",
        ),
    )
    assert tuple(item.kind for item in report.resolved_obligations) == (
        "site_alias_resolved",
        "unit_conversion_policy_applied",
        "period_validated",
        "physical_allocation_support_validated",
    )
    assert tuple(claim.claim_id for claim in report.derived_claims) == (
        ELECTRICITY_MWH_CLAIM_ID,
        ALLOCATION_SHARE_CLAIM_ID,
        ALLOCATED_ELECTRICITY_CLAIM_ID,
    )

    with pytest.raises(ProjectionBlocked, match="CommitReceipt"):
        project_public_row(
            _projection_source(report),
            ProjectionSpec(PROJECTION_ID, PROJECTION_FIELDS),
        )


def test_promoted_report_can_commit_only_through_prepare_commit():
    report = promote_raw_claim_hypothesis(
        raw_claim_hypothesis(),
        _acceptance_profile(),
    )
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
        profile_id=PROFILE_ID,
        dependency_fingerprints=tuple(
            evidence_witness_fingerprint(witness)
            for witness in report.evidence_witnesses
        ),
    )

    assert preparation.package.complete is True
    assert preparation.decision.status == "commit"
    assert preparation.receipt is not None
    assert preparation.receipt.citations is not None
    assert preparation.receipt.citations.reference_binding_ids == (
        ALIAS_BINDING_ID,
        UNIT_CONVERSION_BINDING_ID,
        ALLOCATION_SUPPORT_BINDING_ID,
    )
    assert preparation.receipt.citations.derived_claim_ids == (
        ELECTRICITY_MWH_CLAIM_ID,
        ALLOCATION_SHARE_CLAIM_ID,
        ALLOCATED_ELECTRICITY_CLAIM_ID,
    )

    projection = project_public_row(
        _projection_source(report),
        ProjectionSpec(PROJECTION_ID, PROJECTION_FIELDS),
        receipt=preparation.receipt,
    )
    assert projection == {
        "site_id": "ocheong_plant_1",
        "period": "2025-03",
        "electricity_mwh": 6400,
        "allocation_share": 0.5,
        "allocated_electricity_mwh": 3200,
    }


def _acceptance_profile() -> SyntheticRawClaimPromotionProfile:
    return SyntheticRawClaimPromotionProfile(
        profile_id=PROFILE_ID,
        scenario_id=SCENARIO_ID,
        formula_id=FORMULA_ID,
        selector_rule_id="synthetic.raw_claim_acceptance.fixture",
        claim_ids=PromotionClaimIds(
            electricity_mwh=ELECTRICITY_MWH_CLAIM_ID,
            allocation_share=ALLOCATION_SHARE_CLAIM_ID,
            allocated_electricity_mwh=ALLOCATED_ELECTRICITY_CLAIM_ID,
        ),
        site_alias=SiteAliasSupport(
            raw_site_id="OCH-01",
            canonical_site_id="ocheong_plant_1",
            binding_id=ALIAS_BINDING_ID,
            obligation_id=ALIAS_OBLIGATION_ID,
            witness_id="w-site-alias-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="site_aliases.OCH-01",
            text="OCH-01 -> ocheong_plant_1",
        ),
        unit_conversion=UnitConversionSupport(
            source_unit="GWh",
            target_unit="MWh",
            factor=GWH_TO_MWH_FACTOR,
            binding_id=UNIT_CONVERSION_BINDING_ID,
            obligation_id=UNIT_CONVERSION_OBLIGATION_ID,
            witness_id="w-unit-conversion-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="unit_conversions.GWh_to_MWh",
            text="1 GWh = 1000 MWh",
        ),
        reporting_period=ReportingPeriodSupport(
            period="2025-03",
            obligation_id=PERIOD_OBLIGATION_ID,
            witness_id="w-reporting-period-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="reporting_periods.2025-03",
            text="2025-03 is inside the active reporting window",
        ),
        allocation_support=AllocationSupport(
            share=0.5,
            line_a_mass_ton=LINE_A_MASS_TON,
            total_line_mass_ton=TOTAL_LINE_MASS_TON,
            binding_id=ALLOCATION_SUPPORT_BINDING_ID,
            obligation_id=ALLOCATION_SUPPORT_OBLIGATION_ID,
            witness_id="w-allocation-support",
            source="raw_sources/mes_line_mass.csv",
            span="line_mass_row:line_a",
            text="Line A 50,000 ton; total line mass 100,000 ton",
        ),
    )


def _projection_source(report):
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```bash
python -m pytest tests/test_synthetic_raw_claim_promotion.py -q
```

Expected: FAIL during import with `ModuleNotFoundError: No module named 'comp.scenarios.synthetic.raw_claim_promotion'`.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_synthetic_raw_claim_promotion.py
git commit -m "test: specify raw claim promotion boundary"
```

---

### Task 2: Implement Synthetic Raw Claim Promotion

**Files:**
- Create: `comp/scenarios/synthetic/raw_claim_promotion.py`
- Modify: `comp/scenarios/synthetic/__init__.py`
- Test: `tests/test_synthetic_raw_claim_promotion.py`

- [ ] **Step 1: Create the promotion module**

Create `comp/scenarios/synthetic/raw_claim_promotion.py` with this content:

```python
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    EvidenceWitness,
    ProofObligation,
    ReferenceBinding,
    with_recomputed_status,
)
from comp.compiler_tool.models import InterpretationHypothesis


@dataclass(frozen=True)
class PromotionClaimIds:
    electricity_mwh: str
    allocation_share: str
    allocated_electricity_mwh: str


@dataclass(frozen=True)
class SiteAliasSupport:
    raw_site_id: str
    canonical_site_id: str
    binding_id: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class UnitConversionSupport:
    source_unit: str
    target_unit: str
    factor: Decimal | int | float | str
    binding_id: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class ReportingPeriodSupport:
    period: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class AllocationSupport:
    share: Decimal | int | float | str
    line_a_mass_ton: int | float
    total_line_mass_ton: int | float
    binding_id: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class SyntheticRawClaimPromotionProfile:
    profile_id: str
    scenario_id: str
    formula_id: str
    selector_rule_id: str
    claim_ids: PromotionClaimIds
    site_alias: SiteAliasSupport
    unit_conversion: UnitConversionSupport
    reporting_period: ReportingPeriodSupport
    allocation_support: AllocationSupport


def promote_raw_claim_hypothesis(
    hypothesis: InterpretationHypothesis,
    profile: SyntheticRawClaimPromotionProfile,
) -> CompileReport:
    raw = _raw_claim_values(hypothesis)
    electricity = _electricity_claim(raw)
    electricity_gwh = _decimal(electricity["amount"])
    electricity_mwh = electricity_gwh * _decimal(profile.unit_conversion.factor)
    allocation_share = _decimal(profile.allocation_support.share)
    allocated_electricity_mwh = electricity_mwh * allocation_share

    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=(
                *hypothesis.witnesses,
                *_support_witnesses(profile),
            ),
            checked_claims=(
                CheckedClaim(
                    field="site_id",
                    value=profile.site_alias.canonical_site_id,
                    witness_id=profile.site_alias.witness_id,
                    origin="site_alias_binding",
                ),
                CheckedClaim(
                    field="period",
                    value=profile.reporting_period.period,
                    witness_id=profile.reporting_period.witness_id,
                    origin="reporting_period_policy",
                ),
                CheckedClaim(
                    field="electricity_gwh",
                    value=_number(electricity_gwh),
                    witness_id=str(raw["electricity_witness_id"]),
                    origin="raw_candidate_with_unit_policy",
                ),
                CheckedClaim(
                    field="line_a_mass_ton",
                    value=profile.allocation_support.line_a_mass_ton,
                    witness_id=profile.allocation_support.witness_id,
                    origin="physical_allocation_support",
                ),
                CheckedClaim(
                    field="total_line_mass_ton",
                    value=profile.allocation_support.total_line_mass_ton,
                    witness_id=profile.allocation_support.witness_id,
                    origin="physical_allocation_support",
                ),
            ),
            resolved_obligations=_resolved_obligations(profile),
            reference_bindings=_reference_bindings(profile),
            derived_claims=_derived_claims(
                profile,
                electricity_mwh=electricity_mwh,
                allocation_share=allocation_share,
                allocated_electricity_mwh=allocated_electricity_mwh,
            ),
            can_project_public_row=False,
        )
    )


def _raw_claim_values(hypothesis: InterpretationHypothesis) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for claim in hypothesis.claims:
        values[claim.field] = claim.value
        if claim.witness_id is not None:
            values[f"{claim.field}_witness_id"] = claim.witness_id
    return values


def _electricity_claim(values: dict[str, Any]) -> dict[str, Any]:
    electricity = values["electricity"]
    if not isinstance(electricity, dict):
        raise TypeError("raw electricity claim must be a mapping.")
    return electricity


def _support_witnesses(
    profile: SyntheticRawClaimPromotionProfile,
) -> tuple[EvidenceWitness, ...]:
    return (
        EvidenceWitness(
            witness_id=profile.site_alias.witness_id,
            field="site_alias",
            source=profile.site_alias.source,
            span=profile.site_alias.span,
            text=profile.site_alias.text,
        ),
        EvidenceWitness(
            witness_id=profile.unit_conversion.witness_id,
            field="unit_conversion",
            source=profile.unit_conversion.source,
            span=profile.unit_conversion.span,
            text=profile.unit_conversion.text,
        ),
        EvidenceWitness(
            witness_id=profile.reporting_period.witness_id,
            field="period",
            source=profile.reporting_period.source,
            span=profile.reporting_period.span,
            text=profile.reporting_period.text,
        ),
        EvidenceWitness(
            witness_id=profile.allocation_support.witness_id,
            field="allocation_support",
            source=profile.allocation_support.source,
            span=profile.allocation_support.span,
            text=profile.allocation_support.text,
        ),
    )


def _resolved_obligations(
    profile: SyntheticRawClaimPromotionProfile,
) -> tuple[ProofObligation, ...]:
    return (
        ProofObligation(
            kind="site_alias_resolved",
            field="site_id",
            reason=(
                f"{profile.site_alias.raw_site_id}_alias_bound_to_"
                f"{profile.site_alias.canonical_site_id}"
            ),
            obligation_id=profile.site_alias.obligation_id,
        ),
        ProofObligation(
            kind="unit_conversion_policy_applied",
            field="electricity_mwh",
            reason=(
                f"{profile.unit_conversion.source_unit}_to_"
                f"{profile.unit_conversion.target_unit}_conversion_factor_"
                f"{_number(_decimal(profile.unit_conversion.factor))}"
            ),
            obligation_id=profile.unit_conversion.obligation_id,
        ),
        ProofObligation(
            kind="period_validated",
            field="period",
            reason="period_inside_active_reporting_window",
            obligation_id=profile.reporting_period.obligation_id,
        ),
        ProofObligation(
            kind="physical_allocation_support_validated",
            field="allocation_share",
            reason="line_a_mass_over_total_line_mass",
            obligation_id=profile.allocation_support.obligation_id,
        ),
    )


def _reference_bindings(
    profile: SyntheticRawClaimPromotionProfile,
) -> tuple[ReferenceBinding, ...]:
    return (
        ReferenceBinding(
            binding_id=profile.site_alias.binding_id,
            claim_id=profile.scenario_id,
            reference_id=(
                f"site-alias:{profile.site_alias.raw_site_id}->"
                f"{profile.site_alias.canonical_site_id}"
            ),
            reference_type="site_alias",
            selector_rule_id=profile.selector_rule_id,
            source_witness_ids=(profile.site_alias.witness_id,),
        ),
        ReferenceBinding(
            binding_id=profile.unit_conversion.binding_id,
            claim_id=profile.scenario_id,
            reference_id=(
                f"unit-conversion:{profile.unit_conversion.source_unit}_to_"
                f"{profile.unit_conversion.target_unit}"
            ),
            reference_type="unit_conversion",
            selector_rule_id=profile.selector_rule_id,
            source_witness_ids=(profile.unit_conversion.witness_id,),
        ),
        ReferenceBinding(
            binding_id=profile.allocation_support.binding_id,
            claim_id=profile.scenario_id,
            reference_id="physical-allocation-support:line_a_mass_share",
            reference_type="physical_allocation_support",
            selector_rule_id=profile.selector_rule_id,
            source_witness_ids=(profile.allocation_support.witness_id,),
        ),
    )


def _derived_claims(
    profile: SyntheticRawClaimPromotionProfile,
    *,
    electricity_mwh: Decimal,
    allocation_share: Decimal,
    allocated_electricity_mwh: Decimal,
) -> tuple[DerivedClaim, ...]:
    return (
        _derived_claim(
            claim_id=profile.claim_ids.electricity_mwh,
            field="electricity_mwh",
            value=_number(electricity_mwh),
            unit=profile.unit_conversion.target_unit,
            formula_id=profile.formula_id,
            origin="raw_claim_hypothesis_acceptance_calculated",
            input_claim_ids=("electricity_gwh",),
            reference_binding_ids=(profile.unit_conversion.binding_id,),
            steps=(
                CalculationStep(
                    step_id="convert-gwh-to-mwh",
                    operation="multiply",
                    input_ids=("electricity_gwh", profile.unit_conversion.binding_id),
                    output_value=_number(electricity_mwh),
                    output_unit=profile.unit_conversion.target_unit,
                ),
            ),
        ),
        _derived_claim(
            claim_id=profile.claim_ids.allocation_share,
            field="allocation_share",
            value=_number(allocation_share),
            unit=None,
            formula_id=profile.formula_id,
            origin="raw_claim_hypothesis_acceptance_calculated",
            input_claim_ids=("line_a_mass_ton", "total_line_mass_ton"),
            reference_binding_ids=(profile.allocation_support.binding_id,),
            steps=(
                CalculationStep(
                    step_id="line-a-allocation-share",
                    operation="divide",
                    input_ids=("line_a_mass_ton", "total_line_mass_ton"),
                    output_value=_number(allocation_share),
                ),
            ),
        ),
        _derived_claim(
            claim_id=profile.claim_ids.allocated_electricity_mwh,
            field="allocated_electricity_mwh",
            value=_number(allocated_electricity_mwh),
            unit=profile.unit_conversion.target_unit,
            formula_id=profile.formula_id,
            origin="raw_claim_hypothesis_acceptance_calculated",
            input_claim_ids=(
                profile.claim_ids.electricity_mwh,
                profile.claim_ids.allocation_share,
            ),
            reference_binding_ids=(
                profile.unit_conversion.binding_id,
                profile.allocation_support.binding_id,
            ),
            steps=(
                CalculationStep(
                    step_id="allocated-electricity-mwh",
                    operation="multiply",
                    input_ids=(
                        profile.claim_ids.electricity_mwh,
                        profile.claim_ids.allocation_share,
                    ),
                    output_value=_number(allocated_electricity_mwh),
                    output_unit=profile.unit_conversion.target_unit,
                ),
            ),
        ),
    )


def _derived_claim(
    *,
    claim_id: str,
    field: str,
    value: int | float,
    unit: str | None,
    formula_id: str,
    origin: str,
    input_claim_ids: tuple[str, ...],
    reference_binding_ids: tuple[str, ...],
    steps: tuple[CalculationStep, ...],
) -> DerivedClaim:
    return DerivedClaim(
        claim_id=claim_id,
        field=field,
        value=value,
        unit=unit,
        origin=origin,
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=formula_id,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=reference_binding_ids,
            steps=steps,
        ),
    )


def _decimal(value: Decimal | int | float | str | Any) -> Decimal:
    return Decimal(str(value))


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


__all__ = [
    "AllocationSupport",
    "PromotionClaimIds",
    "ReportingPeriodSupport",
    "SiteAliasSupport",
    "SyntheticRawClaimPromotionProfile",
    "UnitConversionSupport",
    "promote_raw_claim_hypothesis",
]
```

- [ ] **Step 2: Export the promotion API**

Modify `comp/scenarios/synthetic/__init__.py`:

```python
from comp.scenarios.synthetic.raw_claim_promotion import (
    AllocationSupport,
    PromotionClaimIds,
    ReportingPeriodSupport,
    SiteAliasSupport,
    SyntheticRawClaimPromotionProfile,
    UnitConversionSupport,
    promote_raw_claim_hypothesis,
)
```

Add these names to `__all__`:

```python
    "AllocationSupport",
    "PromotionClaimIds",
    "ReportingPeriodSupport",
    "SiteAliasSupport",
    "SyntheticRawClaimPromotionProfile",
    "UnitConversionSupport",
    "promote_raw_claim_hypothesis",
```

- [ ] **Step 3: Run the promotion tests**

Run:

```bash
python -m pytest tests/test_synthetic_raw_claim_promotion.py -q
```

Expected: PASS.

- [ ] **Step 4: Run targeted regression tests**

Run:

```bash
python -m pytest tests/test_synthetic_raw_claim_hypothesis_acceptance.py tests/test_synthetic_raw_claim_hypothesis_gate.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the promotion module**

```bash
git add comp/scenarios/synthetic/raw_claim_promotion.py comp/scenarios/synthetic/__init__.py tests/test_synthetic_raw_claim_promotion.py
git commit -m "feat: add synthetic raw claim promotion boundary"
```

---

### Task 3: Route Acceptance Scenario Through Promotion Boundary

**Files:**
- Modify: `tests/domain_scenarios/synthetic_raw_claim_hypothesis_acceptance/scenario.py`
- Test: `tests/test_synthetic_raw_claim_hypothesis_acceptance.py`
- Test: `tests/test_domain_scenario_lab.py`

- [ ] **Step 1: Replace report construction imports**

In `tests/domain_scenarios/synthetic_raw_claim_hypothesis_acceptance/scenario.py`, remove these imports from `comp.compiler_tool`:

```python
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    EvidenceWitness,
    ProofObligation,
    ReferenceBinding,
    with_recomputed_status,
```

Keep these imports:

```python
from decimal import Decimal

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import evidence_witness_fingerprint, prepare_commit
```

Add this import:

```python
from comp.scenarios.synthetic.raw_claim_promotion import (
    AllocationSupport,
    PromotionClaimIds,
    ReportingPeriodSupport,
    SiteAliasSupport,
    SyntheticRawClaimPromotionProfile,
    UnitConversionSupport,
    promote_raw_claim_hypothesis,
)
```

- [ ] **Step 2: Replace `raw_claim_hypothesis_acceptance_report`**

Replace the function body with:

```python
def raw_claim_hypothesis_acceptance_report():
    return promote_raw_claim_hypothesis(
        raw_claim_hypothesis(),
        _acceptance_profile(),
    )
```

- [ ] **Step 3: Add `_acceptance_profile`**

Add this function below `raw_claim_hypothesis_acceptance_report`:

```python
def _acceptance_profile() -> SyntheticRawClaimPromotionProfile:
    return SyntheticRawClaimPromotionProfile(
        profile_id=PROFILE_ID,
        scenario_id=SCENARIO_ID,
        formula_id=FORMULA_ID,
        selector_rule_id="synthetic.raw_claim_acceptance.fixture",
        claim_ids=PromotionClaimIds(
            electricity_mwh=ELECTRICITY_MWH_CLAIM_ID,
            allocation_share=ALLOCATION_SHARE_CLAIM_ID,
            allocated_electricity_mwh=ALLOCATED_ELECTRICITY_CLAIM_ID,
        ),
        site_alias=SiteAliasSupport(
            raw_site_id="OCH-01",
            canonical_site_id="ocheong_plant_1",
            binding_id=ALIAS_BINDING_ID,
            obligation_id=ALIAS_OBLIGATION_ID,
            witness_id="w-site-alias-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="site_aliases.OCH-01",
            text="OCH-01 -> ocheong_plant_1",
        ),
        unit_conversion=UnitConversionSupport(
            source_unit="GWh",
            target_unit="MWh",
            factor=GWH_TO_MWH_FACTOR,
            binding_id=UNIT_CONVERSION_BINDING_ID,
            obligation_id=UNIT_CONVERSION_OBLIGATION_ID,
            witness_id="w-unit-conversion-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="unit_conversions.GWh_to_MWh",
            text="1 GWh = 1000 MWh",
        ),
        reporting_period=ReportingPeriodSupport(
            period="2025-03",
            obligation_id=PERIOD_OBLIGATION_ID,
            witness_id="w-reporting-period-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="reporting_periods.2025-03",
            text="2025-03 is inside the active reporting window",
        ),
        allocation_support=AllocationSupport(
            share=0.5,
            line_a_mass_ton=LINE_A_MASS_TON,
            total_line_mass_ton=TOTAL_LINE_MASS_TON,
            binding_id=ALLOCATION_SUPPORT_BINDING_ID,
            obligation_id=ALLOCATION_SUPPORT_OBLIGATION_ID,
            witness_id="w-allocation-support",
            source="raw_sources/mes_line_mass.csv",
            span="line_mass_row:line_a",
            text="Line A 50,000 ton; total line mass 100,000 ton",
        ),
    )
```

- [ ] **Step 4: Delete local helper functions made obsolete by promotion**

Remove these functions from the acceptance scenario file:

```python
def _evidence_witnesses() -> tuple[EvidenceWitness, ...]:
def _checked_claims() -> tuple[CheckedClaim, ...]:
def _resolved_obligations() -> tuple[ProofObligation, ...]:
def _reference_bindings() -> tuple[ReferenceBinding, ...]:
def _derived_claims() -> tuple[DerivedClaim, ...]:
def _derived_claim(...):
def _calculated_values() -> dict[str, object]:
def _number(value: Decimal) -> int | float:
```

Keep `_projection_source(report)` because scenario projection still needs a source row assembled from checked and derived claims.

- [ ] **Step 5: Run scenario tests**

Run:

```bash
python -m pytest tests/test_synthetic_raw_claim_hypothesis_acceptance.py tests/test_domain_scenario_lab.py -q
```

Expected: PASS.

- [ ] **Step 6: Run scenario CLI**

Run:

```bash
python -m tests.domain_scenarios run-all
```

Expected output includes:

```text
Passed: 15/15
```

- [ ] **Step 7: Commit the scenario refactor**

```bash
git add tests/domain_scenarios/synthetic_raw_claim_hypothesis_acceptance/scenario.py
git commit -m "refactor: route raw claim acceptance through promotion boundary"
```

---

### Task 4: Sync Governance Docs With the New Boundary

**Files:**
- Modify: `docs/architecture/domain-scenario-pack-generation.md`
- Modify: `docs/architecture/trust-kernel-hardening.md`
- Modify: `tests/test_package_smoke.py`

- [ ] **Step 1: Update domain scenario pack generation doc**

In `docs/architecture/domain-scenario-pack-generation.md`, change the header line:

```text
Last checked against code: 2026-05-20
```

to:

```text
Last checked against code: 2026-05-21
```

Add this section after the existing source input discussion that mentions `synthetic_source_input`:

```markdown
## Raw Claim Promotion Boundary

Synthetic raw `ClaimHypothesis` examples may include LLM-like extractor
candidates, source snippets, aliases, unit hints, and allocation hints. These
raw candidates are not compiler authority.

Promotion from raw candidates into canonical compiler artifacts belongs in the
scenario/domain layer. The synthetic promotion helper may create:

```text
CheckedClaim
ReferenceBinding
DerivedClaim
resolved ProofObligation
CalculationTrace
```

It must not create:

```text
CommitReceipt
public projection
receipt ledger entries
```

The promotion boundary exists so scenario packs can show how domain/profile
support turns candidates into checked artifacts without teaching the trust
kernel domain-specific names such as plant aliases, unit conversion tables, or
allocation support records.
```

- [ ] **Step 2: Update trust kernel hardening doc**

In `docs/architecture/trust-kernel-hardening.md`, change:

```text
Last checked against code: 2026-05-20
```

to:

```text
Last checked against code: 2026-05-21
```

Add this paragraph under `## Core / Domain Boundary`:

```markdown
Raw claim promotion is a domain-layer operation. A promotion helper may turn
supported extractor candidates into `CheckedClaim`, `ReferenceBinding`,
`DerivedClaim`, and `CalculationTrace` artifacts, but the promoted
`CompileReport` still cannot authorize projection. `CommitReceipt` remains the
only public projection authority.
```

- [ ] **Step 3: Change smoke test date validation to per-doc expected dates**

In `tests/test_package_smoke.py`, replace:

```python
        assert "Last checked against code: 2026-05-20" in text
```

inside `test_architecture_docs_are_classified_by_governance_status` with:

```python
        assert f"Last checked against code: {checked_date}" in text
```

Change `expected_status` values from 3-tuples to 4-tuples. Use this exact map:

```python
    expected_status = {
        "active-surface-cutover.md": ("historical-note", "docs", "no", "2026-05-20"),
        "artifact-envelope-builder.md": ("active-contract", "persistence", "yes", "2026-05-20"),
        "document-governance.md": ("active-contract", "trust-kernel", "yes", "2026-05-20"),
        "domain-scenario-pack-generation.md": (
            "implementation-map",
            "scenario-lab",
            "limited",
            "2026-05-21",
        ),
        "extension-port-contracts.md": ("active-contract", "trust-kernel", "yes", "2026-05-20"),
        "legacy-archive-cutover-plan.md": ("historical-note", "docs", "no", "2026-05-20"),
        "llm-orchestrated-compiler-tool-loop.md": (
            "historical-note",
            "agent-layer",
            "no",
            "2026-05-20",
        ),
        "llm-worker-orchestration.md": ("north-star", "agent-layer", "limited", "2026-05-20"),
        "memory-assisted-compiler-loop.md": (
            "active-contract",
            "agent-layer",
            "yes",
            "2026-05-20",
        ),
        "obligation-kernel-working-theory.md": (
            "implementation-map",
            "trust-kernel",
            "limited",
            "2026-05-20",
        ),
        "persistence-ledger-boundary.md": ("active-contract", "persistence", "yes", "2026-05-20"),
        "receipt-proof-graph.md": ("active-contract", "explanation", "yes", "2026-05-20"),
        "retrieval-fabric-north-star.md": ("north-star", "retrieval", "limited", "2026-05-20"),
        "trust-kernel-extension-rings.md": ("active-contract", "trust-kernel", "yes", "2026-05-20"),
        "trust-kernel-hardening.md": ("active-contract", "trust-kernel", "yes", "2026-05-21"),
    }
```

Change the loop unpacking from:

```python
        status, owner, blocking = expected_status[path.name]
```

to:

```python
        status, owner, blocking, checked_date = expected_status[path.name]
```

- [ ] **Step 4: Run smoke tests**

Run:

```bash
python -m pytest tests/test_package_smoke.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit docs and smoke test update**

```bash
git add docs/architecture/domain-scenario-pack-generation.md docs/architecture/trust-kernel-hardening.md tests/test_package_smoke.py
git commit -m "docs: record raw claim promotion boundary"
```

---

### Task 5: Full Verification

**Files:**
- No source edits in this task.

- [ ] **Step 1: Run whitespace check**

Run:

```bash
git diff --check HEAD~3..HEAD
```

Expected: no output and exit code 0.

- [ ] **Step 2: Run full test suite**

Run:

```bash
python -m pytest -q
```

Expected output ends with:

```text
passed
```

The current baseline before this plan is `369 passed`; the exact count should increase after adding `tests/test_synthetic_raw_claim_promotion.py`.

- [ ] **Step 3: Run domain scenarios**

Run:

```bash
python -m tests.domain_scenarios run-all
```

Expected output includes:

```text
Passed: 15/15
```

- [ ] **Step 4: Confirm core did not import scenario or agent layers**

Run:

```bash
python -m pytest tests/test_package_smoke.py::test_comp_core_does_not_import_agent_layer -q
```

Expected: PASS.

Run:

```bash
rg -n "comp\\.scenarios|tests\\.domain_scenarios|minchoagnt" comp/compiler_tool comp/judgment comp/persistence
```

Expected: no output.

- [ ] **Step 5: Commit verification notes only if a tracked verification artifact was intentionally added**

No commit is needed when verification produces only terminal output.

---

## Out Of Scope For This Plan

- Do not add `AuthorityProfile` or `PolicyVersion`.
- Do not generalize formula evaluation beyond the raw claim acceptance scenario.
- Do not add a README quickstart.
- Do not add receipt/replay golden JSON fixtures.
- Do not move `minchoagnt` packaging or define `comp.views`.

Recommended follow-up PR order after this plan:

1. Receipt/replay golden snapshots for `CommitReceiptCitations`, `ProjectionValueCommitment`, `DependencyFingerprint`, and `ProjectionReplayReport`.
2. README 30-line E2E quickstart that uses the new promotion boundary.
3. Explicit active-surface packaging note for `minchoagnt`, `comp.views`, and archived legacy sources.

---

## Self-Review

- Spec coverage: The plan covers the agreed first move: extract raw candidate promotion from scenario fixture code while preserving receipt authority.
- Empty-marker scan: The plan contains no open blanks, delayed implementation markers, or unspecified test commands.
- Type consistency: The tests, module exports, and scenario refactor use the same type names: `SyntheticRawClaimPromotionProfile`, `PromotionClaimIds`, `SiteAliasSupport`, `UnitConversionSupport`, `ReportingPeriodSupport`, `AllocationSupport`, and `promote_raw_claim_hypothesis`.
- Authority check: The plan does not modify receipt builders, public projection, persistence replay, or compiler core authority gates.
