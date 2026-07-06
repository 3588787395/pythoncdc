import sys
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer

code = compile('try:\n    x = 1\nfinally:\n    y = 2', '<test>', 'exec')
builder = CFGBuilder()
cfg = builder.build(code)
analyzer = RegionAnalyzer(cfg)
handler_infos = analyzer._parse_exception_table()
for i, info in enumerate(handler_infos):
    print(f'Handler {i}: try_start={info["try_start"]} try_end={info["try_end"]} handler_start={info["handler_start"]} type={info["handler_type"]} depth={info.get("depth", 0)}')
