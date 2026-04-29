# ESGDL Reference

이 문서는 `comp`에서 사용하는 ESGDL의 **실용적 참조 문서**다.

중요:
이 문서는 grammar 전체를 그대로 옮긴 백과사전이 아니다.
대신 “무엇을 선언하는 언어인가”를 빠르게 이해할 수 있게 정리한다.

정확한 최종 기준은 언제나 실제 grammar / binder / lowering 코드다.
이 문서는 그 구조를 이해하기 위한 안내 문서다.

---

## ESGDL이 하려는 일

ESGDL은 단순한 입력 포맷이 아니다.

이 DSL은 다음을 함께 다루려 한다.

- 어떤 token을 추출할 것인가
- 어떤 parser가 frame을 만들 것인가
- 어떤 inherit / infer 규칙을 적용할 것인가
- 어떤 resolver가 대표 후보를 정할 것인가
- 어떤 governance가 public row 승격을 허용할 것인가

즉 ESGDL은 raw를 row로 바꾸는 “문법”이라기보다
**증거 기반 정제 파이프라인을 선언하는 언어**에 가깝다.

---

## ESGDL의 큰 블록

ESGDL은 대체로 다음 선언 축을 가진다.

### 1. 기초 도메인 선언
예:
- module
- dimension
- unit
- activity
- scope
- context
- frame

이 블록들은 “무엇이 세계의 기초 객체인가”를 정한다.

---

### 2. 추출 선언
예:
- token
- parser
- build
- bind
- inherit
- tag

이 블록들은 raw/fragment에서
무엇을 어떻게 claim / frame으로 끌어올릴지 정한다.

---

### 3. 의미 규칙 선언
예:
- infer
- require
- forbid
- diagnostic

이 블록들은
어떤 조건이 후보를 강화하거나 약화시키는지,
어떤 진단을 붙여야 하는지,
무엇이 금지되어야 하는지를 정한다.

---

### 4. 후반 정책 선언
예:
- resolver
- governance

이 블록들은
여러 후보 중 무엇을 대표로 볼지,
어떤 경우 public row로 승격할지 정한다.

---

## 핵심 개념

### token
fragment에서 직접 찾을 수 있는 추출 단위다.

예를 들면:
- 숫자
- 기간
- 사이트 별칭
- 활동명
- 단위 기호

token은 보통 parser의 재료가 된다.

---

### parser
token과 source expression을 이용해 frame을 만든다.

parser는 대체로:
- 어떤 frame을 build할지
- 어떤 source를 어떤 role에 bind할지
- 무엇을 inherit/tag할지

를 결정한다.

즉 parser는 “문자열을 읽는 함수”가 아니라
**frame 생성 규칙의 선언**이다.

---

### frame
후보와 슬롯을 담는 중간 구조다.

현재 구조 기준으로는
frame이 row보다 먼저 존재하며,
여러 candidate claim을 품은 상태로 repair/resolution 단계를 거친다.

즉 frame은 아직 public row가 아니고,
**정제 중인 구조화 상태**다.

---

### infer
명시적으로 쓰이지 않은 값을 규칙으로 추가한다.

예:
- 어떤 조건이 만족되면 특정 role 값을 추론
- 다른 slot 값을 근거로 유도된 claim 생성

즉 infer는 “없는 것을 마음대로 채우는 것”이 아니라,
**조건부로 후보를 더 생성하는 선언**이다.

---

### require / forbid / diagnostic
이 블록들은 semantic 층의 핵심이다.

- `require`
  - 꼭 있어야 하는 조건을 선언

- `forbid`
  - 있으면 안 되는 조합이나 상태를 선언

- `diagnostic`
  - warning / error / info 같은 진단을 붙이는 규칙

즉 이 블록들은 값 생성보다
**판정과 제약**에 더 가깝다.

---

### resolver
resolver는 frame 내부 후보들 중
어떤 값을 대표로 볼지 정하는 정책 선언이다.

현재 구조에서는 repair 단계와 깊게 연결되어 있다.

resolver는 보통 다음을 다룬다.

- candidate pool
- score 관련 local
- commit_condition
- review_condition

즉 resolver는 단순 정렬 규칙이 아니라
**slot/frame 수준 selection 정책**이다.

---

### governance
governance는 row를 바로 merge하는 코드라기보다
**public 상태 승격 조건을 선언하는 정책**이다.

보통 여기선:
- emit 가능 여부
- merge 조건
- merge 금지 조건

을 다룬다.

즉 governance는 “row 생성”이 아니라
**생성된 row를 밖으로 인정할 수 있는가**를 판단하는 층이다.

---

## 실행 흐름에서 ESGDL이 작동하는 위치

ESGDL은 전체 pipeline의 여러 지점에 걸쳐 작동한다.

### 초기
- token 선언
- parser 선언

### 중간
- inherit / infer
- require / forbid / diagnostic

### 후반
- resolver
- governance

즉 ESGDL은 특정 한 pass만 위한 언어가 아니라
**전체 staged compiler의 의미를 선언하는 언어**다.

---

## binder / compiled path와의 관계

현재 레포는 ESGDL을 단순 AST로만 쓰지 않는다.

장기적으로 중요한 점은:

- syntax는 그대로 유지하되
- binder가 host-aware하게 이름을 묶고
- compiled spec이 실제 실행용 구조를 별도로 가진다는 점이다

즉 ESGDL의 선언은 그대로 사람이 읽는 문법이지만,
실제 실행은 점점 compiled form으로 이동하고 있다.

이건 중요한 차이다.

---

## 자주 헷갈리는 점

### 1. token = 최종 값이 아니다
token은 추출 재료다.
최종 public row 필드와 1:1로 같다고 보면 안 된다.

### 2. frame = row가 아니다
frame은 중간 상태다.
여기엔 candidate, shadow, frozen, diagnostics가 남아 있을 수 있다.

### 3. resolver = governance가 아니다
resolver는 내부 대표 선택,
governance는 public 승격 판단이다.

### 4. infer = 무조건 자동 보정이 아니다
infer는 조건부 후보 생성이다.
semantic / governance를 건너뛰는 shortcut이 아니다.

---

## 지금 문서의 한계

이 문서는 “ESGDL이 무엇을 선언하는가”를 설명하는 안내 문서다.

다음은 의도적으로 자세히 쓰지 않는다.

- 모든 grammar production 나열
- 각 builtin의 전체 시그니처
- binder의 모든 예외 메시지
- 모든 lowering detail

그건 문서가 아니라 코드와 가까운 영역이기 때문이다.

---

## 나중에 더 붙일 수 있는 것

ESGDL이 더 안정화되면 이 문서에 다음을 추가할 수 있다.

1. 최소 동작 예제 1개
2. token / parser / infer / resolver / governance 예제 1개씩
3. builtin reference
4. common mistakes 섹션
5. syntax → compiled spec 대응표

하지만 첫 버전에서는
문법 전체 나열보다 **개념적 지형도**를 먼저 두는 게 낫다.

---

## 요약

ESGDL은 단순 parser용 미니 언어가 아니다.

이 DSL은 다음을 함께 선언한다.

- 추출
- 조립
- 추론
- 진단
- 대표 선택
- public 승격 조건

즉 ESGDL은 raw를 곧바로 row로 바꾸는 언어라기보다,
**증거 기반 정제 파이프라인 전체를 선언하는 언어**로 보는 게 맞다.
