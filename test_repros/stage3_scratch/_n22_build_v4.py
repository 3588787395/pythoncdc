# -*- coding: utf-8 -*-
"""Build the stage-3 B1 v4 J-space: v3 (1577) + the 11 probe-designed N22
entries (1588).  The three reworked shapes (double-paren DictComp, double-
paren SetComp, getlen `case []: return w[1]` -> pp:2452 trap-free member
TRUE) are the final operand-family round (p_j budget v4=N22).

Writes test_repros/stage3_scratch/judgment_space_stage3_b1_v4.json.
"""
import hashlib
import json
import marshal
import os
import sys

REPO = r"F:\Downloads\pythoncdc-main"
SCRATCH = os.path.join(REPO, "test_repros", "stage3_scratch")
V3_JSPACE = os.path.join(SCRATCH, "judgment_space_stage3_b1_v3.json")
N_DIR = "test_repros/round13_b1"
MAGIC = b"\xa7\x0d\x0d\x0a"

SHAPES = [
    ("n22_spec_tuple", "JoinedStr", "n22-tuple-direct-spec-inner",
     "def f(a, b, w):\n    return f'{a:>{(b, w)}}'\n"),
    ("n22_spec_dictcomp", "JoinedStr", "n22-dictcomp-direct-spec-inner",
     "def f(a, k, v, pairs):\n    return f'{a:>({({k: v for k, v in pairs})}}'\n"),
    ("n22_spec_listcomp", "JoinedStr", "n22-listcomp-direct-spec-inner",
     "def f(a, q, w):\n    return f'{a:>{[q for q in w]}}'\n"),
    ("n22_spec_setcomp", "JoinedStr", "n22-setcomp-direct-spec-inner",
     "def f(a, q, w):\n    return f'{a:>({({q for q in w})}}'\n"),
    ("n22_spec_genexp", "JoinedStr", "n22-genexp-direct-spec-inner",
     "def f(a, q, w):\n    return f'{a:>{(q for q in w)}}'\n"),
    ("n22_spec_subscript", "JoinedStr", "n22-subscript-direct-spec-inner",
     "def f(a, w):\n    return f'{a:>{w[1]}}'\n"),
    ("n22_spec_joinedstr", "JoinedStr", "n22-joinedstr-direct-spec-inner",
     "def f(a, b):\n    return f'{a:>{f\"x{b}y\"}}'\n"),
    ("n22_spec_fmtvalue", "JoinedStr", "n22-fmtvalue-direct-spec-inner",
     "def f(a, b):\n    return f'{a:>{f\"{b!r}\"}}'\n"),
    ("n22_unary_not", "BoolOp", "n22-unary-not-transform-block",
     "def f(a, b, c, d):\n    return not (a and b) or (c and not d)\n"),
    ("n22_getlen", "Match", "n22-getlen-empty-seq",
     "def f(x, w):\n    match x:\n        case []:\n            return w[1]\n    return -1\n"),
    ("n22_pjbi", "ListComp", "n22-pjbi-isnone-filter",
     "def f(xs):\n    return [q for q in xs if q is None]\n"),
]
IDS = {"n22_spec_tuple": "N22T", "n22_spec_dictcomp": "N22D",
       "n22_spec_listcomp": "N22L", "n22_spec_setcomp": "N22S",
       "n22_spec_genexp": "N22G", "n22_spec_subscript": "N22X",
       "n22_spec_joinedstr": "N22J", "n22_spec_fmtvalue": "N22F",
       "n22_unary_not": "N22U", "n22_getlen": "N22E", "n22_pjbi": "N22P"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_pyc(py_rel, pyc_rel):
    py_abs = os.path.join(REPO, py_rel.replace("/", os.sep))
    pyc_abs = os.path.join(REPO, pyc_rel.replace("/", os.sep))
    src = open(py_abs, "r", encoding="utf-8").read()
    bind = py_rel.replace("/", "\\")
    code = compile(src, bind, "exec", dont_inherit=True)
    with open(pyc_abs, "rb") as fh:
        head = fh.read(16)
        stored = marshal.load(fh)
    if head[:4] != MAGIC:
        return "bad magic %r" % (head[:4],)
    if stored.co_filename != bind:
        return "co_filename mismatch: %r" % (stored.co_filename,)
    fresh = marshal.loads(marshal.dumps(code))
    got = marshal.loads(marshal.dumps(stored))
    if (fresh.co_code != got.co_code or fresh.co_consts != got.co_consts
            or fresh.co_names != got.co_names
            or fresh.co_varnames != got.co_varnames):
        return "code object mismatch vs fresh compile"
    return None


def main():
    with open(V3_JSPACE, encoding="utf-8-sig") as fh:
        v3 = json.load(fh)
    base_entries = v3["entries"]
    assert len(base_entries) == 1577, len(base_entries)
    existing_ids = {e["id"] for e in base_entries}

    entries = []
    for stem, form, variant, src in SHAPES:
        py_rel = "%s/%s.py" % (N_DIR, stem)
        pyc_rel = "%s/%s.pyc" % (N_DIR, stem)
        py_abs = os.path.join(REPO, py_rel.replace("/", os.sep))
        pyc_abs = os.path.join(REPO, pyc_rel.replace("/", os.sep))
        err = verify_pyc(py_rel, pyc_rel)
        if err:
            raise SystemExit("[v4] %s pyc verification FAILED: %s" % (stem, err))
        eid = "JS-B1-%s" % IDS[stem]
        assert eid not in existing_ids, eid
        entries.append({
            "id": eid,
            "form": form,
            "host": "function-body",
            "depth": "d1",
            "variant": variant,
            "row": "NEW",
            "required_evidence": [{
                "kind": "probe",
                "pyc": pyc_rel,
                "note": "阶段三 B1 N22 预证单元（直形终轮）",
            }],
            "status": "covered",
            "source": (".trae/specs/achieve-any-syntax-completeness/rounds/"
                       "round13/rows/B1_J_EXPANSION_DESIGN.md"),
            "j_schema_version": "v2",
            "expected_label": {"form": form, "variant": variant,
                               "host": "function-body", "depth": "d1"},
            "counterexample_hint": None,
            "host_prelude": None,
            "excluded": [],
            "p_j": py_rel,
            "p_j_sha256": sha256_file(py_abs),
            "p_j_lines": len(src.splitlines()),
            "pyc": pyc_rel,
            "pyc_sha256": sha256_file(pyc_abs),
            "pyc_present": True,
            "pyc_loadable": None,
            "input_model": {
                "kind": "module", "calls": [], "seed": 0,
                "note": ("stage-3 B1 N22 entry; measured only "
                         "(decompile pipelines), never executed"),
            },
            "entrypoint": "module",
            "host_prelude_reason": None,
        })
        print("[v4] JS-B1-%s ok (%s, pyc sha16 %s)"
              % (IDS[stem], stem, entries[-1]["pyc_sha256"][:16]))

    doc = dict(v3)
    doc["entries"] = list(base_entries) + entries
    doc["stage3_b1"] = "stage-3 B1 round 4: + N22 direct-shape family (1588)"
    out = os.path.join(SCRATCH, "judgment_space_stage3_b1_v4.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[v4] %s -> %d entries (sha16 %s)" % (
        os.path.basename(out), len(doc["entries"]),
        hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]))


if __name__ == "__main__":
    main()
