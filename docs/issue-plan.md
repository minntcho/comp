# Issue Plan

이 문서는 `comp` 이행 작업을 GitHub Issue 단위로 관리하기 위한 운영 문서입니다.

중요:
이 문서는 `migration-checklist.md`를 대체하지 않습니다.
`migration-checklist.md`는 전체 이행 상태판이고, 이 문서는 그 상태판에서 실제 GitHub Issue로 내려갈 작업 단위를 정리합니다.

---

## 역할 구분

`comp`에서는 문서, issue, PR의 역할을 다음처럼 나눕니다.

```text
docs/
  왜 이 구조로 가는가
  장기 방향은 무엇인가
  전체 이행 순서는 무엇인가

GitHub Issue
  지금 한 덩어리 작업은 무엇인가
  범위는 어디까지인가
  완료 조건은 무엇인가
  어떤 테스트를 통과해야 하는가

Pull Request
  issue의 완료 조건을 만족시키는 실제 변경
```

즉 issue는 설계 발산용 메모가 아니라,
**작업 전 계약서**에 가깝습니다.

---

## 기본 작업 흐름

권장 흐름은 다음과 같습니다.

```text
1. docs/migration-checklist.md에서 Now / Next 항목을 확인한다.
2. 지금 처리할 issue를 선택한다.
3. issue의 Scope / Out of Scope / Acceptance Criteria를 확인한다.
4. branch를 만들고 작업한다.
5. PR 본문에서 issue를 연결한다.
6. 테스트와 리뷰를 통과시킨다.
7. PR merge 후 issue를 close한다.
8. 필요하면 migration-checklist.md를 Done / Bridge / Now 상태에 맞게 갱신한다.
```

---

## Issue 작성 원칙

각 issue는 최소한 다음 항목을 가져야 합니다.

- Goal
- Why
- Scope
- Acceptance Criteria
- Out of Scope
- Suggested Tests
- Related Docs

특히 `Out of Scope`가 중요합니다.
이 레포는 migration 중이므로, 한 issue에서 import 정리, relocation, runner 이동, architecture refactor를 섞지 않습니다.

---

## 초기 Issue 후보

아래 issue들은 현재 `migration-checklist.md`의 Now / Next 항목을 GitHub Issue로 옮기기 위한 초안입니다.

---

## Issue 1: Relocate `runtime_env` implementation into `comp` package

### Goal

Move the actual `runtime_env` implementation into the `comp` package while preserving the existing top-level `runtime_env.py` import path as a compatibility wrapper.

### Why

`runtime_env.py` is still a top-level implementation module.

Many runner/pass-adjacent modules depend on:

- `ScopeFrame`
- `ScopePath`
- `LexCandidate`
- `RuntimeEnv`
- `SiteRecord`
- `build_runtime_env`

This module should move before deeper runner relocation, because it is one of the core runtime contracts used across the pipeline.

### Scope

- Move the actual implementation to `comp/runtime_env.py`.
- Keep top-level `runtime_env.py` as a thin compatibility wrapper.
- Preserve object identity between package and legacy imports.
- Update package-side imports where safe.
- Add smoke/parity tests for package location.

### Acceptance Criteria

Package imports and legacy imports must refer to the same objects.

At minimum, verify identity for:

- `ScopeFrame`
- `ScopePath`
- `LexCandidate`
- `RuntimeEnv`
- `SiteRecord`
- `build_runtime_env`

### Out of Scope

- No artifact relocation.
- No runner relocation.
- No behavior change.
- No architecture change.
- No judgment semantics change.

### Suggested Tests

```bash
pytest -q tests/test_package_smoke.py
pytest -q tests/test_runtime_env_package_location.py
pytest -q
```

### Suggested Labels

- `track:R-relocation`
- `kind:migration`
- `risk:medium`

### Related Docs

- `docs/migration-checklist.md`
- `docs/migration-plan.md`
- `docs/current-pipeline.md`

---

## Issue 2: Relocate `artifacts` implementation into `comp` package

### Goal

Move the actual `artifacts` implementation into the `comp` package while preserving the existing top-level `artifacts.py` import path as a compatibility wrapper.

### Why

`artifacts.py` defines the central artifact contract of the current staged pipeline.

It contains core data structures such as:

- `CompileArtifacts`
- `TokenOccurrence`
- `ClaimArtifact`
- `RoleSlotArtifact`
- `PartialFrameArtifact`
- `CanonicalRowArtifact`
- `DiagnosticArtifact`
- `GovernanceDecisionArtifact`
- `CalculationArtifact`

Since most passes communicate through these objects, relocating this module is required before runner-adjacent relocation and deeper import convergence.

### Scope

- Move the actual implementation to `comp/artifacts.py` or an equivalent package path.
- Keep top-level `artifacts.py` as a thin compatibility wrapper.
- Preserve object identity between legacy and package imports.
- Update package-side imports where safe.
- Add package-location parity tests.

### Acceptance Criteria

Package imports and legacy imports must point to the same objects.

At minimum, verify identity for:

- `CompileArtifacts`
- `TokenOccurrence`
- `ClaimArtifact`
- `RoleSlotArtifact`
- `PartialFrameArtifact`
- `CanonicalRowArtifact`
- `DiagnosticArtifact`
- `GovernanceDecisionArtifact`
- `CalculationArtifact`
- `warning_codes_from_diagnostics`
- `error_codes_from_diagnostics`

