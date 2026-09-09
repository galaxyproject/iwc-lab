"""Both the RO-Crate generator and the deployment checker must read a workflow's
primary descriptor in either serialization: native Galaxy ``.ga`` (JSON) or
gxformat2 ``.gxwf.yml`` (YAML). Format-2 workflows are the point of this repo,
so the native-only path is a bug rather than a missing feature.
"""

import importlib.util
import json
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(__file__).resolve().parent / "data"


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_missing_deployments = _load(
    "check_missing_deployments", "scripts/check_missing_deployments.py"
)
gen_crates = _load("gen_crates", "workflows/gen_crates.py")


@pytest.fixture(params=["native-workflow", "format2-workflow"])
def repo_dir(request, tmp_path):
    """A workflow repo in each serialization, copied so crates are written to tmp."""
    dest = tmp_path / "average-bigwig-between-replicates"
    shutil.copytree(DATA_DIR / request.param, dest)
    return dest


def test_expected_release_is_read(repo_dir):
    assert check_missing_deployments.get_expected_release(repo_dir) == "0.2"


def test_crate_carries_descriptor_metadata(repo_dir):
    gen_crates.make_crate(repo_dir, "iwc-lab-workflows", ">=0.75.0")

    metadata = json.loads((repo_dir / "ro-crate-metadata.json").read_text())
    graph = {e["@id"]: e for e in metadata["@graph"]}

    root = graph["./"]
    assert root["license"] == "MIT"
    assert (
        root["isBasedOn"]
        == "https://github.com/iwc-lab-workflows/average-bigwig-between-replicates"
    )

    (workflow,) = [
        e
        for e in metadata["@graph"]
        if "ComputationalWorkflow" in e.get("@type", [])
    ]
    assert workflow["version"] == "0.2"
    assert workflow["creator"] == [{"@id": "https://orcid.org/0000-0002-1964-4960"}]
    assert graph["https://orcid.org/0000-0002-1964-4960"]["name"] == "Lucille Delisle"
