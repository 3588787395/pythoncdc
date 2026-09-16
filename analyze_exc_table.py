import sys, types, json
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal

pyc_path = 'F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    orig_code = marshal.load(f)

def extract_code_objects(code_obj):
    result = {}
    name = code_obj.co_name or '<module>'
    result[name] = code_obj
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            result.update(extract_code_objects(const))
    return result

orig_map = extract_code_objects(orig_code)
code = orig_map['save_testds_to_json']

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code, 'save_testds_to_json')
ra = RegionAnalyzer(cfg)
ra.analyze()

ast_gen = RegionASTGenerator(cfg, ra)
ast = ast_gen.generate()

# The ast IS the function def dict
try_node = ast['body'][2]  # The Try node (Try1)

def show_try(node, indent=0, label=""):
    if not isinstance(node, dict):
        return
    t = node.get('type', '?')
    if t == 'Try':
        print(' ' * indent + f'{label}Try:')
        for s in node.get('body', []):
            show_try(s, indent + 2, "body: ")
        for h in node.get('handlers', []):
            exc = h.get('exc_type', {})
            exc_str = exc.get('id', str(exc)) if isinstance(exc, dict) else str(exc)
            print(' ' * indent + f'  Except {exc_str}:')
            for s in h.get('body', []):
                show_try(s, indent + 4, "handler: ")
    elif t == 'Return':
        val = node.get('value', {})
        if isinstance(val, dict) and val.get('type') == 'Constant':
            print(' ' * indent + f'{label}Return {repr(val.get("value"))}')
        else:
            print(' ' * indent + f'{label}Return expr')
    elif t == 'Expr':
        val = node.get('value', {})
        if isinstance(val, dict):
            if val.get('type') == 'Call':
                func = val.get('func', {})
                if isinstance(func, dict):
                    print(' ' * indent + f'{label}Call {func.get("attr", "?")}')
    elif t == 'Assign':
        targets = node.get('targets', [])
        tnames = [tgt.get('id', '?') for tgt in targets if isinstance(tgt, dict)]
        print(' ' * indent + f'{label}Assign {tnames}')
    elif t == 'With':
        print(' ' * indent + f'{label}With:')
        for s in node.get('body', []):
            show_try(s, indent + 2, "with_body: ")
    elif t == 'Pass':
        print(' ' * indent + f'{label}Pass')

show_try(try_node)
