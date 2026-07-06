import py_compile, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

py_compile.compile('test_l01_for_break.py', 'test_l01_for_break.pyc', doraise=True)

from core.pyc_loader_v2 import load_pyc_file_v2
from core.control_flow import ControlFlowAnalyzer

module = load_pyc_file_v2('test_l01_for_break.pyc')
code = module.code_objects[1][1]
analyzer = ControlFlowAnalyzer(code)
cfg = analyzer.build_cfg()

for b in cfg.blocks:
    print(f'Block offset={b.start_offset}, instrs={[i.opname for i in b.instructions]}, successors={[s.start_offset for s in b.successors]}, predecessors={[p.start_offset for p in b.predecessors]}')

from core.cfg.region_analyzer import RegionAnalyzer
ra = RegionAnalyzer(cfg)
regions = ra.analyze()
for r in regions:
    be = None
    if hasattr(r, 'back_edge_block') and r.back_edge_block:
        be = r.back_edge_block.start_offset
    print(f'Region: type={r.region_type}, blocks={[b.start_offset for b in r.blocks]}, back_edge_block={be}')
