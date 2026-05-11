import py_compile, sys, os
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, LoopRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

tf = 'test_e11_loop_with_try.py'
with open(tf) as f:
    source = f.read()

code = compile(source, tf, 'exec')
func_code = code.co_consts[0]

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()

print("=== Regions ===")
for r in gen.regions:
    if isinstance(r, LoopRegion):
        print(f"LoopRegion: entry={r.entry.start_offset}, blocks={sorted(b.start_offset for b in r.blocks)}")
        print(f"  body_blocks={sorted(b.start_offset for b in r.body_blocks)}")
        print(f"  back_edge_block={r.back_edge_block.start_offset if r.back_edge_block else None}")
        print(f"  header_block={r.header_block.start_offset if r.header_block else None}")
        print(f"  else_blocks={sorted(b.start_offset for b in r.else_blocks) if r.else_blocks else []}")
        for child in (r.children or []):
            print(f"  child: {type(child).__name__}, entry={child.entry.start_offset if child.entry else None}")
            if isinstance(child, TryExceptRegion):
                print(f"    try_blocks={sorted(b.start_offset for b in child.try_blocks)}")
                for exc_type, exc_name, handler_blocks in child.except_handlers:
                    print(f"    handler: exc_type={exc_type}, blocks={sorted(b.start_offset for b in handler_blocks)}")
                print(f"    blocks={sorted(b.start_offset for b in child.blocks)}")
    elif isinstance(r, TryExceptRegion):
        print(f"TryExceptRegion: entry={r.entry.start_offset}, blocks={sorted(b.start_offset for b in r.blocks)}")
        print(f"  try_blocks={sorted(b.start_offset for b in r.try_blocks)}")

print("\n=== All Blocks ===")
for block in cfg:
    last_instr = block.get_last_instruction()
    last_op = last_instr.opname if last_instr else None
    last_argval = last_instr.argval if last_instr else None
    succs = [s.start_offset for s in block.successors]
    meaningful = [i.opname for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
    print(f"  block {block.start_offset}: last={last_op}({last_argval}), succs={succs}")
    print(f"    meaningful: {meaningful}")

print("\n=== AST Dict ===")
import json
print(json.dumps(ast_dict, indent=2, default=str))
