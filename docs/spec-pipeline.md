# Spec Pipeline

이 문서는 ESGDL/spec가 어떻게 **실행 가능한 판단 구조**로 내려오는지를 설명합니다.

중요:
이 문서는 grammar reference가 아닙니다.
문법 자체의 큰 블록은 `esgdl-reference.md`가 설명합니다.

여기서는 다음 질문에 답합니다.

- DSL은 어떤 중간 표현을 거치는가
- binder는 무엇을 고정하는가
- lowering 결과는 어떤 실행용 구조인가
- spec validation은 왜 필요한가
- 현재 레포는 어디까지 왔는가

---

## 왜 data pipeline과 별도로 spec pipeline이 필요한가

현재 `comp`를 보기 쉬운 방식은 “raw가 stages를 지나 row가 된다”입니다.
하지만 장기 구조에서는 그것만으로 설명이 부족합니다.

왜냐하면 `comp`는 data만 처리하는 시스템이 아니라,
**어떤 rule/policy/projection으로 처리할 것인지까지 심사해야 하는 시스템**이기 때문입니다.

즉 data pipeline만 있는 것이 아니라,
그 data를 다루는 틀을 만들어 내는 **spec pipeline**도 따로 있어야 합니다.

---

## 입력과 출력

### 입력

입력은 ESGDL/spec 선언입니다.

대표적으로는 다음 선언이 포함됩니다.

- token
- parser
- build/bind/inherit/tag
- infer
- require/forbid/diagnostic
- resolver
- governance

### 출력

출력은 단순 syntax tree가 아니라,
실행용 의미가 정리된 compiled form 입니다.

장기적으로는 이 출력이
**`CompiledJudgmentProgram`에 가까운 형태**가 되어야 합니다.

즉 결과물은 “문법을 읽은 트리”가 아니라,
다음 정보를 가진 실행 구조여야 합니다.

- 어떤 subject가 judgeable한가
- 어떤 transfer rule이 fact를 생성하는가
- 어떤 selection 정책이 frontier/winner를 판정하는가
- 어떤 commit barrier가 public 승격을 막는가
- 어떤 projection이 public view를 정의하는가

---

## 단계 1: syntax parse

제일 앞단은 syntax를 읽는 단계입니다.

여기서 하는 일은:

- grammar로 source를 파싱
- AST/ProgramSpec 수준 구조를 생성
- 선언 블록의 계층과 기본 형태를 잡기

이 단계의 목적은 “실행”이 아니라,
**무엇이 선언되었는가를 구조적으로 복원하는 것**입니다.

중요:
이 단계만으로는 아직 rule이 합법한지,
어떤 host에서 어떤 이름을 참조하는지가 확정되지 않습니다.

---

## 단계 2: binding

binding은 spec pipeline에서 매우 중요한 단계입니다.

이 단계에서 고정해야 하는 것은 단순 이름 치환이 아닙니다.

### binder가 하는 일

- 이름이 무엇을 가리키는지 확정
- 선언 위치와 사용 위치를 연결
- host별로 허용된 참조만 통과시킴
- lexical/source/rule/governance 계열의 의미 범주를 구분
- 불법 참조나 잘못된 builtin 사용을 조기에 차단

즉 binder는 단순 convenience layer가 아니라,
**spec가 어떤 판단 세계에서 합법한가를 고정하는 관문** 입니다.

현재 레포의 binder는 이 host-aware binding 방향을 이미 강하게 반영합니다.

---

## 단계 3: lowering

binding이 끝난 spec는 실행용 구조로 내려와야 합니다.

장기적으로 lowering이 만들고 싶은 것은,
syntax가 아니라 다음과 같은 judgment-oriented program입니다.

- `TransferRule`
- `BundleSpec`
- `CommitSpec`
- `ProjectionSpec`
- `CompiledJudgmentProgram`

직관적으로는 이렇습니다.

### transfer rule
어떤 fact 변화가 새 fact를 유도하는가.

