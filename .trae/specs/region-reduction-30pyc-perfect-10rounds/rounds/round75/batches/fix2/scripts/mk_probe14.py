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

spec = json.load(io.open(os.path.join(D, "probe13g.json"), encoding="utf-8"))
edits = list(spec["edits"])

a5 = "            body_stmts = self._generate_try_body(region)\n"
assert src.count(a5) == 1, src.count(a5)
edits.append({"anchor": a5, "repl": a5 + """            if _G9["on"]:
                try:
                    import os as _osQ, io as _ioQ
                    _tsQ = [(s.get("type") if isinstance(s, dict) else "?")
                            for s in body_stmts]
                    with _ioQ.open(_osQ.environ["R75DBG"], "a", encoding="utf-8") as _f:
                        _f.write("  TRYBODY n=%d hasBreak=%s tail=%s\\n" % (
                            len(body_stmts), "Break" in _tsQ, _tsQ[-8:]))
                except Exception:
                    pass
"""})

a6 = ("    def _generate_block_statements(self, block: BasicBlock, "
      "_cjb_parent: BasicBlock = None) -> List[Dict[str, Any]]:\n")
assert src.count(a6) == 1, src.count(a6)
edits.append({"anchor": a6, "repl": a6 + """        _c6 = getattr(getattr(self, "cfg", None), "code", None)
        if (getattr(_c6, "co_name", None) == "get_trade_status"
                and getattr(block, "start_offset", None) == 598):
            try:
                import os as _os6, io as _io6, traceback as _tb6
                with _io6.open(_os6.environ["R75DBG"], "a", encoding="utf-8") as _f:
                    _f.write("  CALL598 gen=%s\\n  | " % (block in self.generated_blocks))
                    _f.write("  | ".join(s.strip().replace("\\n", "\\n  | ")
                                         for s in _tb6.format_stack()[-6:-1]))
                    _f.write("\\n")
            except Exception:
                pass
"""})

s2 = {"file": "core/cfg/region_ast_generator.py", "edits": edits}
json.dump(s2, io.open(os.path.join(D, "probe14g.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5z %s %s"
        % (G, os.path.join(D, "probe14g.json"), os.path.join(D, "ad5.json")))
print(r.stdout, r.stderr)
dbgf = os.path.join(G, "fix2", "dump", "pz.txt")
if os.path.exists(dbgf):
    os.remove(dbgf)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5z "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s %s\\fix2\\dump\\ecafgd5z_tiu.py" % (G, dbgf, G))
print(r.stdout, r.stderr)
print("----")
txt = io.open(dbgf, encoding="utf-8").read()
import re
for m in re.finditer(r"^  (R75E |MAIN598|TRYBODY|CALL598|ADD598).*?(?=^  (R75E |MAIN598|TRYBODY|CALL598|ADD598)|\Z)",
                     txt, re.S | re.M):
    print(m.group(0)[:1400])
    print(".......")
