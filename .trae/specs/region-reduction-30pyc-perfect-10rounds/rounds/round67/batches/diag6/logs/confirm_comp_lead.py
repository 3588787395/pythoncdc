# -*- coding: utf-8 -*-
"""Read-only confirmation: does extending comprehension_generator._detect_comp_ternary's
condition scan over same-target POP_JUMP chains restore the dropped `and` operand?
(Monkeypatch in-process only; the repo is never written.)"""
import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
import core.cfg.comprehension_generator as CG
_CONDJ = CG.CONDITIONAL_JUMP_OPS
_ORIG = CG.ComprehensionGenerator._detect_comp_ternary

def patched(self, all_instrs, store_idx, append_idx):
    r = _ORIG(self, all_instrs, store_idx, append_idx)
    return r

CG.ComprehensionGenerator._detect_comp_ternary = patched
import pycdc
for p, fn in [('site-packages/IQCommon/strategy/wizard_quant_api.pyc', 'calculate_di'),
              ('D:/Temp/opencode/r67gate/diag6/synth/r67d6_boolop_ternary.pyc', 'v1')]:
    txt = pycdc.decompile_pyc(p)
    for l in txt.splitlines():
        if 'dmp = ' in l or fn == 'v1' and 'sum(' in l:
            print('%-22s %s' % (os.path.basename(p), l.strip()[:150]))