### bundle / selection spec
어떤 후보들이 같이 비교되는가.
어떤 조건이 frontier/winner/review로 이어지는가.

### commit spec
어떤 hazard/provenance/freshness 조건이 public 승격을 막는가.

### projection spec
판정 결과를 바깥에서 어떤 field/view로 materialize할 것인가.

즉 lowering의 결과는 “예쁜 AST”가 아니라,
**runtime이 직접 사용할 수 있는 판정 프로그램** 입니다.

---

## 단계 4: spec validation

장기적으로 spec도 data와 같은 judgment language로 심사해야 합니다.

즉 validation은 단순 schema check가 아닙니다.

예:

- 이 rule은 `well_formed`한가
- 이 selection policy는 admissible하지 않은 winner를 허용하는가
- 이 commit policy는 unsafe한 상태를 막는가
- 이 projection은 provenance 손실을 과도하게 일으키는가

이 질문은 data validation과 전혀 별개의 세계가 아닙니다.
핵심 predicate vocabulary는 공유되어야 합니다.

즉 spec pipeline의 마지막은 “컴파일 끝”이 아니라,
**컴파일된 틀 자체가 판정 가능한가를 본다** 에 가깝습니다.

---

## 현재 레포의 실제 상태

현재 레포는 이미 compiled path를 가지고 있습니다.

예를 들면:

- syntax spec를 읽는다
- binder가 이름과 builtin 사용을 고정한다
- compiled spec를 만든다
- governance/rule evaluation은 compiled form을 읽는다

다만 아직 이 경로가 전부
`CompiledJudgmentProgram`이라는 이름과 형식으로 정리된 것은 아닙니다.

현재 상태를 더 정확히 말하면:

- compiled path는 이미 존재한다
- binder도 이미 중요한 역할을 한다
- 그러나 spec lowering 결과가 judgment-native vocabulary 하나로 완전히 통합된 상태는 아니다
- 일부는 아직 legacy artifact / compiled spec / pass 구조와 bridge 관계에 있다

즉 지금은 **spec pipeline이 이미 시작되었지만, 아직 judgment-first 용어로 완전히 재서술되지는 않은 상태** 입니다.

---

## `esgdl-reference.md`와의 역할 차이

두 문서는 역할이 다릅니다.

### `esgdl-reference.md`

- ESGDL이 무엇을 선언하는가
- token/parser/infer/resolver/governance가 무슨 뜻인가
- 언어의 개념적 지형도

### `spec-pipeline.md`

- 그 선언이 어떤 단계를 거쳐 실행 구조로 내려오는가
- binder가 무엇을 막고 무엇을 허용하는가
- lowering 결과가 어떤 실행 의미를 갖는가
- spec validation이 왜 필요한가

즉 전자는 **언어 설명**, 후자는 **컴파일 경로 설명** 입니다.

---

## 아직 문서가 잠그지 않는 것

이 문서는 다음까지 고정하지는 않습니다.

- 모든 builtin의 전체 시그니처
- binder error의 전체 목록
- lowering IR의 최종 필드 스키마
- `CompiledJudgmentProgram`의 최종 직렬화 포맷

그건 현재 레포가 아직 bridge 단계이기 때문입니다.

대신 이 문서는 다음을 고정합니다.

- spec에도 독립적인 pipeline이 필요하다는 점
- binder가 핵심 관문이라는 점
- lowering의 목표는 judgment-oriented executable form 이라는 점
- spec validation이 data validation과 다른 우주가 아니라는 점

---

## 요약

`comp`에서 ESGDL/spec는 단순 설정 파일이 아닙니다.

spec pipeline은 다음 흐름을 가집니다.

- syntax parse
- host-aware binding
- judgment-oriented lowering
- spec validation

그리고 장기적으로 그 출력은,
pass chain을 그냥 채우는 설정 값이 아니라
**runtime이 직접 실행할 판정 프로그램**에 가까워져야 합니다.
