import py_compile, sys, os, types
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg import build_cfg, CFGRegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

tf = 'test_r1_if_try_except.py'
pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)
code_obj = compile(open(tf).read(), tf, 'exec')
func_code = code_obj.co_consts[0]
cfg = build_cfg(func_code)
ra = CFGRegionAnalyzer(cfg)
regions = ra.analyze()

for r in regions:
    if isinstance(r, IfRegion):
        print(f"IfRegion: entry={r.entry.start_offset}")
        print(f"  cond_block={r.condition_block.start_offset if r.condition_block else None}")
        print(f"  then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"  else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"  merge_block={r.merge_block.start_offset if r.merge_block else None}")
        for eb in r.else_blocks:
            print(f"  else block {eb.start_offset} instructions:")
            for instr in eb.instructions:
                print(f"    {instr.opname} {instr.argval}")
        for tb in r.then_blocks:
            print(f"  then block {tb.start_offset} instructions:")
            for instr in tb.instructions:
                print(f"    {instr.opname} {instr.argval}")
            print(f"    successors: {[s.start_offset for s in tb.successors]}")

os.remove(pyc)
