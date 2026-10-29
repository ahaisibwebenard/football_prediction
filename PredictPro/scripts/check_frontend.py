"""Syntax-check all first-party browser modules using Node 20+ (optional)."""

import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
files = [p for p in (root / "frontend").rglob("*.js") if "vendor" not in p.parts]
for p in files:
    subprocess.run(
        ["node", "--input-type=module", "--check"],
        input=p.read_text(),
        text=True,
        check=True,
    )
print(f"{len(files)} JavaScript modules passed syntax checks.")
