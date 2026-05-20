# Trust Kernel Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the `comp` trust kernel by removing ambient domain defaults, adding profile behavior fingerprints to receipt traces, and extending the canonical scenario through persistence replay.

**Architecture:** Keep the current package layout. Add deterministic fingerprint helpers near the profile model, carry the fingerprint through commit package and receipt citations, and make domain-specific compiler behavior explicit in tests and scenario fixtures. Extend the canonical scenario with artifact envelopes and replay verification without adding durable storage or production retrieval infrastructure.

**Tech Stack:** Python 3.11, dataclasses, pytest, existing `comp.persistence.artifact_digest`, in-memory artifact store and receipt ledger.

---

## File Map

- Modify `docs/index.md` to link the hardening standard.
- Modify `comp/compiler_tool/tool.py` to remove ESG-ish ambient defaults.
- Modify `tests/test_compiler_tool_contract.py` to prove domain behavior is explicit.
- Modify `tests/domain_scenarios/canonical_working_loop/fixtures.py` to pass known fields and units explicitly.
- Modify `comp/compiler_tool/profiles.py` to add profile fingerprint data.
- Modify `comp/compiler_tool/__init__.py` to export the fingerprint API.
- Modify `tests/test_compiler_profile_contract.py` to cover deterministic fingerprints.
- Modify `comp/compiler_tool/commit_package.py` to carry profile fingerprint metadata.
- Modify `comp/compiler_tool/receipt_builder.py` and `comp/judgment/receipts.py` to cite profile fingerprints.
- Modify `tests/test_commit_receipt_builder.py` to verify receipt citations include profile fingerprints.
- Modify `tests/domain_scenarios/canonical_working_loop/scenario.py` and `tests/test_canonical_working_loop_scenario.py` to replay the canonical projection through persistence.

---

### Task 1: Make CompilerTool Domain Behavior Explicit

**Files:**
- Modify: `tests/test_compiler_tool_contract.py`
- Modify: `comp/compiler_tool/tool.py`
- Modify: `tests/domain_scenarios/canonical_working_loop/fixtures.py`

- [ ] **Step 1: Write the failing test for no ambient known fields**

Add this test to `tests/test_compiler_tool_contract.py`:

```python
def test_compiler_tool_has_no_domain_known_fields_by_default():
    report = CompilerTool().compile_interpretation(
        _hypothesis(
            claims=(
                _claim("activity", "electricity", "w-activity"),
            ),
            witnesses=(_witness("w-activity", "activity"),),
        )
    )

    assert report.status == "unchecked"
    assert report.checked_claims == ()
    assert report.unchecked_areas == (
        UncheckedArea(field="activity", reason="missing_rule_coverage"),
    )
```

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
pytest tests/test_compiler_tool_contract.py::test_compiler_tool_has_no_domain_known_fields_by_default -q
```

Expected: FAIL because default `CompilerTool` currently knows `activity`.

- [ ] **Step 3: Remove ambient defaults from CompilerTool**

Change the constructor in `comp/compiler_tool/tool.py` to require explicit known
fields by default:

```python
    def __init__(
        self,
        *,
        allowed_units: frozenset[str] = frozenset(),
        known_fields: frozenset[str] = frozenset(),
    ) -> None:
        self.allowed_units = frozenset(unit.lower() for unit in allowed_units)
        self.known_fields = known_fields
```

- [ ] **Step 4: Make existing tests and canonical fixture explicit**

Update test constructors that expect `activity`, `amount`, `unit`, or
`reporting_year` to pass:

```python
CompilerTool(
    allowed_units=frozenset({"kwh"}),
    known_fields=frozenset({"activity", "amount", "unit", "reporting_year"}),
)
```

Update `compile_raw_evidence()` in
`tests/domain_scenarios/canonical_working_loop/fixtures.py` to include both:

```python
return CompilerTool(
    allowed_units=frozenset({"kwh"}),
    known_fields=frozenset(
        {
            "activity",
            "electricity_kwh",
            "unit",
            "reporting_year",
            "geography",
        }
    ),
).compile_interpretation(extract_raw_evidence(raw_text))
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
pytest tests/test_compiler_tool_contract.py tests/test_canonical_working_loop_scenario.py -q
```

Expected: all selected tests pass.

---

### Task 2: Add Deterministic Profile Fingerprints

**Files:**
- Modify: `tests/test_compiler_profile_contract.py`
- Modify: `comp/compiler_tool/profiles.py`
- Modify: `comp/compiler_tool/__init__.py`

- [ ] **Step 1: Write failing fingerprint tests**

Add imports in `tests/test_compiler_profile_contract.py`:

```python
from comp.compiler_tool import profile_fingerprint
```

Add tests:

```python
def test_profile_fingerprint_is_stable_for_same_active_behavior():
    domain = _domain(
        rules=(_rule("fixture.rule.v1"),),
        rubrics=(_rubric("fixture.rubric.v1"),),
        judge_policies=(_judge_policy("fixture.judge.v1"),),
        retrieval_query_policies=(_retrieval_policy("fixture.retrieval.v1"),),
    )
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(domain,),
        active_rule_ids=("fixture.rule.v1",),
        active_rubric_ids=("fixture.rubric.v1",),
        judge_policy_id="fixture.judge.v1",
        active_retrieval_policy_ids=("fixture.retrieval.v1",),
        projection_policy_id="fixture.projection.v1",
    )

    assert profile_fingerprint(profile) == profile_fingerprint(profile)
    assert profile_fingerprint(profile).digest.startswith("sha256:")


