#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canary runner and leak scan for attack-completeness-claims Task 9.5.

Canaries are opaque JSON probes supplied by an independent custodian.  This
tool does not ship any probe text in its public output: it records only
canary ids, category, source hash, verdict and a seed digest.  If a canary
directory is absent, G6 is UNESTABLISHED, never green.

CLI:
    python -X utf8 tools/completeness/canary_runner.py \
        --canary .canary-private --json rounds/round9/canary_report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import fuzz_driver as fd

TOOL_VERSION = "1.0.0"
CATEGORIES = ("rare_syntax", "deep_host", "semantic_trap")
DEFAULT_SCAN_ROOTS = (
    "core", "tools", "tests", "wiki", "docs", "rules.md",
    ".trae/specs/attack-completeness-claims",
)


def sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_canaries(directory: str) -> list[dict]:
    if not os.path.isdir(directory):
        return []
    out = []
    for name in sorted(os.listdir(directory)):
        if not name.lower().endswith(".json"):
            continue
        path = os.path.join(directory, name)
        with open(path, "r", encoding="utf-8-sig") as fh:
            item = json.load(fh)
        if item.get("source_file"):
            source_path = os.path.join(directory, item["source_file"])
            with open(source_path, "r", encoding="utf-8-sig") as fh:
                item["source"] = fh.read()
        item.setdefault("canary_id", os.path.splitext(name)[0])
        item.setdefault("category", "unknown")
        item.setdefault("entrypoint", "main")
        item.setdefault("args", [])
        item.setdefault("kwargs", {})
        item.setdefault("features", [])
        out.append(item)
    return out


def _read_text(path: str) -> str:
    try:
        if os.path.getsize(path) > 2_000_000:
            return ""
        with open(path, "r", encoding="utf-8-sig", errors="ignore") as fh:
            return fh.read()
    except (OSError, UnicodeError):
        return ""


def scan_leaks(canaries: list[dict], roots: list[str], exclude: str = "") -> list[dict]:
    exclude_real = os.path.realpath(exclude) if exclude else ""
    features = []
    for item in canaries:
        for feature in item.get("features") or []:
            if isinstance(feature, str) and len(feature) >= 8:
                features.append((item.get("canary_id"), feature))
    if not features:
        return []
    hits = []
    seen_paths = set()
    for root in roots:
        path = os.path.abspath(root)
        if os.path.isfile(path):
            files = [path]
        elif os.path.isdir(path):
            files = []
            for dirpath, dirnames, filenames in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__",
                                                                 ".pytest_cache", "node_modules")]
                for name in filenames:
                    files.append(os.path.join(dirpath, name))
        else:
            continue
        for file_path in files:
            real = os.path.realpath(file_path)
            if real in seen_paths:
                continue
            if exclude_real and (real == exclude_real or real.startswith(exclude_real + os.sep)):
                continue
            seen_paths.add(real)
            text = _read_text(file_path)
            if not text:
                continue
            for canary_id, feature in features:
                if feature in text:
                    try:
                        display = os.path.relpath(file_path, ROOT)
                    except ValueError:
                        display = os.path.abspath(file_path)
                    hits.append({"canary_id": canary_id, "feature": feature,
                                 "path": display})
    return hits


def _write_markdown(path: str, report: dict) -> None:
    lines = ["# Canary leak scan", "",
             "- canaries: %d" % report["canaries"],
             "- leak hits: %d" % len(report.get("leak_hits") or []),
             "- scan roots: %s" % ", ".join(report.get("scan_roots") or []), ""]
    if report.get("leak_hits"):
        lines.append("| canary | feature | path |")
        lines.append("|---|---|---|")
        for hit in report["leak_hits"]:
            lines.append("| %s | `%s` | `%s` |" % (hit["canary_id"], hit["feature"], hit["path"]))
    else:
        lines.append("No canary feature string was found in the scanned public paths.")
    lines.extend(["", "The scan is limited to the listed roots; it is not a full-filesystem",
                  "secret scan.  A hit invalidates the round evidence."])
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="run opaque canaries and leak scan")
    parser.add_argument("--canary", required=True)
    parser.add_argument("--json", required=True)
    parser.add_argument("--leak-scan-md", default="")
    parser.add_argument("--scan-root", action="append", default=[])
    parser.add_argument("--custody", default="local-bootstrap",
                        choices=("local-bootstrap", "independent"))
    parser.add_argument("--rotation", default="")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=20.0)
    parser.add_argument("--decompiler", default=fd.PYCDC)
    parser.add_argument("--workdir", default="")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)
    canaries = load_canaries(args.canary)
    roots = args.scan_root or list(DEFAULT_SCAN_ROOTS)
    workdir = args.workdir or os.path.join(ROOT, ".canary-work")
    os.makedirs(workdir, exist_ok=True)
    results = []
    for item in canaries:
        source = item.get("source") or ""
        cid = item.get("canary_id")
        case_dir = os.path.join(workdir, cid)
        if not source:
            results.append({"canary_id": cid, "category": item.get("category"),
                            "verdict": "MISSING_SOURCE", "source_sha256": None})
            continue
        result = fd.evaluate_source(source, cid, case_dir,
                                    entrypoint=item.get("entrypoint") or "main",
                                    args=item.get("args") or [], kwargs=item.get("kwargs") or {},
                                    seed=args.seed, decompiler=args.decompiler,
                                    timeout=args.timeout)
        results.append({
            "canary_id": cid, "category": item.get("category"),
            "source_sha256": sha_text(source),
            "seed_hash": sha_text("%s|%s|%s" % (cid, args.seed, source))[:16],
            "verdict": result.get("status"),
            "diffs": result.get("diffs") or [],
            "errors": result.get("errors") or [],
        })
    counts = {}
    for result in results:
        counts[result["verdict"]] = counts.get(result["verdict"], 0) + 1
    leak_hits = scan_leaks(canaries, roots, exclude=args.canary)
    rotation_ok = False
    if args.rotation and os.path.isfile(args.rotation):
        try:
            with open(args.rotation, "r", encoding="utf-8-sig") as fh:
                rotation_ok = bool(json.load(fh).get("complete"))
        except (OSError, ValueError):
            rotation_ok = False
    if len(canaries) < 24:
        g6 = "UNESTABLISHED"
        reason = "fewer_than_24_canaries"
    elif any(result["verdict"] != "EQUAL" for result in results):
        g6 = "FAIL"
        reason = "canary_not_equal"
    elif leak_hits:
        g6 = "FAIL"
        reason = "canary_leak"
    elif args.custody != "independent":
        g6 = "INCONCLUSIVE"
        reason = "local_bootstrap_custody"
    elif not rotation_ok:
        g6 = "INCONCLUSIVE"
        reason = "rotation_record_missing"
    else:
        g6 = "PASS"
        reason = "ok"
    report = {
        "tool": "canary_runner", "version": TOOL_VERSION,
        "canaries": len(canaries), "counts": counts,
        "equal": counts.get("EQUAL", 0),
        "custody": args.custody, "rotation_ok": rotation_ok,
        "g6": g6, "reason": reason,
        "scan_roots": roots,
        "leak_hits": leak_hits,
        "results": results,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.json)), exist_ok=True)
    with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    if args.leak_scan_md:
        _write_markdown(args.leak_scan_md, report)
    print("[canary] canaries=%d equal=%d leaks=%d G6=%s reason=%s"
          % (len(canaries), report["equal"], len(leak_hits), g6, reason))
    if g6 == "PASS":
        return 0
    return 1 if g6 == "FAIL" else 2


if __name__ == "__main__":
    sys.exit(main())
