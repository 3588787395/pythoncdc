#!/usr/bin/env python3
"""Debug: compare try-except-finally vs try-except;try-except."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.cfg import build_cfg
from core.cfg.dominator_analyzer import DominatorAnalyzer
from core.cfg.region_analyzer import RegionAnalyzer

# Case 1: try-except-finally
code1 = compile('try:\n    x = 1\nexcept:\n    y = 2\nfinally:\n    z = 3', '<tef>', 'exec')
cfg1 = build_cfg(code1)
print("=== try-except-finally ===")
print("Raw exception_table:")
for e in cfg1.exception_table:
    print(f"  start={e.get('start')} end={e.get('end')} target={e.get('target')} depth={e.get('depth')}")

dom1 = DominatorAnalyzer(cfg1)
dom1.analyze()
a1 = RegionAnalyzer(cfg1, dom1)
hi1 = a1._parse_exception_table()
print("Parsed handler_infos:")
for info in hi1:
    print(f"  try=[{info['try_start']},{info['try_end']}) handler={info['handler_start']} type={info.get('handler_type')}")

# Check: does finally's raw entry cover except handler entry?
fin_handler = hi1[1]['handler_start']  # 36
exc_handler = hi1[0]['handler_start']  # 10
fin_raw = [e for e in cfg1.exception_table if e.get('target') == fin_handler]
print(f"finally handler={fin_handler}, except handler={exc_handler}")
for e in fin_raw:
    s, en = e.get('start',0), e.get('end',0)
    covers = s <= exc_handler < en
    print(f"  fin entry [{s},{en}) covers exc_handler {exc_handler}? {covers}")

# Case 2: try-except; try-except (like IQCommon pattern)
code2 = compile('try:\n    x = 1\nexcept:\n    y = 2\ntry:\n    z = 3\nexcept:\n    w = 4', '<te;te>', 'exec')
cfg2 = build_cfg(code2)
print("\n=== try-except; try-except ===")
print("Raw exception_table:")
for e in cfg2.exception_table:
    print(f"  start={e.get('start')} end={e.get('end')} target={e.get('target')} depth={e.get('depth')}")

dom2 = DominatorAnalyzer(cfg2)
dom2.analyze()
a2 = RegionAnalyzer(cfg2, dom2)
hi2 = a2._parse_exception_table()
print("Parsed handler_infos:")
for info in hi2:
    print(f"  try=[{info['try_start']},{info['try_end']}) handler={info['handler_start']} type={info.get('handler_type')}")

# Check both handlers
for i, info in enumerate(hi2):
    h = info['handler_start']
    raw = [e for e in cfg2.exception_table if e.get('target') == h]
    for j, other in enumerate(hi2):
        if i == j:
            continue
        oh = other['handler_start']
        for e in raw:
            s, en = e.get('start',0), e.get('end',0)
            covers = s <= oh < en
            print(f"  handler {h} entry [{s},{en}) covers handler {oh}? {covers}")
