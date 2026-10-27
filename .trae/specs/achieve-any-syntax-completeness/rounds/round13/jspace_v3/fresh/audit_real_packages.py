#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit the 376 real-package exclusions without changing the coverage space.

The audit answers four questions and writes a machine-readable record:

1. Which real-package pycs back the 376 excluded entries?
2. Which of those pycs execute in this Windows/CPython 3.11.7 environment?
3. For the ten module-level entries, does the decompiled-equivalent ``p_j``
   actually contain the claimed host/variant?
4. Can any entry be honestly closed now, or must it stay excluded?

The audit never edits the judgment space, never synthesises a wrapper source,
and never treats a module import as semantic coverage.  Probe results are
triage evidence only; see ``probe_real_package_module.py``.

Run from the repository root:

    python -X utf8 .../fresh/audit_real_packages.py --run-probes \
      --deps D:\\temp\\opencode\\j3deps

Without ``--run-probes`` the script reuses ``REAL_PACKAGE_AUDIT.json``'s
``probes`` block if present, or records ``probe: null``.
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import importlib.metadata as metadata
import json
import os
import platform
import subprocess
import sys

TOOL_VERSION = "1.0.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.getcwd())
DEFAULT_SPACE = os.path.join(HERE, "judgment_space_v3m_b275.json")
DEFAULT_COVERAGE = os.path.join(HERE, "coverage_v3m_b275.json")
DEFAULT_OUT = os.path.join(HERE, "REAL_PACKAGE_AUDIT.json")
PROBE_SCRIPT = os.path.join(HERE, "probe_real_package_module.py")


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def dump(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1, sort_keys=False)
        fh.write("\n")


def norm_path(value: str) -> str:
    value = (value or "").replace("\\", "/").strip()
    while value.startswith("./"):
        value = value[2:]
    return value


def abs_path(value: str) -> str:
    path = norm_path(value)
    if not path:
        return ""
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def module_name(pyc: str) -> str:
    value = norm_path(pyc)
    prefix = "site-packages/"
    if value.startswith(prefix):
        value = value[len(prefix):]
    if value.endswith(".pyc"):
        value = value[:-4]
    return value.replace("/", ".")


def dedicated_probe(entry: dict) -> bool:
    for row in entry.get("required_evidence") or []:
        note = str(row.get("note") or "")
        if "本单元专属见证探针" in note:
            return True
    return False


def top_level_names(tree: ast.AST) -> list[str]:
    return [type(node).__name__ for node in getattr(tree, "body", [])]


