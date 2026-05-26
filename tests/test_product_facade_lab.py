from __future__ import annotations

import tomllib
from pathlib import Path

from examples.product_facade_lab import (
    ProductFacadeRuntime,
    ProductInput,
    ProductWitness,
)


def test_canonical_fast_path_submit_publish_audit_records_touch_log():
    runtime = ProductFacadeRuntime()

    run = runtime.submit(
        ProductInput(
            run_id="run-1",
            subject_id="facility-1",
            public_row_id="public-row-1",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            values={"amount": 1200, "unit": "kWh"},
            witnesses=(
                ProductWitness(
                    field="amount",
                    source="invoice.pdf",
                    span="p1: electricity amount",
                    text="1200",
                ),
                ProductWitness(
                    field="unit",
                    source="invoice.pdf",
                    span="p1: electricity unit",
                    text="kWh",
                ),
            ),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )

    assert run.status == "publishable"
    assert run.required_actions == ()
    assert run.touch_log.flow == "canonical_fast_path"
    assert run.touch_log.operation == "submit"
    assert run.touch_log.sync_required == (
        "InterpretationHypothesis",
        "ValidationReport",
    )
    assert run.touch_log.sync_required_if_publishing == ("PublicOutputReceipt",)
    assert "ArtifactEnvelope" in run.touch_log.deferred
    assert "ProjectionReplayReport" in run.touch_log.deferred
    assert run.touch_log.not_used == (
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
    )

    public = runtime.publish(run.run_id)

    assert public.public_row == {"amount": 1200, "unit": "kWh"}
    assert public.touch_log.operation == "publish"
    assert "PublicOutputReceipt" in public.touch_log.sync_required
    assert "ArtifactEnvelope" in public.touch_log.deferred
    assert "DecisionLedger" in public.touch_log.not_used

    audit = runtime.audit(public.public_row_id)

    assert audit.replay_report.public_row == public.public_row
    assert audit.touch_log.operation == "audit"
    assert audit.touch_log.sync_required == (
        "ArtifactEnvelope",
        "ProjectionReplayReport",
    )
    assert audit.touch_log.not_used == ("ProofGraph",)
    assert audit.artifact_count == len(audit.replay_report.artifact_refs)


def test_product_facade_lab_stays_outside_packaged_comp_surface():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    packages = set(pyproject["tool"]["setuptools"]["packages"])
    source = Path("examples/product_facade_lab/runtime.py").read_text(
        encoding="utf-8"
    )

    assert "examples" not in packages
    assert "examples.product_facade_lab" not in packages
    assert "from comp.policy" not in source
    assert "import comp.policy" not in source
    assert "from comp.runtime import ValidationHandoff" not in source
    assert "SelectedValidationContract(" not in source
    assert "DecisionLedger(" not in source


def test_observation_map_points_to_canonical_lab_without_promoting_runtime():
    product_map = Path(
        "docs/architecture/maps/product-facade-observation.md"
    ).read_text(encoding="utf-8")
    lab_readme = Path("examples/product_facade_lab/README.md").read_text(
        encoding="utf-8"
    )

    assert "examples/product_facade_lab" in product_map
    assert "comp-backed observation lab" in lab_readme
    assert "not a production runtime" in lab_readme
    assert "native production authority engine" in lab_readme
