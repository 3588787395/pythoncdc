# -*- coding: utf-8 -*-
"""Rebuild the stage-3 B1 J-space expansion (v1/v2/v3) after the D:\\temp wipe.

Base      : test_repros/stage3_scratch/judgment_space_r9_rebaselined.json
            (round9 jspace, 1556 entries, zero-perturbation rebaseline,
             p_j/p_j_lines/pyc_sha drift 0/0/0)
N01..N18  : .trae/.../round13/rows/b1_design_data.json (metadata)
N01..N21  : test_repros/round13_b1/n*.py + n*.pyc (21 pairs, intact)
Schema    : round9 v2 entry schema (id, form, host, depth, variant, row,
            required_evidence, status, source, j_schema_version, expected_label,
            counterexample_hint, host_prelude, excluded, p_j, p_j_sha256,
            p_j_lines, pyc, pyc_sha256, pyc_present, pyc_loadable, input_model,
            entrypoint, host_prelude_reason)

Writes (test_repros/stage3_scratch/):
  judgment_space_stage3_b1_v1.json  (1556 + 18 = 1574)
  judgment_space_stage3_b1_v2.json  (1574 + 2 = 1576)
  judgment_space_stage3_b1_v3.json  (1576 + 1 = 1577)

The original builder and its exact N-entry serialization are lost, so the
v1 jspace sha16 target 0c6795cb81726c77 is NOT bit-reproducible; the G4
readings (s2 145 -> v1 150 -> v2 160 -> v3 164, zero regression) are the
acceptance gate.  Achieved hashes are printed for the report.
"""
import hashlib
import json
import marshal
import os
import sys

REPO = r"F:\Downloads\pythoncdc-main"
SCRATCH = os.path.join(REPO, "test_repros", "stage3_scratch")
BASE_JSPACE = os.path.join(SCRATCH, "judgment_space_r9_rebaselined.json")
DESIGN = os.path.join(
    REPO, ".trae", "specs", "achieve-any-syntax-completeness", "rounds",
    "round13", "rows", "b1_design_data.json")
N_DIR = "test_repros/round13_b1"          # repo-relative, forward slashes

STEMS = {
    "N01": "n01_expr_medley",             "N02": "n02_plain_negative",
    "N03": "n03_nested_closure_del",      "N04": "n04_gen_yield",
    "N05": "n05_async_await",             "N06": "n06_bigfunc_extended_arg",
    "N07": "n07_none_backjump",           "N08": "n08_match_patterns",
    "N09": "n09_walrus_star_unpack",      "N10": "n10_with_unpack",
    "N11": "n11_try_handler_battery",     "N12": "n12_comp_battery",
    "N13": "n13_ternary_boolop_chain",    "N14": "n14_store_shapes",
    "N15": "n15_elif_chain_marker",       "N16": "n16_print_expr_single",
    "N17": "n17_return_successor",        "N18": "n18_literal_region",
    "N19": "n19_spec_battery",            "N20": "n20_neg_provider",
    "N21": "n21_guard17_operands",
}
N19_21 = {
    "N19": {"form": "JoinedStr", "variant": "spec-dict-flow-battery",
            "host": "function-body", "depth": "d3plus 三层及以上",
            "title": "f-string spec dict-flow battery (deep-host operand flow)"},
    "N20": {"form": "JoinedStr", "variant": "walrus-starred-fallthrough",
            "host": "function-body", "depth": "d3plus 三层及以上",
            "title": "walrus/starred fallthrough negative provider"},
    "N21": {"form": "JoinedStr", "variant": "boolop-operand-precedence-observation",
            "host": "function-body", "depth": "d3plus 三层及以上",
            "title": "17-guard operand precedence observation battery"},
}
MODES = {e: ("single" if e == "N16" else "exec") for e in STEMS}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pyc(py_path, pyc_path, mode, py_rel):
    """marshal roundtrip check with the build binding (repo-relative path)."""
    src = open(py_path, "r", encoding="utf-8").read()
    bind = py_rel.replace("/", "\\")
    code = compile(src, bind, mode, dont_inherit=True)
    with open(pyc_path, "rb") as fh:
        head = fh.read(16)
        stored = marshal.load(fh)
    if head[:4] != b"\xa7\x0d\x0d\x0a":
        return "bad magic %r" % (head[:4],)
    if stored.co_filename != bind:
        return "co_filename mismatch: %r" % (stored.co_filename,)
    fresh = marshal.loads(marshal.dumps(code))
    got = marshal.loads(marshal.dumps(stored))
    if fresh.co_code != got.co_code or fresh.co_consts != got.co_consts \
            or fresh.co_names != got.co_names or fresh.co_varnames != got.co_varnames:
        return "code object mismatch vs fresh compile"
    return None


