#!/usr/bin/env python3
"""R61: Update pyc_index.json with correct statuses"""
import json
from pathlib import Path

index_path = Path("pyc_index.json")
with open(index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

# Files that were incorrectly marked as OK in the index (pre-existing failures)
pre_existing_failures = {
    "IQCommon/util/pycompatibility.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.8333},
    "IQCommon/util/request_utils.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.75},
    "IQData/utils/pycompatibility.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.8333},
    "IQEngine/data/merger_storage.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.8571},
    "IQEngine/plugins/plugin_system_risk_calculation/risk_calculation.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.9655},
    "IQEngine/utils/pycompatibility.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.8333},
    "fly/common/op_station.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.9091},
    "fly/dumpload/load_algo.pyc": {"decompile_status": "partial", "bytecode_match_rate": 0.5},
}

# Files that my changes fixed
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
            print(f"Fixed: {p}")
    for name, updates_dict in pre_existing_failures.items():
        if name in p:
            for k, v in updates_dict.items():
                entry[k] = v
            entry["last_tested_round"] = 61
            updated += 1
            print(f"Corrected (pre-existing failure): {p}")

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
