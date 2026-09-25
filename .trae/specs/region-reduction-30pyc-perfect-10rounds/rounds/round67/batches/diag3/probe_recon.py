# -*- coding: utf-8 -*-
"""r67-diag3 read-only probe: log every expr_reconstructor.reconstruct call (its
instruction slice + rebuilt node) while decompiling one synth function."""
import io
import json
import sys

sys.path.insert(0, r'D:/Temp/opencode/r67gate/diag3')
import h62  # noqa: E402

pycdc = h62._load_arm('landed')
import core.cfg.region_ast_generator as G  # noqa: E402

CLS = None
for nm, obj in list(vars(G).items()):
    if isinstance(obj, type) and hasattr(obj, '_try_build_ternary_merge_consumer_expr'):
        CLS = obj
        break
print('class', CLS.__name__)

# find the reconstructor class
RC = None
for nm, obj in list(vars(G).items()):
    if isinstance(obj, type) and hasattr(obj, 'reconstruct'):
        RC = obj
        print('recon class', nm)
        break

NAME = sys.argv[2]
LOG = []


def patch(klass, label):
    orig = klass.reconstruct

    def wrapped(self, instrs, *a, **kw):
        try:
            seq = [(i.opname, str(i.argval)[:18]) for i in instrs]
        except Exception:
            seq = ['?']
        r = orig(self, instrs, *a, **kw)
        if len(sys.argv) > 3 and sys.argv[3] == 'all':
            LOG.append((label, seq, r.get('type') if isinstance(r, dict) else repr(r)[:40]))
        elif any(s[0] == 'BUILD_CONST_KEY_MAP' for s in seq):
            LOG.append((label, seq, r.get('type') if isinstance(r, dict) else repr(r)[:40],
                        json.dumps(r, ensure_ascii=False)[:400]))
        return r
    klass.reconstruct = wrapped


if RC is not None:
    patch(RC, RC.__name__)

out = pycdc.decompile_pyc(sys.argv[1])
io.open('scratch_probe_%s.py' % NAME, 'w', encoding='utf-8').write(out)
for e in LOG:
    print('REC', e[0])
    print('   instrs:', ' | '.join('%s %s' % t for t in e[1]))
    print('   node  :', e[2:])
