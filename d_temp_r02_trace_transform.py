import sys, types, marshal
sys.path.insert(0, '.')

# Monkey-patch _loop_extract_self_loop_stmts to trace its output
from core.cfg import region_ast_generator as rag
_orig_extract = rag.RegionASTGenerator._loop_extract_self_loop_stmts

def _traced_extract(self, hdr):
    result = _orig_extract(self, hdr)
    if hdr.start_offset == 50:
        import json
        print("=== _loop_extract_self_loop_stmts for block 50 ===")
        print(json.dumps(result, indent=2, default=str)[:2000])
    return result

rag.RegionASTGenerator._loop_extract_self_loop_stmts = _traced_extract

# Monkey-patch _loop_generate_body to trace body_stmts at key points
_orig_gen_body = rag.RegionASTGenerator._loop_generate_body

class _TraceList(list):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def extend(self, items):
        super().extend(items)
        for item in items:
            if isinstance(item, dict) and item.get('type') == 'If':
                test = item.get('test', {})
                if isinstance(test, dict) and test.get('type') == 'UnaryOp' and test.get('op') == 'not':
                    import json
                    print(f"=== IF with NOT added to body_stmts ===")
                    print(f"  test: not {json.dumps(test.get('operand', {}), default=str)[:200]}")
                    print(f"  body types: {[s.get('type') for s in item.get('body', [])]}")
                    print(f"  orelse types: {[s.get('type') for s in item.get('orelse', []) if s]}")
                elif isinstance(test, dict) and test.get('type') == 'Call':
                    func = test.get('func', {})
                    if isinstance(func, dict) and func.get('attr') == 'is_trading_date':
                        import json
                        print(f"=== IF with is_trading_date added to body_stmts ===")
                        print(f"  test type: {test.get('type')}")
                        print(f"  body types: {[s.get('type') for s in item.get('body', [])]}")
                        print(f"  orelse types: {[s.get('type') for s in item.get('orelse', []) if s]}")

    def append(self, item):
        super().append(item)
        if isinstance(item, dict) and item.get('type') == 'If':
            test = item.get('test', {})
            if isinstance(test, dict) and (test.get('type') == 'UnaryOp' or test.get('attr') == 'is_trading_date'):
                import json
                print(f"=== IF appended to body_stmts ===")
                print(f"  test: {json.dumps(test, default=str)[:200]}")
                print(f"  body types: {[s.get('type') for s in item.get('body', [])]}")
                print(f"  orelse types: {[s.get('type') for s in item.get('orelse', []) if s]}")

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, LoopRegion
import marshal

with open('site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc', 'rb') as f:
    f.read(16)
    code = marshal.load(f)

def find_code(code_obj, name):
    for const in code_obj.co_consts:
        if isinstance(const, types.CodeType):
            if const.co_name == name:
                return const
            result = find_code(const, name)
            if result:
                return result
    return None

tick = find_code(code, 'tick_worker_thread')
builder = CFGBuilder()
cfg = builder.build(tick)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

inner_loop = None
for region in analyzer.regions:
    if isinstance(region, LoopRegion) and region.header_block and region.header_block.start_offset == 50:
        inner_loop = region
        break

gen = rag.RegionASTGenerator(cfg, analyzer)
loop_ast = gen._generate_loop(inner_loop)
