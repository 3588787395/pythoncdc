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
gen = RegionASTGenerator(cfg, recursive=True, parent_code=code, top_level_code=code)
result = gen.generate()

body = result.get('body', [])
print('Function body: %d items' % len(body))
for i, b in enumerate(body):
    if isinstance(b, dict):
        t = b.get('type', '?')
        if t == 'If':
            test = b.get('test', {})
            test_type = test.get('type', '?') if isinstance(test, dict) else '?'
            test_id = test.get('id', '?') if isinstance(test, dict) and test.get('type') == 'Name' else ''
            bl = len(b.get('body', []))
            ol = len(b.get('orelse', []))
            print('  body[%d]: If test=%s(%s) body_len=%d orelse_len=%d' % (i, test_type, test_id, bl, ol))
            for j, bb in enumerate(b.get('body', [])[:3]):
                if isinstance(bb, dict):
                    print('    body[%d]: %s' % (j, bb.get('type', '?')))
        else:
            print('  body[%d]: %s' % (i, t))
