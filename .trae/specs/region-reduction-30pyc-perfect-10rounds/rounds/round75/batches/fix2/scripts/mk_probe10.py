import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Temp\opencode\r75gate\fix2\specs"
G = r"D:\Temp\opencode\r75gate"

ad5 = json.load(io.open(os.path.join(D, "ad5.json"), encoding="utf-8"))


def gated(label, anchor, exprs=()):
    n = len(exprs)
    fmt = "  G" + label + " has598=%s ntry=%s" + (", %s" * n) + "\\n"
    args = ", ".join(["598 in _offs9", "len(_offs9)"] + list(exprs))
    body = (
        "            _cfg9 = getattr(self, 'cfg', None)\n"
        "            _code9 = getattr(_cfg9, 'code', None)\n"
        "            if getattr(_code9, 'co_name', None) == 'get_trade_status':\n"
        "                _offs9 = [b.start_offset for b in try_blocks]\n"
        "                import os as _os9, io as _dio9\n"
        "                _dp9 = _os9.environ.get('R75DBG')\n"
        "                if _dp9:\n"
        "                    with _dio9.open(_dp9, 'a', encoding='utf-8') as _df9:\n"
        "                        _df9.write('" + fmt + "' % (" + args + "))\n")
    return {"anchor": anchor, "repl": body + anchor}


anchors = [
    gated("base",
          "            # Track the try-body entry candidate from pre_handler_blocks expansion.\n",
          ("try_start_for_blocks", "try_end_for_blocks")),
    gated("expanded",
          "                if len(_expanded_try) > len(try_blocks):\n"
          "                    try_blocks = _expanded_try\n"),
    gated("before-excl",
          "            if exclude_from_try:\n"
          "                try_blocks = [b for b in try_blocks if b not in exclude_from_try]\n"),
    gated("appended",
          "            if cleanup_blocks:\n"
          "                region.cleanup_blocks = cleanup_blocks\n"
          "\n"
          "            self.regions.append(region)\n",
          ("region.try_offset_start", "region.try_offset_end",
           "598 in set(region.try_blocks)", "598 in set(region.blocks)")),
]

src = io.open(r"F:\Downloads\pythoncdc-main\core\cfg\region_analyzer.py",
              encoding="utf-8").read()
for a in anchors:
    print("anchor count:", src.count(a["anchor"]))

ad5r = {"file": "core/cfg/region_analyzer.py",
        "edits": list(ad5["edits"]) + anchors}
json.dump(ad5r, io.open(os.path.join(D, "ad5r.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py ec_afgd5q %s %s"
        % (G, os.path.join(D, "ec_gep.json"), os.path.join(D, "ad5r.json")))
print(r.stdout, r.stderr)
dbgf = os.path.join(G, "fix2", "dump", "eq.txt")
if os.path.exists(dbgf):
    os.remove(dbgf)
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afgd5q "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s %s\\fix2\\dump\\ecafgd5q_tiu.py" % (G, dbgf, G))
print(r.stdout, r.stderr)
print("----")
txt = io.open(dbgf, encoding="utf-8").read()
for line in txt.split("\n"):
    if "R75E" in line or " G" in line[:6]:
        print(line)
