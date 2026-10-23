#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C1-C5 judgment-space coverage checker (Task 9.3).

An entry is covered only when all five conditions hold:
  C1 source exists, is non-empty, and its sha256/line count match;
  C2 pyc exists, matches its sha256, and is loadable by this interpreter;
  C3 decompiled product exists, matches its sha256, and has a command;
  C4 semantic_diff has run with verdict/seed/exit code;
  C5 the same record binds C1-C3 hashes, C4, judge sha, runner version.

Missing C3/C4 is probe_only/unexecuted, never covered.  INCONCLUSIVE is
never covered.  The old "probe path exists = covered" reading is gone.

CLI:
    python -X utf8 tools/completeness/coverage_checker.py \
        --space J.json --evidence c1c5.json --judge scripts/pyc_verify.py \
        --out COVERAGE.md --json coverage.json
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import importlib.util
import json
import marshal
import os
import sys

CHECKER_VERSION = "2.0.0"
VERDICTS = ("EQUAL", "DIFFERENT", "INCONCLUSIVE", "ERROR")
NON_COVERED = ("probe_only", "unexecuted", "n/a", "inconclusive", "excluded", "uncovered")


def sha256_file(path: str):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def norm_path(value: str) -> str:
    value = (value or "").replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    return value


def resolve_path(value: str) -> str:
    value = norm_path(value)
    if not value:
        return ""
    return os.path.abspath(value)


def _lines(path: str):
    try:
        with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
            return len(fh.read().splitlines())
    except OSError:
        return None


def _sha_ok(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value.lower())