### Out of Scope

- No `runtime_env` relocation unless already completed.
- No runner relocation.
- No emit/governance behavior change.
- No artifact schema change.
- No judgment architecture change.

### Suggested Tests

```bash
pytest -q tests/test_package_smoke.py
pytest -q tests/test_artifacts_package_location.py
pytest -q tests/test_artifact_contracts.py
pytest -q
```

### Suggested Labels

- `track:R-relocation`
- `kind:migration`
- `risk:medium`

### Related Docs

- `docs/migration-checklist.md`
- `docs/migration-plan.md`
- `docs/current-pipeline.md`
- `docs/testing.md`

---

## Issue 3: Clean package and compatibility imports after runtime/artifact relocation

### Goal

After `runtime_env` and `artifacts` have been relocated into the `comp` package, clean package-side and compatibility imports so new code converges on `comp.*` paths.

### Why

The repository is currently in a bridge state.

Some modules already live under `comp.*`, while several runner/pass-adjacent modules still import from top-level legacy modules.

Once `runtime_env` and `artifacts` are relocated, imports should be normalized without changing behavior.

### Scope

- Update package-side modules to prefer `comp.*` imports.
- Keep top-level wrappers only for compatibility.
- Ensure `comp.compat.*` remains a thin bridge layer.
- Reduce accidental top-level imports in newly relocated/package code.
- Check for import cycles caused by eager imports.

### Acceptance Criteria

- New/package implementation code uses `comp.*` imports where practical.
- Legacy top-level import paths still work.
- `pytest` collection succeeds without import cycles.
- No runtime behavior changes.
- No façade gains new behavior.

### Out of Scope

- No new relocation of runner modules.
- No façade removal yet.
- No architecture refactor.
- No emit/governance behavior change.
- No judgment core absorption.

### Suggested Tests

```bash
pytest -q tests/test_package_smoke.py
pytest -q tests/test_runner_package_facades.py
pytest -q tests/test_pipeline_package_facades.py
pytest -q
```

### Suggested Labels

- `track:A-import`
- `kind:cleanup`
- `kind:migration`
- `risk:medium`

### Related Docs

- `docs/migration-checklist.md`
- `docs/migration-plan.md`

---

## Issue 4: Polish `docs/worked-example.md` against current implementation

### Goal

Tighten `docs/worked-example.md` so it clearly separates:

1. what the current staged pipeline actually does
2. what the long-term judgment-first model is meant to explain

### Why

`worked-example.md` is useful as a bridge document, but several parts should remain aligned with current implementation behavior so readers do not confuse current behavior with target semantics.

This document should become the main small-example walkthrough for the docs set.

### Scope

Revise the worked example to clarify:

- `energy_use_parser` can be the parser name, but the frame type should align with `ActivityObservation`.
- `entity_id` is currently resolved during projection from `site_id`, while long-term semantics may model it as an inferred/provenance-backed fact.
- Current default `EmitPass` only materializes committed frames.
- Governance hold after row materialization differs from non-committed/review draft views.
- Current commit barrier adapter is thinner than the long-term barrier model.
- Raw receipt fields and human-facing explanation view should be separated.
- Candidate frontier should include a small numeric table.
- A pseudo-ESGDL block should be included and clearly marked as illustrative.
- Calculation output should be shown with a small example factor.

### Acceptance Criteria

- The document clearly says which parts are current implementation and which parts are target semantics.
- The example uses `ActivityObservation` as the frame type.
- The hold path distinguishes:
  - current staged pipeline behavior
  - long-term DraftView / ReviewView / PublicExport semantics
- Selection receipt and explanation view are not conflated.
- The example includes a small candidate frontier table.
- The example includes a minimal calculation example.
- The document remains a walkthrough, not a full grammar reference.

### Out of Scope

- No code changes.
- No ESGDL grammar changes.
- No test changes unless broken links are introduced.
- No rewrite of `current-pipeline.md`, `judgment-language.md`, or `core-semantics.md`.

### Suggested Verification

Read `docs/worked-example.md` together with:

- `docs/current-pipeline.md`
- `docs/judgment-language.md`
- `docs/views-ledger.md`
- `docs/execution-model.md`

Confirm that the worked example does not contradict those documents.

### Suggested Labels

- `track:docs`
- `kind:cleanup`
- `risk:low`

### Related Docs

- `docs/worked-example.md`
- `docs/current-pipeline.md`
- `docs/judgment-language.md`
- `docs/core-semantics.md`
- `docs/execution-model.md`
- `docs/views-ledger.md`
- `docs/esgdl-reference.md`

---

## 운영 메모

이 문서의 issue 초안은 실제 GitHub Issue를 열기 위한 starting point입니다.

실제 issue를 생성한 뒤에는 다음 중 하나를 선택합니다.

1. 이 문서에 issue 번호를 추가한다.
2. `migration-checklist.md`의 해당 항목 옆에 issue 번호를 추가한다.
3. PR 본문에서 `Closes #issue_number` 형식으로 연결한다.

권장 방식은 2번과 3번입니다.
이 문서는 issue 후보를 정리하는 운영 문서로 유지하고, 실제 진행 상태는 `migration-checklist.md`와 GitHub Issue/PR에서 추적합니다.
