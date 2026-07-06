import py_compile, sys, os, types, dis
sys.path.insert(0, r'd:\Desktop\ptrade相关\pythoncdc')

tf = 'test_e03_try_else_finally.py'
pyc = tf + 'c'
py_compile.compile(tf, cfile=pyc, doraise=True)

with open(tf) as f:
    code = compile(f.read(), tf, 'exec')

func_code = code.co_consts[0]
print('Original bytecode:')
for i in dis.get_instructions(func_code):
    if not i.opname.startswith('CACHE'):
        print('  %d: %s %s' % (i.offset, i.opname, repr(i.argval)))

from pycdc.pycdc import load_pyc, decompile
from pycdc.cfg.cfg_builder import CFGBuilder
from pycdc.core.region_analyzer import RegionAnalyzer

pyc_data = load_pyc(pyc)
cfg_builder = CFGBuilder()
cfg = cfg_builder.build(func_code)

print('\nCFG Blocks:')
for offset in sorted(cfg.blocks.keys()):
    block = cfg.blocks[offset]
    instrs = ['%s(%s)' % (i.opname, repr(i.argval)) for i in block.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
    succs = [s.start_offset for s in block.successors]
    print('  Block %d: %s -> %s' % (offset, instrs, succs))

ra = RegionAnalyzer(cfg)
regions = ra.analyze()
print('\nRegions:')
for r in regions:
    print('  %s: entry=%s, blocks=%s' % (
        type(r).__name__,
        r.entry.start_offset if r.entry else None,
        sorted(b.start_offset for b in r.blocks)
    ))
    if hasattr(r, 'try_blocks'):
        print('    try_blocks=%s' % sorted(b.start_offset for b in r.try_blocks))
    if hasattr(r, 'finally_blocks'):
        print('    finally_blocks=%s' % sorted(b.start_offset for b in r.finally_blocks))
    if hasattr(r, 'else_blocks'):
        print('    else_blocks=%s' % sorted(b.start_offset for b in r.else_blocks))
    if hasattr(r, 'has_finally'):
        print('    has_finally=%s' % r.has_finally)

after = ra.find_blocks_after_finally(regions[0]) if regions else []
print('\nBlocks after finally: %s' % sorted(b.start_offset for b in after))

for b in after:
    role = ra.get_block_role(b)
    instrs = ['%s(%s)' % (i.opname, repr(i.argval)) for i in b.instructions if i.opname not in ('RESUME', 'NOP', 'CACHE')]
    print('  Block %d: role=%s, instrs=%s' % (b.start_offset, role, instrs))

if os.path.exists(pyc):
    os.remove(pyc)
