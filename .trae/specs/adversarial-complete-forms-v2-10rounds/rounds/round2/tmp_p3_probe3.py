#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""临时探针3：追踪 STORE_NAME D 在块语句主体中的分支。"""
import sys
ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)

from core.pyc_loader_v2 import load_pyc_file_v2
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

module = load_pyc_file_v2(sys.argv[1])
code = module.code
if hasattr(code, 'get'):
    code = code.get()
if hasattr(code, 'to_python_code'):
    code = code.to_python_code()


def find(code, name):
    if code.co_name == name:
        return code
    for c in code.co_consts:
        if hasattr(c, 'co_code'):
            r = find(c, name)
            if r is not None:
                return r
    return None


cls = find(code, 'CAssign')
cfg = build_cfg(cls)
ra = RegionAnalyzer(cfg, cls)
regions = ra.analyze()
gen = RegionASTGenerator(cfg, cls)
gen.regions = regions

_orig_scan = RegionASTGenerator._scan_prefix_chain_assign
_orig_bss = RegionASTGenerator._build_store_statement


def p_scan(self, instrs, store_idx, stmt_instrs):
    res = _orig_scan(self, instrs, store_idx, stmt_instrs)
    print('[scan] idx=%s tail=%s -> end=%s stmt=%s' % (
        store_idx,
        stmt_instrs[-1].opname if stmt_instrs else None,
        res[1], str(res[0])[:80]))
    return res


def p_bss(self, instrs, block=None):
    res = _orig_bss(self, instrs, block)
    print('[bss] instrs=%s -> %s' % (
        [i.opname for i in instrs][-4:], str(res)[:80]))
    return res


RegionASTGenerator._scan_prefix_chain_assign = p_scan
RegionASTGenerator._build_store_statement = p_bss
out = gen.generate()
for s in out.get('body', []):
    print('STMT:', s.get('type'), str(s.get('targets') or s.get('target'))[:120])
