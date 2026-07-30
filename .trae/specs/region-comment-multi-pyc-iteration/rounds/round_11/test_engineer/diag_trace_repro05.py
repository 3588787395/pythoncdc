"""[R11 diag] Trace why block@28 (tuple unpack) is skipped in repro_05.

Instruments _generate_block_statements and _process_if_blocks to print
which blocks reach them, plus block_to_region mapping.
"""
import os, sys, py_compile, marshal

REPRO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'minimal_repros')
repro_path = os.path.join(REPRO_DIR, 'repro_05_pattern_c2_main_pyc_mirror.py')
pyc_path = repro_path + 'c'
py_compile.compile(repro_path, doraise=True, cfile=pyc_path)

sys.path.insert(0, os.path.dirname(REPRO_DIR))
sys.path.insert(0, os.path.abspath('.'))

from core.cfg import region_ast_generator as mod

orig_gbs = mod.RegionASTGenerator._generate_block_statements
orig_pib = mod.RegionASTGenerator._process_if_blocks

gbs_blocks = []
pib_calls = []


def traced_gbs(self, block, *a, **k):
    gbs_blocks.append(block)
    return orig_gbs(self, block, *a, **k)


def traced_pib(self, blocks, region, branch='then'):
    pib_calls.append((branch, list(blocks) if blocks else [],
                      getattr(region, 'entry', None),
                      type(region).__name__))
    return orig_pib(self, blocks, region, branch)


mod.RegionASTGenerator._generate_block_statements = traced_gbs
mod.RegionASTGenerator._process_if_blocks = traced_pib

from pycdc import decompile_pyc
src = decompile_pyc(pyc_path)

print('=== _generate_block_statements called for blocks ===')
for b in gbs_blocks:
    print('  block@', b)

print('\n=== _process_if_blocks calls ===')
for branch, blocks, entry, rtype in pib_calls:
    print(f'  branch={branch} region={rtype}@{entry} blocks={blocks}')

# Dump block_to_region for the function's regions
print('\n=== decompiled source ===')
print(src)
