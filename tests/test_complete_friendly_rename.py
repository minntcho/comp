from pathlib import Path
import subprocess


def test_legacy_authority_names_are_not_active_repo_surface():
    legacy_names = tuple(
        "".join(parts)
        for parts in (
            ("Claim", "Hypothesis"),
            ("Evidence", "Witness"),
            ("Reference", "Candidate"),
            ("Reference", "Binding"),
            ("Derived", "Claim"),
            ("Compile", "Report"),
            ("Proof", "Obligation"),
            ("Commit", "Package"),
            ("Governance", "Decision"),
            ("Commit", "Receipt"),
            ("Commit", "Receipt", "Citations"),
            ("Projection", "Spec"),
            ("Public", "Projection"),
            ("Projection", "Blocked"),
            ("Projection", "Value", "Commitment"),
            ("evidence", "_witness", "_fingerprint"),
            ("build", "_commit", "_receipt"),
            ("project", "_public", "_row"),
            ("can", "_project", "_public", "_row"),
        )
    )
    scanned_roots = ("README.md", "comp/", "minchoagnt/", "tests/", "docs/")
    ignored = (
        "docs/archive/",
        "tests/test_complete_friendly_rename.py",
    )

    paths = subprocess.check_output(
        ["git", "ls-files"],
        text=True,
    ).splitlines()
    offenders = []
    for path_text in paths:
        if path_text.startswith(ignored):
            continue
        if not (path_text == "README.md" or path_text.startswith(scanned_roots)):
            continue
        path = Path(path_text)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for legacy_name in legacy_names:
            if legacy_name in text:
                offenders.append(f"{path_text}: {legacy_name}")

    assert offenders == []


def test_legacy_validation_report_field_names_are_not_active_python_surface():
    legacy_field_patterns = tuple(
        "".join(parts)
        for parts in (
            ("evidence", "_witnesses"),
            ("reference", "_candidates"),
            ("reference", "_bindings"),
            ("derived", "_claims"),
            ("resolved", "_obligations"),
            (".", "obligations"),
            ("obligations", "="),
        )
    )
    scanned_roots = ("comp/", "minchoagnt/", "tests/")
    ignored = (
        "tests/test_complete_friendly_rename.py",
        "tests/test_package_smoke.py",
    )

    paths = subprocess.check_output(
        ["git", "ls-files"],
        text=True,
    ).splitlines()
    offenders = []
    for path_text in paths:
        if path_text.startswith(ignored):
            continue
        if not path_text.startswith(scanned_roots):
            continue
        path = Path(path_text)
        if not path.is_file() or path.suffix != ".py":
            continue
        text = path.read_text(encoding="utf-8")
        for legacy_field in legacy_field_patterns:
            if legacy_field in text:
                offenders.append(f"{path_text}: {legacy_field}")

    assert offenders == []
