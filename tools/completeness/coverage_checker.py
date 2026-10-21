#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""判定空间覆盖检查器 / Judgment-space coverage checker.

输入：
  * 判定空间清单（`judgment_space.json`，由 `tools/completeness/jspace_generator.py` 生成）
  * 已覆盖证据索引（`rec1_probes_*.json` 探针 stamp JSON，递归扫描）

输出：
  * 覆盖统计（逐形态族 + 总计）与**未覆盖单元清单**
  * Markdown 报告（--out）与 JSON 报告（--json）

判定口径（**唯一、可复算**）：
  条目 covered  ⟺ 其 `required_evidence[]` 中存在一条 `kind == "probe"`，
  且该项的 `pyc` 归一化后**命中证据索引**。路径归一化按下列顺序尝试：
    1) 原样（仓根相对）；
    2) 前缀 `<attain-true-completeness 规范目录>/` + 原样（stamp 内的规范相对路径）；
    3) 仅取 .pyc 基名做基名匹配（索引内基名唯一时生效）。
  未命中 ⇒ uncovered。

门禁语义：uncovered > 0 时**退出码 1**（除非 `--allow-uncovered`）。

用法：
    python -X utf8 tools/completeness/coverage_checker.py \
        --space rounds/round1/judgment_space.json \
        --evidence-root .trae/specs/attain-true-completeness/rounds \
        --out rounds/round1/COVERAGE_BASELINE.md \
        [--json rounds/round1/coverage_baseline.json] [--allow-uncovered] [--list-uncovered]
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import sys

SPEC_DIR = ".trae/specs/attain-true-completeness"
STAMP_GLOB = "rec1_probes_*.json"


def norm_path(p: str) -> str:
    p = (p or "").replace("\\", "/").strip()
    while p.startswith("./"):
        p = p[2:]
    return p


def candidates(p: str):
    """一个 `pyc` 字段的全部可能归一化形态（按尝试顺序）。"""
    p = norm_path(p)
    if not p:
        return []
    out = [p]
    if not p.startswith((".trae/", "site-packages/", "test_repros/")):
        out.append(SPEC_DIR + "/" + p)
    # 带 ":行号" 的代码站点引用（core/cfg/ast_converter.py:110）只取路径部分
    if ":" in p and not p.lower().endswith(".pyc"):
        base = p.rsplit(":", 1)[0]
        out.append(base)
        if not base.startswith((".trae/", "site-packages/", "test_repros/")):
            out.append(SPEC_DIR + "/" + base)
    seen, res = set(), []
    for x in out:
        if x and x not in seen:
            seen.add(x)
            res.append(x)
    return res


def build_index(evidence_root: str):
    """扫描 rec1_probes_*.json，建立证据索引。

    返回 (index, meta)：
      index: {(rel_pyc, probe_name): {...}}
      meta:  {stamp_files, entries, paths, names}
    """
    index = {}
    rels = set()
    names = set()
    base = {}
    stamp_files = []
    if evidence_root and os.path.isdir(evidence_root):
        files = sorted(glob.glob(os.path.join(evidence_root, "**", STAMP_GLOB), recursive=True))
    else:
        files = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8-sig", errors="replace") as fh:
                data = json.load(fh)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        stamp_files.append(os.path.relpath(f, evidence_root).replace("\\", "/"))
        for ent in data:
            if not isinstance(ent, dict):
                continue
            name = ent.get("name")
            rel = ent.get("pyc_src_rel")
            if not isinstance(name, str) or not isinstance(rel, str):
                continue
            rel = norm_path(rel)
            if not rel or rel.startswith("@"):
                continue
            if not rel.startswith((".trae/", "site-packages/", "test_repros/")):
                rel = SPEC_DIR + "/" + rel
            rels.add(rel)
            names.add(name)
            base.setdefault(os.path.basename(rel), set()).add(rel)
            key = (rel, name)
            rec = index.setdefault(key, {"rel": rel, "name": name, "stamps": [],
                                        "status": [], "units": []})
            s = os.path.relpath(f, evidence_root).replace("\\", "/")
            if s not in rec["stamps"]:
                rec["stamps"].append(s)
            rec["status"].append(ent.get("status"))
            rec["units"].append([ent.get("units_success"), ent.get("units_total")])
    meta = {"stamp_files": len(stamp_files), "entries": len(index),
            "paths": len(rels), "names": len(names),
            "basename_unique": sum(1 for v in base.values() if len(v) == 1)}
    return index, meta, base


def resolve(p: str, index, base_index):
    """把 `pyc` 字段解析为索引中的 (rel, name)；未命中返回 None。"""
    for c in candidates(p):
        for (rel, name) in index:
            if rel == c:
                return (rel, name)
    bn = os.path.basename(norm_path(p))
    if bn:
        cands = base_index.get(bn)
        if cands and len(cands) == 1:
            rel = next(iter(cands))
            for (r, n) in index:
                if r == rel:
                    return (rel, n)
    return None


