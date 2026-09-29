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
assert src.count(a1) == 1, src.count(a1)
r1 = a1 + """

def _mk_log_set():
    import os as _osL, io as _ioL, traceback as _tbL
    class _LogSet(set):
        def _where(self):
            try:
                _stk = _tbL.format_stack()[:-1]
                return "".join("  | " + s.strip() for s in _stk[-10:])
            except Exception:
                return ""
        def add(self, _x):
            if getattr(_x, "start_offset", None) == 598:
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
    return _LogSet()
"""
edits.append({"anchor": a1, "repl": r1})

a2 = "        self.generated_blocks: Set[BasicBlock] = set()\n"
assert src.count(a2) == 1, src.count(a2)
r2 = "        self.generated_blocks: Set[BasicBlock] = _mk_log_set()\n"
edits.append({"anchor": a2, "repl": r2})

a3 = """        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):
            if block in self.generated_blocks:
                continue
"""
assert src.count(a3) == 1, src.count(a3)
r3 = """        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):
            if block.start_offset == 598:
                try:
                    import os as _osM, io as _ioM
                    with _ioM.open(_osM.environ["R75DBG"], "a", encoding="utf-8") as _f:
                        _f.write("  MAIN598 gen=%s n_eff=%d\\n" % (
                            block in self.generated_blocks, len(_try_blocks_eff)))
                except Exception:
                    pass
            if block in self.generated_blocks:
                continue
"""
edits.append({"anchor": a3, "repl": r3})

spec = {"file": "core/cfg/region_ast_generator.py", "edits": edits}
json.dump(spec, io.open(os.path.join(D, "probe11g.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5w %s %s"
        % (G, os.path.join(D, "probe11g.json"), os.path.join(D, "ad5.json")))
print(r.stdout, r.stderr)
dbgf = os.path.join(G, "fix2", "dump", "pw.txt")
if os.path.exists(dbgf):
    os.remove(dbgf)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5w "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s %s\\fix2\\dump\\ecafgd5w_tiu.py" % (G, dbgf, G))
print(r.stdout, r.stderr)
print("----")
txt = io.open(dbgf, encoding="utf-8").read().split("\n")
out = [l for l in txt if "ADD598" in l or "MAIN598" in l or l.startswith("  |")]
# print ADD598 blocks and MAIN598 lines only
keep = []
i = 0
while i < len(txt):
    if "ADD598" in txt[i] or "MAIN598" in txt[i]:
        keep.append(txt[i])
        j = i + 1
        while j < len(txt) and txt[j].startswith("  |"):
            keep.append(txt[j])
            j += 1
        i = j
    else:
        i += 1
print("\n".join(keep))
