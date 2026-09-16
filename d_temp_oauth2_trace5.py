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

# Monkey-patch generated_blocks.add to trace who adds block 140
class TracingSet(set):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._target_offsets = {140}
    
    def add(self, item):
        if hasattr(item, 'start_offset') and item.start_offset in self._target_offsets:
            import traceback
            print(f"\n[TRACE] generated_blocks.add(block {item.start_offset})", file=sys.stderr)
            traceback.print_stack(limit=10, file=sys.stderr)
        super().add(item)

from core.cfg.region_ast_generator import RegionASTGenerator

orig_init = RegionASTGenerator.__init__
def traced_init(self, *args, **kwargs):
    orig_init(self, *args, **kwargs)
    self.generated_blocks = TracingSet(self.generated_blocks)

RegionASTGenerator.__init__ = traced_init

from pycdc import PycDecompiler
decompiler = PycDecompiler()
decompiler.load_file(pyc)
output = io.StringIO()
try:
    decompiler.decompile(output, use_region=True, use_cfg=False)
except:
    pass
