import json
import os
import sys
import subprocess

sys.stdout.reconfigure(encoding="utf-8")
D = r"D:\Temp\opencode\r75gate\fix2\specs"
parts = ["grp_g.json", "editc9.json"]
edits = []
file = None
for p in parts:
    s = json.load(io_open := __import__("io").open(os.path.join(D, p), encoding="utf-8"))
    if file is None:
        file = s["file"]
    assert s["file"] == file, (p, s["file"])
    edits.extend(s["edits"])
out = os.path.join(D, "ec_g.json")
json.dump({"file": file, "edits": edits},
          __import__("io").open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", out, "edits", len(edits))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


r = run("python -W ignore -X utf8 D:\\Temp\\opencode\\r75gate\\center\\mbuild74.py "
        "ec_afg %s %s" % (out, os.path.join(D, "pad8_1f.json")))
print(r.stdout, r.stderr)
G = r"D:\Temp\opencode\r75gate"
r = run("python -W ignore -X utf8 %s\\fix2\\run_dbg.py ec_afg "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "%s\\fix2\\dump\\ecafg.txt %s\\fix2\\dump\\ecafg_tiu.py" % (G, G, G))
print(r.stdout)
r = run("python -W ignore -X utf8 F:\\Downloads\\pythoncdc-main\\scripts\\pyc_verify.py single "
        "F:\\Downloads\\pythoncdc-main\\site-packages\\IQCommon\\util\\trade_info_utils.pyc "
        "--source %s\\fix2\\dump\\ecafg_tiu.py" % G)
print(r.stdout)