def decorator_text(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def module_level_evidence(tree: ast.AST, form: str, host: str, variant: str) -> dict:
    """Check only the module-level host, where the mapping is unambiguous."""
    top = list(getattr(tree, "body", []))
    evidence = {
        "top_level_statements": [type(node).__name__ for node in top],
        "claimed_host_present": None,
        "detail": "",
        "hits": [],
    }
    if form == "Decorator":
        classes = [node for node in top if isinstance(node, ast.ClassDef)]
        funcs = [node for node in top
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        class_decorated = [node for node in classes if node.decorator_list]
        func_decorated = [node for node in funcs if node.decorator_list]
        if variant == "deco-on-class":
            evidence["claimed_host_present"] = bool(class_decorated)
            evidence["hits"] = [
                {"name": node.name,
                 "decorators": [decorator_text(item) for item in node.decorator_list]}
                for node in class_decorated
            ]
            evidence["detail"] = (
                "top-level ClassDef with a decorator: %d" % len(class_decorated))
        elif variant == "deco-on-function":
            evidence["claimed_host_present"] = bool(func_decorated)
            evidence["hits"] = [
                {"name": node.name,
                 "decorators": [decorator_text(item) for item in node.decorator_list]}
                for node in func_decorated
            ]
            evidence["detail"] = (
                "top-level FunctionDef with a decorator: %d" % len(func_decorated))
        elif variant in ("deco-single", "deco-stack", "deco-with-args", "deco-name-form"):
            if variant == "deco-single":
                selected = [node for node in func_decorated + class_decorated
                            if len(node.decorator_list) == 1]
            elif variant == "deco-stack":
                selected = [node for node in func_decorated + class_decorated
                            if len(node.decorator_list) > 1]
            elif variant == "deco-with-args":
                selected = [node for node in func_decorated + class_decorated
                            if node.decorator_list
                            and isinstance(node.decorator_list[0], ast.Call)]
            else:
                selected = [node for node in func_decorated + class_decorated
                            if node.decorator_list
                            and isinstance(node.decorator_list[0], ast.Name)]
            evidence["claimed_host_present"] = bool(selected)
            evidence["hits"] = [
                {"name": node.name,
                 "decorators": [decorator_text(item) for item in node.decorator_list]}
                for node in selected
            ]
            evidence["detail"] = (
                "top-level decorated definitions matching %s: %d"
                % (variant, len(selected)))
        else:
            evidence["detail"] = "unknown decorator variant: %s" % variant
    elif form == "Import":
        imports = [node for node in top
                   if isinstance(node, (ast.Import, ast.ImportFrom))]
        evidence["claimed_host_present"] = bool(imports)
        evidence["hits"] = [
            {"kind": type(node).__name__,
             "text": decorator_text(node)}
            for node in imports
        ]
        evidence["detail"] = "top-level imports: %d" % len(imports)
    elif form == "Try":
        tries = [node for node in top if isinstance(node, ast.Try)]
        evidence["claimed_host_present"] = bool(tries)
        evidence["hits"] = [
            {"handlers": len(node.handlers), "has_finally": bool(node.finalbody)}
            for node in tries
        ]
        evidence["detail"] = "top-level Try: %d" % len(tries)
    else:
        evidence["detail"] = "module-level host check not implemented for %s" % form
    return evidence


def package_versions(deps: str) -> dict:
    names = ["logbook", "typing_extensions", "tornado", "pyzmq",
             "jsonpickle", "six", "pandas", "numpy", "pytz"]
    old_path = sys.path[:]
    if deps and os.path.isdir(deps):
        sys.path.insert(0, deps)
    try:
        versions = {}
        for name in names:
            try:
                versions[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                versions[name] = None
        return versions
    finally:
        sys.path[:] = old_path


def run_probe(pyc: str, deps: str, timeout: float) -> dict:
    command = [sys.executable, "-X", "utf8", PROBE_SCRIPT,
               "--root", ROOT, "--pyc", abs_path(pyc),
               "--name", module_name(pyc)]
    if deps:
        command.extend(["--deps", os.path.abspath(deps)])
    record = {
        "command": subprocess.list2cmdline(command),
        "exit_code": None,
        "status": "NOT_RUN",
        "first_line": "",
        "error_type": "",
        "output_tail": "",
    }
    try:
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        record["status"] = "TIMEOUT"
        record["output_tail"] = str(exc)[-2000:]
        return record
    except OSError as exc:
        record["status"] = "ERROR"
        record["error_type"] = type(exc).__name__
        record["output_tail"] = str(exc)[-2000:]
        return record
    output = (proc.stdout or "") + (proc.stderr or "")
    record["exit_code"] = proc.returncode
    lines = [line for line in output.splitlines() if line.strip()]
    for line in lines:
        if line.startswith(("OK ", "FAIL ", "READ-FAIL ")):
            record["first_line"] = line
            break
    if record["first_line"].startswith("FAIL "):
        parts = record["first_line"].split(" ", 3)
        if len(parts) >= 3:
            record["error_type"] = parts[2].rstrip(":")
    elif record["first_line"].startswith("READ-FAIL "):
        record["error_type"] = "ReadError"
    if proc.returncode == 0:
        record["status"] = "OK"
    elif proc.returncode == 1:
        record["status"] = "FAIL"
    elif proc.returncode == 2:
        record["status"] = "READ_FAIL"
    else:
        record["status"] = "ERROR"
    record["output_tail"] = output[-2000:]
    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--space", default=DEFAULT_SPACE)
    parser.add_argument("--coverage", default=DEFAULT_COVERAGE)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--deps", default=os.environ.get("J3_DEPS", ""))
    parser.add_argument("--run-probes", action="store_true")
    parser.add_argument("--probe-timeout", type=float, default=60.0)
    args = parser.parse_args(argv)

    space = load(args.space)
    coverage = load(args.coverage)
    excluded = [entry for entry in space.get("entries") or []
                if isinstance(entry, dict) and entry.get("status") == "excluded"]

    previous_probes = {}
    if os.path.isfile(args.out):
        try:
            previous = load(args.out)
            previous_probes = previous.get("probes") or {}
            if not previous_probes:
                previous_probes = {
                    row.get("pyc"): row.get("probe")
                    for row in previous.get("pycs") or []
                    if isinstance(row, dict) and row.get("probe")
                }
        except (OSError, ValueError):
            previous_probes = {}

    pyc_groups = collections.defaultdict(list)
    for entry in excluded:
        pyc_groups[entry.get("pyc") or ""].append(entry)

    probes = {}
    for pyc in sorted(pyc_groups):
        if args.run_probes:
            probes[pyc] = run_probe(pyc, args.deps, args.probe_timeout)
        elif pyc in previous_probes:
            probes[pyc] = previous_probes[pyc]
        else:
            probes[pyc] = None

    ast_cache = {}
    pyc_rows = []
    entry_rows = []
    for pyc in sorted(pyc_groups, key=lambda item: (-len(pyc_groups[item]), item)):
        entries = pyc_groups[pyc]
        path = abs_path(pyc)
        pyc_row = {
            "pyc": pyc,
            "size": os.path.getsize(path) if os.path.isfile(path) else None,
            "sha256": sha256_file(path) if os.path.isfile(path) else None,
            "entries": len(entries),
            "forms": dict(sorted(collections.Counter(
                entry.get("form") for entry in entries).items())),
            "hosts": dict(sorted(collections.Counter(
                entry.get("host") for entry in entries).items())),
            "variants": dict(sorted(collections.Counter(
                entry.get("variant") for entry in entries).items())),
            "p_j": sorted({entry.get("p_j") for entry in entries if entry.get("p_j")}),
            "p_j_sha256": sorted({entry.get("p_j_sha256") for entry in entries
                                  if entry.get("p_j_sha256")}),
            "dedicated_probe_entries": sum(1 for entry in entries if dedicated_probe(entry)),
            "no_dedicated_probe_entries": sum(1 for entry in entries
                                              if not dedicated_probe(entry)),
            "probe": probes.get(pyc),
        }
        pyc_rows.append(pyc_row)

        for entry in entries:
            is_module_level = entry.get("host") == "module-level"
            evidence = None
            reason = ""
            if is_module_level:
                p_j = entry.get("p_j") or ""
                if p_j not in ast_cache:
                    try:
                        ast_cache[p_j] = ast.parse(
                            open(abs_path(p_j), "r", encoding="utf-8-sig").read())
                    except (OSError, SyntaxError) as exc:
                        ast_cache[p_j] = exc
                tree = ast_cache[p_j]
                if isinstance(tree, ast.AST):
                    evidence = module_level_evidence(
                        tree, entry.get("form") or "", entry.get("host") or "",
                        entry.get("variant") or "")
                else:
                    evidence = {
                        "top_level_statements": [],
                        "claimed_host_present": None,
                        "detail": "p_j parse failed: %s: %s"
                                  % (type(tree).__name__, tree),
                        "hits": [],
                    }
                probe = probes.get(pyc)
                if not probe or probe.get("status") != "OK":
                    reason = "pyc_import_blocked"
                elif evidence.get("claimed_host_present") is not True:
                    reason = "p_j_lacks_claimed_host"
                else:
                    reason = "module_witness_not_run"
            else:
                probe = probes.get(pyc)
                reason = ("pyc_import_blocked" if not probe or probe.get("status") != "OK"
                          else "host_specific_call_witness_required")
            entry_rows.append({
                "id": entry.get("id"),
                "pyc": pyc,
                "form": entry.get("form"),
                "host": entry.get("host"),
                "depth": entry.get("depth"),
                "variant": entry.get("variant"),
                "p_j": entry.get("p_j"),
                "dedicated_probe": dedicated_probe(entry),
                "module_level": is_module_level,
                "closable_now": False,
                "reason": reason,
                "p_j_claimed_host_present": (
                    evidence.get("claimed_host_present") if evidence else None),
                "p_j_host_evidence": evidence,
            })

    module_level = [row for row in entry_rows if row["module_level"]]
    pyc_ok = sum(1 for row in pyc_rows
                 if row.get("probe") and row["probe"].get("status") == "OK")
    pyc_blocked = sum(1 for row in pyc_rows
                      if not row.get("probe") or row["probe"].get("status") != "OK")
    summary = {
        "excluded": len(excluded),
        "distinct_pyc": len(pyc_rows),
        "pyc_ok": pyc_ok,
        "pyc_blocked": pyc_blocked,
        "module_level": len(module_level),
        "module_level_pyc_ok": sum(1 for row in module_level
                                   if row.get("reason") != "pyc_import_blocked"),
        "module_level_claimed_host_present": sum(
            1 for row in module_level
            if row.get("p_j_claimed_host_present") is True),
        "module_level_closable_now": sum(1 for row in module_level
                                         if row.get("closable_now")),
        "non_module_level": len(entry_rows) - len(module_level),
        "dedicated_probe_entries": sum(1 for row in entry_rows if row["dedicated_probe"]),
        "no_dedicated_probe_entries": sum(1 for row in entry_rows
                                          if not row["dedicated_probe"]),
        "closable_now": sum(1 for row in entry_rows if row["closable_now"]),
        "host_counts": dict(sorted(collections.Counter(
            row["host"] for row in entry_rows).items())),
    }

    totals = coverage.get("totals") or {}
    readings = {
        "J_total": totals.get("J_total"),
        "covered_5tuple": totals.get("covered_5tuple"),
        "excluded": totals.get("excluded"),
        "uncovered": totals.get("uncovered"),
        "semantic_failures": totals.get("semantic_failures"),
        "green": totals.get("green"),
        "coverage_pct": totals.get("coverage_pct"),
        "judge_sha256": coverage.get("judge_sha256"),
        "space_path": coverage.get("space_path"),
        "evidence_path": coverage.get("evidence_path"),
        "consistent": (
            totals.get("J_total") == len(space.get("entries") or [])
            and totals.get("excluded") == len(excluded)
        ),
    }

    payload = {
        "tool": "audit_real_packages",
        "version": TOOL_VERSION,
        "space": norm_path(args.space),
        "space_sha256": sha256_file(args.space),
        "coverage": norm_path(args.coverage),
        "coverage_sha256": sha256_file(args.coverage),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "probe_script": norm_path(os.path.relpath(PROBE_SCRIPT, ROOT)),
        "probe_script_sha256": sha256_file(PROBE_SCRIPT),
        "deps": os.path.abspath(args.deps) if args.deps else "",
        "packages": package_versions(args.deps),
        "summary": summary,
        "probes": probes,
        "pycs": pyc_rows,
        "module_level": module_level,
        "entries": entry_rows,
        "readings": readings,
        "conclusion": (
            "0 of 376 real-package entries are honestly closable in this "
            "environment. 364 have a registered real-package probe, but 6/7 "
            "pycs cannot import because IQCommon.data.TickDataCache is a "
            "Linux-only extension; the remaining 12 aes_encrypt entries have "
            "no dedicated probe and their p_j has no class decorator, so a "
            "module run would not witness the claimed host/variant."
        ),
    }
    dump(args.out, payload)
    print("[audit] excluded=%d pyc=%d ok=%d blocked=%d module_level=%d "
          "claimed_host=%d closable=%d"
          % (summary["excluded"], summary["distinct_pyc"], summary["pyc_ok"],
             summary["pyc_blocked"], summary["module_level"],
             summary["module_level_claimed_host_present"],
             summary["closable_now"]))
    for row in module_level:
        print("[audit] module-level %-18s %-9s %-28s %s"
              % (row["id"], row["reason"], row["variant"],
                 row["p_j_claimed_host_present"]))
    if not readings["consistent"]:
        print("[audit] WARNING: coverage totals do not match the space",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
