"""
CFG构建器模块 - 从Python字节码构建控制流图
"""

import dis
import sys
import types
from typing import List, Dict, Set, Optional, Tuple, Any, Iterator
from collections import defaultdict

from .basic_block import BasicBlock, Instruction


class ControlFlowGraph:

    def __init__(self, name: str = "<unknown>"):
        self.name = name
        self.blocks: Dict[int, BasicBlock] = {}
        self.entry_block: Optional[BasicBlock] = None
        self.exit_blocks: Set[BasicBlock] = set()
        self.offset_to_block: Dict[int, BasicBlock] = {}
        self.exception_table: List[Dict[str, Any]] = []
        self.line_number_table: Dict[int, int] = {}
        self.annotations: Dict[str, Any] = {}

    def add_block(self, block: BasicBlock) -> None:
        self.blocks[block.id] = block
        self.offset_to_block[block.start_offset] = block

    def get_block_by_offset(self, offset: int) -> Optional[BasicBlock]:
        if offset in self.offset_to_block:
            return self.offset_to_block[offset]
        for block in self.blocks.values():
            if block.start_offset <= offset <= block.end_offset:
                return block
        return None

    def set_entry_block(self, block: BasicBlock) -> None:
        self.entry_block = block
        block.is_entry = True

    def add_exit_block(self, block: BasicBlock) -> None:
        self.exit_blocks.add(block)
        block.is_exit = True

    def get_blocks_in_order(self) -> List[BasicBlock]:
        return sorted(self.blocks.values(), key=lambda b: b.start_offset)

    def __iter__(self) -> Iterator[BasicBlock]:
        return iter(self.get_blocks_in_order())

    def __len__(self) -> int:
        return len(self.blocks)

    def __repr__(self):
        return f"ControlFlowGraph({self.name}, {len(self.blocks)} blocks)"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'block_count': len(self.blocks),
            'entry_block_id': self.entry_block.id if self.entry_block else None,
            'exit_block_ids': [b.id for b in self.exit_blocks],
            'blocks': [b.to_dict() for b in self.get_blocks_in_order()],
        }


