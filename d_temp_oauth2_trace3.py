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

# Monkey-patch _generate_region to trace calls for IfRegion
orig_generate_region = RegionASTGenerator._generate_region

def traced_generate_region(self, region, skip_store_targets=None):
    if isinstance(region, IfRegion):
        entry_off = region.entry.start_offset if region.entry else None
        print(f"[TRACE] _generate_region(IfRegion entry={entry_off})", file=sys.stderr)
    result = orig_generate_region(self, region, skip_store_targets=skip_store_targets)
    if isinstance(region, IfRegion):
        entry_off = region.entry.start_offset if region.entry else None
        if result is None:
            print(f"[TRACE] _generate_region(IfRegion entry={entry_off}) => None", file=sys.stderr)
        elif isinstance(result, dict):
            print(f"[TRACE] _generate_region(IfRegion entry={entry_off}) => dict type={result.get('type','?')}", file=sys.stderr)
        elif isinstance(result, list):
            types = [item.get('type','?') if isinstance(item, dict) else str(item) for item in result[:5]]
            print(f"[TRACE] _generate_region(IfRegion entry={entry_off}) => list len={len(result)} types={types}", file=sys.stderr)
    return result

RegionASTGenerator._generate_region = traced_generate_region

# Monkey-patch _generate_if to trace
orig_generate_if = RegionASTGenerator._generate_if

def traced_generate_if(self, region):
    entry_off = region.entry.start_offset if region.entry else None
    print(f"[TRACE] _generate_if(IfRegion entry={entry_off})", file=sys.stderr)
    result = orig_generate_if(self, region)
    if isinstance(result, dict):
        print(f"[TRACE] _generate_if(IfRegion entry={entry_off}) => dict type={result.get('type','?')}", file=sys.stderr)
    elif isinstance(result, list):
        types = [item.get('type','?') if isinstance(item, dict) else str(item) for item in result[:5]]
        print(f"[TRACE] _generate_if(IfRegion entry={entry_off}) => list len={len(result)} types={types}", file=sys.stderr)
    return result

RegionASTGenerator._generate_if = traced_generate_if

from pycdc import PycDecompiler
decompiler = PycDecompiler()
decompiler.load_file(pyc)
output = io.StringIO()
decompiler.decompile(output, use_region=True, use_cfg=False)
