#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2: trace _generate_boolop_impl branch firing for one function (generate-only)."""
import io
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg import region_ast_generator as _rag
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = sys.argv[1]
name = sys.argv[2]
data = open(pyc, 'rb').read()
code = marshal.loads(data[16:])


def find_code(code, name, out):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                out.append(const)
            find_code(const, name, out)


targets = []
find_code(code, name, targets)
co = targets[-1]
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)

_orig_impl = RegionASTGenerator._generate_boolop_impl
_orig_gbs = RegionASTGenerator._generate_block_statements
_orig_gsi = RegionASTGenerator._generate_stmts_from_instrs
_orig_recon = gen.expr_reconstructor.reconstruct


def _wrap_impl(self, region, skip_store_targets=None):
    print('[IMPL] entry=@%s merge=@%s chain=%s vt=%s blocks=%s' % (
        getattr(region.entry, 'start_offset', None),
        getattr(region.merge_block, 'start_offset', None),
        [(getattr(b, 'start_offset', None), o) for b, o in region.op_chain],
        region.value_target,
        [getattr(b, 'start_offset', None) for b in region.blocks]))
    _mb = region.merge_block
    if _mb is not None:
        print('[IMPL] merge instrs=%s' % [(i.opname, i.argval) for i in _mb.instructions])
    r = _orig_impl(self, region, skip_store_targets)
    if r:
        print('[IMPL] result types=%s' % [s.get('type') for s in r if isinstance(s, dict)])
    else:
        print('[IMPL] result=None')
    return r


def _wrap_gbs(self, block):
    _bi = [(i.opname, i.argval) for i in block.instructions] if block is not None else None
    r = _orig_gbs(self, block)
    print('[GBS] block=@%s instrs=%s -> %s' % (
        getattr(block, 'start_offset', None), _bi,
        [s.get('type') for s in r] if r else r))
    return r


def _wrap_gsi(self, instrs, block):
    r = _orig_gsi(self, instrs, block)
    print('[GSI] block=@%s instrs=%s -> %s' % (
        getattr(block, 'start_offset', None), [i.opname for i in instrs],
        [s.get('type') for s in r] if r else r))
    return r


def _wrap_recon(self, instrs, initial_stack=None):
    r = _orig_recon(self, instrs, initial_stack=initial_stack)
    if initial_stack is not None:
        print('[RECON] instrs=%s init_size=%s -> %s' % (
            [i.opname for i in instrs], len(initial_stack),
            (r or {}).get('type', r) if isinstance(r, dict) else r))
    return r


RegionASTGenerator._generate_boolop_impl = _wrap_impl
RegionASTGenerator._generate_block_statements = _wrap_gbs
RegionASTGenerator._generate_stmts_from_instrs = _wrap_gsi
gen.expr_reconstructor.reconstruct = types.MethodType(_wrap_recon, gen.expr_reconstructor)

out = gen.generate()
print('DONE', type(out))