def test_profile_fingerprint_changes_when_active_policy_changes():
    domain = _domain(
        rules=(),
        retrieval_query_policies=(
            _retrieval_policy("fixture.retrieval.a.v1"),
            _retrieval_policy("fixture.retrieval.b.v1"),
        ),
    )
    first = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(domain,),
        active_retrieval_policy_ids=("fixture.retrieval.a.v1",),
    )
    second = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(domain,),
        active_retrieval_policy_ids=("fixture.retrieval.b.v1",),
    )

    assert profile_fingerprint(first).digest != profile_fingerprint(second).digest
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
pytest tests/test_compiler_profile_contract.py::test_profile_fingerprint_is_stable_for_same_active_behavior tests/test_compiler_profile_contract.py::test_profile_fingerprint_changes_when_active_policy_changes -q
```

Expected: import error or attribute error because `profile_fingerprint` does not
exist.

- [ ] **Step 3: Implement fingerprint model**

Add to `comp/compiler_tool/profiles.py`:

```python
@dataclass(frozen=True)
class ProfileFingerprint:
    profile_id: str
    digest: str
    body: tuple[tuple[str, Any], ...]
```

Add:

```python
def profile_fingerprint(profile: CompilerProfile) -> ProfileFingerprint:
    validate_compiler_profile(profile)
    body = (
        ("profile_id", profile.profile_id),
        ("core_invariant_version", profile.core_invariant_version),
        (
            "domain_packs",
            tuple(
                (domain.domain_id, domain.version)
                for domain in profile.domain_packs
            ),
        ),
        ("active_rule_ids", profile.active_rule_ids),
        ("active_rubric_ids", profile.active_rubric_ids),
        ("judge_policy_id", profile.judge_policy_id),
        ("active_retrieval_policy_ids", profile.active_retrieval_policy_ids),
        ("projection_policy_id", profile.projection_policy_id),
    )
    from comp.persistence.digest import artifact_digest

    return ProfileFingerprint(
        profile_id=profile.profile_id,
        digest=artifact_digest(
            artifact_kind="compiler_profile",
            schema_version="profile-fingerprint-v1",
            body=dict(body),
        ),
        body=body,
    )
```

- [ ] **Step 4: Export the API**

Update `comp/compiler_tool/__init__.py` imports and `__all__` with:

```python
ProfileFingerprint,
profile_fingerprint,
```

- [ ] **Step 5: Verify GREEN**

Run:

```bash
pytest tests/test_compiler_profile_contract.py -q
```

Expected: all profile contract tests pass.

---

### Task 3: Carry Profile Fingerprints Into Receipts

**Files:**
- Modify: `tests/test_commit_receipt_builder.py`
- Modify: `comp/compiler_tool/commit_package.py`
- Modify: `comp/compiler_tool/receipt_builder.py`
- Modify: `comp/judgment/receipts.py`

- [ ] **Step 1: Write failing receipt citation test**

In `tests/test_commit_receipt_builder.py`, create a complete package with a
profile fingerprint and assert the receipt cites it:

```python
def test_commit_receipt_cites_profile_fingerprint():
    package = build_commit_package(
        _accepted_report(),
        subject_id="subject-1",
        profile_id="fixture-profile",
        profile_fingerprint_digest="sha256:fixture-profile",
    )
    decision = decide_governance(package)

    receipt = build_commit_receipt(
        package,
        decision,
        public_row_id="public-row-1",
        projection_id="projection-1",
    )

    assert receipt.citations.profile_fingerprint_digest == "sha256:fixture-profile"
    assert (
        "profile_fingerprint_digest",
        "sha256:fixture-profile",
    ) in receipt.barrier_snapshot
```

Use the existing helper names in the file. If `_accepted_report()` does not
exist, add the smallest local helper that returns an accepted report with one
checked claim.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
pytest tests/test_commit_receipt_builder.py::test_commit_receipt_cites_profile_fingerprint -q
```

