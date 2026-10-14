import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(os.environ.get("KB_ROOT") or Path(__file__).resolve().parents[2])
MODULES = ROOT / "wiki" / "modules"


def main():
    stale = []
    checked = 0
    for page in sorted(MODULES.glob("*.md")):
        text = page.read_text(encoding="utf-8")
        m = re.search(r"^file: (.+)$", text, re.M)
        h = re.search(r"^content_hash: ([0-9a-f]{32})$", text, re.M)
        if not (m and h):
            stale.append((page.name, "missing file/content_hash"))
            continue
        src = ROOT / m.group(1)
        if not src.exists():
            stale.append((page.name, f"source missing: {m.group(1)}"))
            continue
        cur = hashlib.md5(src.read_bytes()).hexdigest()
        checked += 1
        if cur != h.group(1):
            stale.append((page.name, f"hash mismatch: page={h.group(1)[:8]} src={cur[:8]}"))
    print(f"checked={checked} stale={len(stale)}")
    for name, why in stale:
        print(f"  STALE {name}: {why}")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
