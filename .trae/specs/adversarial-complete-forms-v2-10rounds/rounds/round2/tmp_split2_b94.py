"""Temporary experiment v2: split trailing back-edge jump out of NOP-leading loop header blocks."""
import sys, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

PYC = sys.argv[1] if len(sys.argv) > 1 else r"F:\Downloads\pythoncdc-main\test_repros\round2\x01_if_deep_hosts.pyc"
FUNC = sys.argv[2] if len(sys.argv) > 2 else 'if_in_while'
f = open(PYC, 'rb'); f.read(16)
module_code = marshal.load(f)

from core.cfg import build_cfg
from core.cfg.basic_block import BasicBlock
from core.cfg.region_analyzer import BACKWARD_JUMP_OPS, NOISE_OPS

BACK_UNCOND = ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')

def split_backedge_of_nop_header(cfg):
    """For each block B where:
       - instructions[0] is a jump-target NOP (placeholder),
       - real (non-noise, non-placeholder) instructions exist after it,
       - last instruction is an unconditional backward jump targeting B.start_offset,
       split the trailing backward jump into its own block."""
    changed = True
    while changed:
        changed = False
        for off in sorted(cfg.blocks):
            b = cfg.blocks[off]
            ins = b.instructions
            if len(ins) < 3:
                continue
            first = ins[0]
            if first.opname != 'NOP' or not getattr(first, 'is_jump_target', False):
                continue
            real_after = [i for i in ins[1:] if i.opname not in NOISE_OPS]
            if not real_after:
                continue
            last = ins[-1]
            if last.opname not in BACK_UNCOND:
                continue
            if last.argval != b.start_offset:
                continue
            # split: b keeps ins[:-1], new block gets the backward jump
            bj = BasicBlock(start_offset=last.offset)
            bj.instructions = [last]
            b.instructions = ins[:-1]
            b.end_offset = ins[-2].offset
            bj.end_offset = last.offset
            # edges: b --fallthrough--> bj --jump--> b
            b.successors.discard(b)
            b.predecessors.discard(b)
            b.successors.add(bj)
            bj.successors.add(b)
            bj.predecessors.add(b)
            b.predecessors.add(bj)
            cfg.blocks[last.offset] = bj
            # external blocks that jumped to b keep jumping to b (start unchanged)
            changed = True
            break

if FUNC == '<module>':
    target = module_code
else:
    target = [c for c in module_code.co_consts if hasattr(c, 'co_name') and c.co_name == FUNC][0]

cfg = build_cfg(target)
split_backedge_of_nop_header(cfg)
print("=== BLOCKS AFTER SPLIT ===")
for off in sorted(cfg.blocks):
    b = cfg.blocks[off]
    print(f"B{off}: ops={[(i.offset, i.opname) for i in b.instructions]} "
          f"succ={sorted(s.start_offset for s in b.successors)} "
          f"pred={sorted(p.start_offset for p in b.predecessors)}")

from core.cfg.region_ast_generator import RegionASTGenerator
from core.cfg.ast_converter import CFGASTConverter
from core.cfg.code_generator import CFGCodeGenerator

gen = RegionASTGenerator(cfg, top_level_code=None)
ast_dict = gen.generate()
py_ast = CFGASTConverter().convert(ast_dict)
source = CFGCodeGenerator().generate(py_ast)
print("=== OUTPUT ===")
print(source)
