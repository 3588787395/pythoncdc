import sys, types, io
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')

pyc = 'F:/Downloads/pythoncdc-main/site-packages/fly/oauthenticator/oauth2.pyc'
import marshal
with open(pyc, 'rb') as f:
    f.read(16)
    code = marshal.load(f)

# Find OAuthCallbackHandler.post
def find_code_by_varnames(co, target_varnames):
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            if c.co_name == 'post' and c.co_varnames[:3] == target_varnames[:3]:
                return c
            r = find_code_by_varnames(c, target_varnames)
            if r: return r
    return None

co = find_code_by_varnames(code, ('self', 'op_station', 'user'))

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator

# Monkey-patch _build_function_def to trace the specific post function
orig_build_func = RegionASTGenerator._build_function_def

def traced_build_func(self, *args, **kwargs):
    func_obj = kwargs.get('func_obj') or (args[0] if args else None)
    if func_obj and hasattr(func_obj, 'co_name') and func_obj.co_name == 'post':
        if hasattr(func_obj, 'co_varnames') and func_obj.co_varnames[:3] == ('self', 'op_station', 'user'):
            print(f"\n[TRACE] _build_function_def for OAuthCallbackHandler.post", file=sys.stderr)
    result = orig_build_func(self, *args, **kwargs)
    return result

RegionASTGenerator._build_function_def = traced_build_func

# Monkey-patch _generate_block_statements_body to trace block 140 generation
orig_gen_block_body = RegionASTGenerator._generate_block_statements_body

_traced_func_id = None

def traced_gen_block_body(self, block, *args, **kwargs):
    global _traced_func_id
    if _traced_func_id is not None and hasattr(block, 'start_offset') and block.start_offset == 140:
        print(f"\n[TRACE] _generate_block_statements_body(block 140) called", file=sys.stderr)
        print(f"  block already in generated_blocks: {block in self.generated_blocks}", file=sys.stderr)
        # Show what instructions are in this block
        for inst in block.instructions[:5]:
            print(f"  inst: {inst.offset} {inst.opname} {inst.argval}", file=sys.stderr)
    result = orig_gen_block_body(self, block, *args, **kwargs)
    if _traced_func_id is not None and hasattr(block, 'start_offset') and block.start_offset == 140:
        print(f"  result: {len(result) if isinstance(result, list) else type(result).__name__}", file=sys.stderr)
        for i, r in enumerate(result[:5] if isinstance(result, list) else []):
            if isinstance(r, dict):
                print(f"    [{i}] {r.get('type','?')}", file=sys.stderr)
    return result

RegionASTGenerator._generate_block_statements_body = traced_gen_block_body

# Also trace when block 140 is added to generated_blocks in this function's context
class FuncTracingSet(set):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._active = False
    
    def add(self, item):
        if self._active and hasattr(item, 'start_offset') and item.start_offset == 140:
            import traceback
            print(f"\n[TRACE] generated_blocks.add(block 140) in OAuthCallbackHandler.post context", file=sys.stderr)
            traceback.print_stack(limit=5, file=sys.stderr)
        super().add(item)

from pycdc import PycDecompiler
decompiler = PycDecompiler()
decompiler.load_file(pyc)

# Monkey-patch the RegionASTGenerator.__init__ to insert our tracing set
# only for the OAuthCallbackHandler.post function
_orig_gen_init = RegionASTGenerator.__init__
_orig_generate = RegionASTGenerator.generate

def traced_generate(self):
    global _traced_func_id
    # Check if this is the OAuthCallbackHandler.post function
    if self.cfg and self.cfg.name == 'post':
        co_varnames = getattr(self.cfg, '_code_obj', None)
        if co_varnames and hasattr(co_varnames, 'co_varnames'):
            if co_varnames.co_varnames[:3] == ('self', 'op_station', 'user'):
                _traced_func_id = id(self)
                # Replace generated_blocks with tracing set
                old_gb = self.generated_blocks
                self.generated_blocks = FuncTracingSet(old_gb)
                self.generated_blocks._active = True
                result = _orig_generate(self)
                self.generated_blocks._active = False
                _traced_func_id = None
                return result
    return _orig_generate(self)

RegionASTGenerator.generate = traced_generate

output = io.StringIO()
decompiler.decompile(output, use_region=True, use_cfg=False)
