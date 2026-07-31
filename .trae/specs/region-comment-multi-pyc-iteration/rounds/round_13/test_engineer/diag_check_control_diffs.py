"""Check diffs for repro_03 (control) and repro_11 (control) to determine
if remaining diffs are jump-noise or semantic."""
import os, sys, py_compile, marshal, dis
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))
REPRO_DIR = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_13/test_engineer/minimal_repros'

for name in ['repro_03_ctrl_len_chained_subscr_no_unpack.py', 'repro_11_ctrl_simple_subscr_after_unpack.py', 'repro_02_subscr_filter_after_unpack.py']:
    REPRO = REPRO_DIR / name
    PYC = str(REPRO) + 'c'
    OK = str(REPRO)[:-3] + 'OK.py'
    py_compile.compile(str(REPRO), doraise=True, cfile=PYC)
    py_compile.compile(OK, doraise=True, cfile=PYC + '.dec')
    with open(PYC, 'rb') as f:
        f.read(16); orig = marshal.load(f)
    with open(PYC + '.dec', 'rb') as f:
        f.read(16); dec = marshal.load(f)
    def codes(code):
        yield code.co_name, code
        for c in code.co_consts:
            if hasattr(c, 'co_code'):
                yield c.co_name, c
    om = {n: c for n, c in codes(orig)}
    dm = {n: c for n, c in codes(dec)}
    print(f"\n=== {name} ===")
    for fn in om:
        if fn not in dm:
            print(f"  {fn}: MISSING")
            continue
        oi = [(i.opname, i.argval) for i in dis.get_instructions(om[fn])]
        di = [(i.opname, i.argval) for i in dis.get_instructions(dm[fn])]
        if oi == di:
            print(f"  {fn}: MATCH ({len(oi)})")
        else:
            print(f"  {fn}: DIFF (orig={len(oi)} dec={len(di)})")
            shown = 0
            for i, (a, b) in enumerate(zip(oi, di)):
                if a != b and shown < 8:
                    # classify
                    is_jump = 'JUMP' in a[0] or 'JUMP' in b[0]
                    print(f"    [{i}] orig={a} dec={b} {'<JUMP-OFFSET>' if is_jump else ''}")
                    shown += 1
            if len(oi) != len(di):
                print(f"    len mismatch orig={len(oi)} dec={len(di)}")
