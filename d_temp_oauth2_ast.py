import sys, types, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

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

# Full decompilation pipeline
builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, regions, analyzer)
ast_result = ast_gen.generate()

# Print the AST result for the relevant part
import json
def show(d, depth=0):
    if isinstance(d, dict):
        t = d.get('type', '?')
        if t == 'Name':
            return f"Name({d.get('id','?')})"
        if t == 'Constant':
            v = d.get('value','?')
            if isinstance(v, str) and len(v) > 20:
                v = v[:20] + '...'
            return f"Const({v})"
        if t == 'Call':
            func = show(d.get('func',{}), depth+1)
            return f"Call({func})"
        if t == 'Attribute':
            return f"Attr({d.get('attr','?')})"
        if t in ('Assign', 'AugAssign'):
            tgt = show(d.get('targets',[{}])[0], depth+1) if d.get('targets') else '?'
            val = show(d.get('value',{}), depth+1)
            return f"{t}({tgt} = {val})"
        if t == 'Expr':
            return f"Expr({show(d.get('value',{}), depth+1)})"
        if t == 'If':
            test = show(d.get('test',{}), depth+1)
            body_len = len(d.get('body',[]))
            else_len = len(d.get('orelse',[]))
            return f"If(test={test}, body=[{body_len} stmts], orelse=[{else_len} stmts])"
        if t == 'Return':
            return f"Return({show(d.get('value',{}), depth+1)})"
        if t == 'Yield':
            return f"Yield({show(d.get('value',{}), depth+1)})"
        if t == 'Pass':
            return 'Pass'
        if t == 'FunctionDef':
            name = d.get('name','?')
            body_len = len(d.get('body',[]))
            return f"Def({name}, body=[{body_len} stmts])"
        if t == 'ClassDef':
            name = d.get('name','?')
            body_len = len(d.get('body',[]))
            return f"Class({name}, body=[{body_len} stmts])"
        return t
    if isinstance(d, list):
        items = [show(v, depth+1) for v in d]
        if len(items) > 10:
            return items[:10] + ['...']
        return items
    return str(d)

# Find the relevant part
if isinstance(ast_result, list):
    for item in ast_result:
        r = show(item)
        if 'Class' in str(r) or 'post' in str(r).lower() or 'OAuth' in str(r):
            print(json.dumps(r, indent=2, default=str))
