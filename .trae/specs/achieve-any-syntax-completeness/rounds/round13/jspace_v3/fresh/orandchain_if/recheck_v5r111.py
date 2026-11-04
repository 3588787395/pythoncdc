#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rr-v5r111 并发超时抖动案单案复跑归因。

1556 三分片闸门在本机 2 核上并行时，少数 site-packages 大 pyc 的反编译
子进程超过 --timeout 20，未产出 c4（NO_C4）。本脚本对这些案逐案用
--offset <global_index> --limit 1 单独复跑（无并发），证明 verdict 与
v5r110 基线逐字一致，方可按纪律登记为非回归。

只读判官/语料/比较器，不修改任何 verdict，不回填分片文件。
用法：D:/Python/python.exe recheck_v5r111.py
"""
import json
import os
import subprocess

ROOT = "F:/Downloads/pythoncdc-main"
F = ROOT + "/.trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh"
E = F + "/orandchain_if"
SPACE = (".trae/specs/achieve-any-syntax-completeness/rounds/round13/"
         "jspace_v3/fresh/judgment_space_v3m_applied.json")
PY = "D:/Python/python.exe"
PROD = F + "/semantic_products_v5r111/r4_recheck_auto"


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def main():
    space = load(F + "/judgment_space_v3m_applied.json")
    ids = [e.get("id") for e in space["entries"]]
    index = {e: i for i, e in enumerate(ids) if isinstance(e, str)}
    cases = []
    for shard in range(3):
        new = load(F + "/semantic_shard%d_v5r111.json" % shard)
        base = load(F + "/semantic_shard%d_v5r110.json" % shard)
        bm = {r["entry_id"]: r.get("c4", {}).get("verdict", "NO_C4")
              for r in base["records"]}
        for r in new["records"]:
            if r.get("c4", {}).get("verdict", "NO_C4") == "NO_C4":
                cases.append({"shard": shard, "entry_id": r["entry_id"],
                              "base": bm.get(r["entry_id"]),
                              "index": index.get(r["entry_id"]),
                              "note": str(r.get("note", ""))[:120]})
    print("NO_C4 cases:", len(cases))
    rows = []
    for c in cases:
        if c["index"] is None:
            raise SystemExit("cannot locate index for %s" % c["entry_id"])
        name = c["entry_id"].replace("/", "_")
        out_json = E + "/recheck_auto_%s.json" % name
        rep_json = E + "/recheck_auto_%s_report.json" % name
        cmd = [PY, "-X", "utf8", "tools/completeness/semantic_runner.py",
               "--space", SPACE, "--out", out_json, "--report", rep_json,
               "--product-dir", PROD + "/" + name,
               "--offset", str(c["index"]), "--limit", "1",
               "--timeout", "20"]
        subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        doc = load(out_json)
        verdict = doc["records"][0].get("c4", {}).get("verdict", "NO_C4")
        row = dict(c)
        row["recheck"] = verdict
        row["match_base"] = (verdict == c["base"])
        rows.append(row)
        print("  %-20s shard%d base=%-8s recheck=%-8s match=%s" %
              (c["entry_id"], c["shard"], c["base"], verdict,
               row["match_base"]))
    path = E + "/recheck_v5r111_result.json"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"n": len(rows),
                   "all_match": all(r["match_base"] for r in rows),
                   "rows": rows}, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("all_match:", all(r["match_base"] for r in rows), "->", path)


if __name__ == "__main__":
    main()
