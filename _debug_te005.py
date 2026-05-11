import sys, dis
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

tests = [
    ('te005', 'try:\n    x = 1\nexcept:\n    y = 2\nfinally:\n    z = 3'),
    ('te080', 'try:\n    x = 1\nexcept:\n    try:\n        y = 2\n    except:\n        z = 3'),
]

for name, source in tests:
    print(f'=== {name} ===')
    try:
        code = compile(source, '<test>', 'exec')
        cfg = CFGBuilder().build(code)
        analyzer = RegionAnalyzer(cfg)
        regions = analyzer.analyze()

        for r in regions:
            if isinstance(r, TryExceptRegion):
                print(f'  Region: type={r.region_type} try={r.try_offset_start}-{r.try_offset_end}')
                print(f'    try_blocks={[b.start_offset for b in r.try_blocks]}')
                if r.except_handlers:
                    for i, (t, n, bl) in enumerate(r.except_handlers):
                        print(f'    except[{i}]: type={t}, name={n}, blocks={[b.start_offset for b in bl]}')
                if r.handler_entry_blocks:
                    print(f'    handler_entry={[b.start_offset for b in r.handler_entry_blocks]}')
                if hasattr(r, 'finally_blocks') and r.finally_blocks:
                    print(f'    finally_blocks={[b.start_offset for b in r.finally_blocks]}')
                print(f'    has_finally={r.has_finally}')
                if hasattr(r, 'finally_copy_blocks') and r.finally_copy_blocks:
                    print(f'    finally_copy_blocks={r.finally_copy_blocks}')

        generator = RegionASTGenerator(cfg, analyzer)
        result = generator.generate()
        code_gen = CodeGenerator()
        output = code_gen.generate(result)
        print(f'  Output: {output!r}')
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f'  ERROR: {e}')
    print()
