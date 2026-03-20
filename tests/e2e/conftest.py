"""E2E test configuration — Playwright against OpenWebUI on L2.

Configuration via environment variables:
    RARE_ARCHIVE_OPENWEBUI_URL   default: http://localhost:3100
    RARE_ARCHIVE_OPENWEBUI_USER  required
    RARE_ARCHIVE_OPENWEBUI_PASS  required
    RARE_ARCHIVE_SCREENSHOT_DIR  default: tests/e2e/screenshots
"""

import os
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass
class E2EConfig:
    url: str
    user: str
    password: str
    screenshot_dir: Path


@pytest.fixture(scope="session")
def e2e_config():
    """Build E2E config from environment, skip if credentials are missing."""
    user = os.environ.get("RARE_ARCHIVE_OPENWEBUI_USER", "")
    password = os.environ.get("RARE_ARCHIVE_OPENWEBUI_PASS", "")
    if not user or not password:
        pytest.skip("RARE_ARCHIVE_OPENWEBUI_USER / _PASS not set")

    url = os.environ.get("RARE_ARCHIVE_OPENWEBUI_URL", "http://localhost:3100")
    screenshot_dir = Path(
        os.environ.get("RARE_ARCHIVE_SCREENSHOT_DIR", "tests/e2e/screenshots")
    )
    screenshot_dir.mkdir(parents=True, exist_ok=True)

    return E2EConfig(url=url, user=user, password=password, screenshot_dir=screenshot_dir)


# ---------------------------------------------------------------------------
# Demo scenarios (subset of docs/demo_scenarios.md)
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    id: str
    name: str
    query: str
    expected_keywords: list[str]


SCENARIOS = [
    Scenario(
        id="s01_gaucher",
        name="Gaucher Disease (IEM)",
        query=(
            "A 28-year-old Ashkenazi Jewish male with hepatosplenomegaly, "
            "thrombocytopenia, elevated chitotriosidase, and homozygous GBA1 "
            "N370S variant. What is the diagnosis and management?"
        ),
        expected_keywords=["Gaucher", "GBA1"],
    ),
    Scenario(
        id="s03_duchenne",
        name="Duchenne MD (Neuromuscular)",
        query=(
            "A 4-year-old boy with Gowers sign, CK 15,000, and DMD exon 45-50 "
            "deletion. Assess diagnosis, exon skipping eligibility, and management."
        ),
        expected_keywords=["Duchenne", "DMD"],
    ),
    Scenario(
        id="s05_scid",
        name="SCID (Immunodeficiency)",
        query=(
            "A 3-month-old male with absent T cells, PJP pneumonia, and IL2RG "
            "C229X mutation. What is the diagnosis and how urgent is treatment?"
        ),
        expected_keywords=["SCID", "IL2RG"],
    ),
    Scenario(
        id="s06_melas",
        name="MELAS (Mitochondrial)",
        query=(
            "A 19-year-old woman with stroke-like episodes, lactic acidosis, "
            "hearing loss, and m.3243A>G variant at 65% heteroplasmy. Assess "
            "diagnosis and management."
        ),
        expected_keywords=["MELAS", "mitochondrial"],
    ),
    Scenario(
        id="s10_22q",
        name="22q11.2 Deletion (Complex)",
        query=(
            "A 2-year-old girl with cleft palate, neonatal hypocalcemia, right "
            "aortic arch, and T-cell lymphopenia. Microarray shows 2.5 Mb "
            "deletion at 22q11.21. Assess diagnosis and implications."
        ),
        expected_keywords=["22q11", "DiGeorge"],
    ),
]


@pytest.fixture(params=SCENARIOS, ids=[s.id for s in SCENARIOS])
def scenario(request):
    """Parameterized scenario fixture."""
    return request.param
