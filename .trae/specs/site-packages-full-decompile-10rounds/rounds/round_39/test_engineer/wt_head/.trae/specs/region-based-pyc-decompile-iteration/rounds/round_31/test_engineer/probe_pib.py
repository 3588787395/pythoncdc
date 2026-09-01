"""Probe: 追踪 _process_if_blocks 细节（final else [1272,1300,1414,1442]）。"""
import sys

ROOT = r'F:\Downloads\pythoncdc-main'
sys.path.insert(0, ROOT)

from core.cfg.region_ast_generator import RegionASTGenerator

orig_pib = RegionASTGenerator._process_if_blocks
orig_chain = RegionASTGenerator._if_generate_elif_chain


def summ(x, depth=0):
    if isinstance(x, list):
        return '[%s]' % ' | '.join(summ(s, depth + 1) for s in x) if x else '[]'
    if isinstance(x, dict):
        t = x.get('type')
        if t == 'If':
            orelse = x.get('orelse')
            s = 'If(test=%s, body=%s' % (summ(x.get('test')), summ(x.get('body')))
            if orelse:
                s += ', orelse=%s' % summ(orelse)
            if x.get('_is_elif'):
                s += ' ELIF'
            return s + ')'
        if t == 'Assign':
            return 'Assign(%s)' % x.get('targets')
        if t == 'Return':
            return 'Return'
        return str(t)
    return repr(x)[:40]


def p_pib(self, blocks, region, branch='then', *a, **kw):
    offs = [getattr(b, 'start_offset', '?') for b in (blocks or [])]
    r = orig_pib(self, blocks, region, branch, *a, **kw)
    if offs and any(o in (1272, 1300, 1414, 1442) for o in offs):
        print('PIB branch=%s blocks=%s region_entry=%s -> %s' % (
            branch, offs, getattr(getattr(region, 'entry', None), 'start_offset', '?'), summ(r)))
    return r


def p_chain(self, region, *a, **kw):
    r = orig_chain(self, region, *a, **kw)
    eo = getattr(getattr(region, 'entry', None), 'start_offset', '?')
    if eo in (0, 1272):
        print('CHAIN entry=%s -> %s' % (eo, summ(r)))
    return r


RegionASTGenerator._process_if_blocks = p_pib
RegionASTGenerator._if_generate_elif_chain = p_chain

from pycdc import decompile_pyc
decompile_pyc(sys.argv[1], use_cfg=True)
