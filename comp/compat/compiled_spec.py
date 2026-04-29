"""Compatibility wrapper for compiled spec types."""

from comp.dsl.compiled_spec import (
    CompiledBindAction,
    CompiledConstraintSpec,
    CompiledDiagnosticSpec,
    CompiledGovernancePolicy,
    CompiledInheritSpec,
    CompiledInferSpec,
    CompiledParserAction,
    CompiledParserInheritAction,
    CompiledParserSpec,
    CompiledProgramSpec,
    CompiledResolverPolicy,
    CompiledTagAction,
    CompiledTokenSpec,
)

__all__ = [
    "CompiledTokenSpec",
    "CompiledInheritSpec",
    "CompiledConstraintSpec",
    "CompiledDiagnosticSpec",
    "CompiledInferSpec",
    "CompiledBindAction",
    "CompiledParserInheritAction",
    "CompiledTagAction",
    "CompiledParserAction",
    "CompiledParserSpec",
    "CompiledResolverPolicy",
    "CompiledGovernancePolicy",
    "CompiledProgramSpec",
]
