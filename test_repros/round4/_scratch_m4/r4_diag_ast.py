import sys, marshal, json
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator

f = open(r'F:\Downloads\pythoncdc-main\test_repros\round4\c4_02_loop_else.pyc', 'rb')
f.read(16)
code = marshal.load(f)

def find(co, name):
    for c in co.co_consts:
        if hasattr(c, 'co_name') and c.co_name == name:
            return c
    return None

cl = find(code, 'CL')
mm = find(cl, 'm')

builder = CFGBuilder()
cfg = builder.build(mm)
gen = RegionASTGenerator(cfg, recursive=False)
orig_r58 = gen._r58_collect_break_target_stmts
def traced_r58(region, body_set):
    print('R58 called: break_blocks', [(b.start_offset, b in gen.generated_blocks) for b in getattr(region, 'break_blocks', [])])
    res = orig_r58(region, body_set)
    print('R58 result:', json.dumps(res, default=str)[:400])
    return res
gen._r58_collect_break_target_stmts = traced_r58
orig_while = gen._loop_generate_while
def traced_while(region, skip_store_targets=None):
    print('WHILE gen: else_blocks', [(b.start_offset, b in gen.generated_blocks) for b in (region.else_blocks or [])])
    res = orig_while(region, skip_store_targets)
    print('WHILE result:', json.dumps(res, default=str)[:800])
    return res
gen._loop_generate_while = traced_while
ast = gen.generate()
print('=== AST ===')
print(json.dumps(ast, default=str, indent=1))
print('=== generated offs ===', sorted(gen.generated_offsets))