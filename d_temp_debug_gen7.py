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
gen = RegionASTGenerator(cfg, top_level_code=None)

# Now look at the generated AST for the second for loop
ast_dict = gen.generate()
body = ast_dict['body']

# Find the elif table == 'growth_ability' section (the second occurrence)
# Let's look at the overall structure
def show_ast(node, indent=0):
    if isinstance(node, list):
        for item in node:
            show_ast(item, indent)
    elif isinstance(node, dict):
        ntype = node.get('type', '?')
        extra = ''
        if ntype == 'For':
            iter_n = node.get('iter')
            target = node.get('target')
            extra = ' iter=%s target=%s' % (iter_n, target)
        elif ntype == 'If':
            test = node.get('test')
            if isinstance(test, dict):
                extra = ' test_type=%s' % test.get('type', '?')
        elif ntype == 'Expr':
            val = node.get('value')
            if isinstance(val, dict):
                extra = ' value_type=%s' % val.get('type', '?')
        print(' ' * indent + '%s%s' % (ntype, extra))
        for key in ['body', 'orelse']:
            if key in node:
                print(' ' * indent + '  %s:' % key)
                show_ast(node[key], indent + 4)

# Find the elif growth_ability branch  
for item in body:
    if isinstance(item, dict) and item.get('type') == 'If':
        # This is the outer if-elif chain
        orelse = item.get('orelse', [])
        if orelse and isinstance(orelse[0], dict) and orelse[0].get('type') == 'If':
            # Check the elif branches
            current = orelse[0]
            while current:
                test = current.get('test', {})
                # Look for the one that matches table == 'growth_ability' or has the for loop
                body_items = current.get('body', [])
                has_for = any(isinstance(b, dict) and b.get('type') == 'For' for b in body_items)
                has_expr_iter = False
                for b in body_items:
                    if isinstance(b, dict) and b.get('type') == 'Expr':
                        val = b.get('value', {})
                        if isinstance(val, dict) and val.get('type') == 'Iter':
                            has_expr_iter = True
                if has_for or has_expr_iter:
                    print("Found elif branch with for/iter:")
                    show_ast(current, 0)
                    break
                current_orelse = current.get('orelse', [])
                if current_orelse and isinstance(current_orelse[0], dict) and current_orelse[0].get('type') == 'If':
                    current = current_orelse[0]
                else:
                    break
