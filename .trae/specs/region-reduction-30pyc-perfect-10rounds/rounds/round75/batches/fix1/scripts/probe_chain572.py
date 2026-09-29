# -*- coding: utf-8 -*-
"""fix1 jq probe: dump the IfRegion@572 / BoolOpRegion@572 chain of unit1 with
each chain block's last instruction, the analyzer op symbols and the condition
expression the generator would emit."""
import io
import marshal
import sys
import types

sys.path.insert(0, r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')

PYC = r'F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/jq_trans_module.pyc'


def load(path):
    return marshal.loads(io.open(path, 'rb').read()[16:])


def walk(c, out):
    out.append(c)
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            walk(k, out)
    return out


cs = [c for c in walk(load(PYC), []) if c.co_name == 'replace_args'
      and 'func_attribute_history_convert_code' in c.co_qualname]
assert len(cs) == 1, cs
code = cs[0]

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator

cfg = build_cfg(code)
gen = RegionASTGenerator(cfg, top_level_code=None)
regions = gen.region_analyzer.analyze()


def o(r):
    return getattr(r, 'entry', None) and r.entry.start_offset


def li(b):
    i = b.get_last_instruction()
    return (b.start_offset, i.opname, i.argval) if i else (b.start_offset, None, None)


for r in sorted(regions, key=lambda x: o(x) or -1):
    t = type(r).__name__
    if t not in ('IfRegion', 'BoolOpRegion'):
        continue
    print('%s@%s parent=%s blocks=%s' % (t, o(r),
          type(r.parent).__name__ + '@' + str(o(r.parent)) if getattr(r, 'parent', None) else None,
          sorted(b.start_offset for b in r.blocks)))
    if t == 'BoolOpRegion':
        print('   op_chain:')
        for blk, op in r.op_chain:
            print('      block@%s last=%s op=%r' % (blk.start_offset, li(blk)[1:], op))
        print('   merge_block=%s is_condition_context=%s' % (
            r.merge_block.start_offset if getattr(r, 'merge_block', None) else None,
            getattr(r, 'is_condition_context', None)))
        try:
            ce = r.condition_expr
        except Exception as e:
            ce = '<err %s>' % e
        print('   condition_expr=%s' % (repr(ce)[:400] if ce is not None else None))
    else:
        for f in ('condition_block', 'then_blocks', 'else_blocks', 'elif_conditions',
                  'chained_compare_blocks'):
            if hasattr(r, f):
                v = getattr(r, f)
                if not v and not isinstance(v, (int, bool, str)):
                    continue
                if isinstance(v, (list, tuple, set)) and v and hasattr(list(v)[0], 'start_offset'):
                    v = sorted(x.start_offset for x in v)
                print('   %s=%r' % (f, v))
print('\n-- try the generator condition build for IfRegion@572 --')
ifr = [r for r in regions if type(r).__name__ == 'IfRegion' and o(r) == 572][0]
print('cond_block=%s' % (ifr.condition_block.start_offset if ifr.condition_block else None))
cond = gen._if_extract_condition_from_instructions(ifr, ifr.condition_block, [])
print('condition=%s' % (repr(cond)[:800] if cond is not None else None))
