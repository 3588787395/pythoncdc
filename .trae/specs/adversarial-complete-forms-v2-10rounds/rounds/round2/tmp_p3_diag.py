#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时诊断：dump 指定 pyc 指定 code object 的块/区域结构与含特定 opname 的块归属。"""
import sys
import os

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator


def get_code(module, name):
    code = module.code
    if hasattr(code, 'get'):
        code = code.get()
    if hasattr(code, 'to_python_code'):
        code = code.to_python_code()
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if hasattr(c, 'co_code') and c.co_name == name:
            return c
    return None


def main():
    pyc = sys.argv[1]
    coname = sys.argv[2]
    opnames = sys.argv[3].split(',') if len(sys.argv) > 3 else []
    module = load_pyc_file_v2(pyc)
    code = get_code(module, coname)
    if code is None:
        print('code not found:', coname)
        return
    print('=== code:', code.co_name, 'nblocks-instrs', len(code.co_code))
    cfa = build_cfg(code)
    cfg = cfa
    ra = RegionAnalyzer(cfg, code)
    regions = ra.analyze()
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    gen.regions = regions
    # dump blocks with target opnames
    for off, b in sorted(cfg.blocks.items()):
        instr_ops = [i.opname for i in b.instructions]
        hit = [op for op in opnames if op in instr_ops]
        if hit:
            reg = None
            for r in regions:
                if b in getattr(r, 'blocks', ()):
                    reg = '%s entry=%s' % (r.region_type.name, getattr(r.entry, 'start_offset', None))
                    break
            print('block %s ops=%s regions=%s generated=%s' % (
                off, instr_ops, reg, b in gen.generated_blocks))
    print('--- top regions ---')
    for r in regions:
        print('  %s entry=%s blocks=%s' % (
            r.region_type.name, getattr(r.entry, 'start_offset', None),
            [bb.start_offset for bb in getattr(r, 'blocks', ())]))


if __name__ == '__main__':
    main()
