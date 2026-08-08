#!/usr/bin/env python3
"""R61: Update pyc_index.json with new statuses"""
import json
from pathlib import Path
from datetime import datetime

index_path = Path("pyc_index.json")
with open(index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

updates = {
    "live_future_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
    "option_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
}

updated = 0
for entry in index:
    p = entry["path"]
    for name, updates_dict in updates.items():
        if name in p:
            for k, v in updates_dict.items():
                entry[k] = v
            updated += 1
            print(f"Updated: {p}")

with open(index_path, 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

print(f"\nTotal updated: {updated}")

# Calculate new stats
total = len(index)
full_ok = sum(1 for e in index if e["decompile_status"] == "ok" and e["bytecode_match_rate"] == 1.0)
partial = sum(1 for e in index if e["decompile_status"] == "ok" and e["bytecode_match_rate"] < 1.0)
fail = sum(1 for e in index if e["decompile_status"] != "ok")
print(f"Stats: Total={total}, Full OK={full_ok}, Partial={partial}, Fail={fail}")
print(f"Success rate: {full_ok/total*100:.2f}%")
