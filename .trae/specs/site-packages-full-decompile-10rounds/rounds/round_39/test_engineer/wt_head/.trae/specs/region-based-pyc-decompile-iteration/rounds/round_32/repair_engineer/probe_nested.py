# -*- coding: utf-8 -*-
"""探针：t_nested 多余 continue 根因分析。
打印区域层级/块角色，并追踪 Continue 语句的生成调用点。
"""
import os
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.cfg.region_analyzer import (RegionAnalyzer, LoopRegion, TryExceptRegion,
                                      IfRegion, WithRegion, TernaryRegion, BlockRole)
from core.cfg.region_ast_generator import RegionASTGenerator

P = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                 "rounds", "round_32", "repair_engineer", "t_nested.pyc")

# ---- 1. 区域与块结构 ----
import pycdc
import marshal

data = open(P, 'rb').read()
code = marshal.loads(data[16:])
# 找到 nested 函数 code object
import types as _t
def _find(co):
    if co.co_name == "nested":
        return co
    for c in co.co_consts:
        if isinstance(c, _t.CodeType):
            r = _find(c)
            if r:
                return r
    return None
func_code = _find(code)
print("=== FUNC ===", func_code.co_name, "nlocals=", func_code.co_nlocals)

from core.cfg import cfg_builder
builder = cfg_builder.CFGBuilder()
cfg = builder.build(func_code)

analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("=== BLOCKS ===")
for b in cfg.get_blocks_in_order():
    last = b.get_last_instruction()
    print("blk %3d..%-3d role=%-14s last=%s(%s)" % (
        b.start_offset, b.end_offset, analyzer.get_block_role(b).name,
        last.opname if last else None,
        last.argval if last else None))
    print("     succ=[%s] loop_header=%s" % (
        ",".join(str(s.start_offset) for s in b.successors),
        b.loop_header if hasattr(b, 'loop_header') else None))

print("=== REGIONS ===")
for r in analyzer.regions:
    ent = getattr(r, 'entry', None)
    print("%-28s entry=%s blocks=%s range=%s has_finally=%s except_handlers=%s try_start=%s" % (
        type(r).__name__,
        ent.start_offset if ent else None,
        sorted(b.start_offset for b in r.blocks),
        getattr(r, 'get_offset_range', lambda a: None)(analyzer) if hasattr(r, 'get_offset_range') else None,
        getattr(r, 'has_finally', None),
        bool(getattr(r, 'except_handlers', None)),
        getattr(r, 'try_offset_start', None)))

print("=== block->region ===")
for b in cfg.get_blocks_in_order():
    r = analyzer.get_region_for_block(b)
    er = analyzer.get_entry_region_for_block(b)
    print("blk %3d region=%-24s entry_region=%s" % (
        b.start_offset,
        type(r).__name__ if r else None,
        type(er).__name__ if er else None))

# ---- 2. Continue 生成追踪 ----
import core.cfg.region_ast_generator as rag

_orig_gen_block = RegionASTGenerator._generate_block_statements

def _wrap_gen_block(self, block, *a, **kw):
    res = _orig_gen_block(self, block, *a, **kw)
    conts = [s for s in (res or []) if isinstance(s, dict) and s.get('type') == 'Continue']
    if conts:
        import traceback
        print(">>> _generate_block_statements blk=%d produced Continue" % block.start_offset)
        tb = traceback.extract_stack()
        for fr in tb[-4:]:
            print("    at %s:%d %s" % (os.path.basename(fr.filename), fr.lineno, fr.name))
    return res

rag.RegionASTGenerator._generate_block_statements = _wrap_gen_block

# 追踪所有 append Continue 的调用点：hook list append 不现实，改为追踪
# _generate_region 的调用栈打印
_orig_gen_region = RegionASTGenerator._generate_region

def _wrap_gen_region(self, region, *a, **kw):
    import traceback
    ent = getattr(region, 'entry', None)
    print(">>> _generate_region %s entry=%s" % (
        type(region).__name__, ent.start_offset if ent else None))
    res = _orig_gen_region(self, region, *a, **kw)
    return res

rag.RegionASTGenerator._generate_region = _wrap_gen_region

# 追踪 _process_if_blocks / if 生成路径
_orig_process_if = getattr(rag.RegionASTGenerator, '_process_if_blocks', None)
if _orig_process_if:
    def _wrap_process_if(self, block, region=None, **kw):
        import traceback
        print(">>> _process_if_blocks block=%s region=%s" % (
            block.start_offset if hasattr(block, 'start_offset') else block,
            type(region).__name__ if region else None))
        res = _orig_process_if(self, block, region=region, **kw)
        return res
    rag.RegionASTGenerator._process_if_blocks = _wrap_process_if

src = pycdc.decompile_pyc(P, use_cfg=True)
print("=== DECOMPILED ===")
print(src)
