import json
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = sorted(
    path for path in (ROOT / "examples").iterdir() if path.is_dir() and not path.name.startswith("_")
)


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_example_has_required_files(example: Path):
    assert (example / "README.md").is_file()
    assert (example / "docker-compose.yml").is_file()
    assert (example / "app-meta.json").is_file()
    assert (example / "images.txt").is_file()


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_metadata_is_open_source_and_non_overlapping(example: Path):
    metadata = json.loads((example / "app-meta.json").read_text())
    assert metadata["name"] == example.name
    assert metadata["nexigonOverlap"] is False
    assert metadata["industrialUseCase"]
    assert metadata["components"]
    for component in metadata["components"]:
        assert component["name"]
        assert component["role"]
        assert component["license"]


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_compose_has_health_checks(example: Path):
    content = (example / "docker-compose.yml").read_text()
    assert "healthcheck:" in content


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_compose_is_deployment_only(example: Path):
    content = (example / "docker-compose.yml").read_text()
    assert not re.search(r"^\s+build\s*:", content, re.MULTILINE)


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda path: path.name)
def test_image_manifest_matches_compose_images(example: Path):
    compose = (example / "docker-compose.yml").read_text()
    compose_images = set(re.findall(r"^\s+image:\s+([^\s]+)\s*$", compose, re.MULTILINE))

    manifest_images = set()
    for line in (example / "images.txt").read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        assert parts[0] in {"pull", "build"}
        assert len(parts) >= 2
        manifest_images.add(parts[1])
        if parts[0] == "build":
            assert len(parts) == 3
            assert (example / parts[2] / "Dockerfile").is_file()

    assert compose_images == manifest_images
