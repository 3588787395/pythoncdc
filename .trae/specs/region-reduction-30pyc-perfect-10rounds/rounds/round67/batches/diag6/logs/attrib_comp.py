# -*- coding: utf-8 -*-
"""Attribute the dropped `and` operand: recompute _detect_comp_ternary's own index ranges
for the failing comprehension and show which instructions its cond_instrs slice excludes."""
import io, marshal, os, sys, types
sys.path.insert(0, r'F:/Downloads/pythoncdc-main'); os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
import core.cfg.comprehension_generator as CG
CGJ = CG.CONDITIONAL_JUMP_OPS
seen = []
_orig = CG.ComprehensionGenerator._detect_comp_ternary
def w(self, all_instrs, store_idx, append_idx):
    r = _orig(self, all_instrs, store_idx, append_idx)
    ao = all_instrs[append_idx].offset if append_idx < len(all_instrs) else float('inf')
    cji, lfe = None, store_idx
    for idx in range(store_idx + 1, append_idx):
        it = all_instrs[idx]
        if it.opname in CGJ:
            if 'BACKWARD' in it.opname:
                lfe = idx; continue
            if it.argval is not None and it.argval < ao:
                cji = idx; break
            return r
    if cji is None: return r
    n_extra = sum(1 for i in range(cji + 1, append_idx)
                  if all_instrs[i].opname in CGJ and all_instrs[i].argval == all_instrs[cji].argval)
    print('  _detect_comp_ternary: cond_jump@%d(%s->%d) cond_instrs=[%d:%d] n_in_cond=%d '
          'EXTRA same-target cond jumps after it (i.e. boolop operands LOST) = %d  -> %s'
          % (cji, all_instrs[cji].opname, all_instrs[cji].argval, lfe + 1, cji, cji - lfe - 1, n_extra,
             (r or {}).get('type')))
    return r
CG.ComprehensionGenerator._detect_comp_ternary = w
import pycdc
for p in ['site-packages/IQCommon/strategy/wizard_quant_api.pyc',
          'D:/Temp/opencode/r67gate/diag6/synth/r67d6_boolop_ternary.pyc']:
    print('#####', os.path.basename(p))
    pycdc.decompile_pyc(p)
