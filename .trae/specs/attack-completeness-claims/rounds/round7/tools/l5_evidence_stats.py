"""L5: derive the evidence-layer statistics quoted in ATTACK_L5_EVIDENCE.md.

Reads the raw round7 logs (l5_corpus_forms.json, l5_probe_forms.json,
l5_selftest.json, l5_drift_*.json) and writes a single derived-statistics
artifact so every number in the report is reproducible from the repo.

Output: logs/l5_evidence_stats.json
"""

from __future__ import annotations

import collections
import glob
import json
import os
import statistics

HERE = os.path.dirname(os.path.abspath(__file__))
ROUND = os.path.dirname(HERE)
LOGS = os.path.join(ROUND, "logs")


def load(name):
    with open(os.path.join(LOGS, name), encoding="utf-8") as fh:
        return json.load(fh)


def pct(n, d):
    return round(100.0 * n / d, 2) if d else None


def unit_stats(rows):
    units = [r["units_total"] for r in rows if isinstance(r.get("units_total"), int)]
    units_sorted = sorted(units)
    total = sum(units)
    return {
        "files": len(units),
        "units_total": total,
        "min": min(units),
        "p50": statistics.median(units),
        "p90": units_sorted[int(len(units) * 0.9)],
        "p99": units_sorted[int(len(units) * 0.99)],
        "max": max(units),
        "mean": round(statistics.mean(units), 2),
        "files_le_1": sum(1 for u in units if u <= 1),
        "files_le_2": sum(1 for u in units if u <= 2),
        "files_le_3": sum(1 for u in units if u <= 3),
        "files_le_5": sum(1 for u in units if u <= 5),
        "files_le_10": sum(1 for u in units if u <= 10),
        "units_in_files_le_3": sum(u for u in units if u <= 3),
        "units_in_files_le_10": sum(u for u in units if u <= 10),
        "top10_units": sum(sorted(units, reverse=True)[:10]),
        "single_unit_files": sum(1 for u in units if u == 1),
        "single_unit_pct": pct(sum(1 for u in units if u == 1), len(units)),
        "top10_unit_share_pct": pct(sum(sorted(units, reverse=True)[:10]), total),
    }


def form_dist(records, plane, keys):
    dist = []
    for r in records:
        obj = r.get(plane)
        if not obj:
            continue
        feats = obj["features"]
        dist.append(sum(1 for k in keys if feats.get(k, 0) > 0))
    dist.sort()
    return {
        "n": len(dist),
        "min": dist[0],
        "p50": statistics.median(dist),
        "p90": dist[int(len(dist) * 0.9)],
        "max": dist[-1],
        "mean": round(statistics.mean(dist), 2),
        "files_le_3": sum(1 for d in dist if d <= 3),
        "files_le_3_pct": pct(sum(1 for d in dist if d <= 3), len(dist)),
    }


