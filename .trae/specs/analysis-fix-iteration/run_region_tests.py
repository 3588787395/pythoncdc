#!/usr/bin/env python3
"""Quick per-region regression runner.

Usage: python run_region_tests.py <region>
Prints: <passed> <failed> <errors> <total> <duration_s>

Selects a stable, bounded subset of each region's tests so the whole run
finishes well under 300s. Subset selection is deterministic (sorted file list,
every Nth file capped at MAX_FILES).
"""
import os
import sys
import subprocess
import time

REGIONS = {
    "IF": ["tests/exhaustive/if_region/"],
    "LOOP": ["tests/exhaustive/while_loop/", "tests/exhaustive/for_loop/"],
    "TRY": ["tests/exhaustive/try_except/"],
    "WITH": ["tests/exhaustive/with_region/"],
    "MATCH": ["tests/exhaustive/match_region/"],
    "ASSERT": ["tests/exhaustive/ternary/", "tests/exhaustive/if_region/", "tests/nook/"],
    "BOOLOP": ["tests/exhaustive/bool_op/", "tests/exhaustive/boolop/"],
    "TERNARY": ["tests/exhaustive/ternary/"],
    "CC": ["tests/exhaustive/if_region/", "tests/exhaustive/boolop/"],
    "SEQ": ["tests/exhaustive/basic/", "tests/exhaustive/L1_basic/"],
}

MAX_FILES = {
    "IF": 80, "LOOP": 80, "TRY": 80, "WITH": 80, "MATCH": 80,
    "ASSERT": 30, "BOOLOP": 80, "TERNARY": 80, "CC": 40, "SEQ": 80,
}

# For ASSERT/CC, filter by filename keywords since they share dirs.
ASSERT_KEYWORDS = ("assert",)
CC_KEYWORDS = ("chain", "compare", "chained", "cmp")


def collect(region):
    dirs = REGIONS[region]
    max_files = MAX_FILES[region]
    files = []
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if not f.startswith("test_") or not f.endswith(".py"):
                continue
            if f == "__init__.py":
                continue
            if region == "ASSERT":
                if not any(k in f.lower() for k in ASSERT_KEYWORDS):
                    continue
            if region == "CC":
                if not any(k in f.lower() for k in CC_KEYWORDS):
                    continue
            files.append(os.path.join(d, f))
    if not files:
        return []
    # Deterministic bounded subset: stride to spread coverage, cap at max_files.
    if len(files) <= max_files:
        return files
    stride = len(files) / max_files
    idx = [int(i * stride) for i in range(max_files)]
    seen = set()
    out = []
    for i in idx:
        if i not in seen:
            seen.add(i)
            out.append(files[i])
    return out


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in REGIONS:
        print(f"usage: {sys.argv[0]} <region>", file=sys.stderr)
        print(f"regions: {list(REGIONS)}", file=sys.stderr)
        sys.exit(2)
    region = sys.argv[1]
    files = collect(region)
    if not files:
        print("0 0 0 0 0.0")
        return
    t0 = time.time()
    # -p no:cacheprovider to avoid cache overhead/flakiness
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
           "--no-header", "-o", "addopts="] + files
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=280, cwd=os.getcwd())
        out = r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT region={region} files={len(files)}", file=sys.stderr)
        print("0 0 0 0 280.0")
        return
    dur = time.time() - t0
    passed = failed = errors = 0
    for line in out.splitlines():
        line = line.strip()
        # match "N passed", "N failed", "N errors" possibly combined
        if "passed" in line and ("failed" in line or "error" in line):
            pass
        import re
        m = re.search(r"(\d+)\s+passed", line)
        if m:
            passed = int(m.group(1))
        m = re.search(r"(\d+)\s+failed", line)
        if m:
            failed = int(m.group(1))
        m = re.search(r"(\d+)\s+error", line)
        if m:
            errors = int(m.group(1))
    total = passed + failed + errors
    print(f"{passed} {failed} {errors} {total} {dur:.1f} {region} files={len(files)}")


if __name__ == "__main__":
    main()
