#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Insert zero-arg entry wrappers into _build_probes.py (one-shot helper)."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAP = os.path.dirname(HERE)
path = os.path.join(GAP, "_build_probes.py")
src = open(path, encoding="utf-8").read()

DOC = '"""Zero-arg defaulted entry (J input_model.calls driver)."""'

ADDS = {
    "pj_v2if_02": f'def pj_entry_default():\n    {DOC}\n    return pj_entry(2)\n\n',
    "pj_elif_01": f'def pj_entry_default():\n    {DOC}\n    return pj_entry(1), pj_entry_nested(2)\n\n',
    "pj_elif_02": f'def pj_entry_default():\n    {DOC}\n    return pj_entry(2), pj_entry_raise(1)\n\n',
    "pj_with_01": (f'def pj_entry_default():\n    {DOC}\n'
                   '    return (pj_entry(1, 2), pj_entry_three(1, 2, 3),\n'
                   '            pj_entry_nested(1, 2), pj_entry_module_level(1, 2))\n\n'),
    "pj_with_02": (f'async def pj_entry_default():\n    {DOC}\n'
                   '    return await pj_entry(1, 2), await pj_entry_await(1, 2)\n\n'),
    "pj_patchpat_01": (f'def pj_entry_default():\n    {DOC}\n'
                       '    t = Target()\n'
                       '    return pj_entry(t, t, t.method), pj_entry_attr(t), '
                       'pj_entry_compare(t, t)\n\n'),
    "pj_patchpat_02": (f'def pj_entry_default():\n    {DOC}\n'
                       '    return pj_entry(Widget(), {}), pj_entry_nested(Widget())\n\n'),
}

for name, add in ADDS.items():
    key = 'SOURCES["%s"] = ' % name
    start = src.index(key)
    nxt = src.find('SOURCES["', start + len(key))
    if nxt < 0:
        nxt = len(src)
    block = src[start:nxt]
    if "pj_entry_default" in block:
        continue
    idx = block.rindex("def main():")
    block = block[:idx] + add + block[idx:]
    src = src[:start] + block + src[nxt:]

with open(path, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(src)
print("patched", len(ADDS))
