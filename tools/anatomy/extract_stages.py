"""区域归约算法解剖提取器（region-algorithm-decomposition / tasks 1.1、2.1）

只用标准库（ast/hashlib/json/re/pathlib/subprocess）。产出：
  docs/refactor/anatomy-evidence.json   原始证据（方法清单 / 阶段归属 / 重复矩阵）
  docs/refactor/region-anatomy.md       阶段解剖（生成，含生成时刻与 git HEAD）
  docs/refactor/dup-matrix.md           重复矩阵（生成，含三件套证据）

归类规则（design D1）：按方法体实际读写的标识符/被调函数名打分，而非方法名；
方法名前缀仅作 override 兜底。无法归类者进 Unclassified 桶。
"""

import ast
import hashlib
import json
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "docs" / "refactor"
WL_DIRS = ["core", "parsers", "bytecode", "utils"]
ENTRY_FILES = ["pycdc.py", "pycdas.py"]

STAGES = [
    ("S1", "CFG 构建", "BasicBlock/CFGBuilder", "BasicBlock 图 + 边集"),
    ("S2", "块语义标注", "BasicBlock -> BlockSemantics", "BlockRole 标注后的块集"),
    ("S3", "区域识别", "BlockSemantics", "9 类 Region 对象"),
    ("S4", "区域层级装配", "Region 对象列表", "带 parent/children 的区域树"),
    ("S5", "结构化语句生成", "区域树", "语句 AST"),
    ("S6", "表达式重建", "语句 AST", "完整表达式 AST"),
    ("S7", "后处理", "完整 AST", "可输出 AST"),
]

SIGNATURES = {
    "S1": {
        "CFGBuilder": 3, "CFGOptimizer": 3, "build_cfg": 3, "build_basic_blocks": 3,
        "DominatorAnalyzer": 2, "back_edge": 2, "dominator": 2, "BasicBlock": 1,
        "successors": 1, "predecessors": 1,
    },
    "S2": {
        "BlockRole": 3, "BlockSemantics": 3, "_mark_block": 3, "_classify_block": 3,
        "_analyze_block": 3, "mark_role": 3, "is_jump_target": 2, "block_role": 2,
        "is_conditional": 1, "fallthrough": 1, "semantics": 1,
    },
    "S3": {
        "IfRegion": 3, "LoopRegion": 3, "TryExceptRegion": 3, "WithRegion": 3,
        "MatchRegion": 3, "AssertRegion": 3, "BoolOpRegion": 3, "TernaryRegion": 3,
        "RegionType": 2, "_create_": 2, "merge_block": 2, "match_block": 2,
        "body_block": 2, "else_block": 2, "_regions": 2, "identify_": 2, "region": 1,
    },
    "S4": {
        "block_to_region": 3, "set_parent": 3, "get_parent": 3, "_build_region_tree": 3,
        "_link_": 2, "_attach": 2, "hierarchy": 2, "_nest": 2, "region_by_entry": 2,
        "_assemble": 2, "parent": 1, "children": 1,
    },
    "S5": {
        "generate_ast_from_regions": 3, "_gen_stmt": 3, "gen_stmt": 3, "_generate_": 2,
        "_emit": 2, "ASTIf": 2, "ASTWhile": 2, "ASTFor": 2, "ASTTry": 2, "ASTWith": 2,
        "ASTMatch": 2, "ASTAssign": 2, "ASTReturn": 2, "statement": 1, "stmt": 1,
        "while": 1, "for": 1, "if": 1, "try": 1, "with": 1, "match": 1,
    },
    "S6": {
        "ExpressionReconstructor": 3, "reconstruct": 3, "_rebuild": 3, "_build_expr": 3,
        "operand": 2, "precedence": 2, "expression": 1, "expr": 1, "binary": 1,
        "unary": 1, "call_expr": 1, "compare": 1, "BoolOp": 1, "Ternary": 1,
    },
    "S7": {
        "post_process": 3, "_fix_": 3, "_patch_": 3, "_correct_": 3, "_cleanup_": 3,
        "sanitize": 2, "dedup": 2, "elide": 2, "_strip": 2, "_merge_": 2,
        "normalize": 2, "fallback": 1, "overlap": 1,
    },
}

