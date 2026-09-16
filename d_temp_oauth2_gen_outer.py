import sys, types, json
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

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
builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
gen = RegionASTGenerator(cfg, regions, analyzer)

outer_if = None
for r in regions:
    if isinstance(r, IfRegion) and r.entry and r.entry.start_offset == 140:
        outer_if = r
        break

result = gen._generate_if(outer_if)
print("Outer IfRegion generated result:")
def show(d, depth=0):
    if isinstance(d, dict):
        t = d.get('type', '?')
        if t == 'Name':
            return f"Name({d.get('id','?')})"
        if t == 'Constant':
            return f"Const({d.get('value','?')})"
        if t in ('Call', 'Attribute', 'BoolOp', 'Compare', 'UnaryOp', 'BinOp'):
            return f"{t}(...)"
        if t == 'Assign':
            tgt = show(d.get('targets',[{}])[0], depth+1) if d.get('targets') else '?'
            val = show(d.get('value',{}), depth+1)
            return f"Assign({tgt} = {val})"
        if t == 'Expr':
            return f"Expr({show(d.get('value',{}), depth+1)})"
        if t == 'If':
            test = show(d.get('test',{}), depth+1)
            body_len = len(d.get('body',[]))
            else_len = len(d.get('orelse',[]))
            return f"If(test={test}, body=[{body_len} stmts], orelse=[{else_len} stmts])"
        if t == 'Return':
            return f"Return({show(d.get('value',{}), depth+1)})"
        if t == 'Pass':
            return 'Pass'
        return t
    if isinstance(d, list):
        return [show(v, depth+1) for v in d]
    return str(d)

print(json.dumps(show(result), indent=2, default=str))
