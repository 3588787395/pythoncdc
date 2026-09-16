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
from core.ast_nodes import ASTNode, ASTBlock, ASTIf

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
ast_gen = RegionASTGenerator(cfg, regions, analyzer)
ast_result = ast_gen.generate()

# Convert the AST dict to ASTNode objects to see what the code generator receives
def dict_to_node(d):
    if not isinstance(d, dict):
        return d
    return ASTNode.from_dict(d)

# The outer If statement for "if user is None:"
if isinstance(ast_result, list):
    for item in ast_result:
        if isinstance(item, dict) and item.get('type') == 'If':
            # This is the "if user is None:" if
            body = item.get('body', [])
            orelse = item.get('orelse', [])
            print(f"Outer If: body={len(body)} items, orelse={len(orelse)} items")
            for i, b in enumerate(body):
                if isinstance(b, dict):
                    print(f"  body[{i}]: type={b.get('type','?')}")
                    if b.get('type') == 'If':
                        print(f"    test_type={b.get('test',{}).get('type','?')}")
                        print(f"    body_len={len(b.get('body',[]))}")
                        print(f"    orelse_len={len(b.get('orelse',[]))}")
                        for j, sb in enumerate(b.get('body',[])):
                            if isinstance(sb, dict):
                                print(f"      body[{j}]: {sb.get('type','?')}")
            for i, o in enumerate(orelse):
                if isinstance(o, dict):
                    print(f"  orelse[{i}]: type={o.get('type','?')}")
