# Worked Example

이 문서는 `comp`를 **작은 입력 하나로 끝까지 따라가는 예제**로 설명한다.

중요:
이 문서는 `current-pipeline.md`를 대체하지 않는다.
또 `judgment-language.md`, `core-semantics.md`, `spec-pipeline.md`를 반복 설명하는 문서도 아니다.

이 문서의 목적은 다음 하나다.

> `comp`에서 raw 입력이 어떻게 seed가 되고,
> 어떤 candidate가 생기고,
> 왜 어떤 후보가 선택되거나 review로 남고,
> 어떤 조건에서 public row가 되거나 hold 되는지를
> 한 사례로 연결해서 보여 준다.

---

## 이 예제가 보여 주는 것

이 예제는 다음 흐름을 한 번에 본다.

1. raw fragment
2. token / parser / infer / governance 선언
3. 현재 pipeline에서의 claim / frame / row 생성
4. judgment language 관점에서의 subject / fact / receipt
5. frontier / winner / review 가능성
6. commit barrier
7. public projection
8. explanation / receipt / ledger 관점

즉 이 문서는
**현재 구현 흐름**과
**장기 judgment-first 설명**을
같은 사례 위에 겹쳐 보는 문서다.

중요:
이 예제는 현재 코드와 정확히 1:1로 대응되는 고정 fixture가 아니다.
현재 staged pipeline과 장기 judgment-first 의미론을 같은 사례로 설명하기 위한 최소 예제다.

---

## 1. 예제 시나리오

가장 작은 예제로 다음 같은 입력을 가정한다.

```text
Site Alpha consumed 1000 kWh electricity in 2025-01.
```

이 입력에서 우리가 기대하는 최종 public row는 대략 다음과 같다.

```text
site_id = "site_alpha"
entity_id = "entity_alpha"
period = "2025-01"
activity_type = "electricity"
raw_amount = 1000
raw_unit = "kWh"
standardized_amount = 1000
standardized_unit = "kWh"
scope_category = "scope2"
```

하지만 `comp`는 이 값을 곧바로 정답 row로 만들지 않는다.
먼저 후보, 근거, provenance, hazard를 거치는 중간 상태를 만든다.

---

## 2. 최소 spec 가정

설명을 위해 아주 작은 ESGDL/spec 조각이 있다고 가정한다.

### token
- 숫자를 `raw_amount` 후보로 추출
- `kWh`를 `raw_unit` 후보로 추출
- `electricity`를 `activity_type` 후보로 추출
- `Site Alpha`를 `site` 후보로 추출
- `2025-01`을 `period` 후보로 추출

### parser
- 위 token들을 하나의 `energy_use` frame으로 조립

### infer
- `site`가 있으면 registry를 통해 `entity_id`를 유도 가능

### resolver
- 같은 role에 여러 candidate가 있으면 score / specificity / hazard를 기준으로 대표 후보를 정함

### governance
- 필수 필드가 있고
- blocking error가 없고
- provenance가 충분하면 public row 승격을 허용

중요:
이 문서의 목적은 ESGDL 문법 자체를 설명하는 것이 아니라,
이런 선언이 **어떤 판단 구조를 만든다고 볼 수 있는지**를 보여 주는 것이다.

---

## 3. 현재 pipeline에서 보면

`current-pipeline.md` 기준으로 이 예제는 대략 이렇게 흐른다.

### 3.1 LexPass

fragment에서 token occurrence를 찾는다.

예:
- `"Site Alpha"`
- `"1000"`
- `"kWh"`
- `"electricity"`
- `"2025-01"`

결과:
- token occurrence 집합 생성

### 3.2 ParsePass

이 token들을 바탕으로 claim과 partial frame을 만든다.

예:
- claim(site = `"Site Alpha"`)
- claim(raw_amount = `1000`)
- claim(raw_unit = `"kWh"`)
- claim(activity_type = `"electricity"`)
- claim(period = `"2025-01"`)

그리고 `energy_use` frame 하나가 생긴다.

결과:
- claim 추가
- frame 추가

### 3.3 ScopeResolutionPass