# 名族先验（次级证据，权重 2，低于强 token）：仅当名族命中时 +2，最终以总分取胜
NAME_FAMILY = [
    (("identify_", "detect_", "_regions", "region_"), "S3"),
    (("_mark_", "mark_", "_classify", "classify_"), "S2"),
    (("generate", "gen_", "_gen_", "emit", "_stmt", "_statement"), "S5"),
    (("expr", "reconstruct", "rebuild", "operand"), "S6"),
    (("fix", "patch", "correct", "cleanup", "merge", "hack", "workaround",
      "fallback", "sanitize", "dedup", "elide", "post"), "S7"),
    (("block_to_region", "parent", "attach", "link_", "hierarchy", "nest"), "S4"),
    (("cfg", "build_block", "successor", "predecessor", "dominator"), "S1"),
]


def collect_files():
    files = []
    for d in WL_DIRS:
        files += sorted((ROOT / d).rglob("*.py"))
    for name in ENTRY_FILES:
        p = ROOT / name
        if p.exists():
            files.append(p)
    return files


def git_head():
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        return "unknown"


REGION_CLASS_NAMES = {
    "Region", "IfRegion", "LoopRegion", "TryExceptRegion", "WithRegion",
    "MatchRegion", "AssertRegion", "BoolOpRegion", "TernaryRegion",
}


def body_tokens(node):
    """返回 (loads, constructs)。

    loads     = 方法体出现过的标识符/属性名/参数名（不含字符串常量，避免 docstring 噪声）
    constructs = 作为调用目标出现的类/函数名（`IfRegion(...)` 才是"构造区域"的证据；
                 仅作为 isinstance/注解/属性读取属于"消费区域"，属于生成侧信号）
    """
    loads = set()
    constructs = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name):
            loads.add(n.id)
        elif isinstance(n, ast.Attribute):
            loads.add(n.attr)
        elif isinstance(n, ast.arg):
            loads.add(n.arg)
        elif isinstance(n, ast.alias):
            loads.add((n.asname or n.name).split(".")[0])
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                constructs.add(f.id)
            elif isinstance(f, ast.Attribute):
                constructs.add(f.attr)
    return loads, constructs


def self_fields(node):
    reads, writes = set(), set()
    for n in ast.walk(node):
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "self":
            if isinstance(n.ctx, ast.Store):
                writes.add(n.attr)
            else:
                reads.add(n.attr)
    return reads, writes


def name_family(name):
    for tokens, sid in NAME_FAMILY:
        if any(t in name for t in tokens):
            return sid
    return None


ANALYSIS_STAGES = ("S1", "S2", "S3", "S4")
GENERATION_STAGES = ("S5", "S6", "S7")


def class_weights(file_rel):
    """类级角色先验：region_analyzer 是识别侧（S1-S4），region_ast_generator 是生成侧（S5-S7）。

    理由：这两个 god class 就是管线的两半，类归属本身是可靠证据；
    不加此先验时，生成侧方法因"消费"区域类名会被误判为 S3。
    """
    if "region_ast_generator" in file_rel:
        return {sid: (1.2 if sid in GENERATION_STAGES else 0.25) for sid, _, _, _ in STAGES}
    if "region_analyzer" in file_rel:
        return {sid: (1.2 if sid in ANALYSIS_STAGES else 0.25) for sid, _, _, _ in STAGES}
    return {sid: 1.0 for sid, _, _, _ in STAGES}


def classify(name, loads, constructs, weights=None):
    """返回 (final, token_stage, family, score, evidence, conflict)

    token 证据为主（权重 1-3 × 类级先验），名族先验次之（+2）；冲突项单独标记进 review 列表。
    """
    weights = weights or {sid: 1.0 for sid, _, _, _ in STAGES}
    scores = {sid: 0 for sid, _, _, _ in STAGES}
    evidence = {sid: [] for sid, _, _, _ in STAGES}
    consumed = loads - constructs
    for t in constructs:
        for sid, sig in SIGNATURES.items():
            w = sig.get(t)
            if w:
                scores[sid] += w * weights[sid]
                evidence[sid].append(f"new:{t}")
    for t in consumed:
        for sid, sig in SIGNATURES.items():
            w = sig.get(t)
            if w:
                scores[sid] += w * 0.3 * weights[sid]
                evidence[sid].append(t)
    # 消费区域对象 = 生成侧证据（读取 IfRegion/LoopRegion... 而不构造它们）
    for t in consumed & REGION_CLASS_NAMES:
        scores["S5"] += 1.0 * weights["S5"]
        evidence["S5"].append(f"use:{t}")
    token_stage = max(scores.items(), key=lambda kv: kv[1])[0] if max(scores.values()) > 0 else None
    family = name_family(name)
    total = dict(scores)
    if family:
        total[family] += 2
    best = max(total.items(), key=lambda kv: kv[1])
    if best[1] == 0:
        return "Unclassified", token_stage, family, 0, [], False
    ev = sorted(set(evidence.get(best[0], [])))[:5]
    if family:
        ev = [f"family:{family}"] + ev
    conflict = bool(token_stage and family and token_stage != family)
    return best[0], token_stage, family, best[1], ev, conflict


