"""Temporary experiment 3: leading-NOP split + trace header consumption."""
import sys, marshal
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")

from core.cfg import build_cfg
from core.cfg.basic_block import BasicBlock
from core.cfg.dominator_analyzer import PLACEHOLDER_OPS


def split_leading_nop(cfg):
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
            b1 = BasicBlock(start_offset=ins[0].offset)
            b1.instructions = [ins[0]]
            b1.is_jump_target = True
            b2 = BasicBlock(start_offset=ins[1].offset)
            b2.instructions = list(ins[1:])
            b2.is_jump_target = bool(getattr(ins[1], 'is_jump_target', False))
            b1.predecessors = {p for p in b.predecessors if p is not b}
            b1.successors = {b2}
            b2.predecessors = {b1}
            last = ins[-1]
            b2.successors = set()
            if last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                               'JUMP_FORWARD', 'JUMP_ABSOLUTE') and last.argval is not None:
                tgt = cfg.blocks.get(last.argval)
                b2.successors = {tgt if tgt is not None and tgt is not b else b1}
            else:
                nxt = cfg.blocks.get(ins[-1].offset + 2)
                b2.successors = {nxt} if nxt is not None and nxt is not b else set()
            for p in b1.predecessors:
                p.successors.discard(b)
                p.successors.add(b1)
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


f = open(r"F:\Downloads\pythoncdc-main\test_repros\round2\x01_if_deep_hosts.pyc", 'rb'); f.read(16)
module_code = marshal.load(f)
target = [c for c in module_code.co_consts if hasattr(c, 'co_name') and c.co_name == 'if_in_while'][0]
cfg = build_cfg(target)
split_leading_nop(cfg)

from core.cfg.region_ast_generator import RegionASTGenerator

def wrap(cls, name, show_ret=False):
    orig = getattr(cls, name)
    def patched(self, *a, **k):
        tags = []
        for x in a:
            if hasattr(x, 'start_offset'):
                tags.append('blk@%d' % x.start_offset)
        r = orig(self, *a, **k)
        print(('RET' if show_ret else 'CALL'), name, tags, (repr(r)[:150] if show_ret else ''))
        return r
    setattr(cls, name, patched)

for m in ['_loop_handle_header', '_loop_handle_header_no_condition',
          '_generate_block_statements', '_loop_process_header_instructions',
          '_loop_process_body_block', '_loop_handle_back_edge',
          '_loop_process_natural_back_edge', '_generate_loop', '_loop_generate_body']:
    if hasattr(RegionASTGenerator, m):
        wrap(RegionASTGenerator, m, show_ret=(m == '_generate_block_statements'))

gen = RegionASTGenerator(cfg, top_level_code=None)
gen.generate()
