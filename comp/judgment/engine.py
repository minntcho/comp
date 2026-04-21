from __future__ import annotations

from comp.judgment.core import Fact, JudgmentState
from comp.judgment.program import CompiledJudgmentProgram, TransferRule


class FixpointEngine:
    def __init__(self, program: CompiledJudgmentProgram) -> None:
        self.program = program

    def run(self, seed_facts: set[Fact] | list[Fact] | tuple[Fact, ...]) -> JudgmentState:
        state = JudgmentState()
        delta = state.add_facts(seed_facts)

        while delta:
            new_facts: set[Fact] = set()
            for rule in self.program.transfers:
                triggered = self._triggered(rule, delta)
                if not triggered:
                    continue
                emitted = set(rule.emit(state, triggered))
                new_facts |= emitted
            delta = state.add_facts(new_facts)

        return state

    def _triggered(self, rule: TransferRule, delta: set[Fact]) -> frozenset[Fact]:
        return frozenset(
            fact
            for fact in delta
            if fact.tag in rule.subscribe_tags
            and (rule.match_kind is None or fact.subject.kind == rule.match_kind)
        )


__all__ = ["FixpointEngine"]
