import sys, os
sys.path.insert(0, '.')

import core.cfg.region_ast_generator as rag
from core.cfg.ast_generator_v2 import ExpressionReconstructor

_orig_rec = ExpressionReconstructor.reconstruct
def rec(self, instrs, **kw):
    r = _orig_rec(self, instrs, **kw)
    if isinstance(r, dict) and r.get('type') == 'Dict':
        import traceback
        tb = traceback.extract_stack()
        frames = [f"{os.path.basename(fr.filename)}:{fr.lineno}:{fr.name}" for fr in tb[-6:-1]]
        ops = [i.opname for i in instrs]
        print(f"[DICT] n_instrs={len(instrs)} init={len(kw.get('initial_stack', []))} ops={ops[:8]}")
        print(f"       via {' <- '.join(frames)}")
        print(f"       keys={[k.get('value') for k in r.get('keys', [])][:5]} values_n={len(r.get('values', []))}")
    return r
ExpressionReconstructor.reconstruct = rec

import pycdc
out = pycdc.decompile_pyc("site-packages/IQEngine/plugins/plugin_fly_data_source/fly_data_source.pyc")
idx = out.find('def get_stock_info')
print(out[idx:idx+1800])
