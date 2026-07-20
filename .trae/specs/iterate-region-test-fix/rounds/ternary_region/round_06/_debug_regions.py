"""Debug script for R6 ternary bugs - print regions for each failing test case."""
import sys
import os
sys.path.insert(0, '/workspace')
from core.cfg.region_analyzer import RegionAnalyzer, RegionType
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.code_generator import CodeGenerator


CASES = {
    'R6-09 unpack': "x, y = (a if c else b), (d if e else f)",
    'R6-18 lambda': "f = lambda: (a if c else b) + (d if e else g)",
    'R6-19 call_args': "f(a if c else b, d if e else g, h if i else j)",
    'R6-20 subscript_store': "x[a if c else b][d if e else f] = 1",
    'R6-10 listcomp': "z = [a if c else b for x in ys if x > 0]",
    'R6-12 setcomp': "z = {a if c else b for x in ys if x}",
    'R6-13 genexp': "z = list(a if c else b for x in ys if x > 0)",
    'R6-17 annotation': "x: T = a if c else b",
    'R6-06 except_handler': "try:\n    pass\nexcept E:\n    x = a if c else b",
    'R6-02 while_body': "while x:\n    y = a if c else b",
}


def dump_regions(code_obj, indent=0):
    pad = '  ' * indent
    cfg = CFGBuilder().build(code_obj)
    analyzer = RegionAnalyzer(cfg)
    analyzer.analyze()
    print(f"{pad}--- regions for code object {code_obj.co_name} ---")
    for r in analyzer.regions:
        rt = r.region_type.name if hasattr(r.region_type, 'name') else str(r.region_type)
        entry = r.entry.start_offset if r.entry else None
        merge = getattr(r, 'merge_block', None)
        merge_off = merge.start_offset if merge else None
        cond_off = r.condition_block.start_offset if getattr(r, 'condition_block', None) else None
        print(f"{pad}  {type(r).__name__} {rt}: entry={entry} cond={cond_off} "
              f"merge={merge_off} vt={getattr(r, 'value_target', None)} "
              f"ct={getattr(r, 'container_type', None)} "
              f"mc={getattr(r, 'merge_context', None)}")
        # Recurse into nested code objects
        for instr in code_obj.co_consts:
            if hasattr(instr, 'co_code'):
                dump_regions(instr, indent + 1)
                break  # only one level deep enough


for name, src in CASES.items():
    print('=' * 70)
    print(name, '::', src.replace('\n', '\\n'))
    print('=' * 70)
    try:
        code = compile(src, '<test>', 'exec')
        dump_regions(code)
        # Also produce decompiled
        cfg = CFGBuilder().build(code)
        analyzer = RegionAnalyzer(cfg)
        gen = RegionASTGenerator(cfg, analyzer)
        result = gen.generate()
        decomp = CodeGenerator().generate(result)
        print('--- decompiled ---')
        print(decomp)
    except Exception as e:
        import traceback
        traceback.print_exc()
    print()
