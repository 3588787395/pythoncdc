# -*- coding: utf-8 -*-
"""Round 04: trade_live_broker.pyc mismatch 函数分析。"""
import json, sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

reg = json.load(open(r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_03\repair_engineer\regress_000.json", encoding="utf-8"))
for rec in reg["files"]:
    if "trade_live_broker" in rec["path"]:
        print(f"file: {rec['path']}, total={rec['total_functions']}, matched={rec['matched_functions']}")
        for m in rec["mismatches"]:
            fd = m.get("first_diff") or {}
            print(f"  {m['name']:45s} first_diff@{fd.get('index')} orig={fd.get('orig_op')} decomp={fd.get('decomp_op', fd.get('new_op'))}")
        break
