# -*- coding: utf-8 -*-
"""R35 probe #10: full CFG topology around every pure cleanup epilogue, for the two shapes that
must disagree (r35_01 breaks, r35_05 must be preserved), r35_04 and the target.

Captures each code object's CFG by keeping the cfg object handed to
_generate_handler_body_statements, then analyses the graph offline:
  for each epilogue block X:  X.ops / X.preds (ops + pred&succ counts, epilogue?) /
                              X.succs / the region X heads / who claims X.
The question: does the *predecessor topology* tell apart "X is the cleanup of an explicit
source-level return" from "X is the cleanup of an implicit fall-out that the compiler duplicated"?
"""
import importlib.util
import io
import os
import sys

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


CFGS = {}
_orig = RAG.RegionASTGenerator._generate_handler_body_statements


def wrapped(self, block):
    r = _orig(self, block)
    try:
        cfg = getattr(self.region_analyzer, 'cfg', None)
        if cfg is not None and id(cfg) not in CFGS:
            CFGS[id(cfg)] = (cfg, self.region_analyzer)
    except Exception:
        pass
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
    CFGS.clear()
    dst = os.path.join(OUT, 'r10_%s.py' % label)
    if os.path.isfile(dst):
        os.remove(dst)
    pbv.decompile_single(pyc, dst)
    hit = [(c, a) for c, a in CFGS.values()
           if (getattr(c, 'name', '') or '').split('.')[-1] == fn]
    rep.append('== %s  cfgs=%d' % (label, len(hit)))
    for cfg, ana in hit:
        byoff = {}
        for b in cfg.blocks.values():
            if is_epilogue(b):
                byoff[b.start_offset] = b
        rep.append('   cfg=%s blocks=%d regions=%d epi=%s' % (
            getattr(cfg, 'name', '?'), len(cfg.blocks), len(getattr(ana, 'regions', []) or []),
            sorted(byoff)))
        for off in sorted(byoff):
            X = byoff[off]
            reg = ana.get_region_for_block(X)
            head = ana.get_entry_region_for_block(X) if hasattr(ana, 'get_entry_region_for_block') else None
            rep.append('   epi@%-6s pops=%d ops=%-46s role=%s reg=%s@%s entry_of=%s succs=%s' % (
                off, is_epilogue(X), ' '.join(ops(X)),
                str(ana.get_block_role(X)).replace('BlockRole.', ''),
                type(reg).__name__ if reg else None,
                reg.entry.start_offset if reg else '-',
                type(head).__name__ if head else None,
                [s.start_offset for s in X.successors]))
            for p in X.predecessors:
                rep.append('        pred@%-6s npred=%d nsucc=%d epi=%s ops=%s' % (
                    p.start_offset, len(p.predecessors), len(p.successors),
                    bool(is_epilogue(p)), ' '.join(ops(p)[-4:])))
                for q in p.predecessors:
                    rep.append('            pred2@%-6s npred=%d nsucc=%d epi=%s ops=%s' % (
                        q.start_offset, len(q.predecessors), len(q.successors),
                        bool(is_epilogue(q)), ' '.join(ops(q)[-4:])))
io.open(os.path.join(OUT, 'probe10_topology.txt'), 'w',
        encoding='utf-8', newline='\n').write('\n'.join(rep) + '\n')
print('\n'.join(rep))
