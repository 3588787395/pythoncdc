"""Temporary trace: which generation path consumes block B2 (offset 8) of if_in_while."""
import sys, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

PYC = r"F:\Downloads\pythoncdc-main\test_repros\round2\x01_if_deep_hosts.pyc"
f = open(PYC, 'rb'); f.read(16)
module_code = marshal.load(f)
target = None
for const in module_code.co_consts:
    if hasattr(const, 'co_name') and const.co_name == 'if_in_while':
        target = const
        break

from core.cfg import build_cfg
from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

TRACE = [8, 0]

def wrap(cls, name, show_ret=False):
    orig = getattr(cls, name)
    def patched(self, *a, **k):
        tags = []
        for x in a:
            if hasattr(x, 'start_offset'):
                tags.append(f"blk@{x.start_offset}")
            elif hasattr(x, 'header_block'):
                hb = getattr(x, 'header_block', None)
                tags.append(f"region[hdr={hb.start_offset if hb else None}]")
        r = orig(self, *a, **k)
        if show_ret:
            print(f"RET {name}({', '.join(tags)}) = {repr(r)[:400]}")
        else:
            print(f"CALL {name}({', '.join(tags)})")
        return r
    setattr(cls, name, patched)

for m in ['_loop_generate_body', '_loop_dispatch_block', '_loop_handle_header',
          '_loop_handle_header_no_condition', '_generate_loop',
          '_loop_process_body_block', '_loop_handle_back_edge',
          '_generate_basic_region']:
    if hasattr(RegionASTGenerator, m):
        wrap(RegionASTGenerator, m)

wrap(RegionASTGenerator, '_generate_block_statements', show_ret=True)

cfg = build_cfg(target)
gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
print("=== DONE ===")
