#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R4 AST dump：对 pyc 跑 RegionASTGenerator.generate()，dump AST dict（JSON）。
用法: python _r4_astdump.py <pyc> [--out out.json]
"""
import io
import json
import marshal
import os
import sys
import types

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def main():
    pyc = sys.argv[1]
    out = None
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
    data = open(pyc, 'rb').read()
    code = marshal.loads(data[16:])
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    ast_dict = gen.generate()
    txt = json.dumps(ast_dict, ensure_ascii=False, indent=1, default=str)
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(txt)
        print('wrote', out, len(txt))
    else:
        sys.stdout.write(txt)


if __name__ == '__main__':
    main()
