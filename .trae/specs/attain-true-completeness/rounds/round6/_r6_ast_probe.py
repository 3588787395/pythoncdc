# -*- coding: utf-8 -*-
"""R6 evidence: dump region-AST dict for one function in a staged pyc."""
import json
import marshal
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg import build_cfg  # noqa: E402
from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

pyc = sys.argv[1]
fname = sys.argv[2]
outname = sys.argv[3]

raw = open(pyc, 'rb').read()
code = marshal.loads(raw[16:])
cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=code)
ast = gen.generate()


def compact(node, depth=0):
    if isinstance(node, dict):
        ntype = node.get('type')
        if ntype == 'FunctionDef' and node.get('name') != fname:
            return {'type': 'FunctionDef', 'name': node.get('name'), 'skipped': True}
        out = {}
        for k, v in node.items():
            if k in ('type', 'name', 'lineno'):
                out[k] = v
            elif isinstance(v, (list, dict)):
                out[k] = compact(v, depth + 1)
            else:
                try:
                    json.dumps(v)
                    out[k] = v
                except Exception:
                    out[k] = repr(v)
        return out
    if isinstance(node, list):
        return [compact(x, depth + 1) for x in node]
    return node


def find_fn(node):
    if isinstance(node, dict):
        if node.get('type') == 'FunctionDef' and node.get('name') == fname:
            return node
        for v in node.values():
            r = find_fn(v)
            if r is not None:
                return r
    elif isinstance(node, list):
        for x in node:
            r = find_fn(x)
            if r is not None:
                return r
    return None


fn = find_fn(ast)
with open(os.path.join(HERE, outname), 'w', encoding='utf-8') as f:
    json.dump(compact(fn), f, indent=1, ensure_ascii=False, default=repr)
print('done ' + outname)
