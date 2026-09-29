import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
REPO = r"F:\Downloads\pythoncdc-main"
D = r"D:\Temp\opencode\r75gate\fix2\specs"
G = r"D:\Temp\opencode\r75gate"

ede = json.load(io.open(os.path.join(D, "ede.json"), encoding="utf-8"))
e = dict(ede["edits"][0])
add = """
            import os as _osE, io as _dioE
            _dpE = _osE.environ.get('R75DBG')
            _dfE = _dioE.open(_dpE, 'a', encoding='utf-8') if _dpE else None
            if _dfE is not None:
                _dfE.write('  R75E enter n_eff=%s hmin=%s tstart=%s\\n' % (
                    len(_try_blocks_eff), _r75e_hmin, region.try_offset_start))
            for _tb in list(_try_blocks_eff):
                _tb_last = _tb.get_last_instruction()
                if _tb_last is None or 'FOR_ITER' not in _tb_last.opname:
                    continue
                for _succ in _tb.successors:
                    _roleE = self.region_analyzer.get_block_role(_succ)
                    _in_eff = _succ.start_offset in _already_in_eff
                    _in_h = _succ.start_offset in _handler_block_offsets
                    _in_rng = (region.try_offset_start is not None
                               and region.try_offset_start <= _succ.start_offset < _r75e_hmin)
                    if _dfE is not None:
                        _dfE.write('  R75E cand tb=%s succ=%s role=%s in_eff=%s in_h=%s in_rng=%s\\n' % (
                            _tb.start_offset, _succ.start_offset, _roleE, _in_eff, _in_h, _in_rng))
                    if _in_eff or _in_h or not _in_rng:
                        continue
                    if _roleE not in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                        continue
                    _try_blocks_eff.append(_succ)
                    _already_in_eff.add(_succ.start_offset)
                    if _dfE is not None:
                        _dfE.write('  R75E PULLED %s\\n' % _succ.start_offset)
            if _dfE is not None:
                _dfE.close()
"""
repl = e["repl"]
marker = "        for block in sorted(_try_blocks_eff, key=lambda b: b.start_offset):\n"
assert repl.endswith(marker), repr(repl[-120:])
e["repl"] = repl[: -len(marker)] + add + marker
p2 = {"file": "core/cfg/region_ast_generator.py",
      "edits": list(json.load(io.open(os.path.join(D, "ec_ge.json"), encoding="utf-8"))["edits"])[:-1] + [e]}
json.dump(p2, io.open(os.path.join(D, "ec_gep.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5ep %s %s"
        % (G, os.path.join(D, "ec_gep.json"), os.path.join(D, "ad5.json")))
print(r.stdout, r.stderr)
dbgf = os.path.join(G, "fix2", "dump", "ep.txt")
if os.path.exists(dbgf):
    os.remove(dbgf)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5ep "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s %s\\fix2\\dump\\ecafgd5ep_tiu.py" % (G, dbgf, G))
print(r.stdout, r.stderr)
print("----")
txt = io.open(dbgf, encoding="utf-8").read()
for line in txt.split("\n"):
    if "R75E" in line:
        print(line)
