"""Checks for public-facing repository consistency."""

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAINTAINED_TEXT = [
    ROOT / "README.md",
    ROOT / "CONTRIBUTING.md",
    ROOT / "docs" / "USAGE.md",
    ROOT / "docs" / "FAQ.md",
    ROOT / "app" / "README.md",
    ROOT / "app" / "README_HUGGINGFACE.md",
]

MARKDOWN_FILES = MAINTAINED_TEXT + [
    ROOT / "CHANGELOG.md",
    ROOT / "CODE_OF_CONDUCT.md",
    ROOT / "SECURITY.md",
    ROOT / "docs" / "README.md",
    ROOT / "legacy" / "README.md",
]


def test_maintained_docs_exclude_superseded_claims():
    forbidden = (
        "yourusername",
        "original/purpleair",
        "Temporal-TempStrat",
        "0.38-0.53",
        "DOI will be available",
    )
    for path in MAINTAINED_TEXT:
        text = path.read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{phrase!r} remains in {path.relative_to(ROOT)}"


def test_public_links_and_version_are_consistent():
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    app = (ROOT / "app" / "app.py").read_text(encoding="utf-8")
    repository_url = "https://github.com/yunqianz728/purpleair-calibration"
    space_url = "https://huggingface.co/spaces/yunqianz/purpleair-calibration"
    assert "version: 2.0.0" in citation
    assert repository_url in citation and repository_url in readme and repository_url in app
    assert space_url in readme


def test_deployment_dependencies_are_reproducible():
    requirements = (ROOT / "app" / "requirements.txt").read_text(encoding="utf-8")
    assert "xgboost==2.1.4" in requirements
    assert "scikit-learn==1.5.2" in requirements


def test_relative_markdown_links_resolve():
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in MARKDOWN_FILES:
        for target in link_pattern.findall(path.read_text(encoding="utf-8")):
            target = target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            assert resolved.exists(), f"Broken link {target!r} in {path.relative_to(ROOT)}"