context와 scope 규칙을 사용해 후보를 보정한다.

예:
- site alias를 실제 site registry 후보와 연결
- 일부 slot의 role/path를 보정

결과:
- frame 내부 slot 상태 보정
- claim 상태 일부 보정

### 3.4 InferencePass

명시적으로 쓰이지 않은 값을 규칙으로 추가한다.

예:
- `site_alpha`가 확인되면 `entity_alpha` 후보 생성

결과:
- inferred claim 추가

### 3.5 SemanticPass

constraint / diagnostic / rule builtin 평가를 통해 warning/error를 누적한다.

예:
- 필수 필드 존재 여부 확인
- 금지 조합 여부 확인
- 값의 정합성 점검

결과:
- diagnostics 누적

### 3.6 RepairPass

slot별 active/shadow/frozen/rejected를 정리하고,
selection 관련 runtime 값을 계산한다.

예:
- `site` slot 후보들 중 active 후보 결정
- shadow / rejected 후보 정리
- selection receipt 저장

결과:
- slot lifecycle 정리
- frame status 정리
- selection receipt 저장

### 3.7 EmitPass

committed frame을 대상으로 canonical row를 materialize한다.

중요:
- 현재 구조에서는 row가 `artifacts.rows`에 materialize된다.
- 하지만 장기 구조 설명에선 이 row를 projection 쪽으로 다시 본다.

### 3.8 GovernancePass

row 단위 policy와 commit barrier를 보고 merge/hold/skip을 결정한다.

결과:
- merge_log
- event_log
- commit_log
- row status 일부 변경

### 3.9 CalculationPass

merge 가능한 row를 기준으로 후속 계산을 수행한다.

즉 현재 구현 관점에서는
**하나의 artifact container가 stages를 지나며 정제된다**고 보는 것이 가장 정확하다.

---

## 4. judgment language로 다시 보면

같은 사례를 장기 judgment-first 관점으로 보면,
중심은 row가 아니라 **judgeable subject와 fact**다.

### 4.1 data-side subject

이 예제에서 중요한 data-side subject는 대략 다음과 같다.

- `claim`
  - 각 role에 대한 개별 후보 주장
- `bundle`
  - 함께 경쟁하는 후보 묶음
- `draft`
  - 아직 public 이전 상태
- `public_row`
  - commit barrier를 통과한 공개 상태

### 4.2 spec-side subject

같은 사례를 가능하게 만드는 spec-side subject도 있다.

- `transfer_rule`
- `selection_policy`
- `commit_policy`
- `projection`
- `compiled_program`

즉 rule이나 policy도 그냥 코드 조각이 아니라
**판정 가능한 객체**로 본다.

### 4.3 공통 predicate vocabulary

이 예제에서 특히 중요한 predicate는 다음이다.

- `well_formed`
- `supported`
- `unsafe`
- `stale`
- `fresh`
- `admissible`
- `requires_review`
- `committable`

즉 질문은
“row가 있느냐”가 아니라
“어떤 subject가 어떤 판정을 받느냐”가 된다.

---

## 5. seed fact와 초기 상태

이 입력은 먼저 seed fact를 만든다.

예를 들면 다음처럼 생각할 수 있다.

- token proposal fact
- claim proposal fact
- source-linked evidence fact
- site alias lookup fact
- infer-trigger fact

중요:
여기서 아직 public row는 없다.
있는 것은
**후보와 근거가 생겼다는 사실**이다.

즉 data는 먼저 judgment state로 올라간다.

---

## 6. candidate와 frontier

이제 후보를 정리해 보자.

가장 쉬운 경우엔 slot마다 후보가 1개뿐일 수 있다.
하지만 worked example에서는 일부러 **경쟁 후보가 생기는 장면**을 하나 넣는다.

예를 들어 `site` slot에 다음 두 후보가 동시에 생긴다고 가정하자.

- candidate A
  - raw text: `"Site Alpha"`
  - normalized site_id: `site_alpha`
  - extraction_mode: `explicit`

- candidate B
  - raw text: `"Alpha"`
  - normalized site_id: `site_alpha_legacy`
  - extraction_mode: `derived`

