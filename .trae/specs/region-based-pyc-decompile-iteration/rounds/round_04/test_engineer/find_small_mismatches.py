# -*- coding: utf-8 -*-
"""Round 04: 找出全部 mismatch 函数中字节码最小的（简单形状优先）。"""
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


rows = []
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
        fd = m.get("first_diff")
        if not fd or fd.get("index") is None:
            continue  # 顶层字节码一致，差异在嵌套 code object
        co = find_by_name(top, nm) if nm else None
        if co is None:
            continue
        n = sum(1 for i in dis.get_instructions(co) if i.opname not in NOISE)
        rows.append((n, path.split("site-packages/")[-1], nm, fd.get("index")))

rows.sort()
print(f"总 mismatch 函数: {len(rows)}")
print("\n=== 最小的 30 个 ===")
for n, p, nm, fi in rows[:30]:
    print(f"  {n:4d} instrs  fd@{fi:<4d}  {p} :: {nm}")
