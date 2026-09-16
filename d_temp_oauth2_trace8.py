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

co = find_code(code, 'post', ('self', 'op_station', 'user'))

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator

# Trace the generate() method's top_level_regions and entry block processing
orig_generate = RegionASTGenerator.generate

def traced_generate(self):
    from core.cfg.region_analyzer import LoopRegion, TryExceptRegion, WithRegion, MatchRegion, TernaryRegion, AssertRegion
    
    # Run original generate but with tracing
    func_name = self.cfg.name
    
    # Get the entry block
    entry_block = self.cfg.entry_block
    if entry_block is not None:
        if self.region_analyzer.metadata.get('is_generator_entry'):
            gen_entry = self.region_analyzer.metadata.get('generator_entry_block', entry_block)
            if gen_entry is not entry_block:
                entry_block = gen_entry
    
    print(f"\n[TRACE] generate() for function: {func_name}", file=sys.stderr)
    print(f"  entry_block: {entry_block.start_offset if entry_block else None}", file=sys.stderr)
    
    # Run the original generate to get regions
    self.regions = self.region_analyzer.analyze()
    
    top_level = [r for r in self.regions if r.parent is None]
    print(f"  top_level regions: {len(top_level)}", file=sys.stderr)
    for r in top_level:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else None
        print(f"    {rtype}(entry={entry_off}) blocks={len(r.blocks)}", file=sys.stderr)
    
    # Now check which blocks are in generated_blocks after entry processing
    result = orig_generate(self)
    
    # After generate, check the ast_nodes
    if isinstance(result, dict):
        body = result.get('body', [])
        print(f"\n  AST result: type={result.get('type')} body_len={len(body)}", file=sys.stderr)
        for i, b in enumerate(body[:5]):
            if isinstance(b, dict):
                print(f"    body[{i}]: {b.get('type','?')}", file=sys.stderr)
    
    return result

RegionASTGenerator.generate = traced_generate

from pycdc import PycDecompiler
decompiler = PycDecompiler()
decompiler.load_file(pyc)
output = io.StringIO()
decompiler.decompile(output, use_region=True, use_cfg=False)
