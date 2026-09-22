# -*- coding: utf-8 -*-
"""R35 probe #9: why does the same E-integ-D1 emission site break r35_01 but not r35_05?

Every call of _generate_handler_body_statements is recorded at the emission moment with the
structural facts of the block and of every other pure cleanup-epilogue block in the same code
object (POP_EXCEPT*[LOAD_CONST]RETURN): ops, predecessor ops, successors, block role, owning
region, and whether it is already in generated_blocks.

Read-only: nothing in the repo is modified; products go to scratch.
"""
import importlib.util
import io
import os
import sys
import traceback

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
DST = REPO + '/test_repros/round35_epilogue_duplicate_return'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg import region_ast_generator as RAG  # noqa: E402

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
CFGS = {}
_orig = RAG.RegionASTGenerator._generate_handler_body_statements


def short(r):
    out = []
    for st in r:
        t = st.get('type')
        if t == 'Return':
            v = st.get('value') or {}
            out.append('Return(%r)' % v.get('value', v.get('type')))
        else:
            out.append(t)
    return out


def wrapped(self, block):
    r = _orig(self, block)
    try:
        site = None
        for fr in reversed(traceback.extract_stack()[:-1]):
            if fr.filename.endswith('region_ast_generator.py') and fr.lineno != 25627:
                site = fr.lineno
                break
        cfg = getattr(self.region_analyzer, 'cfg', None)
        if cfg is None:
            return r
        CFGS[id(cfg)] = (cfg, getattr(cfg, 'name', '?'))
        byoff = {}
        for b in cfg.blocks.values():
            if is_epilogue(b):
                byoff[b.start_offset] = b
        ep = sorted(byoff)
        reg = self.region_analyzer.get_region_for_block(block)
        ROWS.append({
            'cid': id(cfg), 'fn': CFGS[id(cfg)][1], 'caller': site, 'blk': block.start_offset,
            'E': bool(is_epilogue(block)), 'stmts': tuple(short(r)),
            'role': str(self.region_analyzer.get_block_role(block)).replace('BlockRole.', ''),
            'reg': '%s@%s' % (type(reg).__name__ if reg else None,
                              reg.entry.start_offset if reg else '-'),
            'preds': [(p.start_offset, ops(p)[-3:], bool(is_epilogue(p))) for p in block.predecessors],
            'succs': [s.start_offset for s in block.successors],
            'ops': ops(block),
            'epi': ep,
            'claimed_at_call': {o: (byoff[o] in self.generated_blocks) for o in ep},
        })
    except Exception as e:
        ROWS.append({'error': repr(e)[:150]})
    return r


RAG.RegionASTGenerator._generate_handler_body_statements = wrapped

_bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_bv)
_bv.loader.exec_module(pbv)

TARGETS = [
    ('shape01', os.path.join(DST, 'r35_01_witness_dup_epilogue_fallthrough.pyc'), 'store'),
    ('shape04', os.path.join(DST, 'r35_04_control_depth2_fallout.pyc'), 'store'),
    ('shape05', os.path.join(DST, 'r35_05_negative_real_return_at_depth3.pyc'), 'store'),
    ('target', REPO + '/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc',
     'save_testds_to_json'),
]

rep = []
for label, pyc, fn in TARGETS:
    del ROWS[:]
    CFGS.clear()
    dst = os.path.join(OUT, 'r9_%s.py' % label)
    if os.path.isfile(dst):
        os.remove(dst)
    pbv.decompile_single(pyc, dst)
    res = pbv.bytecode_diff(pyc, dst)
    rep.append('   RAWROWS=%d errors=%d fns=%s' % (
        len(ROWS), len([r for r in ROWS if 'error' in r]),
        sorted(set((r.get('fn') or '?') for r in ROWS))[:6]))
    for r in ROWS[:3]:
        rep.append('   raw %s' % str(r)[:300])
    hits = [r for r in ROWS if (r.get('fn') or '').split('.')[-1] == fn]
    lone = [r for r in hits if r['E'] and r['stmts'] == ('Return(None)',)]
    rep.append('== %-8s official %d/%d  calls=%d epilogue-return-sites=%d' % (
        label, res['matched_functions'], res['total_functions'], len(hits), len(lone)))
    for r in lone:
        rep.append('   SITE caller=%s blk@%-6s pops=%s role=%s reg=%s ops=%s' % (
            r['caller'], r['blk'], is_epilogue_next := len([x for x in r['ops'] if x == 'POP_EXCEPT']),
            r['role'], r['reg'], r['ops']))
        rep.append('        preds=%s' % r['preds'])
        rep.append('        succs=%s epi=%s claimed=%s' % (
            r['succs'], r['epi'], r['claimed_at_call']))
    # epilogue blocks that never reached this call site
    by_cid = {}
    for r in hits:
        by_cid[r['cid']] = r['epi']
    for cid, ep in by_cid.items():
        seen = set(r['blk'] for r in hits if r['cid'] == cid)
        rep.append('   epi-set %s = %s ; never passed to _generate_handler_body_statements: %s'
                   % (CFGS[cid][1], ep, sorted(set(ep) - seen)))
io.open(os.path.join(OUT, 'probe9_epilogue_structures.txt'), 'w',
        encoding='utf-8', newline='\n').write('\n'.join(rep) + '\n')
print('\n'.join(rep))
