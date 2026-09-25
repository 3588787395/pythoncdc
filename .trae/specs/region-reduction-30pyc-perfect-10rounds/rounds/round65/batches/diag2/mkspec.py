# -*- coding: utf-8 -*-
"""Build a spec json from the LIVE repo bytes (read-only) so the anchor is exact."""
import io
import json
import sys

P = r'F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py'


def norm():
    s = io.open(P, encoding='utf-8-sig', newline='').read()
    return s.replace('\r\n', '\n')


def lines_of(u):
    return u.split('\n')


def make(out_path, repl):
    u = norm()
    L = lines_of(u)
    a = '\n'.join(L[36003:36018])
    assert u.count(a) == 1, ('anchor count', u.count(a))
    patched = u.replace(a, repl)
    assert patched != u
    compile(patched, P, 'exec')
    spec = {'file': 'core/cfg/region_ast_generator.py',
            'edits': [{'anchor': a, 'repl': repl}]}
    io.open(out_path, 'w', encoding='utf-8').write(json.dumps(spec, ensure_ascii=False))
    print('wrote', out_path, 'anchor lines', len(a.split('\n')), 'repl lines', len(repl.split('\n')))


if __name__ == '__main__':
    repl = io.open(sys.argv[1], encoding='utf-8').read()
    if repl.endswith('\n'):
        repl = repl[:-1]
    make(sys.argv[2], repl)
