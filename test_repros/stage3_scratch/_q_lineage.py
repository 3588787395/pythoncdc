# -*- coding: utf-8 -*-
"""List per-version added J entry ids (and pyc paths) across the stage-3
jspace lineage, plus each version's entry count."""
import json
import sys

base = "test_repros/stage3_scratch/"
files = [
    ("r9", base + "judgment_space_r9_rebaselined.json"),
    ("v1", base + "judgment_space_stage3_b1_v1.json"),
    ("v2", base + "judgment_space_stage3_b1_v2.json"),
    ("v3", base + "judgment_space_stage3_b1_v3.json"),
    ("v4", base + "judgment_space_stage3_b1_v4.json"),
]
prev = {}
for tag, path in files:
    doc = json.load(open(path, encoding="utf-8-sig"))
    entries = doc.get("entries") or doc.get("jspace") or doc
    if isinstance(entries, dict):
        entries = entries.get("entries", [])
    cur = {}
    for e in entries:
        cur[e.get("id") or e.get("entry_id")] = (e.get("pyc") or e.get("pyc_path")
                                                 or e.get("path") or "")
    added = {k: v for k, v in cur.items() if k not in prev}
    print(f"== {tag}: {len(cur)} entries (+{len(added)}) ==")
    for k in sorted(added):
        print(f"   {k}  {added[k]}")
    prev = cur
