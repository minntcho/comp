from types import SimpleNamespace

from artifacts import ClaimArtifact, CompileArtifacts, PartialFrameArtifact, RoleSlotArtifact
from emit_pass import EmitPass
from comp.views import DEFAULT_PUBLIC_PROJECTION, materialize_public_rows, project_canonical_row


def _env():
    return SimpleNamespace(
        site_records={"SITE-1": SimpleNamespace(entity_id="ENT-1")},
        site_alias_index={"hq": "SITE-1"},
        activity_index={"electricity": SimpleNamespace(scope_category="Scope2")},
        unit_index={
            "kwh": SimpleNamespace(
                normalize_to="kwh",
                normalize_op="*",
                normalize_factor=1.0,
            )
        },
    )


def _claims():
    return {
        "c-site": ClaimArtifact(
            claim_id="c-site",
            frame_id="FRM-1",
            fragment_id="frag-1",
            parser_name="parser-a",
            role_name="site",
            value="hq",
            confidence=0.9,
            extraction_mode="explicit",
            candidate_state="active",
        ),
        "c-activity": ClaimArtifact(
            claim_id="c-activity",
            frame_id="FRM-1",
            fragment_id="frag-1",
            parser_name="parser-a",
            role_name="activity_type",
            value="electricity",
            confidence=0.8,
            extraction_mode="explicit",
            candidate_state="active",
        ),
        "c-amount": ClaimArtifact(
            claim_id="c-amount",
            frame_id="FRM-1",
            fragment_id="frag-1",
            parser_name="parser-a",
            role_name="raw_amount",
            value=100.0,
            confidence=0.7,
            extraction_mode="explicit",
            candidate_state="active",
        ),
        "c-unit": ClaimArtifact(
            claim_id="c-unit",
            frame_id="FRM-1",
            fragment_id="frag-1",
            parser_name="parser-a",
            role_name="raw_unit",
            value="kwh",
            confidence=0.7,
            extraction_mode="explicit",
            candidate_state="active",
        ),
    }


def _frame(status="committed"):
    frame = PartialFrameArtifact(
        frame_id="FRM-1",
        parser_name="parser-a",
        frame_type="ActivityFrame",
        fragment_ids=["frag-1"],
        status=status,
        slots={
            "site": RoleSlotArtifact(role_name="site", active_claim_id="c-site"),
            "activity_type": RoleSlotArtifact(role_name="activity_type", active_claim_id="c-activity"),
            "raw_amount": RoleSlotArtifact(role_name="raw_amount", active_claim_id="c-amount"),
            "raw_unit": RoleSlotArtifact(role_name="raw_unit", active_claim_id="c-unit"),
        },
    )
    frame.runtime.iteration_count = 3
    frame.runtime.stable_count = 2
    frame.runtime.termination_reason = "commit_condition_satisfied"
    frame.metadata["selection_receipts"] = [{"bundle_id": "FRM-1:raw_amount", "winner_id": "c-amount"}]
    return frame


def test_project_canonical_row_keeps_projection_metadata():
    row = project_canonical_row(
        frame=_frame(),
        claims_by_id=_claims(),
        env=_env(),
        projection=DEFAULT_PUBLIC_PROJECTION,
    )

    assert row is not None
    assert row.row_id == "ROW-1"
    assert row.site_id == "SITE-1"
    assert row.entity_id == "ENT-1"
    assert row.scope_category == "Scope2"
    assert row.metadata["projection_id"] == "canonical_row"
    assert row.metadata["selection_receipts"][0]["winner_id"] == "c-amount"


def test_emit_pass_delegates_to_public_view_materializer():
    committed = _frame(status="committed")
    resolving = _frame(status="resolving")
    resolving.frame_id = "FRM-2"

    artifacts = CompileArtifacts(
        claims=list(_claims().values()),
        frames=[committed, resolving],
    )

    EmitPass().run(spec=None, artifacts=artifacts, env=_env())

    assert len(artifacts.rows) == 1
    assert artifacts.rows[0].frame_id == "FRM-1"

    rows = materialize_public_rows(
        [committed, resolving],
        _claims(),
        _env(),
        emit_only_committed=True,
    )
    assert len(rows) == 1
    assert rows[0].frame_id == "FRM-1"
