"""Trace repro_r2_10 AST"""
import sys, marshal, json
sys.path.insert(0, '.')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

pyc_path = '.trae/specs/decompiler-test-comprehensive-10rounds/rounds/round_02/test_engineer/minimal_repros/repro_r2_10_try_wrap_for_else_break.pyc'
with open(pyc_path, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

func_code = None
for c in code.co_consts:
    if hasattr(c, 'co_name') and c.co_name == 'test_try_wrap_for_else_break':
        func_code = c
        break

cfg = build_cfg(func_code)
gen = RegionASTGenerator(cfg)
ast_dict = gen.generate()

# Print the AST structure
print("=== AST body ===")
for i, node in enumerate(ast_dict.get('body', [])):
    if isinstance(node, dict):
        t = node.get('type')
        print(f"  body[{i}]: type={t}")
        if t == 'Try':
            # Print try body
            try_body = node.get('body', [])
            print(f"    try body ({len(try_body)} nodes):")
            for j, tb in enumerate(try_body):
                if isinstance(tb, dict):
                    print(f"      [{j}]: type={tb.get('type')}")
                    if tb.get('type') == 'For':
                        for_body = tb.get('body', [])
                        print(f"        for body ({len(for_body)} nodes):")
                        for k, fb in enumerate(for_body):
                            if isinstance(fb, dict):
                                print(f"          [{k}]: type={fb.get('type')}")
                        for_else = tb.get('orelse', [])
                        print(f"        for orelse ({len(for_else)} nodes):")
                        for k, fe in enumerate(for_else):
                            if isinstance(fe, dict):
                                print(f"          [{k}]: type={fe.get('type')}")
            # Print handlers
            handlers = node.get('handlers', [])
            print(f"    handlers ({len(handlers)}):")
            for h in handlers:
                if isinstance(h, dict):
                    h_body = h.get('body', [])
                    print(f"      handler body ({len(h_body)} nodes):")
                    for j, hb in enumerate(h_body):
                        if isinstance(hb, dict):
                            print(f"        [{j}]: type={hb.get('type')}")

# Generate source
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
code_gen = CFGCodeGenerator()
source = code_gen.generate(py_ast)
print(f"\n=== Source ===\n{source}")
