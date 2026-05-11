import sys, os
sys.path.insert(0, '.')
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.code_generator import CodeGenerator

def decompile_src(src):
    code = compile(src, '<test>', 'exec')
    cfg_builder = CFGBuilder()
    cfg = cfg_builder.build(code)
    analyzer = RegionAnalyzer(cfg)
    generator = RegionASTGenerator(cfg, analyzer)
    result = generator.generate()
    code_gen = CodeGenerator()
    return code_gen.generate(result)

# W026: with containing try/except
print('=== W026 ===')
src = "with open('f') as f:\n    try:\n        x = f.read()\n    except:\n        y = 1"
print(repr(decompile_src(src)))
print()

# W036: with containing try/except with multiple except
print('=== W036 ===')
src = 'with ctx:\n    try:\n        x = 1\n    except TypeError:\n        y = 2\n    except ValueError:\n        z = 3'
print(repr(decompile_src(src)))
print()

# W097: with containing try/except (simple)
print('=== W097 ===')
src = 'with ctx:\n    try:\n        pass\n    except:\n        pass'
print(repr(decompile_src(src)))
print()

# W074: with containing try/except
print('=== W074 ===')
src = 'with ctx:\n    try:\n        x = risky_operation()\n    except:\n        x = fallback()'
print(repr(decompile_src(src)))
print()

# W042: with containing try/except
print('=== W042 ===')
src = 'with lock:\n    try:\n        x = critical_section()\n    except:\n        x = None'
print(repr(decompile_src(src)))
print()

# W040: nested with + try
print('=== W040 ===')
src = "with open('a') as fa:\n    with open('b') as fb:\n        try:\n            x = fa.read() + fb.read()\n        except:\n            x = ''"
print(repr(decompile_src(src)))
print()

# W045: with + try/except/else
print('=== W045 ===')
src = "with open('f') as f:\n    try:\n        x = f.read()\n    except IOError:\n        x = ''\n    else:\n        y = len(x)"
print(repr(decompile_src(src)))
print()

# W050: multi-context with + try
print('=== W050 ===')
src = "with open('a') as fa, open('b') as fb:\n    try:\n        x = fa.read()\n        y = fb.read()\n    except:\n        x = y = ''"
print(repr(decompile_src(src)))
print()

# W15WithTry: with inside try inside while
print('=== W15WithTry ===')
src = "while True:\n    try:\n        with open('f') as a:\n            pass\n    except IndexError:\n        pass"
print(repr(decompile_src(src)))
print()
