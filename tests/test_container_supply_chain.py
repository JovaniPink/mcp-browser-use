"""Static contracts for immutable external container inputs."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCKERFILE = ROOT / "Dockerfile"
RENOVATE_CONFIG = ROOT / "renovate.json"
DIGEST_PATTERN = re.compile(r"@sha256:[0-9a-f]{64}$")


def _external_container_references() -> list[str]:
    references: list[str] = []
    for line in DOCKERFILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("FROM "):
            references.append(stripped.split()[1])
            continue
        if stripped.startswith("COPY --from="):
            reference = stripped.removeprefix("COPY --from=").split()[0]
            if "/" in reference or "." in reference:
                references.append(reference)
    return references


def test_every_external_container_reference_has_a_tag_and_digest() -> None:
    references = _external_container_references()

    assert references
    for reference in references:
        tagged_reference, separator, digest = reference.partition("@")
        assert separator, f"container reference is mutable: {reference}"
        assert ":" in tagged_reference, (
            f"container reference has no reviewable tag: {reference}"
        )
        assert DIGEST_PATTERN.fullmatch(f"@{digest}"), (
            f"container reference has no valid sha256 digest: {reference}"
        )


def test_renovate_is_configured_to_refresh_docker_digests() -> None:
    config = json.loads(RENOVATE_CONFIG.read_text(encoding="utf-8"))
    docker_rules = [
        rule
        for rule in config.get("packageRules", [])
        if "docker" in rule.get("matchDatasources", [])
    ]

    assert any(rule.get("pinDigests") is True for rule in docker_rules)
