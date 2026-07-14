import sys, os, json
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, Region, IfRegion, WithRegion, TryExceptRegion
from core.cfg.cfg_builder import CFGBuilder
import core.cfg.region_ast_generator as rag_mod

src = "try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()\nexcept:\n    x = ''"
code = compile(src, '<t>', 'exec')

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("==== entry_block ====")
print("cfg.entry_block:", cfg.entry_block, getattr(cfg.entry_block, 'start_offset', None))

print()
print("==== top_level regions (parent is None) ====")
for r in analyzer.regions:
    if r.parent is None:
        print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} blocks={sorted([b.start_offset for b in r.blocks])}")

print()
print("==== ALL regions with parent info ====")
for r in analyzer.regions:
    p = r.parent
    p_off = p.entry.start_offset if (p and p.entry) else None
    print(f"  {type(r).__name__} entry={r.entry.start_offset if r.entry else None} parent_entry={p_off}")

# Monkey-patch _generate_region to trace If creation
gen_cls = rag_mod.RegionASTGenerator
orig_generate_region = gen_cls._generate_region
orig_generate_if = None
if hasattr(gen_cls, '_generate_if_region'):
    orig_generate_if = gen_cls._generate_if_region

call_log = []
def traced_generate_region(self, region):
    rt = getattr(region, 'region_type', None)
    e = getattr(region, 'entry', None)
    eoff = e.start_offset if e is not None else None
    result = orig_generate_region(self, region)
    # check for If nodes with Constant True test
    def find_if_true(node, path=""):
        hits = []
        if isinstance(node, dict):
            if node.get('type') == 'If':
                t = node.get('test')
                if isinstance(t, dict) and t.get('type') == 'Constant' and t.get('value') is True:
                    body = node.get('body')
                    orelse = node.get('orelse', 'MISSING')
                    is_pass = (isinstance(body, list) and len(body)==1 and isinstance(body[0], dict) and body[0].get('type')=='Pass')
                    hits.append((path, is_pass, orelse))
            for k, v in node.items():
                hits.extend(find_if_true(v, path + "." + str(k)))
        elif isinstance(node, list):
            for i, item in enumerate(node):
                hits.extend(find_if_true(item, path + f"[{i}]"))
        return hits
    hits = find_if_true(result)
    if hits:
        print(f"  [TRACE] _generate_region({type(region).__name__} entry={eoff} rt={rt}) produced If-True hits: {hits}")
    return result

gen_cls._generate_region = traced_generate_region

# Also patch list.append/extend on ast_nodes - we can't easily, but we can patch _build_statement
# Instead, let's just generate and see
gen = rag_mod.RegionASTGenerator(cfg, analyzer)
ast_dict = gen.generate()

print()
print("==== FINAL Module body types ====")
for i, node in enumerate(ast_dict.get('body', [])):
    t = node.get('type') if isinstance(node, dict) else type(node).__name__
    extra = ""
    if t == 'If':
        test = node.get('test')
        if isinstance(test, dict) and test.get('type') == 'Constant':
            extra = f" test=Constant({test.get('value')})"
        body = node.get('body')
        if isinstance(body, list) and len(body)==1 and isinstance(body[0], dict) and body[0].get('type')=='Pass':
            extra += " body=[Pass]"
        extra += f" orelse={node.get('orelse', 'MISSING')!r}"
    print(f"  [{i}] type={t}{extra}")
