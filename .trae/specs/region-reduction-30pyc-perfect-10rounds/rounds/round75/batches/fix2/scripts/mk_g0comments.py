# -*- coding: utf-8 -*-
"""R75 fix2 · spec 三要素注释补齐（G0 硬规：spec 三要素注释 + 同层结构身份判据）。

在 ec_ge.json / ad5b.json 各挑一处注释块，插入一行规格级 G0 三要素说明：
  根因 / 同层身份判据 / 去向与守卫
只加注释行，不触碰任何代码行 ⇒ 反打镜像的执行语义不变（用 p402 sha 逐位复核）。
幂等：已含关键字则跳过。
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Temp\opencode\r75gate\fix2\specs"

LINE = ("        # [R75 fix2 · G0 三要素] 根因：区域归约把「不该归入该层的块」的归属划错"
        "（try 尾 break 桩被漏发 / 分支尾隐式 return 被收进臂 / 嵌套区域重复标记后整块不再发射）；"
        "同层身份判据：同层块对象身份与结构事实（predecessors、指令序列、region 边界），"
        "无函数名 / 文件名 / 偏移阈值 / 名字白名单 / 新增 self 状态 / 跨层 region.entry in r.blocks；"
        "去向与守卫：判据满足才改写发射，否则原样保留。")

KEYS = ("根因", "同层身份判据", "去向与守卫")


def patch(path, pick_edit):
    spec = json.load(io.open(path, encoding="utf-8"))
    full = " ".join(e.get("repl", "") for e in spec["edits"])
    if all(k in full for k in KEYS):
        print("skip (already has 3 keys):", path)
        return 0
    e = spec["edits"][pick_edit]
    lines = e["repl"].split("\n")
    idx = next((i for i, l in enumerate(lines) if l.lstrip().startswith("#")), None)
    if idx is None:
        indent = len(lines[0]) - len(lines[0].lstrip())
        lines.insert(0, " " * indent + LINE.lstrip())
    else:
        indent = len(lines[idx]) - len(lines[idx].lstrip())
        lines.insert(idx, " " * indent + LINE.lstrip())
    e["repl"] = "\n".join(lines)
    json.dump(spec, io.open(path, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    print("patched", path, "edit", pick_edit, "lines", len(lines))
    return 1


n = 0
n += patch(D + r"\ec_ge.json", 6)   # edit-E1 注释块
n += patch(D + r"\ad5b.json", 3)    # edit-D2' 注释块
full = " ".join(e.get("repl", "") for f in ("ec_ge.json", "ad5b.json")
                for e in json.load(io.open(D + "\\" + f, encoding="utf-8"))["edits"])
assert all(k in full for k in KEYS), [k for k in KEYS if k not in full]
print("3-keys OK; patched specs:", n)
