import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Temp\opencode\r75gate\fix2\specs"
G = r"D:\Temp\opencode\r75gate"
SRC = r"F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py"
src = io.open(SRC, encoding="utf-8-sig").read()
edits = []

a1 = """_TRUE_POLARITY_COND_JUMP_OPS = frozenset({
    'POP_JUMP_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',
})
"""
assert src.count(a1) == 1
r1 = a1 + """

_G9 = {"on": False}


def _mk_log_set(_owner):
    import os as _osL, io as _ioL, traceback as _tbL

    class _LogSet(set):
        def _where(self):
            try:
                _stk = _tbL.format_stack()[:-1]
                return "".join("  | " + s.strip().replace("\\n", "\\n  | ")
                               for s in _stk[-14:])
            except Exception:
                return ""

        def add(self, _x):
            _o = getattr(self, "_owner", None)
            _c = getattr(getattr(_o, "cfg", None), "code", None)
            if (getattr(_c, "co_name", None) == "get_trade_status"
                    and getattr(_x, "start_offset", None) == 598):
                try:
                    with _ioL.open(_osL.environ["R75DBG"], "a", encoding="utf-8") as _f:
                        _f.write("  ADD598\\n" + self._where() + "\\n")
                except Exception:
                    pass
            return set.add(self, _x)

        def update(self, _it):
            for _x in list(_it):
                self.add(_x)
            return None

    _ls = _LogSet()
    _ls._owner = _owner
    return _ls
"""
edits.append({"anchor": a1, "repl": r1})

a2 = "        self.generated_blocks: Set[BasicBlock] = set()\n"
assert src.count(a2) == 1
edits.append({"anchor": a2,
              "repl": "        self.generated_blocks: Set[BasicBlock] = _mk_log_set(self)\n"})

a3 = "    def _generate_try_body(self, region: TryExceptRegion) -> List[Dict[str, Any]]:\n"
assert src.count(a3) == 1
r3 = a3 + """        _c9 = getattr(getattr(self, "cfg", None), "code", None)
        _G9["on"] = (getattr(_c9, "co_name", None) == "get_trade_status")
        if _G9["on"]:
            try:
                import os as _osN, io as _ioN
                with _ioN.open(_osN.environ["R75DBG"], "a", encoding="utf-8") as _f:
                    _f.write("  ENTER try tstart=%s ntry=%d gen598=%s\\n" % (
                        region.try_offset_start, len(region.try_blocks),
                        any(b.start_offset == 598 for b in self.generated_blocks)))
            except Exception:
                pass
"""
edits.append({"anchor": a3, "repl": r3})

a4 = """        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):
            if block in self.generated_blocks:
                continue
"""
assert src.count(a4) == 1
r4 = """        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):
            if _G9["on"] and block.start_offset == 598:
                try:
                    import os as _osM, io as _ioM
                    with _ioM.open(_osM.environ["R75DBG"], "a", encoding="utf-8") as _f:
                        _f.write("  MAIN598 gen=%s offs=%s\\n" % (
                            block in self.generated_blocks,
                            [b.start_offset for b in _try_blocks_eff]))
                except Exception:
                    pass
            if block in self.generated_blocks:
                continue
"""
edits.append({"anchor": a4, "repl": r4})

spec = {"file": "core/cfg/region_ast_generator.py", "edits": edits}
json.dump(spec, io.open(os.path.join(D, "probe12g.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5x %s %s"
        % (G, os.path.join(D, "probe12g.json"), os.path.join(D, "ad5.json")))
print(r.stdout, r.stderr)
dbgf = os.path.join(G, "fix2", "dump", "px.txt")
if os.path.exists(dbgf):
    os.remove(dbgf)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5x "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s %s\\fix2\\dump\\ecafgd5x_tiu.py" % (G, dbgf, G))
print(r.stdout, r.stderr)
print("----")
txt = io.open(dbgf, encoding="utf-8").read()
import re
for m in re.finditer(r"^  (ENTER try|ADD598|MAIN598).*?(?=^  (ENTER try|ADD598|MAIN598)|\Z)",
                     txt, re.S | re.M):
    print(m.group(0)[:3000])
    print(".......")
