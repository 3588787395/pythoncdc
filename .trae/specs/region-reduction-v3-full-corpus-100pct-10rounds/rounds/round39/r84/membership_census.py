"""R21-54 membership census for clock_worker. Counting rule STATED (r82a 148 vs r78a 186 differ
only because of the definition):

  regions   = len(an.analyze()) over the clock_worker code object
  blocks    = number of CFG basic blocks (cfg.blocks values with instructions)
  claim[b]  = number of regions R (over ALL analyzed regions) whose membership set contains b:
              R.blocks ∪ {R.entry_block, R.header_block, R.condition_block, R.merge_block}
              as present (identity by block object).
  two_owner = #blocks with claim == 2   (>=2 counted separately as multi_owner)
  zero_owner= #blocks with claim == 0

The [R21-54] rule is GENERATOR-side (region_ast_generator.py) and reads region data with no
mutation; the analyzer bytes are unchanged (f7d849e974904492), so these numbers are identical
base-vs-candidate by construction. Printed once (analyzer is the same file in both).

usage: python -X utf8 work/membership_census.py
"""
import marshal, os, sys
MIRROR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, MIRROR)
PYC = r"D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc"
from core.cfg import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

CO = type(compile("", "", "exec"))


def gather(c, acc):
    st = [c]
    while st:
        cur = st.pop(); acc.append(cur)
        for x in cur.co_consts:
            if isinstance(x, CO):
                st.append(x)


code = marshal.loads(open(PYC, "rb").read()[16:])
acc = []; gather(code, acc)
target = max([c for c in acc if c.co_name == "clock_worker"], key=lambda c: len(c.co_code))
cfg = build_cfg(target)
an = RegionAnalyzer(cfg)
regions = an.analyze()
blocks = [b for b in cfg.blocks.values() if b.instructions]

claim = {id(b): 0 for b in blocks}
bset = set(id(b) for b in blocks)


def members(r):
    s = set()
    for b in (getattr(r, 'blocks', None) or set()):
        if id(b) in bset:
            s.add(id(b))
    for f in ('entry_block', 'header_block', 'condition_block', 'merge_block'):
        b = getattr(r, f, None)
        if b is not None and id(b) in bset:
            s.add(id(b))
    return s


for r in regions:
    for bid in members(r):
        claim[bid] += 1

two = sum(1 for v in claim.values() if v == 2)
multi = sum(1 for v in claim.values() if v > 2)
zero = sum(1 for v in claim.values() if v == 0)
print("clock_worker regions=%d blocks=%d two_owner(==2)=%d multi_owner(>2)=%d zero_owner=%d"
      % (len(regions), len(blocks), two, multi, zero))
