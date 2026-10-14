"""build_cand_r87a_r2157.py — byte-exact rebuild of the gate-39 LANDED core bytes from the repo,
printing both core sha16s, and the (empty) [R21-57] patch table.

This run delivers NO candidate: see FIX_R21-57 §2 (the landed [R21-55]/[R21-56] predicate has zero
evaluations in `_sync_worker`), §3 (the landed while-condition walk is killed at its first
iteration by `LoopRegion.interrupts_boolop_forward_chain` == `return True`), §5 (a perfect loop1
render alone still reads `Different control flow`, three independent defects must close) and §6
(the exact source text of the last conjunct is not pinned, so no criterion can be validated
against ground truth). The script therefore certifies the landed bytes, copies them out as
`LANDED_*`, prints both sha16s, and refuses to write a candidate unless a patch table is supplied.

BOM + all-CRLF preserved; every anchor asserted unique; refuses on `\\r\\r\\n`; py_compile.
usage: python -X utf8 build_cand_r87a_r2157.py [--emit-candidate]
"""
import hashlib
import os
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
GEN_SRC = REPO + "/core/cfg/region_ast_generator.py"
ANA_SRC = REPO + "/core/cfg/region_analyzer.py"
OUTDIR = "DELIVER"

# gate-39 landed bytes (certified 2026-10-12: 6615/6617 = 99.9698 %, 400/402 files)
LANDED_GEN_SHA16 = "b4363f5858e58074"
LANDED_ANA_SHA16 = "842e2748bcdfeb66"

# [R21-57] patch table: (target, anchor lines, replacement lines). EMPTY this run — see docstring.
PATCHES = []


def load(path, want_sha16):
    raw = open(path, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()[:16]
    print("%-46s sha16=%s bytes=%d %s" % (
        os.path.basename(path), sha, len(raw),
        "OK (landed)" if sha == want_sha16 else "!! NOT THE LANDED BYTES (%s)" % want_sha16))
    if sha != want_sha16:
        raise SystemExit("refusing: %s is not the gate-39 landed bytes" % path)
    if raw[:3] != b"\xef\xbb\xbf":
        raise SystemExit("base is not BOM-prefixed, refusing")
    if b"\r\r\n" in raw:
        raise SystemExit("base already has \\r\\r\\n, refusing")
    if raw.count(b"\n") != raw.count(b"\r\n"):
        raise SystemExit("base is not all-CRLF, refusing")
    return raw


gen_raw = load(GEN_SRC, LANDED_GEN_SHA16)
ana_raw = load(ANA_SRC, LANDED_ANA_SHA16)

if not PATCHES:
    print("PATCHES is empty -> no candidate; certifying and copying the landed bytes only.")
    if "--emit-candidate" in sys.argv:
        raise SystemExit("--emit-candidate requested but the [R21-57] patch table is empty")
    os.makedirs(OUTDIR, exist_ok=True)
    open(OUTDIR + "/LANDED_r87_region_ast_generator.py", "wb").write(gen_raw)
    open(OUTDIR + "/LANDED_r87_region_analyzer.py", "wb").write(ana_raw)
    print("copied: DELIVER/LANDED_r87_region_ast_generator.py, DELIVER/LANDED_r87_region_analyzer.py")
    sys.exit(0)

for target_raw, spec in PATCHES:
    lines = target_raw.split(b"\r\n")
    hits = [i for i, l in enumerate(lines) if l == spec["anchor"]]
    if len(hits) != 1:
        raise SystemExit("anchor not unique (%d): %r" % (len(hits), spec["anchor"][:70]))
    lines[hits[0]:hits[0] + spec["take"]] = [l.encode("utf-8") for l in spec["new"]]
    out = b"\r\n".join(lines)
    if b"\r\r\n" in out:
        raise SystemExit("produced \\r\\r\\n, refusing")
    assert out[:3] == b"\xef\xbb\xbf"
    assert out.count(b"\n") == out.count(b"\r\n")
    os.makedirs(OUTDIR, exist_ok=True)
    open(spec["dst"], "wb").write(out)
    print("DST =", spec["dst"], "sha16 =", hashlib.sha256(out).hexdigest()[:16])
    compile(out.decode("utf-8-sig"), spec["dst"], "exec")
    import py_compile
    py_compile.compile(spec["dst"], doraise=True)
    print("compile + py_compile: OK")
