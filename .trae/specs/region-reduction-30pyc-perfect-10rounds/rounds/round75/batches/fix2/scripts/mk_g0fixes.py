# -*- coding: utf-8 -*-
"""R75 fix2 · G0 修正：去掉新增行里的 `getattr(self, 'regions', None)`。

`self.regions` 在 region_ast_generator.__init__ 已初始化为 []（:280）、analyze() 赋值
（:678），故 getattr 兜底是多余的，且违 G0「新增代码无 getattr(self,...)」硬规。
改成直接读 `self.regions` ⇒ 语义等价（p402 402 份产物 sha 逐位复核）。
幂等：已替换则跳过。
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
P = r"D:\Temp\opencode\r75gate\fix2\specs\ec_ge.json"
OLD = "for _r75c_r in list(getattr(self, 'regions', None) or []):"
NEW = "for _r75c_r in list(self.regions):"

spec = json.load(io.open(P, encoding="utf-8"))
n = 0
for e in spec["edits"]:
    if OLD in e["repl"]:
        e["repl"] = e["repl"].replace(OLD, NEW)
        n += 1
assert n in (0, 1), n
assert all(OLD not in e.get("repl", "") for e in spec["edits"])
if n == 0:
    print("skip (already patched)")
else:
    json.dump(spec, io.open(P, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=1)
    print("patched getattr(self.regions) -> self.regions in edit(s):", n)
