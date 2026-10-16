# Round 10 · 10.2 步骤2 grep 落地标记全量扫描（只读；产出 r10v10_wiki_marks.json）
# 用法: python -X utf8 r10v10_marks_scan.py <repo_root> <out_json>
import json
import os
import re
import subprocess
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "r10v10_wiki_marks.json")
SCAN_DIRS = ["core"]

TARGETS = [
    # --- round9（本批落地声明，positive） ---
    ("[B104-R9", "round9", "present", "B104-R9 语句前缀变体/混合操作数求值段集扩门"),
    ("[B104-R4]", "round9", "present", "B104-R4 POP_TOP 表达式语句终结符（w3_nostore 封闭）"),
    ("_extract_recheck_store_stmts", "round9", "present", "路 A 多语句 STORE 边界抽取器因子化（六项 docstring）"),
    ("[B124-R1", "round9", "present", "B124-R1 自足 return 形扩门（分析器桶）"),
    ("_b124r1_chain_region_is_self_return", "round9", "present", "B124-R1 守卫方法（merge 块清理/协议族+RETURN_VALUE 终结）"),
    ("[B124-R2a", "round9", "present", "B124-R2a 连接清理对守卫（SWAP(2)+POP_TOP 邻接）"),
    ("[B124-R2b", "round9", "present", "B124-R2b with 协议边界守卫（BEFORE_WITH 族）"),
    ("_ternary_host_call_prefix_span", "round9", "present", "T19-4 宿主调用前缀跨度（e10/r8_10 病灶面）"),
    ("[B125-R1", "round9", "present", "B125-R1 祖先链排除（_child_region_blocks_r23 调用侧）"),
    ("_child_region_blocks_r23", "round9", "present", "B125 祖先/子区域区分扫描（R23 守卫族）"),
    ("[B126-R2", "round9", "present", "B126-R2 异常路径尾闩守卫"),
    ("_b126r2_raise_only_trampoline_exit", "round9", "present", "B126-R2 守卫方法（RAISE_VARARGS/RERAISE 终点）"),
    ("[B126-R1", "round9", "absent", "B126-R1 认领集补守卫（9.3b 已按 REVIEW2 R-1 全量移除）"),
    ("_b126_claimed", "round9", "absent", "B126-R1 认领集变量（9.3b 已移除，应 0）"),
    # --- 前八轮（§8.1 表既有 + 8.x 归档） ---
    ("[B106-R3", "prior", "present", "B106-R3 LOAD_METHOD 净栈 +1 补 delta（round8 P0 回退修复）"),
    ("[B109", "prior", "present", "B109 while-else break 守卫（round4 落地）"),
    ("[B110", "prior", "absent", "B110 划除确认（round8 声明为划除，非落地项，应 0）"),
    ("[B112", "prior", "absent", "B112 await 链消费门（round4 开放破口，round8 部分移交——无落地声明，应 0）"),
    ("[B113", "prior", "present", "B113 推导式 for 链回归修复（round8）"),
    ("[B118", "prior", "present", "B118 else-break 三元化（round7）"),
    ("[B119", "prior", "present", "B119 try 体 return 吞并（round7）"),
    ("[B120", "prior", "present", "B120 loop_analyzer NOP 幻影（round7）"),
    ("[B121", "prior", "present", "B121 while 条件守卫 if gate（round7）"),
    ("[B83", "prior", "present", "B83 try/finally+raise 吞并（round4 提出/round8 位B 落地）"),
    ("[B77", "prior", "present", "B77 designated 臂值钻石重建（round8 位B）"),
    ("[B81", "prior", "present", "B81 match guard 字面量幻影（round8 位C）"),
    ("[B102", "prior", "present", "B102 except* handler 链（round4/round8 位C）"),
    ("[B96", "prior", "present", "B96 async 生成器（round8 位C）"),
    ("[B98-R1", "prior", "present", "B98-R1 镜像极性共享块重建（round8 位B 部分封闭）"),
    ("[B82", "prior", "present", "B82 臂 return 副本消费（round8 位B）"),
    ("[B103", "prior", "present", "B103 or 守卫/try 体（round8 位C/R2）"),
    ("[B104-R2a", "prior", "present", "B104-R2a while 条件 and 尾（round8 R2 批）"),
    ("_B104_CC_RECHECK_EVAL_OPS", "prior", "present", "B104-R2b 纯值求值白名单完备化（round8 声明锚点，常量定义+4 消费点）"),
    ("[B104-R2b", "prior", "absent", "B104-R2b 无字面标记（round8 声明锚点 = _B104_CC_RECHECK_EVAL_OPS，另列核验）"),
    ("[B105-R2", "prior", "present", "B105-R2 walrus 消费点（round8 R2 批）"),
    ("[B107-R2", "prior", "present", "B107-R2 多目标赋值（round8 R2 批）"),
    ("[B117", "prior", "present", "B117 挂起循环回边块认领（round7）"),
    ("[B75", "prior", "present", "B75 try 宿主 global 消费（round1 批 B）"),
    ("[B72", "prior", "present", "B72 global 声明错位（v6 harden round10 封闭）"),
    ("[B71", "prior", "present", "B71 try/finally else 块（v6 harden round10 部分封闭）"),
    ("[B48", "prior", "present", "B48 else-try 边界（v6 harden round10 封闭）"),
    ("[B46", "prior", "present", "B46 If 条件嵌套（v6 harden round10 部分封闭）"),
    ("[B1b fix", "prior", "present", "B1 族五臂封闭（round1）"),
    ("_sb_has_body", "prior", "present", "B1 族 or 裸尾续接同一谓词"),
    ("_block_is_continue_target", "prior", "present", "B2 continue 守卫"),
    ("[fix3-T1", "prior", "present", "B3 共享尾守卫族 fix3-T1"),
    ("[fix3-T6", "prior", "present", "B3 共享尾守卫族 fix3-T6"),
    ("[W23", "prior", "present", "B3 共享尾守卫族 W23"),
    ("[R71-thenover", "prior", "present", "B3 共享尾守卫族 R71-thenover"),
    ("W14-C", "prior", "present", "B3 共享尾守卫族 W14-C（臂收集+汇合剪枝）"),
    ("[B99", "prior", "present", "B99 boolop 吸收收窄/残（round3-8）"),
    ("[B100", "prior", "present", "B100 import 深嵌套（round4）"),
    ("[B101", "prior", "present", "B101 star import（round4）"),
    ("[B114", "prior", "present", "B114 import a.b as a（round5）"),
    ("[B115", "prior", "present", "B115 while 条件 and/or 幻影（round5）"),
    ("[B116", "prior", "present", "B116 位置参数 cellvars（round5）"),
    ("[B84", "prior", "present", "B84 del/with 吞并（round2 P2）"),
    ("[B85", "prior", "present", "B85（round2 P2）"),
    ("[B86", "prior", "present", "B86（round2 P2）"),
    ("[B87", "prior", "present", "B87 try 体嵌套宿主（round2 P2/P3）"),
    ("[B88", "prior", "absent", "B88 return 嵌套宿主（round9 矩阵仍破口，无落地声明，应 0）"),
    ("[B89", "prior", "present", "B89 boolop 链（round2 P3）"),
    ("[B90", "prior", "present", "B90 f-string format-spec（round2 P2）"),
    ("[B91", "prior", "present", "B91（round2 P3）"),
    ("[B92", "prior", "present", "B92（round2 P3）"),
    ("[B93", "prior", "absent", "B93 with-in-match 幻影镜像（round9 矩阵仍破口，无落地声明，应 0）"),
    ("[B94", "prior", "absent", "B94 while NOP 残段（round9 矩阵仍破口，无落地声明，应 0）"),
    ("[B95", "prior", "present", "B95（round2 P3）"),
    ("[B97", "prior", "absent", "B97 handler break（round9 矩阵仍破口，无落地声明，应 0）"),
    ("[B108", "prior", "present", "B108 finally 吞并（round8 位B）"),
    ("[B111", "prior", "present", "B111 LOAD_CLASSDEREF/CLOSURE（round8 位B）"),
    ("_graft_pending_operand", "prior", "absent", "B1a 归档嫁接方案（确证废弃不落地，应 0）"),
    ("[B126-R1", "round9", "absent", "重复项占位见上（应 0）"),
]


