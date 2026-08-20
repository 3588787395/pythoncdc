"""Test fix: decompile and compare for exception_handling_complex."""
import sys, marshal, dis, ast
sys.path.insert(0, '.')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion, IfRegion, LoopRegion

f = open('decompiler_test_comprehensive.cpython-311.pyc', 'rb')
f.read(16)
code = marshal.load(f)
dp = [c for c in code.co_consts if hasattr(c, 'co_name') and c.co_name == 'DataProcessor'][0]
ehc = [c for c in dp.co_consts if hasattr(c, 'co_name') and c.co_name == 'exception_handling_complex'][0]

builder = CFGBuilder()
cfg = builder.build(ehc)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

# Check IfRegion@26 then_blocks
for r in analyzer.regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 26:
        print(f"IfRegion@26: then_blocks={[b.start_offset for b in r.then_blocks]}")
        print(f"           else_blocks={[b.start_offset for b in r.else_blocks]}")
        print(f"           merge={r.merge_block.start_offset if r.merge_block else 'NA'}")

from core.cfg.region_ast_generator import RegionASTGenerator
gen = RegionASTGenerator(cfg, analyzer)
result = gen.generate()

# Print the AST
import json
def ast_to_str(node, indent=0):
    lines = []
    prefix = '  ' * indent
    if isinstance(node, dict):
        t = node.get('type', '?')
        if t == 'If':
            lines.append(f"{prefix}If:")
            test = node.get('test', {})
            lines.append(f"{prefix}  test={test}")
            for s in node.get('body', []):
                lines.extend(ast_to_str(s, indent+2))
            orelse = node.get('orelse', [])
            if orelse:
                lines.append(f"{prefix}  else:")
                for s in orelse:
                    lines.extend(ast_to_str(s, indent+3))
        elif t == 'Try':
            lines.append(f"{prefix}Try:")
            for s in node.get('body', []):
                lines.extend(ast_to_str(s, indent+2))
            for h in node.get('handlers', []):
                lines.append(f"{prefix}  except {h.get('type','')}:")
                for s in h.get('body', []):
                    lines.extend(ast_to_str(s, indent+3))
            for s in node.get('orelse', []):
                lines.append(f"{prefix}  else:")
                for s in [s] if isinstance(s, dict) else s:
                    lines.extend(ast_to_str(s, indent+3))
            for s in node.get('finalbody', []):
                lines.append(f"{prefix}  finally:")
                for s in [s] if isinstance(s, dict) else s:
                    lines.extend(ast_to_str(s, indent+3))
        elif t == 'For':
            lines.append(f"{prefix}For:")
            for s in node.get('body', []):
                lines.extend(ast_to_str(s, indent+2))
        elif t == 'Continue':
            lines.append(f"{prefix}continue")
        elif t == 'AugAssign':
            lines.append(f"{prefix}augassign {node.get('target','')}")
        elif t == 'Expr':
            lines.append(f"{prefix}expr {node.get('value','')}")
        else:
            lines.append(f"{prefix}{t}: {node}")
    elif isinstance(node, list):
        for n in node:
            lines.extend(ast_to_str(n, indent))
    else:
        lines.append(f"{prefix}{node}")
    return lines

for stmt in result:
    for line in ast_to_str(stmt):
        print(line)
