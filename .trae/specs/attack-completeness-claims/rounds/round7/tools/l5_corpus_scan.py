"""L5: corpus (402 certified artifacts) form / scale scan.

Two planes per artifact:

* **bytecode plane** on the original ``.pyc`` -- authoritative for the input
  the product actually faced.  Available for 402/402.
* **source plane** on the product output ``*OK.py`` -- available for 402/402,
  but it measures the *product's* output, i.e. a **lower bound** proxy for the
  original source (397/402 original sources no longer exist in the repo).

Output: logs/l5_corpus_forms.json
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

SHARD_DIR = os.path.join(
    REPO, ".trae", "specs", "adversarial-complete-forms-v2-10rounds", "baseline", "shards"
)
OUT = os.path.join(ROUND, "logs", "l5_corpus_forms.json")


def main() -> int:
    try:
        from xdis.bytecode import parse_exception_table as xdis_parse
        have_xdis = True
    except Exception:
        have_xdis = False
    xdis_mismatch = 0
    xdis_checked = 0
    paths = []
    for i in range(8):
        p = os.path.join(SHARD_DIR, "shard%d.json" % i)
        with open(p, encoding="utf-8") as fh:
            for it in json.load(fh):
                paths.append(it["path"])
    seen = set()
    uniq = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            uniq.append(p)

    records = []
    missing = []
    no_src = 0
    empty_src = 0
    no_product = 0
    for p in uniq:
        local = p
        if not os.path.exists(local):
            alt = os.path.join(REPO, "site-packages", os.path.relpath(p, "site-packages"))
            if os.path.exists(alt):
                local = alt
            else:
                missing.append(p)
                continue
        code = F.load_pyc_code(local)
        if code is None:
            missing.append(p)
            continue
        rec = {"path": p.replace("\\", "/"),
               "local": os.path.relpath(local, REPO).replace("\\", "/")}
        rec["bytecode"] = F.bytecode_features(code)
        if have_xdis:
            for co in F.iter_code(code):
                tbl = getattr(co, "co_exceptiontable", b"")
                if not tbl:
                    continue
                xdis_checked += 1
                mine = [(s, e, t, d) for (s, e, t, d) in F._exc_entries(co)]
                theirs = [(x.start, x.end, x.target, x.depth)
                          for x in xdis_parse(tbl)]
                if mine != theirs:
                    xdis_mismatch += 1
        sp = local[:-4] + ".py"
        if os.path.exists(sp):
            if os.path.getsize(sp) == 0:
                # existence is not availability: the five surviving .py files
                # in the repo are 0-byte placeholders (found in this round)
                rec["source_original"] = None
                rec["source_original_empty"] = True
                empty_src += 1
            else:
                try:
                    with open(sp, encoding="utf-8", errors="replace") as fh:
                        rec["source_original"] = F.source_features(fh.read())
                except Exception as exc:
                    rec["source_original"] = None
                    rec["source_original_error"] = str(exc)
        else:
            rec["source_original"] = None
            no_src += 1
        prod = local[:-4] + "OK.py"
        if os.path.exists(prod):
            try:
                with open(prod, encoding="utf-8", errors="replace") as fh:
                    rec["source"] = F.source_features(fh.read())
            except Exception as exc:
                rec["source"] = None
                rec["source_error"] = str(exc)
        else:
            rec["source"] = None
            no_product += 1
        records.append(rec)

    payload = {
        "tool": "l5_corpus_scan.py",
        "corpus": "402 certified artifacts (adversarial-complete-forms-v2-10rounds/"
                  "baseline/shards/shard0..7.json)",
        "python": sys.version,
        "plane_notes": {
            "bytecode": "original .pyc (authoritative for the product's input)",
            "source": "product output *OK.py (LOWER BOUND proxy: the product can drop "
                      "forms - see ATTACK_L4_RUNTIME B202/B203/B208 - but does not invent them)",
            "source_original": "original .py: 5/402 files exist but all are "
                                "0-byte placeholders; effective availability = 0/402",
            "plane_limits": F.PLANE_LIMITS,
        },
        "summary_bytecode": F.summarize(records, "bytecode"),
        "summary_source_product": F.summarize(records, "source"),
        "n_records": len(records),
        "xdis_exception_table_crosscheck": {
            "checked_code_objects": xdis_checked,
            "mismatches": xdis_mismatch,
            "note": "xdis.bytecode.parse_exception_table is the parser the "
                    "pylingual judge uses for exception tables; "
                    "mismatches=0 => this audit reads exception tables exactly "
                    "like the ruler does",
        },
        "missing": missing,
        "source_original_missing": no_src,
        "source_original_empty": empty_src,
        "source_original_files_present": empty_src + sum(
            1 for r in records if r.get("source_original")),
        "source_original_available": sum(1 for r in records if r.get("source_original")),
        "product_output_available": sum(1 for r in records if r.get("source")),
        "records": records,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    sb = payload["summary_bytecode"]
    ss = payload["summary_source_product"]
    print("corpus scanned:", len(records), "missing:", len(missing),
          "original src available:", payload["source_original_available"],
          "present:", payload["source_original_files_present"],
          "empty:", payload["source_original_empty"],
          "product out:", payload["product_output_available"])
    print("-- bytecode-plane presence %")
    for k, v in sorted(sb["presence_pct"].items(), key=lambda kv: -kv[1]):
        print("   %-20s %6.2f%%" % (k, v))
    print("-- product-output source-plane presence %")
    for k, v in sorted(ss["presence_pct"].items(), key=lambda kv: -kv[1]):
        print("   %-20s %6.2f%%" % (k, v))
    print("-- bytecode scale", json.dumps(sb["max_func_instr"], ensure_ascii=False),
          json.dumps(sb["max_exc_table_depth"], ensure_ascii=False))
    print("-- product-output scale", json.dumps(ss["max_func_stmts"], ensure_ascii=False),
          json.dumps(ss["max_nest_depth"], ensure_ascii=False),
          json.dumps(ss["max_expr_width"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
