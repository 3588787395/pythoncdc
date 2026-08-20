"""Trace AST generation for exception_handling_complex"""
import sys
sys.path.insert(0, '.')

from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
import marshal, types, ast

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
f.close()

# Find exception_handling_complex
for c in code.co_consts:
    if isinstance(c, types.CodeType):
        for cc in c.co_consts:
            if isinstance(cc, types.CodeType) and cc.co_name == 'exception_handling_complex':
                target_code = cc
                break

print(f"Found: {target_code.co_name}")

# Build CFG
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(target_code)

# Build regions
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Generate AST
gen = RegionASTGenerator(cfg, analyzer)
ast_dict = gen.generate()

# Print AST
import json

def print_ast(node, indent=0):
    if isinstance(node, dict):
        t = node.get('type', '?')
        print('  ' * indent + f"{t}", end='')
        if t == 'Constant':
            print(f" value={node.get('value')!r}")
        elif t == 'Name':
            print(f" id={node.get('id')!r}")
        elif t == 'Assign':
            print()
            for k in ('targets', 'value'):
                if k in node:
                    print_ast(node[k], indent+1)
        elif t == 'AugAssign':
            print(f" op={node.get('op')}")
            print_ast(node.get('target', {}), indent+1)
            print_ast(node.get('value', {}), indent+1)
        elif t == 'Expr':
            print()
            print_ast(node.get('value', {}), indent+1)
        elif t == 'Try':
            print()
            print("  " * (indent+1) + "body:")
            for s in node.get('body', []):
                print_ast(s, indent+2)
            if node.get('handlers'):
                print("  " * (indent+1) + "handlers:")
                for h in node.get('handlers', []):
                    print_ast(h, indent+2)
            if node.get('orelse'):
                print("  " * (indent+1) + "orelse:")
                for s in node['orelse']:
                    print_ast(s, indent+2)
            if node.get('finalbody'):
                print("  " * (indent+1) + "finalbody:")
                for s in node['finalbody']:
                    print_ast(s, indent+2)
        elif t == 'ExceptHandler':
            print(f" name={node.get('name')}")
            print("  " * (indent+1) + "body:")
            for s in node.get('body', []):
                print_ast(s, indent+2)
        elif t == 'For':
            print()
            print("  " * (indent+1) + "target:")
            print_ast(node.get('target', {}), indent+2)
            print("  " * (indent+1) + "iter:")
            print_ast(node.get('iter', {}), indent+2)
            print("  " * (indent+1) + "body:")
            for s in node.get('body', []):
                print_ast(s, indent+2)
            if node.get('orelse'):
                print("  " * (indent+1) + "orelse:")
                for s in node['orelse']:
                    print_ast(s, indent+2)
        elif t == 'If':
            print()
            print("  " * (indent+1) + "test:")
            print_ast(node.get('test', {}), indent+2)
            print("  " * (indent+1) + "body:")
            for s in node.get('body', []):
                print_ast(s, indent+2)
            if node.get('orelse'):
                print("  " * (indent+1) + "orelse:")
                for s in node['orelse']:
                    print_ast(s, indent+2)
        elif t == 'Continue':
            print()
        elif t == 'Break':
            print()
        elif t == 'Pass':
            print()
        elif t == 'Return':
            print()
            if 'value' in node:
                print_ast(node['value'], indent+1)
        elif t == 'FunctionDef':
            print(f" name={node.get('name')!r}")
            for s in node.get('body', []):
                print_ast(s, indent+1)
        elif t == 'ClassDef':
            print(f" name={node.get('name')!r}")
            for s in node.get('body', []):
                print_ast(s, indent+1)
        elif t == 'Call':
            func = node.get('func', {})
            args = node.get('args', [])
            print(f" func={func}")
            for a in args:
                print_ast(a, indent+1)
        else:
            for k, v in node.items():
                if k != 'type':
                    if isinstance(v, (dict, list)):
                        print()
                        print_ast(v, indent+1)
                    else:
                        print(f" {k}={v!r}", end='')
            print()
    elif isinstance(node, list):
        for item in node:
            print_ast(item, indent)

# Find and print exception_handling_complex in AST
def find_in_ast(node, name):
    if isinstance(node, dict):
        if node.get('type') == 'FunctionDef' and node.get('name') == name:
            return node
        for v in node.values():
            result = find_in_ast(v, name)
            if result:
                return result
    elif isinstance(node, list):
        for item in node:
            result = find_in_ast(item, name)
            if result:
                return result
    return None

ehc = find_in_ast(ast_dict, 'exception_handling_complex')
if ehc:
    print("\n=== exception_handling_complex AST ===")
    print_ast(ehc)
else:
    print("Not found in AST!")
    print("\nTop-level AST:")
    print_ast(ast_dict)
