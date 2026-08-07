"""Diagnostic: trace block structure and statement generation for bar.pyc."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Monkey-patch _generate_block_statements and _build_statement
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.basic_block import BasicBlock

orig_gen_block = RegionASTGenerator._generate_block_statements
orig_build_stmt = RegionASTGenerator._build_statement
orig_build_store = RegionASTGenerator._build_store_statement

call_count = [0]

def traced_gen_block(self, block, _cjb_parent=None):
    call_count[0] += 1
    if call_count[0] <= 5:
        instrs_summary = [(i.opname, i.argval if hasattr(i, 'argval') else i.arg) for i in block.instructions[:10]]
        import sys as _sys
        print(f"\n[TRACE] _generate_block_statements #{call_count[0]} block@{block.start_offset}", file=_sys.stderr)
        print(f"  instrs (first 10): {instrs_summary}", file=_sys.stderr)
        print(f"  total instrs: {len(block.instructions)}", file=_sys.stderr)
        has_lbc = any(i.opname == 'LOAD_BUILD_CLASS' for i in block.instructions)
        if has_lbc:
            print(f"  *** HAS LOAD_BUILD_CLASS ***", file=_sys.stderr)
    result = orig_gen_block(self, block, _cjb_parent)
    if call_count[0] <= 5 and result:
        import sys as _sys
        print(f"  result: {len(result)} stmts, types: {[r.get('type') if isinstance(r, dict) else type(r).__name__ for r in result[:5]]}", file=_sys.stderr)
    return result

def traced_build_stmt(self, instrs, **kwargs):
    has_lbc = any(i.opname == 'LOAD_BUILD_CLASS' for i in instrs) if instrs else False
    if has_lbc:
        import sys as _sys
        print(f"\n[TRACE] _build_statement: LOAD_BUILD_CLASS detected!", file=_sys.stderr)
        print(f"  instrs: {[(i.opname, i.argval if hasattr(i, 'argval') else i.arg) for i in instrs]}", file=_sys.stderr)
    result = orig_build_stmt(self, instrs, **kwargs)
    if has_lbc and result:
        import sys as _sys
        print(f"  result type: {result.get('type') if isinstance(result, dict) else type(result).__name__}", file=_sys.stderr)
    return result

def traced_build_store(self, instrs, block=None):
    has_lbc = any(i.opname == 'LOAD_BUILD_CLASS' for i in instrs) if instrs else False
    if has_lbc:
        import sys as _sys
        print(f"\n[TRACE] _build_store_statement: LOAD_BUILD_CLASS detected!", file=_sys.stderr)
    result = orig_build_store(self, instrs, block)
    if has_lbc and result:
        import sys as _sys
        print(f"  result type: {result.get('type') if isinstance(result, dict) else type(result).__name__}", file=_sys.stderr)
    return result

RegionASTGenerator._generate_block_statements = traced_gen_block
RegionASTGenerator._build_statement = traced_build_stmt
RegionASTGenerator._build_store_statement = traced_build_store

# Also trace the generate method
orig_generate = RegionASTGenerator.generate
def traced_generate(self):
    import sys as _sys
    print(f"\n[TRACE] generate() called for cfg: {self.cfg.name}", file=_sys.stderr)
    print(f"  regions: {len(self.region_analyzer.analyze()) if hasattr(self, 'region_analyzer') else 'N/A'}", file=_sys.stderr)
    result = orig_generate(self)
    if result:
        print(f"  generate() result body: {len(result.get('body', []))} stmts", file=_sys.stderr)
    return result
RegionASTGenerator.generate = traced_generate

from pycdc import decompile_pyc
pyc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site-packages', 'IQEngine', 'core', 'bar.pyc')
try:
    source = decompile_pyc(pyc_path)
    print(f"\n=== Source ({len(source)} chars) ===")
    print(source[:2000])
except Exception as e:
    import traceback
    traceback.print_exc()
