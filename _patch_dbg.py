import io
import json
import sys
import os

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

import _probe_r3 as P
from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator


def dump(node, indent=0, maxdepth=12):
    pad = '  ' * indent
    if indent > maxdepth:
        print(pad + '...')
        return
    if isinstance(node, dict):
        t = node.get('type')
        extra = {k: v for k, v in node.items()
                 if k not in ('body', 'orelse', 'finalbody', 'handlers', 'orelse',
                              'test', 'value', 'left', 'right', 'targets', 'func',
                              'args', 'elts', 'values', 'names', 'msg', 'attr',
                              'operand', 'ops', 'slice', 'keywords', 'ctx',
                              'flags', 'decorator_list', 'returns', 'annotations')}
        print('%s%s %s' % (pad, t, json.dumps({k: str(v)[:70] for k, v in extra.items()},
                                              ensure_ascii=False)))
        for key in ('body', 'orelse', 'finalbody', 'handlers'):
            v = node.get(key)
            if isinstance(v, list) and v:
                print('%s.%s:' % (pad, key))
                for it in v:
                    dump(it, indent + 1, maxdepth)
    elif isinstance(node, list):
        for it in node:
            dump(it, indent, maxdepth)
    else:
        print(pad + str(node))


def main():
    pyc = sys.argv[1]
    func = sys.argv[2] if len(sys.argv) > 2 else None
    code = P.load_code(pyc, func) if func else P.load_code(pyc, None)
    cfg = build_cfg(code)
    gen = RegionASTGenerator(cfg, top_level_code=code if code.co_name == '<module>' else None)
    ast_dict = gen.generate()
    if func:
        # locate function node
        found = []

        def walk(n):
            if isinstance(n, dict):
                if n.get('type') == 'FunctionDef' and (n.get('name') == func):
                    found.append(n)
                for v in n.values():
                    walk(v)
            elif isinstance(n, list):
                for v in n:
                    walk(v)
        walk(ast_dict)
        if found:
            dump(found[0])
        else:
            print('function node not found; dumping all')
            dump(ast_dict)
    else:
        dump(ast_dict)


if __name__ == '__main__':
    main()
