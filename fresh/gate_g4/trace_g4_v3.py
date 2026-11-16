#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G4 v3 tracer: record *predicate-measured* rule hits, not anchor-line arrivals.

Why this file exists
--------------------
``traces_v2.json`` was produced by a line-coverage tracer (``coverage.py``): a
rule counts as "hit" for an entry as soon as the rule's **anchor line** is
reached.  Measured on the same 131 pyc runs, that over-counts by thousands of
``(run, rule)`` pairs whose predicate is false at every evaluation
(``fresh/gate_g4/G4_V1_READINGS.md`` §5.3).

This tracer keeps the same entry space (the frozen judgment space J) and the
same region pipeline, but records the *verdict of the rule predicate itself*:

    rules_true [entry_id] = rules whose predicate evaluated **true** at least
                            once while that J entry's pyc was reduced

Predicate rebuilding + evaluation is **imported** from
``tools/completeness/rule_proof_check.py`` (``build_rule_index``, ``_scan_file``,
``Measurer``); no predicate logic is re-implemented here.  This file only
(i) drives the 131 runs, (ii) adds an executed-code-object inventory used by
the G4 triage, and (iii) writes ``traces_v3.json``.

It never modifies ``universe_v2.json`` / ``manifest_v2.json`` /
``traces_v2.json`` / ``trace_g4_current.py``.

Output (all read-only inputs; new files only):

    --out            traces_v3.json           per-entry rules_true / rules_false
    --inventory-out  executed_inventory_v3.json  which anchor-file code objects
                                              actually ran (import phase + runs)
    --mirror-dir     optional copy of both files

CLI (cwd = repo root):

    python -X utf8 fresh/gate_g4/trace_g4_v3.py \
        --universe fresh/gate_g4/universe_v3.json \
        --jspace  .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json \
        --traces-v2 .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/gate_gap/traces_v2.json \
        --out fresh/gate_g4/traces_v3.json \
        --inventory-out fresh/gate_g4/executed_inventory_v3.json \
        --mirror-dir D:/temp/opencode/cl_layout/g4v2
