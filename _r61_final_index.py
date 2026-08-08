#!/usr/bin/env python3
"""R61: Only update the 3 files I actually fixed, don't touch anything else"""
import json
from pathlib import Path

index_path = Path("pyc_index.json")
with open(index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

my_fixes = {
    "live_future_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
    "option_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
    "live_option_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
}

updated = 0
for entry in index:
    p = entry["path"]
    for name, updates_dict in my_fixes.items():
        if name in p:
            for k, v in updates_dict.items():
                entry[k] = v
            updated += 1
            print(f"Updated: {p}")

with open(index_path, 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print(f"\nTotal updated: {updated}")

total = len(index)
full_ok = sum(1 for e in index if e["decompile_status"] == "ok" and e["bytecode_match_rate"] == 1.0)
partial_ok = sum(1 for e in index if e["decompile_status"] == "ok" and e["bytecode_match_rate"] < 1.0)
fail = sum(1 for e in index if e["decompile_status"] != "ok")
all_ok = sum(1 for e in index if e["decompile_status"] == "ok")
print(f"Stats: Total={total}, AllOK={all_ok}, FullOK={full_ok}, PartialOK={partial_ok}, Fail={fail}")
