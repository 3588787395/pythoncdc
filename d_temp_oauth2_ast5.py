import sys, types, io, json
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
ast_gen = RegionASTGenerator(cfg, regions, analyzer)
ast_result = ast_gen.generate()

# ast_result is a FunctionDef dict
body = ast_result.get('body', [])
print(f"Function body: {len(body)} items")
for j, b in enumerate(body):
    if isinstance(b, dict):
        t = b.get('type', '?')
        print(f"  body[{j}]: {t}")
        if t == 'If':
            body2 = b.get('body', [])
            orelse2 = b.get('orelse', [])
            test2 = b.get('test', {})
            print(f"    test={test2.get('type','?')}")
            if test2.get('type') == 'Compare':
                left = test2.get('left', {})
                print(f"    test.left={left.get('type','?')}({left.get('id', left.get('attr',''))})")
            print(f"    body_len={len(body2)}")
            print(f"    orelse_len={len(orelse2)}")
            for k, bb in enumerate(body2):
                if isinstance(bb, dict):
                    print(f"      body[{k}]: {bb.get('type','?')}")
                    if bb.get('type') == 'If':
                        b3 = bb.get('body', [])
                        o3 = bb.get('orelse', [])
                        print(f"        nested_if body_len={len(b3)} orelse_len={len(o3)}")
                        for m, bbb in enumerate(b3[:5]):
                            if isinstance(bbb, dict):
                                print(f"          body[{m}]: {bbb.get('type','?')}")
                        for m, ooo in enumerate(o3[:5]):
                            if isinstance(ooo, dict):
                                print(f"          orelse[{m}]: {ooo.get('type','?')}")
            for k, oo in enumerate(orelse2[:5]):
                if isinstance(oo, dict):
                    print(f"      orelse[{k}]: {oo.get('type','?')}")
