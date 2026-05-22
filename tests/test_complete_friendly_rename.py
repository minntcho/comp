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
