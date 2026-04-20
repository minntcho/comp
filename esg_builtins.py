# esg_builtins.py
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Optional

from runtime_env import LexCandidate

if TYPE_CHECKING:
    from runtime_env import RuntimeEnv


# ---------------------------------
# Regexes
# ---------------------------------

YEAR_MONTH_1 = re.compile(r"(?P<year>20\d{2})[-/](?P<month>0?[1-9]|1[0-2])")
YEAR_MONTH_2 = re.compile(r"(?P<year>20\d{2})\s*년\s*(?P<month>0?[1-9]|1[0-2])\s*월")
YEAR_ONLY = re.compile(r"(?P<year>20\d{2})")
NUMBER_RE = re.compile(r"-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?")


# ---------------------------------
# Lexical builtins
# ---------------------------------

def site_alias(text: str, env: RuntimeEnv) -> list[LexCandidate]:
    hits: list[LexCandidate] = []
    for alias, site_id in sorted(env.site_alias_index.items(), key=lambda x: len(x[0]), reverse=True):
        for m in re.finditer(re.escape(alias), text.lower()):
            hits.append(
                LexCandidate(
                    value=site_id,
                    start=m.start(),
                    end=m.end(),
                    confidence=0.92,
                    metadata={"surface": text[m.start():m.end()], "site_id": site_id},
                )
            )
    return _dedupe_hits(hits)


def activity_alias(text: str, env: RuntimeEnv) -> list[LexCandidate]:
    hits: list[LexCandidate] = []
    for alias, canonical in sorted(env.activity_alias_index.items(), key=lambda x: len(x[0]), reverse=True):
        for m in re.finditer(re.escape(alias), text.lower()):
            hits.append(
                LexCandidate(
                    value=canonical,
                    start=m.start(),
                    end=m.end(),
                    confidence=0.92,
                    metadata={"surface": text[m.start():m.end()], "activity_type": canonical},
                )
            )
    return _dedupe_hits(hits)


def unit_symbol(text: str, env: RuntimeEnv) -> list[LexCandidate]:
    hits: list[LexCandidate] = []
    for alias, canonical in sorted(env.unit_alias_index.items(), key=lambda x: len(x[0]), reverse=True):
        for m in re.finditer(re.escape(alias), text.lower()):
            hits.append(
                LexCandidate(
                    value=canonical,
                    start=m.start(),
                    end=m.end(),
                    confidence=0.95,
                    metadata={"surface": text[m.start():m.end()], "raw_unit": canonical},
                )
            )
    return _dedupe_hits(hits)


def period_expr(text: str, env: RuntimeEnv | None = None) -> list[LexCandidate]:
    hits: list[LexCandidate] = []

    for pat in (YEAR_MONTH_1, YEAR_MONTH_2):
        for m in pat.finditer(text):
            year = int(m.group("year"))
            month = int(m.group("month"))
            hits.append(
                LexCandidate(
                    value=f"{year:04d}-{month:02d}",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.97,
                    metadata={"kind": "year_month"},
                )
            )

    # 연-월을 못 찾은 경우에만 연도 토큰을 쓰는 편이 안전하다
    if not hits:
        for m in YEAR_ONLY.finditer(text):
            hits.append(
                LexCandidate(
                    value=f"{int(m.group('year')):04d}",
                    start=m.start(),
                    end=m.end(),
                    confidence=0.75,
                    metadata={"kind": "year"},
                )
            )

    return _dedupe_hits(hits)


def number(text: str, env: RuntimeEnv | None = None) -> list[LexCandidate]:
    hits: list[LexCandidate] = []
    for m in NUMBER_RE.finditer(text):
        raw = m.group(0).replace(",", "")
        value = float(raw) if "." in raw else int(raw)
        hits.append(
            LexCandidate(
                value=value,
                start=m.start(),
                end=m.end(),
                confidence=0.96,
                metadata={"surface": m.group(0)},
            )
        )
    return hits


def one_of(text: str, *choices: str, env: RuntimeEnv | None = None) -> list[LexCandidate]:
    hits: list[LexCandidate] = []
    lower_text = text.lower()

    for choice in choices:
        lower_choice = choice.lower()
        for m in re.finditer(re.escape(lower_choice), lower_text):
            hits.append(
                LexCandidate(
                    value=choice,
                    start=m.start(),
                    end=m.end(),
                    confidence=0.90,
                    metadata={"surface": text[m.start():m.end()]},
                )
            )
    return _dedupe_hits(hits)


def fuzzy_lex(role_name: str, text: str, env: RuntimeEnv) -> list[LexCandidate]:
    if not env.can_call_llm():
        return []

    if not env.consume_llm_budget(1):
        return []

    out = env.llm_fallback(role_name, text)
    return out or []


