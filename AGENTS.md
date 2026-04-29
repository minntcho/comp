# AGENTS.md

이 문서는 `comp` 레포에서 GPT/agent가 작업할 때 따라야 하는 운영 규칙이다.

목표는 작업을 임시 대화 흐름에 의존하지 않고, GitHub Issue / PR / docs 상태판을 기준으로 반복 가능하게 운영하는 것이다.

---

## 1. Source of Truth

이 레포의 migration / refactor / architecture 작업은 아래 문서를 기준으로 진행한다.

1. `docs/migration-checklist.md`
2. `docs/issue-plan.md`
3. `docs/migration-plan.md`

각 문서의 역할은 다음과 같다.

```text
docs/migration-checklist.md
  전체 이행 청사진
  Done / Bridge / Now / Next / Later 상태판
  track별 acceptance criteria
  검증 커맨드
  진행 로그

docs/issue-plan.md
  checklist 항목을 GitHub Issue 작업 단위로 내리는 변환 문서
  issue 작성 형식
  issue 후보 초안
  scope / out-of-scope 기준

docs/migration-plan.md
  현재 bridge 상태
  구조 debt
  장기 이행 방향
```

작업을 시작하기 전에 항상 `docs/migration-checklist.md`를 먼저 확인한다.

---

## 2. Work Unit Model

이 레포의 기본 작업 단위는 다음과 같다.

```text
Checklist item
  -> GitHub Issue
  -> Branch
  -> Pull Request
  -> Issue close
  -> Checklist update
  -> Follow-up issue when needed
```

각 역할은 다음과 같다.

```text
Checklist item
  큰 청사진 속의 작업 후보

GitHub Issue
  작업 전 계약서
  범위, 완료 조건, 제외 범위, 테스트를 고정한다

Pull Request
  issue의 완료 조건을 만족했다는 실제 증거

Issue comment
  작업 결과와 남은 residue를 기록하는 로그

Follow-up issue
  이번 작업 범위를 벗어난 독립 후속 작업
```

---

## 3. Issue Selection Rule

새 작업을 시작할 때는 다음 순서로 issue 후보를 고른다.

1. `docs/migration-checklist.md`의 `Now` 항목을 우선 확인한다.
2. 이미 열린 GitHub Issue가 있으면 해당 issue를 우선 사용한다.
3. 열린 issue가 없으면 `docs/issue-plan.md` 형식에 맞춰 새 issue를 만든다.
4. `Next` 항목은 병렬 진행이 가능하거나 `Now` 항목이 막혔을 때 issue화한다.
5. `Later` 항목은 즉시 issue화하지 않는다. 명확한 작업 단위가 생긴 경우에만 backlog issue로 만든다.

---

## 4. Issue Format

새 GitHub Issue는 최소한 다음 항목을 포함한다.

```md
## Goal

## Why

## Scope

## Acceptance Criteria

## Out of Scope

## Suggested Tests

## Related Docs
```

특히 `Out of Scope`는 반드시 작성한다.

이 레포는 migration 중이므로, 한 issue에서 서로 다른 성격의 작업을 섞지 않는다.

---

## 5. Do Not Mix Rule

하나의 issue / PR 안에서 아래 작업을 섞지 않는다.

```text
- import convergence
- actual relocation
- architecture refactor
- behavior change
- facade removal
- judgment core absorption
- test-only cleanup
- docs-only clarification
```

예외가 필요하면 issue 본문이나 PR 본문에 이유를 명시한다.

기본 원칙은 다음과 같다.

```text
Import 정리는 import 정리만 한다.
Relocation은 relocation만 한다.
Architecture refactor는 packaging migration과 분리한다.
Behavior change는 별도 issue/PR로 분리한다.
```

---

## 6. Work Cycle

agent는 작업 명령을 받으면 다음 사이클을 따른다.

```text
1. 관련 checklist 항목 확인
2. 관련 GitHub Issue 확인 또는 생성
3. issue를 현재 작업자에게 assign
4. status label을 in-progress로 변경
5. issue scope 안에서만 작업
6. branch 생성
7. 코드/docs 수정
8. 관련 테스트 실행 또는 최소 검증 수행
9. PR 생성
10. PR 본문에 issue 연결
11. issue에 작업 요약 comment 남김
12. 완료 시 status label을 done으로 변경
13. issue close
14. checklist 상태 갱신
15. 남은 residue가 있으면 follow-up issue 생성
```

