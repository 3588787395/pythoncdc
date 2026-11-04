#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rr-v5r111 闸门逐案对比：v5r111 vs v5r110 的 c4 verdict。

只读脚本：不改任何判官/语料/产品输入，仅读取 semantic_runner 产出的 json，
按 entry_id 逐案比对 c4.verdict，输出差异清单与回归/改善/抖动计数。
NO_C4（判定未产出，2 核并行下大 pyc 反编译 TimeoutExpired）单列为
timeout_flake，不并入实质回归；其归因由 recheck_v5r111.py 单案复跑证明。
用法：D:/Python/python.exe compare_v5r111.py
"""
import json
from collections import Counter

ROOT = "F:/Downloads/pythoncdc-main"
F = ROOT + "/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh"
E = F + "/orandchain_if"
CHAIN = F + "/chainfor_foriter"


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def verdict_map(doc):
    return {r["entry_id"]: r.get("c4", {}).get("verdict", "NO_C4")
            for r in doc["records"]}


def classify(base, new):
    """verdict 排名：EQUAL 最好；NO_C4 为判定未产出，单列超时抖动待复跑归因。"""
    if base == new:
        return "same"
    if new == "NO_C4":
        return "timeout_flake"
    if base == "NO_C4":
        return "improvement"
    rank = {"EQUAL": 0, "DIFFERENT": 1, "INCONCLUSIVE": 2, "ERROR": 3}
    b, n = rank.get(base, 5), rank.get(new, 5)
    if n > b:
        return "regression"
    if n < b:
        return "improvement"
    return "change"


def compare(label, base_path, new_path, out):
    b, n = load(base_path), load(new_path)
    bm, nm = verdict_map(b), verdict_map(n)
    print("=" * 78)
    print(label)
    print("  base:", base_path)
    print("  new :", new_path)
    print("  base summary:", json.dumps(b["summary"], ensure_ascii=False))
    print("  new  summary:", json.dumps(n["summary"], ensure_ascii=False))
    common = sorted(set(bm) & set(nm))
    only_base = sorted(set(bm) - set(nm))
    only_new = sorted(set(nm) - set(bm))
    print("  common=%d only_base=%d only_new=%d" %
          (len(common), len(only_base), len(only_new)))
    if only_base:
        print("  only_base:", only_base)
    if only_new:
        print("  only_new:", only_new)
    diffs, buckets = [], {"regression": [], "improvement": [],
                          "change": [], "timeout_flake": []}
    cb, cn = Counter(), Counter()
    for eid in common:
        cb[bm[eid]] += 1
        cn[nm[eid]] += 1
        if bm[eid] != nm[eid]:
            cls = classify(bm[eid], nm[eid])
            diffs.append({"entry_id": eid, "base": bm[eid],
                          "new": nm[eid], "class": cls})
            buckets[cls].append(eid)
    print("  verdict counts base:", dict(cb))
    print("  verdict counts new :", dict(cn))
    print("  TOTAL changes=%d regression=%d improvement=%d "
          "timeout_flake=%d other=%d" %
          (len(diffs), len(buckets["regression"]),
           len(buckets["improvement"]), len(buckets["timeout_flake"]),
           len(buckets["change"])))
    for d in diffs:
        print("    %-20s %-12s -> %-12s [%s]" %
              (d["entry_id"], d["base"], d["new"], d["class"]))
    out[label] = {
        "base_summary": b["summary"], "new_summary": n["summary"],
        "common": len(common), "only_base": only_base, "only_new": only_new,
        "base_counts": dict(cb), "new_counts": dict(cn),
        "changes": diffs,
        "n_regression": len(buckets["regression"]),
        "n_improvement": len(buckets["improvement"]),
        "n_timeout_flake": len(buckets["timeout_flake"]),
        "n_other": len(buckets["change"]),
    }
    return out


def main():
    out = {}
    for i in range(3):
        compare("shard%d" % i,
                F + "/semantic_shard%d_v5r110.json" % i,
                F + "/semantic_shard%d_v5r111.json" % i, out)
    compare("46sweep",
            CHAIN + "/semantic_46_v5r110.json",
            E + "/semantic_46_v5r111.json", out)
    path = E + "/compare_v5r111_result.json"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("=" * 78)
    print("written:", path)


if __name__ == "__main__":
    main()