# ---------------------------------
# Semantic / evaluation builtins
# ---------------------------------

def dimension(raw_unit: str, env: RuntimeEnv) -> Optional[str]:
    spec = env.unit_index.get(raw_unit)
    return None if spec is None else spec.dimension


def compatible(activity_type: str, raw_unit: str, env: RuntimeEnv) -> bool:
    act = env.activity_index.get(activity_type)
    unit = env.unit_index.get(raw_unit)

    if act is None or unit is None:
        return False

    return act.dimension == unit.dimension


def valid(value: Any, env: RuntimeEnv | None = None) -> bool:
    """
    MVP용 generic valid.
    period에 주로 쓰일 걸 가정하고, 숫자/단위/문자열도 느슨하게 허용.
    """
    if value is None:
        return False

    if isinstance(value, (int, float)):
        return True

    if isinstance(value, str):
        if YEAR_MONTH_1.fullmatch(value) or YEAR_ONLY.fullmatch(value):
            return True
        if env is not None and value in env.unit_index:
            return True
        if value.strip():
            return True

    return False


def valid_period(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(YEAR_MONTH_1.fullmatch(value) or YEAR_ONLY.fullmatch(value))


def missing(role_name: str, frame: Any) -> bool:
    """
    frame.bindings 또는 frame.slots 를 느슨하게 지원한다.
    """
    # typed frame 스타일
    bindings = getattr(frame, "bindings", None)
    if isinstance(bindings, dict):
        return role_name not in bindings or bindings[role_name] is None

    # frame.slots 스타일
    slot = _lookup_slot(frame, role_name)
    if slot is None:
        return True

    active_claim_id = getattr(slot, "active_claim_id", None)
    resolved_value = getattr(slot, "resolved_value", None)
    missing_tag = getattr(slot, "missing_tag", None)

    if active_claim_id is None and resolved_value in (None, ""):
        return True

    if missing_tag is not None and resolved_value in (None, ""):
        return True

    return False


def origin(role_name: str, frame: Any, claims_by_id: dict[str, Any] | None = None) -> Optional[str]:
    """
    active claim의 extraction_mode를 리턴한다.
    """
    if claims_by_id is None:
        return None

    slot = _lookup_slot(frame, role_name)
    if slot is None:
        return None

    claim_id = getattr(slot, "active_claim_id", None)
    if claim_id is None:
        return None

    claim = claims_by_id.get(claim_id)
    if claim is None:
        return None

    return getattr(claim, "extraction_mode", None)


def evidence(kind: str, frame: Any, claims_by_id: dict[str, Any] | None = None) -> int:
    """
    MVP: active claim들에 달린 evidence_ids 중 kind prefix가 맞는 것 카운트.
    """
    if claims_by_id is None:
        return 0

    total = 0
    slots = getattr(frame, "slots", None)
    if not isinstance(slots, dict):
        return total

    for slot in slots.values():
        claim_id = getattr(slot, "active_claim_id", None)
        if claim_id is None:
            continue

        claim = claims_by_id.get(claim_id)
        if claim is None:
            continue

        for ev_id in getattr(claim, "evidence_ids", []):
            if str(ev_id).startswith(f"{kind}:"):
                total += 1

    return total


def register_default_builtins(env: RuntimeEnv) -> None:
    env.builtin_registry.update(
        {
            # lexical
            "site_alias": site_alias,
            "activity_alias": activity_alias,
            "unit_symbol": unit_symbol,
            "period_expr": period_expr,
            "number": number,
            "one_of": one_of,
            "llm.fuzzy_lex": fuzzy_lex,

            # semantic
            "dimension": dimension,
            "compatible": compatible,
            "valid": valid,
            "valid_period": valid_period,
            "missing": missing,
            "origin": origin,
            "evidence": evidence,
        }
    )


# ---------------------------------
# Internal helpers
# ---------------------------------

def _dedupe_hits(hits: list[LexCandidate]) -> list[LexCandidate]:
    seen: set[tuple[Any, int | None, int | None]] = set()
    out: list[LexCandidate] = []

    for h in hits:
        key = (h.value, h.start, h.end)
        if key in seen:
            continue
        seen.add(key)
        out.append(h)

    out.sort(key=lambda x: (x.start if x.start is not None else 10**9, -(x.end or 0)))
    return out


def _lookup_slot(frame: Any, role_name: str) -> Any | None:
    slots = getattr(frame, "slots", None)
    if not isinstance(slots, dict):
        return None

    if role_name in slots:
        return slots[role_name]

    for k, v in slots.items():
        key_str = getattr(k, "value", k)
        if key_str == role_name:
            return v

    return None