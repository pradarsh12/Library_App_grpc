"""Compile the .proto files in proto/ into Python stubs under src/library/.

Run with the project's venv active:

    python scripts/generate_proto.py

Cross-platform equivalent of a small shell script; kept as Python so it
works the same on Windows/macOS/Linux without a separate .sh/.ps1 pair.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto"
OUT_DIR = ROOT / "src"

PROTO_FILES = sorted(PROTO_DIR.glob("library/v1/*.proto"))


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "grpc_tools.protoc",
        f"-I{PROTO_DIR}",
        f"--python_out={OUT_DIR}",
        f"--grpc_python_out={OUT_DIR}",
        *[str(p) for p in PROTO_FILES],
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)

    # grpc_tools.protoc doesn't emit __init__.py files; add them so the
    # generated tree is importable as `library.v1.xxx_pb2`.
    for pkg_dir in [OUT_DIR / "library", OUT_DIR / "library" / "v1"]:
        init_file = pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")

    print(f"Generated stubs in {OUT_DIR / 'library'}")


if __name__ == "__main__":
    main()
