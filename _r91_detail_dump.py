#!/usr/bin/env python3
"""R91 detailed nested IfRegion AST dump"""
import sys, marshal, types, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

target_pyc = "site-packages/IQCommon/api/klinedata.pyc"
with open(target_pyc, 'rb') as f:
    f.read(16)
    orig_code = marshal.loads(f.read())

def find_function(code, name):
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            inner = find_function(const, name)
            if inner:
                return inner
    return None

func_code = find_function(orig_code, 'get_price_common')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

# Find the nested IfRegion at entry=280
nested_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 280:
        nested_if = r
        break

if nested_if:
    result = ast_gen._generate_if(nested_if)
    if isinstance(result, dict) and result.get('type') == 'If':
        def dump(node, indent=0):
            if not isinstance(node, dict):
                return
            t = node.get('type', '?')
            prefix = '  ' * indent
            if t == 'If':
                test = node.get('test', {})
                _is_elif = node.get('_is_elif', False)
                test_detail = ''
                if test.get('type') == 'Compare':
                    ops = test.get('ops', [])
                    left = test.get('left', {})
                    if left.get('type') == 'Name':
                        test_detail = f"{left.get('id')} {ops}"
                    elif left.get('type') == 'Call':
                        test_detail = f"Call({left.get('func', {}).get('id', '?')}) {ops}"
                    else:
                        test_detail = f"{left.get('type')} {ops}"
                elif test.get('type') == 'UnaryOp':
                    operand = test.get('operand', {})
                    if operand.get('type') == 'Compare':
                        test_detail = f"not {operand.get('left', {}).get('id', '?')} {operand.get('ops', [])}"
                    else:
                        test_detail = f"UnaryOp({operand.get('type')})"
                elif test.get('type') == 'Call':
                    func = test.get('func', {})
                    test_detail = f"Call({func.get('id', '?')})"
                else:
                    test_detail = test.get('type', '?')
                
                print(f"{prefix}If{' (elif)' if _is_elif else ''} test={test_detail}")
                for s in node.get('body', []):
                    dump(s, indent+1)
                orelse = node.get('orelse', [])
                if orelse:
                    print(f"{prefix}else:")
                    for s in orelse:
                        dump(s, indent+1)
            elif t == 'Return':
                val = node.get('value')
                val_type = val.get('type') if isinstance(val, dict) else None
                print(f"{prefix}Return (value={val_type})")
            elif t == 'Expr':
                val = node.get('value', {})
                if val.get('type') == 'Call':
                    func = val.get('func', {})
                    print(f"{prefix}Expr Call({func.get('id', '?')})")
                else:
                    print(f"{prefix}Expr value={val.get('type')}")
            elif t == 'Assign':
                targets = node.get('targets', [])
                tgt_names = [t.get('id','?') if t.get('type')=='Name' else t.get('type','?') for t in targets]
                val = node.get('value', {})
                print(f"{prefix}Assign targets={tgt_names} value={val.get('type')}")
            elif t == 'Pass':
                print(f"{prefix}Pass")
            else:
                print(f"{prefix}{t}")
        
        dump(result)
