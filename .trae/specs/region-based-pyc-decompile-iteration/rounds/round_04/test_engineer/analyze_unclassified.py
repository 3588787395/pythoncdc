# -*- coding: utf-8 -*-
"""Round 04: 分析未归类不匹配函数的分布，选出目标文件。"""
import json
from collections import Counter

imp = json.load(open(r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_04\test_engineer\impact_families.json", encoding="utf-8"))
unc = imp["unclassified_mismatch_funcs"]
files = Counter()
for item in unc:
    rel = item.split("::")[0]
    files[rel] += 1

print("=== 未归类函数按文件分布（Top 20）===")
for rel, n in files.most_common(20):
    print(f"  {n:3d}  {rel}")
print(f"\n总文件数: {len(files)}, 总函数数: {len(unc)}")

# 每文件总 mismatch 数（从 regress json）
reg = json.load(open(r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_03\repair_engineer\regress_000.json", encoding="utf-8"))
print("\n=== 按总 mismatch 数排序（Top 15，含已归类）===")
rows = []
for rec in reg["files"]:
    n = len(rec.get("mismatches", []))
    if n:
        rows.append((n, rec["path"].split("site-packages/")[-1]))
rows.sort(reverse=True)
for n, p in rows[:15]:
    print(f"  {n:3d}  {p}")
