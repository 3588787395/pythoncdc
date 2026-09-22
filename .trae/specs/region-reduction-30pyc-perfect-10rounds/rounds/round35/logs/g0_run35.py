# -*- coding: utf-8 -*-
"""Round 35 G0 runner: measure the five shapes on the LANDED core (repo core at HEAD).

Per shape we print
  official   m/n from scripts/pyc_batch_verify.bytecode_diff
  strict     kind + delta + the non-equal opcode hunks (the target signature is
             delete ['POP_EXCEPT','POP_EXCEPT','LOAD_CONST','RETURN_VALUE'])
  emitted    how many `return None` lines the product has vs the shape source
  decidable  whether the shape's handler-tail `return None` choice is visible in the bytecode
             at all (compare src vs alt instruction sequences)
  sites      the emission rows at _generate_handler_body_statements, with the candidate
             structural facts E (pure cleanup epilogue) and D1 (>=1 sibling epilogue)

G0 criterion: the WITNESS must FAIL on landed bytes and every CONTROL must PASS.
usage: python -X utf8 g0_run35.py [arm-dir]
"""
import difflib
import dis
import importlib.util
import io
import os
import sys

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
DST = REPO + '/test_repros/round35_epilogue_duplicate_return'
CORE = sys.argv[1] if len(sys.argv) > 1 else REPO
sys.path.insert(0, CORE)
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, OUT)
from shapes35 import SHAPES  # noqa: E402

_s = importlib.util.spec_from_file_location('r10', REPO + '/_r10_strict_check.py')
r10 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(r10)

_bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_bv)
_bv.loader.exec_module(pbv)

import py_compile  # noqa: E402

FILTERED_OUT = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')


def ops(b):
    return [i.opname for i in b.instructions if i.opname not in FILTERED_OUT]


def is_epilogue(b):
    o = ops(b)
    if not o or 'POP_EXCEPT' not in o:
        return 0
    if o[-1] not in ('RETURN_VALUE', 'RETURN_CONST'):
        return 0
    core = o[:-1]
    if core and core[-1] == 'LOAD_CONST':
        core = core[:-1]
    if not core or any(x != 'POP_EXCEPT' for x in core):
        return 0
    return o.count('POP_EXCEPT')


ROWS = []
from core.cfg import region_ast_generator as RAG  # noqa: E402
_orig = RAG.RegionASTGenerator._generate_handler_body_statements


def wrapped(self, block):
    r = _orig(self, block)
    try:
        lone = (len(r) == 1 and r[0].get('type') == 'Return'
                and (r[0].get('value') or {}).get('type') == 'Constant'
                and (r[0].get('value') or {}).get('value') is None)
        if lone:
            site = None
            import traceback as tb
            for fr in reversed(tb.extract_stack()[:-1]):
                if fr.filename.endswith('region_ast_generator.py') and fr.lineno != 25627:
                    site = fr.lineno
                    break
            cfg = getattr(self.region_analyzer, 'cfg', None)
            ep = [(b, is_epilogue(b)) for b in (cfg.blocks.values() if cfg is not None else [])]
            ep = [(b, k) for (b, k) in ep if k]
            others = [(b, k) for (b, k) in ep if b is not block]
            ROWS.append({'caller': site, 'blk': block.start_offset, 'E': bool(is_epilogue(block)),
                         'pops': is_epilogue(block), 'n_epi': len(ep), 'D1': bool(others),
                         'epi': sorted((b.start_offset, k) for b, k in ep)})
    except Exception as e:
        ROWS.append({'error': repr(e)[:120]})
    return r


RAG.RegionASTGenerator._generate_handler_body_statements = wrapped


def code_of(src):
    co = compile(src, '<s>', 'exec')
    for c in co.co_consts:
        if type(c).__name__ == 'code' and c.co_name == 'store':
            return c
    raise KeyError('store')


def seq(src):
    return [i.opname for i in dis.get_instructions(code_of(src)) if i.opname != 'CACHE']


def tok(i):
    if r10._is_jump(i.opname):
        return ('<JUMP>', r10._norm_jump_op(i.opname))
    return (r10._norm_arg(i), i.opname)


rep = ['CORE=%s' % CORE]
nv = 0
for name in sorted(SHAPES):
    sh = SHAPES[name]
    pyc = os.path.join(DST, name + '.pyc')
    prod = os.path.join(OUT, 'g0_%s.py' % name)
    if os.path.isfile(prod):
        os.remove(prod)
    del ROWS[:]
    pbv.decompile_single(pyc, prod)
    res = pbv.bytecode_diff(pyc, prod)
    rows = ['%s %d/%d jd%s td%s' % (m['name'], m['orig_count'], m['decomp_count'],
                                    m['jump_diffs'], m['true_diffs'])
            for m in res['mismatches']]
    src_ret = sum(1 for l in sh['src'].split('\n') if l.strip() == 'return None')
    txt = io.open(prod, encoding='utf-8-sig').read()
    nret = sum(1 for l in txt.split('\n') if l.strip() == 'return None')
    try:
        a, b = seq(sh['src']), seq(sh['alt'])
        dec = ('DETERMINED(+%d)' % (len(a) - len(b))) if a != b else 'UNDERDETERMINED'
    except Exception as e:
        dec = 'ERR %s' % repr(e)[:60]
    tmp = os.path.join(OUT, 'g0c_%s.pyc' % name)
    py_compile.compile(prod, cfile=tmp, doraise=True, quiet=2)
    o, d = r10._load_map(pyc), r10._load_map(tmp)
    key = [k for k in o if k.split('.')[-1] == 'store'][0]
    kind, msg, defect = r10.strict_compare(o[key], d[key])
    fo, fd = r10.filtered(o[key]), r10.filtered(d[key])
    hunks = []
    for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [tok(x) for x in fo],
                                                     [tok(x) for x in fd],
                                                     autojunk=False).get_opcodes():
        if t != 'equal':
            hunks.append('%s@%s %s -> %s' % (t, fo[i1].offset if i1 < len(fo) else 'EOF',
                                             [x.opname for x in fo[i1:i2]],
                                             [x.opname for x in fd[j1:j2]]))
    ok = (res['matched_functions'] == res['total_functions'] and not defect)
    nv += 1 if ok else 0
    rep.append('%-46s %s  official %d/%d  strict %s lo=%d ld=%d delta%+d  src_ret=%d emitted_ret=%d'
               ' tail-choice=%s %s' % (
                   name, 'PASS' if ok else 'FAIL', res['matched_functions'],
                   res['total_functions'], kind, len(fo), len(fd), len(fd) - len(fo),
                   src_ret, nret, dec, ('| ' + '; '.join(rows)) if rows else ''))
    for h in hunks:
        rep.append('      hunk %s' % h[:200])
    for r in ROWS:
        rep.append('      site %s' % r)
rep.append('PASS %d / %d' % (nv, len(SHAPES)))
io.open(os.path.join(OUT, 'g0_landed.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(rep) + '\n')
print('\n'.join(rep))