class CFGBuilder:

    JUMP_INSTRUCTIONS = {
        'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD',
        'JUMP_BACKWARD_NO_INTERRUPT',
        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
        'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
        'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
        'FOR_ITER', 'FOR_ITER_RANGE', 'FOR_ITER_LIST', 'FOR_ITER_TUPLE',
        'FOR_ITER_GEN', 'FOR_ITER_DICT',
        'SETUP_FINALLY', 'SETUP_EXCEPT',
    }

    BRANCH_INSTRUCTIONS = {
        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
        'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
        'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
        'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
        'FOR_ITER', 'FOR_ITER_RANGE', 'FOR_ITER_LIST', 'FOR_ITER_TUPLE',
        'FOR_ITER_GEN', 'FOR_ITER_DICT',
    }

    RETURN_INSTRUCTIONS = {
        'RETURN_VALUE', 'RETURN_CONST', 'RETURN_GENERATOR',
    }

    RAISE_INSTRUCTIONS = {
        'RAISE_VARARGS', 'RERAISE', 'RAISE',
    }

    RESUME_INSTRUCTIONS = {
        'RESUME', 'CACHE', 'PUSH_NULL',
    }

    def __init__(self):
        self.cfg: Optional[ControlFlowGraph] = None
        self.code_obj: Optional[types.CodeType] = None
        self.instructions: List[Instruction] = []
        self.jump_targets: Set[int] = set()

    def build(self, code_obj: types.CodeType, name: Optional[str] = None) -> ControlFlowGraph:
        BasicBlock.reset_id_counter()
        self.code_obj = code_obj
        self.cfg = ControlFlowGraph(name or code_obj.co_name)
        self.cfg.code = code_obj

        self._parse_instructions()
        self._identify_jump_targets()
        self._build_basic_blocks()
        self._parse_exception_table()
        self._split_blocks_at_exception_boundaries()
        self._connect_blocks()
        self._identify_exit_blocks()

        return self.cfg

    def _parse_instructions(self) -> None:
        self.instructions = []
        try:
            for instr in dis.get_instructions(self.code_obj):
                # [R12-batch1] KW_NAMES 的 arg 是 co_consts 索引，dis 不会自动
                # 解析 argval（返回 <unknown>）。这里手动解析为关键字参数名元组，
                # 使所有下游消费者（栈模拟、ast_generator_v2 等）都能直接使用 argval。
                # 否则 `f(x=ternary) > 0` 等场景的关键字参数会被错误地当作位置参数。
                _argval = instr.argval
                if (instr.opname == 'KW_NAMES' and instr.arg is not None
                        and not isinstance(_argval, tuple)):
                    try:
                        _resolved = self.code_obj.co_consts[instr.arg]
                        if isinstance(_resolved, tuple):
                            _argval = _resolved
                    except (IndexError, TypeError):
                        pass
                instruction = Instruction(
                    offset=instr.offset,
                    opcode=instr.opcode,
                    opname=instr.opname,
                    arg=instr.arg,
                    argval=_argval,
                    starts_line=instr.starts_line,
                    is_jump_target=instr.is_jump_target,
                )
                self.instructions.append(instruction)
                if instr.starts_line:
                    self.cfg.line_number_table[instr.offset] = instr.starts_line
        except Exception as e:
            print(f"Warning: Error parsing instructions: {e}")

    def _identify_jump_targets(self) -> None:
        self.jump_targets = set()
        for i, instr in enumerate(self.instructions):
            if instr.is_jump_target:
                self.jump_targets.add(instr.offset)
            if instr.opname in self.JUMP_INSTRUCTIONS and instr.argval is not None:
                if isinstance(instr.argval, int):
                    self.jump_targets.add(instr.argval)
                    if instr.opname in self.BRANCH_INSTRUCTIONS and i + 1 < len(self.instructions):
                        next_offset = self.instructions[i + 1].offset
                        self.jump_targets.add(next_offset)
            if instr.opname == 'NOP' and i > 0:
                self.jump_targets.add(instr.offset)

    def _build_basic_blocks(self) -> None:
        if not self.instructions:
            return

        entry_offset = self.instructions[0].offset
        for i, instr in enumerate(self.instructions):
            if instr.opname == 'RESUME':
                entry_offset = instr.offset
                break

        current_block = BasicBlock(self.instructions[0].offset)
        self.cfg.add_block(current_block)
        self.cfg.set_entry_block(current_block)

        for i, instr in enumerate(self.instructions):
            is_leader = (
                instr.offset in self.jump_targets or
                (i > 0 and self.instructions[i-1].opname in self.JUMP_INSTRUCTIONS) or
                (i > 0 and self.instructions[i-1].opname in self.RETURN_INSTRUCTIONS) or
                (i > 0 and self.instructions[i-1].opname in self.RAISE_INSTRUCTIONS)
            )
            if i > 0 and self.instructions[i-1].opname in self.BRANCH_INSTRUCTIONS:
                is_leader = True
            if i > 0 and self.instructions[i-1].opname == 'RETURN_GENERATOR':
                is_leader = True

            if is_leader and i > 0:
                current_block = BasicBlock(instr.offset)
                self.cfg.add_block(current_block)
            current_block.add_instruction(instr)

        if entry_offset != self.instructions[0].offset:
            for block in self.cfg.blocks.values():
                if block.start_offset <= entry_offset <= block.end_offset:
                    self.cfg.set_entry_block(block)
                    break

    def _connect_blocks(self) -> None:
        blocks = self.cfg.get_blocks_in_order()
        block_map = {b.start_offset: b for b in blocks}

        for i, block in enumerate(blocks):
            if not block.instructions:
                continue
            last_instr = block.get_last_instruction()
            if last_instr is None:
                continue

            if last_instr.opname in self.JUMP_INSTRUCTIONS:
                if isinstance(last_instr.argval, int):
                    target_offset = last_instr.argval
                    if target_offset in block_map:
                        block.add_successor(block_map[target_offset])
                if last_instr.opname not in {'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD'}:
                    if i + 1 < len(blocks):
                        block.add_successor(blocks[i + 1])
            elif last_instr.opname == 'RETURN_GENERATOR':
                # [R9 聚类A] RETURN_GENERATOR 是生成器/异步函数的 setup 指令，
                # 语义上 fall-through 到下一条指令（在后续 resume 时执行）。
                # 若不连接后继，block 0 成为孤立块且被 _identify_exit_blocks
                # 标记为 is_exit，破坏 post-dominator 分析（virtual_exit 误连），
                # 导致嵌套 ternary 的 merge_block 无法被识别（merge=None）。
                # 依「每块唯一归属」：RETURN_GENERATOR 块归属函数入口序言，
                # 由 entry_block 引用下一条指令作为后继。
                if i + 1 < len(blocks):
                    block.add_successor(blocks[i + 1])
            elif last_instr.opname in self.RETURN_INSTRUCTIONS:
                pass
            elif last_instr.opname in self.RAISE_INSTRUCTIONS:
                pass
            else:
                if i + 1 < len(blocks):
                    block.add_successor(blocks[i + 1])

        self._connect_exception_edges(block_map)

    def _connect_exception_edges(self, block_map: Dict[int, BasicBlock]) -> None:
        if not self.cfg.exception_table:
            return

        offset_to_block = {}
        for offset, block in block_map.items():
            for i in range(offset, block.end_offset + 1):
                offset_to_block[i] = block

        for entry in self.cfg.exception_table:
            start_offset = entry['start']
            end_offset = entry['end']
            target_offset = entry['target']

            for off in range(start_offset, end_offset):
                try_block = offset_to_block.get(off)
                handler_block = offset_to_block.get(target_offset)

                if try_block and handler_block:
                    if handler_block not in try_block.successors:
                        try_block.add_successor(handler_block)
                    try_block.exception_successors.add(handler_block)
                    handler_block.is_exception_handler = True

    def _identify_exit_blocks(self) -> None:
        for block in self.cfg.blocks.values():
            if not block.successors:
                if block.instructions:
                    last_instr = block.get_last_instruction()
                    # [R9 聚类A] RETURN_GENERATOR 不是真正的 return，是生成器
                    # setup。在 _connect_blocks 中已 fall-through 到下一条指令，
                    # 因此该块必然有后继，不会进入此分支。此处仅作为安全兜底：
                    # 若某 RETURN_GENERATOR 块确实无后继（异常 CFG），不标记为
                    # exit，避免破坏 post-dominator 分析。
                    if (last_instr and last_instr.opname in self.RETURN_INSTRUCTIONS
                            and last_instr.opname != 'RETURN_GENERATOR'):
                        self.cfg.add_exit_block(block)

    def _split_blocks_at_exception_boundaries(self) -> None:
        if not self.cfg.exception_table:
            return

        split_offsets = set()
        for entry in self.cfg.exception_table:
            split_offsets.add(entry['start'])
            split_offsets.add(entry['end'])
            split_offsets.add(entry['target'])

        for offset in sorted(split_offsets):
            self._split_block_at_offset(offset)

    def _split_block_at_offset(self, offset: int) -> None:
        block_to_split = None
        for block in list(self.cfg.blocks.values()):
            if block.start_offset < offset <= block.end_offset:
                block_to_split = block
                break

        if block_to_split is None:
            return

        split_idx = None
        for i, instr in enumerate(block_to_split.instructions):
            if instr.offset == offset:
                split_idx = i
                break

        if split_idx is None or split_idx == 0:
            return

        before_instrs = block_to_split.instructions[:split_idx]
        after_instrs = block_to_split.instructions[split_idx:]

        if not before_instrs or not after_instrs:
            return

        block_to_split.instructions = before_instrs
        block_to_split.end_offset = before_instrs[-1].offset

        new_block = BasicBlock(offset)
        for instr in after_instrs:
            new_block.add_instruction(instr)

        new_block.predecessors = {block_to_split}
        new_block.successors = set(block_to_split.successors)

        for succ in block_to_split.successors:
            succ.predecessors.discard(block_to_split)
            succ.predecessors.add(new_block)

        block_to_split.successors = {new_block}

        for attr in ('dominators', 'post_dominators', 'dominated_blocks'):
            setattr(new_block, attr, set())

        new_block.immediate_dominator = None
        new_block.immediate_post_dominator = None
        new_block.loop_header = block_to_split.loop_header
        new_block.loop_depth = block_to_split.loop_depth
        new_block.is_exit = block_to_split.is_exit
        new_block.exception_handler = False

        if block_to_split.is_exit:
            block_to_split.is_exit = False
            if block_to_split in self.cfg.exit_blocks:
                self.cfg.exit_blocks.discard(block_to_split)

        self.cfg.add_block(new_block)

    def _parse_exception_table(self) -> None:
        if hasattr(self.code_obj, 'co_exceptiontable'):
            try:
                import dis
                if hasattr(dis, '_parse_exception_table'):
                    entries = list(dis._parse_exception_table(self.code_obj))
                    for entry in entries:
                        self.cfg.exception_table.append({
                            'start': entry.start,
                            'end': entry.end,
                            'target': entry.target,
                            'depth': entry.depth,
                            'lasti': entry.lasti,
                        })
            except Exception as e:
                pass

    def get_cfg(self) -> Optional[ControlFlowGraph]:
        return self.cfg


