import py_compile, sys, os, json
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from pycdc import decompile_pyc

tf = 'test_r1_try_except_finally.py'
pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)

sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.cfg_builder import CFGBuilder
from core.cfg.region_analyzer import RegionAnalyzer
import dis, marshal, types

with open(pyc, 'rb') as f:
    magic = f.read(4)
    flags = int.from_bytes(f.read(4), 'little')
    if flags & 0x1:
        f.read(8)
    code = marshal.load(f)

cfg_builder = CFGBuilder()
cfg = cfg_builder.build_from_code(code)

region_analyzer = RegionAnalyzer(cfg)
region_analyzer.analyze()

gen = RegionASTGenerator(cfg, region_analyzer)

for r in region_analyzer.regions:
    if hasattr(r, 'has_finally') and r.has_finally:
        print(f"Region: {type(r).__name__}")
        print(f"  has_finally: {r.has_finally}")
        print(f"  has_else: {r.has_else}")
        print(f"  try_blocks: {[b.start_offset for b in r.try_blocks]}")
        print(f"  except_handlers: {[(et, en, [b.start_offset for b in hbs]) for et, en, hbs in r.except_handlers]}")
        print(f"  finally_blocks: {[b.start_offset for b in r.finally_blocks]}")
        print(f"  entry: {r.entry.start_offset}")
        print()

        result = gen._generate_try(r)
        print(f"  Generated AST:")
        print(f"  {json.dumps(result, indent=2, default=str)[:2000]}")

if os.path.exists(pyc): os.remove(pyc)
