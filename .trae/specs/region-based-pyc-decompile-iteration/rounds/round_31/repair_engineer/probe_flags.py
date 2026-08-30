"""Probe: dump _generate_elif_or_else 收到的 orelse.nodes 属性（复现 make 结构）。"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.code_generator import CodeGenerator

orig = CodeGenerator._generate_elif_or_else


def summ(x, depth=0):
    pad = '  ' * depth
    if isinstance(x, list):
        if not x:
            return '[]'
        return '[\n' + '\n'.join(pad + '  ' + summ(s, depth + 1) for s in x) + '\n' + pad + ']'
    if hasattr(x, 'test'):  # ASTIf
        s = 'If(test=%r, _is_elif=%s, _is_nested_if=%s' % (
            x.test, getattr(x, '_is_elif', None), getattr(x, '_is_nested_if', None))
        s += ', body=%s' % summ(x.body.nodes if x.body else [])
        s += ', orelse=%s' % summ(x.orelse.nodes if x.orelse else [])
        return s + ')'
    return '%s(%s)' % (type(x).__name__, repr(getattr(x, 'targets', getattr(x, 'value', x)))[:40])


def patched(self, orelse, *a, **kw):
    nodes = orelse.nodes if orelse else []
    if len(nodes) >= 2 and hasattr(nodes[0], 'test'):
        print('=== GEIO call, %d nodes ===' % len(nodes))
        print(summ(nodes))
    return orig(self, orelse, *a, **kw)


CodeGenerator._generate_elif_or_else = patched

from pycdc import decompile_pyc
decompile_pyc(sys.argv[1], use_cfg=True)
