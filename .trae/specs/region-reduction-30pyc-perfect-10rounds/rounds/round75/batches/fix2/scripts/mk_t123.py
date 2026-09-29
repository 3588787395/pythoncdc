import io
import json
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
G = r"D:\Temp\opencode\r75gate"
D = os.path.join(G, "fix2", "specs")
ad5 = json.load(io.open(os.path.join(D, "ad5.json"), encoding="utf-8"))
ecg = json.load(io.open(os.path.join(D, "ec_g.json"), encoding="utf-8"))
E = ad5["edits"]
assert len(E) == 4, len(E)
groups = {
    "t_A": [E[2]],            # pad8_1f (edit-A)
    "t_D": [E[0], E[1]],      # edit-D head + carve-out
    "t_D2": [E[3]],           # edit-D2
}
for name, eds in groups.items():
    spec = {"file": "core/cfg/region_analyzer.py", "edits": eds}
    json.dump(spec, io.open(os.path.join(D, name + ".json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(name, "edits", len(eds))


def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


for name in groups:
    arm = "ecg_" + name
    r = run("python -W ignore -X utf8 %s\\center\\mbuild74.py %s %s %s"
            % (G, arm, os.path.join(D, "ec_g.json"), os.path.join(D, name + ".json")))
    print(arm, (r.stdout or "").strip().splitlines()[-1] if r.stdout else r.stderr.strip())
    r = run("python -W ignore -X utf8 %s\\center\\h62.py run --arm=%s --list=%s "
            "--out=%s" % (G, arm, os.path.join(D, "..", "dump", "list1_asset.txt"),
                          os.path.join(D, "..", "dump", "p1_asset_%s.jsonl" % name)))
    print("   ", (r.stdout or "").strip(), r.stderr.strip()[:200])
