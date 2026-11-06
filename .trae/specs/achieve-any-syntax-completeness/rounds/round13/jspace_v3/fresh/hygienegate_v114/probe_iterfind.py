import sys, os
REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2('F:/Downloads/pythoncdc-main/.trae/specs/attack-completeness-claims/rounds/round6/offcorpus/stdlib_xml_ElementPath.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
root = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
def find_code(code, acc):
    for c in code.co_consts:
        if hasattr(c, 'co_name'):
            acc.append(c); find_code(c, acc)
acc = []
find_code(root, acc)
fn = [c for c in acc if c.co_name == 'iterfind'][0]
cfg = build_cfg(fn)
gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generate()
print('=== regions (iterfind) ===')
for r in gen.regions:
    extra = ''
    tn = type(r).__name__
    if tn == 'IfRegion':
        extra = ' then=%s else=%s elifc=%s' % (
            [b.start_offset for b in (r.then_blocks or [])][:6],
            [b.start_offset for b in (r.else_blocks or [])][:6],
            [c.start_offset for c in (r.elif_conditions or [])][:6])
    elif tn == 'LoopRegion':
        extra = ' is_while_true=%s cond=%s body=%s' % (
            getattr(r, 'is_while_true', None),
            r.condition_block.start_offset if getattr(r, 'condition_block', None) else None,
            [b.start_offset for b in (r.body_blocks or [])][:10])
    elif tn == 'TryExceptRegion':
        extra = ' handler=%s' % ([b.start_offset for b in (r.handler_blocks or [])][:6] if getattr(r, 'handler_blocks', None) else None)
    elif tn == 'BoolOpRegion':
        extra = ' op_chain=%s' % ([(b.start_offset, op) for b, op in r.op_chain],)
    print('%-16s entry=%-4s blocks=%s%s' % (
        tn, r.entry.start_offset,
        [b.start_offset for b in r.blocks][:14], extra))
print()
print('=== blocks ===')
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print('block@%-4s: %s' % (b.start_offset, [i.opname for i in b.instructions][:8]))
