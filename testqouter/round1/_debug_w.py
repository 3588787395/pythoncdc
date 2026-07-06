import py_compile, sys, os, marshal, json
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator

for tf in ['test_w03_multi_with.py','test_w04_nested_with.py','test_w06_try_with_with.py']:
    pyc = tf+'c'
    py_compile.compile(tf, cfile=pyc, doraise=True)
    with open(pyc, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    func_code = code.co_consts[0]
    cfg = CFGBuilder().build(func_code)

    gen = RegionASTGenerator(cfg, top_level_code=func_code)
    ast = gen.generate()

    body = ast.get('body', [])
    print(f'=== {tf} ===')
    for node in body:
        t = node.get('type', '?')
        if t == 'Import':
            names = node.get('names', [])
            print(f'  Import: {[n["name"] for n in names]}')
        elif t == 'Assign':
            tgt = node.get('targets', [{}])[0]
            tgt_id = tgt.get('id', '?') if isinstance(tgt, dict) else '?'
            val = node.get('value', {})
            val_type = val.get('type', '?') if isinstance(val, dict) else '?'
            val_val = val.get('value', '?') if isinstance(val, dict) else '?'
            print(f'  Assign: {tgt_id} = {val_type}({val_val})')
        elif t == 'With':
            items = node.get('items', [])
            print(f'  With: {len(items)} items')
            for item in items:
                var = item.get('optional_vars', {})
                var_id = var.get('id', '?') if isinstance(var, dict) else None
                print(f'    var={var_id}')
            for s in node.get('body', []):
                st = s.get('type', '?')
                print(f'    body: {st}')
        elif t == 'Try':
            print(f'  Try:')
            for s in node.get('body', []):
                st = s.get('type', '?')
                print(f'    body: {st}')
            for h in node.get('handlers', []):
                for s in h.get('body', []):
                    st = s.get('type', '?')
                    print(f'    handler: {st}')
        elif t == 'Return':
            val = node.get('value', {})
            val_type = val.get('type', '?') if isinstance(val, dict) else '?'
            val_val = val.get('value', '?') if isinstance(val, dict) else '?'
            print(f'  Return: {val_type}({val_val})')
        else:
            print(f'  {t}')
    print()
    if os.path.exists(pyc): os.remove(pyc)
