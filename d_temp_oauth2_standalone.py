import sys, types
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

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

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

# Create the generator with recursive=True like _build_function_def does
gen = RegionASTGenerator(cfg, recursive=True, parent_code=code, top_level_code=code)
result = gen.generate()

body = result.get('body', [])
print(f"Function body: {len(body)} items")
for i, b in enumerate(body):
    if isinstance(b, dict):
        t = b.get('type', '?')
        print(f"  body[{i}]: {t}")
        if t == 'If':
            body2 = b.get('body', [])
            orelse2 = b.get('orelse', [])
            print(f"    body_len={len(body2)}")
            print(f"    orelse_len={len(orelse2)}")
            for j, bb in enumerate(body2):
                if isinstance(bb, dict):
                    print(f"      body[{j}]: {bb.get('type','?')}")
            for j, oo in enumerate(orelse2[:5]):
                if isinstance(oo, dict):
                    print(f"      orelse[{j}]: {oo.get('type','?')}")
