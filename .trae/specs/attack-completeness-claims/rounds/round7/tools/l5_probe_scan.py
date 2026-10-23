"""L5: probe corpus scan (all probes that ever produced a recorded verdict).

The probe corpus is collected from two places:

* **P1 -- stamped probes**: every ``pyc_src_rel`` appearing in a recorded
  probe stamp (``rec1_probes_*.json`` and friends) under
  ``.trae/specs/attain-true-completeness/rounds/**`` and
  ``.trae/specs/attack-completeness-claims/rounds/**``.  These are exactly the
  artifacts whose verdict was recorded, i.e. the evidence base of the
  completeness claim.
* **P2 -- probe sources**: every ``*.py`` under the probe directories of both
  spec trees (sources that were written but whose stamp may be missing).

Output: logs/l5_probe_forms.json
"""

from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(ROUND, "..", "..", "..", "..", ".."))
sys.path.insert(0, HERE)

import l5_features as F  # noqa: E402

SPECS = os.path.join(REPO, ".trae", "specs")
OUT = os.path.join(ROUND, "logs", "l5_probe_forms.json")

PROBE_DIR_MARKERS = ("probe", "repro", "test_repros", "boundary")
# the round-4 mutation corpus is *not* a probe corpus: those files are
# deliberately corrupted artifacts used to measure the judge, not evidence
# for the product.  They are excluded from P2 (and reported separately).
MUTATION_DIR_MARKERS = (os.sep + "_probes" + os.sep + "miss",
                        os.sep + "_probes" + os.sep + "mut",
                        os.sep + "_out" + os.sep)


def find_stamps() -> list:
    out = []
    for root in (os.path.join(SPECS, "attain-true-completeness"),
                 os.path.join(SPECS, "attack-completeness-claims")):
        for dp, dn, fn in os.walk(root):
            if "__pycache__" in dp:
                continue
            for f in fn:
                if f.startswith("rec1_probes") and f.endswith(".json"):
                    out.append(os.path.join(dp, f))
    return out


def find_probe_sources() -> list:
    out = []
    for root in (os.path.join(SPECS, "attain-true-completeness"),
                 os.path.join(SPECS, "attack-completeness-claims")):
        for dp, dn, fn in os.walk(root):
            if "__pycache__" in dp:
                continue
            parts = os.path.relpath(dp, root).split(os.sep)
            if not any(m in p for p in parts for m in PROBE_DIR_MARKERS):
                continue
            if "tools" in parts or "tools" in os.path.basename(dp):
                continue
            if any(m in dp for m in MUTATION_DIR_MARKERS):
                continue
            for f in fn:
                if not f.endswith(".py") or f.endswith("OK.py"):
                    continue
                out.append(os.path.join(dp, f))
    return out


def main() -> int:
    stamps = find_stamps()
    stamped = {}
    stamp_files = 0
    for sp in stamps:
        try:
            with open(sp, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            continue
        if not isinstance(data, list):
            continue
        stamp_files += 1
        for it in data:
            if not isinstance(it, dict):
                continue
            cands = []
            for key in ("pyc_src_rel", "staged_pyc", "pyc_src"):
                v = it.get(key)
                if v:
                    cands.append(v.replace("\\", "/"))
            if not cands:
                continue
            resolved = None
            for c in cands:
                for p in (c, os.path.join(REPO, c)):
                    if os.path.exists(p):
                        resolved = p
                        break
                if resolved:
                    break
            if resolved is None:
                base = os.path.basename(cands[0])
                hits = []
                for base_dir, _dn, fns in os.walk(SPECS):
                    if base in fns:
                        hits.append(os.path.join(base_dir, base))
                    if len(hits) > 3:
                        break
                if hits:
                    resolved = hits[0]
            key = resolved.replace("\\", "/") if resolved else cands[0]
            stamped.setdefault(key, []).append(os.path.basename(sp))

    records = []
    missing = []
    n_stamped = 0
    for rel, srcs in sorted(stamped.items()):
        p = rel if os.path.isabs(rel) else os.path.join(REPO, rel)
        if not os.path.exists(p):
            missing.append(rel)
            continue
        code = F.load_pyc_code(p)
        if code is None:
            missing.append(rel)
            continue
        n_stamped += 1
        rec = {"kind": "stamped", "path": rel,
               "stamps": sorted(set(srcs)),
               "bytecode": F.bytecode_features(code)}
        sp = p[:-4] + ".py"
        if os.path.exists(sp):
            try:
                with open(sp, encoding="utf-8", errors="replace") as fh:
                    rec["source"] = F.source_features(fh.read())
            except Exception as exc:
                rec["source"] = None
                rec["source_error"] = str(exc)
        else:
            rec["source"] = None
        records.append(rec)

    n_src_only = 0
    for sp in sorted(set(find_probe_sources())):
        rel = os.path.relpath(sp, REPO).replace("\\", "/")
        if any(r["path"].endswith(os.path.basename(sp)) and
               os.path.splitext(r["path"])[0].endswith(os.path.splitext(rel)[0][:40])
               for r in records):
            pass
        try:
            with open(sp, encoding="utf-8", errors="replace") as fh:
                src = fh.read()
            sf = F.source_features(src)
        except Exception:
            continue
        # skip if a stamped record already covers the same file
        base = os.path.splitext(rel)[0]
        if any(os.path.splitext(r["path"])[0] == base for r in records):
            continue
        n_src_only += 1
        records.append({"kind": "source_only", "path": rel, "source": sf,
                        "bytecode": None})

    payload = {
        "tool": "l5_probe_scan.py",
        "python": sys.version,
        "probe_definition": {
            "P1_stamped": "every pyc_src_rel in a recorded probe stamp "
                          "(rec1_probes_*.json) -- the artifacts whose verdict "
                          "was recorded",
            "P2_source_only": "probe .py sources found in probe directories that "
                              "are not covered by a stamped .pyc",
        },
        "stamp_files": stamp_files,
        "n_stamped_records": n_stamped,
        "n_source_only_records": n_src_only,
        "summary_bytecode": F.summarize([r for r in records if r.get("bytecode")],
                                        "bytecode"),
        "summary_source": F.summarize([r for r in records if r.get("source")],
                                      "source"),
        "missing": missing,
        "records": records,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    sb = payload["summary_bytecode"]
    ss = payload["summary_source"]
    print("stamp files:", stamp_files, "| stamped probes:", n_stamped,
          "| source-only probes:", n_src_only, "| missing:", len(missing))
    print("-- probe bytecode-plane presence %")
    for k, v in sorted(sb["presence_pct"].items(), key=lambda kv: -kv[1]):
        print("   %-20s %6.2f%%" % (k, v))
    print("-- probe source-plane presence %")
    for k, v in sorted(ss["presence_pct"].items(), key=lambda kv: -kv[1]):
        print("   %-20s %6.2f%%" % (k, v))
    print("-- probe source scale", json.dumps(ss["max_func_stmts"], ensure_ascii=False),
          json.dumps(ss["max_nest_depth"], ensure_ascii=False),
          json.dumps(ss["max_expr_width"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
