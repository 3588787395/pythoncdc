import sys, os, dis, types
sys.path.insert(0, '/workspace')

from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.region_analyzer import RegionAnalyzer, TryExceptRegion
from core.cfg.code_generator import CodeGenerator

def diagnose(name, source):
    print(f"\n{'='*60}")
    print(f"[{name}]")
    print(f"{'='*60}")
    code = compile(source, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    
    gen = RegionASTGenerator(cfg)
    regions = gen.region_analyzer.analyze()
    
    for i, r in enumerate(regions):
        if isinstance(r, TryExceptRegion):
            print(f"  Region[{i}]: try_offset={r.try_offset_start}-{r.try_offset_end}, handlers={r.except_handlers}")
            print(f"    handler_entry_blocks={[b.start_offset for b in r.handler_entry_blocks]}")
            print(f"    has_finally={r.has_finally}, finally_blocks={[b.start_offset for b in r.finally_blocks] if r.finally_blocks else []}")
            print(f"    try_blocks={[b.start_offset for b in r.try_blocks]}")
            print(f"    parent={type(r.parent).__name__ if r.parent else None}")
    
    result = gen.generate()
    code_gen = CodeGenerator()
    decompiled = code_gen.generate(result)
    print(f"  DECOMPILED:\n{decompiled}")
    
    # Check nested code objects
    for const in code.co_consts:
        if isinstance(const, types.CodeType):
            print(f"\n  NESTED CODE: {const.co_name}")
            orig_instrs = list(dis.get_instructions(const))
            print(f"  ORIG BYTECODE ({len(orig_instrs)} instrs):")
            for i2, instr in enumerate(orig_instrs):
                print(f"    {i2}: {instr.opname} {instr.argval!r}")
    
    try:
        recompiled = compile(decompiled, '<recompiled>', 'exec')
        for const in recompiled.co_consts:
            if isinstance(const, types.CodeType):
                print(f"\n  RECOMP NESTED CODE: {const.co_name}")
                recomp_instrs = list(dis.get_instructions(const))
                print(f"  RECOMP BYTECODE ({len(recomp_instrs)} instrs):")
                for i2, instr in enumerate(recomp_instrs):
                    print(f"    {i2}: {instr.opname} {instr.argval!r}")
    except SyntaxError as e:
        print(f"  RECOMPILE ERROR: {e}")

# B1: try-finally-return
diagnose('B1', 'def f():\n    try:\n        return 1\n    finally:\n        pass')

# D1: te104
diagnose('D1', "def f():\n    try:\n        x = 1\n    except ValueError:\n        return 'val'\n    finally:\n        cleanup()")

# D4: try15_try_return
diagnose('D4', 'def safe_get(d, key):\n    try:\n        return d[key]\n    except KeyError:\n        return default')
