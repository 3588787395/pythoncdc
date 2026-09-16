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
from core.cfg.region_analyzer import RegionAnalyzer, IfRegion, BoolOpRegion
from core.cfg.region_ast_generator import RegionASTGenerator

# Trace generated_blocks throughout generate()
class TracingSet(set):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def add(self, item):
        if hasattr(item, 'start_offset') and item.start_offset == 140:
            import traceback
            print(f"\n!!! generated_blocks.add(block 140) !!!", file=sys.stderr)
            # Show abbreviated stack
            stack = traceback.format_stack()
            for frame in stack[-5:]:
                print(frame.rstrip(), file=sys.stderr)
        super().add(item)

orig_init = RegionASTGenerator.__init__
def traced_init(self, *args, **kwargs):
    orig_init(self, *args, **kwargs)
    if not hasattr(self, '_tracing_set_installed'):
        self.generated_blocks = TracingSet(self.generated_blocks)
        self._tracing_set_installed = True

RegionASTGenerator.__init__ = traced_init

builder = CFGBuilder()
cfg = builder.build(co)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

gen = RegionASTGenerator(cfg, recursive=True, parent_code=code, top_level_code=code)
result = gen.generate()

body = result.get('body', [])
print(f"\nFunction body: {len(body)} items")
