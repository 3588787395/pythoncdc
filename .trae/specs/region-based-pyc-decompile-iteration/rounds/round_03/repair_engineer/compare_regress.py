# -*- coding: utf-8 -*-
"""对比 Round 03 baseline 与回归结果。"""
import json

base = json.load(open(r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_03\baseline\batch_000.json", encoding="utf-8"))
reg = json.load(open(r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_03\repair_engineer\regress_000.json", encoding="utf-8"))


def norm(d):
    out = {}
    for v in d.get("files", []):
        out[v["path"]] = (v.get("status"), v.get("matched_functions", 0),
                          v.get("total_functions", 0))
    return out


b, r = norm(base), norm(reg)
flipped, improved, regressed = [], [], []
for k in sorted(set(b) | set(r)):
    if k not in b:
        print("NEW:", k, r[k]); continue
    if k not in r:
        print("MISSING:", k, b[k]); continue
    bs, bm, bt = b[k]
    rs, rm, rt = r[k]
    if bs != "ok" and rs == "ok":
        flipped.append((k, bs, rs, f"{bm}/{bt}->{rm}/{rt}"))
    elif rm > bm:
        improved.append((k, f"{bm}->{rm}/{rt}"))
    elif rm < bm:
        regressed.append((k, f"{bm}->{rm}/{rt}"))

print(f"\n=== 翻转 partial->ok ({len(flipped)}) ===")
for k, a, c, d in flipped:
    print(f"  {k}: {a}->{c} {d}")
print(f"\n=== 匹配数提升 ({len(improved)}) ===")
for k, d in improved:
    print(f"  {k}: {d}")
print(f"\n=== 匹配数回退 ({len(regressed)}) ===")
for k, d in regressed:
    print(f"  {k}: {d}")
