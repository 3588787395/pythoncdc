#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2 诊断 harness（只读，不写树）。

用法：
  python -X utf8 _r2_probe.py <pyc> <co_name> [--regions] [--ast] [--blocks] [--dis]

--regions : 构建 CFG + RegionAnalyzer.analyze() 后 dump 区域树与 block->region
--ast     : 跑 RegionASTGenerator.generate() 打印 AST JSON（生成态）
--blocks  : 打印基本块指令
--dis     : dis.dis(code)
"""
import dis
import io
import json
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


def dump_block(b, indent=''):
    ins = ' | '.join('%d:%s%s' % (i.offset, i.opname,
                                  (' %r' % (i.argval,)) if i.argval is not None else '')
                     for i in b.instructions)
    print('%sBLOCK@%d end=%d succ=%s pred=%s' % (
        indent, b.start_offset, b.end_offset,
        sorted(s.start_offset for s in (b.successors or set())),
        sorted(p.start_offset for p in (b.predecessors or set()))))
    print('%s   %s' % (indent, ins))


def dump_region(r, depth=0):
    ind = '  ' * depth
    extra = []
    for attr in ('condition_block', 'header_block', 'merge_block', 'back_edge_block',
                 'value_target', 'merge_context', 'boolop_op', 'prefix_block',
                 'for_iter_setup', 'true_value_block', 'false_value_block'):
        v = getattr(r, attr, None)
        if v is not None and not callable(v):
            if hasattr(v, 'start_offset'):
                extra.append('%s=@%d' % (attr, v.start_offset))
            elif isinstance(v, (str, int, bool)):
                extra.append('%s=%s' % (attr, v))
    for attr in ('then_blocks', 'else_blocks', 'body_blocks', 'condition_chain_blocks',
                 'finally_blocks', 'handler_blocks', 'blocks'):
        v = getattr(r, attr, None)
        if v:
            try:
                extra.append('%s=%s' % (attr, sorted(x.start_offset for x in v)))
            except Exception:
                pass
    oc = getattr(r, 'op_chain', None)
    if oc:
        extra.append('op_chain=%s' % ([(b.start_offset, op) for b, op in oc],))
    print('%sREGION %s entry=@%s %s' % (
        ind, getattr(r, 'region_type', type(r).__name__),
        getattr(r, 'entry', None) and r.entry.start_offset,
        ' '.join(extra)))
    for c in (getattr(r, 'children', None) or []):
        dump_region(c, depth + 1)


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    targets = []
    find_code(code, name, targets)
    if not targets:
        print('code object not found: %s' % name)
        return 1
    co = targets[-1]
    print('==== %s (%s) ====' % (co.co_name, getattr(co, 'co_qualname', '')))
    if '--dis' in sys.argv:
        dis.dis(co)
    cfg = build_cfg(co)
    if '--blocks' in sys.argv:
        print('---- blocks ----')
        for b in cfg.get_blocks_in_order():
            dump_block(b)
    gen = RegionASTGenerator(cfg, top_level_code=None)
    analyzer = gen.region_analyzer
    regions = analyzer.analyze()
    if '--regions' in sys.argv:
        print('---- top regions ----')
        for r in regions:
            dump_region(r, 0)
        print('---- block_to_region ----')
        for b, r in analyzer.block_to_region.items():
            print('  @%d -> %s entry=@%s' % (b.start_offset,
                  getattr(r, 'region_type', type(r).__name__),
                  getattr(r, 'entry', None) and r.entry.start_offset))
    if '--ast' in sys.argv:
        print('---- AST ----')
        try:
            ast = gen.generate()
            print(json.dumps(ast, indent=1, default=str)[:12000])
        except Exception as exc:
            import traceback
            traceback.print_exc()
    return 0


if __name__ == '__main__':
    sys.exit(main())