def method_body_hash(fn):
    mod = ast.Module(body=fn.body, type_ignores=[])
    return hashlib.md5(ast.dump(mod).encode()).hexdigest()[:10]


def analyze_file(path):
    rel = path.relative_to(ROOT).as_posix()
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace").lstrip("﻿")
    info = {
        "file": rel,
        "bytes": len(raw),
        "lines": len(text.splitlines()),
        "md5": hashlib.md5(raw).hexdigest(),
        "classes": [],
        "functions": {},
        "parse_error": None,
    }
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        info["parse_error"] = f"{exc.msg} (line {exc.lineno})"
        return info
    weights = class_weights(rel)
    for n in tree.body:
        if isinstance(n, ast.ClassDef):
            cls = {
                "name": n.name,
                "lineno": n.lineno,
                "lines": (n.end_lineno or n.lineno) - n.lineno + 1,
                "bases": [ast.unparse(b) for b in n.bases],
                "methods": [],
            }
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    loads, constructs = body_tokens(m)
                    stage, token_stage, family, score, ev, conflict = classify(m.name, loads, constructs, weights)
                    reads, writes = self_fields(m)
                    span = (m.end_lineno or m.lineno) - m.lineno + 1
                    cls["methods"].append({
                        "name": m.name,
                        "lineno": m.lineno,
                        "lines": span,
                        "stage": stage,
                        "token_stage": token_stage,
                        "name_family": family,
                        "score": score,
                        "evidence": ev,
                        "conflict": conflict,
                        "self_reads": len(reads),
                        "self_writes": len(writes),
                        "body_hash": method_body_hash(m),
                    })
            info["classes"].append(cls)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info["functions"][n.name] = {
                "lineno": n.lineno,
                "lines": (n.end_lineno or n.lineno) - n.lineno + 1,
                "body_hash": method_body_hash(n),
            }
    return info


def dup_matrix(infos):
    parsed = [i for i in infos if not i["parse_error"]]
    rows = []
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            a, b = parsed[i], parsed[j]
            fa = {m["name"]: m for c in a["classes"] for m in c["methods"]}
            fb = {m["name"]: m for c in b["classes"] for m in c["methods"]}
            fa.update(a["functions"])
            fb.update(b["functions"])
            same_name = set(fa) & set(fb)
            same_body = {n for n in same_name if fa[n]["body_hash"] == fb[n]["body_hash"]}
            if len(same_name) < 3:
                continue
            rows.append({
                "a": a["file"],
                "b": b["file"],
                "a_lines": a["lines"],
                "b_lines": b["lines"],
                "funcs_a": len(fa),
                "funcs_b": len(fb),
                "same_name": len(same_name),
                "same_body": len(same_body),
                "differing": sorted(same_name - same_body),
                "hash_sample": sorted({fa[n]["body_hash"] for n in same_body})[:3],
            })
    rows.sort(key=lambda r: (-r["same_body"], -r["same_name"]))
    return rows


