"""Rebuild the reviewed source patch and compare the resulting owned wheel."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tarfile
import tempfile
import tomllib
import urllib.request
from pathlib import Path

from verify import digest, require, verify


def build(directory: Path, destination: Path) -> Path:
    record = verify(directory)
    upstream = record["upstream"]
    build_tools = record["build"]
    archive_path = destination / upstream["sdist_filename"]
    with urllib.request.urlopen(upstream["sdist_url"], timeout=60) as response:
        source_bytes = response.read()
    require(
        digest(source_bytes) == upstream["sdist_sha256"],
        "downloaded upstream source hash mismatch",
    )
    archive_path.write_bytes(source_bytes)
    with tarfile.open(archive_path) as archive:
        archive.extractall(destination / "source", filter="data")
    source = destination / "source" / "browser_use-0.13.14"
    require(
        digest((source / "pyproject.toml").read_bytes())
        == upstream["pyproject_sha256"],
        "upstream manifest hash mismatch",
    )
    require(
        digest((source / "LICENSE").read_bytes()) == upstream["license_sha256"],
        "upstream source license mismatch",
    )
    patch = directory / "source.patch"
    subprocess.run(["git", "apply", "--check", str(patch)], cwd=source, check=True)
    subprocess.run(["git", "apply", str(patch)], cwd=source, check=True)
    require(
        digest((source / "pyproject.toml").read_bytes())
        == record["patch"]["patched_pyproject_sha256"],
        "patched manifest hash mismatch",
    )
    manifest = tomllib.loads((source / "pyproject.toml").read_text())
    require(
        manifest["build-system"]["requires"]
        == [f"hatchling=={build_tools['hatchling']}"],
        "upstream build backend is not pinned to the recorded version",
    )
    for name, expected in record["artifact"]["runtime_files_sha256"].items():
        require(
            digest((source / name).read_bytes()) == expected,
            f"runtime source changed by packaging patch: {name}",
        )
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = build_tools["source_date_epoch"]
    output = destination / "artifacts"
    subprocess.run(
        [
            "uv",
            "tool",
            "run",
            "--from",
            f"uv=={build_tools['uv']}",
            "uv",
            "build",
            "--wheel",
            "--python",
            build_tools["python"],
            "--out-dir",
            str(output),
            str(source),
        ],
        env=environment,
        check=True,
    )
    subprocess.run(
        [
            "uv",
            "tool",
            "run",
            "--from",
            f"wheel=={build_tools['wheel']}",
            "wheel",
            "tags",
            "--build",
            build_tools["build_tag"],
            str(output / "browser_use-0.13.14-py3-none-any.whl"),
        ],
        env=environment,
        check=True,
    )
    result = output / record["artifact"]["filename"]
    require(
        digest(result.read_bytes()) == record["artifact"]["sha256"],
        "reproduced wheel differs from the reviewed artifact",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify reproducibility")
    parser.add_argument(
        "--output", type=Path, help="copy verified build to this directory"
    )
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="mcbu-owned-build-") as temporary:
        result = build(directory, Path(temporary))
        if args.output:
            args.output.mkdir(parents=True, exist_ok=True)
            shutil.copy2(result, args.output / result.name)
        print(f"Reproduced owned browser-use build: {digest(result.read_bytes())}")


if __name__ == "__main__":
    main()
