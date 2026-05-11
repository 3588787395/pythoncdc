import sys; sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, BoolOpRegion, IfRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

src = 'if a and b:\n    x = 1'
code = compile(src, '<test>', 'exec')
cfg = CFGBuilder().build(code)
analyzer = RegionAnalyzer(cfg)
regions = analyzer.analyze()

gen = RegionASTGenerator(cfg, analyzer)

orig_process = gen._process_if_blocks
def traced_process(blocks, region, branch='then'):
    result = orig_process(blocks, region, branch)
    for b in blocks:
        is_gen = b in gen.generated_blocks
        role = analyzer.get_block_role(b)
        entry_r = analyzer.get_entry_region_for_block(b)
        print(f"  process block {b.start_offset}: generated={is_gen}, role={role}, entry_region={type(entry_r).__name__ if entry_r else None}")
    print(f"  branch={branch}, result={result}")
    return result
gen._process_if_blocks = traced_process

result = gen.generate()
code_gen = CodeGenerator()
output = code_gen.generate(result)
print(f"\nOutput: {output}")
