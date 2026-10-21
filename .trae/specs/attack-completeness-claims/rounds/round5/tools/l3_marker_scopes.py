#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 §2：标记计数的第三口径 —— 「机制点」口径（去重到 承载函数 × 破口号）。

理由：口径 A（191，注释标记出现次数）与口径 B（123，纯数字破口号）都不是
「落地机制数」：同一机制在同一文件内可被多处注释标注，同一破口号可在多个
文件重复出现。本脚本按「承载该标记的最内层 `def`/`class` 作用域 × 破口号」
去重，给出机制点的第三个读数。
"""
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

WIDE = re.compile(r"\[B(?P<b>\d+[A-Za-z]*)-V3R(?P<r>\d+)")
DEF = re.compile(r"^(\s*)(?:async\s+)?def\s+(?P<n>\w+)")
CLS = re.compile(r"^(\s*)class\s+(?P<n>\w+)")


def scope_of(lines, idx):
    """返回 (kind, name, lineno)：该行所处的最内层 def/class 作用域。"""
    best = ("<module>", "<module>", 0)
    for j in range(idx + 1):
        m = DEF.match(lines[j])
        if m:
            ind = len(m.group(1))
            if best[0] != "<module>" and ind <= len(best[1]) if False else True:
                pass
            best = ("def", m.group("n"), j + 1, ind)
        m2 = CLS.match(lines[j])
        if m2:
            best = ("class", m2.group("n"), j + 1, len(m2.group(1)))
    # 保留最内层（后出现的、缩进更大的）
    return best


def main():
    core = "core/cfg"
    rows = []
    for fn in sorted(os.listdir(core)):
        if not fn.endswith(".py"):
            continue
        lines = open(os.path.join(core, fn), encoding="utf-8", errors="replace").read().splitlines()
        stack = []  # (indent, kind, name, lineno)
        for i, line in enumerate(lines):
            while stack and (line.strip() == "" or len(line) - len(line.lstrip()) <= stack[-1][0]):
                if line.strip() == "":
                    break
                stack.pop()
            m = DEF.match(line)
            if m:
                stack.append((len(m.group(1)), "def", m.group("n"), i + 1))
            else:
                m2 = CLS.match(line)
                if m2:
                    stack.append((len(m2.group(1)), "class", m2.group("n"), i + 1))
            for mm in WIDE.finditer(line):
                owner = stack[-1] if stack else (0, "module", "<module>", 0)
                nxt = line[mm.end():mm.end() + 1]
                rows.append({
                    "file": fn,
                    "line": i + 1,
                    "breach": mm.group("b"),
                    "family": "R" + mm.group("r"),
                    "owner_kind": owner[1],
                    "owner_name": owner[2],
                    "owner_line": owner[3],
                    "strict": bool(mm.group("b").isdigit() and nxt == "]"),
                    "tail": line[mm.end():mm.end() + 24].rstrip(),
                })
    per_fam = {}
    for r in rows:
        per_fam.setdefault(r["family"], []).append(r)
    print("口径 A（标记出现次数） =", len(rows))
    print("口径 B（纯数字破口号 + 紧邻 ']'） =", sum(1 for r in rows if r["strict"]))
    print("口径 C（机制点 = 承载函数 × 破口号） =", len({(r["file"], r["owner_name"], r["breach"]) for r in rows}))
    print("承载函数数 =", len({(r["file"], r["owner_name"]) for r in rows}))
    print()
    print("191 的分解：")
    print("  (a) 纯数字破口号且紧邻 ']'          =", sum(1 for r in rows if r["strict"]))
    print("  (b) 字母后缀破口号 (B61a…/B70c…)    =", sum(1 for r in rows if not r["breach"].isdigit()))
    print("  (c) 纯数字破口号但后缀文字（如 ' 修复'）=", sum(1 for r in rows if r["breach"].isdigit() and not r["strict"]))
    print()
    print("逐族：标记数 / 破口号数 / 机制点数 / 承载函数数")
    for fam in sorted(per_fam):
        rs = per_fam[fam]
        print("  %-4s markers=%-3d breaches=%-3d mechpoints=%-3d owners=%d" % (
            fam, len(rs), len({r["breach"] for r in rs}),
            len({(r["file"], r["owner_name"], r["breach"]) for r in rs}),
            len({(r["file"], r["owner_name"]) for r in rs})))
    out = ".trae/specs/attack-completeness-claims/rounds/round5/logs/l3_marker_rows.json"
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    print("\nrows ->", out)


if __name__ == "__main__":
    main()
