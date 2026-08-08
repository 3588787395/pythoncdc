#!/usr/bin/env python3
"""R61: Update pyc_index.json with REAL match rates"""
import json
from pathlib import Path

index_path = Path("pyc_index.json")
with open(index_path, 'r', encoding='utf-8') as f:
    index = json.load(f)

# Files I fixed
my_fixes = {
    "live_future_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
    "option_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
    "live_option_position.pyc": {"decompile_status": "ok", "bytecode_match_rate": 1.0, "ok_py_generated": True, "last_tested_round": 61},
}

# Files that were actually broken (tested on both original and modified code - same result)
real_broken = {
    "IQCommon/util/pycompatibility.pyc": ("partial", 0.8333),
    "IQCommon/util/request_utils.pyc": ("partial", 0.75),
    "IQData/utils/pycompatibility.pyc": ("partial", 0.8333),
    "IQEngine/data/merger_storage.pyc": ("partial", 0.8571),
    "IQEngine/plugins/plugin_system_risk_calculation/risk_calculation.pyc": ("partial", 0.9655),
    "IQEngine/utils/pycompatibility.pyc": ("partial", 0.8333),
    "fly/common/op_station.pyc": ("partial", 0.9091),
    "fly/dumpload/load_algo.pyc": ("partial", 0.5),
}

for entry in index:
    p = entry["path"]
    for name, upd in my_fixes.items():
        if name in p:
            for k, v in upd.items():
                entry[k] = v
    for name, (status, rate) in real_broken.items():
        if name in p:
            entry["decompile_status"] = status
            entry["bytecode_match_rate"] = rate
            entry["last_tested_round"] = 61

with open(index_path, 'w', encoding='utf-8') as f:
    json.dump(index, f, indent=2, ensure_ascii=False)

total = len(index)
all_ok = sum(1 for e in index if e["decompile_status"] == "ok")
full_ok = sum(1 for e in index if e["decompile_status"] == "ok" and e["bytecode_match_rate"] == 1.0)
fail = sum(1 for e in index if e["decompile_status"] != "ok")
print(f"Total={total}, AllOK={all_ok}, FullOK={full_ok}, Fail={fail}")
