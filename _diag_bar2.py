"""Diagnostic: trace class definition handling with debug output."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Monkey-patch _build_store_statement to trace class def calls
from core.cfg.region_ast_generator import RegionASTGenerator
orig_build_store = RegionASTGenerator._build_store_statement
orig_build_class = RegionASTGenerator._build_class_def

def traced_build_store(self, instrs, block=None):
    has_lbc = any(i.opname == 'LOAD_BUILD_CLASS' for i in instrs)
    if has_lbc:
        import sys as _sys
        print(f"\n[TRACE] _build_store_statement: LOAD_BUILD_CLASS detected!", file=_sys.stderr)
        print(f"  instrs: {[(i.opname, i.argval if hasattr(i, 'argval') else i.arg) for i in instrs]}", file=_sys.stderr)
        result = orig_build_store(self, instrs, block)
        if result:
            print(f"  result type: {result.get('type')}", file=_sys.stderr)
            if result.get('type') == 'ClassDef':
                print(f"  ClassDef name: {result.get('name')}, body len: {len(result.get('body', []))}", file=_sys.stderr)
            else:
                print(f"  result: {str(result)[:200]}", file=_sys.stderr)
        else:
            print(f"  result: None", file=_sys.stderr)
        return result
    return orig_build_store(self, instrs, block)

def traced_build_class(self, *args, **kwargs):
    import sys as _sys
    print(f"\n[TRACE] _build_class_def called!", file=_sys.stderr)
    if 'call_expr' in kwargs:
        ce = kwargs['call_expr']
        print(f"  call_expr type: {ce.get('type') if isinstance(ce, dict) else type(ce)}", file=_sys.stderr)
        print(f"  is_class_def: {ce.get('is_class_def') if isinstance(ce, dict) else 'N/A'}", file=_sys.stderr)
        if isinstance(ce, dict) and 'args' in ce:
            for i, arg in enumerate(ce['args']):
                if isinstance(arg, dict):
                    print(f"  arg[{i}] type: {arg.get('type')}", file=_sys.stderr)
                    if arg.get('type') == 'FunctionObject':
                        code = arg.get('code')
                        if hasattr(code, 'co_name'):
                            print(f"    code.co_name: {code.co_name}", file=_sys.stderr)
    result = orig_build_class(self, *args, **kwargs)
    if result:
        print(f"  result type: {result.get('type')}", file=_sys.stderr)
        if result.get('type') == 'ClassDef':
            print(f"  ClassDef name: {result.get('name')}, body len: {len(result.get('body', []))}", file=_sys.stderr)
    else:
        print(f"  result: None", file=_sys.stderr)
    return result

RegionASTGenerator._build_store_statement = traced_build_store
RegionASTGenerator._build_class_def = traced_build_class

# Now try decompiling
from pycdc import decompile_pyc
pyc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'site-packages', 'IQEngine', 'core', 'bar.pyc')
try:
    source = decompile_pyc(pyc_path)
    print(f"\n=== Source ({len(source)} chars) ===")
    print(source[:2000])
except Exception as e:
    import traceback
    traceback.print_exc()
