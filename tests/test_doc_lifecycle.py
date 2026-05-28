from pathlib import Path


ANCHOR_PREFIXES = ("code:", "test:", "doc:")
HISTORICAL_NON_CURRENT_GUIDANCE = (
    "Historical note. This document cannot block PRs and must not be cited as "
    "current guidance."
)
STALE_PHRASES = (
    "first PR",
    "first slice",
    "upcoming",
    "should eventually",
    "can be migrated",
    "future implementation",
)
STRICT_CURRENT_HEADINGS = {
    "Current Architecture",
    "Current Position",
    "Current Implementation Status",
    "Core Rule",
    "Authority Boundary",
    "State Transition Requirements",
}
REFRESHED_CURRENT_GUIDANCE_DOCS = {
    Path("docs/architecture/contracts/policy-boundary.md"),
    Path("docs/architecture/maps/domain-scenario-pack-generation.md"),
    Path("docs/architecture/maps/obligation-kernel-working-theory.md"),
    Path("docs/architecture/maps/product-facade-conformance-runner.md"),
    Path("docs/architecture/north-stars/scenario-trust-runtime-bridge.md"),
}
DOC_REFRESH_QUEUE = Path("docs/archive/plans/2026-05-28-doc-refresh-queue.md")


def _governed_architecture_docs():
    governed_dirs = (
        Path("docs/architecture"),
        Path("docs/architecture/contracts"),
        Path("docs/architecture/maps"),
        Path("docs/architecture/north-stars"),
        Path("docs/archive/architecture"),
    )
    return sorted(path for directory in governed_dirs for path in directory.glob("*.md"))


def _doc_header(path):
    header = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:8]:
        if ": " in line:
            key, value = line.split(": ", 1)
            header[key] = value
    return header


def _list_block(text, title):
    lines = text.splitlines()
    start = f"{title}:"
    for index, line in enumerate(lines):
        if line.strip() != start:
            continue
        items = []
        for item in lines[index + 1 :]:
            stripped = item.strip()
            if not stripped:
                break
            if not stripped.startswith("- "):
                break
            items.append(stripped[2:].strip())
        return tuple(items)
    return ()


def _local_anchor_path(target):
    path = target.strip().strip("`")
    return path.split("::", 1)[0]


def _sections(text):
    current_heading = None
    body = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_heading is not None:
                yield current_heading, "\n".join(body)
            current_heading = line.removeprefix("## ").strip()
            body = []
            continue
        body.append(line)
    if current_heading is not None:
        yield current_heading, "\n".join(body)


def test_checked_anchors_point_to_existing_paths_when_declared():
    docs_with_anchors = []

    for path in _governed_architecture_docs():
        text = path.read_text(encoding="utf-8")
        anchors = _list_block(text, "Checked anchors")
        if not anchors:
            continue
        docs_with_anchors.append(path)

        for anchor in anchors:
            matching_prefixes = [
                prefix for prefix in ANCHOR_PREFIXES if anchor.startswith(prefix)
            ]
            assert len(matching_prefixes) == 1, f"{path}: invalid anchor {anchor!r}"
            target = anchor.split(":", 1)[1].strip()
            anchor_path = _local_anchor_path(target)
            assert Path(anchor_path).exists(), f"{path}: missing anchor {target!r}"

    assert Path("docs/architecture/document-governance.md") in docs_with_anchors


def test_refreshed_current_guidance_docs_declare_lifecycle_metadata():
    for path in REFRESHED_CURRENT_GUIDANCE_DOCS:
        text = path.read_text(encoding="utf-8")
        header = _doc_header(path)

        assert header["Last checked against code"] == "2026-05-28", path
        assert _list_block(text, "Checked anchors"), path
        assert _list_block(text, "Freshness triggers"), path
        assert "Stale-language policy:" in text, path


def test_strict_current_sections_do_not_use_known_stale_phrases_when_policy_declared():
    docs_with_policy = []

    for path in _governed_architecture_docs():
        text = path.read_text(encoding="utf-8")
        if "Stale-language policy:" not in text:
            continue
        docs_with_policy.append(path)

        for heading, body in _sections(text):
            if heading not in STRICT_CURRENT_HEADINGS:
                continue
            lowered_body = body.lower()
            for phrase in STALE_PHRASES:
                assert phrase.lower() not in lowered_body, (
                    f"{path}:{heading} uses stale phrase {phrase!r}"
                )

    assert Path("docs/architecture/document-governance.md") in docs_with_policy


def test_historical_notes_declare_they_are_not_current_guidance():
    for path in _governed_architecture_docs():
        header = _doc_header(path)
        if header.get("Status") != "historical-note":
            continue

        text = path.read_text(encoding="utf-8")
        assert HISTORICAL_NON_CURRENT_GUIDANCE in text, path


def test_document_governance_defines_refresh_queue_boundary():
    governance = Path("docs/architecture/document-governance.md").read_text(
        encoding="utf-8"
    )

    assert "## Refresh Queue" in governance
    assert "`docs/archive/plans/`" in governance
    assert "Refresh queue entries cannot block PRs." in governance
    assert "refresh, confirm no drift, or demote" in governance


def test_doc_refresh_queue_is_non_authoritative():
    text = DOC_REFRESH_QUEUE.read_text(encoding="utf-8")

    assert "Authority: none" in text
    assert "This queue cannot block PRs." in text
    assert "This queue must not be cited as current guidance." in text
    assert "Status: active-contract" not in text
    assert "Can block PRs: yes" not in text
    assert "| doc | issue | required anchor check | target action |" in text
    assert "refresh" in text
    assert "confirm no drift" in text
    assert "demote/archive" in text
