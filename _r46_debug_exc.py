"""Debug the exception handling for repro_21."""
import sys, dis, marshal, types
sys.path.insert(0, '.')

from core.cfg.cfg_builder import build_cfg
from core.cfg.structured_analyzer import StructuredAnalyzer
from core.cfg.exception_handler import identify_try_except_simplified

REPRO_DIR = ".trae/specs/region-comment-multi-pyc-iteration/rounds/round_46/test_engineer/minimal_repros"

with open(f'{REPRO_DIR}/repro_21_try_except_format.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func = None
for const in code.co_consts:
    if isinstance(const, types.CodeType) and const.co_name == 'func':
        func = const
        break

if func is None:
    print("func not found")
    sys.exit(1)

print("=== Exception Table (raw) ===")
print(func.co_exceptiontable)

cfg = build_cfg(func)
print(f"\n=== CFG Blocks ===")
for b in cfg.get_blocks_in_order():
    last = b.get_last_instruction()
    last_str = f"{last.opname}" if last else "None"
    print(f"  Block {b.id} [{b.start_offset}-{b.end_offset}] last={last_str}")
    for instr in b.instructions:
        print(f"    {instr.offset:4d}  {instr.opname:30s}  {instr.arg if instr.arg is not None else ''}")

print(f"\n=== Exception Table (parsed) ===")
for entry in cfg.exception_table:
    print(f"  {entry}")

analyzer = StructuredAnalyzer(cfg)
analyzer.analyze()
identify_try_except_simplified(analyzer, set())

print(f"\n=== Exception Structures ({len(analyzer.control_structures)}) ===")
for s in analyzer.control_structures:
    print(f"  type={s.struct_type}")
    print(f"  has_else={s.has_else}")
    print(f"  has_finally={s.has_finally}")
    print(f"  try_body={[b.start_offset for b in s.try_body]}")
    print(f"  else_body={[b.start_offset for b in s.else_body]}")
    print(f"  finally_body={[b.start_offset for b in s.finally_body]}")
    for i, (exc_type, exc_name, h_blocks) in enumerate(s.except_handlers):
        print(f"  handler[{i}]: type={exc_type}, name={exc_name}, blocks={[b.start_offset for b in h_blocks]}")
