import json, sys

for name in ("r1_residual_replay.json", "r1_sentry_replay.json"):
    path = f".trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/{name}"
    r = json.load(open(path, encoding="utf-8"))
    print(f"=== {name} files={r['files_total']} units={r['units_success']}/{r['units_total']} ===")
    for row in r["rows"]:
        p = row["pyc"].replace("F:/Downloads/pythoncdc-main/", "").replace("test_repros/", "")
        fails = ";".join(f.replace("***", "").replace(": Failure", "") for f in row["failures"])
        print(f"{p}|{row['status']}|{row['units_success']}/{row['units_total']}|{fails}")