def load_space(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        space = json.load(fh)
    if not isinstance(space, dict):
        raise ValueError("judgment space manifest must be a JSON object")
    if not isinstance(space.get("entries"), list):
        raise ValueError("judgment space manifest has no 'entries' list")
    return space


def load_evidence(path: str) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8-sig") as fh:
        data = json.load(fh)
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        if isinstance(data.get("records"), list):
            records = data["records"]
        else:
            records = []
            for key, value in data.items():
                if isinstance(value, dict):
                    record = dict(value)
                    record.setdefault("entry_id", key)
                    records.append(record)
    else:
        raise ValueError("evidence manifest must be a JSON object or list")
    out = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        eid = record.get("entry_id") or record.get("j_id") or record.get("id")
        if isinstance(eid, str) and eid:
            out[eid] = record
    return out


def _c1(entry: dict, record: dict):
    c1 = record.get("c1") if isinstance(record.get("c1"), dict) else {}
    path = c1.get("source_path") or entry.get("p_j")
    expected = c1.get("sha256") or entry.get("p_j_sha256")
    if not path:
        return False, "c1_source_missing", {}
    path = resolve_path(path)
    if not os.path.isfile(path):
        return False, "c1_source_missing", {"path": path}
    if os.path.getsize(path) == 0:
        return False, "c1_source_empty", {"path": path}
    actual = sha256_file(path)
    if not actual:
        return False, "c1_source_unreadable", {"path": path}
    if not _sha_ok(expected):
        return False, "c1_sha_missing", {"path": path}
    if actual != str(expected).lower():
        return False, "c1_sha_mismatch", {"path": path, "actual": actual}
    lines = c1.get("lines") if isinstance(c1.get("lines"), int) else entry.get("p_j_lines")
    if not isinstance(lines, int) or lines <= 0:
        return False, "c1_lines_missing", {"path": path}
    return True, "ok", {"path": path, "sha256": actual, "lines": lines}


def _c2(entry: dict, record: dict):
    c2 = record.get("c2") if isinstance(record.get("c2"), dict) else {}
    path = c2.get("pyc_path") or entry.get("pyc")
    expected = c2.get("sha256") or entry.get("pyc_sha256")
    if not path:
        return False, "c2_pyc_missing", {}
    path = resolve_path(path)
    if not os.path.isfile(path):
        return False, "c2_pyc_missing", {"path": path}
    actual = sha256_file(path)
    if not actual:
        return False, "c2_pyc_unreadable", {"path": path}
    if not _sha_ok(expected):
        return False, "c2_sha_missing", {"path": path}
    if actual != str(expected).lower():
        return False, "c2_sha_mismatch", {"path": path, "actual": actual}
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        if len(data) < 16:
            raise ValueError("short pyc")
        if data[:4] != importlib.util.MAGIC_NUMBER:
            raise ValueError("magic mismatch")
        marshal.loads(data[16:])
    except BaseException as exc:
        return False, "c2_pyc_unloadable", {"path": path, "error": "%s: %s" % (type(exc).__name__, exc)}
    version = c2.get("python_version") or sys.version.split()[0]
    if not isinstance(version, str) or not version:
        return False, "c2_version_missing", {"path": path}
    return True, "ok", {"path": path, "sha256": actual, "python_version": version}


def _c3(record: dict):
    c3 = record.get("c3") if isinstance(record.get("c3"), dict) else {}
    path = c3.get("product_path")
    if not path:
        return False, "c3_product_missing", {}
    path = resolve_path(path)
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return False, "c3_product_missing", {"path": path}
    actual = sha256_file(path)
    if not actual:
        return False, "c3_product_unreadable", {"path": path}
    expected = c3.get("sha256")
    if not _sha_ok(expected):
        return False, "c3_sha_missing", {"path": path}
    if actual != str(expected).lower():
        return False, "c3_sha_mismatch", {"path": path, "actual": actual}
    command = c3.get("command")
    if not isinstance(command, str) or not command.strip():
        return False, "c3_command_missing", {"path": path}
    return True, "ok", {"path": path, "sha256": actual, "command": command}


def _c4(record: dict):
    c4 = record.get("c4") if isinstance(record.get("c4"), dict) else {}
    verdict = c4.get("verdict")
    if verdict not in VERDICTS:
        return False, "c4_verdict_missing", {}
    if "seed" not in c4:
        return False, "c4_seed_missing", {"verdict": verdict}
    if not isinstance(c4.get("exit_code"), int):
        return False, "c4_exit_missing", {"verdict": verdict}
    return True, "ok", {"verdict": verdict, "seed": c4.get("seed"),
                        "exit_code": c4.get("exit_code")}


def _c5(record: dict, c1: dict, c2: dict, c3: dict, judge_sha):
    c5 = record.get("c5") if isinstance(record.get("c5"), dict) else {}
    if not c5:
        return False, "c5_missing", {}
    for key, value in (("source_sha256", c1.get("sha256")),
                       ("pyc_sha256", c2.get("sha256")),
                       ("product_sha256", c3.get("sha256"))):
        if not _sha_ok(c5.get(key)) or str(c5.get(key)).lower() != str(value).lower():
            return False, "c5_chain_mismatch", {"field": key}
    if not _sha_ok(c5.get("judge_sha256")):
        return False, "c5_judge_missing", {}
    if judge_sha and str(c5.get("judge_sha256")).lower() != judge_sha:
        return False, "c5_judge_mismatch", {"expected": judge_sha}
    if not isinstance(c5.get("runner_version"), str) or not c5["runner_version"]:
        return False, "c5_runner_missing", {}
    return True, "ok", {"judge_sha256": c5.get("judge_sha256"),
                        "runner_version": c5.get("runner_version")}


def check(space: dict, evidence: dict, judge_sha=None):
    rows = []
    per_family = collections.defaultdict(lambda: collections.Counter())
    for index, entry in enumerate(space.get("entries") or []):
        if not isinstance(entry, dict):
            continue
        eid = entry.get("id") or ("#%d" % index)
        form = entry.get("form") or "?"
        record = evidence.get(eid, {})
        c1_ok, c1_reason, c1 = _c1(entry, record)
        c2_ok, c2_reason, c2 = _c2(entry, record)
        c3_ok, c3_reason, c3 = _c3(record) if c1_ok and c2_ok else (False, "c3_not_reached", {})
        c4_ok, c4_reason, c4 = _c4(record) if c3_ok else (False, "c4_not_reached", {})
        c5_ok, c5_reason, c5 = (_c5(record, c1, c2, c3, judge_sha)
                                if c4_ok and c4.get("verdict") not in ("INCONCLUSIVE", "ERROR")
                                else (False, "c5_not_reached", {}))
        excluded = bool(entry.get("excluded")) or entry.get("status") == "excluded" or record.get("status") == "excluded"
        na = entry.get("status") == "n/a" or bool(entry.get("n/a")) or record.get("status") == "n/a"
        verdict = c4.get("verdict") if c4_ok else None
        if excluded:
            status, reason = "excluded", "entry_excluded"
        elif na:
            status, reason = "n/a", "entry_n/a"
        elif not c1_ok:
            status, reason = "uncovered", c1_reason
        elif not c2_ok:
            status, reason = "probe_only", c2_reason
        elif not c3_ok:
            status, reason = "probe_only", c3_reason
        elif not c4_ok:
            status, reason = "unexecuted", c4_reason
        elif verdict in ("INCONCLUSIVE", "ERROR"):
            status, reason = "inconclusive", "c4_%s" % verdict.lower()
        elif not c5_ok:
            status, reason = "uncovered", c5_reason
        else:
            status, reason = "covered_5tuple", "ok"
        per_family[form][status] += 1
        per_family[form]["total"] += 1
        rows.append({
            "id": eid, "form": form, "host": entry.get("host"),
            "depth": entry.get("depth"), "variant": entry.get("variant"),
            "row": entry.get("row"), "status": status, "reason": reason,
            "declared_status": entry.get("status"), "verdict": verdict,
            "green": bool(status == "covered_5tuple" and verdict == "EQUAL"),
            "witness_pyc": entry.get("pyc") or (entry.get("required_evidence") or [{}])[0].get("pyc"),
            "expected_label": entry.get("expected_label"),
            "c1": c1, "c2": c2, "c3": c3, "c4": c4, "c5": c5,
        })
    return rows, per_family


def write_json(path: str, payload: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def write_md(path: str, payload: dict, per_family: dict, space: dict) -> None:
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    t = payload["totals"]
    lines = []
    add = lines.append
    add("# C1-C5 判定空间覆盖报告（Task 9.3）")
    add("")
    add("> checker `%s`；space `%s`；J schema `%s`；evidence `%s`。"
        % (payload["checker_version"], payload["space_path"],
           space.get("j_schema_version"), payload["evidence_path"] or "(none)"))
    add("")
    add("| 读数 | 值 |")
    add("|---|---:|")
    for key in ("J_total", "covered_5tuple", "probe_only", "unexecuted", "n/a",
                "inconclusive", "excluded", "uncovered", "semantic_failures", "green"):
        add("| %s | %d |" % (key, t[key]))
    add("| coverage_pct | %.2f%% |" % t["coverage_pct"])
    add("| checker_version | %s |" % payload["checker_version"])
    add("")
    add("口径：`covered_5tuple` 必须同时有 C1 源 hash/行数、C2 pyc hash/可加载、C3 产物 hash/命令、"
        "C4 verdict/seed/exit、C5 同一记录哈希链 + judge/runner。`probe_only`、`unexecuted`、"
        "`n/a`、`inconclusive`、`excluded`、`uncovered` 全部不计入 covered。")
    add("")
    add("## 逐形态族")
    add("")
    add("| form | total | covered_5tuple | probe_only | unexecuted | n/a | inconclusive | excluded | uncovered |")
    add("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for form in sorted(per_family):
        c = per_family[form]
        add("| %s | %d | %d | %d | %d | %d | %d | %d | %d |" % (
            form, c["total"], c["covered_5tuple"], c["probe_only"], c["unexecuted"],
            c["n/a"], c["inconclusive"], c["excluded"], c["uncovered"]))
    add("")
    add("## 未覆盖/未完全覆盖条目")
    add("")
    add("| id | status | reason | form | host | depth | variant |")
    add("|---|---|---|---|---|---|---|")
    for row in payload["uncovered"]:
        add("| %s | %s | %s | %s | %s | %s | %s |" % (
            row["id"], row["status"], row["reason"], row["form"], row["host"],
            row["depth"], row["variant"]))
    add("")
    add("## 复算")
    add("")
    add("```")
    add("python -X utf8 tools/completeness/coverage_checker.py \\")
    add("  --space %s --evidence %s --json %s" % (
        payload["space_path"], payload["evidence_path"] or "c1c5.json", payload["json_path"]))
    add("```")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="C1-C5 judgment-space coverage checker")
    parser.add_argument("--space", required=True)
    parser.add_argument("--evidence", default="")
    parser.add_argument("--judge", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--json", default="")
    parser.add_argument("--allow-uncovered", action="store_true")
    parser.add_argument("--list-uncovered", action="store_true")
    parser.add_argument("--evidence-root", default="",
                        help="deprecated; old probe-only index is not accepted as C1-C5 evidence")
    parser.add_argument("--version", action="version", version=CHECKER_VERSION)
    args = parser.parse_args(argv)
    if args.evidence_root and not args.evidence:
        print("[coverage] NOTE: --evidence-root is ignored; C1-C5 needs --evidence", file=sys.stderr)
    try:
        space = load_space(args.space)
        evidence = load_evidence(args.evidence)
    except Exception as exc:
        print("[coverage] ERROR: %s" % exc, file=sys.stderr)
        return 2
    judge_sha = sha256_file(args.judge) if args.judge else None
    if args.judge and not judge_sha:
        print("[coverage] ERROR: cannot read judge %s" % args.judge, file=sys.stderr)
        return 2
    rows, per_family = check(space, evidence, judge_sha)
    counts = collections.Counter(row["status"] for row in rows)
    total = len(rows)
    covered = counts["covered_5tuple"]
    uncovered = total - covered
    payload = {
        "space_path": norm_path(args.space),
        "evidence_path": norm_path(args.evidence),
        "json_path": norm_path(args.json),
        "checker_version": CHECKER_VERSION,
        "j_schema_version": space.get("j_schema_version"),
        "evidence_records": len(evidence),
        "judge_sha256": judge_sha,
        "totals": {
            "J_total": total, "covered_5tuple": covered,
            "probe_only": counts["probe_only"], "unexecuted": counts["unexecuted"],
            "n/a": counts["n/a"], "inconclusive": counts["inconclusive"],
            "excluded": counts["excluded"], "uncovered": uncovered,
            "semantic_failures": sum(1 for row in rows if row["verdict"] == "DIFFERENT"),
            "green": sum(1 for row in rows if row["green"]),
            "coverage_pct": (100.0 * covered / total) if total else 0.0,
        },
        "per_family": {
            form: {
                "total": c["total"], "covered_5tuple": c["covered_5tuple"],
                "probe_only": c["probe_only"], "unexecuted": c["unexecuted"],
                "n/a": c["n/a"], "inconclusive": c["inconclusive"],
                "excluded": c["excluded"],
                "uncovered": c["total"] - c["covered_5tuple"],
            }
            for form, c in sorted(per_family.items())
        },
        "uncovered": [{key: row[key] for key in
                       ("id", "status", "reason", "form", "host", "depth", "variant", "verdict")}
                      for row in rows if row["status"] != "covered_5tuple"],
        "rows": rows,
    }
    if args.out:
        write_md(args.out, payload, per_family, space)
    if args.json:
        write_json(args.json, payload)
    t = payload["totals"]
    print("[coverage] J_total=%d covered_5tuple=%d probe_only=%d unexecuted=%d n/a=%d "
          "inconclusive=%d excluded=%d uncovered=%d coverage=%.2f%%"
          % (t["J_total"], t["covered_5tuple"], t["probe_only"], t["unexecuted"], t["n/a"],
             t["inconclusive"], t["excluded"], t["uncovered"], t["coverage_pct"]))
    if args.list_uncovered:
        for row in payload["uncovered"]:
            print("[uncovered] %s %s %s | %s | %s | %s" % (
                row["id"], row["status"], row["reason"], row["form"], row["host"], row["variant"]))
    if uncovered > 0 and not args.allow_uncovered:
        print("[coverage] GATE FAIL: uncovered=%d (covered_5tuple is the only numerator)" % uncovered)
        return 1
    if uncovered > 0:
        print("[coverage] GATE BYPASSED: uncovered=%d" % uncovered)
        return 0
    print("[coverage] GATE PASS: covered_5tuple=%d" % covered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