def build_cfg(code_obj: types.CodeType, name: Optional[str] = None) -> ControlFlowGraph:
    builder = CFGBuilder()
    cfg = builder.build(code_obj, name)
    cfg.code = code_obj
    return cfg


def build_cfg_from_source(source: str, name: str = "<module>") -> Optional[ControlFlowGraph]:
    try:
        code_obj = compile(source, name, 'exec')
        return build_cfg(code_obj, name)
    except SyntaxError:
        return None


def build_cfg_from_function(func: types.FunctionType) -> ControlFlowGraph:
    return build_cfg(func.__code__, func.__name__)


class CFGPrinter:

    @staticmethod
    def print_cfg(cfg: ControlFlowGraph, show_instructions: bool = True) -> None:
        print(f"\n{'='*60}")
        print(f"Control Flow Graph: {cfg.name}")
        print(f"{'='*60}")
        print(f"Total blocks: {len(cfg.blocks)}")
        print(f"Entry block: {cfg.entry_block.id if cfg.entry_block else 'None'}")
        print(f"Exit blocks: {[b.id for b in cfg.exit_blocks]}")
        print(f"{'='*60}\n")

        for block in cfg.get_blocks_in_order():
            CFGPrinter.print_block(block, show_instructions)
            print()

    @staticmethod
    def print_block(block: BasicBlock, show_instructions: bool = True) -> None:
        print(str(block))

    @staticmethod
    def print_dot(cfg: ControlFlowGraph) -> str:
        lines = [f'digraph "{cfg.name}" {{']
        lines.append('    node [shape=box];')

        for block in cfg.get_blocks_in_order():
            label = f"Block {block.id}"
            if block.is_entry:
                label += "\\n[ENTRY]"
            if block.is_exit:
                label += "\\n[EXIT]"
            lines.append(f'    block{block.id} [label="{label}"];')

        for block in cfg.get_blocks_in_order():
            for succ in block.successors:
                lines.append(f'    block{block.id} -> block{succ.id};')

        lines.append('}')
        return '\n'.join(lines)
