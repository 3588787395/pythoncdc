"""Dump the region AST for handle_backtest_build in backtest.pyc.

Goal: inspect how the long BUILD_STRING 25 f-string (user_code assignment)
is reconstructed. Expectation: JoinedStr with 25 values. If fewer, the
reconstruct is being fed a truncated instruction list.
"""
import sys, os, json, marshal, types
sys.path.insert(0, r'f:/Downloads/pythoncdc-main')

from core.control_flow import ControlFlowAnalyzer
from core.cfg.region_ast_generator import generate_ast_from_regions, RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer

PYC = r'f:/Downloads/pythoncdc-main/site-packages/IQCommon/backtest/backtest.pyc'

with open(PYC, 'rb') as f:
    f.read(16)
    top = marshal.load(f)

# Find handle_backtest_build code object
hb = None
for c in top.co_consts:
    if hasattr(c, 'co_code') and c.co_name == 'handle_backtest_build':
        hb = c
        break
assert hb is not None, 'handle_backtest_build not found'

print(f'Function: {hb.co_name}')
print(f'co_code length: {len(hb.co_code)}')
print(f'co_consts count: {len(hb.co_consts)}')

# Build CFG
from core.pyc_loader_v2 import load_pyc_file_v2
mod = load_pyc_file_v2(PYC)
# Use the loader's machinery to get a CFG for the function
from bytecode.pyc_disasm import PycDisassembler
from core.control_flow import ControlFlowAnalyzer as CFA

# Try the standard path: build a PycCode wrapper then ControlFlowAnalyzer
from core.pyc_loader_v2 import PycCode
# Some loaders expose PycCode; fall back to using dis.Bytecode-derived instructions
try:
    pyc_code = PycCode.from_code(hb) if hasattr(PycCode, 'from_code') else None
except Exception as e:
    print('PycCode.from_code failed:', e)
    pyc_code = None

# Easiest: re-run the full decompiler but capture the generator's AST.
# Monkey-patch RegionASTGenerator.generate to capture per-CFG result.
import core.cfg.region_ast_generator as rag_mod
_OrigRegionASTGenerator = rag_mod.RegionASTGenerator
captured = {}  # keyed by cfg.name
class _HookedGen(_OrigRegionASTGenerator):
    def generate(self):
        ast = _OrigRegionASTGenerator.generate(self)
        try:
            key = getattr(self.cfg, 'name', None) or '<unknown>'
        except Exception:
            key = '<unknown>'
        captured[key] = ast
        return ast
rag_mod.RegionASTGenerator = _HookedGen
# Also patch the pycdc module's reference (it imports RegionASTGenerator at call time)
import pycdc as _pycdc_mod
_pycdc_mod.RegionASTGenerator = _HookedGen

# Now run the decompiler
from pycdc import decompile_pyc
try:
    src = decompile_pyc(PYC)
    print('=== DECOMPILE OK ===')
except Exception as e:
    import traceback
    traceback.print_exc()
    print('=== DECOMPILE FAILED ===')
    src = ''

# Restore
rag_mod.RegionASTGenerator = _OrigRegionASTGenerator
_pycdc_mod.RegionASTGenerator = _OrigRegionASTGenerator

ast = captured.get('ast')
if ast is None:
    print('Captured CFGs:', list(captured.keys()))
    ast = captured.get('handle_backtest_build')
if ast is None:
    print('NO AST CAPTURED for handle_backtest_build')
    sys.exit(0)

# Walk AST to find the function body
def find_func(node, name):
    if not isinstance(node, dict):
        return None
    if node.get('type') == 'FunctionDef' and node.get('name') == name:
        return node
    for v in node.values():
        if isinstance(v, list):
            for x in v:
                r = find_func(x, name)
                if r: return r
        elif isinstance(v, dict):
            r = find_func(v, name)
            if r: return r
    return None

fn = find_func(ast, 'handle_backtest_build')
if fn is None:
    print('FunctionDef not found in AST; dumping top-level keys')
    print(json.dumps({k: type(v).__name__ for k,v in ast.items()}, indent=2))
    sys.exit(0)

body = fn.get('body', [])
print(f'Function body has {len(body)} statements')

