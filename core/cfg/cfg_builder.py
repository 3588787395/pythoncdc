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
        # [R4-G 修复] 连接完成后、出口块识别之前做短路归并点切分：
        # 需要 predecessors/successors 已建立以便重连，且切分可能改变
        # is_exit 归属，故必须在 _identify_exit_blocks 之前。
        self._split_blocks_at_short_circuit_merges()
        self._identify_exit_blocks()

        return self.cfg

    def _parse_instructions(self) -> None:
        self.instructions = []
        try:
            for instr in dis.get_instructions(self.code_obj):
                # KW_NAMES 的 arg 是 co_consts 索引，dis 不会自动
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
        """
        识别跳转目标，确定基本块边界。

        1. 算法依据：每块唯一归属 — 块边界仅由跳转目标 + 跳转/return/raise 之后
           位置确定；NOP 不是块边界（CPython 3.11+ 在 decorator 与 MAKE_FUNCTION
           之间插入 NOP 仅用于行对齐，非跳转目标）。
        2. 归约顺序：CFG 构建阶段（最早期），在 _build_basic_blocks 之前完成。
        3. 唯一归属判定：每个指令偏移只能属于一个基本块；块边界由
           is_jump_target + JUMP 指令目标 + BRANCH 下一指令偏移共同确定。
        4. 嵌套处理：N/A（CFG 层级，无嵌套结构）。
        5. 入口引用语义：N/A（CFG 层级，无 region 引用）。
        6. 反编译流程：枚举指令 → 收集跳转目标集合 → 后续 _build_basic_blocks
           据此切分基本块；NOP 不作为块边界，避免将
           `LOAD_NAME decorator + LOAD_CONST defaults + MAKE_FUNCTION + CALL`
           原子序列在 NOP 处切断（导致 decorator 丢失 / defaults 元组作为
           装饰器 `@((...))` 泄漏）。
        """
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
            # NOP 块边界状态仅由 instr.is_jump_target 决定（见上方分支）。
            # 不再无条件将 NOP 视为块边界：CPython 3.11+ 在 decorator 与
            # MAKE_FUNCTION 之间插入 NOP 用于行对齐，并非跳转目标；若将其
            # 视为块边界会切断 `LOAD_NAME decorator + LOAD_CONST defaults +
            # MAKE_FUNCTION + CALL` 原子序列，导致 decorator 丢失 /
            # defaults 元组被错误发射为 `@((...))` 装饰器（repro_13）。

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
                # RETURN_GENERATOR 是生成器/异步函数的 setup 指令，
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
                    # RETURN_GENERATOR 不是真正的 return，是生成器
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

    # ==================================================================
    # [R4-G 修复] 短路归并点块切分（区域归约算法前置归一化）
    # ==================================================================
    # 识别条件（纯结构判据，无函数名/文件名/常量特判）：
    #   设基本块 B 以短路跳转 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP
    #   跳向块 T。无论从哪条边进入 T，栈顶恰好承载「短路归并值」这一个
    #   逻辑值。沿 T 的指令前向累积栈效应（push-pop），首个使累积量转负的
    #   指令 C 即消费该归并值的指令。若 C 属于值消费指令
    #   （STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF/STORE_ATTR/
    #   STORE_SUBSCR/POP_TOP/RETURN_*/YIELD_VALUE）且 C 之后 T 内仍有指令，
    #   则 T 在同一块内跨越了语句边界。
    # 归约方式：
    #   在 C 之后（即 C 的下一条指令偏移）切分 T：T 只保留到 C，新块 S 承载
    #   其余指令并继承 T 的全部后继。切分后 BoolOpRegion 的 merge_block 恰
    #   好止于归并值消费点，「每块唯一归属」原则（区域归约原则 2）得以恢复：
    #   归并点之后的语句与其后的 IfRegion 各自独占新的入口块，不再被
    #   BoolOpRegion 连带吞并。
    # 若不切分（修复前）：
    #   `op = self.a() or self.b(); user = g(); if user is None: ...`
    #   中归并块 T 同时含 STORE_FAST op / STORE_FAST user / if 条件，
    #   BoolOpRegion 把整块纳入 region.blocks 并在生成时标记整块已生成，
    #   随后以 T 为入口的 IfRegion 被静默跳过，语句整体丢失——反编译输出
    #   只到 `op = ... or ...` 为止（或塌成 pass）。
    # AST 映射：
    #   `x = a or b` 恒映射为 ast.Assign(value=ast.BoolOp)，其余语句映射为
    #   紧随其后的同级语句；两者的归属由「归并值消费点」唯一确定。
    _R4G_SHORT_CIRCUIT_JUMPS = frozenset({
        'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
    })
    _R4G_VALUE_CONSUMERS = frozenset({
        'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
        'STORE_ATTR', 'STORE_SUBSCR', 'POP_TOP',
        'RETURN_VALUE', 'RETURN_CONST', 'YIELD_VALUE',
    })

    def _r4g_stack_delta(self, instr) -> Tuple[int, int]:
        """[R4-G] 归并值消费点定位专用栈效应，返回 (push, pop)。

        覆盖面刻意收窄到「短路归并点之后可能出现的指令」，未列出的指令
        返回 (0, 0)。与 region_analyzer._stack_effect 的关键差别：
        POP_TOP 记为 (0, 1)——本 pass 正是要用「累积栈深首次转负」定位
        归并值的消费指令。
        """
        op = instr.opname
        arg = instr.arg or 0
        if op == 'SWAP':
            return 0, 0
        if op in ('NOP', 'CACHE', 'EXTENDED_ARG', 'RESUME', 'PRECALL'):
            return 0, 0
        if op == 'POP_TOP':
            return 0, 1
        if op == 'COPY':
            return 1, 0
        if op in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
            return 0, 1
        if op == 'STORE_ATTR':
            return 0, 2
        if op == 'STORE_SUBSCR':
            return 0, 3
        if op in ('RETURN_VALUE', 'YIELD_VALUE'):
            return 0, 1
        if op == 'RETURN_CONST':
            return 0, 0
        if op == 'LOAD_ATTR':
            return 1, 1
        if op == 'LOAD_METHOD':
            return 2, 1
        if op.startswith('LOAD_'):
            return 1, 0
        if op == 'BINARY_SUBSCR':
            return 1, 2
        if op in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'BINARY_OP'):
            return 1, 2
        if op.startswith('UNARY_'):
            return 1, 1
        if op == 'BUILD_STRING':
            return 1, arg
        if op == 'BUILD_MAP':
            return 1, 2 * arg
        if op.startswith('BUILD_'):
            return 1, arg
        if op == 'CALL':
            return 1, arg + 2
        if op == 'FORMAT_VALUE':
            return 1, 1 if arg < 2 else 2
        if op in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                  'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                  'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                  'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
                  'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
            return 0, 1
        return 0, 0

    def _r4g_split_merge_target(self, target: BasicBlock) -> None:
        """[R4-G] 在归并值消费点之后切分短路归并目标块。"""
        instrs = [i for i in target.instructions
                  if i.opname not in ('CACHE', 'EXTENDED_ARG')]
        if len(instrs) < 2:
            return
        depth = 0
        consume_idx = None
        for k, instr in enumerate(instrs):
            push, pop = self._r4g_stack_delta(instr)
            depth += push - pop
            if depth < 0:
                consume_idx = k
                break
        if consume_idx is None:
            return
        consumer = instrs[consume_idx]
        if consumer.opname not in self._R4G_VALUE_CONSUMERS:
            return
        if consume_idx + 1 >= len(instrs):
            return
        # [R4-G 修复·语句边界必要性守卫] 仅当消费点之后**确实还有新语句**
        # 时才切分。若余下部分只是外层 if/while 的条件（取值 + 条件跳转，
        # 无任何语句级指令），则该块形态是「赋值 + 条件」，由既有 IfRegion
        # 机制按「前序语句 + 条件」正确处理，切分反而把 BoolOpRegion 的
        # merge 块与 IfRegion 的 condition_block 拆开（实测
        # arg_checker._is_valid_quarter：`valid = isinstance(value, ...) and
        # value[-2] == 'q'` 紧跟 `if valid:`，切分后生成多余 `else` 并使
        # 匹配函数数下降）。语句级指令判据（纯结构）：STORE_*/DELETE_*，
        # 或 CALL 后紧跟 POP_TOP（表达式语句），或 RETURN_*/RAISE_VARARGS。
        _tail = instrs[consume_idx + 1:]
        _has_stmt = False
        for _k, _ti in enumerate(_tail):
            _n = _ti.opname
            if _n in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                      'STORE_ATTR', 'STORE_SUBSCR') or _n.startswith('DELETE_'):
                _has_stmt = True
                break
            if _n in ('RETURN_VALUE', 'RETURN_CONST', 'YIELD_VALUE', 'RAISE_VARARGS'):
                _has_stmt = True
                break
            if _n == 'POP_TOP' and _k > 0 and _tail[_k - 1].opname == 'CALL':
                _has_stmt = True
                break
        if not _has_stmt:
            return
        split_offset = instrs[consume_idx + 1].offset
        if split_offset <= target.start_offset:
            return
        # [R4-G 修复·异常保护区间守卫] 若切分点落在异常表任一保护区间
        # [start, end) 内，则禁止切分：该块是 try 体的首块/内部块，
        # 切分会把它从 try 体中割裂出去，使 TryExceptRegion 的块跨度被
        # 破坏（实测 arg_checker._is_valid_frequency / _is_valid_quarter：
        # 在 try 体首块 80 切分后，内层 if 的 else 体被错挂到 try 上，
        # 生成多余 `else:` 与 2 条指令）。异常保护区间是结构性边界，
        # 短路归并切分不得跨越或落在其中。
        for _entry in (self.cfg.exception_table or []):
            _s = _entry.get('start')
            _e = _entry.get('end')
            if _s is None or _e is None:
                continue
            if _s <= split_offset < _e:
                return
        self._split_block_at_offset(split_offset)

    def _split_blocks_at_short_circuit_merges(self) -> None:
        """[R4-G 修复] 对所有短路归并目标块执行消费点切分（见上方说明）。"""
        if self.cfg is None:
            return
        targets: List[BasicBlock] = []
        seen_ids = set()
        for block in list(self.cfg.blocks.values()):
            last = block.get_last_instruction()
            if last is None or last.opname not in self._R4G_SHORT_CIRCUIT_JUMPS:
                continue
            if not isinstance(last.argval, int):
                continue
            target = self.cfg.get_block_by_offset(last.argval)
            if target is None or id(target) in seen_ids:
                continue
            seen_ids.add(id(target))
            targets.append(target)
        # 由后往前切分：切分只新增更靠后的块，不影响尚未处理的更早目标块。
        for target in sorted(targets, key=lambda b: b.start_offset, reverse=True):
            self._r4g_split_merge_target(target)

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