def load_space(path: str):
    with open(path, "r", encoding="utf-8-sig") as fh:
        space = json.load(fh)
    if not isinstance(space, dict):
        raise ValueError("judgment space manifest must be a JSON object")
    entries = space.get("entries")
    if not isinstance(entries, list):
        raise ValueError("judgment space manifest has no 'entries' list")
    return space


def check(space, index, base_index):
    rows = []
    per_fam = collections.defaultdict(lambda: collections.Counter())
    mismatch = []
    for i, e in enumerate(entries_of(space)):
        if not isinstance(e, dict):
            continue
        eid = e.get("id") or ("#%d" % i)
        fam = e.get("form") or "?"
        declared = e.get("status")
        ev = e.get("required_evidence")
        witness = None
        if isinstance(ev, list):
            for item in ev:
                if not isinstance(item, dict):
                    continue
                if item.get("kind") not in (None, "probe"):
                    continue
                p = item.get("pyc")
                if not isinstance(p, str):
                    continue
                witness = resolve(p, index, base_index)
                if witness:
                    break
        status = "covered" if witness else "uncovered"
        per_fam[fam][status] += 1
        per_fam[fam]["total"] += 1
        if declared and declared != status:
            mismatch.append({"id": eid, "declared": declared, "computed": status})
        rows.append({
            "id": eid, "form": fam, "host": e.get("host"), "depth": e.get("depth"),
            "variant": e.get("variant"), "row": e.get("row"),
            "status": status, "declared_status": declared,
            "witness_pyc": witness[0] if witness else None,
            "witness_name": witness[1] if witness else None,
            "source": e.get("source"),
            "required_evidence": ev if isinstance(ev, list) else [],
        })
    return rows, per_fam, mismatch


def entries_of(space):
    return space.get("entries") or []


def write_json(path, payload):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


