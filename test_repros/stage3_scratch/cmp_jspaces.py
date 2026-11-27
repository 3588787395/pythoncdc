# -*- coding: utf-8 -*-
import hashlib
import json
import os

REPO = r"F:\Downloads\pythoncdc-main"
BASE = os.path.join(REPO, ".trae", "specs", "achieve-any-syntax-completeness",
                    "rounds", "round13")
CANDS = [
    os.path.join(BASE, "jspace_v3", "judgment_space_v3.json"),
    os.path.join(BASE, "jspace_v3", "fresh", "judgment_space_v3m.json"),
    os.path.join(BASE, "jspace_v3", "fresh", "judgment_space_v3m_applied.json"),
    os.path.join(BASE, "jspace_v3", "fresh", "judgment_space_v3a.json"),
    os.path.join(BASE, "jspace_v3", "fresh", "judgment_space_v3r.json"),
    os.path.join(BASE, "jspace_v3", "fresh", "judgment_space_v3m_applied_v5r79.json"),
]

for p in CANDS:
    d = json.load(open(p, encoding="utf-8-sig"))
    es = d["entries"] if isinstance(d, dict) else d
    stat = {}
    idset = []
    pj_missing = 0
    pj_first = None
    for e in es:
        stat[e.get("status", "?")] = stat.get(e.get("status", "?"), 0) + 1
        idset.append(e["id"])
        pj = e.get("p_j")
        if pj and pj_first is None:
            pj_first = pj
        if pj and not os.path.exists(os.path.join(REPO, pj.replace("/", os.sep))):
            pj_missing += 1
    row = e
    print(os.path.basename(p))
    print("  entries=%d statuses=%s p_j_missing=%d" % (len(es), stat, pj_missing))
    print("  first_pj=%s row=%s j_schema=%s" % (pj_first, row.get("row"),
                                                row.get("j_schema_version")))
    print("  ids_sha=%s" % hashlib.sha256("|".join(idset).encode()).hexdigest()[:16])
    extra = {k: v for k, v in d.items() if k != "entries"} if isinstance(d, dict) else {}
    keys = list(extra.keys())
    print("  top_keys=%s" % keys[:8])