def main() -> int:
    corp = load("l5_corpus_forms.json")
    probe = load("l5_probe_forms.json")
    selftest = load("l5_selftest.json")

    keys = list(corp["summary_bytecode"]["presence_pct"].keys())
    corp_recs = corp["records"]
    probe_recs = probe["records"]
    stamped = [r for r in probe_recs if r["kind"] == "stamped"]
    source_only = [r for r in probe_recs if r["kind"] == "source_only"]

    drift_rows = []
    for f in sorted(glob.glob(os.path.join(LOGS, "l5_drift_*.json"))):
        with open(f, encoding="utf-8") as fh:
            drift_rows.extend(json.load(fh)["rows"])
    units = unit_stats(drift_rows)

    corpus_original_present = sum(
        1 for r in corp_recs
        if r.get("source_original") or r.get("source_original_empty"))
    empty_original = sum(1 for r in corp_recs if r.get("source_original_empty"))
    no_function = sum(1 for r in corp_recs if r["bytecode"]["max_func_instr"] == 0)
    zero_bc = [k for k in keys if corp["summary_bytecode"]["presence_pct"].get(k, 0) == 0]
    zero_src = [k for k in keys if corp["summary_source_product"]["presence_pct"].get(k, 0) == 0]
    zero_probe_bc = [k for k in keys if probe["summary_bytecode"]["presence_pct"].get(k, 0) == 0]
    zero_probe_src = [k for k in keys if probe["summary_source"]["presence_pct"].get(k, 0) == 0]

    SPECS = os.path.abspath(os.path.join(ROUND, "..", "..", ".."))
    stamp_entries = 0
    for root in (os.path.join(SPECS, "attain-true-completeness"),
                 os.path.join(SPECS, "attack-completeness-claims")):
        for f in glob.glob(os.path.join(root, "**", "rec1_probes*.json"),
                           recursive=True):
            try:
                with open(f, encoding="utf-8") as fh:
                    d = json.load(fh)
                if isinstance(d, list):
                    stamp_entries += len(d)
            except Exception:
                pass

    stamp_refs = collections.Counter()
    for r in stamped:
        for name in r.get("stamps") or []:
            stamp_refs[name] += 1
    max_stamps_per_artifact = max((len(r.get("stamps") or []) for r in stamped),
                                  default=0)

    payload = {
        "tool": "l5_evidence_stats.py",
        "sources": [
            "l5_corpus_forms.json", "l5_probe_forms.json",
            "l5_selftest.json", "l5_drift_*.json",
        ],
        "corpus": {
            "n_records": len(corp_recs),
            "missing": len(corp["missing"]),
            "source_original_missing": corp.get("source_original_missing"),
            "source_original_empty": empty_original,
            "source_original_files_present": corpus_original_present,
            "source_original_available": corp.get("source_original_available"),
            "product_output_available": corp.get("product_output_available"),
            "no_function_code_object": no_function,
            "no_function_code_object_pct": pct(no_function, len(corp_recs)),
            "bytecode_zero_forms": zero_bc,
            "bytecode_zero_form_count": len(zero_bc),
            "product_source_zero_forms": zero_src,
            "product_source_zero_form_count": len(zero_src),
            "bytecode_forms_per_file": form_dist(corp_recs, "bytecode", keys),
            "product_source_forms_per_file": form_dist(corp_recs, "source", keys),
            "units": units,
        },
        "probe": {
            "stamp_files": probe["stamp_files"],
            "stamped": len(stamped),
            "source_only": len(source_only),
            "stamped_with_source": sum(1 for r in stamped if r.get("source")),
            "stamped_without_source": sum(1 for r in stamped if not r.get("source")),
            "source_only_with_source": sum(1 for r in source_only if r.get("source")),
            "stamp_entries": stamp_entries,
            "entries_per_unique_artifact": round(stamp_entries / len(stamped), 2),
            "unique_stamp_names": len(stamp_refs),
            "resolved_stamp_refs": sum(stamp_refs.values()),
            "resolved_refs_per_unique_artifact": round(
                sum(stamp_refs.values()) / len(stamped), 2),
            "max_artifacts_per_stamp": max(stamp_refs.values(), default=0),
            "max_stamps_per_artifact": max_stamps_per_artifact,
            "bytecode_zero_forms": zero_probe_bc,
            "bytecode_zero_form_count": len(zero_probe_bc),
            "source_zero_forms": zero_probe_src,
            "source_zero_form_count": len(zero_probe_src),
            "bytecode_forms_per_file": form_dist(stamped, "bytecode", keys),
            "source_forms_per_file": form_dist(
                [r for r in probe_recs if r.get("source")], "source", keys),
            "bytecode_max_code_instr": probe["summary_bytecode"]["max_code_instr"],
            "source_max_func_stmts": probe["summary_source"]["max_func_stmts"],
        },
        "selftest": {
            "n_samples": selftest["n_samples"],
            "n_failures": selftest["n_failures"],
            "source_only_ground_truths": 3,
            "negative_controls": 1,
        },
        "drift": {
            "files": len(drift_rows),
            "statuses": dict(collections.Counter(r["status"] for r in drift_rows)),
            "units_success": sum(r.get("units_success") or 0 for r in drift_rows),
            "units_total": sum(r.get("units_total") or 0 for r in drift_rows),
        },
    }
    out = os.path.join(LOGS, "l5_evidence_stats.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=1)
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
