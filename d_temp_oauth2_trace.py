import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

# Use the actual decompile_pyc pipeline with added debugging
pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(co, name, parent_name=None):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == name:
                if parent_name is None or co.co_name == parent_name:
                    return c
            r = find_code(c, name, parent_name)
            if r: return r
    return None

co = find_code(code, 'post', 'OAuthCallbackHandler')

# Full pipeline
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.decompile import Decompiler

# Monkey-patch _generate_if to add debug output
import core.cfg.region_ast_generator as rag_module
orig_if_gen = rag_module.RegionASTGenerator._generate_if

def debug_if_gen(self, region):
    if isinstance(region, IfRegion) and region.entry and region.entry.start_offset == 140:
        result = orig_if_gen(self, region)
        # Show the result
        def show(d, depth=0):
            if isinstance(d, dict):
                t = d.get('type', '?')
                if t in ('Name', 'Constant'):
                    return f"{t}({d.get('id', d.get('value','?'))})"
                if t in ('Call', 'Attribute', 'Compare', 'BoolOp', 'UnaryOp', 'BinOp'):
                    return f"{t}(...)"
                if t == 'Assign':
                    tgt = show(d.get('targets',[{}])[0], depth+1) if d.get('targets') else '?'
                    return f"Assign({tgt})"
                if t == 'Expr':
                    return f"Expr({show(d.get('value',{}), depth+1)})"
                if t == 'If':
                    body = d.get('body', [])
                    orelse = d.get('orelse', [])
                    test = show(d.get('test',{}), depth+1)
                    body_types = [show(x, depth+1) for x in body[:5]]
                    orelse_types = [show(x, depth+1) for x in orelse[:5]]
                    return f"If(test={test}, body={body_types}, orelse={orelse_types})"
                if t == 'Return':
                    return "Return"
                if t == 'Pass':
                    return "Pass"
                return t
            if isinstance(d, list):
                return [show(x, depth+1) for x in d[:3]]
            return str(d)
        print(f"\n!!! DEBUG: Outer IfRegion(140) _generate_if result: {show(result)}", file=sys.stderr)
        return result
    return orig_if_gen(self, region)

rag_module.RegionASTGenerator._generate_if = debug_if_gen

from pycdc import decompile_pyc
output = decompile_pyc(pyc)
# Find OAuthCallbackHandler.post
lines = output.split('\n')
in_class = False
for line in lines:
    if 'class OAuthCallbackHandler' in line:
        in_class = True
    if in_class:
        print(line)
        if line.startswith('class ') and 'OAuthCallbackHandler' not in line:
            break
