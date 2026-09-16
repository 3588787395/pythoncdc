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
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator
cfg = build_cfg(co)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()

body = ast_dict['body']
for i, item in enumerate(body):
    if isinstance(item, dict):
        ntype = item.get('type', '?')
        extra = ''
        if ntype == 'Expr':
            val = item.get('value', {})
            extra = f' value={val}'
        elif ntype == 'AugAssign':
            extra = f' target={item.get("target")} op={item.get("op")}'
        elif ntype == 'If':
            test = item.get('test', {})
            extra = f' test_type={test.get("type") if isinstance(test, dict) else test}'
        elif ntype == 'For':
            extra = f' iter={item.get("iter")} target={item.get("target")}'
        elif ntype == 'Return':
            extra = f' value={item.get("value")}'
        print(f'body[{i}]: type={ntype}{extra}')
