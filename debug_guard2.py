import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, RegionType, MatchRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator
from core.cfg.pattern_parser import PatternParser

src = 'match x:\n    case Point(x=x, y=y) if x == y:\n        y = 1\n    case _:\n        y = 0'
code = compile(src, '<test>', 'exec')

cfg_builder = CFGBuilder()
cfg = cfg_builder.build(code)

analyzer = RegionAnalyzer(cfg)
generator = RegionASTGenerator(cfg, analyzer)
result = generator.generate()
analyzer = generator.region_analyzer

match_regions = [r for r in analyzer.regions if isinstance(r, MatchRegion)]
for mr in match_regions:
    print(f"subject_block={mr.subject_block.start_offset}")
    print(f"case_blocks={[cb.start_offset for cb in mr.case_blocks]}")
    print(f"case_bodies={[[b.start_offset for b in body] for body in mr.case_bodies]}")
    print(f"case_guards={mr.case_guards}")
    print(f"blocks={[b.start_offset for b in mr.blocks]}")
    
    # Test pattern block collection
    for cb in mr.case_blocks:
        pattern_blocks = analyzer.pattern_parser.collect_pattern_blocks(cb, mr.blocks)
        print(f"  pattern_blocks for case_block {cb.start_offset}: {[pb.start_offset for pb in pattern_blocks]}")
        guard = analyzer.pattern_parser.parse_case_guard(pattern_blocks)
        print(f"  guard={guard}")
        
        # Debug the guard extraction
        all_instrs = []
        for pb in pattern_blocks:
            for instr in pb.instructions:
                if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    all_instrs.append(instr)
        print(f"  all_instrs (first 20):")
        for idx, instr in enumerate(all_instrs[:20]):
            print(f"    [{idx}] {instr.opname}({instr.argval})")