def make_entry(eid, meta):
    stem = STEMS[eid]
    py_rel = "%s/%s.py" % (N_DIR, stem)
    pyc_rel = "%s/%s.pyc" % (N_DIR, stem)
    py_abs = os.path.join(REPO, py_rel.replace("/", os.sep))
    pyc_abs = os.path.join(REPO, pyc_rel.replace("/", os.sep))
    err = verify_pyc(py_abs, pyc_abs, MODES[eid], py_rel)
    if err:
        raise SystemExit("[rebuild] %s pyc verification FAILED: %s" % (eid, err))
    lines = len(open(py_abs, "r", encoding="utf-8").read().splitlines())
    return {
        "id": "JS-B1-%s" % eid,
        "form": meta["form"],
        "host": meta["host"],
        "depth": meta["depth"],
        "variant": meta["variant"],
        "row": "NEW",
        "required_evidence": [{
            "kind": "probe",
            "pyc": pyc_rel,
            "note": "阶段三 B1 扩展正证单元（N 族，重建版）",
        }],
        "status": "covered",
        "source": (".trae/specs/achieve-any-syntax-completeness/rounds/round13/"
                   "rows/B1_J_EXPANSION_DESIGN.md"),
        "j_schema_version": "v2",
        "expected_label": {
            "form": meta["form"],
            "variant": meta["variant"],
            "host": meta["host"],
            "depth": meta["depth"],
        },
        "counterexample_hint": None,
        "host_prelude": None,
        "excluded": [],
        "p_j": py_rel,
        "p_j_sha256": sha256_file(py_abs),
        "p_j_lines": lines,
        "pyc": pyc_rel,
        "pyc_sha256": sha256_file(pyc_abs),
        "pyc_present": True,
        "pyc_loadable": None,
        "input_model": {
            "kind": "module",
            "calls": [],
            "seed": 0,
            "note": ("stage-3 B1 J-space expansion entry (N-family, rebuilt); "
                     "measured only (decompile pipelines), never executed"),
        },
        "entrypoint": "module",
        "host_prelude_reason": None,
    }


def write_jspace(base, entries, path, note):
    doc = dict(base)
    doc["entries"] = list(base["entries"]) + entries
    doc["stage3_b1"] = note
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[rebuild] %s -> %d entries (sha16 %s)" % (
        os.path.basename(path), len(doc["entries"]),
        hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]))


def main():
    with open(BASE_JSPACE, encoding="utf-8-sig") as fh:
        base = json.load(fh)
    with open(DESIGN, encoding="utf-8-sig") as fh:
        design = json.load(fh)
    assert len(base["entries"]) == 1556, len(base["entries"])

    made = {}
    for eid in sorted(STEMS):
        meta = dict(design["entries"][eid]) if eid in design["entries"] \
            else dict(N19_21[eid])
        made[eid] = make_entry(eid, meta)
        print("[rebuild] %s ok (%d lines, pyc sha16 %s)"
              % (made[eid]["id"], made[eid]["p_j_lines"],
                 made[eid]["pyc_sha256"][:16]))

    v1 = [made[e] for e in sorted(STEMS) if e <= "N18"]
    v2 = v1 + [made["N19"], made["N20"]]
    v3 = v2 + [made["N21"]]
    write_jspace(base, v1,
                 os.path.join(SCRATCH, "judgment_space_stage3_b1_v1.json"),
                 "stage-3 B1 round 1: N01..N18 (1574, rebuilt)")
    write_jspace(base, v2,
                 os.path.join(SCRATCH, "judgment_space_stage3_b1_v2.json"),
                 "stage-3 B1 round 2: + N19/N20 (1576, rebuilt)")
    write_jspace(base, v3,
                 os.path.join(SCRATCH, "judgment_space_stage3_b1_v3.json"),
                 "stage-3 B1 round 3: + N21 (1577, rebuilt)")
    print("[rebuild] all jspaces rebuilt on round9-rebaselined base; "
          "pyc integrity verified for 21/21")


if __name__ == "__main__":
    main()
