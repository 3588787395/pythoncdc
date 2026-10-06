import sys, marshal
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

path = sys.argv[1]
f = open(path, 'rb'); f.read(16); co = marshal.load(f)
targets = sys.argv[2:]
for c in co.co_consts:
    if not hasattr(c, 'co_code'):
        continue
    if targets and c.co_name not in targets:
        continue
    print('##########', c.co_name)
    cb = CFGBuilder(); cfg = cb.build(c)
    an = RegionAnalyzer(cfg); an.analyze()
    for r in an.regions:
        rt = getattr(r.region_type, 'name', r.region_type)
        if 'TRY' not in str(rt):
            continue
        print('  REGION', rt, 'entry', r.entry.start_offset if r.entry else None)
        print('    try_blocks', [b.start_offset for b in getattr(r, 'try_blocks', [])])
        print('    handlers', [[ (b.start_offset) for b in h[2]] for h in getattr(r, 'except_handlers', [])])
        print('    handler_entry', [b.start_offset for b in getattr(r, 'handler_entry_blocks', [])])
        print('    else', [b.start_offset for b in getattr(r, 'else_blocks', [])])
        print('    finally', [b.start_offset for b in getattr(r, 'finally_blocks', [])])
        print('    try_offset_end', getattr(r, 'try_offset_end', None))