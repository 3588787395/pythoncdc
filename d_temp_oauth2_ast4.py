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

# The result should be a list of statements for the function body
print(f"Type of ast_result: {type(ast_result)}")
if isinstance(ast_result, list):
    print(f"Length: {len(ast_result)}")
    for i, item in enumerate(ast_result):
        if isinstance(item, dict):
            print(f"  [{i}] type={item.get('type','?')}")
            if item.get('type') == 'FunctionDef':
                body = item.get('body', [])
                print(f"       body_len={len(body)}")
                for j, b in enumerate(body):
                    if isinstance(b, dict):
                        t = b.get('type', '?')
                        print(f"         body[{j}]: {t}")
                        if t == 'If':
                            body2 = b.get('body', [])
                            orelse2 = b.get('orelse', [])
                            test2 = b.get('test', {})
                            print(f"           test={test2.get('type','?')}")
                            print(f"           body_len={len(body2)}")
                            print(f"           orelse_len={len(orelse2)}")
                            for k, bb in enumerate(body2[:5]):
                                if isinstance(bb, dict):
                                    print(f"             body[{k}]: {bb.get('type','?')}")
                            for k, oo in enumerate(orelse2[:5]):
                                if isinstance(oo, dict):
                                    print(f"             orelse[{k}]: {oo.get('type','?')}")
elif isinstance(ast_result, dict):
    print(json.dumps({k: type(v).__name__ for k, v in ast_result.items()}, indent=2))
