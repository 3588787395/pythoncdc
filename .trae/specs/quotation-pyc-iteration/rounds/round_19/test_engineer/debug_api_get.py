"""R19 测试工程师：调试 api_get 函数的 try-except post 代码丢失问题"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, LoopRegion, TryExceptRegion

PYC = '/workspace/quotation.pyc'
target_name = 'api_get'

module = load_pyc_file_v2(PYC)
code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
if hasattr(code_obj, 'to_python_code'):
    code_obj = code_obj.to_python_code()

target = None
for const in code_obj.co_consts:
    if hasattr(const, 'co_name') and const.co_name == target_name:
        target = const
        break

print(f'=== {target_name} 原始字节码 ===')
dis.dis(target)
print()

builder = CFGBuilder()
cfg = builder.build(target)
ra = RegionAnalyzer(cfg)
ra.analyze()

print('=== All Regions ===')
for r in ra.regions:
    blocks = sorted([b.start_offset for b in r.blocks])
    print(f'  {type(r).__name__}: blocks={blocks}, entry={r.entry.start_offset if r.entry else None}')
    if isinstance(r, TryExceptRegion):
        print(f'    try_blocks: {[b.start_offset for b in r.try_blocks]}')
        print(f'    else_blocks: {[b.start_offset for b in (r.else_blocks or [])]}')
        print(f'    finally_blocks: {[b.start_offset for b in (r.finally_blocks or [])]}')
        print(f'    cleanup_blocks: {[b.start_offset for b in (r.cleanup_blocks or [])]}')
        print(f'    handler_entry_blocks: {[b.start_offset for b in r.handler_entry_blocks]}')
        print(f'    has_else: {getattr(r, "has_else", None)}')
        print(f'    has_finally: {getattr(r, "has_finally", None)}')
        print(f'    try_offset_start: {r.try_offset_start}')
        print(f'    try_offset_end: {r.try_offset_end}')
        print(f'    parent: {type(r.parent).__name__ if r.parent else None}')