---

## 7. Assignment and Labels

작업 시작 시 issue에는 assignee와 status label을 붙인다.

기본 구분은 다음과 같다.

```text
assignee
  누가 이 작업을 맡았는지 나타낸다.

labels
  이 작업이 migration 지도 안에서 어디에 놓이는지 나타낸다.
```

즉 agent 이름이나 작업자 종류를 label로 표현하지 않는다.
작업자는 assignee로 표현하고, label은 작업의 좌표를 표현한다.

권장 label 체계:

```text
status:ready
status:in-progress
status:blocked
status:review
status:done

track:A-import
track:R-relocation
track:B-facade
track:C-architecture
track:docs

kind:migration
kind:cleanup
kind:docs
kind:test
kind:architecture
kind:refactor

area:dsl
area:eval
area:builtins
area:pipeline
area:runner
area:compat
area:views
area:judgment
area:docs
area:tests

risk:low
risk:medium
risk:high

flow:parallel-ok
flow:stacked
flow:blocked-by-pr
flow:blocked-by-issue
flow:needs-rebase
flow:ready-after-merge
```

각 label 축의 의미는 다음과 같다.

```text
status
  지금 issue를 집어도 되는지, 진행 중인지, 리뷰 단계인지 나타낸다.

track
  migration의 큰 작업 레일을 나타낸다.
  Do Not Mix Rule의 충돌 방지 경계로 사용한다.

kind
  변경의 성격을 나타낸다.
  예: migration, cleanup, docs, test, architecture, refactor.

area
  주로 영향을 받는 코드/문서 영역을 나타낸다.
  병렬 작업자가 같은 영역을 동시에 건드리는지 판단하는 데 사용한다.

risk
  회귀 가능성과 리뷰 강도를 나타낸다.

flow
  병렬 가능성, stacked PR 여부, blocking 관계, rebase 필요 여부를 나타낸다.
```

예시:

```text
track:R-relocation
kind:migration
area:dsl
risk:low
flow:parallel-ok
status:in-progress
```

이 조합은 DSL 영역의 실제 relocation 작업이며, 낮은 위험도로 병렬 진행 가능하고, 현재 작업 중이라는 뜻이다.

```text
track:A-import
kind:cleanup
area:pipeline
risk:medium
flow:blocked-by-pr
status:blocked
```

이 조합은 pipeline 영역의 import convergence 작업이지만, 선행 PR이 머지되기 전까지 막혀 있다는 뜻이다.

label이 아직 레포에 없으면 기존 label을 우선 사용한다.
새 label이 필요하면 작업 로그에 남기거나 별도 정리 issue를 만든다.

---

## 8. PR Rules

PR 본문에는 다음을 포함한다.

```md
## Summary

## Linked Issue

Closes #<issue-number>

## Changes

## Tests

## Notes
```

stacked PR인 경우 base branch를 반드시 명시한다.

```md
## Base Branch

This PR is stacked on `<branch-name>`.
```

PR은 가능한 한 issue 하나의 acceptance criteria만 만족해야 한다.

---

## 9. Completion Rule

작업 완료는 코드 변경만으로 끝나지 않는다.

완료 조건은 다음을 모두 포함한다.

```text
- issue acceptance criteria 충족
- 관련 테스트 또는 검증 수행
- PR 생성
- issue에 결과 comment 기록
- checklist 상태 갱신 필요 여부 확인
- follow-up residue 분리
```

PR이 merge된 뒤에는 issue를 close한다.

완료된 항목은 `docs/migration-checklist.md`의 `Done` 또는 진행 로그에 반영한다.

---

## 10. Follow-up Issue Rule

작업이 끝날 때마다 무조건 새 issue를 만들지 않는다.

follow-up issue는 아래 조건 중 하나를 만족할 때만 만든다.