def write_md(path, payload, rows, per_fam, mismatch, meta, space):
    d = os.path.dirname(os.path.abspath(path))
    if d:
        os.makedirs(d, exist_ok=True)
    t = payload["totals"]
    L = []
    A = L.append
    A("# 判定空间覆盖基线（Coverage Baseline）— attack-completeness-claims / Task 1")
    A("")
    A("> 工具：`tools/completeness/coverage_checker.py`；判定空间：`%s`。" % payload["space_path"])
    A("> 证据索引根：`%s`（扫描到 %d 份 `%s` stamp，%d 条探针记录，%d 个探针路径）。"
      % (payload["evidence_root"], meta["stamp_files"], STAMP_GLOB, meta["entries"], meta["paths"]))
    A("> 覆盖口径：条目 `required_evidence[].pyc` 命中证据索引 ⇒ covered；否则 uncovered。")
    A("")
    A("## 0. 总读数")
    A("")
    A("| 项 | 值 |")
    A("|---|---|")
    A("| 判定空间条目总数 | **%d** |" % t["entries"])
    A("| covered（有专属见证探针） | **%d** |" % t["covered"])
    A("| uncovered（无专属见证探针） | **%d** |" % t["uncovered"])
    A("| 覆盖率 | %.2f%% |" % t["coverage_pct"])
    A("| 形态族数 | %d |" % t["families"])
    A("| 清单声明与实测状态不一致 | %d |" % t["status_mismatch"])
    A("")
    A("> **这就是本次攻击的首个读数**：上一规范以「完备 128 / 破口 0 / 零能力 0 = 100%%」结案，"
      "而按**判定空间口径**，当前仅 %d/%d 个单元有专属见证探针（%.2f%%），"
      "**%d 个单元无任何专属证据**。「100%%」是折叠口径的读数，不是判定空间口径的读数。"
      % (t["covered"], t["entries"], t["coverage_pct"], t["uncovered"]))
    A("")
    A("## 1. 逐形态族覆盖")
    A("")
    A("| form | row | 条目 | covered | uncovered | 覆盖率 |")
    A("|---|---|---|---|---|---|")
    for fam in sorted(per_fam):
        c = per_fam[fam]
        pct = (100.0 * c["covered"] / c["total"]) if c["total"] else 0.0
        row = ""
        for r in rows:
            if r["form"] == fam:
                row = r.get("row") or ""
                break
        A("| %s | %s | %d | %d | %d | %.2f%% |" % (fam, row, c["total"], c["covered"], c["uncovered"], pct))
    A("")
    worst = sorted(per_fam.items(), key=lambda kv: (-kv[1]["uncovered"], -kv[1]["total"]))[:10]
    A("### 1.1 最差形态族（uncovered 绝对数前 10）")
    A("")
    A("| form | 条目 | covered | uncovered |")
    A("|---|---|---|---|")
    for fam, c in worst:
        A("| %s | %d | %d | %d |" % (fam, c["total"], c["covered"], c["uncovered"]))
    A("")
    A("## 2. 未覆盖单元清单")
    A("")
    unc = [r for r in rows if r["status"] == "uncovered"]
    A("共 **%d** 条。`required_evidence.pyc` 列给出该单元所引用的**同族锚点探针**"
      "（仓内真实存在，但从未登记进 `rec1_probes_*.json` 证据索引）。" % len(unc))
    A("")
    A("| id | form | host | depth | variant | row | 锚点探针 |")
    A("|---|---|---|---|---|---|---|")
    for r in unc:
        ev = r["required_evidence"][0] if r["required_evidence"] else {}
        A("| %s | %s | %s | %s | %s | %s | `%s` |" % (
            r["id"], r["form"], r["host"], r["depth"], r["variant"], r["row"], ev.get("pyc", "")))
    A("")
    if mismatch:
        A("### 2.1 清单声明与实测不一致（须修清单）")
        A("")
        A("| id | 声明 | 实测 |")
        A("|---|---|---|")
        for m in mismatch[:50]:
            A("| %s | %s | %s |" % (m["id"], m["declared"], m["computed"]))
        A("")
    A("## 3. 复算方式")
    A("")
    A("```")
    A("python -X utf8 tools/completeness/coverage_checker.py \\")
    A("    --space %s \\" % payload["space_path"])
    A("    --evidence-root %s \\" % payload["evidence_root"])
    A("    --out %s --json %s" % (payload["out_path"], payload["json_path"]))
    A("```")
    A("")
    A("- 退出码：`uncovered > 0` ⇒ **1**（门禁不放行）；`--allow-uncovered` ⇒ 0。")
    A("- 索引构建：递归扫描 `--evidence-root` 下 `%s`；每条 stamp 的 `pyc_src_rel` 归一化为仓根相对路径"
      "（非 `.trae/`/`site-packages/`/`test_repros/` 开头的按规范目录前缀补齐）。" % STAMP_GLOB)
    A("- 路径匹配：原样 → 规范目录前缀补齐 → 仅取 .pyc 基名（索引内基名唯一时生效）。")
    A("")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L))
        fh.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description="判定空间覆盖检查器")
    ap.add_argument("--space", required=True, help="judgment_space.json 路径")
    ap.add_argument("--evidence-root", default=".trae/specs/attain-true-completeness/rounds",
                    help="探针 stamp JSON 根目录（递归扫描 rec1_probes_*.json）")
    ap.add_argument("--out", default="", help="Markdown 报告输出路径")
    ap.add_argument("--json", default="", help="JSON 报告输出路径")
    ap.add_argument("--allow-uncovered", action="store_true",
                    help="即使 uncovered > 0 也以 0 退出（默认门禁语义为退出码 1）")
    ap.add_argument("--list-uncovered", action="store_true", help="在标准输出列出未覆盖单元")
    args = ap.parse_args(argv)

    try:
        space = load_space(args.space)
    except Exception as exc:
        print("[coverage] ERROR: cannot load judgment space %s: %s" % (args.space, exc))
        return 2
    index, meta, base_index = build_index(args.evidence_root)
    rows, per_fam, mismatch = check(space, index, base_index)

    covered = sum(1 for r in rows if r["status"] == "covered")
    uncovered = sum(1 for r in rows if r["status"] == "uncovered")
    entries = len(rows)
    fam_rows = {}
    for r in rows:
        fam_rows.setdefault(r["form"], r.get("row"))
    payload = {
        "space_path": norm_path(args.space),
        "evidence_root": norm_path(args.evidence_root),
        "out_path": norm_path(args.out),
        "json_path": norm_path(args.json),
        "index": meta,
        "totals": {
            "entries": entries, "covered": covered, "uncovered": uncovered,
            "coverage_pct": (100.0 * covered / entries) if entries else 0.0,
            "families": len(per_fam), "status_mismatch": len(mismatch),
        },
        "per_family": {
            f: {"row": fam_rows.get(f), "total": c["total"], "covered": c["covered"],
                "uncovered": c["uncovered"],
                "coverage_pct": (100.0 * c["covered"] / c["total"]) if c["total"] else 0.0}
            for f, c in sorted(per_fam.items())
        },
        "status_mismatch": mismatch,
        "uncovered": [r for r in rows if r["status"] == "uncovered"],
        "rows": [{k: v for k, v in r.items() if k != "required_evidence"} for r in rows],
    }

    if args.out:
        write_md(args.out, payload, rows, per_fam, mismatch, meta, space)
    if args.json:
        write_json(args.json, payload)

    print("[coverage] entries=%d covered=%d uncovered=%d coverage=%.2f%% families=%d stamps=%d"
          % (entries, covered, uncovered, payload["totals"]["coverage_pct"],
             len(per_fam), meta["stamp_files"]))
    worst = sorted(per_fam.items(), key=lambda kv: (-kv[1]["uncovered"], -kv[1]["total"]))[:5]
    for f, c in worst:
        print("[coverage] worst family: %s uncovered=%d/%d" % (f, c["uncovered"], c["total"]))
    if args.list_uncovered:
        for r in payload["uncovered"]:
            print("[uncovered] %s %s | %s | %s | %s" % (r["id"], r["form"], r["host"], r["depth"], r["variant"]))
    if uncovered > 0 and not args.allow_uncovered:
        print("[coverage] GATE FAIL: uncovered=%d (use --allow-uncovered to bypass)" % uncovered)
        return 1
    if uncovered > 0:
        print("[coverage] GATE BYPASSED (--allow-uncovered): uncovered=%d" % uncovered)
        return 0
    print("[coverage] GATE PASS: uncovered=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
