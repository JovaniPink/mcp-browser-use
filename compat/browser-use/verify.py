"""Verify the owned wheel and its recorded upstream source identity offline."""

from __future__ import annotations

import email
import hashlib
import json
import zipfile
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(directory: Path) -> dict:
    provenance = json.loads((directory / "provenance.json").read_text())
    artifact = provenance["artifact"]
    wheel = directory / artifact["filename"]
    require(digest(wheel.read_bytes()) == artifact["sha256"], "wheel hash mismatch")
    require(
        digest((directory / "source.patch").read_bytes())
        == provenance["patch"]["sha256"],
        "source patch hash mismatch",
    )
    require(
        digest((directory / "LICENSE").read_bytes())
        == provenance["upstream"]["license_sha256"],
        "upstream license hash mismatch",
    )
    with zipfile.ZipFile(wheel) as archive:
        prefix = "browser_use-0.13.14.dist-info/"
        metadata = email.message_from_bytes(archive.read(prefix + "METADATA"))
        tags = email.message_from_bytes(archive.read(prefix + "WHEEL"))
        require(metadata["Name"] == "browser-use", "unexpected package name")
        require(metadata["Version"] == "0.13.14", "unexpected source version")
        require(tags["Build"] == "1mcbu1", "owned build tag is missing")
        require(
            metadata["Summary"] == artifact["summary"],
            "owned build identification is missing",
        )
        require(
            metadata.get_all("Requires-Dist") == artifact["requires_dist"],
            "declared dependency metadata differs from the reviewed build",
        )
        payload = {
            name: digest(archive.read(name))
            for name in archive.namelist()
            if name.startswith("browser_use/") and not name.endswith("/")
        }
        require(
            payload == artifact["runtime_files_sha256"],
            "runtime payload differs from the recorded upstream source",
        )
        require(
            digest(archive.read(prefix + "licenses/LICENSE"))
            == provenance["upstream"]["license_sha256"],
            "wheel does not preserve the upstream MIT license",
        )
    return provenance


if __name__ == "__main__":
    record = verify(Path(__file__).resolve().parent)
    print(f"Verified owned browser-use build: {record['artifact']['sha256']}")
