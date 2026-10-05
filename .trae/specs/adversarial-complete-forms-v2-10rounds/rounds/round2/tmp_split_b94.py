"""Temporary experiment: split leading jump-target NOP out of loop header block, run pipeline."""
import sys, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

PYC = r"F:\Downloads\pythoncdc-main\test_repros\round2\x01_if_deep_hosts.pyc"
FUNC = sys.argv[1] if len(sys.argv) > 1 else 'if_in_while'
f = open(PYC, 'rb'); f.read(16)
module_code = marshal.load(f)
target = [c for c in module_code.co_consts if hasattr(c, 'co_name') and c.co_name == FUNC][0]

from core.cfg import build_cfg
from core.cfg.basic_block import BasicBlock

cfg = build_cfg(target)

# --- split experiment: for each block, if first instr is jump-target NOP and block has
#     real instrs after, split into [NOP] + [rest]
from core.cfg.dominator_analyzer import PLACEHOLDER_OPS

def split_blocks(cfg):
    changed = True
    while changed:
        changed = False
        for off in sorted(cfg.blocks):
            b = cfg.blocks[off]
            ins = b.instructions
            if len(ins) < 2:
                continue
            if ins[0].opname not in PLACEHOLDER_OPS:
                continue
            if not ins[0].is_jump_target:
                continue
            rest_ops = [i.opname for i in ins[1:] if i.opname not in PLACEHOLDER_OPS]
            if not rest_ops:
                continue
            # split at index 1
            b1 = BasicBlock(start_offset=ins[0].offset)
            b1.instructions = [ins[0]]
            b1.is_jump_target = True
            b2 = BasicBlock(start_offset=ins[1].offset)
            b2.instructions = list(ins[1:])
            b2.is_jump_target = bool(getattr(ins[1], 'is_jump_target', False))
            # predecessors of b now flow into b1
            b1.predecessors = {p for p in b.predecessors if p is not b}
            b1.successors = {b2}
            b2.predecessors = {b1}
            # recompute b2 successors from its last instruction's jump target
            last = ins[-1]
            b2.successors = set()
            if last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                               'JUMP_FORWARD', 'JUMP_ABSOLUTE') and last.argval is not None:
                tgt = cfg.blocks.get(last.argval)
                if tgt is not None and tgt is not b:
                    b2.successors = {tgt}
                else:
                    b2.successors = {b1}  # self-loop back to the split head
            else:
                # fallthrough to next block by offset
                nxt = cfg.blocks.get(ins[-1].offset + 2)
                if nxt is not None and nxt is not b:
                    b2.successors = {nxt}
            # remap external refs: any predecessor p of b (other than b itself)
            for p in b1.predecessors:
                p.successors.discard(b)
                p.successors.add(b1)
            # any block whose successor set contains b (e.g., jump targets) -> b1
            for ob in list(cfg.blocks.values()):
                if ob is b:
                    continue
                if b in ob.successors:
                    ob.successors.discard(b)
                    ob.successors.add(b1)
            del cfg.blocks[off]
            cfg.blocks[b1.start_offset] = b1
            cfg.blocks[b2.start_offset] = b2
            changed = True
            break

split_blocks(cfg)
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
converter = CFGASTConverter()
py_ast = converter.convert(ast_dict)
source = CFGCodeGenerator().generate(py_ast)
print("=== OUTPUT ===")
print(source)
