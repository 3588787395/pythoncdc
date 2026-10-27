#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repair the three invalid probes that produced the 36 `c4_error` entries.

The historical pyc files load-fail in the *original* artifact, before any
decompiler code runs:

  test_repros/round4/c4_15_star_import.py  NameError: name 'path' is not defined
  test_repros/round2/c05_class_with.py     NameError: name '_CM' is not defined
  test_repros/round2/c01_class_assign.py   NameError: name 'B' is not defined

Those are corpus defects, not decompiler defects.  This tool writes minimal
repaired copies under `fresh/repaired_sources/`, compiles them to
`fresh/repaired_pyc/`, and rewrites only the affected entries into
`fresh/judgment_space_v3r.json`.  The historical probes under `test_repros/`
are never modified.

Run from the repository root:

    python -X utf8 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/repair_invalid_probes.py
"""

from __future__ import annotations

import hashlib
import json
import os
import py_compile
import sys

TOOL_VERSION = "1.0.0"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.getcwd())
FRESH = HERE

# Keyed by the historical *pyc* path used in the manifest.
TARGETS = {
    "test_repros/round4/c4_15_star_import.pyc": "c4_15_star_import.py",
    "test_repros/round2/c05_class_with.pyc": "c05_class_with.py",
    "test_repros/round2/c01_class_assign.pyc": "c01_class_assign.py",
}

ERROR_EVIDENCE = {
    "c4_15_star_import.py": {
        "phase": "load",
        "type": "NameError",
        "message": "name 'path' is not defined",
        "cause": "`from os.path import *` does not bind the module name `path`, "
                 "but the module body and e01_use() read `path`.",
        "fix": "add `from os import path` before the star import; all original "
               "star-import and `path` uses are preserved.",
    },
    "c05_class_with.py": {
        "phase": "load",
        "type": "NameError",
        "message": "name '_CM' is not defined",
        "cause": "class-body `with _CM()` executes at class creation time and "
                 "the probe never defines `_CM`.",
        "fix": "add a minimal `_CM` context-manager class before `CWith`; the "
               "class-level with forms and nesting are unchanged.",
    },
    "c01_class_assign.py": {
        "phase": "load",
        "type": "NameError",
        "message": "name 'B' is not defined",
        "cause": "`(lambda v: v * B)(2)` runs inside the class body; class-body "
                 "names are not closure variables, so `B` is unbound.",
        "fix": "bind the class-body value as a default: "
               "`(lambda v, B=B: v * B)(2)`; the assignment form is unchanged.",
    },
}


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path: str) -> dict:
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def write_json(path: str, payload: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def repair_source(name: str, text: str) -> str:
    if name == "c4_15_star_import.py":
        if "from os import path" not in text.splitlines()[:3]:
            return "from os import path\n" + text
        return text
    if name == "c05_class_with.py":
        marker = '"""c05: class-level with."""'
        block = (
            marker + "\n"
            "class _CM:\n"
            "    def __enter__(self):\n"
            "        return self\n"
            "    def __exit__(self, *exc):\n"
            "        return False\n"
        )
        if marker not in text:
            raise SystemExit("unexpected c05_class_with.py header")
        return text.replace(marker + "\n", block, 1)
    if name == "c01_class_assign.py":
        old = "(lambda v: v * B)(2)"
        new = "(lambda v, B=B: v * B)(2)"
        if old not in text:
            raise SystemExit("unexpected c01_class_assign.py lambda")
        return text.replace(old, new, 1)
    raise SystemExit("unknown repair target: %s" % name)


def main() -> int:
    space_path = os.path.join(FRESH, "judgment_space_v3.json")
    space = load(space_path)
    entries = [entry for entry in space.get("entries", []) if isinstance(entry, dict)]
    by_pyc = {entry.get("pyc"): entry for entry in entries if entry.get("pyc")}

    src_dir = os.path.join(FRESH, "repaired_sources")
    pyc_dir = os.path.join(FRESH, "repaired_pyc")
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(pyc_dir, exist_ok=True)

    repaired = {}
    for original_pyc_rel, basename in TARGETS.items():
        original_rel = original_pyc_rel[:-1]
        original_abs = os.path.join(ROOT, original_rel)
        with open(original_abs, "r", encoding="utf-8-sig") as fh:
            original_text = fh.read()
        fixed_text = repair_source(basename, original_text)
        fixed_abs = os.path.join(src_dir, basename)
        with open(fixed_abs, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(fixed_text)
        fixed_pyc = os.path.join(pyc_dir, basename + "c")
        py_compile.compile(fixed_abs, cfile=fixed_pyc, doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        repaired[original_pyc_rel] = {
            "original_source": original_rel,
            "original_sha256": sha256_file(original_abs),
            "repaired_source": os.path.relpath(fixed_abs, ROOT).replace("\\", "/"),
            "repaired_source_sha256": sha256_file(fixed_abs),
            "repaired_pyc": os.path.relpath(fixed_pyc, ROOT).replace("\\", "/"),
            "repaired_pyc_sha256": sha256_file(fixed_pyc),
            "error": ERROR_EVIDENCE[basename],
        }

    updated = []
    changed_ids = []
    for entry in entries:
        item = dict(entry)
        rel = item.get("pyc")
        if rel in repaired:
            info = repaired[rel]
            src_rel = info["repaired_source"]
            pyc_rel = info["repaired_pyc"]
            src_abs = os.path.join(ROOT, src_rel)
            pyc_abs = os.path.join(ROOT, pyc_rel)
            with open(src_abs, "r", encoding="utf-8-sig", errors="replace") as fh:
                lines = len(fh.read().splitlines())
            item["p_j"] = src_rel
            item["p_j_sha256"] = sha256_file(src_abs)
            item["p_j_lines"] = lines
            item["pyc"] = pyc_rel
            item["pyc_sha256"] = sha256_file(pyc_abs)
            item["pyc_provenance"] = "repaired_invalid_probe"
            item["repair_note"] = (
                "J v3 fresh repair: the historical probe is load-invalid "
                "(%s: %s); a minimal executable copy is used for C1-C5. "
                "See fresh/REPAIR.md." % (info["error"]["type"], info["error"]["message"])
            )
            changed_ids.append(item.get("id"))
        updated.append(item)

    out_space = dict(space)
    out_space["entries"] = updated
    out_space["fresh_repair"] = {
        "tool": "repair_invalid_probes", "version": TOOL_VERSION,
        "base_manifest": "judgment_space_v3.json",
        "repaired_files": repaired,
        "changed_entries": len(changed_ids),
    }
    write_json(os.path.join(FRESH, "judgment_space_v3r.json"), out_space)

    repair_entries = [entry for entry in updated if entry.get("id") in set(changed_ids)]
    repair_space = dict(space)
    repair_space["entries"] = repair_entries
    write_json(os.path.join(FRESH, "repair_manifest.json"), repair_space)

    report = {
        "tool": "repair_invalid_probes", "version": TOOL_VERSION,
        "base_manifest": "judgment_space_v3.json",
        "out_manifest": "judgment_space_v3r.json",
        "repair_manifest": "repair_manifest.json",
        "entries_changed": len(changed_ids),
        "changed_ids": changed_ids,
        "repaired_files": repaired,
    }
    write_json(os.path.join(FRESH, "REPAIR_REPORT.json"), report)

    print("[repair] files=%d entries=%d" % (len(repaired), len(changed_ids)))
    for rel, info in repaired.items():
        print("[repair] %-46s %s -> %s" % (rel, info["error"]["type"],
                                           info["repaired_pyc"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
