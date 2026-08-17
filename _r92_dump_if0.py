#!/usr/bin/env python3
"""R92 dump IfRegion@0 AST"""
import sys, marshal, types
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

func_code = find_function(orig_code, 'get_multiminute_his_data')
builder = CFGBuilder()
cfg = builder.build(func_code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, analyzer)

for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 0:
        result = ast_gen._generate_if(r)
        
        def dump(node, indent=0):
            if not isinstance(node, dict):
                if isinstance(node, list):
                    for item in node:
                        dump(item, indent)
                return
            t = node.get('type', '?')
            prefix = '  ' * indent
            if t == 'If':
                test = node.get('test', {})
                print(f"{prefix}If test={test.get('type')}")
                for s in node.get('body', []):
                    dump(s, indent+1)
                orelse = node.get('orelse', [])
                if orelse:
                    print(f"{prefix}else:")
                    for s in orelse:
                        dump(s, indent+1)
            elif t == 'Return':
                val = node.get('value', {})
                print(f"{prefix}Return value={val.get('type') if val else None}")
            elif t == 'Assign':
                targets = node.get('targets', [])
                names = [t.get('id','?') if t.get('type')=='Name' else t.get('type','?') for t in targets]
                val = node.get('value', {})
                print(f"{prefix}Assign {names} = {val.get('type')}")
            elif t == 'Expr':
                val = node.get('value', {})
                print(f"{prefix}Expr {val.get('type')}")
            else:
                print(f"{prefix}{t}")
        
        if isinstance(result, list):
            for item in result:
                dump(item)
        else:
            dump(result)
        break
