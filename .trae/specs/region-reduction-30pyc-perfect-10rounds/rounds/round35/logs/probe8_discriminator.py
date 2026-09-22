# -*- coding: utf-8 -*-
"""R35 probe #8: does a *CFG-side* structural discriminator separate the one improving site
from the ten regressing sites of probe #7?

Candidate fact set, evaluated at the real emission moment (the fall-through arm of _generate_try
calling _generate_handler_body_statements, caller line 24695) for every handler-tail lone
`Return(None)`:

  E  = the emitting block's filtered ops are pure cleanup -> terminal return (POP_EXCEPT* [LOAD_CONST] RETURN*)
  D1 = there is another block of the same shape in the same CFG
  D2 = ... and that other block is NOT yet in generated_blocks (the core emits nothing for it)
  D3 = ... and its predecessor chain is cleanup-only too
  P  = POP_EXCEPT multiplicity of each

Nothing in the repo is written; the patched generator runs against copies in scratch.
"""
import importlib.util
import io
import json
import os
import sys
import traceback

REPO = r'F:\Downloads\pythoncdc-main'
OUT = r'D:/Temp/r35gate/r35'
sys.path.insert(0, REPO)
sys.stdout.reconfigure(encoding='utf-8')

from core.cfg import region_ast_generator as RAG  # noqa: E402

SP = REPO + '/site-packages/'
SITES = [  # (pyc relpath, function name, verdict of probe #7)
    ('IQEngine/plugins/plugin_system_risk_calculation/function.pyc', 'save_testds_to_json', 'IMPROVED'),
    ('IQData/data/date_set_storage.pyc', 'get_date_set', 'REGRESSED'),
    ('IQEngine/account/base_position.pyc', '__missing__', 'REGRESSED'),
    ('IQEngine/plugins/plugin_fly_data/fly_api/base.pyc', 'cancel_order', 'REGRESSED'),
    ('IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc', 'over_night_order', 'REGRESSED'),
    ('IQEngine/plugins/plugin_fly_data/fly_api/order_api_trade.pyc', 'order_market', 'REGRESSED'),
    ('IQEngine/plugins/plugin_system_simulation/live.pyc', '_on_entrust_rsp', 'REGRESSED'),
    ('IQEngine/plugins/plugin_system_trade/send_message_api.pyc', 'send_qywx', 'REGRESSED'),
    ('IQEngine/plugins/plugin_system_trade/send_message_api.pyc', 'send_email', 'REGRESSED'),
    ('fly/common/future_param.pyc', 'load_future_info_from_pbox', 'REGRESSED'),
]

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
_orig = RAG.RegionASTGenerator._generate_handler_body_statements


def wrapped(self, block):
    r = _orig(self, block)
    try:
        lone_return_none = (len(r) == 1 and r[0].get('type') == 'Return'
                            and (r[0].get('value') or {}).get('type') == 'Constant'
                            and (r[0].get('value') or {}).get('value') is None)
        if lone_return_none:
            site = None
            for fr in reversed(traceback.extract_stack()[:-1]):
                if fr.filename.endswith('region_ast_generator.py') and fr.lineno != 25627:
                    site = fr.lineno
                    break
            cfg = getattr(self.region_analyzer, 'cfg', None)
            allb = list(cfg.blocks.values()) if hasattr(cfg, 'blocks') else []
            ep = [(b, is_epilogue(b)) for b in allb]
            ep = [(b, k) for (b, k) in ep if k]
            mine = is_epilogue(block)
            others = [(b, k) for (b, k) in ep if b is not block]
            unclaimed = [(b, k) for (b, k) in others if b not in self.generated_blocks]
            d3 = [(b, k) for (b, k) in unclaimed
                  if b.predecessors and all(is_epilogue(p) or set(ops(p)) <= {'POP_EXCEPT'}
                                            for p in b.predecessors)]
            reg = self.region_analyzer.get_region_for_block(block)
            ROWS.append({'caller': site, 'blk': block.start_offset, 'E': bool(mine),
                         'pops': mine, 'fn': getattr(cfg, 'name', '?'),
                         'n_epi': len(ep), 'epi': sorted((b.start_offset, k) for b, k in ep),
                         'D1': bool(others), 'D2': bool(unclaimed), 'D3': bool(d3),
                         'region': type(reg).__name__ if reg else None,
                         'region_entry': reg.entry.start_offset if reg else None,
                         'succs': [s.start_offset for s in block.successors],
                         'preds': [p.start_offset for p in block.predecessors],
                         'role': str(self.region_analyzer.get_block_role(block))})
    except Exception as e:
        ROWS.append({'error': repr(e)[:120]})
    return r


RAG.RegionASTGenerator._generate_handler_body_statements = wrapped

_bv = importlib.util.spec_from_file_location('pbv', REPO + '/scripts/pyc_batch_verify.py')
pbv = importlib.util.module_from_spec(_bv)
_bv.loader.exec_module(pbv)

report = []
for rel, fn, verdict in SITES:
    pyc = SP + rel.replace('/', os.sep)
    dst = os.path.join(OUT, 'r8_%s.py' % os.path.splitext(os.path.basename(rel))[0])
    del ROWS[:]
    pbv.decompile_single(pyc, dst)
    hits = [r for r in ROWS if r.get('fn') == fn or (r.get('fn') or '').endswith('.' + fn)
            or r.get('fn') == fn or fn in (r.get('fn') or '')]
    report.append('== %-58s %-30s %s  (emissions in file=%d, in this fn=%d)' % (
        rel, fn, verdict, len(ROWS), len(hits)))
    for r in hits:
        report.append('   caller=%s blk@%-6s E=%s pops=%s n_epi=%s D1=%s D2=%s D3=%s role=%s '
                      'region=%s@%s preds=%s succs=%s epi=%s' % (
                          r['caller'], r['blk'], r['E'], r['pops'], r['n_epi'], r['D1'], r['D2'],
                          r['D3'], r['role'].replace('BlockRole.', ''), r['region'],
                          r['region_entry'], r['preds'], r['succs'], r['epi']))
io.open(os.path.join(OUT, 'probe8_discriminator.txt'), 'w', encoding='utf-8', newline='\n').write(
    '\n'.join(report) + '\n')
print('\n'.join(report))
