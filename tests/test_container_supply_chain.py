"""Dependency-free contracts for immutable external build inputs."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCKERFILE = ROOT / "Dockerfile"
RENOVATE_CONFIG = ROOT / "renovate.json"
WORKFLOWS = ROOT / ".github" / "workflows"
DIGEST_PATTERN = re.compile(r"^@sha256:[0-9a-f]{64}$")
ACTION_PATTERN = re.compile(r"^\s*-\s+uses:\s*(?P<reference>[^\s#]+)")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")


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


def _external_action_references() -> list[str]:
    references: list[str] = []
    for workflow in sorted(WORKFLOWS.glob("*.y*ml")):
        for line in workflow.read_text(encoding="utf-8").splitlines():
            match = ACTION_PATTERN.match(line)
            if match is None:
                continue
            reference = match.group("reference")
            if not reference.startswith("./"):
                references.append(reference)
    return references


class ContainerSupplyChainContractTests(unittest.TestCase):
    def test_every_external_container_reference_has_a_tag_and_digest(self) -> None:
        references = _external_container_references()

        self.assertTrue(references, "no external container references found")
        for reference in references:
            tagged_reference, separator, digest = reference.partition("@")
            self.assertTrue(separator, f"container reference is mutable: {reference}")
            self.assertIn(
                ":",
                tagged_reference,
                f"container reference has no reviewable tag: {reference}",
            )
            self.assertRegex(
                f"@{digest}",
                DIGEST_PATTERN,
                f"container reference has no valid sha256 digest: {reference}",
            )

    def test_every_external_action_uses_a_full_commit_sha(self) -> None:
        references = _external_action_references()

        self.assertTrue(references, "no external GitHub Actions found")
        for reference in references:
            action, separator, revision = reference.partition("@")
            self.assertTrue(
                separator, f"GitHub Action reference is mutable: {reference}"
            )
            self.assertIn("/", action, f"GitHub Action is not external: {reference}")
            self.assertRegex(
                revision,
                COMMIT_PATTERN,
                f"GitHub Action is not pinned to a full commit SHA: {reference}",
            )

    def test_renovate_refreshes_container_and_action_digests(self) -> None:
        config = json.loads(RENOVATE_CONFIG.read_text(encoding="utf-8"))
        docker_rules = [
            rule
            for rule in config.get("packageRules", [])
            if "docker" in rule.get("matchDatasources", [])
        ]

        self.assertTrue(
            any(rule.get("pinDigests") is True for rule in docker_rules),
            "Renovate does not refresh Docker digests",
        )
        self.assertIn(
            "helpers:pinGitHubActionDigests",
            config.get("extends", []),
            "Renovate does not keep GitHub Action commit pins current",
        )


if __name__ == "__main__":
    unittest.main()