Expected: FAIL because package and citations do not carry the field.

- [ ] **Step 3: Add the field to CommitPackage**

Add to `CommitPackage` in `comp/compiler_tool/commit_package.py`:

```python
    profile_fingerprint_digest: str | None = None
```

Add a keyword argument to `build_commit_package()`:

```python
    profile_fingerprint_digest: str | None = None,
```

Pass it into the dataclass.

- [ ] **Step 4: Add the field to CommitReceiptCitations**

Add to `CommitReceiptCitations` in `comp/judgment/receipts.py` after
`profile_id`:

```python
    profile_fingerprint_digest: str | None = None
```

Add it to `to_barrier_snapshot()`:

```python
("profile_fingerprint_digest", self.profile_fingerprint_digest),
```

- [ ] **Step 5: Populate citations in receipt_builder**

Update `_receipt_citations()` in `comp/compiler_tool/receipt_builder.py`:

```python
profile_fingerprint_digest=package.profile_fingerprint_digest,
```

- [ ] **Step 6: Verify GREEN**

Run:

```bash
pytest tests/test_commit_receipt_builder.py tests/test_receipt_gated_projection.py -q
```

Expected: all selected tests pass.

---

### Task 4: Extend Canonical Scenario Through Persistence Replay

**Files:**
- Modify: `tests/test_canonical_working_loop_scenario.py`
- Modify: `tests/domain_scenarios/canonical_working_loop/scenario.py`

- [ ] **Step 1: Write failing replay test**

Add to `tests/test_canonical_working_loop_scenario.py`:

```python
def test_canonical_working_loop_replays_projection_from_receipt_artifacts():
    result = run_canonical_working_loop_scenario()

    assert result.projection_replay is not None
    assert result.projection_replay.public_row == result.projection
    assert result.projection_replay.receipt_key.public_row_id == (
        "public-row:canonical-raw-pcf-1"
    )
    assert (
        "governance-decision:commit-package:product:canonical-raw-pcf-1",
        "sha256:",
    ) in tuple(
        (artifact_id, digest[:7])
        for artifact_id, digest in result.projection_replay.artifact_digests
    )
```

If `DomainScenarioResult` does not yet expose `projection_replay`, add that in
this task as a frozen optional field with default `None`.

- [ ] **Step 2: Run the test and verify RED**

Run:

```bash
pytest tests/test_canonical_working_loop_scenario.py::test_canonical_working_loop_replays_projection_from_receipt_artifacts -q
```

Expected: FAIL because the scenario does not yet expose replay.

- [ ] **Step 3: Add replay field to DomainScenarioResult**

Modify `tests/domain_scenarios/core.py`:

```python
from comp.persistence import ProjectionReplayReport
```

Add to `DomainScenarioResult`:

```python
projection_replay: ProjectionReplayReport | None = None
```

Add an optional parameter to `build_domain_scenario_result()` and pass it
through.

- [ ] **Step 4: Build artifact envelopes in the canonical scenario**

In `tests/domain_scenarios/canonical_working_loop/scenario.py`, after commit
preparation succeeds, create an `InMemoryArtifactStore`, record envelopes for:

```text
commit_package
governance_decision
checked claim source commitments
reference_binding
derived_claim
calculation_trace
formula
evidence_witness
```

Use `ArtifactEnvelope.from_body()` with small JSON-ready bodies containing the
ids and fields already cited by the receipt.

- [ ] **Step 5: Record receipt and replay projection**

Use:

```python
ledger = InMemoryReceiptLedger()
ledger.record(preparation.receipt)
projection_replay = replay_public_projection(
    projection,
    ProjectionSpec(
        "canonical-pcf-public-row",
        ("electricity_kwh", "reporting_year", "co2e_kg"),
    ),
    receipt=preparation.receipt,
    artifacts=artifact_store,
)
```

Pass `projection_replay=projection_replay` into
`build_domain_scenario_result()`.

- [ ] **Step 6: Verify GREEN**

Run:

```bash
pytest tests/test_canonical_working_loop_scenario.py tests/test_persistence_projection_replay.py -q
```

Expected: all selected tests pass.

---

### Task 5: Full Verification

**Files:**
- No additional file edits.

- [ ] **Step 1: Run the full test suite**

Run:

```bash
pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Inspect the diff**

Run:

```bash
git diff -- docs comp tests
git status --short
```

Expected: only intended docs, compiler tool, receipt, and scenario files changed.

- [ ] **Step 3: Commit**

Run:

```bash
git add docs comp tests
git commit -m "feat: harden trust kernel traceability"
```

Expected: commit succeeds after the full test suite passes.
