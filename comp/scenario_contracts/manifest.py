from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ScenarioManifestError(ValueError):
    """Raised when a scenario manifest cannot use the public trust bridge."""


@dataclass(frozen=True, slots=True)
class ScenarioManifest:
    scenario_id: str
    input_mode: str
    runtime_case_path: Path
    artifact_envelopes_path: Path
    invariants: tuple[str, ...]
    report_format: str = "json"
    report_path: Path | None = None

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        *,
        base_path: Path,
    ) -> "ScenarioManifest":
        scenario_id = _required_str(payload, "id")
        input_mode = _required_str(payload, "input_mode")
        if input_mode != "canonical_bundle":
            raise ScenarioManifestError(
                "Scenario manifests must use input_mode='canonical_bundle' "
                "before comp can run the trust path."
            )

        runtime_case = _required_mapping(payload, "runtime_case")
        artifact_envelopes = _required_mapping(payload, "artifact_envelopes")
        expected = _required_mapping(payload, "expected")
        invariants = tuple(_required_sequence(expected, "invariants"))
        if not invariants:
            raise ScenarioManifestError("expected.invariants must not be empty.")

        report = payload.get("report", {})
        if report is None:
            report = {}
        if not isinstance(report, Mapping):
            raise ScenarioManifestError("report must be an object when provided.")

        report_format = str(report.get("format", "json"))
        if report_format != "json":
            raise ScenarioManifestError("report.format must be 'json'.")
        report_path = report.get("path")
        return cls(
            scenario_id=scenario_id,
            input_mode=input_mode,
            runtime_case_path=_resolve_path(
                base_path,
                _required_str(runtime_case, "path"),
            ),
            artifact_envelopes_path=_resolve_path(
                base_path,
                _required_str(artifact_envelopes, "path"),
            ),
            invariants=invariants,
            report_format=report_format,
            report_path=(
                None
                if report_path is None
                else _resolve_path(base_path, str(report_path))
            ),
        )


def load_manifest(path: str | Path) -> ScenarioManifest:
    manifest_path = Path(path)
    payload = _load_mapping(manifest_path)
    return ScenarioManifest.from_mapping(payload, base_path=manifest_path.parent)


def _load_mapping(path: Path) -> Mapping[str, Any]:
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError as exc:
            raise ScenarioManifestError(
                "YAML scenario manifests require PyYAML; use JSON or install PyYAML."
            ) from exc
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        raise ScenarioManifestError(
            "Scenario manifest path must end with .json, .yaml, or .yml."
        )
    if not isinstance(payload, Mapping):
        raise ScenarioManifestError("Scenario manifest must be a JSON/YAML object.")
    return payload


def _required_mapping(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, Mapping):
        raise ScenarioManifestError(f"{key} must be an object.")
    return value


def _required_sequence(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ScenarioManifestError(f"{key} must be a list of strings.")
    return tuple(value)


def _required_str(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ScenarioManifestError(f"{key} must be a non-empty string.")
    return value


def _resolve_path(base_path: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return base_path / path


__all__ = ["ScenarioManifest", "ScenarioManifestError", "load_manifest"]
