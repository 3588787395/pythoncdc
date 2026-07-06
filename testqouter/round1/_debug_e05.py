import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

tf = 'test_e05_try_except_finally.py'
pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)

from core.pyc_loader_v2 import load_pyc_file_v2
module = load_pyc_file_v2(pyc)
code_obj = module.code.get()
inner_code = code_obj.to_python_code().co_consts[0]

from dis import get_instructions
print(f"Inner code: {inner_code.co_name}")
print("\n=== Bytecode ===")
for instr in get_instructions(inner_code):
    print(f"  {instr.offset:4d}: {instr.opname:30s} {instr.argval!r}")

from core.cfg.cfg_builder import build_cfg
cfg = build_cfg(inner_code)

print("\n=== CFG Blocks ===")
for offset in sorted(cfg.blocks.keys()):
    block = cfg.get_block_by_offset(offset)
    if block is None:
        continue
    instrs = [(i.offset, i.opname, i.argval) for i in block.instructions]
    succs = [s.start_offset for s in block.successors]
    print(f"  Block {block.start_offset}: {instrs} -> {succs}")

from core.cfg.region_analyzer import RegionAnalyzer
ra = RegionAnalyzer(cfg)
ra.analyze()

print("\n=== Regions ===")
for i, r in enumerate(ra.regions):
    rtype = type(r).__name__
    has_finally = getattr(r, 'has_finally', False)
    has_else = getattr(r, 'has_else', False)
    handlers = getattr(r, 'except_handlers', [])
    entry = getattr(r, 'entry', None)
    entry_off = entry.start_offset if entry else None
    try_blocks = [b.start_offset for b in getattr(r, 'try_blocks', [])]
    finally_blocks = [b.start_offset for b in getattr(r, 'finally_blocks', [])]
    else_blocks = [b.start_offset for b in getattr(r, 'else_blocks', [])]
    handler_info = [(et, en, [b.start_offset for b in hbs]) for et, en, hbs in handlers]
    parent = getattr(r, 'parent', None)
    parent_type = type(parent).__name__ if parent else None
    print(f"  Region {i}: {rtype}")
    print(f"    entry={entry_off}, has_finally={has_finally}, has_else={has_else}")
    print(f"    try_blocks={try_blocks}")
    print(f"    except_handlers={handler_info}")
    print(f"    finally_blocks={finally_blocks}")
    print(f"    else_blocks={else_blocks}")
    print(f"    parent={parent_type}")
    print()

if os.path.exists(pyc): os.remove(pyc)
