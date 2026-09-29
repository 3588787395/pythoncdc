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

ec_ge = json.load(io.open(os.path.join(D, "ec_ge.json"), encoding="utf-8"))
base_edits = list(ec_ge["edits"])

# --- extend the edit-E (last) edit with logs ---
e = dict(base_edits[-1])
old_tail = "        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):\n"
assert e["repl"].endswith(old_tail), repr(e["repl"][-200:])
new_tail = """        if _G9["on"]:
            try:
                import os as _osN, io as _ioN
                with _ioN.open(_osN.environ["R75DBG"], "a", encoding="utf-8") as _f:
                    _f.write("  R75E n_eff=%d offs=%s gen598=%s\\n" % (
                        len(_try_blocks_eff),
                        [b.start_offset for b in _try_blocks_eff],
                        any(b.start_offset == 598 for b in self.generated_blocks)))
            except Exception:
                pass
        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):
            if _G9["on"] and block.start_offset == 598:
                try:
                    import os as _osM, io as _ioM
                    with _ioM.open(_osM.environ["R75DBG"], "a", encoding="utf-8") as _f:
                        _f.write("  MAIN598 gen=%s role=%s\\n" % (
                            block in self.generated_blocks,
                            self.region_analyzer.get_block_role(block)))
                except Exception:
                    pass
"""
e["repl"] = e["repl"][: -len(old_tail)] + new_tail
edits = base_edits[:-1] + [e]

# --- probe edits: LogSet helper + owner gate ---
a1 = """_TRUE_POLARITY_COND_JUMP_OPS = frozenset({
    'POP_JUMP_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',
})
"""
assert src.count(a1) == 1
edits.append({"anchor": a1, "repl": a1 + """

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
"""})

a2 = "        self.generated_blocks: Set[BasicBlock] = set()\n"
assert src.count(a2) == 1
edits.append({"anchor": a2,
              "repl": "        self.generated_blocks: Set[BasicBlock] = _mk_log_set(self)\n"})

a3 = "    def _generate_try_body(self, region: TryExceptRegion) -> List[Dict[str, Any]]:\n"
assert src.count(a3) == 1
edits.append({"anchor": a3, "repl": a3 + """        _c9 = getattr(getattr(self, "cfg", None), "code", None)
        _G9["on"] = (getattr(_c9, "co_name", None) == "get_trade_status")
"""})

spec = {"file": "core/cfg/region_ast_generator.py", "edits": edits}
json.dump(spec, io.open(os.path.join(D, "probe13g.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5y %s %s"
        % (G, os.path.join(D, "probe13g.json"), os.path.join(D, "ad5.json")))
print(r.stdout, r.stderr)
dbgf = os.path.join(G, "fix2", "dump", "py.txt")
if os.path.exists(dbgf):
    os.remove(dbgf)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5y "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s %s\\fix2\\dump\\ecafgd5y_tiu.py" % (G, dbgf, G))
print(r.stdout, r.stderr)
print("----")
txt = io.open(dbgf, encoding="utf-8").read()
import re
for m in re.finditer(r"^  (ENTER|R75E |ADD598|MAIN598).*?(?=^  (ENTER|R75E |ADD598|MAIN598)|\Z)",
                     txt, re.S | re.M):
    print(m.group(0)[:2600])
    print(".......")
