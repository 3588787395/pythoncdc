import sys, os, json
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator

src = "try:\n    with open('a') as fa:\n        with open('b') as fb:\n            x = fa.read() + fb.read()\nexcept:\n    x = ''"
code = compile(src, '<t>', 'exec')

cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
analyzer.analyze()

print("==== DECOMPILED SOURCE ====")
gen = RegionASTGenerator(cfg, analyzer)
ast_dict = gen.generate()
print(json.dumps(ast_dict, indent=2, default=str))

print()
print("==== _meaningful check (L710-714) ====")
code_obj = getattr(cfg, 'code', None)
_consts = code_obj.co_consts
print("co_consts:", _consts)
_all_instrs = []
for b in cfg.blocks.values():
    _all_instrs.extend(b.instructions)
_meaningful = [i for i in _all_instrs if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'RETURN_VALUE', 'RETURN_CONST', 'LOAD_CONST', 'POP_TOP')]
print("_meaningful count:", len(_meaningful))
print("_meaningful:", [(i.offset, i.opname) for i in _meaningful[:20]])

print()
print("==== Full region tree (recursive walk) ====")
def walk_region(r, depth=0):
    indent = "  " * depth
    rt = getattr(r, 'region_type', None)
    entry = getattr(r, 'entry', None)
    entry_off = entry.start_offset if entry is not None else None
    blocks = getattr(r, 'blocks', None)
    block_offs = sorted([b.start_offset for b in blocks]) if blocks else []
    print(f"{indent}{type(r).__name__} type={rt} entry={entry_off} blocks={block_offs}")
    children = getattr(r, 'children', None) or []
    for c in children:
        walk_region(c, depth+1)

for r in analyzer.regions:
    if getattr(r, 'parent', None) is None:
        walk_region(r, 0)
