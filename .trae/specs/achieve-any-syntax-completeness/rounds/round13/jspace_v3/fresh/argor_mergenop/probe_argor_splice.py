# rr-v5r114 探针：repro1 R67 拼接干跑
import sys, os
REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2('D:/temp/opencode/cl_layout/r114diag/repro1.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
def find_code(code, acc):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            acc.append(c); find_code(c, acc)
root = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
acc = []; find_code(root, acc)
init_code = [c for c in acc if c.co_name == '__init__'][0]
cfg = build_cfg(init_code)
gen = RegionASTGenerator(cfg, top_level_code=init_code)
gen.generate()

for r in gen.regions:
    if type(r).__name__ != 'BoolOpRegion' or getattr(r, 'merge_block', None) is None:
        continue
    mb_all = [i for i in r.merge_block.instructions if i.opname not in ('RESUME','NOP','CACHE','PUSH_NULL')]
    sa = next((k for k, i in enumerate(mb_all) if i.opname == 'STORE_ATTR'), None)
    if sa is None or sa == 0:
        continue
    print('BoolOpRegion entry=%s merge=%s sa=%d' % (r.entry.start_offset, r.merge_block.start_offset, sa))
    boolop_expr = gen._build_boolop_expression(r)
    print('boolop_expr:', str(boolop_expr)[:120])
    fcb = r.op_chain[0][0]
    pin = gen.region_analyzer.identify_block_prefix_instructions(fcb)
    gen.expr_reconstructor.reconstruct(list(pin or []))
    res = [s for s in gen.expr_reconstructor.stack if s.get('type') != 'PUSH_NULL']
    print('chain residual len=%d, top type=%s' % (len(res), res[-1].get('type') if res else None))
    init = list(res)
    init[-1] = boolop_expr
    pre = mb_all[:sa]
    print('merge prefix ops:', [i.opname for i in pre])
    spliced = gen.expr_reconstructor.reconstruct(list(pre), initial_stack=init)
    stk = [s for s in gen.expr_reconstructor.stack if s.get('type') != 'PUSH_NULL']
    print('spliced return:', str(spliced)[:80])
    print('post-splice stack len=%d' % len(stk))
    for k, s in enumerate(stk):
        print('  [%d] %s %s' % (k, s.get('type'), str(s)[:110]))
