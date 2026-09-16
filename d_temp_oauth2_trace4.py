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
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

# Monkey-patch _generate_if to trace the early-return paths
orig_generate_if = RegionASTGenerator._generate_if

def traced_generate_if(self, region):
    if isinstance(region, IfRegion) and region.entry and region.entry.start_offset == 140:
        print(f"[TRACE] _generate_if(140) called", file=sys.stderr)
        print(f"  region_type={region.region_type.name}", file=sys.stderr)
        
        # Check BoolOpRegion ownership
        _entry_owner = self.region_analyzer.block_to_region.get(region.entry)
        print(f"  entry_owner={type(_entry_owner).__name__ if _entry_owner else None}", file=sys.stderr)
        if isinstance(_entry_owner, BoolOpRegion):
            print(f"  value_target={getattr(_entry_owner, 'value_target', None)}", file=sys.stderr)
            print(f"  parent_is_self={_entry_owner.parent is region}", file=sys.stderr)
        
        # Check generated_blocks state
        print(f"  generated_blocks_count={len(self.generated_blocks)}", file=sys.stderr)
        print(f"  region.entry in generated_blocks={region.entry in self.generated_blocks}", file=sys.stderr)
        for b in region.blocks:
            if b in self.generated_blocks:
                print(f"  block {b.start_offset} already generated!", file=sys.stderr)
        
        # Check _generated_regions
        for r in self.regions:
            if id(r) in self._generated_regions:
                rtype = type(r).__name__
                entry_off = getattr(r, 'entry', None)
                if entry_off and hasattr(entry_off, 'start_offset'):
                    entry_off = entry_off.start_offset
                print(f"  region {rtype}(entry={entry_off}) already generated", file=sys.stderr)
    
    return orig_generate_if(self, region)

RegionASTGenerator._generate_if = traced_generate_if

from pycdc import PycDecompiler
decompiler = PycDecompiler()
decompiler.load_file(pyc)
output = io.StringIO()
decompiler.decompile(output, use_region=True, use_cfg=False)