이제 문제는
“둘 중 값을 하나 고른다”가 아니라,
**어떤 후보가 더 admissible한가**가 된다.

### 6.1 candidate summary

각 후보는 대략 다음 정보를 가진다고 볼 수 있다.

- positive evidence
- negative evidence
- hazard count
- specificity
- provenance depth

예를 들면:

- A는 직접 추출이라 specificity가 높다.
- B는 alias 기반 유도 후보라 specificity가 더 낮다.

### 6.2 dominance와 frontier

frontier 관점에선 전체 후보를 즉시 삭제하지 않는다.
먼저 dominance를 보고 최대 후보 집합을 계산한다.

이 관점에선:

- 하나만 남으면 single winner 가능
- 둘 이상 남으면 review 가능성
- 탈락 후보는 삭제보다 residue/shadow 쪽으로 남음

즉 selection은
“정렬 후 1등 하나 뽑기”보다
**frontier를 계산하고, review 여부를 판정하는 문제**에 가깝다.

### 6.3 이 예제의 selection 결과

이 예제에서는 A가 더 강하다고 가정하자.

그 이유는 예를 들면 다음과 같다.

- 직접 추출 evidence가 더 강함
- specificity가 더 높음
- provenance가 더 짧고 직접적임
- blocking hazard가 없음

그러면 selection 결과는 대략 이렇게 설명할 수 있다.

- winner = `site_alpha`
- frontier size = 1
- requires_review = false

이 순간 active candidate는 정해지지만,
아직 public row가 된 것은 아니다.

---

## 7. draft snapshot과 commit barrier

selection이 끝나도 곧바로 public이 되지 않는다.

이제 중요한 것은 현재 draft가 `committable`한가다.

이 예제에서 barrier는 예를 들면 다음을 본다.

- 필수 bundle이 다 채워졌는가
- blocking hazard가 남아 있는가
- selection이 stale하지 않은가
- provenance가 충분한가

### 7.1 commit 가능 사례

다음 조건을 만족한다고 하자.

- site 있음
- period 있음
- activity_type 있음
- raw_amount 있음
- raw_unit 있음
- blocking error 없음
- provenance 충분
- selection fresh

그러면 이 draft는 `committable = true`다.

### 7.2 hold 사례

worked example에는 반드시 hold 경우도 같이 넣는다.

예를 들어 `raw_unit`이 누락되었거나,
`site` 후보가 둘 다 frontier에 남아 review가 필요한 경우를 생각할 수 있다.

그러면 결과는 대략 이렇게 된다.

- `committable = false`
- public projection은 계산 가능할 수 있음
- 하지만 public ledger append나 merge는 hold

이 장면이 중요하다.
왜냐하면 여기서 처음으로
“보이는 row”와 “정당하게 공개된 row”가 다르다는 점이 드러나기 때문이다.

---

## 8. public projection

이제 commit barrier를 통과한 경우를 보자.

판정 결과를 canonical row 형태로 projection 하면
대략 다음과 같은 결과가 나온다.

```text
site_id = "site_alpha"
entity_id = "entity_alpha"
period = "2025-01"
activity_type = "electricity"
raw_amount = 1000
raw_unit = "kWh"
standardized_amount = 1000
standardized_unit = "kWh"
scope_category = "scope2"
```

중요:
이 row는 source of truth라기보다
**판정 결과를 바깥으로 materialize한 public projection**이다.

즉 이 문서의 핵심은
“row가 만들어졌다”보다
“어떤 판단 상태가 projection 되었다”는 데 있다.

---

## 9. receipt와 explanation

이 예제는 마지막에 반드시 receipt까지 보여 줘야 한다.

### 9.1 selection receipt

selection receipt는 예를 들면 다음을 담는다.

- 어떤 bundle이었는가
- frontier에는 어떤 candidate가 남았는가
- winner는 누구였는가
- 선택 이유로 어떤 reason code가 남았는가

예시:

```text
bundle_id = "frame_1:site"
frontier_ids = ["claim_site_alpha"]
winner_id = "claim_site_alpha"
reason = ["higher_specificity", "direct_evidence"]
```

