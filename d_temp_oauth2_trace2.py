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

# Monkey-patch _generate_if to trace the result for the outer IfRegion
orig_generate_if = RegionASTGenerator._generate_if

call_count = {}
def traced_generate_if(self, region):
    if isinstance(region, IfRegion) and region.entry and region.entry.start_offset == 140:
        result = orig_generate_if(self, region)
        # Find the If node in the result
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and item.get('type') == 'If':
                    body = item.get('body', [])
                    orelse = item.get('orelse', [])
                    print(f"[TRACE] Outer IfRegion(140) _generate_if: If body={len(body)} orelse={len(orelse)}")
                    for i, b in enumerate(body):
                        if isinstance(b, dict):
                            print(f"  body[{i}]: {b.get('type','?')}")
                    for i, o in enumerate(orelse):
                        if isinstance(o, dict):
                            print(f"  orelse[{i}]: {o.get('type','?')}")
        return result
    return orig_generate_if(self, region)

RegionASTGenerator._generate_if = traced_generate_if

# Now run the full decompile pipeline
from pycdc import PycDecompiler
decompiler = PycDecompiler()
decompiler.load_file(pyc)
output = io.StringIO()
decompiler.decompile(output, use_region=True, use_cfg=False)
result = output.getvalue()

# Find the OAuthCallbackHandler.post output
lines = result.split('\n')
in_handler = False
for line in lines:
    if 'class OAuthCallbackHandler' in line:
        in_handler = True
    if in_handler:
        print(line)
        if line.startswith('class ') and 'OAuthCallbackHandler' not in line:
            break
