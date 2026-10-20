import json
d = r".trae/specs/attain-true-completeness/rounds/round5/"
for f in ["rec1_probes_r5_b93_fix.json", "rec1_probes_r5post4_neigh.json",
          "rec1_probes_r5post5_neg9.json", "rec1_probes_r5post6_r4prot.json",
          "rec1_probes_r5t1_b93tgt.json", "rec1_probes_r5_b122_fix.json"]:
    j = json.load(open(d + f, encoding="utf-8"))
    rows = j["rows"] if isinstance(j, dict) and "rows" in j else j
    out = []
    for r in rows:
        out.append("{}:{}:{}/{}".format(r.get("name"), r.get("status"),
                                        r.get("units_success"), r.get("units_total")))
    print(f, "=>", "; ".join(out)[:600])
