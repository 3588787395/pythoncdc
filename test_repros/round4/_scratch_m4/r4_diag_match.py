import sys, marshal, json
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType

path = sys.argv[1]
f = open(path, 'rb')
f.read(16)
code = marshal.load(f)

def find(co, name):
    for c in co.co_consts:
        if hasattr(c, 'co_name') and c.co_name == name:
            return c
    return None

target = sys.argv[2] if len(sys.argv) > 2 else 'e07_capture'
co = find(code, target)
if co and sys.argv[3:]:
    co = find(co, sys.argv[3])
builder = CFGBuilder()
cfg = builder.build(co)
ra = RegionAnalyzer(cfg)
ra.analyze()
for r in ra.regions:
    if r.region_type == RegionType.MATCH:
        print('MATCH entry', getattr(r.entry, 'start_offset', None))
        for i, (p, g) in enumerate(zip(r.case_patterns or [], r.case_guards or [])):
            print('  case', i, 'pattern=', json.dumps(p, default=str))
            print('        guard=', json.dumps(g, default=str))