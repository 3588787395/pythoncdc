#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B104 trace harness (monkeypatch, no tree modification)."""
import sys
import marshal
import types

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def find(c, n):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            if k.co_name == n:
                return k
            r = find(k, n)
            if r is not None:
                return r
    return None


def main():
    pyc = sys.argv[1]
    name = sys.argv[2]
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    co = find(code, name)
    cfg = build_cfg(co)
    gen = RegionASTGenerator(cfg, top_level_code=None)

    _orig_gbs = gen._generate_block_statements

    def gbs(block, *a, **k):
        out = _orig_gbs(block, *a, **k)
        if out:
            print('[gbs block@%d] -> %s' % (block.start_offset,
                  [s.get('type') if isinstance(s, dict) else s for s in out]))
        return out
    gen._generate_block_statements = gbs

    _orig_br = gen._if_generate_branch_stmts

    def br(blocks, *a, **k):
        out = _orig_br(blocks, *a, **k)
        print('[branch %s] -> %s' % (
            [b.start_offset for b in blocks],
            [s.get('type') if isinstance(s, dict) else s for s in (out or [])]))
        return out
    gen._if_generate_branch_stmts = br

    _orig_gen = gen._generate_region

    def gen_region(region, *a, **k):
        print('[enter region %s entry=@%s]' % (
            getattr(region, 'region_type', '?'),
            getattr(region, 'entry', None) and region.entry.start_offset))
        out = _orig_gen(region, *a, **k)
        print('[exit region %s] -> %s' % (
            getattr(region, 'region_type', '?'),
            [s.get('type') if isinstance(s, dict) else s for s in out] if isinstance(out, list) else (out or {}).get('type')))
        return out
    gen._generate_region = gen_region

    ast = gen.generate()
    import json
    print('==== final ====')
    print(json.dumps(ast, indent=1, default=str)[:4000])


if __name__ == '__main__':
    main()
