# -*- coding: utf-8 -*-
"""N22 family: write the 11 probe-designed shapes, compile exact pycs, and
build a MINI preview jspace (11 entries only) for a diagnostic checker run
before the official v4 round.

Shapes (all single-function modules, minimal by design):
  8 probe-verified direct spec-inner operand shapes (ladder member TRUEs
  at core/cfg/code_generator.py chain lines, zero 4744 guard flows) +
  3 source-path-designed non-ladder shapes:
    n22_unary_not  -> rag:52090 transform-only UNARY_NOT block in a BoolOp
                      chain (comment's own example; py3.12: no TO_BOOL)
    n22_getlen     -> agv2:21513/21525/21641 + pattern_parser:2251/2452
                      (GET_LEN in the `case []` empty-sequence match)
    n22_pjbi       -> agv2:5381 POP_JUMP_BACKWARD_IF_NOT_NONE inside the
                      comprehension filter `if q is None` (filter back-jump)
"""
import hashlib
import json
import marshal
import os
import struct
import sys

REPO = r"F:\Downloads\pythoncdc-main"
N_DIR = os.path.join(REPO, "test_repros", "round13_b1")
SCRATCH = os.path.join(REPO, "test_repros", "stage3_scratch")
BASE_JSPACE = os.path.join(SCRATCH, "judgment_space_r9_rebaselined.json")

MAGIC = b"\xa7\x0d\x0d\x0a"  # py3.12 (3495)

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


def main():
    for stem, form, variant, src in SHAPES:
        py_abs = os.path.join(N_DIR, stem + ".py")
        pyc_abs = os.path.join(N_DIR, stem + ".pyc")
        py_rel = "test_repros/round13_b1/%s.py" % stem
        pyc_rel = "test_repros/round13_b1/%s.pyc" % stem
        bind = py_rel.replace("/", "\\")
        with open(py_abs, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        code = compile(src, bind, "exec", dont_inherit=True)
        body = marshal.dumps(code)
        header = MAGIC + b"\x00\x00\x00\x00" + b"\x00\x00\x00\x00" \
            + struct.pack("<I", len(src.encode("utf-8")))
        with open(pyc_abs, "wb") as fh:
            fh.write(header + body)
        # verify roundtrip exactly like the builder's verify_pyc
        with open(pyc_abs, "rb") as fh:
            head = fh.read(16)
            stored = marshal.load(fh)
        assert head[:4] == MAGIC, stem
        assert stored.co_filename == bind, (stem, stored.co_filename)
        fresh = marshal.loads(marshal.dumps(code))
        assert fresh.co_code == stored.co_code, stem
        assert fresh.co_consts == stored.co_consts, stem
        print("[n22] %s ok (id JS-B1-%s, %d bytes pyc)"
              % (stem, IDS[stem], 16 + len(body)))

    # mini preview jspace: base doc schema, entries = only the 11 n22 entries
    with open(BASE_JSPACE, encoding="utf-8-sig") as fh:
        base = json.load(fh)
    entries = []
    for stem, form, variant, src in SHAPES:
        py_rel = "test_repros/round13_b1/%s.py" % stem
        pyc_rel = "test_repros/round13_b1/%s.pyc" % stem
        py_abs = os.path.join(N_DIR, stem + ".py")
        pyc_abs = os.path.join(N_DIR, stem + ".pyc")
        entries.append({
            "id": "JS-B1-%s" % IDS[stem],
            "form": form,
            "host": "function-body",
            "depth": "d1",
            "variant": variant,
            "row": "NEW",
            "required_evidence": [{
                "kind": "probe",
                "pyc": pyc_rel,
                "note": "阶段三 B1 N22 预证单元（迷你预跑）",
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
                "note": ("stage-3 B1 N22 preview entry; measured only "
                         "(decompile pipelines), never executed"),
            },
            "entrypoint": "module",
            "host_prelude_reason": None,
        })
    doc = dict(base)
    doc["entries"] = entries
    doc["stage3_b1_n22_preview"] = "N22 diagnostic preview (11 entries only)"
    mini_path = os.path.join(SCRATCH, "judgment_space_stage3_b1_n22_preview.json")
    with open(mini_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("[n22] mini preview jspace -> %s (%d entries, sha16 %s)"
          % (os.path.basename(mini_path), len(entries),
             hashlib.sha256(open(mini_path, "rb").read()).hexdigest()[:16]))


if __name__ == "__main__":
    main()
