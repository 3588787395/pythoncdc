import json
d = r".trae/specs/attain-true-completeness/rounds/round5/"
for f in ["rec1_probes_r5synth.json", "rec1_probes_r5synth3.json",
          "rec1_probes_r5synthg4a.json", "rec1_probes_r5synthg4b.json",
          "rec1_probes_r5synthg4c.json", "rec1_probes_r5synthg4d.json"]:
    j = json.load(open(d + f, encoding="utf-8"))
    rows = j["rows"] if isinstance(j, dict) and "rows" in j else j
    out = []
    for r in rows:
        out.append("{}:{},{}/{}".format(r.get("name"), r.get("status"),
                                        r.get("units_success"), r.get("units_total")))
    print(f, "=>", "; ".join(out))
    for r in rows:
        txt = (r.get("stdout") or "") + (r.get("stderr") or "")
        for line in txt.splitlines():
            if "***" in line:
                print("    ", line.strip()[:150])
