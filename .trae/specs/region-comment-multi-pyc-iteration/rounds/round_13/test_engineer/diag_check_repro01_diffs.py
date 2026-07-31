"""Check remaining diffs in repro_01 after fix."""
import os, sys, py_compile, marshal, dis
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_ROOT))
REPRO = PROJECT_ROOT / '.trae/specs/region-comment-multi-pyc-iteration/rounds/round_13/test_engineer/minimal_repros/repro_01_len_chained_subscr_after_unpack.py'
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
for name in om:
    if name not in dm:
        print(f"{name}: MISSING in decomp")
        continue
    oi = [(i.opname, i.argval) for i in dis.get_instructions(om[name])]
    di = [(i.opname, i.argval) for i in dis.get_instructions(dm[name])]
    if oi == di:
        print(f"{name}: MATCH ({len(oi)} instrs)")
    else:
        print(f"{name}: DIFF (orig={len(oi)} dec={len(di)})")
        for i, (a, b) in enumerate(zip(oi, di)):
            if a != b:
                print(f"  [{i}] orig={a} dec={b}")
        if len(oi) != len(di):
            print(f"  len mismatch: orig={len(oi)} dec={len(di)}")
