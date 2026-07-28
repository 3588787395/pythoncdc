"""R30 测试工程师：调试repro_12的IfRegion跳过问题"""
import sys
import dis
import types
import inspect
import marshal
import struct
import time
import tempfile
import os

sys.path.insert(0, '/workspace')
sys.path.insert(0, '/workspace/.trae/specs/quotation-pyc-iteration/rounds/round_30/test_engineer/minimal_repros')

import repro_01_elif_merge_block_skips_next_if as mod
from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer

func = mod.repro_12_elif_chain_then_while_loop
src = inspect.getsource(func)
lines = src.split('\n')
min_indent = min(len(l) - len(l.lstrip()) for l in lines if l.strip())
src = '\n'.join(l[min_indent:] for l in lines)

mod_code = compile(src, '<repro>', 'exec')
with tempfile.NamedTemporaryFile(suffix='.pyc', delete=False, mode='wb') as f:
    magic = b'\xa7\r\r\n'
    flags = 0
    timestamp = int(time.time())
    size = len(src.encode())
    f.write(magic + struct.pack('<III', flags, timestamp, size))
    f.write(marshal.dumps(mod_code))
    pyc_path = f.name

from core.pyc_loader_v2 import load_pyc_file_v2
m = load_pyc_file_v2(pyc_path)
co = m.code.get() if hasattr(m.code, 'get') else m.code
if hasattr(co, 'to_python_code'):
    co = co.to_python_code()

# Find repro_12
def find_code(c, name):
    if c.co_name == name:
        return c
    for const in c.co_consts:
        if isinstance(const, type(c)):
            r = find_code(const, name)
            if r:
                return r
    return None

target = find_code(co, 'repro_12_elif_chain_then_while_loop')
print(f"Found: {target.co_name}")

cfg = build_cfg(target)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()
regions = analyzer.regions

print(f"\n=== Regions ({len(regions)}) ===")
for r in regions:
    parent_entry = r.parent.entry.start_offset if r.parent and r.parent.entry else None
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} blocks={[b.start_offset for b in r.blocks] if hasattr(r, 'blocks') else 'N/A'} parent_entry={parent_entry}")

print(f"\n=== CFG Blocks ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print(f"\nBlock {b.start_offset}:")
    for i in b.instructions:
        print(f"  {i.offset:4d}: {i.opname:30s} {i.argval}")
    print(f"  preds: {[p.start_offset for p in b.predecessors]}")
    print(f"  succs: {[s.start_offset for s in b.successors]}")

# Generate AST
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
print(f"\n=== AST ===")
print(f"type: {ast_dict.get('type')}")
if 'body' in ast_dict:
    for i, stmt in enumerate(ast_dict['body']):
        t = stmt.get('type') if isinstance(stmt, dict) else type(stmt).__name__
        print(f"  [{i}] {t}")

print(f"\n=== generated_blocks ===")
for b in sorted(cfg.blocks.values(), key=lambda x: x.start_offset):
    print(f"  Block {b.start_offset}: {b in gen.generated_blocks}")

os.unlink(pyc_path)
