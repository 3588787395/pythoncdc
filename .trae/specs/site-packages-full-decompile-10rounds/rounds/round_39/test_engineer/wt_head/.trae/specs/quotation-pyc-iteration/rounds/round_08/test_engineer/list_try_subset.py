#!/usr/bin/env python3
"""List which files the bounded TRY region subset picks + their pass/fail."""
import os, sys, subprocess, re

REGIONS = {"TRY": ["tests/exhaustive/try_except/"]}
MAX_FILES = {"TRY": 80}

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
            files.append(os.path.join(d, f))
    if not files:
        return []
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

files = collect("TRY")
print(f"subset_size={len(files)}")
cmd = [sys.executable, "-m", "pytest", "-v", "--no-header", "-o", "addopts="] + files
r = subprocess.run(cmd, capture_output=True, text=True, timeout=280)
out = r.stdout + r.stderr
failed = []
passed = 0
for line in out.splitlines():
    line = line.strip()
    if line.startswith("FAILED"):
        failed.append(line)
    elif line.startswith("PASSED"):
        passed += 1
print(f"passed={passed} failed={len(failed)}")
for f in failed:
    print(f)
