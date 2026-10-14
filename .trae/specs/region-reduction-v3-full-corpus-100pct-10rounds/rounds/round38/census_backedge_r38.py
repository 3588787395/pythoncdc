"""Population census: loops whose designated back_edge_block is NOT the header-landing back edge.

Hypothesis measured here (region_analyzer.py:4958-5001): `back_edges_for_header` collects every
theoretical back edge of the loop, including source-level `continue`s whose operand lands on the
pure-noise pre-header block (CPython 3.11's continue re-entry NOP), and the pre-header exclusion at
:4960 only runs when `condition_block == header`. Loops whose region carries
`condition_block is None` while the header block itself ends in a conditional jump skip that filter,
and the selection key at :4992 then prefers the block with MORE body instructions, so a fat
`else: stmt; continue` block beats the true body tail and becomes `back_edge_block`.

For every LoopRegion of the 20 panel files this prints:
  mis           designated back_edge_block's backward operand lands on a block other than header_block
  better_exists some other loop block's backward operand lands exactly on header_block
  changes       the designation would move to a different block if the filter ran (the actionable set)

usage: python -X utf8 census_backedge_r38.py [nfiles]
"""
import dis
import marshal
import os
import sys

REPO = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main"
sys.path.insert(0, REPO)
from core.cfg import build_cfg                                        # noqa: E402
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion       # noqa: E402

NOISE = ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG', 'PUSH_NULL')
BACK = ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
CO = type(compile('', '', 'exec'))

FILES = [
    'fly/data/quote.pyc',
    'IQCommon/api/klinedata.pyc',
    'IQCommon/logger/handlers.pyc',
    'IQCommon/strategy/wizard_quant_api.pyc',
    'IQCommon/util/trade_info_utils.pyc',
    'IQData/api/api_base.pyc',
    'IQData/plugins/plugin_system_realquote/real_quote.pyc',
    'IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc',
    'IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc',
    'IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc',
    'IQEngine/plugins/plugin_system_matcher/matcher.pyc',
    'IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc',
    'IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc',
    'IQCommon/arg_checker.pyc',
    'IQData/utils/arg_checker.pyc',
    'IQEngine/utils/arg_checker.pyc',
    'IQCommon/profiler_func.pyc',
    'IQData/utils/profiler_func.pyc',
    'IQEngine/utils/profiler_func.pyc',
    'fly/data/quotation.pyc',
]


def gather(c, acc):
    acc.append(c)
    for x in c.co_consts:
        if isinstance(x, CO):
            gather(x, acc)


def landing(cfg, blk):
    li = blk.get_last_instruction() if blk is not None else None
    if li is None or li.opname not in BACK or li.argval is None:
        return None
    return cfg.get_block_by_offset(li.argval)


def pre_header_noise_preds(cfg, header):
    out = set()
    for p in (header.predecessors or []):
        if (p.start_offset < header.start_offset
                and all(i.opname in NOISE for i in p.instructions)
                and len(p.successors) == 1 and header in p.successors):
            out.add(p)
    return out


nf = int(sys.argv[1]) if len(sys.argv) > 1 else len(FILES)
tot = {'loops': 0, 'mis': 0, 'better': 0, 'changes': 0, 'guard_skipped': 0, 'units': 0}
rows = []
for rel in FILES[:nf]:
    pyc = os.path.join(REPO, 'site-packages', *rel.split('/'))
    if not os.path.exists(pyc):
        print('MISSING', rel)
        continue
    acc = []
    gather(marshal.loads(open(pyc, 'rb').read()[16:]), acc)
    f = {'loops': 0, 'mis': 0, 'better': 0, 'changes': 0, 'guard_skipped': 0}
    for co in acc:
        try:
            cfg = build_cfg(co)
            an = RegionAnalyzer(cfg)
            regions = an.analyze()
        except Exception as e:                                    # noqa: BLE001
            print('  analyze failed %s %s: %s' % (rel, co.co_name, e))
            continue
        f['units'] = f.get('units', 0) + 1
        for r in regions:
            if not isinstance(r, LoopRegion) or r.header_block is None:
                continue
            f['loops'] += 1
            hdr = r.header_block
            hl = hdr.get_last_instruction()
            hdr_is_test = hl is not None and 'JUMP' in hl.opname and 'FORWARD' in hl.opname
            cond_is_hdr = (r.condition_block is hdr)
            if not cond_is_hdr and hdr_is_test:
                f['guard_skipped'] += 1
            be = getattr(r, 'back_edge_block', None)
            if be is None:
                continue
            land = landing(cfg, be)
            if land is hdr:
                continue
            f['mis'] += 1
            pool = list(r.body_blocks or []) + [be, hdr]
            better = [b for b in pool if landing(cfg, b) is hdr]
            if better:
                f['better'] += 1
                if any(b is not be for b in better):
                    f['changes'] += 1
                    rows.append('%s :: %s loop@%s hdr@%s be@%s->@%s better=%s' % (
                        rel, co.co_name, hdr.start_offset, hdr.start_offset,
                        be.start_offset, land.start_offset if land else None,
                        [b.start_offset for b in better]))
    print('%-62s loops=%-4d mis=%-3d better=%-3d changes=%-3d guard_skipped=%d' % (
        rel, f['loops'], f['mis'], f['better'], f['changes'], f['guard_skipped']))
    for k in tot:
        tot[k] += f.get(k, 0)
print('TOTAL', tot)
print('=== actionable designation changes')
for x in rows[:40]:
    print('  ' + x)
print('actionable rows printed=%d of %d' % (min(len(rows), 40), len(rows)))
