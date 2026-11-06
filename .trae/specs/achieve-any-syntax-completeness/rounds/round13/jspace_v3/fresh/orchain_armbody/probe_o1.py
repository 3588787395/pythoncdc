import sys, os
REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2('D:/temp/opencode/cl_layout/r121diag/o1.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
root = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
def find_code(code, acc):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            acc.append(c); find_code(c, acc)
acc = []
find_code(root, acc)
fn = [c for c in acc if c.co_name == 'f'][0]
cfg = build_cfg(fn)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generate()
print('=== regions ===')
for r in gen.regions:
    extra = ''
    if type(r).__name__ == 'IfRegion':
        extra = ' then=%s else=%s elifc=%s' % (
            [b.start_offset for b in (r.then_blocks or [])],
            [b.start_offset for b in (r.else_blocks or [])][:5],
            [c.start_offset for c in (r.elif_conditions or [])])
    if type(r).__name__ == 'BoolOpRegion':
        extra = ' op_chain=%s merge=%s' % (
            [(b.start_offset, op) for b, op in r.op_chain],
            r.merge_block.start_offset if r.merge_block else None)
    print('%-15s entry=%-4s blocks=%s%s' % (
        type(r).__name__, r.entry.start_offset,
        [b.start_offset for b in r.blocks][:12], extra))
print()
print('=== blocks ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print('block@%-4s: %s' % (b.start_offset, [i.opname for i in b.instructions]))
