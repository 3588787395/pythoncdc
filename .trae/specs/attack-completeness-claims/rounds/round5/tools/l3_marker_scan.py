#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 机制层攻击：标记族重算 + 触发谓词抽取。

计数口径（显式声明，见 ATTACK_L3_MECHANISM.md §2）：
  口径 A（宽）：正则 ``\[B\d+[A-Za-z]*-V3R\d+``，按出现次数计（允许字母后缀破口号）。
  口径 B（严）：正则 ``\[B\d+-V3R\d+\]``，仅纯数字破口号。
  族归属：由标记里的 ``-V3R<n>`` 段直接给出（R2..R8），与落地轮次一致。

同时抽取每个标记点上方 12 行内的注释/文档串文本，作为「触发谓词」原文证据。
"""
import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict

WIDE = re.compile(r"\[B\d+[A-Za-z]*-V3R\d+")
STRICT = re.compile(r"\[B\d+-V3R\d+\]")
FAMILY = re.compile(r"\[B(?P<b>\d+[A-Za-z]*)-V3R(?P<r>\d+)")


def scan(core_dir):
    files = sorted(
        os.path.join(core_dir, f)
        for f in os.listdir(core_dir)
        if f.endswith(".py")
    )
    rows = []
    wide_total = 0
    strict_total = 0
    per_family_wide = Counter()
    per_family_strict = Counter()
    per_family_file = defaultdict(Counter)
    per_breach_wide = Counter()
    for path in files:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        for i, line in enumerate(lines, 1):
            for m in WIDE.finditer(line):
                wide_total += 1
                fm = FAMILY.search(m.group(0))
                if not fm:
                    continue
                fam = "R" + fm.group("r")
                b = fm.group("b")
                per_family_wide[fam] += 1
                per_breach_wide[b] += 1
                per_family_file[fam][os.path.basename(path)] += 1
                # 口径 B：完整形如 ``[B123-V3R3]``（纯数字破口号 + 闭合方括号）
                strict_form = m.group(0) + "]" if line[m.end():m.end() + 1] == "]" else None
                if strict_form and STRICT.fullmatch(strict_form):
                    strict_total += 1
                    per_family_strict[fam] += 1
                # context: preceding comment/docstring lines
                ctx = []
                for j in range(max(0, i - 13), i):
                    t = lines[j].rstrip("\n").strip()
                    if t.startswith("#") or t.startswith('"""') or t.startswith("'''") or t.startswith("*"):
                        ctx.append(f"{j+1}: {t}")
                    elif t == "":
                        continue
                    else:
                        ctx.append(f"{j+1}: {t}")
                rows.append(
                    {
                        "file": os.path.relpath(path).replace("\\", "/"),
                        "line": i,
                        "marker": m.group(0),
                        "family": fam,
                        "breach": b,
                        "code": line.strip()[:220],
                        "context": ctx[-13:],
                    }
                )
    return {
        "wide_total": wide_total,
        "strict_total": strict_total,
        "per_family_wide": dict(sorted(per_family_wide.items())),
        "per_family_strict": dict(sorted(per_family_strict.items())),
        "per_family_file": {k: dict(v) for k, v in sorted(per_family_file.items())},
        "per_breach_wide": dict(sorted(per_breach_wide.items(), key=lambda kv: (len(kv[0]), kv[0]))),
        "rows": rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", default="core/cfg")
    ap.add_argument("--out", default=".trae/specs/attack-completeness-claims/rounds/round5/logs/l3_markers.json")
    a = ap.parse_args()
    res = scan(a.core)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    print("wide(口径A)=", res["wide_total"], "strict(口径B)=", res["strict_total"])
    print("per_family_wide=", res["per_family_wide"])
    print("per_family_strict=", res["per_family_strict"])
    print("per_family_file=")
    for f, c in res["per_family_file"].items():
        print("  ", f, dict(c))
    print("breaches=", len(res["per_breach_wide"]))


if __name__ == "__main__":
    main()