```text
- 이번 issue의 scope 밖 문제가 발견됨
- 다음 작업 단위가 독립적으로 분리 가능함
- 지금 PR에 넣으면 scope가 커짐
- 병렬 작업으로 넘길 수 있음
- TODO를 코드나 문서에 묻어두면 잊힐 가능성이 큼
```

follow-up issue에는 원래 issue나 PR을 참조한다.

```md
Related to #<issue-number>
Follow-up from #<pr-number>
```

---

## 11. Checklist Update Rule

`docs/migration-checklist.md`는 전체 migration 상태판이다.

아래 상황에서는 checklist를 갱신한다.

```text
- Now 항목이 완료되어 Done으로 이동해야 할 때
- Bridge state 항목이 해소되었을 때
- Next 항목이 Now로 승격되었을 때
- 새로운 migration debt가 발견되었을 때
- 검증 커맨드가 바뀌었을 때
- PR 분할 계획이 바뀌었을 때
```

단순한 작업 메모는 checklist에 넣지 않는다.
세부 진행 기록은 issue comment나 PR 본문에 둔다.

---

## 12. Track Boundaries

### A-track: Import Convergence

목표:

```text
신규/수정 코드의 import 경로를 comp.* 중심으로 수렴한다.
legacy import는 compat/bridge 문맥으로 제한한다.
```

주의:

```text
- relocation과 섞지 않는다.
- behavior change와 섞지 않는다.
- import cycle을 특히 확인한다.
```

### R-track: Actual Relocation

목표:

```text
top-level implementation을 comp package 내부 구현으로 이동한다.
top-level legacy module은 thin wrapper로 축소한다.
package import와 legacy import의 identity/parity를 유지한다.
```

주의:

```text
- import convergence PR과 섞지 않는다.
- architecture change와 섞지 않는다.
- smoke/parity test를 추가한다.
```

### B-track: Facade Thinness

목표:

```text
공개 API로 유지할 facade와 임시 bridge wrapper를 구분한다.
wrapper가 의미 변경을 담지 못하도록 기준을 세운다.
```

주의:

```text
- 제거보다 inventory와 thinness rule을 먼저 둔다.
- compatibility 경로를 갑자기 깨지 않는다.
```

### Architecture Track

목표:

```text
emit / governance / projection / commit / receipt / judgment core의 책임 경계를 정리한다.
```

주의:

```text
- packaging migration과 섞지 않는다.
- 구현된 현재 사실과 장기 target semantics를 구분한다.
- 문서에서 미래 구조를 이미 완료된 것처럼 쓰지 않는다.
```

---

## 13. Verification

작업 범위에 따라 `docs/migration-checklist.md`의 검증 커맨드를 우선 따른다.

기본 smoke:

```bash
pytest -q
```

package / facade 관련:

```bash
pytest -q tests/test_package_smoke.py
pytest -q tests/test_runner_package_facades.py tests/test_pipeline_package_facades.py
```

relocation 관련 테스트는 이동한 모듈에 맞는 package-location test를 추가하거나 갱신한다.

---

## 14. Agent Behavior Rules

agent는 다음 원칙을 따른다.

```text
- 작업 전에 관련 docs를 읽는다.
- issue 없이 큰 작업을 바로 시작하지 않는다.
- issue scope를 벗어나는 변경은 follow-up issue로 분리한다.
- 의미 변경이 아닌 PR에서는 behavior를 바꾸지 않는다.
- docs와 코드가 충돌하면 현재 구현 사실을 먼저 확인한다.
- 완료했다고 말하기 전에 실제 변경/PR/issue 상태를 확인한다.
- 불확실한 내용은 단정하지 않고 issue/PR comment에 명시한다.
```

---

## 15. Command Shortcut

사용자가 다음처럼 말하면:

```text
체크리스트 기준으로 issue 사이클 돌려줘.
```

agent는 다음 의미로 처리한다.

```text
1. docs/migration-checklist.md 확인
2. 적절한 Now / Next 항목 선택
3. 기존 issue 확인 또는 새 issue 생성
4. assignee / status label 설정
5. 작업 수행
6. PR 생성
7. issue comment 기록
8. 완료 처리
9. checklist 갱신
10. 필요한 follow-up issue 생성
```
