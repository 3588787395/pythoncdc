# -*- coding: utf-8 -*-
"""R5 x05 with_in_match：trace _generate_with/_generate_if_region 产物结构。

用法: python -X utf8 _r5_x05_wtrace.py <pyc> <out.txt>
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
pyc, out_path = sys.argv[1], sys.argv[2]

out = open(out_path, 'w', encoding='utf-8')


def log(msg):
    out.write(str(msg) + '\n')
    out.flush()


sys.path.insert(0, ROOT)
os.chdir(ROOT)

from core.cfg import region_ast_generator as G  # noqa: E402

orig_with = G.RegionASTGenerator._generate_with
orig_if = G.RegionASTGenerator._generate_region
depth = {'n': 0}
state2 = {}


def off(b):
    return getattr(b, 'start_offset', None)


def summarize(node, ind=0):
    pad = '  ' * ind
    if isinstance(node, list):
        for n in node:
            summarize(n, ind)
        return
    if not isinstance(node, dict):
        log('%s<%s>' % (pad, type(node).__name__))
        return
    t = node.get('type')
    extra = ''
    if t == 'With':
        items = node.get('items') or []
        names = []
        for it in items:
            if isinstance(it, dict):
                ctx = it.get('context_expr')
                names.append(str(ctx)[:60])
        extra = 'items=%s' % names
    log('%s%s %s' % (pad, t, extra))
    for key in ('body', 'orelse', 'handlers', 'finalbody'):
        v = node.get(key)
        if isinstance(v, list) and v:
            log('%s .%s:' % (pad, key))
            summarize(v, ind + 2)


def peek(node):
    if not isinstance(node, dict):
        return repr(node)[:80]
    t = node.get('type')
    if t == 'With':
        items = node.get('items') or []
        names = [str(it.get('context_expr'))[:50] for it in items if isinstance(it, dict)]
        return 'With items=%s' % names
    return str(t)


def wrap_with(self, region, *args, **kwargs):
    if getattr(self.cfg, 'name', None) == 'with_in_match':
        log('=== _generate_with entry=%s blocks=%s ===' % (
            off(region.entry), sorted(off(b) for b in region.blocks)))
        try:
            r = orig_with(self, region, *args, **kwargs)
        except BaseException as e:
            import traceback
            log('  !! _generate_with EXC %r' % (e,))
            log(traceback.format_exc())
            raise
        log('  -> %s' % peek(r))
        body = r.get('body') if isinstance(r, dict) else None
        if isinstance(body, list):
            for s in body:
                log('     stmt %s' % peek(s))
        return r
    return orig_with(self, region, *args, **kwargs)


def wrap_region(self, region, *args, **kwargs):
    if getattr(self.cfg, 'name', None) == 'with_in_match':
        depth['n'] += 1
        d = depth['n']
        kind = type(region).__name__
        e = off(getattr(region, 'entry', None))
        if kind == 'WithRegion' and e == 14:
            state2['w14'] = state2.get('w14', 0) + 1
            if state2['w14'] >= 2:
                import traceback
                stack = traceback.format_stack()
                keep = [ln.strip() for ln in stack if 'region_ast_generator.py' in ln]
                log('!!!! re-enter WithRegion@14 call#%d stack:' % state2['w14'])
                for ln in keep[-12:]:
                    log('      | %s' % ln)
        if d <= 6:
            log('%s> gen_region %s entry=%s' % ('  ' * d, kind, e))
        try:
            r = orig_if(self, region, *args, **kwargs)
        except BaseException as ex:
            import traceback
            log('%s!! gen_region %s entry=%s EXC %r' % ('  ' * d, kind, e, ex))
            log(traceback.format_exc())
            depth['n'] -= 1
            raise
        if d <= 6:
            if isinstance(r, list):
                for s in r:
                    log('%s  <- %s' % ('  ' * d, peek(s)))
            else:
                log('%s  <- %s' % ('  ' * d, peek(r)))
        depth['n'] -= 1
        return r
    return orig_if(self, region, *args, **kwargs)


G.RegionASTGenerator._generate_with = wrap_with
G.RegionASTGenerator._generate_region = wrap_region

sys.argv = ['pycdc.py', pyc, '-o', os.path.join(HERE, '_r5_x05_wtrace_ok.py')]
try:
    runpy.run_path(os.path.join(ROOT, 'pycdc.py'), run_name='__main__')
except SystemExit as e:
    import traceback
    log('SystemExit %s' % e)
    log(traceback.format_exc())
except Exception as e:
    import traceback
    log('EXC %r' % e)
    log(traceback.format_exc())
finally:
    out.close()
