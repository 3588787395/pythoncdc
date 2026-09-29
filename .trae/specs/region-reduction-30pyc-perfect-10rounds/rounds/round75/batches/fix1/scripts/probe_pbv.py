# -*- coding: utf-8 -*-
"""fix1: run the official-style bytecode_diff (scripts/pyc_batch_verify) on the
landed product for jq_trans_module and print the mismatch detail."""
import importlib.util as iu
import io
import sys

sys.stdout.reconfigure(encoding='utf-8')
REPO = r'F:/Downloads/pythoncdc-main'
PYC = REPO + r'\site-packages\IQCommon\strategy\jq_trans_module.pyc'
OUT = r'D:/Temp/opencode/r75gate/fix1/jq_prod.py'

_s = iu.spec_from_file_location('pbv', REPO + r'\scripts\pyc_batch_verify.py')
pbv = iu.module_from_spec(_s)
_s.loader.exec_module(pbv)

sys.path.insert(0, REPO)
import pycdc  # noqa: E402

io.open(OUT, 'w', encoding='utf-8').write(pycdc.decompile_pyc(PYC))
print('wrote %s' % OUT)

r = pbv.bytecode_diff(PYC, OUT)
print({k: v for k, v in r.items() if k != 'mismatches'})
for m in r.get('mismatches') or []:
    print('MISMATCH', m.get('name'), m.get('orig_count'), m.get('decomp_count'),
          'jump_diffs', m.get('jump_diffs'), 'true_diffs', m.get('true_diffs'))
    for k, v in (m.get('details') or m).items():
        if k not in ('name', 'orig_count', 'decomp_count', 'jump_diffs', 'true_diffs'):
            print('   ', k, str(v)[:600])
