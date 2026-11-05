import sys, os
REPO = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, REPO)
os.chdir(REPO)
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2('D:/temp/opencode/cl_layout/r114diag/repro4.pyc')
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
root = code_obj.to_python_code() if hasattr(code_obj, 'to_python_code') else code_obj
cfg = build_cfg(root)
gen = RegionASTGenerator(cfg, top_level_code=root)
gen.generate()
for r in gen.regions:
    print('%-16s entry=%-4s merge=%-4s blocks=%s value_target=%r' % (
        type(r).__name__, getattr(r.entry, 'start_offset', None),
        getattr(r.merge_block, 'start_offset', None) if getattr(r, 'merge_block', None) else None,
        [b.start_offset for b in getattr(r, 'blocks', [])], getattr(r, 'value_target', None)))
# NOP 所在块归属
for b in cfg.blocks.values():
    offs = [i.offset for i in b.instructions]
    if 196 in offs:
        print('block@%s instrs=%s' % (b.start_offset, offs))
        own = None
        for r in gen.regions:
            if any(bb is b for bb in getattr(r, 'blocks', [])):
                own = type(r).__name__
            if getattr(r, 'merge_block', None) is b:
                print('  ^ is merge_block of', type(r).__name__)
        print('  in blocks of:', own)