# Recursive walk to find ALL Assign nodes and JoinedStr counts
def walk(node, depth=0, path='body'):
    if not isinstance(node, dict):
        return
    t = node.get('type')
    if t == 'Assign':
        tgt = node.get('targets', [])
        tgt_str = '?'
        if tgt and isinstance(tgt[0], dict):
            tgt_str = tgt[0].get('id') or tgt[0].get('attr') or tgt[0].get('type')
        val = node.get('value', {})
        val_type = val.get('type') if isinstance(val, dict) else type(val).__name__
        extra = ''
        if val_type == 'JoinedStr':
            extra = f' values_count={len(val.get("values",[]))}'
        print(f'{"  "*depth}[{path}] Assign target={tgt_str} value_type={val_type}{extra}')
        # Recurse into value
        walk(val, depth+1, 'value')
    elif t == 'JoinedStr':
        vals = node.get('values', [])
        print(f'{"  "*depth}[{path}] JoinedStr values_count={len(vals)}')
        for i, v in enumerate(vals):
            vt = v.get('type') if isinstance(v, dict) else type(v).__name__
            if vt == 'Constant':
                cv = v.get('value')
                cv_s = repr(cv)[:60] if isinstance(cv, str) else str(cv)
                print(f'{"  "*depth}  [{i}] Constant {cv_s}')
            elif vt == 'FormattedValue':
                inn = v.get('value', {})
                it = inn.get('type') if isinstance(inn, dict) else type(inn).__name__
                print(f'{"  "*depth}  [{i}] FormattedValue inner={it}')
            else:
                print(f'{"  "*depth}  [{i}] {vt}')
    else:
        if t:
            print(f'{"  "*depth}[{path}] {t}')
        for k, v in node.items():
            if k in ('type', 'lineno', 'col_offset', 'end_lineno', 'end_col_offset',
                     'ctx', 'op', 'ops', 'conversion', 'format_spec', ' decorators',
                     'returns', 'annotation', 'args', 'keywords', 'kind', 'vararg',
                     'kwarg', 'kw_defaults', 'defaults'):
                continue
            if isinstance(v, list):
                for j, x in enumerate(v):
                    walk(x, depth+1, f'{k}[{j}]')
            elif isinstance(v, dict):
                walk(v, depth+1, k)

for i, s in enumerate(body):
    walk(s, 0, f'body[{i}]')

# Also write the full function AST to a file for inspection
import io
_buf = io.StringIO()
def emit(node, depth=0):
    if not isinstance(node, dict):
        _buf.write('  '*depth + repr(node)[:120] + '\n')
        return
    t = node.get('type', '?')
    tgt = ''
    if t == 'Assign':
        tgts = node.get('targets', [])
        if tgts and isinstance(tgts[0], dict):
            tgt = ' target=' + str(tgts[0].get('id') or tgts[0].get('attr') or tgts[0].get('type'))
    if t == 'JoinedStr':
        tgt = f' values_count={len(node.get("values",[]))}'
    if t == 'Constant':
        cv = node.get('value')
        tgt = ' value=' + (repr(cv)[:80] if isinstance(cv, str) else str(cv))
    _buf.write('  '*depth + str(t) + tgt + '\n')
    for k, v in node.items():
        if k in ('type', 'lineno', 'col_offset', 'end_lineno', 'end_col_offset',
                 'ctx', 'op', 'ops', 'conversion', 'format_spec',
                 'returns', 'annotation', 'args', 'keywords', 'kind', 'vararg',
                 'kwarg', 'kw_defaults', 'defaults', 'value'):
            continue
        if isinstance(v, list):
            for j, x in enumerate(v):
                _buf.write('  '*(depth+1) + f'[{k}][{j}]\n')
                emit(x, depth+2)
        elif isinstance(v, dict):
            _buf.write('  '*(depth+1) + f'[{k}]\n')
            emit(v, depth+2)
emit(fn)
with open(r'f:/Downloads/pythoncdc-main/.trae/specs/region-comment-multi-pyc-iteration/rounds/round_09/test_engineer/_fn_ast.txt', 'w', encoding='utf-8') as _f:
    _f.write(_buf.getvalue())
print(f'Wrote _fn_ast.txt ({len(_buf.getvalue())} chars)')

# Find user_code Assign anywhere
found_uc = []
def find_assigns(node, name):
    if not isinstance(node, dict):
        return
    t = node.get('type')
    if t == 'Assign':
        tgt = node.get('targets', [])
        if tgt and isinstance(tgt[0], dict) and tgt[0].get('id') == name:
            found_uc.append(node)
    for v in node.values():
        if isinstance(v, list):
            for x in v:
                find_assigns(x, name)
        elif isinstance(v, dict):
            find_assigns(v, name)

find_assigns(fn, 'user_code')
if not found_uc:
    print('\nuser_code Assign NOT FOUND anywhere in function AST')
else:
    for uc in found_uc:
        val = uc.get('value', {})
        print('\n=== user_code Assign value (truncated) ===')
        print(json.dumps(val, indent=2, ensure_ascii=False, default=str)[:6000])

# Also find so_error_path
found_so = []
def find_so(node):
    if not isinstance(node, dict):
        return
    t = node.get('type')
    if t == 'Assign':
        tgt = node.get('targets', [])
        if tgt and isinstance(tgt[0], dict) and tgt[0].get('id') == 'so_error_path':
            found_so.append(node)
    for v in node.values():
        if isinstance(v, list):
            for x in v:
                find_so(x)
        elif isinstance(v, dict):
            find_so(v)
find_so(fn)
print(f'\nso_error_path Assigns found: {len(found_so)}')
