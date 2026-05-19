from comp.compiler_tool import CommitPackage, decide_governance


def test_governance_decision_commits_complete_package_without_projection_authority():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        checked_claim_fields=("amount",),
        reference_binding_ids=("bind-amount-factor",),
        derived_claim_ids=("hyp-1:co2e_emission",),
        calculation_trace_ids=("trace:hyp-1:co2e_emission",),
        complete=True,
    )

    decision = decide_governance(package)

    assert decision.decision_id == "governance-decision:commit-package:facility-1"
    assert decision.package_id == "commit-package:facility-1"
    assert decision.subject_id == "facility-1"
    assert decision.status == "commit"
    assert decision.reasons == ("commit_package_complete",)
    assert decision.can_issue_commit_receipt is True
    assert decision.can_authorize_public_projection is False


def test_governance_decision_holds_open_obligations():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="review_required",
        open_obligation_ids=("reference-selection:hyp-1:co2e_emission",),
        complete=False,
    )

    decision = decide_governance(package)

    assert decision.status == "hold"
    assert decision.reasons == (
        "report_status:review_required",
        "open_obligation:reference-selection:hyp-1:co2e_emission",
    )
    assert decision.can_issue_commit_receipt is False


def test_governance_decision_holds_hazards_for_review():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="review_required",
        hazard_ids=("hazard:conflict:scope2_method:review",),
        complete=False,
    )

    decision = decide_governance(package)

    assert decision.status == "hold"
    assert decision.reasons == (
        "report_status:review_required",
        "hazard:conflict:scope2_method:review",
    )


def test_governance_decision_rejects_blocked_terminal_package():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="blocked",
        complete=False,
    )

    decision = decide_governance(package)

    assert decision.status == "reject"
    assert decision.reasons == ("report_status:blocked",)


def test_governance_decision_uses_explicit_decision_id():
    package = CommitPackage(
        package_id="commit-package:facility-1",
        subject_id="facility-1",
        report_status="accepted",
        complete=True,
    )

    decision = decide_governance(package, decision_id="governance-custom")

    assert decision.decision_id == "governance-custom"
