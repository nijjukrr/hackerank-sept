"""Packages the final submission zip (code.zip) excluding dataset, venv, pycache."""

import os
import zipfile
from pathlib import Path

root = Path(".").resolve()
zip_path = root / "code.zip"

if zip_path.exists():
    zip_path.unlink()

include_paths = [
    root / "README.md",
    root / "CONSTANTS.md",
    root / "evaluation",
    root / "code",
]

excluded_patterns = [
    "__pycache__",
    ".pyc",
    ".git",
    ".venv",
    "venv",
    ".DS_Store",
    "code.zip",
]

print(f"Creating {zip_path}...")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for base in include_paths:
        if base.is_file():
            zf.write(base, arcname=base.relative_to(root))
            print(f"  Added {base.relative_to(root)}")
        elif base.is_dir():
            for root_dir, dirs, files in os.walk(base):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not any(p in d for p in excluded_patterns)]
                for file in files:
                    if any(p in file for p in excluded_patterns):
                        continue
                    file_path = Path(root_dir) / file
                    rel_name = file_path.relative_to(root)
                    zf.write(file_path, arcname=rel_name)
                    print(f"  Added {rel_name}")

print(f"Successfully packaged {zip_path} ({zip_path.stat().st_size} bytes)")
