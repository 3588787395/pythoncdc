import sys, types, io
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

orig = RegionASTGenerator._generate_if
def traced(self, region):
    if isinstance(region, IfRegion) and region.entry and region.entry.start_offset == 140:
        print('IfRegion(140): entry in generated_blocks = %s' % (region.entry in self.generated_blocks), file=sys.stderr)
        result = orig(self, region)
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and item.get('type') == 'If':
                    bl = len(item.get('body', []))
                    ol = len(item.get('orelse', []))
                    print('  If body_len=%d orelse_len=%d' % (bl, ol), file=sys.stderr)
        elif isinstance(result, dict) and result.get('type') == 'If':
            bl = len(result.get('body', []))
            ol = len(result.get('orelse', []))
            print('  If body_len=%d orelse_len=%d' % (bl, ol), file=sys.stderr)
        return result
    return orig(self, region)
RegionASTGenerator._generate_if = traced

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()
gen = RegionASTGenerator(cfg, recursive=True, parent_code=code, top_level_code=code)
result = gen.generate()
