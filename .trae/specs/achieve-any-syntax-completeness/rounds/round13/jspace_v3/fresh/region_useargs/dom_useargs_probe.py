# Confirm the dominance criterion for a narrow fix (or its absence).
import sys, types, textwrap
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer

lines = open(r'D:\Python\Lib\enum.py', encoding='utf-8').read().split('\n')
start = next(i for i,l in enumerate(lines) if 'def _find_new_' in l)
end = start+1
while end < len(lines):
    l = lines[end]
    if l.startswith('    def ') or l.startswith('class ') or l.startswith('EnumMeta'):
        break
    end += 1
src = textwrap.dedent('\n'.join(lines[start:end]))
code = compile(src + '\n', '<fnc>', 'exec')
fnc = [c for c in code.co_consts if isinstance(c, types.CodeType)][0]
cfg = build_cfg(fnc, name='_find_new_')
an = RegionAnalyzer(cfg, parent_code=fnc)
an.analyze()

def dom(b):
    return {d.id for d in getattr(b, 'dominators', set()) or set()}

B = cfg.blocks
for bid in (3,4,5,11,12,13,14,15):
    b = B.get(bid)
    print(f'B{bid} dominators={sorted(dom(b))} succs={sorted(s.id for s in b.successors)} preds={sorted(p.id for p in b.predecessors)}')

print()
# Criterion: does if-entry B11 dominate its claimed merge B15?
print('B11 dominates B15?', 11 in dom(B[15]))
print('B15 preds:', sorted(p.id for p in B[15].predecessors))
# Does any B15 pred reach the loop header B5 without traversing B15? (loop-bypass pred)
def reaches_without(start, target, forbidden):
    seen=set(); stack=[start]
    while stack:
        u=stack.pop()
        if u in seen: continue
        seen.add(u.id)
        if u.id==target: return True
        for v in u.successors:
            if v.id==forbidden: continue
            if v.id not in seen: stack.append(v)
    return False
for p in (3,12,14):
    print(f'B{p} reaches loop-header B5 without traversing B15? {reaches_without(B[p], 5, 15)}')