### 9.2 commit receipt

commit receipt는 예를 들면 다음을 담는다.

- 어떤 draft였는가
- barrier snapshot은 어땠는가
- 어떤 row가 public으로 나갔는가
- 어떤 rule/policy가 merge를 허용했는가

예시:

```text
draft_id = "frame_1"
public_row_id = "row_1"
barrier_snapshot = {
  fresh = true,
  active_hazard_count = 0,
  provenance_edges = 5
}
winner_receipt_ids = ["merge_condition:default"]
```

### 9.3 explanation view

receipt와 fact를 사람이 읽기 좋게 정리하면
예를 들면 이렇게 설명할 수 있다.

- `site_alpha`가 선택된 이유:
  - 직접 추출 evidence가 더 강함
  - legacy alias 후보보다 specificity가 높음

- merge가 허용된 이유:
  - 필수 필드 충족
  - blocking error 없음
  - provenance 충분

중요:
설명 문자열이 본체가 아니라,
설명은 fact/receipt를 다시 읽기 좋게 만든 view다.

---

## 10. hold 버전을 같이 보면

이 문서는 happy path만 보여 주면 안 된다.
같은 예제를 hold 버전으로도 잠깐 봐야 한다.

예를 들어 다음 입력을 생각하자.

```text
Alpha consumed 1000 electricity in 2025-01.
```

여기서는 `raw_unit`이 없고,
`Alpha`가 여러 site 후보에 걸릴 수 있다고 가정할 수 있다.

그러면:

- site 후보 frontier가 2개 남을 수 있음
- `requires_review = true`
- `raw_unit` missing hazard가 열릴 수 있음
- draft는 생성되더라도 `committable = false`
- public projection snapshot은 만들 수 있어도 merge는 hold

즉 이 경우는
“구조화는 일부 되었지만 공개 상태는 아님”을 보여 준다.

이 장면이 있어야 다음 구분이 실제로 보인다.

- draft view
- review view
- public export snapshot
- public ledger append

---

## 11. 이 예제를 현재 코드와 장기 구조에 각각 대응시키기

### 현재 코드 관점

현재 코드 흐름에 대응시키면 다음처럼 읽을 수 있다.

- Lex / Parse / Scope / Infer / Semantic / Repair / Emit / Governance / Calculation
- `CompileArtifacts`가 단계별로 갱신됨
- row는 현재 물리적으로 `artifacts.rows`에 materialize됨
- merge/hold 결정은 governance 쪽에서 남음

### 장기 구조 관점

장기 구조에 대응시키면 다음처럼 읽을 수 있다.

- frontend
- saturation
- arbitration
- commit
- post-commit / views

즉 같은 사례를

- **현재는 staged artifact flow로**
- **장기적으로는 judgment core + shell로**

둘 다 설명할 수 있어야 한다.

이 이중 설명 가능성이 현재 `comp` docs 전체의 핵심 목표다.

---

## 12. 이 예제가 보여 주는 핵심

이 예제에서 가장 중요한 점은 다음이다.

1. `comp`는 raw를 바로 정답 row로 바꾸지 않는다.
2. 먼저 후보/근거/hazard/provenance를 만든다.
3. selection은 frontier 관점으로 설명된다.
4. public row는 commit barrier를 통과한 projection이다.
5. selection과 commit의 이유는 receipt로 남는다.
6. explanation은 본체가 아니라 파생 view다.
7. hold/review 상태도 같은 언어로 설명된다.

즉 `comp`는 단순 ETL보다
**판정 가능한 세계를 만들고 그 세계를 public 상태로 승격시키는 judgment machine**에 가깝다.

---

## 같이 읽을 문서

- 현재 실제 실행 흐름: `current-pipeline.md`
- 공통 판정 어휘: `judgment-language.md`
- 코어 의미론: `core-semantics.md`
- spec 컴파일 경로: `spec-pipeline.md`
- 목표 실행 모델: `execution-model.md`
- authoritative state / view 구분: `views-ledger.md`