def scan():
    hits = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "core")):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
                for lineno, line in enumerate(f, 1):
                    for pat in [(t[0], t) for t in TARGETS]:
                        if pat[0] in line:
                            hits.append((pat[1], rel, lineno, line.strip()[:240]))
    return hits


def main():
    raw = scan()
    by_pattern = {}
    for tgt, rel, lineno, text in raw:
        key = tgt[0] + "|" + tgt[1] + "|" + tgt[2]
        by_pattern.setdefault(key, []).append({"file": rel, "line": lineno, "text": text})

    markers = []
    seen = set()
    for pat, group, expect, desc in TARGETS:
        key = pat + "|" + group + "|" + expect
        if key in seen:
            continue
        seen.add(key)
        hs = by_pattern.get(key, [])
        count = len(hs)
        if expect == "present":
            verdict = "PASS" if count > 0 else "FAIL(0-hit)"
        else:
            verdict = "PASS" if count == 0 else "FAIL(unexpected-hit)"
        markers.append({
            "pattern": pat, "group": group, "expect": expect, "desc": desc,
            "count": count, "verdict": verdict, "hits": hs,
        })

    # 全树 B 标记清单（交叉核对用）
    inv = {}
    mark_re = re.compile(r"\[(B\d+[A-Za-z0-9\-_a-z\.]*)\]")
    for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "core")):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            p = os.path.join(dirpath, fn)
            with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
                for line in f:
                    for m in mark_re.findall(line):
                        inv[m] = inv.get(m, 0) + 1

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    summary = {
        "total": len(markers),
        "pass": sum(1 for m in markers if m["verdict"] == "PASS"),
        "fail": sum(1 for m in markers if m["verdict"] != "PASS"),
        "fail_list": [m["pattern"] for m in markers if m["verdict"] != "PASS"],
    }
    out = {"head": head, "grep_root": "core/", "markers": markers,
           "bracket_marker_inventory": dict(sorted(inv.items())), "summary": summary}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
