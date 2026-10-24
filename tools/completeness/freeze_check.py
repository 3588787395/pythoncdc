#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only freeze-state checker for the basic comparator (Task 0.4).

Checks (never modifies anything):
  1. scripts/pyc_verify.py SHA256 equals the frozen baseline;
  2. external pylingual/equivalence_check.py SHA256 equals the frozen baseline;
  3. `git diff --name-only -- scripts/pyc_verify.py` output is empty;
  4. `git diff --name-only -- tests/` output is empty;
  5. current HEAD commit sha is recorded (equality with the baseline commit
     is NOT required; this check only records).

Any failure means comparator contamination: acceptance fails immediately and
new readings must not be presented as completeness evidence.

CLI:
    python -X utf8 tools/completeness/freeze_check.py
    python -X utf8 tools/completeness/freeze_check.py --json out.json
    python -X utf8 tools/completeness/freeze_check.py --md out.md
    python -X utf8 tools/completeness/freeze_check.py --json out.json --md out.md

Exit code: 0 when all checks pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

TOOL_VERSION = "1.0.0"
BASELINE_COMMIT = "e755d773"
PYC_VERIFY_SHA256 = "FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4"
EXTERNAL_EQUIV_SHA256 = "9C7567BD6776B36B6AF1991AF222CF79E48412335CA01CBB07146F9ED50045A6"
PYC_VERIFY_REL = os.path.join("scripts", "pyc_verify.py")
EXTERNAL_EQUIV_ABS = r"D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py"


def repo_root() -> str:
    # tools/completeness/freeze_check.py -> repo root is three levels up.
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def sha256_upper(path: str):
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest().upper()
    except OSError:
        return None


def run_git(args, cwd: str):
    try:
        proc = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        return None, "git-not-runnable: %s" % exc
    out = proc.stdout.decode("utf-8", "replace").strip()
    err = proc.stderr.decode("utf-8", "replace").strip()
    if proc.returncode != 0:
        return None, "git-exit-%d: %s" % (proc.returncode, err or "unknown error")
    return out, None


def make_check(name: str, ok: bool, actual, expected):
    return {"name": name, "pass": bool(ok), "actual": actual, "expected": expected}


def build_report() -> dict:
    root = repo_root()
    checks = []

    pyc_verify_path = os.path.join(root, PYC_VERIFY_REL)
    actual_sha = sha256_upper(pyc_verify_path)
    checks.append(make_check(
        "pyc_verify_sha256",
        actual_sha == PYC_VERIFY_SHA256,
        actual_sha if actual_sha is not None else "FILE MISSING/UNREADABLE: %s" % PYC_VERIFY_REL,
        PYC_VERIFY_SHA256,
    ))

    actual_ext = sha256_upper(EXTERNAL_EQUIV_ABS)
    checks.append(make_check(
        "external_equivalence_check_sha256",
        actual_ext == EXTERNAL_EQUIV_SHA256,
        actual_ext if actual_ext is not None else "FILE MISSING/UNREADABLE: %s" % EXTERNAL_EQUIV_ABS,
        EXTERNAL_EQUIV_SHA256,
    ))

    diff_pyc, err = run_git(["diff", "--name-only", "--", "scripts/pyc_verify.py"], root)
    checks.append(make_check(
        "git_diff_pyc_verify_empty",
        diff_pyc is not None and diff_pyc == "",
        diff_pyc if diff_pyc is not None else err,
        "",
    ))

    diff_tests, err = run_git(["diff", "--name-only", "--", "tests/"], root)
    checks.append(make_check(
        "git_diff_tests_empty",
        diff_tests is not None and diff_tests == "",
        diff_tests if diff_tests is not None else err,
        "",
    ))

    head, err = run_git(["rev-parse", "HEAD"], root)
    checks.append(make_check(
        "head_commit_recorded",
        head is not None,
        head if head is not None else err,
        "record-only; equality with baseline %s not required" % BASELINE_COMMIT,
    ))

    return {
        "tool": "tools/completeness/freeze_check.py",
        "version": TOOL_VERSION,
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "repo_root": root,
        "baseline_commit": BASELINE_COMMIT,
        "head_commit": head,
        "all_pass": all(c["pass"] for c in checks),
        "checks": checks,
    }


def render_md(report: dict) -> str:
    lines = []
    lines.append("# 比较器冻结校验报告（freeze_check）")
    lines.append("")
    lines.append("- 生成时间：%s" % report["generated"])
    lines.append("- 仓库根：`%s`" % report["repo_root"])
    lines.append("- 基线 commit：`%s`" % report["baseline_commit"])
    lines.append("- 当前 HEAD：`%s`" % report["head_commit"])
    lines.append("- 总体结果：**%s**" % ("ALL PASS" if report["all_pass"] else "FAIL"))
    lines.append("")
    lines.append("| 检查项 | pass | 实际值 | 期望值 |")
    lines.append("|---|---|---|---|")
    for c in report["checks"]:
        actual = str(c["actual"]).replace("|", "\\|")
        expected = str(c["expected"]).replace("|", "\\|")
        lines.append("| `%s` | %s | `%s` | `%s` |" % (
            c["name"], "true" if c["pass"] else "false", actual, expected))
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only freeze-state check for the basic comparator (Task 0.4).")
    parser.add_argument("--json", metavar="OUT_JSON", help="write JSON report to this file")
    parser.add_argument("--md", metavar="OUT_MD", help="write Markdown report to this file")
    args = parser.parse_args(argv)

    report = build_report()
    payload = json.dumps(report, ensure_ascii=False, indent=2)

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(payload + "\n")
    else:
        sys.stdout.write(payload + "\n")

    if args.md:
        with open(args.md, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render_md(report) + "\n")

    failed = [c["name"] for c in report["checks"] if not c["pass"]]
    if failed:
        sys.stderr.write("freeze_check: FAIL -> %s\n" % ", ".join(failed))
    else:
        sys.stderr.write("freeze_check: ALL PASS (%d/%d checks)\n" % (
            len(report["checks"]), len(report["checks"])))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
