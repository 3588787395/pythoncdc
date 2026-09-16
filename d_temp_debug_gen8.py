import sys, marshal, types
sys.stdout.reconfigure(encoding='utf-8')
pyc = 'F:/Downloads/pythoncdc-main/site-packages/IQData/plugins/plugin_system_local_finance/finance_data_source.pyc'
with open(pyc, 'rb') as f:
    f.read(16); orig = marshal.load(f)
def extract(co):
    r = {}; r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType): r.update(extract(c))
    return r
om = extract(orig)
co = om['growth_factors_sql_get']
from core.cfg import build_cfg
cfg = build_cfg(co)
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
lines = source.split('\n')
# Print lines 138-160 (the second for stock in security area)
for i in range(137, min(165, len(lines))):
    print(f'{i+1}: {lines[i]}')
