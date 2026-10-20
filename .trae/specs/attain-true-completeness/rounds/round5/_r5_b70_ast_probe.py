# -*- coding: utf-8 -*-
"""R5 B70 probe: dump generated AST dicts for while_with_whole_body."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator  # noqa: E402

orig_gw = RegionASTGenerator._generate_with
orig_gl = RegionASTGenerator._generate_loop


def dump(node, depth=0, out=None):
    pad = '  ' * depth
    if isinstance(node, dict):
        t = node.get('type')
        extra = ''
        for k in ('test', 'value', 'targets', 'items'):
            if k in node and not isinstance(node[k], (dict, list)):
                extra += ' %s=%r' % (k, node[k])
        out.append('%s%s%s' % (pad, t, extra))
        for k in ('body', 'orelse', 'finalbody', 'handlers', 'items'):
            v = node.get(k)
            if isinstance(v, list):
                out.append('%s %s:[' % (pad, k))
                for c in v:
                    dump(c, depth + 2, out)
                out.append('%s ]' % pad)
            elif isinstance(v, dict):
                out.append('%s %s:[' % (pad, k))
                dump(v, depth + 2, out)
                out.append('%s ]' % pad)
    elif isinstance(node, list):
        out.append('%s[' % pad)
        for c in node:
            dump(c, depth + 1, out)
        out.append('%s]' % pad)
    else:
        out.append('%s%r' % (pad, node))


def probe_gw(self, region):
    res = orig_gw(self, region)
    e = getattr(region, 'entry', None)
    if e is not None and e.start_offset in (4,):
        out = ['=== _generate_with WithRegion@%s ===' % e.start_offset]
        dump(res, 0, out)
        print('\n'.join(out))
    return res


def probe_gl(self, region, **kw):
    e = getattr(region, 'entry', None)
    if e is not None and e.start_offset in (4,):
        res = orig_gl(self, region, **kw)
        out = ['=== _generate_loop LoopRegion@%s ===' % e.start_offset]
        dump(res, 0, out)
        print('\n'.join(out))
        return res
    return orig_gl(self, region, **kw)


RegionASTGenerator._generate_with = probe_gw
RegionASTGenerator._generate_loop = probe_gl

import io  # noqa: E402

buf = io.StringIO()
_old = sys.stdout
sys.stdout = buf
from pycdc import decompile_pyc  # noqa: E402
src = decompile_pyc(r'test_repros\round9\rv9_02_b66_with_nest.pyc')
sys.stdout = _old
open(os.path.join(HERE, '_r5_b70_ast.txt'), 'w', encoding='utf-8').write(buf.getvalue())
print('done')
