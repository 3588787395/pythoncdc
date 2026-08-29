# -*- coding: utf-8 -*-
"""Round 04: 量化 G1(yield 丢失) 影响面 — 扫描全部 mismatch 函数的原始字节码含 YIELD_VALUE。"""
import json, sys, os, marshal, types, dis
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

NOISE = {'RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG', 'PRECALL', 'COPY_FREE_VARS', 'MAKE_CELL'}

reg = json.load(open(r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_03\repair_engineer\regress_000.json", encoding="utf-8"))


def find_by_name(top, name):
    if (top.co_name or '<module>') == name:
        return top
    for c in top.co_consts:
        if isinstance(c, types.CodeType):
            r = find_by_name(c, name)
            if r:
                return r
    return None


def load_code(p):
    with open(p, 'rb') as f:
        f.read(16)
        return marshal.load(f)


yield_hits = []
cache = {}
for rec in reg["files"]:
    path = rec["path"]
    mism = rec.get("mismatches", [])
    if not mism or not os.path.exists(path):
        continue
    if path not in cache:
        try:
            cache[path] = load_code(path)
        except Exception:
            cache[path] = None
    top = cache[path]
    if top is None:
        continue
    for m in mism:
        nm = m.get("name")
        co = find_by_name(top, nm) if nm else None
        if co is None:
            continue
        ops = {i.opname for i in dis.get_instructions(co)}
        if 'YIELD_VALUE' in ops or 'GET_YIELD_FROM_STACK' in ops or co.co_flags & 0x20:
            yield_hits.append((path.split("site-packages/")[-1], nm))

print(f"=== G1 候选（mismatch 且原始代码为生成器/含 yield）: {len(yield_hits)} ===")
for p, nm in yield_hits:
    print(f"  {p} :: {nm}")
