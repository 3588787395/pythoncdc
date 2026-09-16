import sys, types, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

# Patch _generate_if to check and trace for IfRegion@140
orig_generate_if = RegionASTGenerator._generate_if

def traced_generate_if(self, region):
    if isinstance(region, IfRegion) and region.entry and region.entry.start_offset == 140:
        # Check if entry is already generated
        if region.entry in self.generated_blocks:
            # Find who generated it - check if it's in _generated_regions
            print(f"\n[TRACE] IfRegion(140) entry already generated!", file=sys.stderr)
            print(f"  generated_blocks offsets: {sorted(b.start_offset for b in self.generated_blocks)}", file=sys.stderr)
            
            # Check the region's condition_block
            cond = getattr(region, 'condition_block', None)
            if cond:
                print(f"  condition_block offset: {cond.start_offset}", file=sys.stderr)
                print(f"  condition_block in generated: {cond in self.generated_blocks}", file=sys.stderr)
            
            # Check if the entire region's blocks are already generated
            all_gen = all(b in self.generated_blocks for b in region.blocks)
            print(f"  all region blocks generated: {all_gen}", file=sys.stderr)
            
            # Show which blocks are NOT generated
            not_gen = [b.start_offset for b in region.blocks if b not in self.generated_blocks]
            print(f"  not-generated blocks: {not_gen}", file=sys.stderr)
    
    return orig_generate_if(self, region)

RegionASTGenerator._generate_if = traced_generate_if

from pycdc import PycDecompiler
decompiler = PycDecompiler()
decompiler.load_file(pyc)
output = io.StringIO()
decompiler.decompile(output, use_region=True, use_cfg=False)
