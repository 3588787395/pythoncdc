import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def debug(src, name=""):
    code = compile(src, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    regions = analyzer.analyze()
    
    print(f"=== {name} ===")
    print(f"Regions: {len(regions)}")
    for r in regions:
        rtype = type(r).__name__
        entry_off = r.entry.start_offset if r.entry else None
        blocks = [b.start_offset for b in r.blocks] if hasattr(r, 'blocks') else []
        print(f"  {rtype}: entry={entry_off}, blocks={blocks}")
        if hasattr(r, 'with_blocks'):
            print(f"    with_blocks={[b.start_offset for b in r.with_blocks]}")
        if hasattr(r, 'target'):
            print(f"    target={r.target}")
        if hasattr(r, 'body_offset_start'):
            print(f"    body_offset_start={r.body_offset_start}")
        if hasattr(r, 'body_offset_end'):
            print(f"    body_offset_end={r.body_offset_end}")
        if hasattr(r, 'children'):
            for child in r.children:
                ctype = type(child).__name__
                centry = child.entry.start_offset if child.entry else None
                cblocks = [b.start_offset for b in child.blocks] if hasattr(child, 'blocks') else []
                print(f"    child: {ctype} entry={centry}, blocks={cblocks}")
    
    print("\n=== Blocks ===")
    for offset in sorted(cfg.blocks.keys()):
        block = cfg.blocks[offset]
        role = analyzer.get_block_role(block)
        instrs = [(i.offset, i.opname, getattr(i, 'argval', None)) for i in block.instructions]
        print(f"  Block {offset} (role={role}): {instrs}")

    print("\n=== Exception Table ===")
    for entry in cfg.exception_table:
        print(f"  {entry}")
    
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    code_gen = CodeGenerator()
    output = code_gen.generate(result)
    print(f"\nDecompiled:\n{output}")
    print()

debug('with ctx1:\n    pass\nwith ctx2:\n    pass', 'w091')