def stage_rollup(classes):
    roll = defaultdict(lambda: {"methods": 0, "lines": 0})
    unclassified = []
    conflicts = []
    for cls in classes:
        for m in cls["methods"]:
            r = roll[m["stage"]]
            r["methods"] += 1
            r["lines"] += m["lines"]
            if m["stage"] == "Unclassified":
                unclassified.append({"class": cls["name"], **m})
            if m["conflict"]:
                conflicts.append({"class": cls["name"], **m})
    return roll, unclassified, conflicts


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    head = git_head()
    infos = [analyze_file(f) for f in collect_files()]

    god = {}
    for key in ("core/cfg/region_analyzer.py", "core/cfg/region_ast_generator.py"):
        cls = next(
            (c for c in next(i for i in infos if i["file"] == key)["classes"]
             if c["name"] in ("RegionAnalyzer", "RegionASTGenerator")),
            None,
        )
        god[key] = cls

    roll, unclassified, conflicts = stage_rollup([c for c in god.values() if c])
    total_methods = sum(r["methods"] for r in roll.values())
    total_lines = sum(r["lines"] for r in roll.values())
    pairs = dup_matrix(infos)

    evidence = {
        "generated_at": stamp,
        "git_head": head,
        "whitelist_files": len(infos),
        "god_classes": {
            k: {
                "class": v["name"], "file": k, "lines": v["lines"],
                "methods": len(v["methods"]),
                "method_lines": sum(m["lines"] for m in v["methods"]),
            } for k, v in god.items() if v
        },
        "stage_rollup": {sid: dict(roll.get(sid, {"methods": 0, "lines": 0})) for sid, _, _, _ in STAGES}
        | {"Unclassified": dict(roll.get("Unclassified", {"methods": 0, "lines": 0}))},
        "total_methods": total_methods,
        "total_method_lines": total_lines,
        "unclassified_detail": unclassified,
        "conflict_detail": conflicts,
        "dup_pairs": pairs,
        "files": infos,
    }
    (OUT_DIR / "anatomy-evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )

    # ---------- region-anatomy.md ----------
    p = 0.5
    rows = []
    for sid, name, src, dst in STAGES:
        r = roll.get(sid, {"methods": 0, "lines": 0})
        share = r["lines"] / total_lines * 100 if total_lines else 0
        rows.append([sid, name, src, dst, r["methods"], r["lines"], f"{share:.1f}%"])
    u = roll.get("Unclassified", {"methods": 0, "lines": 0})
    rows.append(["U", "Unclassified", "—", "—", u["methods"], u["lines"],
                 f"{u['lines'] / total_lines * 100:.1f}%" if total_lines else "0%"])

    per_class_sections = []
    for key, cls in god.items():
        if not cls:
            continue
        sub_roll, sub_un, sub_conf = stage_rollup([cls])
        sub_total = sum(r["lines"] for r in sub_roll.values())
        lines = [f"### {cls['name']}（`{key}:{cls['lineno']}`）", ""]
        lines.append(f"类体 {cls['lines']:,} 行 / {len(cls['methods'])} 个方法"
                     + (f"，方法合计 {sub_total:,} 行（占类体 {sub_total / cls['lines'] * 100:.0f}%）" if cls["lines"] else ""))
        lines.append("")
        rows2 = []
        for sid, name, _, _ in STAGES:
            r = sub_roll.get(sid, {"methods": 0, "lines": 0})
            if r["methods"]:
                rows2.append([sid, name, r["methods"], r["lines"],
                              f"{r['lines'] / sub_total * 100:.1f}%"])
        if sub_un:
            r = sub_roll.get("Unclassified", {"methods": 0, "lines": 0})
            rows2.append(["U", "Unclassified", r["methods"], r["lines"],
                          f"{r['lines'] / sub_total * 100:.1f}%"])
        lines.append(md_table(["阶段", "名称", "方法数", "行数", "占比"], rows2))
        lines.append("")
        lines.append("体长前 12 方法（外提成本参考，`self` 读/写字段数越高外提越贵）：")
        lines.append("")
        top = sorted(cls["methods"], key=lambda m: -m["lines"])[:12]
        lines.append(md_table(
            ["方法", "行", "行数", "阶段", "得分", "self 读/写", "锚点"],
            [[f"`{m['name']}`", m["lineno"], m["lines"], m["stage"], m["score"],
              f"{m['self_reads']}/{m['self_writes']}", f"`{key}:{m['lineno']}`"] for m in top],
        ))
        lines.append("")
        per_class_sections.append("\n".join(lines))

    un_lines = []
    if unclassified:
        un_lines = ["## Unclassified 清单（需人工判定或修阶段模型）", "",
                    md_table(["类", "方法", "行", "行数", "self 读/写", "锚点"],
                             [[c["class"], f"`{c['name']}`", c["lineno"], c["lines"],
                               f"{c['self_reads']}/{c['self_writes']}",
                               f"`core/cfg/region_analyzer.py:{c['lineno']}`" if c["class"] == "RegionAnalyzer"
                               else f"`core/cfg/region_ast_generator.py:{c['lineno']}`"]
                              for c in sorted(unclassified, key=lambda x: -x["lines"])])]

    conf_lines = []
    if conflicts:
        conf_lines = ["## 冲突项（名族先验与 token 证据不一致，需人工确认）", "",
                      f"共 {len(conflicts)} 个方法，最终归属以 token 证据为主。", "",
                      md_table(["类", "方法", "行", "行数", "token 证据", "名族先验", "定稿阶段"],
                               [[c["class"], f"`{c['name']}`", c["lineno"], c["lines"],
                                 c["token_stage"] or "—", c["name_family"] or "—", c["stage"]]
                                for c in sorted(conflicts, key=lambda x: -x["lines"])[:40]]),
                      ""]
    conf_block = "\n".join(conf_lines)
    un_block = "\n".join(un_lines) if un_lines else "## Unclassified 清单\n\n（空）"

    anatomy = f"""# 区域归约算法解剖（生成文档）

> 由 `tools/anatomy/extract_stages.py` 生成，**不要手改数字**。生成时刻 `{stamp}`，git HEAD `{head}`。
> 源码变化后重跑：`python tools/anatomy/extract_stages.py`（并行迭代代理改过 region 文件时必须重跑，见 design D4）。

## 阶段模型（design D1）

区域归约 = 七个阶段，相邻阶段只通过显式数据结构传递：

{md_table(["阶段", "名称", "输入", "输出"], [[s[0], s[1], f"`{s[2]}`", f"`{s[3]}`"] for s in STAGES])}

## 归属汇总（RegionAnalyzer + RegionASTGenerator）

{md_table(["阶段", "名称", "输入", "输出", "方法数", "行数", "占比"], rows)}

合计 {total_methods} 个方法 / {total_lines:,} 行。Unclassified 占比 {u['lines'] / total_lines * 100:.1f}%
（阈值 15%，见 spec `region-stage-model`）。

{chr(10).join(per_class_sections)}

{conf_block}

{un_block}
"""
    (OUT_DIR / "region-anatomy.md").write_text(anatomy, encoding="utf-8", newline="\n")

    # ---------- dup-matrix.md ----------
    dup_rows = []
    for r in pairs:
        verdict = "合并/删除候选" if r["same_body"] >= 10 else "不同构，保留"
        dup_rows.append([
            f"`{r['a']}`", f"`{r['b']}`", r["funcs_a"], r["funcs_b"],
            r["same_name"], r["same_body"], verdict,
            ", ".join(r["hash_sample"]) or "—",
        ])
    diff_details = []
    for r in pairs:
        if r["same_body"] >= 10 and r["differing"]:
            diff_details.append(
                f"### `{r['a']}` ↔ `{r['b']}`：{len(r['differing'])} 个同名不同体函数\n\n"
                + "、".join(f"`{n}`" for n in r["differing"][:60])
                + ("…\n" if len(r["differing"]) > 60 else "\n")
            )

    dup = f"""# 重复矩阵（生成文档）

> 由 `tools/anatomy/extract_stages.py` 生成。生成时刻 `{stamp}`，git HEAD `{head}`。
> 判据（spec `dup-triage`）：同名数 / 同体数 / 函数体 AST 哈希三件套；行数量级相似**不作为**重复判据。

## 全量文件对（同名 ≥ 3）

{dmd if (dmd := md_table(["文件 A", "文件 B", "A 函数数", "B 函数数", "同名", "同体", "结论", "AST 哈希样本"], dup_rows)) else "（无）"}

## 差异函数明细（需逐个判定保留哪一侧）

{chr(10).join(diff_details) if diff_details else "（无同体 ≥10 的文件对）"}

## 净减行数折算（design D5）

净减行数只对「合并/删除」结论成立；阶段化搬移不计入净减行数。
"""
    (OUT_DIR / "dup-matrix.md").write_text(dup, encoding="utf-8", newline="\n")

    print(f"files={len(infos)} methods={total_methods} unclassified={u['methods']} "
          f"({u['lines'] / total_lines * 100:.1f}%) dup_pairs={len(pairs)}")
    for r in pairs[:5]:
        print(f"  {r['a']} <-> {r['b']}: same_name={r['same_name']} same_body={r['same_body']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