"""

from __future__ import annotations

import argparse
import collections
import json
import marshal
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL_VERSION = "1.0.0"
TRACE_TOOL = "g4-predicate-aware-trace"


# --------------------------------------------------------------------------- #
# helpers (path/io only -- no predicate logic)
# --------------------------------------------------------------------------- #
def repo_root(start):
    cur = os.path.abspath(start)
    while not os.path.isdir(os.path.join(cur, "core", "cfg")):
        parent = os.path.dirname(cur)
        if parent == cur:
            raise SystemExit("cannot locate repo root (no core/cfg above %s)" % start)
        cur = parent
    return cur


def load(path):
    with open(path, "r", encoding="utf-8-sig") as fh:
        return json.load(fh)


def write_json(path, data, indent=1):
    if not path:
        return
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=indent)
        fh.write("\n")


# --------------------------------------------------------------------------- #
# measurer: rule_proof_check.Measurer + executed code-object inventory
# --------------------------------------------------------------------------- #
def make_measurer_class(rpc):
    class InventoryMeasurer(rpc.Measurer):
        """Same predicate evaluation as the v1 checker; also notes which code
        objects of the anchor files actually ran (for the D1/D2/D3 triage)."""

        def __init__(self, candidates_by_line, candidates, watch_files):
            rpc.Measurer.__init__(self, candidates_by_line, candidates)
            self.watch_files = {f for f in watch_files}
            # file -> { "<co_name>@<co_firstlineno>": {"name","firstlineno","phase":..} }
            self.keyed = {}
            self.seen_code = set()          # id(code) already recorded
            self.held = []                  # strong refs, prevents id reuse
            self.phase = "run"
            self.import_files = set()
            self.run_files = set()

        # -- inventory ------------------------------------------------------ #
        def _record(self, code):
            slot = id(code)
            if slot in self.seen_code:
                return
            self.seen_code.add(slot)
            self.held.append(code)
            try:
                f = rpc.norm(code.co_filename)
            except BaseException:
                return
            if f not in self.watch_files:
                return
            bucket = self.keyed.setdefault(f, {})
            key = "%s@%d" % (code.co_name, code.co_firstlineno)
            entry = bucket.get(key)
            if entry is None:
                entry = {"name": code.co_name, "firstlineno": code.co_firstlineno,
                         "phases": []}
                bucket[key] = entry
            if self.phase not in entry["phases"]:
                entry["phases"].append(self.phase)
            (self.import_files if self.phase == "import" else self.run_files).add(f)

        # -- trace hooks ---------------------------------------------------- #
        def global_trace(self, frame, event, arg):
            if event != "call":
                return None
            self._record(frame.f_code)
            if self._code_map(frame.f_code) is None:
                return None
            return self.local_trace

        # -- run control ---------------------------------------------------- #
        def begin_phase(self, pyc, phase="run"):
            self.phase = phase
            self.begin_run(pyc)

        def discard_run(self):
            """Drop the counters of a phase that is not a J entry run."""
            self.current_pyc = None
            self.run_resolved = set()
            self.run_true = collections.Counter()
            self.run_false = collections.Counter()
            self.run_true_ev = {}
            self.run_false_ev = {}

    return InventoryMeasurer


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="G4 predicate-aware tracer (v3)")
    parser.add_argument("--universe", required=True)
    parser.add_argument("--jspace", required=True)
    parser.add_argument("--traces-v2", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--inventory-out", default="")
    parser.add_argument("--mirror-dir", default="")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--version", action="version", version=TOOL_VERSION)
    args = parser.parse_args(argv)

    args.universe = os.path.abspath(args.universe)
    args.jspace = os.path.abspath(args.jspace)
    args.out = os.path.abspath(args.out)
    if args.inventory_out:
        args.inventory_out = os.path.abspath(args.inventory_out)
    if args.traces_v2:
        args.traces_v2 = os.path.abspath(args.traces_v2)

    root = repo_root(HERE)
    for path in (root, os.path.join(root, "tools", "completeness")):
        if path not in sys.path:
            sys.path.insert(0, path)
    os.chdir(root)

    import rule_proof_check as rpc          # predicate rebuilding + evaluation
    InventoryMeasurer = make_measurer_class(rpc)

    universe = load(args.universe)
    jspace = load(args.jspace)
    rules = universe.get("rules") or []
    rule_by_id = {r["rule_id"]: r for r in rules}

    # ---- rebuild the same candidates the v1 checker builds --------------- #
    _by_key, by_position = rpc.build_rule_index(universe)
    anchor_files = sorted({f for (f, _l, _k, _s) in by_position})
    candidates, unmapped = [], []
    parse_errors = {}
    for path in anchor_files:
        try:
            rpc._scan_file(path, by_position, candidates, unmapped)
        except BaseException as exc:
            parse_errors[path] = "%s: %s" % (type(exc).__name__, exc)
    candidates_by_line = collections.defaultdict(list)
    located = collections.Counter()
    for cand in candidates:
        candidates_by_line[(cand.file, cand.line)].append(cand)
        located[cand.rule_id] += 1

    meas = InventoryMeasurer(candidates_by_line, candidates, set(anchor_files))

    # ---- entry -> pyc map (same grouping the v1 checker uses) ------------- #
    entries = jspace.get("entries") or []
    entries_by_pyc = collections.OrderedDict()
    for entry in entries:
        pyc = str(entry.get("pyc") or "").replace("\\", "/")
        if pyc:
            entries_by_pyc.setdefault(pyc, []).append(entry)
    entry_by_id = {e["id"]: e for e in entries if e.get("id")}

    # ---- phase 0: import the pipeline while the inventory is listening ---- #
    started = time.perf_counter()
    meas.begin_phase("__import__", phase="import")
    sys.settrace(meas.global_trace)
    try:
        from core.cfg import build_cfg
        from core.cfg.region_ast_generator import RegionASTGenerator
        from core.cfg.ast_converter import CFGASTConverter
        from core.cfg.code_generator import CFGCodeGenerator
    finally:
        sys.settrace(None)
    meas.discard_run()

    # ---- 131 runs: the exact region pipeline, predicate-aware ------------ #
    run_failures = {}
    run_timing = {}
    runs = 0
    for pyc in sorted(entries_by_pyc):
        if not os.path.isfile(pyc):
            run_failures[pyc] = "pyc_missing"
            continue
        tick = time.perf_counter()
        try:
            with open(pyc, "rb") as fh:
                fh.read(16)
                code = marshal.load(fh)
            meas.begin_phase(pyc, phase="run")
            sys.settrace(meas.global_trace)
            try:
                cfg = build_cfg(code)
                gen = RegionASTGenerator(
                    cfg, top_level_code=code if code.co_name == "<module>" else None)
                ast_dict = gen.generate()
                py_ast = CFGASTConverter().convert(ast_dict)
                CFGCodeGenerator().generate(py_ast)
            finally:
                sys.settrace(None)
            meas.end_run()
            runs += 1
        except BaseException as exc:
            sys.settrace(None)
            meas.discard_run()
            run_failures[pyc] = "%s: %s" % (type(exc).__name__, exc)
        run_timing[pyc] = round(time.perf_counter() - tick, 3)
        if not args.quiet and runs and runs % 25 == 0:
            print("[trace_g4_v3] runs=%d/%d" % (runs, len(entries_by_pyc)), flush=True)

    # ---- per-entry records ------------------------------------------------ #
    records = []
    true_pair_total = 0
    false_pair_total = 0
    for pyc, members in sorted(entries_by_pyc.items()):
        r_true = sorted(meas.pyc_true.get(pyc, set()))
        r_false = sorted(meas.pyc_false_counts.get(pyc, {}).keys())
        r_eval = sorted(set(r_true) | set(r_false))
        true_pair_total += len(r_true) * len(members)
        false_pair_total += len(r_false) * len(members)
        for member in sorted(members, key=lambda e: e["id"]):
            records.append({
                "entry_id": member["id"],
                "rules_true": r_true,
                "rules_false": r_false,
                "rules_evaluated": r_eval,
                # predicate-aware "hit" list, the field downstream tools read:
                # a rule is hit only when its predicate measured TRUE.
                "rule_ids": r_true,
                "pyc": pyc,
            })
    records.sort(key=lambda r: r["entry_id"])

    all_true = set()
    all_false = set()
    for rec in records:
        all_true.update(rec["rules_true"])
        all_false.update(rec["rules_false"])
    never_true = [r for r in rules if r["rule_id"] not in all_true]
    never_true_located = [r for r in never_true if located.get(r["rule_id"], 0)]
    not_located = [r for r in rules if not located.get(r["rule_id"], 0)]

    # ---- comparison with traces_v2 (anchor arrival) ---------------------- #
    comparison = {}
    if args.traces_v2:
        v2 = load(args.traces_v2)
        v2_by_entry = {}
        v2_pairs = 0
        v2_hit_rules = set()
        for item in v2.get("records") or []:
            eid = item.get("entry_id") or item.get("id")
            rids = sorted(set(item.get("rule_ids") or []))
            if not eid:
                continue
            v2_by_entry[eid] = rids
            v2_pairs += len(rids)
            v2_hit_rules.update(rids)
        per_pyc_v2 = collections.defaultdict(set)
        for pyc, members in entries_by_pyc.items():
            for member in members:
                per_pyc_v2[pyc].update(v2_by_entry.get(member["id"], []))
        anchor_only_pairs = 0          # (run, rule): v2 hit, predicate never true
        true_pairs_v2_hit = 0          # (run, rule): v2 hit AND predicate true
        true_pairs_v2_miss = 0         # (run, rule): predicate true, v2 did not hit
        per_rule_anchor_only = collections.Counter()
        for pyc in sorted(entries_by_pyc):
            hit = per_pyc_v2.get(pyc, set())
            truth = meas.pyc_true.get(pyc, set())
            extra = hit - truth
            anchor_only_pairs += len(extra)
            true_pairs_v2_hit += len(hit & truth)
            true_pairs_v2_miss += len(truth - hit)
            for rid in extra:
                per_rule_anchor_only[rid] += 1
        # entry-level (each J entry, not each pyc) count, matching how
        # traces_v2 counts "rule_ids" lists
        entry_anchor_only = 0
        entry_true = 0
        for rec in records:
            v2r = set(v2_by_entry.get(rec["entry_id"], []))
            entry_anchor_only += len(v2r - set(rec["rules_true"]))
            entry_true += len(set(rec["rules_true"]))
        comparison = {
            "traces_v2_path": args.traces_v2.replace("\\", "/"),
            "traces_v2_entries": len(v2_by_entry),
            "traces_v2_rule_id_pairs_per_entry": v2_pairs,
            "traces_v2_rules_hit": len(v2_hit_rules),
            "traces_v3_rules_hit_true": len(all_true),
            "rules_hit_delta": len(v2_hit_rules) - len(all_true),
            "empty_cov_v2": len(rules) - len(v2_hit_rules),
            "empty_cov_v3": len(rules) - len(all_true),
            "run_rule_pairs": {
                "v2_hit_and_true": true_pairs_v2_hit,
                "v2_hit_but_predicate_never_true": anchor_only_pairs,
                "true_but_v2_not_hit": true_pairs_v2_miss,
            },
            "entry_rule_pairs": {
                "v3_true": entry_true,
                "v2_hit_but_not_true": entry_anchor_only,
            },
            "rules_anchor_only_ranked": [
                {"rule_id": rid, "runs_hit_but_never_true": n,
                 "kind": (rule_by_id.get(rid) or {}).get("kind"),
                 "symbol": (rule_by_id.get(rid) or {}).get("symbol"),
                 "anchor": (rule_by_id.get(rid) or {}).get("anchor")}
                for rid, n in per_rule_anchor_only.most_common(20)],
        }

    summary = {
        "distinct_pyc_runs": runs,
        "distinct_pyc": len(entries_by_pyc),
        "entries": len(records),
        "run_failures": len(run_failures),
        "rules_total": len(rules),
        "rules_hit_true": len(all_true),
        "rules_false_at_site": len(all_false),
        "rules_hit_true_and_false": len(all_true & all_false),
        "empty_cov_true": len(never_true),
        "empty_cov_true_with_located_predicate": len(never_true_located),
        "rules_predicate_not_located": len(not_located),
        "rules_predicate_never_evaluated": sum(
            1 for r in rules if not meas.evaluations.get(r["rule_id"], 0)
            and located.get(r["rule_id"], 0)),
        "predicate_evaluations": sum(meas.evaluations.values()),
        "predicate_evaluations_true": sum(meas.evaluations_true.values()),
        "predicate_evaluations_false": sum(meas.evaluations_false.values()),
        "predicate_evaluation_errors": sum(meas.errors.values()),
        "run_rule_pairs_true": true_pair_total,
        "run_rule_pairs_false": false_pair_total,
        "candidates_located": len(candidates),
        "declared_anchors": len(by_position),
        "anchor_files": anchor_files,
        "parse_errors": parse_errors,
        "unmapped_source_predicates": len(unmapped),
        "run_failures_detail": run_failures,
        "runtime_seconds_pipeline": round(sum(run_timing.values()), 1),
        "elapsed_seconds": round(time.perf_counter() - started, 1),
    }

    payload = {
        "tool": TRACE_TOOL,
        "version": TOOL_VERSION,
        "note": ("Predicate-aware replay of the 131 J pycs: a rule is recorded as hit "
                 "only when its predicate (rebuilt from the universe kind+symbol at "
                 "the declared anchor and evaluated on the live frame by "
                 "tools/completeness/rule_proof_check.py) measured TRUE. "
                 "rules_false lists rules measured false at least once. "
                 "NEEDS REVIEW -- this is a measurement, not a G4 verdict."),
        "universe": args.universe.replace("\\", "/"),
        "universe_rules": len(rules),
        "jspace": args.jspace.replace("\\", "/"),
        "inputs": {
            "universe_sha256": rpc.file_sha256(args.universe),
            "jspace_sha256": rpc.file_sha256(args.jspace),
        },
        "summary": summary,
        "comparison_with_traces_v2": comparison,
        "records": records,
    }

    write_json(args.out, payload)
    print("[trace_g4_v3] entries=%d runs=%d failed=%d rules_hit_true=%d/%d empty_cov_true=%d"
          % (len(records), runs, len(run_failures), len(all_true), len(rules),
             len(never_true)), flush=True)
    if comparison:
        print("[trace_g4_v3] vs traces_v2: rules_hit %d -> %d; empty_cov %d -> %d; "
              "run_rule pairs v2_hit_but_never_true=%d"
              % (comparison["traces_v2_rules_hit"], len(all_true),
                 comparison["empty_cov_v2"], comparison["empty_cov_v3"],
                 comparison["run_rule_pairs"]["v2_hit_but_predicate_never_true"]), flush=True)

    # ---- executed code-object inventory (for the D1/D2/D3 triage) -------- #
    if args.inventory_out:
        inventory = {
            "tool": "g4-executed-inventory",
            "version": TOOL_VERSION,
            "note": ("Which code objects of the universe anchor files actually ran, "
                     "during the import phase and during the 131 J pyc runs. "
                     "Used only to tier rules that were never measured true."),
            "anchor_files": anchor_files,
            "phase": {"import": sorted(meas.import_files), "run": sorted(meas.run_files)},
            "files": {f: sorted(v.values(), key=lambda e: (e["name"], e["firstlineno"]))
                      for f, v in sorted(meas.keyed.items())},
        }
        write_json(args.inventory_out, inventory)
        print("[trace_g4_v3] wrote %s (%d anchor files executed)"
              % (args.inventory_out, len(meas.keyed)), flush=True)

    if args.mirror_dir:
        os.makedirs(args.mirror_dir, exist_ok=True)
        write_json(os.path.join(args.mirror_dir, os.path.basename(args.out)), payload)
        if args.inventory_out:
            write_json(os.path.join(args.mirror_dir,
                                    os.path.basename(args.inventory_out)), inventory)
        print("[trace_g4_v3] mirrored to %s" % args.mirror_dir.replace("\\", "/"), flush=True)

    print("[trace_g4_v3] wrote %s" % args.out.replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
