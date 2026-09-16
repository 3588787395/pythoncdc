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

# Traverse the AST to find where 'security' Expr comes from
def find_expr_security(node, path=''):
    if isinstance(node, list):
        for i, item in enumerate(node):
            find_expr_security(item, f'{path}[{i}]')
    elif isinstance(node, dict):
        ntype = node.get('type', '?')
        if ntype == 'Expr':
            val = node.get('value', {})
            if isinstance(val, dict) and val.get('type') in ('Name', 'Iter'):
                vid = val.get('id', '')
                vtype = val.get('type', '')
                if vid == 'security' or (vtype == 'Iter' and isinstance(val.get('value'), dict) and val.get('value').get('id') == 'security'):
                    print(f'Found Expr({vtype} security) at path: {path}')
        for key in ['body', 'orelse', 'items']:
            if key in node:
                find_expr_security(node[key], f'{path}.{key}')

find_expr_security(ast_dict.get('body', []), 'body')
