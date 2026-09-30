"""白名单模块可达性分析：从入口 BFS import 图，回答"什么是程序、什么不是"。

- 入口：pycdc.py、pycdas.py
- 可达 = 程序代码；不可达 = 死模块（0 入边且从入口不可达）
- 输出：stdout 汇总 + docs/refactor/reachability.json
"""

import ast
import json
from datetime import date
from pathlib import Path

ROOT = Path(r"F:\Downloads\pythoncdc-main")
OUT = ROOT / "docs" / "refactor" / "reachability.json"
WL_DIRS = ["core", "parsers", "bytecode", "utils"]
ENTRIES = ["pycdc", "pycdas"]


def collect():
    mods = {}
    for d in WL_DIRS:
        for f in (ROOT / d).rglob("*.py"):
            rel = f.relative_to(ROOT).with_suffix("")
            name = rel.as_posix().replace("/", ".")
            if name.endswith(".__init__"):
                name = name[: -len(".__init__")]
            mods[name] = f
    for e in ENTRIES:
        mods[e] = ROOT / f"{e}.py"
    return mods


def importer_package(mod_name, f):
    if f.name == "__init__.py":
        return mod_name
    return mod_name.rpartition(".")[0]


def touched_modules(mod_name, f):
    """返回该文件 import 语句触及的所有绝对模块名（含父包 __init__ 与 from X import sub 的 sub）。"""
    try:
        tree = ast.parse(f.read_text(encoding="utf-8", errors="replace").lstrip("﻿"))
    except SyntaxError:
        return set()
    pkg = importer_package(mod_name, f).split(".") if mod_name else []
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                out.add(a.name)
        elif isinstance(n, ast.ImportFrom):
            if n.level == 0:
                base = (n.module or "").split(".") if n.module else []
            else:
                base = pkg[: len(pkg) - (n.level - 1)] + ((n.module or "").split(".") if n.module else [])
            full = ".".join(base)
            if full:
                out.add(full)
                for a in n.names:
                    out.add(f"{full}.{a.name}")
    # 父包 __init__ 会被执行，一并触及
    expanded = set()
    for s in out:
        parts = s.split(".")
        for i in range(1, len(parts) + 1):
            expanded.add(".".join(parts[:i]))
    return expanded


def main():
    mods = collect()
    edges = {}
    for m, f in mods.items():
        hits = set()
        for s in touched_modules(m, f):
            if s in mods:
                hits.add(s)
            else:
                pref = ".".join(s.split(".")[:-1])
                while pref:
                    if pref in mods:
                        hits.add(pref)
                        break
                    pref = ".".join(pref.split(".")[:-1])
        edges[m] = hits - {m}

    seen, queue = set(), list(ENTRIES)
    while queue:
        cur = queue.pop()
        if cur in seen:
            continue
        seen.add(cur)
        queue.extend(edges.get(cur, ()))

    dead = sorted(set(mods) - seen)
    lines = {m: len(mods[m].read_text(encoding="utf-8", errors="replace").splitlines()) for m in mods}
    live_lines = sum(lines[m] for m in seen)
    dead_lines = sum(lines[m] for m in dead)

    print(f"modules total : {len(mods)}")
    print(f"live (reachable from entries) : {len(seen)}  ({live_lines} lines)")
    print(f"dead (unreachable) : {len(dead)}  ({dead_lines} lines)")
    for m in dead:
        print(f"  DEAD {m}  ({lines[m]} lines)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated": date.today().isoformat(),
                "entries": ENTRIES,
                "live_modules": sorted(seen),
                "live_lines": live_lines,
                "dead_modules": {m: lines[m] for m in dead},
                "dead_lines": dead_lines,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"JSON -> {OUT}")


if __name__ == "__main__":
    main()
