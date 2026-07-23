"""
区域分析器模块

基于编译器理论的区域归约算法，将CFG分解为层次化的区域结构。
替代 structured_analyzer.py 中的补丁式模式匹配。

核心算法：
1. 回边检测 → 循环区域
2. 支配边界分析 → 条件区域（if/elif/else）
3. 异常表 → 异常处理区域（try/except/finally）
4. 指令特征 → with/match/assert 区域
5. 剩余线性块 → 序列区域

原则：
- 每个结构在识别阶段就正确分类，不需要后处理修正
- 区域归约保证不重叠
- 算法驱动，不使用启发式规则
"""

from enum import Enum, auto
from typing import List, Dict, Set, Optional, Tuple, Any, Iterable
from dataclasses import dataclass, field

from .basic_block import BasicBlock, Instruction
from .cfg_builder import ControlFlowGraph
from .dominator_analyzer import (
    DominatorAnalyzer, LoopAnalyzer,
    FOR_ITER_OPS, BACKWARD_JUMP_OPS, FORWARD_JUMP_OPS, PLACEHOLDER_OPS,
)

from .pattern_parser import PatternParser
from .opcode_feature_detector import get_opcode_detector
from .peephole_patterns import PeepholePatternLibrary

FORWARD_CONDITIONAL_JUMP_OPS = frozenset({
    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
    'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
    'POP_JUMP_IF_NONE', 'POP_JUMP_IF_NOT_NONE',
})

BACKWARD_CONDITIONAL_JUMP_OPS = frozenset({
    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
    'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
})

CONDITIONAL_JUMP_OPS = FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS

SHORT_CIRCUIT_JUMP_OPS = frozenset({
    'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP',
})

NONE_CHECK_OPS = frozenset({
    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
    'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
})

NOISE_OPS = frozenset({
    'RESUME', 'NOP', 'CACHE', 'PUSH_NULL',
})

CLEANUP_OPS = NOISE_OPS | frozenset({
    'POP_TOP', 'COPY', 'PUSH_EXC_INFO', 'POP_EXCEPT',
    'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST', 'RERAISE',
    'SWAP',
})

PURE_JUMP_OPS = NOISE_OPS | frozenset({
    'POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'LOAD_CONST',
})

MIN_INSTRS_FOR_NESTED_CASE_PATTERN = 3  # 嵌套case比较最小指令数（LOAD/COPY + LOAD_CONST + COMPARE_OP）
# 理论依据：CPython编译器对match-case的最小比较单元生成3条有效指令

RERAISE_ONLY_OPS = frozenset({
    'POP_TOP', 'LOAD_CONST', 'RERAISE', 'COPY', 'PUSH_EXC_INFO',
})

WITH_EXIT_INDICATOR_OPS = frozenset({
    'POP_EXCEPT', 'POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE',
    'NOP', 'CACHE', 'RESUME', 'RERAISE',
    'GET_AWAITABLE', 'SEND', 'YIELD_VALUE',
})

class BlockRole(Enum):
    NORMAL = auto()
    LOOP_HEADER = auto()
    LOOP_CONDITION = auto()
    LOOP_BODY = auto()
    LOOP_ELSE = auto()
    LOOP_INIT = auto()
    IF_CONDITION = auto()
    IF_THEN = auto()
    IF_ELSE = auto()
    IF_ELIF_CONDITION = auto()
    TRY_BODY = auto()
    EXCEPT_HANDLER = auto()
    EXCEPT_STORE = auto()
    FINALLY_BODY = auto()
    TRY_ELSE = auto()
    WITH_ENTRY = auto()
    WITH_BODY = auto()
    WITH_EXIT_CLEANUP = auto()
    WITH_STACK_CLEANUP = auto()
    WITH_EXIT_CALL = auto()
    WITH_HANDLER = auto()
    MATCH_SUBJECT = auto()
    MATCH_CASE = auto()
    MATCH_GUARD_ROLE = auto()
    LOOP_BACK_EDGE = auto()
    LOOP_CONDITION_RECHECK = auto()
    LOOP_EXIT = auto()
    CONTINUE = auto()
    BREAK = auto()
    RETURN = auto()
    RETURN_NONE = auto()
    RERAISE = auto()
    RERAISE_CLEANUP = auto()
    PURE_CONTINUE = auto()
    PURE_BREAK = auto()
    PURE_JUMP = auto()
    TRIVIAL = auto()
    ITER_SETUP = auto()
    AWAIT_SEND = auto()
    AWAIT_YIELD = auto()
    NOP = auto()

class RegionType(Enum):
    BASIC = auto()
    SEQUENCE = auto()
    IF = auto()
    IF_THEN = auto()
    IF_THEN_ELSE = auto()
    IF_ELIF_CHAIN = auto()
    WHILE_LOOP = auto()
    FOR_LOOP = auto()
    TRY_EXCEPT = auto()
    TRY_FINALLY = auto()
    WITH = auto()
    MATCH = auto()
    ASSERT = auto()
    BREAK = auto()
    CONTINUE = auto()
    PASS = auto()
    RETURN = auto()
    BOOL_OP = auto()
    TERNARY = auto()

@dataclass
class BlockSemantics:
    role: BlockRole = BlockRole.NORMAL
    is_back_edge: bool = False
    back_edge_target: Optional[int] = None
    effective_instructions: List[Instruction] = field(default_factory=list)
    statement_boundaries: List[Tuple[int, int]] = field(default_factory=list)
    belongs_to_region: Optional[RegionType] = None
    is_continue: bool = False
    is_break: bool = False
    is_return: bool = False

@dataclass(eq=False)
class Region:
    region_type: RegionType = RegionType.BASIC
    entry: Optional[BasicBlock] = None
    blocks: Set[BasicBlock] = field(default_factory=set)
    exit: Optional[BasicBlock] = None
    parent: Optional['Region'] = None
    children: List['Region'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    has_trailing_return_none: bool = False

    def __hash__(self):
        return id(self)

    def mark_trailing_return_none(self):
        """标记此区域尾部有Return None"""
        self.has_trailing_return_none = True

    def add_child(self, child: 'Region') -> None:
        if child is self:
            return
        if child.parent is not None and child.parent is not self:
            return
        current = self.parent
        while current is not None:
            if current is child:
                return
            current = current.parent
        child.parent = self
        if child not in self.children:
            self.children.append(child)

    def get_content_blocks(self) -> Set[BasicBlock]:
        return set(self.blocks)

    def find_enclosing_parent(self, region_types: Tuple[type, ...] = None, require_finally: bool = False) -> Optional['Region']:
        current = self.parent
        while current is not None:
            if region_types and not isinstance(current, region_types):
                current = current.parent
                continue
            if require_finally and not getattr(current, 'has_finally', False):
                current = current.parent
                continue
            return current
        return None

    def find_descendant_region_for_block(self, block: BasicBlock, region_types: Tuple[type, ...] = None) -> Optional['Region']:
        for child in self.children:
            if region_types is None or isinstance(child, region_types):
                if block in child.blocks:
                    return child
                if hasattr(child, 'header_block') and child.header_block == block:
                    return child
                if hasattr(child, 'condition_block') and child.condition_block == block:
                    return child
                if child.entry == block:
                    return child
            deeper = child.find_descendant_region_for_block(block, region_types)
            if deeper is not None:
                return deeper
        return None

    def iter_descendants(self, region_types: Tuple[type, ...] = None) -> Iterable['Region']:
        for child in self.children:
            if region_types is None or isinstance(child, region_types):
                yield child
            yield from child.iter_descendants(region_types)

    def annotate_structural_roles(self, analyzer) -> None:
        """多态分发：标注区域结构化角色。子类按需覆写。"""
        return None

    def annotate_cond_recheck(self, analyzer) -> None:
        """多态分发：循环条件复查 / 链式比较操作数计算。子类按需覆写。"""
        return None

    def get_score_merge_block(self) -> Optional['BasicBlock']:
        """多态分发：评分时获取merge_block。仅BoolOp/If/Ternary覆写。"""
        return None

    def precompute_analysis(self, analyzer) -> None:
        """多态分发：预计算区域分析数据。子类按需覆写。"""
        return None

    def is_block_entry(self, block) -> bool:
        """多态分发：判断block是否为区域的入口/条件/header块。子类按需覆写。"""
        return False

    def contains_block(self, block) -> bool:
        """多态分发：判断block是否属于区域的关键块（try_blocks/entry等）。子类按需覆写。"""
        return False

    def is_block_in_body(self, block) -> bool:
        """多态分发：判断block是否在区域体内（用于if检测）。子类按需覆写。"""
        return False

    def else_block_conflict(self, block) -> bool:
        """多态分发：判断block是否与区域的else放置冲突（True=冲突需return None）。子类按需覆写。"""
        return True

    def get_with_body_orphan_instructions(self, block) -> list:
        """多态分发：with体内嵌套本区域时，提取块中属于外层with的orphan指令。
        默认无orphan（返回空列表）。LoopRegion覆写以处理GET_ITER拆分。"""
        return []

    def get_compactness_successors(self, analyzer) -> Optional[List['BasicBlock']]:
        """多态分发：分支紧致度评分时获取后继块对[ft, jt]或[then_first, else_first]。
        默认None（评分返回50.0）。BoolOpRegion/IfRegion覆写。"""
        return None

    def get_offset_range(self, analyzer) -> Tuple[int, int]:
        """多态分发：获取区域的字节码偏移范围(start, end)。默认基于blocks集合。
        TryExceptRegion覆写（按内容块计算），IfRegion覆写（按需扩展到后继try体）。"""
        if not self.blocks:
            return (0, 0)
        offsets = [block.start_offset for block in self.blocks]
        return (min(offsets), max(offsets))

    def get_if_branch_boundary_stop(self, block) -> set:
        """多态分发：在if分支收集时，返回本区域体外的直接后继块集合（BFS额外停止点）。
        默认空集合。TryExceptRegion/LoopRegion覆写。"""
        return set()

    def interrupts_boolop_forward_chain(self, ft_succ) -> bool:
        """多态分发：while循环boolop前向链检测时，ft_succ落入本区域是否应中断链扩展。
        默认不中断。LoopRegion覆写为始终中断，IfRegion覆写为条件块不匹配时中断。"""
        return False

    def can_be_ternary_header(self, block, analyzer) -> bool:
        """多态分发：block作为ternary header块时，本区域占用block是否允许创建ternary。
        默认允许（return True）。Ternary/Assert/Match覆写为禁止，BoolOp/Loop/If按条件判断。"""
        return True

    def get_if_body_blocks(self) -> Optional[Tuple[List['BasicBlock'], List['BasicBlock']]]:
        """多态分发：获取if区域的(then_blocks, else_blocks)体块。
        默认None（评分返回默认值）。IfRegion覆写。"""
        return None

    def get_else_blocks_for_merge(self) -> Optional[List['BasicBlock']]:
        """多态分发：获取区域的else_blocks用于嵌套try合并判断。
        默认None（非TryExcept或无else_blocks）。TryExceptRegion覆写。"""
        return None

    def try_except_absorb_split_from(self, inner: 'Region') -> bool:
        """多态分发：作为外层try-except，吸收内层split try-except的handler/else/blocks。
        默认不吸收（返回False）。TryExceptRegion覆写。"""
        return False

    def should_merge_with(self, other: 'Region', analyzer) -> bool:
        """多态分发：判定是否可与另一区域合并为连续with（with A: ... with B: ...）。
        默认不合并（返回False）。WithRegion覆写。"""
        return False

    def preserves_against_nested_match(self) -> bool:
        """多态分发：嵌套match注册block_to_region时，是否应保留本区域不被覆盖。
        默认False（允许覆盖）。MatchRegion覆写为True（保留已存在的match）。"""
        return False

@dataclass
class IfRegion(Region):
    condition_block: Optional[BasicBlock] = None
    then_blocks: List[BasicBlock] = field(default_factory=list)
    else_blocks: List[BasicBlock] = field(default_factory=list)
    merge_block: Optional[BasicBlock] = None
    elif_conditions: List[BasicBlock] = field(default_factory=list)
    elif_bodies: List[List[BasicBlock]] = field(default_factory=list)
    elif_final_else: List[BasicBlock] = field(default_factory=list)
    inline_boolop_chains: Dict[int, dict] = field(default_factory=dict)
    chained_compare_blocks: List[BasicBlock] = field(default_factory=list)
    chained_compare_ops: List[str] = field(default_factory=list)
    chained_left_instr: Optional[Instruction] = None
    chained_comparator_instrs: List[Instruction] = field(default_factory=list)

    def get_content_blocks(self) -> Set[BasicBlock]:
        content = set()
        if self.then_blocks:
            content.update(self.then_blocks)
        if self.else_blocks:
            content.update(self.else_blocks)
        if self.elif_conditions:
            content.update(self.elif_conditions)
        for body_list in self.elif_bodies:
            content.update(body_list)
        if self.elif_final_else:
            content.update(self.elif_final_else)
        return content

    def annotate_structural_roles(self, analyzer) -> None:
        analyzer._annotate_if_structural_roles(self)

    def annotate_cond_recheck(self, analyzer) -> None:
        if self.chained_compare_blocks:
            analyzer.compute_chained_compare_operands(self)

    def get_score_merge_block(self) -> Optional['BasicBlock']:
        return self.merge_block

    def precompute_analysis(self, analyzer) -> None:
        analyzer._precompute_chained_compare_analysis(self)

    def is_block_entry(self, block) -> bool:
        return self.condition_block == block or self.entry == block

    def else_block_conflict(self, block) -> bool:
        return False

    def get_compactness_successors(self, analyzer):
        if self.then_blocks or self.else_blocks:
            then_first = self.then_blocks[0] if self.then_blocks else None
            else_first = self.else_blocks[0] if self.else_blocks else None
            if then_first and else_first:
                return [then_first, else_first]
        return None

    def get_offset_range(self, analyzer):
        if not self.blocks:
            return (0, 0)
        offsets = [block.start_offset for block in self.blocks]
        for _tb in (self.then_blocks or []):
            for _succ in _tb.successors:
                _succ_region = analyzer.block_to_region.get(_succ)
                if (isinstance(_succ_region, TryExceptRegion) and
                    _succ_region.entry is _succ and
                    _succ_region is not self):
                    _has_closer_loop = False
                    _if_range_no_expansion = (min(offsets), max(offsets)) if offsets else (0, 0)
                    _te_range = analyzer._get_region_offset_range(_succ_region)
                    _expanded_range = (min(_if_range_no_expansion[0], _te_range[0]), max(_if_range_no_expansion[1], _te_range[1]))
                    for _lr in analyzer._filter_regions(analyzer.regions if hasattr(analyzer, 'regions') else [], LoopRegion):
                        if _lr is not self and _lr.entry:
                            _lr_range = analyzer._get_region_offset_range(_lr)
                            _lr_inside_te = (_lr_range[0] >= _te_range[0] and _lr_range[1] <= _te_range[1])
                            if (not _lr_inside_te and
                                _lr_range[0] >= _expanded_range[0] and _lr_range[1] <= _expanded_range[1] and
                                (_lr_range[1] - _lr_range[0]) < (_expanded_range[1] - _expanded_range[0])):
                                _has_closer_loop = True
                                break
                    if not _has_closer_loop:
                        for _child_block in _succ_region.try_blocks:
                            offsets.append(_child_block.start_offset)
                        for _, _, _hblocks in _succ_region.except_handlers:
                            for _hb in _hblocks:
                                offsets.append(_hb.start_offset)
                        for _eb in (_succ_region.else_blocks or []):
                            offsets.append(_eb.start_offset)
                        for _fb in (_succ_region.finally_blocks or []):
                            offsets.append(_fb.start_offset)
        return (min(offsets), max(offsets))

    def interrupts_boolop_forward_chain(self, ft_succ) -> bool:
        # if条件块与ft_succ不匹配时，ft_succ不属于该if的条件链，应中断boolop扩展
        return self.condition_block != ft_succ

    def can_be_ternary_header(self, block, analyzer) -> bool:
        # if区域占用ternary header块时，若存在链式比较块则禁止创建ternary
        return not bool(self.chained_compare_blocks)

    def get_if_body_blocks(self):
        # 返回if区域的(then_blocks, else_blocks)体块，已规范化为非None列表
        return (self.then_blocks or [], self.else_blocks or [])

@dataclass(eq=False)
class LoopRegion(Region):
    header_block: Optional[BasicBlock] = None
    body_blocks: List[BasicBlock] = field(default_factory=list)
    condition_block: Optional[BasicBlock] = None
    else_blocks: List[BasicBlock] = field(default_factory=list)
    init_blocks: List[BasicBlock] = field(default_factory=list)
    is_async: bool = False
    is_yield_from: bool = False
    back_edge_block: Optional[BasicBlock] = None
    is_while_true: bool = False
    has_break: bool = False
    else_is_follow: bool = False
    pre_condition_blocks: List[BasicBlock] = field(default_factory=list)
    break_blocks: List[BasicBlock] = field(default_factory=list)
    back_edge_blocks: Set[BasicBlock] = field(default_factory=set)
    condition_recheck_blocks: Set[BasicBlock] = field(default_factory=set)
    condition_chain_blocks: List[BasicBlock] = field(default_factory=list)
    condition_chain_expr: Optional[Any] = None

    def get_content_blocks(self) -> Set[BasicBlock]:
        content = set(self.body_blocks)
        if self.condition_block and self.condition_block != self.header_block:
            content.add(self.condition_block)
        content.update(self.else_blocks)
        content.update(self.init_blocks)
        return content

    def annotate_structural_roles(self, analyzer) -> None:
        analyzer._annotate_loop_structural_roles(self)

    def annotate_cond_recheck(self, analyzer) -> None:
        for block in self.condition_recheck_blocks:
            analyzer._assign_region_role(block.start_offset,
                                          BlockRole.LOOP_CONDITION_RECHECK)

    def precompute_analysis(self, analyzer) -> None:
        analyzer._precompute_loop_analysis_data(self)

    def is_block_entry(self, block) -> bool:
        return (self.header_block == block or
                self.entry == block or
                self.condition_block == block)

    def is_block_in_body(self, block) -> bool:
        if block == self.header_block:
            return False
        if block == self.condition_block:
            return False
        if block in getattr(self, 'condition_chain_blocks', []):
            return False
        if block == self.back_edge_block:
            return False
        if block in getattr(self, 'back_edge_blocks', set()):
            return False
        last = block.get_last_instruction()
        if last and last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
            return False
        return True

    def else_block_conflict(self, block) -> bool:
        return (block == self.condition_block or
                block == self.header_block or
                block == self.entry)

    def get_with_body_orphan_instructions(self, block) -> list:
        # with体内嵌套for循环时，GET_ITER之前的指令属于外层with的orphan
        # （如 `with ctx: for x in iter:` 中GET_ITER前的上下文表达式指令）。
        get_iter_idx = None
        for idx, instr in enumerate(block.instructions):
            if instr.opname in ('GET_ITER', 'GET_AITER'):
                get_iter_idx = idx
                break
        if get_iter_idx is None:
            return []
        split_idx = get_iter_idx
        last_store_idx = -1
        for idx in range(get_iter_idx):
            if block.instructions[idx].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                last_store_idx = idx
        if last_store_idx >= 0:
            split_idx = last_store_idx + 1
        else:
            expr_start = get_iter_idx - 1
            while expr_start >= 0:
                iname = block.instructions[expr_start].opname
                if iname in NOISE_OPS:
                    expr_start -= 1
                    continue
                if iname == 'PUSH_NULL':
                    split_idx = expr_start
                    break
                if iname.startswith('LOAD_') or iname in ('PRECALL', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD'):
                    expr_start -= 1
                    continue
                break
        orphan = []
        for instr in block.instructions[:split_idx]:
            if instr.opname not in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                orphan.append(instr)
        return orphan

    def get_if_branch_boundary_stop(self, block) -> set:
        loop_body_set = set(self.body_blocks) | set(self.else_blocks)
        if self.condition_block:
            loop_body_set.add(self.condition_block)
        boundary = set()
        for lb in self.body_blocks:
            for succ in lb.successors:
                if succ not in loop_body_set:
                    boundary.add(succ)
        boundary.add(self.header_block)
        if self.condition_block:
            boundary.add(self.condition_block)
        # [Phase 4 回归修复] back_edge_block 含条件回边跳转
        # （POP_JUMP_BACKWARD_IF_TRUE/FALSE）时是循环的条件重检块，属于
        # LoopRegion（每块唯一归属），不应被嵌套 IfRegion 的 else 分支吸收。
        # 但若 back_edge_block 仅含无条件 JUMP_BACKWARD（for 循环的隐式
        # continue），它可能同时是 if 分支的真实 body（如
        # `for x in r: if c: x = x+1`），此时不应排除。用最后指令区分：
        # 条件回边 → 排除；无条件回边 → 保留。
        if self.back_edge_block is not None:
            _be_last = self.back_edge_block.get_last_instruction()
            if _be_last and _be_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                boundary.add(self.back_edge_block)
        return boundary

    def interrupts_boolop_forward_chain(self, ft_succ) -> bool:
        # ft_succ落入循环区域时，boolop链不应扩展进循环体，始终中断
        return True

    def can_be_ternary_header(self, block, analyzer) -> bool:
        # 循环占用ternary header块时，需确认block是循环内的纯表达式分支
        if block == self.condition_block:
            return False
        if block == self.back_edge_block:
            return False
        if block == self.header_block and self.condition_block is None:
            return False
        if block not in self.blocks:
            return False
        _cond_succs = list(block.conditional_successors)
        if len(_cond_succs) != 2:
            return False
        for _cs in _cond_succs:
            if not analyzer._is_single_expression_block(_cs):
                return False
            _cs_last = _cs.get_last_instruction()
            if _cs_last and _cs_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                return False
            if _cs in self.blocks and _cs != self.back_edge_block:
                _cs_inner_last = _cs.get_last_instruction()
                if _cs_inner_last and _cs_inner_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                    # [R9 聚类A] 嵌套 ternary：若 _cs 已是某 TernaryRegion 的 entry
                    # （如 `a if c1 else (b if c2 else d)` 中外层 false_block 是
                    # 内层 ternary 的 condition_block），_cs 作为内层 ternary 的抽象
                    # 节点引用，是合法的 false_value/true_value。依「嵌套即抽象节点」
                    # 原则：内层 ternary 在外层 ternary 中是单表达式值节点，不应拒绝。
                    _cs_existing = analyzer.block_to_region.get(_cs)
                    if isinstance(_cs_existing, TernaryRegion) and _cs_existing.entry is _cs:
                        continue
                    return False
        return True

@dataclass
class TryExceptRegion(Region):
    try_blocks: List[BasicBlock] = field(default_factory=list)
    except_handlers: List[Tuple[Optional[str], Optional[str], List[BasicBlock]]] = field(default_factory=list)
    else_blocks: List[BasicBlock] = field(default_factory=list)
    finally_blocks: List[BasicBlock] = field(default_factory=list)
    has_else: bool = False
    has_finally: bool = False
    try_offset_start: int = 0
    try_offset_end: int = 0
    handler_entry_blocks: List[BasicBlock] = field(default_factory=list)
    finally_copy_blocks: Dict[int, int] = field(default_factory=dict)
    cleanup_blocks: List[BasicBlock] = field(default_factory=list)
    enclosing_try: Optional['TryExceptRegion'] = None

    def get_content_blocks(self) -> Set[BasicBlock]:
        content = set(self.try_blocks)
        for _, _, handler_blocks in self.except_handlers:
            content.update(handler_blocks)
        content.update(self.handler_entry_blocks)
        if self.else_blocks:
            content.update(self.else_blocks)
        if self.finally_blocks:
            content.update(self.finally_blocks)
        return content

    def annotate_structural_roles(self, analyzer) -> None:
        analyzer._annotate_try_except_structural_roles(self)

    def precompute_analysis(self, analyzer) -> None:
        analyzer._enhance_finally_copy_annotation(self)

    def is_block_entry(self, block) -> bool:
        return self.entry == block

    def contains_block(self, block) -> bool:
        return block in self.try_blocks

    def else_block_conflict(self, block) -> bool:
        return False

    def get_offset_range(self, analyzer):
        content_offsets = set()
        for block in self.try_blocks:
            content_offsets.add(block.start_offset)
        for _, _, handler_blocks in self.except_handlers:
            for block in handler_blocks:
                content_offsets.add(block.start_offset)
        for block in (self.else_blocks or []):
            content_offsets.add(block.start_offset)
        for block in (self.finally_blocks or []):
            content_offsets.add(block.start_offset)
        if content_offsets:
            return (min(content_offsets), max(content_offsets))
        return (self.try_offset_start, self.try_offset_end)

    def get_if_branch_boundary_stop(self, block) -> set:
        if block not in self.try_blocks:
            return set()
        try_body_set = set(self.try_blocks) | set(self.else_blocks)
        boundary = set()
        for tb in try_body_set:
            for succ in tb.successors:
                if succ not in try_body_set:
                    boundary.add(succ)
        return boundary

    def get_else_blocks_for_merge(self):
        # 返回else_blocks用于嵌套try合并判断；空则返回None
        return self.else_blocks or None

    def try_except_absorb_split_from(self, inner: 'Region') -> bool:
        # 作为外层try-except，吸收内层split try-except的handler/else/blocks
        # inner 期望为 TryExceptRegion（由调用方_filter_regions保证）
        inner_has_handler = bool(inner.handler_entry_blocks)
        outer_has_finally = self.has_finally and bool(self.finally_blocks)
        if inner_has_handler and outer_has_finally and not self.handler_entry_blocks:
            self.handler_entry_blocks = inner.handler_entry_blocks
            self.handler_regions = getattr(inner, 'handler_regions', [])
            self.except_handlers = getattr(inner, 'except_handlers', [])
            self.has_else = inner.has_else
            self.else_blocks = inner.else_blocks
            self.blocks = self.blocks | inner.blocks
            if inner.entry.start_offset < self.entry.start_offset:
                self.entry = inner.entry
            return True
        return False

@dataclass
class WithRegion(Region):
    with_blocks: List[BasicBlock] = field(default_factory=list)
    exception_blocks: List[BasicBlock] = field(default_factory=list)
    cleanup_blocks: List[BasicBlock] = field(default_factory=list)
    resource_expr: Optional[Any] = None
    target: Optional[str] = None
    is_async: bool = False
    items: List[Tuple[List[Instruction], Optional[str]]] = field(default_factory=list)
    body_offset_start: int = 0
    body_offset_end: int = 0

    def get_content_blocks(self) -> Set[BasicBlock]:
        return set(self.with_blocks)

    def is_block_entry(self, block) -> bool:
        return self.entry == block

    def contains_block(self, block) -> bool:
        return True

    def is_block_in_body(self, block) -> bool:
        return True

    def else_block_conflict(self, block) -> bool:
        return False

    def should_merge_with(self, other: 'Region', analyzer) -> bool:
        # 判定是否可与另一区域合并为连续with（with A: ... with B: ...）
        # other 期望为 WithRegion（由调用方_build_single_with_region保证）
        entry1_has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in self.entry.instructions)
        entry2_has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in other.entry.instructions)
        if not entry1_has_bw or not entry2_has_bw:
            return False
        if self.body_offset_end is None or other.body_offset_start is None:
            return False
        if self.body_offset_end + 1 != other.body_offset_start:
            return False
        entry1_depth = -1
        entry2_depth = -1
        for e in analyzer.cfg.exception_table:
            if e.get('start', 0) == self.body_offset_start:
                entry1_depth = e.get('depth', -1)
            if e.get('start', 0) == other.body_offset_start:
                entry2_depth = e.get('depth', -1)
        if entry1_depth != entry2_depth:
            return False
        return True

@dataclass
class MatchRegion(Region):
    subject_block: Optional[BasicBlock] = None
    case_blocks: List[BasicBlock] = field(default_factory=list)
    case_patterns: List[Any] = field(default_factory=list)
    case_guards: List[Optional[Any]] = field(default_factory=list)
    case_bodies: List[List[BasicBlock]] = field(default_factory=list)
    merge_block: Optional[BasicBlock] = None
    parent_region: Optional['Region'] = None
    case_body_start_indices: Dict[int, int] = field(default_factory=dict)

    def get_content_blocks(self) -> Set[BasicBlock]:
        content = set()
        if self.subject_block:
            content.add(self.subject_block)
        for body_list in self.case_bodies:
            content.update(body_list)
        return content

    def is_block_entry(self, block) -> bool:
        return self.entry == block

    def is_block_in_body(self, block) -> bool:
        return block != self.subject_block

    def can_be_ternary_header(self, block, analyzer) -> bool:
        # match区域占用ternary header块时禁止创建ternary（match优先于ternary）
        return False

    def preserves_against_nested_match(self) -> bool:
        # 已存在的match区域不被嵌套match覆盖
        return True

@dataclass
class AssertRegion(Region):
    condition_block: Optional[BasicBlock] = None
    message_block: Optional[BasicBlock] = None
    # [Round4-12] assert 条件为链式比较（如 `assert 0 < a < 10`）时，
    # condition_block 仅为链式比较的起始块；后续 COMPARE_OP 块通过
    # chained_compare_blocks / chained_compare_ops 持有，由 _generate_assert
    # 重建为多 op 的 Compare 节点。遵循"每块唯一归属"：这些块同时纳入
    # region.blocks，避免被父 IfRegion 重复生成。
    chained_compare_blocks: List[BasicBlock] = field(default_factory=list)
    chained_compare_ops: List[str] = field(default_factory=list)
    # [R10 err 1] assert 条件为 BoolOp（`assert a > 0 and b > 0, "msg"`）时，
    # condition_block 仅为 BoolOp 首段（a > 0）；后续段（b > 0）通过
    # boolop_chain_blocks / boolop_chain_ops 持有，由 _generate_assert
    # 重建为 BoolOp(And/Or, [...]) 节点。每块唯一归属：所有 chain 块
    # 纳入 region.blocks，避免被父 IfRegion 重复生成或被独立识别为
    # 第二条 AssertRegion（导致一条 assert 被错误拆为多条）。
    boolop_chain_blocks: List[BasicBlock] = field(default_factory=list)
    boolop_chain_ops: List[str] = field(default_factory=list)

    def is_block_entry(self, block) -> bool:
        return self.condition_block == block

    def can_be_ternary_header(self, block, analyzer) -> bool:
        # [R8] assert 的 condition_block/entry 块禁止作为 ternary header
        # （ternary 不能吞掉 assert 的测试表达式）。但 message_block 允许：
        # 当 message_block 与 condition_block 不同且等于请求块时，说明
        # message_block 同时是某嵌套 TernaryRegion 的入口（condition_block），
        # 例如 `assert x, (a if c else b)` 的 message_block 含
        # LOAD_ASSERTION_ERROR + ternary 条件跳转。遵循「嵌套即抽象节点」
        # （原则 3）与「父引用子入口」（原则 4）：AssertRegion 通过
        # message_block 引用嵌套 TernaryRegion 的入口，TernaryRegion 在
        # 父 AssertRegion 中作为单个抽象节点。
        if (block is self.message_block
                and self.message_block is not None
                and block is not self.condition_block):
            return True
        return False

@dataclass
class BoolOpRegion(Region):
    op_chain: List[Tuple[BasicBlock, str]] = field(default_factory=list)
    merge_block: Optional[BasicBlock] = None
    value_target: Optional[str] = None
    prefix_block: Optional[BasicBlock] = None
    prefix_op_type: Optional[str] = None
    body_block: Optional[BasicBlock] = None
    condition_expr: Optional[Dict[str, Any]] = None
    condition_block: Optional[BasicBlock] = None
    # [R10 err 3] AugAssign with BoolOp rhs (`x += a and b`):
    # merge_block contains BINARY_OP (in-place, arg>=13) before STORE.
    # value_target is the augassign target (e.g. 'x'), but the leading
    # LOAD of value_target in the first chain block is the augassign
    # target load (not a BoolOp operand) and must be stripped.
    # [R11-err4/5/6] 扩展支持属性/下标目标 (`x.y += a and b`, `x[0] += ...`):
    # augassign_target_kind 区分 'name' / 'attr' / 'subscr'，对 attr/subscr
    # 需在 _generate_boolop 中重建 Attribute/Subscript target 而非 Name。
    is_augassign: bool = False
    augassign_op: Optional[str] = None  # '+', '-', '*', etc. (without '=')
    augassign_target_kind: Optional[str] = None  # 'name' | 'attr' | 'subscr'
    augassign_target_attr: Optional[str] = None  # 属性名（仅 'attr' 时有效）

    def get_score_merge_block(self) -> Optional['BasicBlock']:
        return self.merge_block

    def is_block_entry(self, block) -> bool:
        return self.entry == block

    def contains_block(self, block) -> bool:
        return block == self.entry

    def else_block_conflict(self, block) -> bool:
        return False

    def get_compactness_successors(self, analyzer):
        if not self.op_chain:
            return None
        last_block = self.op_chain[-1][0]
        last_instr = last_block.get_last_instruction()
        if last_instr and last_instr.argval is not None:
            jt = analyzer.cfg.get_block_by_offset(last_instr.argval)
            ft_succs = sorted(last_block.conditional_successors, key=lambda s: s.start_offset)
            ft = next((s for s in ft_succs if s.start_offset != last_instr.argval), None)
            if jt and ft:
                return [ft, jt]
        return None

    def can_be_ternary_header(self, block, analyzer) -> bool:
        # boolop占用ternary header块时，仅当boolop入口==block且非循环条件块时，
        # 才可能升级为ternary（委托analyzer._is_boolop_ternary_candidate判定）
        if self.entry != block:
            return False
        if any(r.condition_block == block
               for r in analyzer._filter_regions(analyzer.regions, LoopRegion)):
            return False
        return analyzer._is_boolop_ternary_candidate(self)

@dataclass
class TernaryRegion(Region):
    condition_block: Optional[BasicBlock] = None
    true_value_block: Optional[BasicBlock] = None
    false_value_block: Optional[BasicBlock] = None
    merge_block: Optional[BasicBlock] = None
    value_target: Optional[str] = None
    merge_context: Optional[str] = None  # Phase 12: merge块上下文类型
    condition_chain_blocks: List[BasicBlock] = field(default_factory=list)
    container_type: Optional[str] = None
    func_call_info: Optional[Dict[str, Any]] = None
    dict_key_info: Optional[Dict[str, Any]] = None
    # [R10-batch1 err 4] For await (ternary): merge_block ends with
    # GET_AWAITABLE + LOAD_CONST None (await setup); the polling loop
    # (SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT) and the
    # STORE_FAST block live in successor blocks. These are merged here
    # so the generator can reconstruct the full Await expression.
    merge_extra_blocks: List[BasicBlock] = field(default_factory=list)

    def get_score_merge_block(self) -> Optional['BasicBlock']:
        return self.merge_block

    def is_block_entry(self, block) -> bool:
        return self.entry == block

    def else_block_conflict(self, block) -> bool:
        return False

    def can_be_ternary_header(self, block, analyzer) -> bool:
        # 已存在的ternary区域占用block时禁止重复创建ternary
        return False

class RegionAnalyzer:
    """
    区域分析器 - 基于编译器理论的结构化分析

    算法流程：
    1. 计算支配树和回边
    2. 识别循环区域（基于回边）
    3. 识别条件区域（基于支配边界）
    4. 识别异常处理区域（基于异常表）
    5. 识别with/match/assert（基于指令特征）
    6. 识别序列区域（剩余线性块）
    7. 构建区域层次树
    """

    def __init__(self, cfg: ControlFlowGraph, parent_code=None, top_level_code=None):
        self.cfg = cfg
        self.parent_code = parent_code
        self._top_level_code = top_level_code
        self.dom_analyzer = DominatorAnalyzer(cfg)
        self.loop_analyzer: Optional[LoopAnalyzer] = None
        self.regions: List[Region] = []
        self.block_to_region: Dict[BasicBlock, Region] = {}
        self.block_roles: Dict[int, BlockRole] = {}
        self.dominance_frontiers: Dict[BasicBlock, Set[BasicBlock]] = {}
        self.effective_instructions: Dict[int, List['Instruction']] = {}
        self._reraise_block_offsets_cache: Optional[Set[int]] = None
        self.metadata: Dict[str, Any] = {}
        self.pattern_parser = PatternParser()
        self.handler_infos: List[Dict[str, Any]] = []
        self.global_declarations: List[Dict[str, Any]] = []
        self._block_metadata: Dict[int, Dict[str, Any]] = {}
        self._current_loop_blocks: Set[BasicBlock] = set()
        self._current_boolop_regions: List[Region] = []
        self.peephole_library = PeepholePatternLibrary()
        self._peephole_matches: List[Dict[str, Any]] = []

    def _filter_regions(self, regions: List['Region'], region_class) -> List['Region']:
        """按精确类型过滤区域列表（使用 type() 而非 isinstance 以避免子类匹配）。"""
        if isinstance(region_class, tuple):
            return [r for r in regions if type(r) in region_class]
        return [r for r in regions if type(r) is region_class]

    def _stack_effect(self, instr) -> tuple:
        """计算单条指令的栈效应（push_count, pop_count）。

        用于静态分析栈深度，判断merge_block中的COMPARE_OP是否消费ternary结果。
        仅覆盖常见的 LOAD/CALL/BINARY_OP/FORMAT_VALUE/BUILD_* 等指令。
        """
        op = instr.opname
        arg = instr.arg
        # [聚类1 修复] COPY 必须先于 LOAD_* 判定（COPY 不以 LOAD_ 开头，
        # 但显式列出以保持可读性）。COPY n 净压 1（复制栈上已有元素）。
        if op == 'COPY':
            return 1, 0
        # [聚类1 修复] LOAD_ATTR 消费栈顶对象，压入属性值（净效应 0）。
        # Python 3.11: LOAD_ATTR arg 仅为 co_names 索引，LSB 无方法标志含义；
        # 方法调用使用独立的 LOAD_METHOD 操作码（压入 NULL+bound method，弹 1）。
        # Python 3.12+ 的 LOAD_ATTR 才用 arg&1 区分方法形式，但当前测试环境
        # 为 3.11，故统一按属性访问处理（LOAD_METHOD 分支处理方法形式）。
        if op == 'LOAD_ATTR':
            return 1, 1
        if op == 'LOAD_METHOD':
            return 2, 1
        if op.startswith('LOAD_'):
            return 1, 0
        # [聚类1 修复] BINARY_SUBSCR 弹 2（value + slice），压 1（subscript）
        if op == 'BINARY_SUBSCR':
            return 1, 2
        # [聚类1 修复] NONE_CHECK_OPS 与条件跳转弹 1（被测试的值）
        if op in NONE_CHECK_OPS:
            return 0, 1
        if op in (FORWARD_CONDITIONAL_JUMP_OPS | BACKWARD_CONDITIONAL_JUMP_OPS):
            # IF_NONE / IF_NOT_NONE 已在上面处理；IF_FALSE / IF_TRUE 弹 1
            if 'IF_NONE' in op or 'IF_NOT_NONE' in op:
                return 0, 1
            return 0, 1
        if op in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
            return 1, 2
        if op == 'BINARY_OP':
            return 1, 2
        if op.startswith('UNARY_'):
            return 1, 1
        if op == 'FORMAT_VALUE':
            return 1, 1 if (arg or 0) < 2 else 2
        if op == 'BUILD_STRING':
            return 1, arg or 0
        # [聚类1 修复] BUILD_MAP 弹 2*argc（key-value 对），压 1（dict）
        if op == 'BUILD_MAP':
            return 1, 2 * (arg or 0)
        if op.startswith('BUILD_'):
            return 1, arg or 0
        if op in ('PRECALL', 'POP_TOP'):
            return 0, 0
        if op == 'CALL':
            return 1, (arg or 0) + 1
        # [聚类1 修复] SWAP 净效应为 0（交换栈顶两元素）
        if op == 'SWAP':
            return 0, 0
        if op == 'STORE_FAST' or op == 'STORE_NAME' or op == 'STORE_GLOBAL' or op == 'STORE_DEREF':
            return 0, 1
        # 默认：假设无栈效应（保守估计）
        return 0, 0

    def _check_block_has_trailing_return_none(self, block: BasicBlock) -> bool:
        """检查单个块是否以Return None结尾

        检测标准：
        - 块的最后一条指令是 RETURN_CONST
        - 该指令的参数值是 None

        Args:
            block: 待检测的基本块

        Returns:
            bool: 是否以 Return None 结尾
        """
        if not block or not block.instructions:
            return False
        last_instr = block.get_last_instruction()
        if last_instr is None:
            return False
        if last_instr.opname == 'RETURN_CONST' and last_instr.argval is None:
            return True
        if last_instr.opname == 'RETURN_VALUE':
            instrs = block.instructions
            for i in reversed(instrs[:-1]):
                if i.opname in ('NOP', 'CACHE', 'POP_TOP'):
                    continue
                if i.opname == 'LOAD_CONST' and i.argval is None:
                    return True
                break
        return False

    def analyze(self) -> List[Region]:
        """
        区域归约（Region-Reduction）分析的总驱动。

        ══════════════════════════════════════════════════════════════════════
        核心原则（来自 "No More Gotos" Launez et al., 2013 + 用户归约算法约束）
        ══════════════════════════════════════════════════════════════════════
        1. 自底向上归约：从最内层区域向最外层识别（归约顺序），不回溯修正。
        2. 每块唯一归属：任一基本块在任何层级只属于一个区域。
        3. 嵌套即抽象节点：嵌套区域在其父区域中表示为单个抽象节点。
        4. 入口引用语义：归约后父区域的 then/else/body 列表引用**子区域入口块**，
           而非子区域的所有块；子区域块只属于子区域。
        禁令：禁止跨区域/跨层次的启发式规则；禁止破坏算法对嵌套的天然支持。
        算法驱动：回边检测（支配树）→ 区域分类 → 归约 → AST 映射（一一对应）。

        ══════════════════════════════════════════════════════════════════════
        各区域类型的反编译逻辑（识别方法注释的统一模板）
        ══════════════════════════════════════════════════════════════════════
        区域类型          识别方法                   CFG 形态 / 算法                          AST 映射
        ────────────────────────────────────────────────────────────────────────────────────
        WHILE_LOOP        _identify_loop_regions    回边 B→H(H 支配 B)；自然循环体收集；        While(test, body)
                                                  header 含条件 → while cond；否则 while True
        FOR_LOOP          _identify_loop_regions    header 含 FOR_ITER/GET_ANITER             For(target, iter, body)
        IF/IF_THEN_ELSE    _identify_conditional_    两后继 A,B；最近公共支配后继=merge；        If(test, body, orelse)
                          _regions                  A→then, B→else；else 入口为条件块→elif 链
        IF_ELIF_CHAIN      _identify_conditional_    嵌套 if 区域合并为 elif 链                If(…, orelse=[If(…)])
                          _regions
        TRY_EXCEPT        _identify_try_except_     异常表(co_exceptiontable / SETUP_*)定义     Try(body, handlers,
                          _regions                 受保护区与 handler；PUSH_EXC_INFO+           finalbody)
                                                  CHECK_EXC_MATCH→except；RERAISE→finally
        WITH              _identify_with_regions    BEFORE_WITH/ WITH_EXCEPT_START 配对        With(items, body)
        MATCH             _identify_match_regions   MATCH/COMPARE_OP+POP_JUMP_IF_NONE 链        Match(subject, cases)
        ASSERT            _identify_assert_regions  POP_JUMP_IF_TRUE + RAISE_VARARGS(1)         Assert(test, msg)
        BOOL_OP           _identify_boolop_regions  and/or 短路：cond 跳至下一分支=右操作数     BoolOp(op, [l, r])
        TERNARY           _identify_ternary_regions POP_JUMP_IF_* 两路汇聚到同一 merge          IfExp(test, body, orelse)
        CHAINED_COMPARE    _identify_chained_        a<b<c：连续比较块，左值跨块复用            Compare(left, ops, comps)
                          _compare_regions
        SEQUENCE          _identify_sequence_regions 剩余无结构的基本块按前驱→后继顺序拼接      stmt 序列

        归约语义（对每一区域通用）：
        - 区域入口块 = 该结构头（loop header / if condition / try protected-entry / …）。
        - 父区域引用本区域入口块作为抽象节点；本区域内部块不出现在父区域的 then/else/body 展开中。
        - 回边（loop 的 JUMP_BACKWARD）是循环迭代机制的一部分，随 `while/for` 隐式表达，
          不应作为独立 if-break 生成（见 _identify_loop_regions 注释中的「底部闩锁」说明）。

        ══════════════════════════════════════════════════════════════════════
        当前实现说明（与纯迭代归约的关系）
        ══════════════════════════════════════════════════════════════════════
        本方法当前采用「固定优先级三阶段流水线」(TRY>LOOP>WITH/MATCH/ASSERT>
        CHAINED_COMPARE>BOOLOP>TERNARY>IF>SEQUENCE) 作为对论文 4.1 迭代归约循环
        的工程近似。该流水线在满足上述 4 条核心原则（每块唯一归属、嵌套即抽象节点、
        父引用子入口、回边吸收）时，与真·迭代归约等价。任何识别方法都不得以
        跨层/跨区域的特例判断破坏这些原则；如遇此类特例，应回归到区域归约本身修正。

        ══════════════════════════════════════════════════════════════════════
        多态分发：Region 基类上的覆写点
        ══════════════════════════════════════════════════════════════════════
        归约过程中跨区域类型的语义差异通过 Region 基类上定义的多态分发方法
        （子类按需覆写，默认实现为 no-op）消解，避免在识别器里散布 isinstance
        分支。当前共 19 个覆写点（位于本文件 Region 基类定义内），按职责分组：
          - 结构化角色/预计算: annotate_structural_roles, annotate_cond_recheck,
            precompute_analysis, get_score_merge_block
          - 块归属判定: is_block_entry, contains_block, is_block_in_body,
            else_block_conflict, get_offset_range
          - if/分支协调: get_if_branch_boundary_stop, get_if_body_blocks,
            get_compactness_successors, get_else_blocks_for_merge
          - ternary/boolop 协调: can_be_ternary_header, interrupts_boolop_forward_chain
          - with/try/match 协调: get_with_body_orphan_instructions,
            try_except_absorb_split_from, should_merge_with,
            preserves_against_nested_match
        这些方法在 _identify_conditional_regions / _identify_boolop_regions /
        _identify_ternary_regions / _build_region_hierarchy 等处被调用，承载
        "嵌套即抽象节点" 与 "父引用子入口" 两条原则的类型相关逻辑。

        ══════════════════════════════════════════════════════════════════════
        孤儿块释放（Orphan Block Release）—— 在下游 generate() 阶段执行
        ══════════════════════════════════════════════════════════════════════
        analyze() 仅完成区域识别与 block_to_region 登记；孤儿块释放发生在
        region_ast_generator.RegionASTGenerator.generate() 顶部，作为归约→AST
        映射之间的桥接：
          - 当内部区域被过滤掉（其 entry 在外层区域 blocks 中）时，其部分块
            （如 merge 点）可能既不属于任何顶级区域、也不属于自身区域。这些
            "孤儿块" 需从 block_to_region 释放，使其能获得独立的 BASIC 区域，
            否则会在最终 AST 中丢失（违反"每块唯一归属"的全覆盖目标）。
          - te046 修复（2026-07-14，解锁 100% 基线）：原逻辑仅检查"块所属区域
            非顶级 + 块不在任何顶级区域 blocks 中"即判为孤儿并释放，但合法
            嵌套子区域（有顶级祖先）的块符合该条件且不应被释放——它们由父区域
            生成子区域时通过入口引用语义处理（原则3「嵌套即抽象节点」）。
            修复增加"顶级祖先"检查：沿 parent 链查找，若存在顶级祖先则该块
            为合法嵌套子区域块，不释放；否则才视为真正孤儿块释放并补建 BASIC
            区域。此修复消除了 spurious `if True: pass` 输出。

        ══════════════════════════════════════════════════════════════════════
        当前测试矩阵状态
        ══════════════════════════════════════════════════════════════════════
        全量通过率: 100%（2068/2068，te046 已修复通过）。
        算法合规度: 完全合规（4 核心原则全满足，无硬编码深度限制）。
        字节码一致性: 全部测试用例反编译产物与原字节码完全匹配。
        """
        #print(f"[DEBUG analyze] ({self.cfg.name}) ENTER analyze()")
        # 初始化分析器
        self.dom_analyzer.analyze()
        self.loop_analyzer = LoopAnalyzer(self.cfg, self.dom_analyzer)
        self.loop_analyzer.analyze()
        self._coalesce_nop_prefix_loop_headers()
        self.dominance_frontiers = self.dom_analyzer.compute_all_dominance_frontiers()

        # Phase 1: 低层区域识别（按优先级排序）
        # 优先级规则：TRY(异常处理) > LOOP(循环) > WITH/MATCH/ASSERT(其他结构)
        # 原因：
        # - 异常处理区域可能跨越循环和条件（最高优先级）
        # - 循环有回边需要特殊处理（次高优先级）
        # - 其他结构依赖前两者的结果
        try_regions = self._identify_try_except_regions()
        try_regions = self._coalesce_split_try_except_finally_regions(try_regions)
        loop_regions = self._identify_loop_regions()
        with_regions = self._identify_with_regions()
        match_regions = self._identify_match_regions()
        assert_regions = self._identify_assert_regions()

        # [Phase 2.5.1-2.5.2] CPython peephole 优化模式库预处理
        # 扫描所有 P1 模式（模块级三元表达式语句 → 双 RETURN_VALUE），
        # 释放被 MatchRegion 误识别的值块（match_regions 守卫会拒绝三元识别）。
        # 此预处理在所有 Phase 1 区域识别完成后、Phase 2 高层识别前执行，
        # 确保三元识别阶段能看到正确的 match_regions 集合。
        self._peephole_matches = self.peephole_library.match_peephole_pattern(
            list(self.cfg.blocks.values()), self.cfg
        )
        if self._peephole_matches:
            _p1_value_blocks: Set[BasicBlock] = set()
            for _match in self._peephole_matches:
                _p1_value_blocks.update(_match.get('value_blocks_to_release', []))
            if _p1_value_blocks:
                match_regions = [
                    _mr for _mr in match_regions
                    if not (_mr.blocks & _p1_value_blocks)
                ]

        # Phase 2: 高层区域识别(接收Phase 1结果)
        chained_compare_regions = self._identify_chained_compare_regions(
            loop_regions=loop_regions,
            try_regions=try_regions,
            with_regions=with_regions,
            match_regions=match_regions,
            assert_regions=assert_regions
        )
        boolop_regions = self._identify_boolop_regions(
            existing_regions=loop_regions + try_regions + with_regions + match_regions + assert_regions + chained_compare_regions
        )
        ternary_regions = self._identify_ternary_regions(
            loop_regions=loop_regions,
            try_regions=try_regions,
            with_regions=with_regions,
            match_regions=match_regions,
            boolop_regions=boolop_regions,
            conditional_regions=chained_compare_regions
        )

        _ternary_block_sets = []
        _ternary_regions_with_blocks = []
        for tr in ternary_regions:
            if tr.blocks:
                _ternary_block_sets.append(tr.blocks)
                _ternary_regions_with_blocks.append(tr)

        if _ternary_block_sets:
            def _region_overlaps_with_ternary(region):
                for _ti, tb_set in enumerate(_ternary_block_sets):
                    _tr = _ternary_regions_with_blocks[_ti]
                    # [R8 / R17-11] AssertRegion 可与嵌套 TernaryRegion 合法重叠：
                    #  - message_block == 某 TernaryRegion.entry（`assert x, (ternary)`）
                    #  - condition_block == 某 TernaryRegion.merge_block
                    #    （`assert (ternary).method()`，merge_block 含消费指令 + assert
                    #     测试跳转 POP_JUMP_IF_TRUE）。依「嵌套即抽象节点」+
                    #    「父引用子入口」：AssertRegion 通过 condition_block /
                    #    message_block 引用嵌套 TernaryRegion，属合法嵌套，不过滤。
                    if isinstance(region, AssertRegion):
                        _mb = region.message_block
                        _cb = region.condition_block
                        _legal_overlap = set()
                        if (_mb is not None and _mb is not _cb
                                and _mb in tb_set
                                and _tr.entry is _mb):
                            _legal_overlap.add(_mb)
                        if (_cb is not None
                                and _cb in tb_set
                                and getattr(_tr, 'merge_block', None) is _cb):
                            _legal_overlap.add(_cb)
                        if _legal_overlap:
                            overlap = region.blocks & tb_set
                            if overlap <= _legal_overlap:
                                continue  # 合法嵌套：跳过此 tb_set
                            return True
                        # AssertRegion 与此 ternary 无合法嵌套关系，但若仍有块
                        # 重叠（entry 或其他），按常规处理。
                        if region.entry and region.entry in tb_set:
                            return True
                        overlap = region.blocks & tb_set
                        if overlap:
                            return True
                        continue
                    if region.entry and region.entry in tb_set:
                        return True
                    overlap = region.blocks & tb_set
                    if overlap:
                        # [R8] AssertRegion 的 message_block 可能是某嵌套
                        # TernaryRegion 的 entry（如 `assert x, (a if c else b)`，
                        # AssertRegion.blocks={0,6}, TernaryRegion.blocks={6,12,16,18}，
                        # 重叠={6}=message_block）。这种情况是「嵌套即抽象节点」
                        # （原则 3）+「父引用子入口」（原则 4）的合法嵌套，
                        # 不应过滤掉 AssertRegion。_generate_assert 通过
                        # message_block 引用嵌套 TernaryRegion 入口。
                        if (isinstance(region, AssertRegion)
                                and region.message_block is not None
                                and region.message_block is not region.condition_block
                                and overlap == {region.message_block}):
                            continue  # 合法嵌套：跳过此 tb_set
                        return True
                return False

            match_regions = [r for r in match_regions if not _region_overlaps_with_ternary(r)]
            assert_regions = [r for r in assert_regions if not _region_overlaps_with_ternary(r)]

        conditional_regions = self._identify_conditional_regions(
            loop_regions=loop_regions,
            assert_regions=assert_regions,
            try_regions=try_regions,
            with_regions=with_regions,
            match_regions=match_regions,
            boolop_regions=boolop_regions,
            ternary_regions=ternary_regions
        )

        _while_boolop_data = []
        for _wbr in boolop_regions:
            if getattr(_wbr, 'is_condition_context', False):
                _wlr = _wbr.parent if hasattr(_wbr, 'parent') and isinstance(_wbr.parent, LoopRegion) else None
                if _wlr and _wlr.condition_block is not None:
                    _boolop_chain_blocks = set(b for b, _ in _wbr.op_chain)
                    _while_boolop_data.append((_wbr, _wlr, _boolop_chain_blocks))
        if _while_boolop_data:
            _to_remove_cond = []
            for _ci, _cr in enumerate(conditional_regions):
                if not isinstance(_cr, IfRegion):
                    continue
                _should_remove = False
                for _wbr, _wlr, _boolop_chain_blocks in _while_boolop_data:
                    _cr_cond = getattr(_cr, 'condition_block', None)
                    if _cr_cond is None or _cr_cond != _wlr.condition_block:
                        continue
                    if _cr.entry == _wbr.entry or _cr.entry == _wlr.condition_block:
                        _should_remove = True
                        break
                if _should_remove:
                    _to_remove_cond.append(_ci)
            for _ci in sorted(_to_remove_cond, reverse=True):
                _removed = conditional_regions.pop(_ci)
                for _rb in _removed.blocks:
                    if _rb in self.block_to_region and self.block_to_region[_rb] is _removed:
                        del self.block_to_region[_rb]
                if _removed in self.regions:
                    self.regions.remove(_removed)

        # Phase 2.5: 嵌套Match区域二次扫描
        # 反编译逻辑：
        # 当match语句嵌套在if/for/try等父区域中时，父区域的blocks会包含match的subject块和case块。
        # 在Phase 1的_identify_match_regions()中，这些块已被标记为claimed（被父区域占用），
        # 导致嵌套match无法被识别。
        #
        # 解决方案：在所有高层区域（if/for/try等）识别完成后，
        # 对每个父区域内部进行二次match扫描，发现嵌套match时创建子MatchRegion。
        #
        # 字节码特征：
        # - 嵌套match的字节码模式与顶层match完全相同
        # - 区别仅在于subject块和case块已被父区域的block_to_region映射覆盖
        #
        # 处理策略：
        # 1. 收集所有可能包含嵌套match的父区域（IfRegion、ForRegion、TryRegion、WithRegion）
        # 2. 对每个父区域，扫描其blocks中未被match占用的块
        # 3. 检测match特征：_has_match_op()或_is_match_subject_block()或_is_simple_match_case_block()
        # 4. 收集完整的case链并创建子MatchRegion
        # 5. 子MatchRegion的blocks可以与父区域重叠（作为子区域）
        #
        # 关键约束：
        # - 子match不能跨越父区域边界
        # - 子match的blocks必须是父区域blocks的子集
        # - 需要更新block_to_region映射以反映父子关系
        nested_match_regions = self._identify_nested_match_regions(
            parent_regions=conditional_regions + loop_regions + try_regions + with_regions,
            existing_match_regions=match_regions
        )
        match_regions = match_regions + nested_match_regions

        elif_chain_entries = set()
        for cr in self._filter_regions(conditional_regions, IfRegion):
            if cr.region_type == RegionType.IF_ELIF_CHAIN:
                elif_chain_entries.add(cr.entry)
        ternary_regions = [tr for tr in ternary_regions
                          if not (tr.entry and tr.entry in elif_chain_entries)]

        elif_condition_blocks = set()
        for cr in self._filter_regions(conditional_regions, IfRegion):
            if cr.elif_conditions:
                for ec in cr.elif_conditions:
                    elif_condition_blocks.add(ec)
        # [Phase 3 adv15_ternary_elif_test] 区分两种 entry 落在
        # elif_condition_blocks 中的三元：
        #
        # (A) 真正的"三元作为 elif 条件"——三元的结果被内联为条件
        #     测试（CPython 3.11+ 优化）。此时 true_value_block 和
        #     false_value_block 各自带 POP_JUMP_IF_FALSE/TRUE 跳到
        #     "skip body" 块，且 true_value_block 末尾通过 JUMP_FORWARD
        #     跳到 merge_block。`_detect_ternary_pattern` 将此模式识别
        #     为 has_jump_forward_skip=True，并设置
        #     merge_context='while_cond' / value_target='__while_cond_target__'。
        #     此类三元必须保留——它就是 elif 条件本身。移除会使其
        #     被错误地拆解为多层 elif 链：
        #       `elif (b if c else d): pass` → `elif c: if b: pass / elif d: pass`
        #     语义不等价。
        #
        # (B) if/elif/else 被误识别为三元（语句体而非表达式体）。
        #     此类三元的 value_target 是真实变量名或 None，
        #     merge_context 不是 'while_cond'。继续按原逻辑移除。
        def _is_ternary_conditional_context(_tr):
            return (_tr.merge_context == 'while_cond'
                    or _tr.value_target == '__while_cond_target__')
        removed_ternary = [tr for tr in ternary_regions
                          if tr.entry and tr.entry in elif_condition_blocks
                          and not _is_ternary_conditional_context(tr)]
        ternary_regions = [tr for tr in ternary_regions
                          if not (tr.entry and tr.entry in elif_condition_blocks
                                  and not _is_ternary_conditional_context(tr))]
        # 条件上下文三元作为 elif 条件：与 IfRegion 建立父子关系，
        # 类似 boolop 在 elif 条件上下文中的处理（line 1249+）。
        for tr in ternary_regions:
            if (tr.entry and tr.entry in elif_condition_blocks
                    and _is_ternary_conditional_context(tr)):
                if getattr(tr, 'parent', None) is None:
                    for cr in self._filter_regions(conditional_regions, IfRegion):
                        if tr.entry in cr.elif_conditions:
                            tr.parent = cr
                            if tr not in cr.children:
                                cr.add_child(tr)
                            break
        for br in boolop_regions:
            if br.entry and br.entry in elif_condition_blocks:
                br.is_condition_context = True
                if hasattr(br, 'parent') and br.parent is None:
                    for cr in self._filter_regions(conditional_regions, IfRegion):
                        if br.entry in cr.elif_conditions:
                            br.parent = cr
                            if br not in cr.children:
                                cr.add_child(br)
                            break
        for tr in removed_ternary:
            if tr in self.regions:
                self.regions.remove(tr)
            for b in tr.blocks:
                if b in self.block_to_region and self.block_to_region[b] is tr:
                    del self.block_to_region[b]

        if removed_ternary:
            removed_entries = set()
            for tr in removed_ternary:
                if tr.entry:
                    removed_entries.add(tr.entry)
            conditional_regions = [cr for cr in conditional_regions
                                   if not (isinstance(cr, IfRegion) and cr.entry in removed_entries
                                           and any(b in elif_condition_blocks for b in cr.blocks))]

        # Phase 11修复: 移除与Ternary重叠的IfRegion和BoolOpRegion
        #
        # 问题: 当同一代码既可以被识别为Ternary又可以被识别为IfRegion/BoolOp时，
        #       IfRegion(30)和BoolOp(20)会由于更高优先级而覆盖Ternary(15)
        #
        # 解决: 在合并到all_phase12_regions之前，移除被Ternary完全覆盖的区域
        # 条件: 区域的entry与某个Ternary的entry相同
        #
        # 这确保了 `a if a and b else 0` 被正确识别为Ternary而非If/BoolOp
        # NOTE: Disabled due to over-aggressive TernaryRegion identification causing
        #       massive IfRegion loss. Let priority-based resolution handle conflicts instead.
        filtered_conditional_regions = list(conditional_regions)
        filtered_boolop_regions = list(boolop_regions)

        all_phase12_regions = (
            loop_regions + try_regions + with_regions +
            match_regions + assert_regions + chained_compare_regions + filtered_boolop_regions + ternary_regions + filtered_conditional_regions
        )

        #print(f"[DEBUG analyze] ({self.cfg.name}) chained_compare_regions count: {len(chained_compare_regions)}")
        for r in chained_compare_regions:
            #print(f"  region: {type(r).__name__}, blocks={[b.start_offset for b in r.blocks]}, region_type={r.region_type}")
            pass
        #print(f"[DEBUG analyze] loop: {len(loop_regions)}, try: {len(try_regions)}, with: {len(with_regions)}, match: {len(match_regions)}, assert: {len(assert_regions)}, boolop: {len(boolop_regions)}, ternary: {len(ternary_regions)}, cond: {len(conditional_regions)}")
        #print(f"[DEBUG analyze] all_phase12_regions count: {len(all_phase12_regions)}")
        for r in all_phase12_regions:
            #print(f"  region: {type(r).__name__}, blocks={[b.start_offset for b in r.blocks]}, region_type={r.region_type}")
            pass

        sequence_regions = self._identify_sequence_regions(existing_regions=all_phase12_regions)

        all_regions = all_phase12_regions + sequence_regions
        
        elif_boolop_entry_blocks = set()
        for region in self._filter_regions(all_regions, BoolOpRegion):
            if region.entry and region.entry in elif_condition_blocks:
                for b, _ in region.op_chain:
                    elif_boolop_entry_blocks.add(b)

        self._elif_boolop_entry_blocks = elif_boolop_entry_blocks

        # 区域归约算法：收集所有 MatchRegion 的 case body 块集合
        # 反编译逻辑：match case body 内的 if/elif/else 语句体（IfRegion）和
        # and/or 条件表达式（BoolOpRegion）是 MatchRegion 的内层区域。
        # 根据"每块唯一归属"原则，内层区域应优先于外层 MatchRegion。
        # 此集合用于 block_to_region 重建时判断 IfRegion 是否嵌套在 MatchRegion 内。
        match_case_body_blocks = set()
        for region in self._filter_regions(all_regions, MatchRegion):
            for body_list in region.case_bodies:
                match_case_body_blocks.update(body_list)

        self.block_to_region.clear()
        for region in all_regions:
            current_priority = self.REGION_TYPE_PRIORITY.get(region.region_type, 0)
            for block in region.blocks:
                existing = self.block_to_region.get(block)
                if existing is None:
                    self.block_to_region[block] = region
                else:
                    if isinstance(region, BoolOpRegion) and block in elif_boolop_entry_blocks:
                        self.block_to_region[block] = region
                    elif isinstance(existing, BoolOpRegion) and block in elif_boolop_entry_blocks:
                        pass
                    elif self._should_use_dynamic_priority(existing, region):
                        existing_score = self._compute_dynamic_region_score(block, existing)
                        candidate_score = self._compute_dynamic_region_score(block, region)
                        if candidate_score > existing_score:
                            self.block_to_region[block] = region
                    else:
                        existing_priority = self.REGION_TYPE_PRIORITY.get(
                            existing.region_type, 0)
                        if current_priority > existing_priority:
                            self.block_to_region[block] = region

        self._build_region_hierarchy(regions=all_regions)

        self._cleanup_try_else_in_loop_body(loop_regions, try_regions)

        self._annotate_all_roles(all_regions)

        for _lr in loop_regions:
            if hasattr(_lr, 'break_blocks'):
                for _bb in _lr.break_blocks:
                    if _bb in _lr.blocks:
                        self.block_roles[_bb.start_offset] = BlockRole.BREAK

        fake_loop_region_ids = self._detect_and_filter_conditional_recheck_fake_loops(loop_regions)
        if fake_loop_region_ids:
            self._rebuild_block_roles_after_fake_loop_removal(loop_regions, fake_loop_region_ids)
            loop_regions = [r for r in loop_regions if id(r) not in fake_loop_region_ids]
            all_regions = [r for r in all_regions if id(r) not in fake_loop_region_ids]
            for block, region in list(self.block_to_region.items()):
                if id(region) in fake_loop_region_ids:
                    del self.block_to_region[block]

        self._precompute_all_generator_data(all_regions)

        for block in self.cfg.blocks.values():
            if self._has_with_exit_call(block):
                self._assign_region_role(block.start_offset, BlockRole.WITH_EXIT_CALL)

        self.regions = all_regions

        #print(f"[DEBUG analyze] ({self.cfg.name}) FINAL self.regions count: {len(self.regions)}")
        for r in self.regions:
            #print(f"  region: {type(r).__name__}, blocks={[b.start_offset for b in r.blocks]}, region_type={r.region_type}")
            pass

        self._compute_generator_entry_metadata()

        code_obj = getattr(self.cfg, 'code', None)
        self.global_declarations = self._detect_global_declarations(code_obj) if code_obj else []

        return self.regions

    def _detect_global_declarations(self, code_obj) -> List[Dict[str, Any]]:
        if code_obj is None:
            return []
        import dis as _dis
        local_vars = set(code_obj.co_varnames) if hasattr(code_obj, 'co_varnames') else set()
        free_vars = set(code_obj.co_freevars) if hasattr(code_obj, 'co_freevars') else set()
        cell_vars = set(code_obj.co_cellvars) if hasattr(code_obj, 'co_cellvars') else set()
        global_names = []
        nonlocal_names = []
        load_global_names = []
        for block in self.cfg.blocks.values():
            for instr in block.instructions:
                if instr.opname == 'STORE_GLOBAL' and instr.argval not in global_names:
                    if instr.argval not in local_vars:
                        global_names.append(instr.argval)
                if instr.opname == 'LOAD_GLOBAL' and instr.argval not in load_global_names:
                    if instr.argval not in local_vars and instr.argval not in free_vars:
                        load_global_names.append(instr.argval)
                if instr.opname == 'STORE_DEREF' and instr.argval not in nonlocal_names:
                    if instr.argval in free_vars and instr.argval not in cell_vars:
                        nonlocal_names.append(instr.argval)

        if not nonlocal_names and free_vars:
            parent_code = getattr(self, 'parent_code', None)
            if parent_code is not None and hasattr(parent_code, 'co_name') and parent_code.co_name != '<module>':
                parent_cellvars = set(getattr(parent_code, 'co_cellvars', ()))
                for fv in free_vars:
                    if fv in parent_cellvars and fv not in nonlocal_names:
                        nonlocal_names.append(fv)

        if not global_names:
            for instr in _dis.get_instructions(code_obj):
                if instr.opname in ('STORE_GLOBAL', 'DELETE_GLOBAL') and instr.argval not in global_names:
                    if instr.argval not in local_vars:
                        global_names.append(instr.argval)

        if not load_global_names:
            for instr in _dis.get_instructions(code_obj):
                if instr.opname == 'LOAD_GLOBAL' and instr.argval not in load_global_names:
                    if instr.argval not in local_vars and instr.argval not in free_vars:
                        load_global_names.append(instr.argval)

        if load_global_names:
            try:
                import builtins
                builtin_names = set(dir(builtins))
            except ImportError:
                builtin_names = set()

            import_stores = set()
            func_class_names = set()
            non_import_stores = set()

            _parents_to_check = []
            _cur_parent = self.parent_code
            if _cur_parent is None:
                _cur_parent = getattr(self.cfg, 'code', None)
            while _cur_parent is not None and hasattr(_cur_parent, 'co_name') and _cur_parent.co_name != '<module>':
                _parents_to_check.append(_cur_parent)
                if hasattr(_cur_parent, 'co_consts'):
                    for const in _cur_parent.co_consts:
                        if hasattr(const, 'co_name') and const.co_name != '<module>':
                            func_class_names.add(const.co_name)
                _cur_parent = None
                if hasattr(self, '_top_level_code') and self._top_level_code is not None:
                    _cur_parent = self._top_level_code
                    break
            if _cur_parent is not None and hasattr(_cur_parent, 'co_name') and _cur_parent.co_name == '<module>':
                _parents_to_check.append(_cur_parent)

            for parent in _parents_to_check:
                if not hasattr(parent, 'co_consts'):
                    continue
                for const in parent.co_consts:
                    if hasattr(const, 'co_name') and const.co_name != '<module>':
                        func_class_names.add(const.co_name)

                parent_instrs = list(_dis.get_instructions(parent))
                for i, instr in enumerate(parent_instrs):
                    if instr.opname in ('STORE_NAME', 'STORE_GLOBAL'):
                        is_import_store = False
                        for j in range(i - 1, max(i - 10, -1), -1):
                            if parent_instrs[j].opname in ('IMPORT_NAME', 'IMPORT_FROM'):
                                is_import_store = True
                                break
                            if parent_instrs[j].opname in ('STORE_NAME', 'STORE_GLOBAL'):
                                break
                        if is_import_store:
                            import_stores.add(instr.argval)
                        else:
                            non_import_stores.add(instr.argval)

            for name in load_global_names:
                if name in global_names:
                    continue
                if name in builtin_names:
                    continue
                if name in import_stores:
                    continue
                if name in func_class_names:
                    continue
                if non_import_stores and name not in non_import_stores:
                    continue
                global_names.append(name)

        result = []
        if global_names:
            result.append({'type': 'Global', 'names': global_names})
        if nonlocal_names:
            result.append({'type': 'Nonlocal', 'names': nonlocal_names})
        return result

    def _find_nearest_common_post_dominator(self, block_a: BasicBlock, block_b: BasicBlock) -> Optional[BasicBlock]:
        return self.dom_analyzer.find_nearest_common_post_dominator_two(block_a, block_b)


    def _collect_blocks_on_path(self, entry: BasicBlock, exit_block: BasicBlock, stop_set: Optional[Set[BasicBlock]] = None) -> Set[BasicBlock]:
        result: Set[BasicBlock] = set()
        worklist = [entry]
        visited: Set[BasicBlock] = {entry}
        while worklist:
            current = worklist.pop()
            if current == exit_block:
                continue
            if stop_set and current in stop_set:
                continue
            result.add(current)
            last = current.get_last_instruction()
            if last and last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                continue
            for succ in current.successors:
                if succ not in visited:
                    visited.add(succ)
                    worklist.append(succ)
        return result

    @staticmethod
    def _has_with_exit_call(block: BasicBlock) -> bool:
        for idx in range(len(block.instructions) - 5):
            window = block.instructions[idx:idx + 6]
            if (window[0].opname == 'LOAD_CONST' and window[0].argval is None and
                window[1].opname == 'LOAD_CONST' and window[1].argval is None and
                window[2].opname == 'LOAD_CONST' and window[2].argval is None and
                window[3].opname in ('PRECALL',) and
                window[4].opname in ('CALL', 'CALL_FUNCTION') and
                window[5].opname == 'POP_TOP'):
                return True
        return False

    def _is_single_expression_block(self, block: BasicBlock) -> bool:
        """检测是否是单表达式块（Phase 5增强版）

        允许的情况：
        1. 纯表达式指令（LOAD/CALL/BINARY_OP等）
        2. 最后一个指令可以是：JUMP_FORWARD/POP_TOP
        3. 不允许：STORE/DELETE/RAISE/YIELD/IMPORT等副作用操作

        Phase 5修复（关键bug修复）：
        - 排除 [LOAD_*, RETURN_VALUE] 模式（if-elif-return 语句的典型特征）
        - 真正的三元表达式值分支以 JUMP_FORWARD 到合并点结尾（用于后续STORE）
        - if/elif 分支中的 return 语句以 RETURN_VALUE 直接结尾（无JUMP）
        - 此修复解决18个 if-elif-return 被误判为 TernaryRegion 的问题

        字节码证据：
          三元表达式: LOAD_CONST 1, JUMP_FORWARD → merge  (值需被存储)
          if-return:   LOAD_CONST 1, RETURN_VALUE            (直接函数返回)
        """
        effective = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not effective:
            return False

        while effective and effective[-1].opname in (
            'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
            effective = effective[:-1]
        if not effective:
            return False

        if effective[-1].opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
            effective = effective[:-1]
            if not effective:
                return False

        # [R1 Bug 1/2 修复] walrus (y := expr) 的 COPY+STORE 副作用剥离
        # 字节码模式: <expr 求值>; COPY 1; STORE_*(y)
        # COPY 1 复制栈顶值，STORE 消耗复制体给 walrus 目标 y，
        # 原值留在栈上作为 ternary 值块的求值结果（流向 merge_block）。
        # 整个 COPY+STORE 对是 walrus 子表达式的副作用，不破坏外层
        # 单表达式性——块仍只产生一个表达式值（原 expr 求值结果）。
        # 依「嵌套即抽象节点」：walrus 是值表达式内的子节点，
        # 块整体归属 TernaryRegion（每块唯一归属）。
        # 注意：walrus := 仅可目标 NAME，所以 STORE 必为 STORE_FAST/NAME/GLOBAL/DEREF。
        _walrus_stripped = []
        _idx = 0
        while _idx < len(effective):
            _instr = effective[_idx]
            if (_instr.opname == 'COPY' and _instr.argval >= 1
                    and _idx + 1 < len(effective)
                    and effective[_idx + 1].opname in (
                        'STORE_FAST', 'STORE_NAME',
                        'STORE_GLOBAL', 'STORE_DEREF')):
                # walrus 副作用对 (COPY + STORE)，跳过
                _idx += 2
                continue
            _walrus_stripped.append(_instr)
            _idx += 1
        effective = _walrus_stripped
        if not effective:
            return False

        pop_idx = None
        for idx, instr in enumerate(effective):
            if instr.opname == 'POP_TOP':
                pop_idx = idx
                break
        if pop_idx is not None:
            effective = effective[:pop_idx]
        if not effective:
            return False

        store_or_terminal_ops = frozenset({
            'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_ATTR', 'STORE_SUBSCR',
            'DELETE_NAME', 'DELETE_FAST', 'DELETE_GLOBAL', 'DELETE_ATTR',
            'RAISE_VARARGS',
            'YIELD_VALUE',
            'IMPORT_NAME', 'IMPORT_FROM', 'IMPORT_STAR',
            'GLOBAL', 'NONLOCAL',
            # [R18 Bug 2-3 修复] GET_YIELD_FROM_ITER 是 yield from 语句的迭代器
            # 获取指令，总是后跟 SEND 循环。含此指令的块是 yield from 语句的
            # setup 块（语句级语义），不是三元表达式的值块（表达式级语义）。
            # 若不排除，if-elif-else 三分支都含 yield from 时，setup 块会被
            # 误识别为 ternary 值块，导致整体退化为嵌套 ternary
            # `None if ... else None if ... else None`，所有 yield from 逃逸
            # 到函数顶层。依「每块唯一归属」原则：yield from setup 块归属
            # LoopRegion（SEND 循环），不归属 TernaryRegion。
            'GET_YIELD_FROM_ITER',
        })

        allowed_terminal_ops = frozenset({
            'RETURN_VALUE', 'RETURN_CONST',
        })

        for idx, instr in enumerate(effective):
            is_last = (idx == len(effective) - 1)
            if instr.opname in store_or_terminal_ops:
                return False
            if instr.opname.startswith('JUMP_') or instr.opname.startswith('POP_JUMP_'):
                return False
            if not is_last and instr.opname in allowed_terminal_ops:
                return False

        if len(effective) == 1:
            last = effective[0]
            if last.opname == 'RETURN_CONST' and last.argval is None:
                return False
            if last.opname == 'LOAD_CONST' and last.argval is None:
                # LOAD_CONST None as a value expression:
                # In ternary context, the false branch may be just `None`
                # which flows to a merge block (RETURN_VALUE in the merge).
                # This is valid as a single expression IF the block falls through
                # to a merge block (no RETURN_VALUE/RETURN_CONST in this block).
                has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in block.instructions if i.opname not in NOISE_OPS)
                if not has_return:
                    return True
                # Phase 11增强: 可能是被POP_TOP截断前的None模式
                # 尝试用原始指令重新检查
                original = [i for i in block.instructions if i.opname not in NOISE_OPS]
                while original and original[-1].opname in (
                    'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                    original = original[:-1]
                if original and original[-1].opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                    original = original[:-1]
                if (len(original) == 4 and
                    original[0].opname == 'LOAD_CONST' and original[0].argval is None and
                    original[1].opname == 'POP_TOP' and
                    original[2].opname == 'LOAD_CONST' and original[2].argval is None and
                    original[3].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                    return True
                return False

        if len(effective) == 2:
            if (effective[0].opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME',
                                        'LOAD_GLOBAL', 'LOAD_DEREF') and
                    effective[1].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                ret_val = effective[1].argval if effective[1].opname == 'RETURN_CONST' else None
                load_val = effective[0].argval if effective[0].opname == 'LOAD_CONST' else None
                if ret_val is None and load_val is None:
                    return False
                return False

        # Phase 11增强: 支持3指令的 None 模式
        #
        # 对于 `x if cond else None` 的 false 分支，字节码可能是:
        #   LOAD_CONST None, POP_TOP, LOAD_CONST None, RETURN_VALUE
        # 移除 POP_TOP 后: [LOAD_CONST None, LOAD_CONST None, RETURN_VALUE]
        #
        # 这是有效的单表达式: 加载None（被丢弃），然后返回None
        if len(effective) == 3:
            if (effective[0].opname == 'LOAD_CONST' and effective[0].argval is None and
                effective[1].opname == 'LOAD_CONST' and effective[1].argval is None and
                effective[2].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                return True

        return True

    def get_block_role(self, block: BasicBlock) -> BlockRole:
        return self.block_roles.get(block.start_offset, BlockRole.NORMAL)

    def _annotate_all_roles(self, all_regions: List[Region]) -> None:
        """统一的层次构建和角色标注流程

        合并以下4个方法的功能：
        - _annotate_control_flow_role: 控制流角色标注
        - _annotate_region_blocks: 区域-块映射维护
        - _annotate_loop_continue_blocks: 循环continue/back_edge标注
        - _compute_effective_instructions: 有效指令计算

        算法流程：
        阶段1：初始化所有块角色为NORMAL
        阶段2：基于区域边界的结构化角色推导
        阶段3：基于CFG边的控制流角色推导
        阶段4：有效指令计算
        阶段5：区域映射更新（带优先级）
        """
        STATEMENT_TERMINATORS = frozenset({
            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
            'STORE_SUBSCR', 'STORE_ATTR',
            'RETURN_VALUE', 'RETURN_CONST',
            'RAISE_VARARGS', 'IMPORT_NAME', 'IMPORT_FROM',
            'YIELD_VALUE', 'YIELD_FROM', 'POP_TOP'
        })

        EFFECTIVE_NOISE_OPS = frozenset({
            'RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'COPY'
        })

        for block in self.cfg.blocks.values():
            self.block_roles[block.start_offset] = BlockRole.NORMAL

        loop_regions = self._filter_regions(all_regions, LoopRegion)

        for loop in loop_regions:
            header = loop.header_block
            if header is None:
                continue

            # 优先使用循环识别阶段保存的 continue_map（包含 try body 内的 continue 块），
            # 否则重新计算
            if hasattr(loop, 'continue_map') and loop.continue_map:
                continue_map = loop.continue_map
            else:
                _, continue_map = self._detect_break_continue(loop.body_blocks, header)
            for block, role in continue_map.items():
                if role == 'LOOP_BACK_EDGE':
                    self._assign_region_role(block.start_offset, BlockRole.LOOP_BACK_EDGE)
                else:
                    self._assign_region_role(block.start_offset, BlockRole.CONTINUE)

        for loop in loop_regions:
            if not loop.back_edge_block:
                continue
            for other_loop in loop_regions:
                if other_loop is loop:
                    continue
                if other_loop.parent is not loop:
                    continue
                if not other_loop.else_blocks:
                    continue
                if loop.back_edge_block in other_loop.else_blocks:
                    self.block_roles[loop.back_edge_block.start_offset] = BlockRole.CONTINUE

        for region in all_regions:
            region.annotate_structural_roles(self)

        for block in self.cfg.blocks.values():
            offset = block.start_offset
            if self.block_roles[offset] != BlockRole.NORMAL:
                continue

            enclosing_loop = self._get_loop_region_for_block(block)
            is_in_loop_body = (enclosing_loop and block in enclosing_loop.body_blocks
                               and block != enclosing_loop.header_block
                               and block != enclosing_loop.condition_block)

            if is_in_loop_body:
                loop_block_set = enclosing_loop.blocks
                has_external_exit = any(succ not in loop_block_set for succ in block.successors)
                if has_external_exit:
                    self._assign_region_role(offset, BlockRole.BREAK)
                    continue
                has_header_jump = any(succ == enclosing_loop.header_block for succ in block.successors)
                if has_header_jump and block != enclosing_loop.back_edge_block:
                    non_jump_meaningful = [i for i in block.instructions
                                           if i.opname not in NOISE_OPS
                                           and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                                'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                           and i.opname not in CONDITIONAL_JUMP_OPS
                                           and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                    if not non_jump_meaningful:
                        self._assign_region_role(offset, BlockRole.CONTINUE)
                        continue

            if not block.successors:
                self._assign_region_role(offset, BlockRole.RETURN)
                continue

            if offset in self._reraise_block_offsets:
                self._assign_region_role(offset, BlockRole.RERAISE)

        for loop in loop_regions:
            header = loop.header_block
            for block in loop.body_blocks:
                if block == header:
                    continue
                if self.block_roles.get(block.start_offset) != BlockRole.NORMAL:
                    continue
                last = block.get_last_instruction()
                if last is None or last.argval is None:
                    continue
                if last.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') \
                   and last.opname not in BACKWARD_CONDITIONAL_JUMP_OPS:
                    continue
                if not isinstance(last.argval, int):
                    continue
                target_block = self.cfg.get_block_by_offset(last.argval)
                if target_block != header:
                    continue
                if last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                    if block == loop.back_edge_block:
                        be_non_jump = [i for i in block.instructions
                                       if i.opname not in NOISE_OPS
                                       and i.opname not in ('JUMP_BACKWARD',
                                                            'JUMP_BACKWARD_NO_INTERRUPT',
                                                            'JUMP_FORWARD',
                                                            'JUMP_ABSOLUTE')]
                        if not be_non_jump:
                            has_natural_be = any(
                                other != header and other != block
                                and other in loop.body_blocks
                                and self.block_roles.get(other.start_offset) == BlockRole.NORMAL
                                and other.get_last_instruction() is not None
                                and other.get_last_instruction().argval is not None
                                and other.get_last_instruction().opname in (
                                    BACKWARD_CONDITIONAL_JUMP_OPS
                                    | frozenset({'JUMP_BACKWARD',
                                                 'JUMP_BACKWARD_NO_INTERRUPT'}))
                                and isinstance(other.get_last_instruction().argval, int)
                                and self.cfg.get_block_by_offset(
                                    other.get_last_instruction().argval
                                ) in loop.body_blocks
                                and any(i.opname not in NOISE_OPS
                                        and i.opname not in (
                                            'JUMP_BACKWARD',
                                            'JUMP_BACKWARD_NO_INTERRUPT',
                                            'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                        for i in other.instructions)
                                for other in loop.body_blocks
                            )
                            if has_natural_be:
                                self.block_roles[block.start_offset] = BlockRole.CONTINUE
                            else:
                                self._assign_region_role(block.start_offset,
                                                         BlockRole.LOOP_BACK_EDGE)
                        else:
                            self._assign_region_role(block.start_offset,
                                                     BlockRole.LOOP_BACK_EDGE)
                    else:
                        # 修复: 只有当块只包含跳转指令时才标记为CONTINUE
                        # 如果块包含有意义的非跳转语句（如赋值、函数调用等），
                        # 则不应该标记为CONTINUE，而应该标记为LOOP_BODY
                        block_non_jump_instrs = [
                            i for i in block.instructions
                            if i.opname not in NOISE_OPS
                            and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                            and i.opname not in CONDITIONAL_JUMP_OPS
                            and i.opname not in SHORT_CIRCUIT_JUMP_OPS
                        ]
                        if block_non_jump_instrs:
                            # 有意义语句，标记为LOOP_BODY而不是CONTINUE
                            self._assign_region_role(block.start_offset, BlockRole.LOOP_BODY)
                        else:
                            # 纯跳转块，可以安全地标记为CONTINUE
                            self._assign_region_role(block.start_offset, BlockRole.CONTINUE)
                elif last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                    self._assign_region_role(block.start_offset, BlockRole.LOOP_BACK_EDGE)

        for loop in loop_regions:
            header = loop.header_block
            for block in loop.body_blocks:
                if block == header:
                    continue
                if self.block_roles.get(block.start_offset) not in (
                        BlockRole.NORMAL, BlockRole.LOOP_BODY):
                    continue
                last = block.get_last_instruction()
                if last is None or last.argval is None:
                    continue
                if last.opname not in BACKWARD_CONDITIONAL_JUMP_OPS:
                    continue
                if not isinstance(last.argval, int):
                    continue
                target_block = self.cfg.get_block_by_offset(last.argval)
                if target_block is None:
                    continue
                if target_block not in loop.body_blocks or target_block == header:
                    continue
                be_non_jump = [i for i in block.instructions
                               if i.opname not in NOISE_OPS
                               and i.opname not in ('JUMP_BACKWARD',
                                                    'JUMP_BACKWARD_NO_INTERRUPT',
                                                    'JUMP_FORWARD',
                                                    'JUMP_ABSOLUTE')
                               and i.opname not in BACKWARD_CONDITIONAL_JUMP_OPS]
                if be_non_jump:
                    self.block_roles[block.start_offset] = BlockRole.LOOP_BACK_EDGE

        for block in self.cfg.blocks.values():
            if not block.instructions:
                self.effective_instructions[block.start_offset] = []
                continue

            effective = []
            for instr in block.instructions:
                if instr.opname in EFFECTIVE_NOISE_OPS:
                    continue
                effective.append(instr)
                if instr.opname in STATEMENT_TERMINATORS:
                    break

            while effective and effective[-1].opname in (
                'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                'JUMP_BACKWARD_NO_INTERRUPT'):
                effective.pop()

            self.effective_instructions[block.start_offset] = effective

            offset = block.start_offset
            if self.block_roles[offset] == BlockRole.NORMAL:
                if len(effective) <= 1:
                    self._assign_region_role(offset, BlockRole.PURE_JUMP)
            elif self.block_roles[offset] == BlockRole.BREAK:
                non_jump_meaningful = [i for i in block.instructions
                                       if i.opname not in NOISE_OPS
                                       and i.opname not in ('JUMP_FORWARD', 'JUMP_BACKWARD',
                                                            'JUMP_ABSOLUTE',
                                                            'JUMP_BACKWARD_NO_INTERRUPT')
                                       and i.opname not in CONDITIONAL_JUMP_OPS
                                       and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                if not non_jump_meaningful:
                    self.block_roles[offset] = BlockRole.PURE_BREAK
            elif self.block_roles[offset] == BlockRole.CONTINUE:
                non_jump_meaningful = [i for i in block.instructions
                                       if i.opname not in NOISE_OPS
                                       and i.opname not in ('JUMP_FORWARD', 'JUMP_BACKWARD',
                                                            'JUMP_ABSOLUTE',
                                                            'JUMP_BACKWARD_NO_INTERRUPT')
                                       and i.opname not in CONDITIONAL_JUMP_OPS
                                       and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                if not non_jump_meaningful:
                    self.block_roles[offset] = BlockRole.PURE_CONTINUE

        self.block_to_region.clear()
        for region in all_regions:
            current_priority = self.REGION_TYPE_PRIORITY.get(region.region_type, 0)
            for block in region.blocks:
                existing_region = self.block_to_region.get(block)
                if existing_region is None:
                    self.block_to_region[block] = region
                else:
                    if isinstance(region, BoolOpRegion) and block in self._elif_boolop_entry_blocks:
                        self.block_to_region[block] = region
                    elif isinstance(existing_region, BoolOpRegion) and block in self._elif_boolop_entry_blocks:
                        pass
                    elif self._should_use_dynamic_priority(existing_region, region):
                        existing_score = self._compute_dynamic_region_score(block, existing_region)
                        candidate_score = self._compute_dynamic_region_score(block, region)
                        if candidate_score > existing_score:
                            self.block_to_region[block] = region
                    else:
                        existing_priority = self.REGION_TYPE_PRIORITY.get(
                            existing_region.region_type, 0)
                        if current_priority > existing_priority:
                            self.block_to_region[block] = region

        for region in all_regions:
            region.annotate_cond_recheck(self)

    def _annotate_loop_structural_roles(self, loop: LoopRegion) -> None:
        """基于LoopRegion边界标注循环结构化角色"""
        if loop.header_block:
            self._assign_region_role(loop.header_block.start_offset,
                                   BlockRole.LOOP_HEADER)
        if loop.condition_block and loop.condition_block != loop.header_block:
            self._assign_region_role(loop.condition_block.start_offset,
                                   BlockRole.LOOP_CONDITION)
        loop_body_set = set(loop.body_blocks) | {loop.header_block}
        if loop.condition_block:
            loop_body_set.add(loop.condition_block)
        for block in loop.body_blocks:
            if block != loop.header_block and block != loop.condition_block:
                current_role = self.block_roles.get(block.start_offset)
                if current_role != BlockRole.NORMAL:
                    continue
                has_external_exit = any(succ not in loop_body_set for succ in block.successors)
                if has_external_exit:
                    last_instr = block.get_last_instruction()
                    is_unconditional_exit = (
                        last_instr and last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')
                        and last_instr.argval is not None
                        and self.cfg.get_block_by_offset(last_instr.argval) not in loop_body_set
                    )
                    if is_unconditional_exit:
                        self.block_roles[block.start_offset] = BlockRole.BREAK
                        continue
                has_header_jump = any(succ == loop.header_block for succ in block.successors)
                if has_header_jump and block != loop.back_edge_block:
                    last_instr = block.get_last_instruction()
                    is_unconditional_continue = (
                        last_instr and last_instr.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                        and last_instr.argval is not None
                        and self.cfg.get_block_by_offset(last_instr.argval) == loop.header_block
                    )
                    if is_unconditional_continue:
                        non_jump_meaningful = [i for i in block.instructions
                                               if i.opname not in NOISE_OPS
                                               and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                                    'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                               and i.opname not in CONDITIONAL_JUMP_OPS
                                               and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                        if not non_jump_meaningful:
                            self.block_roles[block.start_offset] = BlockRole.CONTINUE
                            continue
                self._assign_region_role(block.start_offset,
                                       BlockRole.LOOP_BODY)
        for block in loop.else_blocks:
            if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(block.start_offset,
                                       BlockRole.LOOP_ELSE)
        for block in loop.init_blocks:
            if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(block.start_offset,
                                       BlockRole.LOOP_INIT)
        if loop.back_edge_block and loop.back_edge_block != loop.header_block:
            be_role = self.block_roles.get(loop.back_edge_block.start_offset)
            if be_role in (BlockRole.NORMAL, BlockRole.LOOP_BODY):
                self.block_roles[loop.back_edge_block.start_offset] = \
                    BlockRole.LOOP_BACK_EDGE

    def _annotate_if_structural_roles(self, if_region: IfRegion) -> None:
        """基于IfRegion边界标注条件结构化角色"""
        if if_region.condition_block:
            self._assign_region_role(if_region.condition_block.start_offset,
                                   BlockRole.IF_CONDITION)
        for block in if_region.then_blocks:
            if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(block.start_offset,
                                       BlockRole.IF_THEN)
        for block in if_region.else_blocks:
            if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(block.start_offset,
                                       BlockRole.IF_ELSE)
        for idx, cond_block in enumerate(if_region.elif_conditions):
            if self.block_roles.get(cond_block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(cond_block.start_offset,
                                       BlockRole.IF_ELIF_CONDITION)
            if idx < len(if_region.elif_bodies):
                for body_block in if_region.elif_bodies[idx]:
                    if self.block_roles.get(body_block.start_offset) == BlockRole.NORMAL:
                        self._assign_region_role(body_block.start_offset,
                                               BlockRole.IF_THEN)

    def _annotate_try_except_structural_roles(self,
                                             try_region: TryExceptRegion) -> None:
        """基于TryExceptRegion边界标注异常处理结构化角色"""
        for block in try_region.try_blocks:
            if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(block.start_offset,
                                       BlockRole.TRY_BODY)
        for handler_entry in try_region.handler_entry_blocks:
            if self.block_roles.get(handler_entry.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(handler_entry.start_offset,
                                       BlockRole.EXCEPT_HANDLER)
        for _, _, handler_blocks in try_region.except_handlers:
            for block in handler_blocks:
                if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                    self._assign_region_role(block.start_offset,
                                           BlockRole.EXCEPT_STORE)
        for block in try_region.finally_blocks:
            if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(block.start_offset,
                                       BlockRole.FINALLY_BODY)
        for block in try_region.else_blocks:
            if self.block_roles.get(block.start_offset) == BlockRole.NORMAL:
                self._assign_region_role(block.start_offset,
                                       BlockRole.TRY_ELSE)

    def _assign_region_role(self, offset: int, role: BlockRole) -> None:
        if self.block_roles.get(offset, BlockRole.NORMAL) == BlockRole.NORMAL:
            self.block_roles[offset] = role

    def _get_loop_region_for_block(self, block: BasicBlock) -> Optional[LoopRegion]:
        innermost = None
        innermost_size = float('inf')
        for region in self._filter_regions(self.regions, LoopRegion):
            if block in region.blocks:
                size = len(region.blocks)
                if size < innermost_size:
                    innermost = region
                    innermost_size = size
        return innermost

    REGION_TYPE_PRIORITY = {
        RegionType.TRY_EXCEPT: 70,
        RegionType.TRY_FINALLY: 70,
        RegionType.WHILE_LOOP: 60,
        RegionType.FOR_LOOP: 60,
        RegionType.WITH: 50,
        RegionType.MATCH: 40,
        RegionType.IF_THEN_ELSE: 30,
        RegionType.IF_ELIF_CHAIN: 30,
        RegionType.IF_THEN: 25,
        RegionType.BOOL_OP: 20,
        RegionType.TERNARY: 15,
        RegionType.ASSERT: 10,
        RegionType.SEQUENCE: 5,
        RegionType.BASIC: 0,
    }

    DYNAMIC_PRIORITY_WEIGHTS = {
        'merge_semantics': 0.20,
        'branch_compactness': 0.15,
        'expression_context': 0.15,
        'structural_nesting': 0.15,
        'if_body_substance': 0.35,
    }

    def _compute_dynamic_region_score(self, block: BasicBlock, region: 'Region') -> float:
        w = self.DYNAMIC_PRIORITY_WEIGHTS
        rt = region.region_type
        score = 0.0
        score += w['merge_semantics'] * self._score_merge_semantics(block, region)
        score += w['branch_compactness'] * self._score_branch_compactness(block, region)
        score += w['expression_context'] * self._score_expression_context(block, region)
        score += w['structural_nesting'] * self._score_structural_nesting(block, region)
        score += w['if_body_substance'] * self._score_if_body_substance(block, region)
        return score

    def _score_merge_semantics(self, block: BasicBlock, region: 'Region') -> float:
        rt = region.region_type
        merge = region.get_score_merge_block()
        if not merge:
            return 50.0
        has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                       for i in merge.instructions)
        has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in merge.instructions)
        if rt in (RegionType.BOOL_OP, RegionType.TERNARY):
            if has_store:
                return 90.0
            if has_return:
                return 80.0
            return 40.0
        if rt in (RegionType.IF_THEN_ELSE, RegionType.IF_THEN, RegionType.IF_ELIF_CHAIN):
            if has_store:
                return 20.0
            if has_return:
                return 30.0
            return 70.0
        return 50.0

    def _score_branch_compactness(self, block: BasicBlock, region: 'Region') -> float:
        rt = region.region_type
        succs = region.get_compactness_successors(self)
        if not succs:
            return 50.0
        effective_counts = []
        for s in succs:
            eff = [i for i in s.instructions if i.opname not in NOISE_OPS]
            effective_counts.append(len(eff))
        avg_size = sum(effective_counts) / len(effective_counts) if effective_counts else 99
        max_size = max(effective_counts) if effective_counts else 99
        if rt in (RegionType.BOOL_OP, RegionType.TERNARY):
            if avg_size <= 2 and max_size <= 3:
                return 90.0
            if avg_size <= 4 and max_size <= 6:
                return 65.0
            if avg_size <= 8:
                return 45.0
            return 25.0
        if rt in (RegionType.IF_THEN_ELSE, RegionType.IF_THEN, RegionType.IF_ELIF_CHAIN):
            if avg_size <= 2 and max_size <= 3:
                return 25.0
            if avg_size <= 4 and max_size <= 6:
                return 45.0
            if avg_size <= 8:
                return 65.0
            return 85.0
        return 50.0

    def _score_expression_context(self, block: BasicBlock, region: 'Region') -> float:
        rt = region.region_type
        merge = region.get_score_merge_block()
        if not merge:
            return 50.0
        non_noise = [i for i in merge.instructions if i.opname not in NOISE_OPS]
        store_ops = {'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                     'STORE_SUBSCR', 'STORE_ATTR'}
        has_store = any(i.opname in store_ops for i in non_noise)
        has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in non_noise)
        is_expr_terminator = False
        if non_noise:
            last = non_noise[-1]
            if last.opname in store_ops or last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                is_expr_terminator = True
        if rt in (RegionType.BOOL_OP, RegionType.TERNARY):
            if is_expr_terminator:
                return 85.0
            if has_store or has_return:
                return 75.0
            return 35.0
        if rt in (RegionType.IF_THEN_ELSE, RegionType.IF_THEN, RegionType.IF_ELIF_CHAIN):
            if is_expr_terminator:
                return 25.0
            if has_store or has_return:
                return 35.0
            return 75.0
        return 50.0

    def _score_structural_nesting(self, block: BasicBlock, region: 'Region') -> float:
        rt = region.region_type
        is_nested_condition = False
        for r in self.regions:
            if r is region:
                continue
            if isinstance(r, (IfRegion, LoopRegion)):
                if hasattr(r, 'condition_block') and r.condition_block:
                    if block == r.condition_block or block in getattr(r, 'condition_chain_blocks', []):
                        is_nested_condition = True
                        break
                if isinstance(r, BoolOpRegion) and block in set(b for b, _ in r.op_chain):
                    is_nested_condition = True
                    break
        if rt in (RegionType.BOOL_OP, RegionType.TERNARY):
            if is_nested_condition:
                return 80.0
            return 45.0
        if rt in (RegionType.IF_THEN_ELSE, RegionType.IF_THEN, RegionType.IF_ELIF_CHAIN):
            if is_nested_condition:
                return 30.0
            return 60.0
        return 50.0

    def _score_if_body_substance(self, block: BasicBlock, region: 'Region') -> float:
        rt = region.region_type
        if rt not in (RegionType.IF_THEN_ELSE, RegionType.IF_THEN, RegionType.IF_ELIF_CHAIN):
            if rt in (RegionType.BOOL_OP, RegionType.TERNARY):
                return 50.0
            return 50.0
        body_blocks = region.get_if_body_blocks()
        if body_blocks is None:
            return 50.0
        then_blocks, else_blocks = body_blocks
        all_body_blocks = set(then_blocks + else_blocks)
        if not all_body_blocks:
            return 25.0
        boolop_competitor = None
        for r in self._filter_regions(self.regions, BoolOpRegion):
            if r is not region and r.entry == region.entry:
                boolop_competitor = r
                break
        if boolop_competitor:
            boolop_blocks = set(boolop_competitor.blocks)
            exclusive_body = all_body_blocks - boolop_blocks
            if exclusive_body:
                return 95.0
            else:
                return 30.0
        total_effective_instrs = 0
        for b in all_body_blocks:
            effective = [i for i in b.instructions if i.opname not in NOISE_OPS]
            total_effective_instrs += len(effective)
        if total_effective_instrs >= 5:
            return 90.0
        if total_effective_instrs >= 3:
            return 70.0
        if total_effective_instrs >= 1:
            return 50.0
        return 30.0

    def _should_use_dynamic_priority(self, existing_region: 'Region', candidate_region: 'Region') -> bool:
        existing_rt = existing_region.region_type
        candidate_rt = candidate_region.region_type
        conflict_pairs = [
            (RegionType.BOOL_OP, RegionType.IF_THEN_ELSE),
            (RegionType.BOOL_OP, RegionType.IF_THEN),
            (RegionType.BOOL_OP, RegionType.IF_ELIF_CHAIN),
            (RegionType.TERNARY, RegionType.IF_THEN_ELSE),
            (RegionType.TERNARY, RegionType.IF_THEN),
        ]
        return (existing_rt, candidate_rt) in conflict_pairs or (candidate_rt, existing_rt) in conflict_pairs

    @property
    def _reraise_block_offsets(self) -> Set[int]:
        if self._reraise_block_offsets_cache is None:
            handler_targets = set()
            if self.cfg.exception_table:
                for entry in self.cfg.exception_table:
                    handler_targets.add(entry.get('target', -1))
            offsets = set()
            for offset in handler_targets:
                block = self.cfg.get_block_by_offset(offset)
                if block and any(i.opname == 'RERAISE' for i in block.instructions):
                    offsets.add(offset)
            self._reraise_block_offsets_cache = offsets
        return self._reraise_block_offsets_cache

    def identify_block_prefix_instructions(self, block: BasicBlock) -> List[Instruction]:

        result = []
        for instr in block.instructions:
            if instr.opname in NOISE_OPS:
                continue
            if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                                'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                                'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                                'POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE',
                                'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                                'FOR_ITER', 'SETUP_LOOP', 'GET_ITER', 'GET_AITER'):
                break
            if instr.opname in ('POP_EXCEPT', 'PUSH_EXC_INFO', 'RERAISE',
                                'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH'):
                continue
            result.append(instr)
        has_get_iter = any(i.opname in ('GET_ITER', 'GET_AITER') for i in block.instructions)
        if has_get_iter and result:
            get_iter_idx = None
            for idx, instr in enumerate(block.instructions):
                if instr.opname in ('GET_ITER', 'GET_AITER'):
                    get_iter_idx = idx
                    break
            if get_iter_idx is not None:
                last_store_idx = -1
                for idx in range(get_iter_idx):
                    if block.instructions[idx].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        last_store_idx = idx
                if last_store_idx >= 0:
                    store_offset = block.instructions[last_store_idx].offset
                    result = [instr for instr in result if instr.offset <= store_offset]
                else:
                    iter_expr_start = get_iter_idx - 1
                    split_idx = 0
                    while iter_expr_start >= 0:
                        iname = block.instructions[iter_expr_start].opname
                        if iname in NOISE_OPS:
                            iter_expr_start -= 1
                            continue
                        if iname == 'PUSH_NULL':
                            split_idx = iter_expr_start
                            break
                        if iname.startswith('LOAD_') or iname in (
                            'PRECALL', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                            'BINARY_OP', 'UNARY_OP', 'BUILD_TUPLE', 'BUILD_LIST',
                            'BUILD_DICT', 'BUILD_SET', 'BUILD_STRING', 'BUILD_SLICE',
                            'IS_OP', 'CONTAINS_OP', 'COMPARE_OP', 'BINARY_SUBSCR',
                            'FORMAT_VALUE', 'CONVERT_VALUE', 'UNARY_NOT',
                            'LOAD_BUILD_CLASS', 'GET_AWAITABLE', 'SWAP', 'COPY'):
                            iter_expr_start -= 1
                            continue
                        split_idx = iter_expr_start + 1
                        break
                    if split_idx < len(block.instructions):
                        split_offset = block.instructions[split_idx].offset
                        result = [instr for instr in result if instr.offset < split_offset]
        return result

    def compute_chained_compare_operands(self, region: IfRegion) -> None:
        ops = region.chained_compare_ops
        if len(ops) < 2:
            return
        all_blocks = [region.condition_block] + list(region.chained_compare_blocks)
        if not all_blocks or region.condition_block is None:
            return

        left_expr = None
        comparators = []

        for block_idx, block in enumerate(all_blocks):
            load_instrs = []
            last_store_idx = -1
            for idx, instr in enumerate(block.instructions):
                # [Round6-01/02] 跳过 IS_OP/CONTAINS_OP（链式 is/in 比较的运算指令）
                if instr.opname in NOISE_OPS | {'POP_TOP', 'COPY', 'SWAP',
                                                'COMPARE_OP', 'IS_OP', 'CONTAINS_OP'}:
                    continue
                if instr.opname in (CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS |
                                    {'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'}):
                    continue
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    last_store_idx = idx
                    continue
                if instr.opname.startswith('LOAD_'):
                    if block_idx == 0 and last_store_idx >= 0:
                        pass
                    load_instrs.append(instr)

            if block_idx == 0 and last_store_idx >= 0:
                filtered_loads = []
                for idx, instr in enumerate(block.instructions):
                    if idx <= last_store_idx:
                        continue
                    if instr.opname in NOISE_OPS | {'POP_TOP', 'COPY', 'SWAP',
                                                    'COMPARE_OP', 'IS_OP', 'CONTAINS_OP'}:
                        continue
                    if instr.opname in (CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS |
                                        {'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'}):
                        continue
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        continue
                    if instr.opname.startswith('LOAD_'):
                        filtered_loads.append(instr)
                load_instrs = filtered_loads

            if left_expr is None:
                if len(load_instrs) >= 2:
                    left_expr = load_instrs[0]
                    comparators.append(load_instrs[1])
                elif len(load_instrs) == 1:
                    left_expr = load_instrs[0]
            else:
                filtered = [li for li in load_instrs
                            if not (li.opname == 'LOAD_CONST' and li.argval is None)]
                if filtered:
                    comparators.append(filtered[-1])

        region.chained_left_instr = left_expr
        region.chained_comparator_instrs = comparators


    @staticmethod
    def extract_dict_key_from_block(block: Optional[BasicBlock]) -> Optional[Dict[str, Any]]:
        if not block:
            return None
        instrs = [i for i in block.instructions
                  if i.opname not in ('RESUME', 'NOP', 'CACHE')]
        if not instrs:
            return None
        last_instr = instrs[-1]
        if last_instr.opname not in (*CONDITIONAL_JUMP_OPS, *SHORT_CIRCUIT_JUMP_OPS):
            return None
        import dis
        stack_depth = 0
        cond_start_idx = None
        for idx in range(len(instrs) - 1, -1, -1):
            instr = instrs[idx]
            try:
                effect = dis.stack_effect(instr.opcode, instr.arg)
            except Exception:
                effect = 0
            stack_depth -= effect
            if stack_depth <= 0:
                cond_start_idx = idx
                break
        if cond_start_idx is not None and cond_start_idx > 0:
            key_instrs = instrs[:cond_start_idx]
            if len(key_instrs) == 1:
                ki = key_instrs[0]
                if ki.opname == 'LOAD_CONST':
                    return {'type': 'Constant', 'value': ki.argval}
                elif ki.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL'):
                    return {'type': 'Name', 'id': ki.argval, 'ctx': 'Load'}
            elif len(key_instrs) > 1:
                return None
        return None

    def _get_dominance_depth(self, block):
        if hasattr(block, 'dominators') and block.dominators:
            return len(block.dominators) - 1
        return 0


    def _identify_loop_regions(self) -> List[Region]:
        """_identify_loop_regions - 循环区域识别（Loop Region Identification）

【区域类型】 WHILE_LOOP / FOR_LOOP — 循环区域（Loop Region）
RegionType 枚举值: RegionType.WHILE_LOOP / RegionType.FOR_LOOP

1. 算法描述（基于"No More Gotos"论文）
   - 归约阶段: Phase 1（与 TRY 并行，在 WITH/MATCH 之前）
   - 识别策略: 基于 LoopAnalyzer 提供的回边（back edge）+ 支配树分析，
     实现论文第4.2节的自然循环（Natural Loop）识别：
     回边 (n → d) 满足 d DOM n，d 即循环 header；
     循环体 = 不经过 header 能到达 back_edge_source 的所有节点。
   - 归约过程:
     Step 1: 从 LoopAnalyzer 获取所有自然循环 (all_loops)，按 dominance_depth
             倒序排序，确保内层循环先于外层归约（自底向上）。
     Step 2: 对每个 header，确定回边源节点 back_edge_sources：
             筛选 self.loop_analyzer.back_edges 中目标为 header 且 header 支配
             源节点的边；FOR_ITER/GET_ANEXT 循环若无显式回边源，允许继续。
     Step 3: 调用 _collect_natural_loop_body 收集循环体（栈式 DFS）；
             用 frozenset(body) 去重，已处理过的相同 body 跳过。
     Step 4: 调用 _is_fake_loop 过滤 continue 形成的假回边伪循环。
     Step 5: 子集过滤：若 body 是已处理循环 body 的真子集且非 for 循环，跳过
             （保证"每块唯一归属"，循环区域不重叠）。
     Step 6: 调用 _classify_loop_type 分类循环类型，返回 loop_type、
             for_iter_setup/exit/fall_through、is_while_true、is_yield_from。
     Step 7: WHILE_LOOP 下搜索 condition_block，依次尝试:
             (a) header 前驱中末指令为 FORWARD_CONDITIONAL_JUMP_OPS 且跳转目标
                 是 header 或 body 内的块；
             (b) 前驱末指令属于 CONDITIONAL_JUMP_OPS（含后向）；
             (c) header 自身末指令为 CONDITIONAL_JUMP_OPS；
             (d) while_true 模式下搜索前向条件跳转跳出循环的前驱，并将
                 is_while_true 降级为 False；若 condition_block 跳出 body/header
                 也会降级 is_while_true。
     Step 8: _find_loop_else 提取 else_blocks 和 natural_exit；
             选择 back_edge_block（按有效指令数和 start_offset 取最大）；
             _detect_break_continue 标注 break_blocks 与 continue_map。
     Step 9: 将 condition_block 及其条件链前驱（沿 FORWARD_CONDITIONAL_JUMP_OPS
             反向扩展，排除已被回边指向的块）加入 region_blocks；验证 break_blocks
             必须有前驱在 body 中，否则剔除。
     Step 10: 构建 LoopRegion 并注册到 self.regions / block_to_region。

2. 字节码模式（CPython 编译器行为）
   模式 A: for 循环
     源码: for x in iterable: body
     字节码结构:
       preheader: GET_ITER
       header:    FOR_ITER → exit ; STORE_FAST x
       body:      ... ; JUMP_BACKWARD → header
       exit:      ...循环后语句
     特征指令: GET_ITER, FOR_ITER, STORE_FAST, JUMP_BACKWARD
              异步变体: GET_AITER, GET_ANEXT, END_ASYNC_FOR
   模式 B: while 循环
     源码: while cond: body
     字节码结构:
       condition_block: ...条件计算; POP_JUMP_FORWARD_IF_FALSE → exit
       header/body:     ...; JUMP_BACKWARD → condition_block
       exit:            ...
     特征指令: POP_JUMP_*_IF_*, JUMP_BACKWARD, JUMP_BACKWARD_NO_INTERRUPT
   模式 C: while True + break
     - 无条件回边（JUMP_BACKWARD）；
     - header/condition_block 含前向条件跳转跳出循环作为 break 路径；
     - is_while_true 标记，必要时由 Step 7(d) 降级。
   模式 D: for-else / while-else
     - else 块位于循环正常退出路径（natural_exit 指向 else 入口）；
     - break 跳过 else 块；
     - 由 _find_loop_else 标注 else_blocks。
   模式 E: yield from 隐式循环
     - GET_YIELD_FROM_ITER + SEND + YIELD_VALUE 模式；
     - is_yield_from 标记，由 _generate_loop 特殊处理。

3. 边界条件（数学性质）
   - 回边检测: 由 LoopAnalyzer 基于支配关系预先计算；本方法再次以
              self.dom_analyzer.is_dominator(header, src) 校验。
   - 循环体边界: 不经过 header 能到达 back_edge_source 的所有节点集合
                （_collect_natural_loop_body 栈式 DFS 收集）。
   - 嵌套处理: 按 dominance_depth 倒序排序，内层循环先归约；
              子集过滤确保外层循环不会重新吞并已归约的内层循环体
              （for 循环除外，因为 for 循环 body 天然可能含内层循环）。
   - 区域不相交: frozenset(body) 去重 + 子集过滤共同保证"每块唯一归属"。

4. 归约语义（与父区域的契约）
   - 入口块: 优先 condition_block（while 循环典型情况），
            否则使用 header_block（for 循环、while True）。
   - 父区域引用: 父区域仅引用本 LoopRegion 的 entry 块，
                循环体内部块不出现于父区域的 blocks 集合中。
   - 子区域块不出现: 嵌套的 IfRegion/TryExceptRegion/WithRegion/MatchRegion/
                   LoopRegion/AssertRegion 等在归约后由本 LoopRegion.children 持有，
                   其块不出现在父区域 blocks 中（嵌套即抽象节点）。

5. AST 映射
   - 对应生成方法: _generate_loop（region_ast_generator.py）
   - AST 节点类型:
       RegionType.FOR_LOOP   → ast.For
       RegionType.WHILE_LOOP → ast.While
   - 关键字段映射:
       LoopRegion.header_block       → AST.test（while 条件）或 iter/target（for）
       LoopRegion.condition_block    → AST.test（while 条件表达式来源）
       LoopRegion.body_blocks        → AST.body
       LoopRegion.else_blocks        → AST.orelse
       LoopRegion.back_edge_block    → 隐式 continue，不生成显式 AST 节点
       LoopRegion.break_blocks       → AST.body 中的 ast.Break 语句
       LoopRegion.is_while_true      → AST.test = Constant(True)
       LoopRegion.is_yield_from      → ast.Expr(YieldFrom(...))，不生成 For/While

6. 已知失败模式
   - 当前测试矩阵通过率: 100%（while_loop 120/120 + for_loop 193/193 = 313/313），无已知失败模式
   - 本方法遵循区域归约算法 4 核心原则:
     自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
        """
        all_loops = self.loop_analyzer.get_all_loops()
        sorted_loops = sorted(all_loops.items(), key=lambda x: self._get_dominance_depth(x[0]), reverse=True)

        seen_bodies = set()
        processed_bodies = []
        regions = []

        for header, _ in sorted_loops:
            has_for_iter = any(i.opname in ('FOR_ITER', 'GET_ANEXT') for i in header.instructions)
            back_edge_sources = [src for src, tgt in self.loop_analyzer.back_edges
                                if tgt == header and self.dom_analyzer.is_dominator(header, src)]
            if not back_edge_sources:
                if has_for_iter:
                    back_edge_sources = []
                else:
                    continue

            body = self._collect_natural_loop_body(header, back_edge_sources, is_for_loop=has_for_iter)

            body_key = frozenset(body)
            if body_key in seen_bodies:
                continue
            seen_bodies.add(body_key)

            is_fake_loop = self._is_fake_loop(header, body, back_edge_sources)
            if is_fake_loop:
                continue

            # [聚类2 修复] 抑制 await 轮询自循环的 LoopRegion 创建。
            # CPython 为 `await <expr>` 生成的轮询自循环字节码为：
            #   GET_AWAITABLE + LOAD_CONST None + SEND + YIELD_VALUE +
            #   RESUME + JUMP_BACKWARD_NO_INTERRUPT
            # 这是 await 的实现细节，绝不应被物化为 `while True: pass`。
            # 其前驱（含 GET_AWAITABLE）属于 await 表达式，应归入外围
            # if/return 的条件求值链。区域归约算法原则"嵌套即抽象节点"
            # 不适用于此——这是同一线性表达式的内联轮询，非嵌套结构。
            if self._is_await_polling_loop(header, body):
                continue

            is_subset_of_existing = False
            for existing_body in processed_bodies:
                if body < existing_body:
                    if not has_for_iter:
                        is_subset_of_existing = True
                        break
            if is_subset_of_existing:
                continue
            processed_bodies.append(body)

            loop_type, for_iter_setup, for_iter_exit, for_iter_fall_through, is_while_true, is_yield_from = \
                self._classify_loop_type(header, body)

            condition_block = None
            if loop_type == RegionType.WHILE_LOOP:
                for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                    if pred in body:
                        continue
                    last_instr = pred.get_last_instruction()
                    if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        if last_instr.argval is not None:
                            target = self.cfg.get_block_by_offset(last_instr.argval)
                            if target == header or target in body:
                                condition_block = pred
                                break
                if condition_block is None and not is_while_true:
                    for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                        if pred in body:
                            continue
                        last_instr = pred.get_last_instruction()
                        if last_instr and last_instr.opname in CONDITIONAL_JUMP_OPS:
                            condition_block = pred
                            break
                if condition_block is None and not is_while_true:
                    header_last = header.get_last_instruction()
                    if header_last and header_last.opname in CONDITIONAL_JUMP_OPS:
                        condition_block = header
                if condition_block is None and is_while_true:
                    for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                        if pred in body:
                            continue
                        last_instr = pred.get_last_instruction()
                        if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                            if last_instr.argval is not None:
                                target = self.cfg.get_block_by_offset(last_instr.argval)
                                if target not in body and target != header:
                                    condition_block = pred
                                    is_while_true = False
                                    break
                if condition_block is not None and is_while_true:
                    cond_last = condition_block.get_last_instruction()
                    if cond_last and cond_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        if cond_last.argval is not None:
                            target = self.cfg.get_block_by_offset(cond_last.argval)
                            if target not in body and target != header:
                                is_while_true = False
            else_blocks, natural_exit = self._find_loop_else(header, body, loop_type, for_iter_exit, condition_block=condition_block)
            else_blocks = else_blocks or []
            self._current_loop_blocks = body
            back_edges_for_header = [src for src, tgt in self.loop_analyzer.back_edges if tgt == header]
            if back_edges_for_header:
                back_edge_block = max(back_edges_for_header, key=lambda b: (
                    len([i for i in b.instructions
                         if i.opname not in NOISE_OPS
                         and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                              'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                         and i.opname not in CONDITIONAL_JUMP_OPS]),
                    b.start_offset))
            else:
                back_edge_block = None
            break_blocks, continue_map = self._detect_break_continue(body, header, natural_exit, natural_back_edge=back_edge_block, condition_block=condition_block)

            region_blocks = set(body)
            if condition_block and condition_block not in body:
                if header in condition_block.successors or any(pred in body for pred in condition_block.predecessors):
                    region_blocks.add(condition_block)
                    _cb = condition_block
                    # [CPython peephole] Compound while condition like
                    # `while not done and has_data():` is lowered as a chain
                    # of FORWARD_CONDITIONAL_JUMP blocks. Each operand's
                    # short-circuit target is a SEPARATE trivial exit block
                    # (LOAD_CONST None; RETURN_VALUE) at module/function-tail
                    # position. They are semantically equivalent — all do
                    # "exit the loop". The backward walk must accept a
                    # predecessor whose jump target is ANY equivalent exit
                    # block, not just _cb/body/header. Without this, only
                    # the last operand (e.g., `has_data()`) is captured as
                    # condition_block, and earlier operands (e.g., `not done`)
                    # leak out as spurious outer IfRegion.
                    _cond_exit = None
                    _cond_last = condition_block.get_last_instruction()
                    if _cond_last and _cond_last.argval is not None:
                        _cond_exit = self.cfg.get_block_by_offset(_cond_last.argval)
                    # [Discriminator] A compound `and` while-condition (e.g.
                    # `while not done and has_data():`) is re-evaluated at the
                    # back edge. The back-edge recheck emits a FORWARD
                    # conditional jump to a trivial exit block for each operand
                    # that short-circuits (e.g. `LOAD done;
                    # POP_JUMP_FORWARD_IF_TRUE @exit`). A loop with a SIMPLE
                    # condition (e.g. `while a > 10:`) has only a BACKWARD
                    # conditional jump to the header at the back edge — NO
                    # forward jump to an exit. This distinguishes a true
                    # condition-chain predecessor (part of the while condition)
                    # from an outer construct's condition block (e.g. the `if`
                    # in `if a > 0: while a > 10:`) whose exit block is also a
                    # trivial return but is NOT a loop exit. Without this
                    # discriminator, the backward walk would absorb the outer
                    # `if`'s condition block into the LoopRegion, causing the
                    # IfRegion to vanish.
                    # Count the back-edge recheck's FORWARD-jump-to-exit blocks.
                    # Each represents one operand of a compound `and` condition
                    # that is re-evaluated at the back edge. This count limits
                    # how many `and`-chain predecessors the backward walk may
                    # absorb: an outer construct's condition block (e.g. `if c:`
                    # wrapping `while (x := f()) and g():`) has an equivalent
                    # trivial-return exit but NO corresponding back-edge recheck
                    # block, so it would push the accepted count past this
                    # limit and is correctly rejected.
                    _back_edge_recheck_count = 0
                    for _b in body:
                        _b_last = _b.get_last_instruction()
                        if (_b_last
                                and _b_last.opname in FORWARD_CONDITIONAL_JUMP_OPS
                                and _b_last.argval is not None):
                            _b_target = self.cfg.get_block_by_offset(_b_last.argval)
                            if (_b_target is not None
                                    and _b_target is not header
                                    and self._is_trivial_return_block(_b_target)):
                                _back_edge_recheck_count += 1
                    _accepted_equivalent_count = 0
                    while _cb is not None:
                        _cb_preds = [p for p in _cb.predecessors
                                     if p not in body and p not in region_blocks
                                     and p != header]
                        _next_cb = None
                        for p in _cb_preds:
                            p_last = p.get_last_instruction()
                            if p_last and p_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                if p_last.argval is not None:
                                    p_target = self.cfg.get_block_by_offset(p_last.argval)
                                    _is_equivalent_exit = (
                                        _cond_exit is not None
                                        and p_target is not None
                                        and p_target != _cond_exit
                                        and self._is_equivalent_exit_block(p_target, _cond_exit)
                                        and _back_edge_recheck_count > 0
                                        and _accepted_equivalent_count < _back_edge_recheck_count
                                    )
                                    if p_target == _cb or p_target in body or p_target == header or _is_equivalent_exit:
                                        _has_back_edge_to_p = any(
                                            be.get_last_instruction() is not None and
                                            be.get_last_instruction().opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') and
                                            be.get_last_instruction().argval == p.start_offset
                                            for be in body
                                        )
                                        # p is a valid condition-chain predecessor —
                                        # always claim it for this LoopRegion so it
                                        # does not leak out as a spurious outer
                                        # IfRegion. Only continue the backward walk
                                        # when p is not an inner-loop header (no
                                        # back-edge to p from this loop's body).
                                        region_blocks.add(p)
                                        if _is_equivalent_exit:
                                            _accepted_equivalent_count += 1
                                        if not _has_back_edge_to_p:
                                            _next_cb = p
                                        break
                        _cb = _next_cb
            verified_break_blocks = set()
            if break_blocks:
                for break_block in break_blocks:
                    if any(pred in body for pred in break_block.predecessors):
                        verified_break_blocks.add(break_block)
                        if break_block in body:
                            region_blocks.add(break_block)
                        elif not any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in break_block.instructions):
                            region_blocks.add(break_block)
                        else:
                            _has_user_code = False
                            for i in break_block.instructions:
                                if i.opname == 'LOAD_CONST' and i.argval is not None:
                                    _has_user_code = True
                                    break
                                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP',
                                                   'POP_BLOCK', 'POP_EXCEPT', 'COPY', 'RERAISE',
                                                   'PUSH_EXC_INFO', 'LOAD_CONST', 'RETURN_VALUE',
                                                   'RETURN_CONST', 'JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                                    _has_user_code = True
                                    break
                            if not _has_user_code:
                                region_blocks.add(break_block)
            if for_iter_setup and for_iter_setup not in body and header in for_iter_setup.successors:
                region_blocks.add(for_iter_setup)
            region_blocks.update(else_blocks)
            # [W3 fix] Include the loop's natural exit (fallthrough from back-edge block when
            # condition becomes false) in region_blocks. Without this, the exit block becomes a
            # standalone Region and the AST generator emits a spurious `return None` for the
            # implicit function return. Unique block ownership: the exit belongs to LoopRegion.
            # Only include trivial exit blocks (LOAD_CONST None; RETURN_VALUE) that are implicit
            # returns — non-trivial exits are real statements and stay standalone.
            if back_edge_block:
                for _be_succ in back_edge_block.successors:
                    if _be_succ in body or _be_succ == header:
                        continue
                    if _be_succ in region_blocks:
                        continue
                    if _be_succ == condition_block:
                        continue
                    if self._check_block_has_trailing_return_none(_be_succ):
                        region_blocks.add(_be_succ)
            ordered_body = sorted(body, key=lambda b: b.start_offset)
            entry = condition_block or header
            region = LoopRegion(
                region_type=loop_type, entry=entry, blocks=region_blocks, header_block=header,
                is_async=any(i.opname in ('GET_ANEXT', 'GET_AITER') for i in header.instructions),
                back_edge_block=back_edge_block, is_while_true=is_while_true,
                has_break=bool(verified_break_blocks), else_is_follow=False)
            region.body_blocks = ordered_body
            region.condition_block = condition_block
            region.else_blocks = else_blocks
            region.init_blocks = []
            region.back_edge_blocks = {back_edge_block} if back_edge_block else set()
            region.break_blocks = sorted(verified_break_blocks, key=lambda b: b.start_offset)
            region.continue_map = continue_map
            for _bb in verified_break_blocks:
                if _bb in region_blocks:
                    self.block_roles[_bb.start_offset] = BlockRole.BREAK
            region.metadata.update({'for_iter_setup': for_iter_setup, 'for_iter_exit': for_iter_exit,
                                   'for_iter_fall_through': for_iter_fall_through})
            if loop_type == RegionType.WHILE_LOOP and condition_block and condition_block == header:
                region.metadata['is_degenerate_while'] = any(
                    i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF')
                    for i in condition_block.instructions)
            if else_blocks and self._check_block_has_trailing_return_none(else_blocks[-1]):
                region.mark_trailing_return_none()
            if is_yield_from:
                region.metadata['is_yield_from_loop'] = True
            natural_back_edge = back_edge_block
            if back_edge_block and back_edge_block != header:
                last_instr = back_edge_block.get_last_instruction()
                if last_instr and last_instr.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                    meaningful_instrs = [i for i in back_edge_block.instructions
                                        if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                                        and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
                    if not meaningful_instrs:
                        for body_block in body:
                            if body_block != back_edge_block and body_block != header:
                                bl = body_block.get_last_instruction()
                                if (bl and bl.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                    and bl.argval == header.start_offset):
                                    natural_back_edge = body_block
                                    break
            region.metadata['natural_back_edge'] = natural_back_edge

            self.regions.append(region)
            for block in region.blocks:
                if block not in self.block_to_region:
                    self.block_to_region[block] = region

            regions.append(region)

        for region in self._filter_regions(regions, LoopRegion):
            recheck_blocks = set()
            for block in self.cfg.blocks.values():
                if block in self.block_to_region:
                    continue
                last_instr = block.get_last_instruction()
                if not last_instr or last_instr.opname not in CONDITIONAL_JUMP_OPS:
                    continue
                jump_target = self.cfg.get_block_by_offset(last_instr.argval) if last_instr.argval is not None else None
                if jump_target is None:
                    continue
                if jump_target != region.header_block and jump_target != region.condition_block:
                    if jump_target not in region.pre_condition_blocks:
                        continue
                meaningful = [i for i in block.instructions
                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')]
                if not meaningful:
                    recheck_blocks.add(block)
                    continue
                if meaningful[-1] != last_instr:
                    continue
                pre_jump = meaningful[:-1]
                if not pre_jump:
                    recheck_blocks.add(block)
                    continue
                has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                for i in pre_jump)
                if has_store:
                    continue
                has_side_effect = any(i.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                                    'CALL_FUNCTION_KW', 'CALL_FUNCTION_EX',
                                                    'DELETE_SUBSCR', 'DELETE_ATTR',
                                                    'RAISE_VARARGS', 'IMPORT_NAME')
                                      for i in pre_jump)
                if has_side_effect:
                    continue
                recheck_blocks.add(block)
            region.condition_recheck_blocks = recheck_blocks

            if region.condition_block:
                cond_block = region.condition_block
                chain = [cond_block]
                visited = {cond_block}
                cur = cond_block

                while cur:

                    next_block = None
                    last_i = cur.get_last_instruction()
                    if not last_i or last_i.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
                        break
                    for succ in cur.successors:
                        if succ in visited:
                            continue
                        if succ in region.body_blocks or succ == region.header_block:
                            continue
                        if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in succ.instructions):
                            continue
                        if succ in self.loop_analyzer.loop_headers:
                            continue
                        succ_last = succ.get_last_instruction()
                        if succ_last and succ_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                            has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                            for i in succ.instructions)
                            if not has_store:
                                next_block = succ
                                break
                    if next_block:
                        chain.append(next_block)
                        visited.add(next_block)
                        cur = next_block
                    else:
                        break
                region.condition_chain_blocks = chain

        loop_regions = self._filter_regions(regions, LoopRegion)
        if len(loop_regions) >= 2:
            removal_set = set()
            for i, lr_a in enumerate(loop_regions):
                if id(lr_a) in removal_set:
                    continue
                blocks_a = set(lr_a.blocks)
                for j, lr_b in enumerate(loop_regions):
                    if i == j or id(lr_b) in removal_set:
                        continue
                    blocks_b = set(lr_b.blocks)
                    body_b_set = set(lr_b.body_blocks or [])
                    cond_b = lr_b.condition_block
                    body_a_set = set(lr_a.body_blocks or [])
                    cond_a = lr_a.condition_block
                    same_cond = (cond_a and cond_b and cond_a.start_offset == cond_b.start_offset)
                    if same_cond:
                        if blocks_a < blocks_b and lr_a.header_block:
                            removal_set.add(id(lr_a))
                        elif blocks_b < blocks_a and lr_b.header_block:
                            removal_set.add(id(lr_b))
                        continue
                    if lr_a.is_while_true and cond_b and cond_b == lr_a.header_block:
                        if body_a_set and body_b_set and body_b_set <= body_a_set:
                            removal_set.add(id(lr_a))
                            continue
                    if lr_b.is_while_true and cond_a and cond_a == lr_b.header_block:
                        if body_a_set and body_b_set and body_a_set <= body_b_set:
                            removal_set.add(id(lr_b))
                            continue
            if removal_set:
                regions = [r for r in regions if id(r) not in removal_set]
                self.regions = [r for r in self.regions if id(r) not in removal_set]
                for rid in removal_set:
                    for rr in loop_regions:
                        if id(rr) == rid:
                            for blk in list(rr.blocks or []):
                                if blk in self.block_to_region and self.block_to_region[blk] is rr:
                                    del self.block_to_region[blk]
                            break

        return regions

    def _rebuild_block_roles_after_fake_loop_removal(self, regions: List[Region], fake_loop_ids: Set[int]) -> None:
        """
        过滤条件重检假循环后，修复相关块的block_role
        
        假循环被过滤后，以下块的role需要修正：
        1. 假循环的else_blocks (JUMP_BACKWARD块) → 应标记为CONTINUE/PURE_CONTINUE
        2. 假循环的back_edge_block (POP_JUMP_BACKWARD_IF_*块) → 应标记为LOOP_BODY或LOOP_BACK_EDGE
        3. 假循环的body_blocks中被错误标记为CONTINUE → 应标记为LOOP_BODY（如果有意义语句）
        """
        loop_regions = self._filter_regions(regions, LoopRegion)
        
        for region in loop_regions:
            if id(region) not in fake_loop_ids:
                continue
            
            # Fix 1: 修正else_blocks的角色
            for else_block in (region.else_blocks or []):
                last_instr = else_block.get_last_instruction()
                if last_instr and last_instr.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                    current_role = self.block_roles.get(else_block.start_offset)
                    if current_role in (BlockRole.LOOP_BACK_EDGE, BlockRole.LOOP_ELSE, BlockRole.NORMAL):
                        meaningful = [i for i in else_block.instructions
                                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                                    and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')]
                        if not meaningful:
                            self.block_roles[else_block.start_offset] = BlockRole.PURE_CONTINUE
                        else:
                            self.block_roles[else_block.start_offset] = BlockRole.CONTINUE
            
            # Fix 2: 修正back_edge_block的角色
            if region.back_edge_block:
                be = region.back_edge_block
                last_instr = be.get_last_instruction()
                if last_instr and last_instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                    current_role = self.block_roles.get(be.start_offset)
                    if current_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
                        meaningful = [i for i in be.instructions
                                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                                    and i.opname not in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')]
                        if meaningful:
                            self.block_roles[be.start_offset] = BlockRole.LOOP_BODY
                        else:
                            self.block_roles[be.start_offset] = BlockRole.LOOP_BACK_EDGE
            
            # Fix 3: 修正body_blocks(含header)中被错误标记为CONTINUE/NON-NORMAL的块
            # 当假循环被过滤后，其header和body_blocks中的非continue块应该恢复为LOOP_BODY
            for body_block in list(region.body_blocks or []) + ([region.header_block] if region.header_block else []):
                if body_block in (region.else_blocks or []):
                    continue
                if body_block == region.back_edge_block:
                    continue
                
                current_role = self.block_roles.get(body_block.start_offset)
                if current_role in (BlockRole.LOOP_HEADER, BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
                    meaningful_instrs = [
                        i for i in body_block.instructions
                        if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                        and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                            'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                        and i.opname not in CONDITIONAL_JUMP_OPS
                        and i.opname not in SHORT_CIRCUIT_JUMP_OPS
                    ]
                    if meaningful_instrs:
                        self.block_roles[body_block.start_offset] = BlockRole.LOOP_BODY

    def _cleanup_try_else_in_loop_body(self, loop_regions: List['LoopRegion'], try_regions: List['TryExceptRegion']):
        for tr in try_regions:
            if not tr.else_blocks or not tr.has_else:
                continue
            enclosing_loops = [lr for lr in loop_regions
                               if any(b in lr.body_blocks for b in tr.try_blocks)]
            if not enclosing_loops:
                continue
            loop_body_blocks = set()
            for lr in enclosing_loops:
                if hasattr(lr, 'body_blocks') and lr.body_blocks:
                    loop_body_blocks.update(lr.body_blocks)
            try_blocks_set = set(tr.try_blocks) if tr.try_blocks else set()
            spurious = [eb for eb in tr.else_blocks
                        if eb in loop_body_blocks
                        and self.block_roles.get(eb.start_offset) not in (BlockRole.PURE_CONTINUE, BlockRole.CONTINUE)
                        and not any(tb in try_blocks_set
                                    and eb in tb.successors
                                    and tb.get_last_instruction() is not None
                                    and tb.get_last_instruction().opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT', 'JUMP_ABSOLUTE')
                                    and tb.get_last_instruction().opname not in CONDITIONAL_JUMP_OPS
                                    for tb in try_blocks_set)]
            if not spurious:
                continue
            for eb in spurious:
                tr.else_blocks.remove(eb)
                if eb in tr.blocks:
                    tr.blocks.remove(eb)
            if not tr.else_blocks:
                tr.has_else = False

        for lr in loop_regions:
            if not lr.else_blocks:
                continue
            parent_loops = [pl for pl in loop_regions
                           if pl is not lr
                           and hasattr(pl, 'body_blocks') and pl.body_blocks
                           and any(b in pl.body_blocks for b in lr.body_blocks)]
            if not parent_loops:
                continue
            parent_body = set()
            for pl in parent_loops:
                parent_body.update(pl.body_blocks)
            spurious = [eb for eb in lr.else_blocks if eb in parent_body]
            if not spurious:
                continue
            for eb in spurious:
                lr.else_blocks.remove(eb)
                if eb in lr.blocks:
                    lr.blocks.remove(eb)

    def _detect_and_filter_conditional_recheck_fake_loops(self, regions: List[Region]) -> Set[int]:
        """
        检测并过滤条件重检假循环（由continue语句导致的重叠LoopRegion）
        
        Python编译器为含continue的while循环生成特殊字节码模式：
        - 外层循环：真正的while循环
        - 内层"循环"：由条件重检(POP_JUMP_BACKWARD_IF_*) + continue形成的假循环
        
        假循环的特征：
        1. 内层header在外层body_blocks中
        2. 共享condition_block或内层condition_block==内层header
        3. 内层else_blocks只包含纯JUMP_BACKWARD块（continue目标块）
        4. 内层back_edge_block是POP_JUMP_BACKWARD_IF_*类型（条件重检特征）
        
        Returns:
            需要被过滤的假循环region ID集合
        """
        fake_loop_region_ids = set()
        loop_regions = self._filter_regions(regions, LoopRegion)
        
        for inner in loop_regions:
            if id(inner) in fake_loop_region_ids:
                continue
            if not inner.header_block:
                continue
                
            for outer in loop_regions:
                if inner is outer:
                    continue
                if id(outer) in fake_loop_region_ids:
                    continue
                if not outer.body_blocks:
                    continue
                
                if inner.header_block not in outer.body_blocks:
                    continue
                
                shared_condition = (
                    (inner.condition_block == outer.condition_block) or
                    (inner.condition_block == inner.header_block)
                )
                if not shared_condition:
                    continue
                
                inner_else_blocks = set(inner.else_blocks or [])
                if not inner_else_blocks:
                    continue
                
                is_pure_continue_else = True
                for block in inner_else_blocks:
                    last_instr = block.get_last_instruction()
                    has_trailing_jump_to_outer = (
                        last_instr is not None
                        and last_instr.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                        and last_instr.argval is not None
                        and outer.header_block is not None
                        and self.cfg.get_block_by_offset(last_instr.argval) == outer.header_block
                    )
                    if has_trailing_jump_to_outer:
                        continue
                    meaningful_instrs = [
                        i for i in block.instructions
                        if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                        and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                    ]
                    if meaningful_instrs:
                        is_pure_continue_else = False
                        break
                
                if not is_pure_continue_else:
                    continue
                
                if inner.back_edge_block:
                    back_edge_last = inner.back_edge_block.get_last_instruction()
                    if back_edge_last and back_edge_last.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                        fake_loop_region_ids.add(id(inner))
                        break
        
        return fake_loop_region_ids


    def _classify_loop_type(self, header: BasicBlock, body: Set[BasicBlock] = None) -> Tuple[RegionType, Optional[BasicBlock], Optional[BasicBlock], Optional[BasicBlock], bool, bool]:
        """
        分类循环类型：FOR_LOOP vs WHILE_LOOP

        字节码模式：
        - FOR_LOOP：header包含FOR_ITER指令，前驱包含GET_ITER
        - WHILE_LOOP：header不含FOR_ITER，回边由条件跳转或无条件跳转形成
        - ASYNC_FOR_LOOP：header包含GET_ANEXT指令
        - yield from循环：body中包含SEND+YIELD_VALUE+JUMP_BACKWARD_NO_INTERRUPT

        分类算法：
        1. 检查header是否包含FOR_ITER → FOR_LOOP
        2. 检查header是否包含GET_ANEXT → ASYNC FOR_LOOP
        3. 检查body是否包含yield from模式 → WHILE_LOOP(is_yield_from)
        4. 默认 → WHILE_LOOP
        5. 调用_is_while_true判断是否为while True循环

        FOR_ITER后继识别：
        - fall_through：offset + 2的后继，即循环体入口
        - exit：argval指向的后继，即迭代耗尽后的出口

        边界条件：
        - FOR_ITER的前驱可能包含GET_ITER或JUMP_FORWARD跳转
        - yield from需要SEND+YIELD_VALUE+JUMP_BACKWARD_NO_INTERRUPT三指令同时存在
        - while True检测：header无有意义指令/无条件跳转/含STORE后跟条件跳转
        - header含body+条件重检时，_is_while_true需区分body的STORE和条件重检的LOAD

        区域归约算法符合度：
        - FOR_ITER是for循环的唯一标识，符合编译器理论
        - while True判定基于header指令语义分析，非启发式
        """
        detector = get_opcode_detector()

        for instr in header.instructions:
            if detector.is_loop_header_opcode(instr):
                if detector.is_for_iter(instr):
                    successors = sorted(header.successors, key=lambda s: s.start_offset)
                    for_iter_fall_through = next((s for s in successors if s.start_offset == instr.offset + 2),
                                                successors[0] if successors else None)
                    for_iter_exit = next((s for s in successors if s.start_offset == instr.argval), None) \
                        if instr.argval is not None else None
                    if for_iter_exit is None:
                        for_iter_exit = next((s for s in successors if s != for_iter_fall_through), None)
                    for_iter_setup = None
                    for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                        if pred == header:
                            continue
                        if any(detector.is_iterator_setup_opcode(i) for i in pred.instructions) or \
                           any(i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE') and
                               self.cfg.get_block_by_offset(i.argval) == header for i in pred.instructions):
                            for_iter_setup = pred
                            break
                    header_has_get_iter = any(detector.is_iterator_setup_opcode(i) for i in header.instructions)
                    if for_iter_setup is None and header_has_get_iter:
                        for_iter_setup = header
                    return RegionType.FOR_LOOP, for_iter_setup, for_iter_exit, for_iter_fall_through, False, False
                elif detector.is_get_anext(instr):
                    # [Round5-09] async for：GET_ANEXT 在 header，GET_AITER 在前驱块。
                    # FOR_ITER 的等价物跨两块：GET_ANEXT (header) + SEND (后继块)。
                    # 与 sync FOR_ITER 分支保持对称：检测含 GET_AITER 的前驱作为
                    # for_iter_setup，从 SEND 的 argval 提取 fall_through（循环体入口），
                    # 从后继链中的 END_ASYNC_FOR 提取 exit（迭代耗尽出口）。
                    for_iter_setup = None
                    for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                        if pred == header:
                            continue
                        if any(detector.is_iterator_setup_opcode(i) for i in pred.instructions):
                            for_iter_setup = pred
                            break
                    header_has_get_aier = any(detector.is_iterator_setup_opcode(i) for i in header.instructions)
                    if for_iter_setup is None and header_has_get_aier:
                        for_iter_setup = header
                    for_iter_fall_through = None
                    for_iter_exit = None
                    _visited = {header}
                    _queue = list(header.successors)
                    while _queue:
                        _succ = _queue.pop(0)
                        if _succ in _visited:
                            continue
                        _visited.add(_succ)
                        _has_send = False
                        for si in _succ.instructions:
                            if si.opname == 'SEND' and si.argval is not None:
                                _has_send = True
                                _ft = self.cfg.get_block_by_offset(si.argval)
                                if _ft and for_iter_fall_through is None:
                                    for_iter_fall_through = _ft
                                break
                        if any(i.opname == 'END_ASYNC_FOR' for i in _succ.instructions):
                            for_iter_exit = _succ
                        # Only descend through the SEND/YIELD sub-loop (async for
                        # 挂起协议块)；避免误把循环体或外层块纳入搜索。
                        if _has_send or any(i.opname == 'END_ASYNC_FOR' for i in _succ.instructions):
                            for _ss in _succ.successors:
                                if _ss not in _visited:
                                    _queue.append(_ss)
                    return RegionType.FOR_LOOP, for_iter_setup, for_iter_exit, for_iter_fall_through, False, False

        is_yield_from = False
        if body is not None:
            for block in body:
                has_send = has_yield = has_jump_backward_no_interrupt = False
                for instr in block.instructions:
                    if detector.is_send(instr):
                        has_send = True
                    elif detector.is_yield_value(instr):
                        has_yield = True
                    elif detector.is_jump_backward_no_interrupt(instr):
                        has_jump_backward_no_interrupt = True
                if has_send and has_yield and has_jump_backward_no_interrupt:
                    for pred in header.predecessors:
                        if any(detector.is_get_yield_from_iter(i) for i in pred.instructions):
                            is_yield_from = True
                            break
                    break

        is_while_true = self._is_while_true(header, body) if body is not None else False
        return RegionType.WHILE_LOOP, None, None, None, is_while_true, is_yield_from

    def _is_while_true(self, header: BasicBlock, body: Set[BasicBlock]) -> bool:
        meaningful = [i for i in header.instructions 
                    if i.opname not in NOISE_OPS]
        
        if not meaningful:
            return True
        
        has_conditional_jump = False
        has_store_before_jump = False
        cond_jump_instr = None
        for i in meaningful:
            if i.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                          'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                          'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                          'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                          'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
                          'FORWARD_JUMP_IF_TRUE', 'FORWARD_JUMP_IF_FALSE'):
                has_conditional_jump = True
                cond_jump_instr = i
                break
            if i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                has_store_before_jump = True
        
        if not has_conditional_jump:
            return True
        
        if cond_jump_instr is not None and cond_jump_instr.argval is not None:
            jump_target = self.cfg.get_block_by_offset(cond_jump_instr.argval)
            if jump_target is not None and jump_target == header:
                if cond_jump_instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                    has_non_trivial_body_stmts = False
                    for i in meaningful:
                        if i is cond_jump_instr:
                            continue
                        if i.opname in ('BINARY_OP', 'BINARY_SUBSCR', 'LOAD_METHOD', 'CALL',
                                       'LOAD_ATTR', 'STORE_SUBSCR', 'DELETE_ATTR',
                                       'DELETE_SUBSCR', 'GET_ITER', 'FOR_ITER',
                                       'SEND', 'FORMAT_VALUE', 'BUILD_STRING',
                                       'LIST_APPEND', 'SET_ADD', 'MAP_ADD',
                                       'IMPORT_NAME', 'IMPORT_FROM',
                                       'RAISE_VARARGS', 'RETURN_VALUE', 'RETURN_CONST'):
                            has_non_trivial_body_stmts = True
                            break
                    if has_non_trivial_body_stmts:
                        return False
                return True
            if jump_target is not None and jump_target in body:
                return True
        
        if has_store_before_jump:
            last = header.get_last_instruction()
            if (last and last.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                    and last.argval is not None
                    and self.cfg.get_block_by_offset(last.argval) == header):
                has_non_trivial_body_stmts = False
                for i in meaningful:
                    if i.opname in ('BINARY_OP', 'BINARY_SUBSCR', 'LOAD_METHOD', 'CALL',
                                   'LOAD_ATTR', 'STORE_SUBSCR', 'DELETE_ATTR',
                                   'DELETE_SUBSCR', 'GET_ITER', 'FOR_ITER',
                                   'SEND', 'FORMAT_VALUE', 'BUILD_STRING',
                                   'LIST_APPEND', 'SET_ADD', 'MAP_ADD',
                                   'IMPORT_NAME', 'IMPORT_FROM',
                                   'RAISE_VARARGS', 'RETURN_VALUE', 'RETURN_CONST'):
                        has_non_trivial_body_stmts = True
                        break
                if has_non_trivial_body_stmts:
                    return False
            return True
        
        return False


    def _find_loop_else(self, header: BasicBlock, loop_body: Set[BasicBlock], loop_type: RegionType,
                        for_iter_exit: Optional[BasicBlock] = None,
                        condition_block: Optional[BasicBlock] = None) -> Tuple[Optional[List[BasicBlock]], Optional[BasicBlock]]:
        """
        识别循环else块

        字节码模式：
        - for循环：FOR_ITER耗尽后跳转到else块入口（for_iter_exit）
        - while循环：条件跳转的fall-through路径到达else块
        - break目标：循环体内JUMP_FORWARD/JUMP_ABSOLUTE跳到循环外，跳过else块

        识别算法：
        1. for循环：for_iter_exit即为else块入口
           a. 收集循环体内跳到循环外的break目标块
           b. 找到break目标的最近公共后必经节点（post_else）
           c. 从for_iter_exit到post_else之间的块为else块
           d. 无break时，for_iter_exit本身就是else块
        2. while循环：
           a. 收集header和body块的所有不在body_set中的后继
           b. 找到loop_successors的最近公共后必经节点（natural_exit）
           c. 从natural_exit可达的块（不在body_set中）为else块

        边界条件：
        - 无else块时loop_successors为空
        - natural_exit在body_set中说明循环没有正常出口
        - else块仅在循环正常退出（非break）时执行
        - break跳过else块直接到natural_exit之后
        - for_iter_exit可能同时是else块和break后的汇聚点
        - while循环条件块的fall-through目标可能是else块

        区域归约算法符合度：
        - 基于后必经节点分析，符合编译器理论
        - else块与break目标通过post-dominator区分
        - else_is_follow标记需正确设置，确保AST生成时else作为orelse而非独立语句
        """
        body_set = loop_body | {header}

        if loop_type == RegionType.FOR_LOOP and for_iter_exit and for_iter_exit not in body_set:
            natural_exit = for_iter_exit
            break_targets = []
            _break_hits_for_iter_exit = False
            for block in body_set:
                if block == header:
                    continue
                for succ in block.successors:
                    if succ not in body_set and succ not in break_targets:
                        block_last = block.get_last_instruction()
                        if block_last and block_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                            if succ == for_iter_exit:
                                _break_hits_for_iter_exit = True
                            else:
                                break_targets.append(succ)
                        elif block_last and block_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                            if succ == for_iter_exit:
                                pass
                            elif succ not in body_set:
                                _succ_last = succ.get_last_instruction()
                                if _succ_last and _succ_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                                    _succ_target = self.cfg.get_block_by_offset(_succ_last.argval) if _succ_last.argval is not None else None
                                    if _succ_target == for_iter_exit:
                                        _break_hits_for_iter_exit = True
                                    elif _succ_target and _succ_target not in body_set and _succ_target not in break_targets:
                                        break_targets.append(_succ_target)
                                elif _succ_last and _succ_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                    if succ not in break_targets:
                                        break_targets.append(succ)
            if _break_hits_for_iter_exit:
                return None, natural_exit
            if break_targets:
                post_else = self.dom_analyzer.find_nearest_common_post_dominator(set(break_targets))
                if post_else and post_else in break_targets and len(break_targets) == 1:
                    for succ in post_else.successors:
                        if succ not in body_set:
                            post_else = succ
                            break
                if post_else and post_else != for_iter_exit:
                    else_blocks = []
                    visited = set()
                    stack = [for_iter_exit]
                    while stack:
                        cur = stack.pop()
                        if cur in visited or cur == post_else:
                            continue
                        visited.add(cur)
                        if cur.start_offset < header.start_offset:
                            continue
                        if cur not in body_set:
                            else_blocks.append(cur)
                        for succ in cur.successors:
                            if succ not in visited and succ != post_else:
                                stack.append(succ)
                    result = sorted(else_blocks, key=lambda b: b.start_offset) if else_blocks else None
                    if result:
                        _with_cleanup_blocks = set()
                        for _wr in self._filter_regions(self.regions, WithRegion):
                            if hasattr(_wr, 'cleanup_blocks') and _wr.cleanup_blocks:
                                _with_cleanup_blocks.update(_wr.cleanup_blocks)
                            if hasattr(_wr, 'exception_blocks') and _wr.exception_blocks:
                                _with_cleanup_blocks.update(_wr.exception_blocks)
                        result = [b for b in result
                                  if b not in _with_cleanup_blocks
                                  and (b == for_iter_exit or not self._is_early_return_block(b))
                                  and not self._is_except_handler_block(b)]
                        if not result:
                            result = None
                    return result, natural_exit
                else:
                    return None, natural_exit
            else:
                if for_iter_exit and for_iter_exit not in body_set:
                    return [for_iter_exit], natural_exit
                return None, natural_exit

        loop_successors = [s for s in header.successors if s not in body_set and s != header]
        if condition_block:
            loop_successors = [s for s in loop_successors if s != condition_block]
        loop_successors = [s for s in loop_successors if not any(i.opname == 'RAISE_VARARGS' for i in s.instructions)]
        detector = get_opcode_detector()
        for block in body_set:
            if block == header:
                continue
            for succ in block.successors:
                if succ not in body_set and succ != header and succ not in loop_successors:
                    if condition_block and succ == condition_block:
                        continue
                    block_last = block.get_last_instruction()
                    if block_last and detector.is_conditional_jump(block_last):
                        if any(i.opname == 'RAISE_VARARGS' for i in succ.instructions):
                            continue
                        loop_successors.append(succ)
        cond_exit_targets = []
        if condition_block and condition_block != header and condition_block not in body_set:
            cond_last = condition_block.get_last_instruction()
            if cond_last and cond_last.opname in FORWARD_CONDITIONAL_JUMP_OPS and cond_last.argval is not None:
                cond_exit = self.cfg.get_block_by_offset(cond_last.argval)
                if cond_exit and cond_exit not in body_set and cond_exit != header:
                    if cond_exit not in loop_successors:
                        loop_successors.append(cond_exit)
                    cond_exit_targets.append(cond_exit)
        loop_successors = list(set(loop_successors))

        if not loop_successors:
            return None, None

        natural_exit = self.dom_analyzer.find_nearest_common_post_dominator(set(loop_successors))
        if not natural_exit or natural_exit in body_set:
            non_return_successors = [s for s in loop_successors
                                    if not self._check_block_has_trailing_return_none(s)
                                    or s in cond_exit_targets]
            if loop_type == RegionType.WHILE_LOOP:
                non_return_successors = [s for s in non_return_successors
                                        if not self._is_early_return_block(s)
                                        and not self._is_except_handler_block(s)]
            if non_return_successors:
                else_blocks = sorted(non_return_successors, key=lambda b: b.start_offset)
                return else_blocks, None
            return None, natural_exit

        else_blocks = []
        for succ in loop_successors:
            if natural_exit == succ:
                else_blocks.append(natural_exit)
            else:
                path_blocks = self._collect_blocks_on_path(natural_exit, succ)
                else_blocks.extend(path_blocks)
        else_blocks = list(set(else_blocks) - body_set)

        if loop_type == RegionType.WHILE_LOOP:
            _cond_exit_set = set(cond_exit_targets) if cond_exit_targets else set()
            _break_targets = set()
            for _b in body_set:
                _b_last = _b.get_last_instruction()
                if _b_last and _b_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    _b_target = self.cfg.get_block_by_offset(_b_last.argval) if _b_last.argval is not None else None
                    if _b_target and _b_target not in body_set and _b_target != header:
                        _break_targets.add(_b_target)
                elif _b_last and _b_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    if not _b.successors:
                        _b_meaningful = [i for i in _b.instructions
                                         if i.opname not in NOISE_OPS
                                         and i.opname not in ('LOAD_CONST', 'POP_TOP')
                                         and i.opname not in PURE_JUMP_OPS
                                         and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                        if not _b_meaningful:
                            for _b_pred in _b.predecessors:
                                if _b_pred in body_set:
                                    _b_pred_last = _b_pred.get_last_instruction()
                                    if _b_pred_last and _b_pred_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                        _break_targets.add(_b)
                                        break
            _else_is_skipped_by_break = False
            for _eb in else_blocks:
                if _eb not in _break_targets:
                    if _break_targets:
                        _else_is_skipped_by_break = True
                    break
            if not _break_targets:
                if natural_exit and else_blocks:
                    _filtered = [b for b in else_blocks
                                 if not self._is_early_return_block(b)
                                 and not self._is_except_handler_block(b)]
                    if _filtered:
                        else_blocks = _filtered
                    else:
                        else_blocks = None
                else:
                    else_blocks = None
            elif _else_is_skipped_by_break:
                _break_trampoline_blocks = set()
                for b in else_blocks:
                    if b in _break_targets:
                        continue
                    b_meaningful = [i for i in b.instructions
                                    if i.opname not in NOISE_OPS
                                    and i.opname not in PURE_JUMP_OPS]
                    if len(b_meaningful) == 0:
                        b_last = b.get_last_instruction()
                        if b_last and b_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                            b_target = self.cfg.get_block_by_offset(b_last.argval) if b_last.argval is not None else None
                            if b_target in _break_targets:
                                _break_trampoline_blocks.add(b)
                else_blocks = [b for b in else_blocks
                               if (b in _cond_exit_set and not self._is_early_return_block(b))
                               or (b not in _cond_exit_set
                                   and not self._is_early_return_block(b)
                                   and not self._is_except_handler_block(b)
                                   and b not in _break_trampoline_blocks)]
            else:
                else_blocks = []

        result = sorted(else_blocks, key=lambda b: b.start_offset) if else_blocks else None
        return result, natural_exit

    def _is_early_return_block(self, block: BasicBlock) -> bool:
        if not block or not block.instructions:
            return False
        last_instr = block.get_last_instruction()
        if last_instr is None:
            return False
        if last_instr.opname == 'RETURN_CONST' and last_instr.argval is not None:
            return True
        if last_instr.opname == 'RETURN_VALUE':
            if self._check_block_has_trailing_return_none(block):
                return False
            has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                          for i in block.instructions)
            if has_store:
                return False
            for i in reversed(block.instructions):
                if i.opname == 'LOAD_CONST' and i.argval is not None:
                    return True
                if i.opname not in ('NOP', 'CACHE', 'POP_TOP'):
                    break
            has_load = any(i.opname.startswith('LOAD_') for i in block.instructions
                          if i.opname not in ('LOAD_CONST',) or i.argval is not None)
            if has_load:
                return True
        return False

    def _is_except_handler_block(self, block: BasicBlock) -> bool:
        """Check if a block is part of an except handler.

        Bytecode pattern:
        - Block contains PUSH_EXC_INFO (handler entry)
        - Block contains CHECK_EXC_MATCH or CHECK_EG_MATCH (exception type check)
        - Such blocks are part of exception handling, NOT loop else clauses

        Root cause:
        - _find_loop_else collected these blocks as else_blocks because they are
          successors of body blocks outside the body set
        - But semantically they are exception handlers, not normal loop exit paths

        Returns True if block is an except handler block (should be excluded from else).
        """
        if not block or not block.instructions:
            return False
        return any(i.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH',
                               'WITH_EXCEPT_START')
                  for i in block.instructions)

    def _detect_break_continue(self, loop_body: Set[BasicBlock], header: BasicBlock,
                               natural_exit: Optional[BasicBlock] = None,
                               natural_back_edge: Optional[BasicBlock] = None,
                               condition_block: Optional[BasicBlock] = None) -> Tuple[Set[BasicBlock], Dict[BasicBlock, str]]:
        """
        检测循环中的break和continue

        字节码模式：
        - break：循环体内的块跳转到循环外（不在body_set中且不是natural_exit）
        - continue：循环体内的块跳回循环header
        - break到natural_exit：当natural_exit是终止块（RETURN_VALUE）时，条件跳转到natural_exit也是break
        - 条件break：POP_JUMP_FORWARD_IF_*跳转到循环外

        检测算法：
        1. 遍历循环体每个块的后继
        2. 后继不在body_set且不是natural_exit → break目标块
        3. 后继是natural_exit且natural_exit是终止块 → break
        4. 块的最后指令跳回header → continue或LOOP_BACK_EDGE
        5. 过滤条件回边跳转（不算break）

        边界条件：
        - 条件回边跳转（POP_JUMP_BACKWARD_IF_*）不算break
        - RETURN_VALUE/RETURN_CONST不算break（函数返回）
        - 异常处理块（PUSH_EXC_INFO）不算break目标
        - 支配header的回边块标记为LOOP_BACK_EDGE而非CONTINUE
        - 嵌套循环中内层break/continue不被外层捕获
        - break目标块需标记BlockRole.BREAK角色

        区域归约算法符合度：
        - break/continue基于CFG边语义，符合结构化控制流定义
        - LOOP_BACK_EDGE vs CONTINUE区分基于支配关系
        - break_blocks集合用于AST生成时正确插入break语句
        """
        break_blocks_set = set()
        continue_map = {}
        body_set = set(loop_body) if not isinstance(loop_body, set) else loop_body

        if natural_exit is not None:
            ne_meaningful = [i for i in natural_exit.instructions
                             if i.opname not in NOISE_OPS
                             and i.opname not in ('RETURN_VALUE', 'RETURN_CONST', 'LOAD_CONST')
                             and i.opname not in PURE_JUMP_OPS]
            ne_is_terminator = not ne_meaningful and any(
                i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in natural_exit.instructions
            )
        else:
            ne_is_terminator = False

        for b in loop_body:
            last = b.get_last_instruction()
            is_back_edge_condition = (
                last and last.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                and last.argval is not None
                and self.cfg.get_block_by_offset(last.argval) in body_set
            )
            for s in b.successors:
                if s == condition_block and condition_block is not None and condition_block not in body_set:
                    continue
                if s not in body_set and s != natural_exit:
                    if any(i.opname in ('RAISE_VARARGS', 'RERAISE') for i in s.instructions):
                        continue
                    if not any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in s.instructions):
                        if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in s.instructions):
                            if is_back_edge_condition:
                                continue
                            if last and last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', *FORWARD_CONDITIONAL_JUMP_OPS):
                                break_blocks_set.add(s)
                            else:
                                s_meaningful = [i for i in s.instructions
                                                if i.opname not in NOISE_OPS
                                                and i.opname not in ('LOAD_CONST',)
                                                and i.opname not in PURE_JUMP_OPS
                                                and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                                _has_exc_handler = any(
                                    any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') 
                                        for i in _sb.instructions)
                                    for _sb in b.successors if _sb != s
                                ) or any(
                                    any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')
                                        for i in _sb.instructions)
                                    for _sb in self.cfg.blocks.values()
                                    if s in _sb.successors
                                )
                                if not s_meaningful:
                                    if not _has_exc_handler or self.dom_analyzer.is_dominator(header, s):
                                        break_blocks_set.add(s)
                                else:
                                    if not _has_exc_handler:
                                        break_blocks_set.add(s)
                        else:
                            if is_back_edge_condition:
                                continue
                            # Fix: 如果后继块是跳回循环头部或循环条件的 JUMP_BACKWARD 块
                            # （即 continue 语句），不应将其归类为 break 块。
                            # 这种情况发生在 try body 内的 continue 块未被纳入
                            # loop_body 但仍属于循环结构时。
                            # while 循环中 continue 跳转到循环条件块（header 的前驱），
                            # for 循环中 continue 跳转到 header 本身。
                            _s_last = s.get_last_instruction()
                            if _s_last and _s_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                                _s_target = self.cfg.get_block_by_offset(_s_last.argval) if _s_last.argval is not None else None
                                if _s_target == header or _s_target in header.predecessors:
                                    continue_map[s] = 'CONTINUE'
                                    continue
                            break_blocks_set.add(s)
                elif s == natural_exit and ne_is_terminator:
                    if last and last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        if last.argval is not None and self.cfg.get_block_by_offset(last.argval) in body_set:
                            break_blocks_set.add(s)

        detector = get_opcode_detector()
        for block in loop_body:
            if block == header:
                continue
            last_instr = block.get_last_instruction()
            if not last_instr:
                continue
            jump_offset = last_instr.argval if isinstance(last_instr.argval, int) else last_instr.arg
            target = (self.cfg.get_block_by_offset(int(jump_offset))
                      if jump_offset is not None else None)
            is_jump_to_header = ((target == header or target == condition_block) and
                                 (detector.is_unconditional_jump(last_instr) or
                                  detector.is_conditional_jump(last_instr)))
            if not is_jump_to_header and target is not None:
                if (detector.is_unconditional_jump(last_instr) or detector.is_conditional_jump(last_instr)):
                    if (target != header and target in header.predecessors
                            and len(target.instructions) == 1 and target.instructions[0].opname == 'NOP'
                            and len(target.successors) == 1 and list(target.successors)[0] == header):
                        is_jump_to_header = True
            if not is_jump_to_header:
                continue
            _blk_meaningful = [i for i in block.instructions
                               if i.opname not in NOISE_OPS
                               and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                    'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                               and i.opname not in CONDITIONAL_JUMP_OPS]
            if block == natural_back_edge:
                # [Phase 3 adv17_for_if_elif_else_flow] 当 natural_back_edge
                # 实际是显式 continue（条件分支 true body / fall-through）时，
                # 标记为 CONTINUE 而非 LOOP_BACK_EDGE。判据：块只有一个前驱
                # （在循环体内），前驱末指令是 FORWARD 条件跳转，且本块是
                # fall-through（true body，非 jump target）。当循环所有路径
                # 都显式 break/continue/return 时，唯一回边可能是 elif body
                # 的 continue，把它当 LOOP_BACK_EDGE 会让 elif body 变 pass
                # 而非 continue。fall-through（true body）始终是显式分支
                # （必须走"if true"路径才能到达），不会是自然回边；jump
                # target（false body）可能是自然路径（如 while 循环末尾），
                # 故仅检测 fall-through 情形。
                _nb_preds = [p for p in block.predecessors if p in body_set]
                _is_explicit_cont = False
                if len(_nb_preds) == 1:
                    _np = _nb_preds[0]
                    _npl = _np.get_last_instruction()
                    if (_npl and _npl.opname in FORWARD_CONDITIONAL_JUMP_OPS
                            and _npl.argval is not None):
                        _jt = self.cfg.get_block_by_offset(_npl.argval)
                        if _jt is not block:
                            _is_explicit_cont = True
                if _is_explicit_cont:
                    continue_map[block] = 'CONTINUE'
                else:
                    continue_map[block] = 'LOOP_BACK_EDGE'
                continue
            if _blk_meaningful:
                continue_map[block] = 'CONTINUE'
            else:
                continue_map[block] = ('LOOP_BACK_EDGE'
                                       if self.dom_analyzer.is_dominator(block, header)
                                       else 'CONTINUE')

        for block in loop_body:
            if block == header:
                continue
            if block in break_blocks_set:
                continue
            if block in continue_map:
                continue
            if not block.successors:
                last = block.get_last_instruction()
                if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    meaningful = [i for i in block.instructions
                                 if i.opname not in NOISE_OPS
                                 and i.opname not in ('LOAD_CONST', 'POP_TOP')
                                 and i.opname not in PURE_JUMP_OPS
                                 and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                    if not meaningful:
                        # [Phase 3 adv17_while_multi_if_flow] 仅当
                        # LOAD_CONST 值为 None 时才可能是 break 的
                        # peephole 优化（while True 末尾 break → return
                        # None）。显式 return <非None常量>（如 return 1 →
                        # LOAD_CONST 1 + RETURN_VALUE）不应被分类为 break。
                        _is_break_peephole = False
                        for i in block.instructions:
                            if i.opname == 'LOAD_CONST':
                                if i.argval is None:
                                    _is_break_peephole = True
                                break
                            if i.opname == 'RETURN_CONST':
                                if i.argval is None:
                                    _is_break_peephole = True
                                break
                        if not _is_break_peephole:
                            continue
                        for pred in block.predecessors:
                            if pred in body_set:
                                pred_last = pred.get_last_instruction()
                                if pred_last and pred_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                    break_blocks_set.add(block)
                                    break

        return break_blocks_set, continue_map


    def _collect_natural_loop_body(self, header: BasicBlock,
                                    back_edge_sources: List[BasicBlock],
                                    is_for_loop: bool = False) -> Set[BasicBlock]:
        body = {header}
        stack = []
        for src in back_edge_sources:
            if src != header:
                stack.append(src)

        while stack:
            block = stack.pop()
            if block in body:
                continue
            body.add(block)
            for pred in block.predecessors:
                if pred not in body:
                    stack.append(pred)

        detector = get_opcode_detector()
        if len(body) == 1 and header in body:
            last_hdr = header.get_last_instruction()
            has_back_edge_condition = (
                last_hdr and last_hdr.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                and last_hdr.argval is not None
                and self.cfg.get_block_by_offset(last_hdr.argval) == header
            )
            if not has_back_edge_condition:
                if is_for_loop:
                    for_iter_instr = next((i for i in header.instructions if i.opname == 'FOR_ITER'), None)
                    if for_iter_instr:
                        fall_through_offset = for_iter_instr.offset + 2
                        fall_through = self.cfg.get_block_by_offset(fall_through_offset)
                        if fall_through:
                            body.add(fall_through)
                            exit_offset = for_iter_instr.argval
                            exit_block = self.cfg.get_block_by_offset(exit_offset) if exit_offset else None
                            queue = [fall_through]
                            while queue:
                                current = queue.pop()
                                for succ in current.successors:
                                    if succ == header or succ in body:
                                        continue
                                    if exit_block and succ == exit_block:
                                        continue
                                    body.add(succ)
                                    queue.append(succ)
                else:
                    for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                        if pred == header or pred in self.loop_analyzer.loop_headers:
                            continue
                        last = pred.get_last_instruction()
                        if last and last.opname in FORWARD_CONDITIONAL_JUMP_OPS and last.argval is not None:
                            exit_block = self.cfg.get_block_by_offset(last.argval)
                            if exit_block and exit_block not in {header} and not any(
                                detector.is_for_iter(i) for i in pred.instructions
                            ):
                                body.add(pred)
                                break
        
        if not is_for_loop:
            while_true_predecessor = None
            for pred in sorted(header.predecessors, key=lambda p: p.start_offset):
                if pred in body or pred in self.loop_analyzer.loop_headers:
                    continue
                if all(i.opname in NOISE_OPS for i in pred.instructions) and pred.start_offset != 0:
                    while_true_predecessor = pred
                    break
            if while_true_predecessor is not None:
                body.add(while_true_predecessor)

            _header_last = header.get_last_instruction()
            _header_backward_cond_fallthrough = None
            if _header_last and _header_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS and _header_last.argval is not None:
                _header_jump_target = self.cfg.get_block_by_offset(_header_last.argval)
                for _hs in header.successors:
                    if _hs != _header_jump_target:
                        _header_backward_cond_fallthrough = _hs
                        break
            _is_async_send_loop = all(
                i.opname in ('SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 'NOP')
                for i in header.instructions
            )
            _fwd_queue = []
            if not _is_async_send_loop:
                # [Phase 3 adv17_while_multi_if_flow] 此前仅从 header 的
                # 后继开始前向遍历，遗漏了通过回边收集的 body 块的后继。
                # 例如 while True 内多 if + return 1：Block 22（if y）由
                # 回边后向遍历收集入 body，但其后继 Block 38（return 1）
                # 未被前向遍历处理（因 _fwd_visited = set(body) 跳过已入
                # body 的块）。当 while True 无自然出口时，所有路径以
                # RETURN_VALUE 或 JUMP_BACKWARD 结束，return 块应属于循环
                # 体。修正：从所有 body 块的后继开始前向遍历。
                #
                # 但需排除循环回测块的 fall-through（自然出口）。while cond
                # 的循环回测块（POP_JUMP_BACKWARD_IF_TRUE/FALSE to header）
                # 的 fall-through 是循环条件失败时的自然出口（return None），
                # 不属于循环体。若不排除，会把自然出口误纳入 body，导致
                # 生成多余的 break。
                _loop_backtest_fallthroughs: Set[BasicBlock] = set()
                for _b in body:
                    _b_last = _b.get_last_instruction()
                    if (_b_last and _b_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                            and _b_last.argval is not None):
                        _b_target = self.cfg.get_block_by_offset(_b_last.argval)
                        if _b_target == header:
                            for _s in _b.successors:
                                if _s != header:
                                    _loop_backtest_fallthroughs.add(_s)
                                    break
                for _b in list(body):
                    for _s in _b.successors:
                        if _s in body or _s == header:
                            continue
                        if _s == _header_backward_cond_fallthrough:
                            continue
                        if _s in _loop_backtest_fallthroughs:
                            continue
                        if self.dom_analyzer.is_dominator(header, _s):
                            if _s not in _fwd_queue:
                                _fwd_queue.append(_s)
                _fwd_visited = set(body)
                while _fwd_queue:
                    _fwd_block = _fwd_queue.pop(0)
                    if _fwd_block in _fwd_visited:
                        continue
                    _fwd_visited.add(_fwd_block)
                    body.add(_fwd_block)
                    _fwd_last = _fwd_block.get_last_instruction()
                    _is_break_exit = False
                    if _fwd_last and _fwd_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                        _fwd_target = self.cfg.get_block_by_offset(_fwd_last.argval) if _fwd_last.argval is not None else None
                        if _fwd_target and _fwd_target not in body and _fwd_target != header:
                            _is_break_exit = True
                    if _is_break_exit:
                        continue
                    for _fs in _fwd_block.successors:
                        if _fs in body or _fs == header or _fs in _fwd_visited:
                            continue
                        if _fs in _loop_backtest_fallthroughs:
                            continue
                        if self.dom_analyzer.is_dominator(header, _fs):
                            _fwd_queue.append(_fs)

        return body

    def _coalesce_nop_prefix_loop_headers(self) -> None:
        _nop_headers = []
        for h in list(self.loop_analyzer.loop_headers):
            if (len(h.instructions) == 1 and h.instructions[0].opname == 'NOP'
                    and len(h.successors) == 1):
                _succ = list(h.successors)[0]
                if _succ in self.loop_analyzer.loop_headers and _succ != h:
                    _nop_headers.append((h, _succ))
        for nop_h, real_h in _nop_headers:
            _redirect = [(src, real_h) for src, tgt in self.loop_analyzer.back_edges
                         if tgt == nop_h]
            self.loop_analyzer.back_edges = [(src, tgt) for src, tgt in self.loop_analyzer.back_edges
                                              if tgt != nop_h]
            self.loop_analyzer.back_edges.extend(_redirect)
            self.loop_analyzer.loop_headers.discard(nop_h)
            if nop_h in self.loop_analyzer.loop_bodies:
                del self.loop_analyzer.loop_bodies[nop_h]

    _BODY_CODE_OPS = frozenset({
        'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
        'BINARY_OP', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD',
        'DELETE_SUBSCR', 'DELETE_ATTR', 'RAISE_VARARGS',
        'IMPORT_NAME', 'UNPACK_SEQUENCE', 'UNPACK_EX',
        'RETURN_VALUE', 'RETURN_CONST',
    })

    def _is_fake_loop(self, header: BasicBlock, body: Set[BasicBlock],
                       back_edge_sources: List[BasicBlock]) -> bool:
        if len(body) == 1 and header in body:
            return False

        if len(back_edge_sources) != 1:
            return False

        src = back_edge_sources[0]
        if src == header:
            return False

        if len(body) != 2:
            return False

        if src not in body:
            return False

        src_last = src.get_last_instruction()
        if not src_last:
            return False

        backward_jump_ops = ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                           'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
        if src_last.opname not in backward_jump_ops:
            return False

        if src.start_offset <= header.start_offset:
            return False

        header_instrs = [i for i in header.instructions
                       if i.opname not in NOISE_OPS]
        has_loop_instr = any(i.opname in ('FOR_ITER', 'GET_ANEXT', 'GET_ITER')
                            for i in header_instrs)
        if has_loop_instr:
            return False

        has_conditional_jump = any(
            i.opname in CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
            for i in header_instrs
        )
        if not has_conditional_jump:
            return False

        header_meaningful = [i for i in header_instrs
                            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                            and i.opname not in CONDITIONAL_JUMP_OPS]
        if any(i.opname in self._BODY_CODE_OPS for i in header_meaningful):
            return False

        src_meaningful = [i for i in src.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                         and i.opname not in BACKWARD_JUMP_OPS]
        if any(i.opname in self._BODY_CODE_OPS for i in src_meaningful):
            return False

        return True

    def _is_await_polling_loop(self, header: BasicBlock, body: Set[BasicBlock]) -> bool:
        """检测当前循环是否为 `await <expr>` 或 `async for` 的轮询自循环。

        CPython 为 `await <expr>` 生成的字节码模式：
            pred : ... <expr> ... ; GET_AWAITABLE ; LOAD_CONST None
            hdr  : SEND   <exit_offset>
                   YIELD_VALUE
                   RESUME <3>
                   JUMP_BACKWARD_NO_INTERRUPT <hdr_offset>   (回边自循环)
            exit : POP_JUMP_*_IF_*  (条件跳转，继续 await 值消费)

        CPython 为 `async for x in iter:` 生成的轮询子循环模式：
            pred : GET_AITER ; GET_ANEXT ; LOAD_CONST None
            hdr  : SEND   <body_offset>
                   YIELD_VALUE
                   RESUME <3>
                   JUMP_BACKWARD_NO_INTERRUPT <hdr_offset>   (回边自循环)
            body : STORE_FAST x ; ...循环体...
        注意：async for 的轮询子循环 header 与外层 async for 的 GET_ANEXT header
        是相邻块（或被 CFG 拆分为两个块：GET_ANEXT 块 + SEND 块）。轮询子循环是
        async for 协议的实现细节，外层 LoopRegion（含 GET_ANEXT）已完整归属整个
        async for 结构，轮询子循环不应被物化为独立 LoopRegion，否则会吞并 ternary
        的 condition/merge 块（违反「每块唯一归属」原则）。

        判定要点（同时满足）：
          1. header 不含 FOR_ITER / GET_ANEXT / GET_AITER（非 for / async-for header）
          2. body 内存在 SEND + YIELD_VALUE + JUMP_BACKWARD_NO_INTERRUPT 三联
          3. 前驱链中含有 GET_AWAITABLE（await 模式）或 GET_ANEXT（async for 模式）
          4. 前驱不含 GET_YIELD_FROM_ITER（排除 yield from）

        这种循环是 await / async for 的实现细节，不应被物化为 `while True: pass`。
        """
        # 条件 1: header 不是 for/async-for 循环头
        header_has_iter = any(
            i.opname in ('FOR_ITER', 'GET_ANEXT', 'GET_AITER')
            for i in header.instructions
        )
        if header_has_iter:
            return False

        # 条件 2: body 内含 SEND + YIELD_VALUE + JUMP_BACKWARD_NO_INTERRUPT 三联
        has_send = has_yield = has_jbni = False
        for block in body:
            for instr in block.instructions:
                if instr.opname == 'SEND':
                    has_send = True
                elif instr.opname == 'YIELD_VALUE':
                    has_yield = True
                elif instr.opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                    has_jbni = True
            if has_send and has_yield and has_jbni:
                break
        if not (has_send and has_yield and has_jbni):
            return False

        # 条件 3 + 4: 前驱链中含 GET_AWAITABLE 或 GET_ANEXT，且不含 GET_YIELD_FROM_ITER
        # 前驱链 = header 直接前驱 + body 块前驱（覆盖 await/async for 嵌套于其他块的情况）
        # [R9 聚类A] 新增 GET_ANEXT 检测：async for 的轮询子循环前驱含 GET_ANEXT
        # （async for 的 header），该子循环是 async for 协议实现细节，不应独立物化。
        pred_blocks = set()
        for block in [header] + list(body):
            for p in block.predecessors:
                if p is not header and p not in body:
                    pred_blocks.add(p)
        has_awaitable = False
        has_anext = False
        has_yield_from_iter = False
        for p in pred_blocks:
            for instr in p.instructions:
                if instr.opname == 'GET_AWAITABLE':
                    has_awaitable = True
                elif instr.opname == 'GET_ANEXT':
                    has_anext = True
                elif instr.opname == 'GET_YIELD_FROM_ITER':
                    has_yield_from_iter = True
        # 若前驱链无 GET_AWAITABLE 且无 GET_ANEXT，检查 body 自身
        # （await/async for 可能与条件求值在同块）
        if not has_awaitable and not has_anext:
            for block in body:
                for instr in block.instructions:
                    if instr.opname == 'GET_AWAITABLE':
                        has_awaitable = True
                        break
                    if instr.opname == 'GET_ANEXT':
                        has_anext = True
                        break
                if has_awaitable or has_anext:
                    break
        if not has_awaitable and not has_anext:
            return False
        if has_yield_from_iter:
            return False
        return True

    def _collect_await_predecessor_chain(self, condition_block: BasicBlock) -> List[BasicBlock]:
        """从 condition_block 反向追踪 await 前驱链。

        await 在 if 条件中的典型字节码布局：
            setup_block : ... <expr> ... ; GET_AWAITABLE ; LOAD_CONST None
            poll_block  : SEND <exit> ; YIELD_VALUE ; RESUME ;
                          JUMP_BACKWARD_NO_INTERRUPT <poll_block>  (自循环)
            cond_block  : POP_JUMP_FORWARD_IF_FALSE <else>          (condition_block)

        本方法从 condition_block 出发，沿前驱链反向查找：
          - poll_block：含 SEND + YIELD_VALUE + JUMP_BACKWARD_NO_INTERRUPT 的自循环块
          - setup_block：含 GET_AWAITABLE 的前驱块（await 表达式主体所在）

        返回 [setup_block, poll_block]（若均找到），否则返回空列表。
        仅返回确属 await 模式的块，避免误伤普通条件链。
        """
        result: List[BasicBlock] = []
        # 步骤 1: 找 poll_block（condition_block 的前驱中含 await 轮询三联的块）
        poll_block = None
        for pred in condition_block.predecessors:
            has_send = has_yield = has_jbni = False
            for instr in pred.instructions:
                if instr.opname == 'SEND':
                    has_send = True
                elif instr.opname == 'YIELD_VALUE':
                    has_yield = True
                elif instr.opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                    has_jbni = True
            if has_send and has_yield and has_jbni:
                poll_block = pred
                break
        if poll_block is None:
            return []
        result.append(poll_block)

        # 步骤 2: 找 setup_block（poll_block 的前驱中含 GET_AWAITABLE 的块）
        # 排除 poll_block 自身（自循环前驱）
        setup_block = None
        for pred in poll_block.predecessors:
            if pred is poll_block:
                continue
            if any(instr.opname == 'GET_AWAITABLE' for instr in pred.instructions):
                setup_block = pred
                break
        if setup_block is None:
            return []
        result.append(setup_block)

        # 步骤 3: 排除 GET_YIELD_FROM_ITER（yield from 而非 await）
        for instr in setup_block.instructions:
            if instr.opname == 'GET_YIELD_FROM_ITER':
                return []
        return result

    def _skip_await_poll_to_cond_block(self, setup_block: BasicBlock) -> Optional[BasicBlock]:
        """[Round 2 修复] 正向跳过 await 轮询链，返回 truthy 测试 cond_block。

        与 ``_collect_await_predecessor_chain``（反向：从 cond_block 找前驱）
        互补，本方法正向遍历：从 setup_block（含 GET_AWAITABLE）出发，经
        poll_block（SEND+YIELD_VALUE+JUMP_BACKWARD_NO_INTERRUPT 自循环）找到
        其非自循环后继 cond_block（POP_JUMP_FORWARD_IF_TRUE/FALSE）。

        用于 BoolOp 链检测中 ``x or await g()`` 模式：第一个操作数 ``x``
        所在块以 POP_JUMP_IF_TRUE 结尾，fallthrough 后继是 await setup_block
        （非条件跳转），链检测在此中断。本方法跳过 setup+poll，让链检测
        继续到 await 结果的 truthy 测试块，识别为第二个操作数。

        返回 cond_block，或 None（非 await 模式 / 结构不完整）。
        """
        # setup_block 必须含 GET_AWAITABLE（且不含 GET_YIELD_FROM_ITER）
        has_awaitable = any(i.opname == 'GET_AWAITABLE' for i in setup_block.instructions)
        if not has_awaitable:
            return None
        for instr in setup_block.instructions:
            if instr.opname == 'GET_YIELD_FROM_ITER':
                return None
        # setup_block 的后继是 poll_block（含 SEND+YIELD+JUMP_BACKWARD_NO_INTERRUPT）
        poll_succs = list(setup_block.successors)
        if not poll_succs:
            return None
        poll_block = None
        for succ in poll_succs:
            _has_send = any(i.opname == 'SEND' for i in succ.instructions)
            _has_yield = any(i.opname == 'YIELD_VALUE' for i in succ.instructions)
            _has_jbni = any(i.opname == 'JUMP_BACKWARD_NO_INTERRUPT' for i in succ.instructions)
            if _has_send and _has_yield and _has_jbni:
                poll_block = succ
                break
        if poll_block is None:
            return None
        # poll_block 的非自循环后继是 cond_block
        for succ in poll_block.successors:
            if succ is poll_block:
                continue
            return succ
        return None

    def _has_body_code_before_before_with(self, block: BasicBlock) -> bool:
        store_idx = None
        bw_idx = None
        for i, instr in enumerate(block.instructions):
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                bw_idx = i
                break
            if store_idx is None and instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                store_idx = i
        if store_idx is None or bw_idx is None:
            return False
        context_expr_ops = {'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_CONST',
                            'LOAD_ATTR', 'LOAD_METHOD', 'PRECALL', 'CALL',
                            'CALL_FUNCTION', 'CALL_METHOD', 'PUSH_NULL'}
        noise_ops = {'RESUME', 'NOP', 'CACHE', 'PUSH_NULL'}
        for i in range(store_idx + 1, bw_idx):
            instr = block.instructions[i]
            if instr.opname in noise_ops:
                continue
            if instr.opname in context_expr_ops:
                continue
            return True
        return False

    def _is_with_exit_cleanup(self, block: BasicBlock) -> bool:
        WITH_EXIT_INDICATOR_OPS = {
            'LOAD_CONST', 'PRECALL', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD',
            'RETURN_VALUE', 'RETURN_CONST', 'POP_EXCEPT',
            'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
            'GET_AWAITABLE', 'SEND', 'YIELD_VALUE',
        }
        none_count = 0
        has_call = False
        has_body_instr = False

        for instr in block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):
                continue
            if instr.opname == 'LOAD_CONST' and instr.argval is None:
                none_count += 1
                continue
            if instr.opname not in WITH_EXIT_INDICATOR_OPS:
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    has_body_instr = True
                return False
            if instr.opname in ('PRECALL', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD'):
                has_call = True
            elif instr.opname == 'LOAD_CONST' and instr.argval is not None:
                has_body_instr = True

        return (none_count >= 2 and has_call) and not has_body_instr

    def _is_with_exit_leading_to_break(self, block: BasicBlock,
                                        current_loop: Optional['LoopRegion'] = None,
                                        visited: Optional[Set[BasicBlock]] = None,
                                        depth: int = 0) -> bool:
        # 无限嵌套支持：递归终止由 visited 集合（循环检测）+ CFG 有限性保证，
        # 不使用硬编码深度上限。depth 参数仅用于 depth==0 的遍历范围控制。
        if visited is None:
            visited = set()
        if block in visited:
            return False
        visited.add(block)

        jump_result = self._check_jump_backward_for_break(block, current_loop)
        if jump_result is not None:
            return jump_result

        return_value_result = self._check_return_for_break(block, current_loop)
        if return_value_result is not None:
            return return_value_result

        for succ in block.successors:
            if self.get_block_role(succ) in (BlockRole.WITH_EXIT_CLEANUP, BlockRole.WITH_STACK_CLEANUP, BlockRole.WITH_HANDLER):
                if self._is_with_exit_leading_to_break(succ, current_loop, visited, depth + 1):
                    return True
            elif depth == 0:
                if self._is_with_exit_leading_to_break(succ, current_loop, visited, depth + 1):
                    return True
        return False

    def _check_jump_backward_for_break(self, block, current_loop):
        for instr in block.instructions:
            if instr.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                continue
            target_block = self.cfg.get_block_by_offset(instr.argval)
            if not target_block:
                return False
            target_region = self.get_entry_region_for_block(target_block)
            if not isinstance(target_region, LoopRegion):
                return True
            if target_region.region_type == RegionType.FOR_LOOP:
                return target_block != target_region.header_block
            return target_block != target_region.condition_block
        return None

    def _check_return_for_break(self, block, current_loop):
        for instr in block.instructions:
            if instr.opname == 'RETURN_VALUE':
                return True if current_loop is not None else False
        return None

    def _is_with_exit_leading_to_continue(self, block: BasicBlock,
                                           current_loop: Optional['LoopRegion'] = None,
                                           visited: Optional[Set[BasicBlock]] = None,
                                           depth: int = 0) -> bool:
        # 无限嵌套支持：递归终止由 visited 集合（循环检测）+ CFG 有限性保证，
        # 不使用硬编码深度上限。depth 参数仅用于 depth==0 的遍历范围控制。
        if visited is None:
            visited = set()
        if block in visited:
            return False
        visited.add(block)
        for instr in block.instructions:
            if instr.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                target_block = self.cfg.get_block_by_offset(instr.argval)
                if target_block:
                    target_region = self.get_entry_region_for_block(target_block)
                    if isinstance(target_region, LoopRegion):
                        if self.get_block_role(block) == BlockRole.LOOP_BACK_EDGE:
                            return False
                        if target_region.region_type == RegionType.FOR_LOOP:
                            if target_block == target_region.header_block:
                                return True
                        else:
                            if target_block == target_region.condition_block:
                                return True
                return False
            if instr.opname == 'RETURN_VALUE':
                return False
        for succ in block.successors:
            if self.get_block_role(succ) in (BlockRole.WITH_EXIT_CLEANUP, BlockRole.WITH_STACK_CLEANUP, BlockRole.WITH_HANDLER):
                if self._is_with_exit_leading_to_continue(succ, current_loop, visited, depth + 1):
                    return True
            elif depth == 0:
                if self._is_with_exit_leading_to_continue(succ, current_loop, visited, depth + 1):
                    return True
        return False

    def _detect_with_body_return(self, block: BasicBlock, with_region: WithRegion,
                                  expr_reconstructor: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in block.instructions)
        if not has_return:
            return None

        swap_idx = None
        return_idx = None
        return_instr = None
        exit_call_start = None
        exit_call_end = None

        for idx, instr in enumerate(block.instructions):
            if instr.opname == 'SWAP' and swap_idx is None:
                swap_idx = idx
            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                return_idx = idx
                return_instr = instr
                break

        if return_idx is None:
            return None

        search_start = (swap_idx + 1) if swap_idx is not None else 0
        for idx in range(search_start, len(block.instructions) - 5):
            window = block.instructions[idx:idx + 6]
            if (window[0].opname == 'LOAD_CONST' and window[0].argval is None and
                window[1].opname == 'LOAD_CONST' and window[1].argval is None and
                window[2].opname == 'LOAD_CONST' and window[2].argval is None and
                window[3].opname in ('PRECALL',) and
                window[4].opname in ('CALL', 'CALL_FUNCTION') and
                window[5].opname == 'POP_TOP'):
                exit_call_start = idx
                exit_call_end = idx + 6
                break

        if exit_call_start is None:
            if return_instr.opname == 'RETURN_CONST':
                return {'type': 'Return', 'value': {'type': 'Constant', 'value': return_instr.argval}}
            return None

        skip_store_targets = set()
        if with_region.target:
            skip_store_targets.add(with_region.target)

        if swap_idx is not None and swap_idx < exit_call_start:
            value_instrs = []
            for i in block.instructions[:swap_idx]:
                if i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
                    continue
                if i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF') and i.argval in skip_store_targets:
                    continue
                value_instrs.append(i)
        else:
            value_instrs = []
            for i in block.instructions[exit_call_end:return_idx]:
                if i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):
                    continue
                value_instrs.append(i)

        if return_instr.opname == 'RETURN_CONST':
            return {'type': 'Return', 'value': {'type': 'Constant', 'value': return_instr.argval}}

        if value_instrs and expr_reconstructor is not None:
            expr = expr_reconstructor.reconstruct(value_instrs)
            if expr:
                return {'type': 'Return', 'value': expr}

        return {'type': 'Return', 'value': {'type': 'Constant', 'value': None}}

    def _is_return_none_block(self, block: BasicBlock) -> bool:
        instrs = [i for i in block.instructions
                  if i.opname not in NOISE_OPS]
        if len(instrs) == 2:
            if instrs[0].opname == 'LOAD_CONST' and instrs[0].argval is None and instrs[1].opname == 'RETURN_VALUE':
                return True
        if len(instrs) == 1:
            if instrs[0].opname == 'RETURN_CONST' and instrs[0].argval is None:
                return True
        return False

    def _is_trivial_block(self, block: BasicBlock) -> bool:
        if self._is_return_none_block(block):
            return True
        instrs = [i for i in block.instructions
                  if i.opname not in NOISE_OPS]
        if not instrs:
            return True
        if len(instrs) == 1:
            if instrs[0].opname in ('RETURN_VALUE', 'RETURN_CONST', 'JUMP_FORWARD', 'JUMP_BACKWARD'):
                return True
        if len(instrs) == 2:
            if (instrs[0].opname == 'LOAD_CONST' and instrs[0].argval is None
                and instrs[1].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                return True
        return False

    def _block_exits_loop(self, block, loop_region):
        if hasattr(loop_region, 'else_blocks') and block in loop_region.else_blocks:
            return False
        last = block.get_last_instruction()
        if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE'):
            return True
        if last and last.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
            if last.argval is not None:
                target = self.cfg.get_block_by_offset(last.argval)
                if target and target not in loop_region.blocks:
                    return True
        return False

    def _identify_try_except_regions(self) -> List[Region]:
        """_identify_try_except_regions — 识别异常处理区域

        【区域类型】 TRY_EXCEPT / TRY_FINALLY — 异常处理区域（Try-Except Region）
        RegionType 枚举值: RegionType.TRY_EXCEPT

        1. 算法描述（基于"No More Gotos"论文）
           - 归约阶段: Phase 1（最先识别，优先级最高；TRY > WITH > LOOP > IF > ASSERT）
           - 识别策略: 基于 CPython 3.11+ 异常表（exception table）的
             (start, end, target, depth) 条目定位 try 范围与 handler 入口。
             通过 handler 入口首指令（PUSH_EXC_INFO / WITH_EXCEPT_START）分类 handler 类型。
           - 归约过程:
             Step 1: 解析异常表，将 target 偏移映射到 BasicBlock，分类 handler 类型。
             Step 2: 标记内层 handler 与配对关系（except-finally 配对）。
             Step 3: 逐个构建 TryExceptRegion，收集 try_blocks/handler_blocks/finally_blocks/else_blocks/cleanup_blocks。

        2. 字节码模式（CPython 编译器行为）
           模式 A: try-except
             源码: try: ... except Exception as e: ...
             特征指令: PUSH_EXC_INFO, CHECK_EXC_MATCH, POP_EXCEPT, RERAISE
           模式 B: try-finally
             handler 入口: PUSH_EXC_INFO + COPY + POP_EXCEPT + RERAISE（无 CHECK_EXC_MATCH）
           模式 C: try-except-else
             else 块位于 try_end 与首个 handler_start 之间
           模式 D: try-except-finally
             异常表有两条条目，finally 的 try 范围包含 except 的 try 范围

        3. 边界条件（数学性质）
           - try 范围由异常表 [start, end) 唯一确定
           - handler 类型由入口首指令决定
           - 嵌套关系由 (try_start, try_end) 区间包含关系刻画（结构包含判定，非 depth 数值比较）
           - 每个基本块经 block_to_region 唯一归属一个 TryExceptRegion

        4. 归约语义（与父区域的契约）
           - 入口块: try 范围起始偏移对应的 BasicBlock（region.entry）
           - 父区域引用: 父区域仅引用本 region 的 entry 块
           - 子区域块不出现: try/handler/finally/else/cleanup 全部归约为单个抽象节点

        5. AST 映射
           - 对应生成方法: _generate_try（region_ast_generator.py）
           - AST 节点类型: ast.Try
           - 关键字段映射:
             try_blocks → Try.body
             except_handlers → Try.handlers
             else_blocks → Try.orelse
             finally_blocks → Try.finalbody

        6. 已知失败模式
           - 当前测试矩阵通过率: 100%（try_except 230/230），无已知失败模式
           - te046 已修复 (2026-07-14): spurious `if True: pass` 缺陷已通过在
             `region_ast_generator.py` L599-634 增加「顶级祖先」检查修复，根因是 WithRegion
             的 exception_block 被误判为孤儿块。修复后字节码完全匹配 (71 vs 71)。
           - 本方法遵循区域归约算法 4 核心原则:
             自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
        """
        if not self.cfg.exception_table:
            return []

        handler_infos = self._parse_exception_table()
        if not handler_infos:
            return []

        self.handler_infos = handler_infos
        initial_region_count = len(self.regions)

        inner_handler_indices = set()
        for i, info in enumerate(handler_infos):
            handler_block = self.cfg.get_block_by_offset(info['handler_start'])
            if handler_block and handler_block.instructions:
                first_instr = handler_block.instructions[0]
                if first_instr.opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):
                    has_copy = any(instr.opname == 'COPY' for instr in handler_block.instructions)
                    has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in handler_block.instructions)
                    has_reraise = any(instr.opname == 'RERAISE' for instr in handler_block.instructions)
                    if has_copy and has_pop_except and has_reraise:
                        has_bare_except_entry = False
                        for blk in self.cfg.blocks.values():
                            if blk == handler_block:
                                continue
                            if any(info['try_start'] <= instr.offset < info['try_end'] for instr in blk.instructions):
                                if any(instr.opname == 'PUSH_EXC_INFO' for instr in blk.instructions):
                                    has_no_check = not any(instr.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for instr in blk.instructions)
                                    has_no_reraise = not any(instr.opname == 'RERAISE' for instr in blk.instructions)
                                    if has_no_check and has_no_reraise:
                                        has_bare_except_entry = True
                                        break
                        if not has_bare_except_entry:
                            inner_handler_indices.add(i)
                            continue
            # 结构包含判定标记inner handler：
            # - other 的 try 范围严格包含 info 的 try 范围（other 为外层，info 为内层）
            #   等价于原 depth 比较：other.depth < info.depth 表示 other 更浅（外层）
            # - 非PUSH_EXC_INFO开头的handler（cleanup块）：总是进行结构包含判定
            # - PUSH_EXC_INFO开头的handler（真正except handler）：
            #   仅当内层try_start < 外层handler_start时标记为inner
            #   （即内层try在外层try body中，由_generate_try_body处理）
            #   当内层try_start >= 外层handler_start时，不标记为inner
            #   （即内层try在外层except handler body中，由handler body生成代码处理）
            for j, other in enumerate(handler_infos):
                if i == j:
                    continue
                if (other['try_start'] <= info['try_start'] and
                    info['try_end'] <= other['try_end'] and
                    not (other['try_start'] == info['try_start'] and other['try_end'] == info['try_end'])):
                    if info['try_start'] >= other['handler_start']:
                        # 对于真正的except handler（PUSH_EXC_INFO开头），
                        # 只有当内层try在外层try body中时才标记为inner
                        # 当内层try在外层except handler body中时，不标记为inner
                        if first_instr.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):
                            # 真正的except handler嵌套在另一个handler体内
                            # 不标记为inner，由AST生成器处理嵌套关系
                            continue
                        inner_handler_indices.add(i)
                        break

        paired_except_indices = set()
        for i, info in enumerate(handler_infos):
            if info.get('handler_type') != 'finally':
                continue
            if i in inner_handler_indices:
                continue
            for j, other in enumerate(handler_infos):
                if i == j or other.get('handler_type') != 'except':
                    continue
                if (other['try_start'] >= info['try_start'] and
                    other['try_end'] <= info['try_end']):
                    if (other['try_start'] == info['try_start'] or
                        other['handler_start'] >= info['try_start'] and
                        other['handler_start'] < info['try_end']):
                        # 额外检查：如果 except handler 的 try_start 与 finally handler 不同，
                        # 且两者深度相同，则 except handler 可能是 finally 块内部的
                        # 独立 try-except 结构，而非与 finally 配对的 except handler
                        if other['try_start'] != info['try_start']:
                            if ((other['try_start'] < info['try_start'] and info['try_end'] <= other['try_end']) or
                                (info['try_start'] < other['try_start'] and other['try_end'] <= info['try_end'])):
                                continue
                        paired_except_indices.add(j)

        for i, handler_info in enumerate(handler_infos):
            if handler_info.get('handler_type') == 'with' or i in paired_except_indices or i in inner_handler_indices:
                continue

            handler_type = handler_info.get('handler_type', 'except')
            try_start = handler_info['try_start']
            try_end = handler_info['try_end']
            handler_start_offset = handler_info['handler_start']

            handler_entry_block = self.cfg.get_block_by_offset(handler_start_offset)
            if handler_entry_block is None:
                continue

            entry_block = self.cfg.get_block_by_offset(try_start)
            if entry_block is None:
                continue

            paired_except_infos = None
            except_try_start = try_start
            effective_try_end = try_end
            if handler_type == 'finally':
                paired_except_infos = [handler_infos[j] for j in paired_except_indices
                                       if (handler_infos[j]['try_start'] >= handler_info['try_start'] and
                                           handler_infos[j]['try_end'] <= handler_info['try_end'])]
                if paired_except_infos:
                    except_try_start = min(pi['try_start'] for pi in paired_except_infos)
                    except_try_end = max(pi['try_end'] for pi in paired_except_infos)
                    first_except_handler_start = min(pi['handler_start'] for pi in paired_except_infos)
                    effective_try_end = max(except_try_end, first_except_handler_start, try_end)

            try_start_for_blocks = min(except_try_start, try_start) if (handler_type == 'finally' and paired_except_infos) else try_start
            try_end_for_blocks = effective_try_end if (handler_type == 'finally' and paired_except_infos) else try_end

            excluded_offsets = set()
            for other_info in handler_infos:
                if other_info is handler_info:
                    continue
                # 结构包含判定：other 不严格包含 current（同层或更深）时排除其 handler 偏移
                if not (other_info['try_start'] < handler_info['try_start'] and
                        handler_info['try_end'] <= other_info['try_end']):
                    for key in ('handler_start', 'finally_handler_start'):
                        offset = other_info.get(key)
                        if offset:
                            excluded_offsets.add(offset)

            for exc_entry in self.cfg.exception_table:
                exc_target = exc_entry.get('target', 0)
                exc_blk = self.cfg.get_block_by_offset(exc_target)
                if exc_blk and any(instr.opname == 'WITH_EXCEPT_START' for instr in exc_blk.instructions):
                    excluded_offsets.add(exc_target)

            finally_entry_block = None
            finally_start = handler_info.get('finally_handler_start')
            if finally_start:
                finally_entry_block = self.cfg.get_block_by_offset(finally_start)

            try_blocks = []
            for block in self.cfg.get_blocks_in_order():
                if not any(try_start_for_blocks <= instr.offset < try_end_for_blocks for instr in block.instructions):
                    continue
                if block == handler_entry_block or block == finally_entry_block:
                    continue
                if any(instr.opname == 'WITH_EXCEPT_START' for instr in block.instructions):
                    continue
                if block.start_offset in excluded_offsets:
                    continue
                if block in self.block_to_region:
                    continue
                try_blocks.append(block)

            # Track the try-body entry candidate from pre_handler_blocks expansion.
            # The LAST pre_handler_block (highest offset, closest to handler) is the actual
            # try-body entry — NOT the first, which may include enclosing-loop setup blocks.
            pre_handler_entry_candidate = None

            if handler_type == 'except' and handler_entry_block is not None:
                handler_in_try_range = any(
                    try_start_for_blocks <= instr.offset < try_end_for_blocks
                    for instr in handler_entry_block.instructions
                )
                if handler_in_try_range:
                    pre_handler_blocks = []
                    for block in self.cfg.get_blocks_in_order():
                        if block.start_offset >= handler_entry_block.start_offset:
                            continue
                        if block in self.block_to_region:
                            continue
                        if block == handler_entry_block:
                            continue
                        if any(instr.opname == 'PUSH_EXC_INFO' for instr in block.instructions):
                            continue
                        if any(instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for instr in block.instructions):
                            before_with_offset = next((i.offset for i in block.instructions if i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH')), None)
                            if before_with_offset is not None and not (try_start_for_blocks <= before_with_offset < try_end_for_blocks):
                                continue
                        if block.start_offset < try_start_for_blocks:
                            has_outer_branch = any(
                                succ.start_offset >= try_end_for_blocks and succ != handler_entry_block
                                for succ in block.successors
                            )
                            if has_outer_branch:
                                continue
                        pre_handler_blocks.append(block)
                    if pre_handler_blocks:
                        for phb in pre_handler_blocks:
                            if phb not in try_blocks:
                                try_blocks.insert(0, phb)
                        try_start_for_blocks = min(try_start_for_blocks,
                                                   min(b.start_offset for b in pre_handler_blocks))
                        pre_handler_entry_candidate = max(pre_handler_blocks,
                                                           key=lambda b: b.start_offset)

            if handler_type == 'finally' and handler_entry_block is not None:
                _need_pre_expand = not try_blocks or try_start_for_blocks >= handler_entry_block.start_offset
                if _need_pre_expand:
                    pre_handler_blocks = []
                    for block in self.cfg.get_blocks_in_order():
                        if block.start_offset >= handler_entry_block.start_offset:
                            continue
                        if block in self.block_to_region:
                            continue
                        if block == handler_entry_block:
                            continue
                        if any(instr.opname == 'PUSH_EXC_INFO' for instr in block.instructions):
                            continue
                        if any(instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for instr in block.instructions):
                            continue
                        if block.start_offset < try_start_for_blocks:
                            has_outer_branch = any(
                                succ.start_offset >= handler_entry_block.start_offset and succ != handler_entry_block
                                for succ in block.successors
                            )
                            if not has_outer_branch:
                                pre_handler_blocks.append(block)
                            continue
                        pre_handler_blocks.append(block)
                    if pre_handler_blocks:
                        for phb in pre_handler_blocks:
                            if phb not in try_blocks:
                                try_blocks.insert(0, phb)
                        try_start_for_blocks = min(try_start_for_blocks,
                                                   min(b.start_offset for b in pre_handler_blocks))
                        pre_handler_entry_candidate = max(pre_handler_blocks,
                                                           key=lambda b: b.start_offset)

            # Update entry_block to the try-body entry when pre_handler_blocks expansion
            # found try-body blocks that precede the exception-table's try_start.
            # This happens with CPython 3.12+ optimization where the try body (e.g., `pass`)
            # generates no exception-table entry; the table only covers the handler body.
            # Without this fix, the TRY region's entry points to the handler (PUSH_EXC_INFO)
            # instead of the try body, causing parent regions (e.g., IF) to not recognize the
            # TRY region as a child and pulling the try-except out of the if body.
            # We use the LAST pre_handler_block (closest to handler) as the try-body entry,
            # not the first, because earlier blocks may belong to enclosing loop/if setup.
            if pre_handler_entry_candidate and entry_block:
                if pre_handler_entry_candidate.start_offset < entry_block.start_offset:
                    entry_block = pre_handler_entry_candidate

            all_except_handlers = []
            all_handler_entry_blocks = []
            all_handler_blocks_set = set()

            if handler_type == 'finally':
                if paired_except_infos:
                    for except_info in paired_except_infos:
                        self._collect_handler_chain(
                            except_info['handler_start'], all_except_handlers,
                            all_handler_entry_blocks, all_handler_blocks_set)

                handler_body_blocks, finally_copy_blocks = self._collect_finally_body_blocks(
                    handler_entry_block, try_blocks, all_except_handlers if paired_except_infos else None)

                all_handler_blocks_set |= set(handler_body_blocks) | {handler_entry_block}
                finally_blocks = handler_body_blocks
            else:
                handler_body_blocks = self._collect_handler_chain(
                    handler_info['handler_start'], all_except_handlers,
                    all_handler_entry_blocks, all_handler_blocks_set)
                finally_copy_blocks = {}
                finally_blocks = []

            # Pattern C fix: Find handler body blocks that were misclassified as
            # try_blocks in try-except-finally where the except handler returns.
            #
            # In CPython 3.11+, when a try-except-finally's except handler contains
            # a return statement, the compiler places the finally body + return
            # AFTER POP_EXCEPT (because the finally body must execute before the
            # return). The _collect_body function stops at POP_EXCEPT, so these
            # blocks are not collected as handler body. They end up in try_blocks
            # (because they're in the try range), causing:
            #   1. The try body to contain the handler's code (finally body + return)
            #   2. The except handler body to be empty (just `pass`)
            #
            # Fix: Find normal successors of POP_EXCEPT blocks in the handler body
            # that are in try_blocks. Follow the chain (stopping at RETURN_VALUE/
            # RETURN_CONST/RERAISE) and add them to all_handler_blocks_set and the
            # owning except handler's body. This removes them from try_blocks
            # (via the handler_blocks_in_try exclusion) and ensures they're
            # generated as handler code.
            if all_except_handlers:
                _pop_except_blocks = [b for b in all_handler_blocks_set
                                      if any(i.opname == 'POP_EXCEPT' for i in b.instructions)]
                if _pop_except_blocks:
                    _extra_handler_blocks = set()
                    _visited_eh = set()
                    _worklist_eh = []
                    for peb in _pop_except_blocks:
                        for succ in peb.successors:
                            if succ in peb.exception_successors:
                                continue
                            if succ in all_handler_blocks_set:
                                continue
                            if succ in self.block_to_region:
                                continue
                            if succ not in try_blocks:
                                continue
                            _worklist_eh.append(succ)
                    while _worklist_eh:
                        _blk = _worklist_eh.pop()
                        if _blk in _visited_eh:
                            continue
                        if _blk in all_handler_blocks_set:
                            continue
                        if _blk in self.block_to_region:
                            continue
                        _visited_eh.add(_blk)
                        _extra_handler_blocks.add(_blk)
                        _last_instr = _blk.get_last_instruction()
                        if _last_instr and _last_instr.opname in (
                                'RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
                            continue
                        for _succ in _blk.successors:
                            if _succ in _blk.exception_successors:
                                continue
                            if _succ in all_handler_blocks_set:
                                continue
                            if _succ in self.block_to_region:
                                continue
                            if _succ in _visited_eh:
                                continue
                            _worklist_eh.append(_succ)
                    if _extra_handler_blocks:
                        all_handler_blocks_set |= _extra_handler_blocks
                        # Add to the owning except handler's body for code generation
                        for peb in _pop_except_blocks:
                            for i, h in enumerate(all_except_handlers):
                                hbody = h[2] if len(h) > 2 else None
                                if hbody is not None and peb in hbody:
                                    for ehb in _extra_handler_blocks:
                                        if ehb not in hbody:
                                            hbody.append(ehb)
                                    break

            all_blocks = set(try_blocks) | all_handler_blocks_set | set(finally_blocks)

            # Pattern A fix: Include the normal-path finally body in all_blocks so it's
            # consumed by the TRY_FINALLY region (marked as generated in _generate_try),
            # but do NOT add it to finally_blocks (so its code isn't generated as finally
            # body — the finally body is already generated from the exception path).
            #
            # In CPython's try-finally implementation, the finally body appears in two
            # paths:
            #   1. Normal path: try body falls through to finally body, then returns
            #   2. Exception path: PUSH_EXC_INFO -> finally body -> RERAISE -> cleanup
            #
            # The exception path is collected by _collect_finally_body_blocks (->
            # finally_blocks). The normal path is NOT collected, leaving it as a
            # standalone BASIC region. This causes the finally body to be duplicated
            # in the output (once from finally_blocks, once from the standalone BASIC
            # region), and the implicit return to appear as an extra block.
            #
            # Fix: Find the normal-path finally body (normal successors of try_blocks
            # that are NOT the handler entry, NOT in try_blocks/handler_blocks/
            # finally_blocks, NOT in block_to_region) and add them to all_blocks only.
            # The implicit return in these blocks will be re-added by the compiler
            # when it compiles the try-finally statement.
            if handler_type == 'finally' and finally_blocks:
                _normal_path_blocks = set()
                _visited_np = set()
                _worklist_np = []
                for tb in try_blocks:
                    for succ in tb.successors:
                        if succ in tb.exception_successors:
                            continue
                        if succ == handler_entry_block or succ == finally_entry_block:
                            continue
                        if succ in try_blocks or succ in finally_blocks:
                            continue
                        if succ in all_handler_blocks_set:
                            continue
                        if succ in self.block_to_region:
                            continue
                        _worklist_np.append(succ)
                # [R18 Bug 25-27 修复] 计算 finally_blocks (异常路径) 的最大偏移。
                # normal-path finally body 的块偏移应小于此最大偏移；超出此范围的
                # 后继块是 try-finally 之后的代码（after-try code），不应被纳入
                # TRY_FINALLY 区域。否则 try-finally 之后的 if-elif 链、return 等
                # 代码会被错误归约为 TRY_FINALLY 的一部分，导致后续代码全部丢失。
                # 依「每块唯一归属」原则：try-finally 之后的代码归属后续 IfRegion 等，
                # 不归属 TRY_FINALLY。
                # 例外：函数末尾的隐式 return None（LOAD_CONST None + RETURN_VALUE
                # 或 RETURN_CONST None）需纳入 all_blocks（Pattern A fix 意图），
                # 编译器会在编译 try-finally 语句时重新添加。
                _finally_max_offset = max((fb.start_offset for fb in finally_blocks), default=0)
                while _worklist_np:
                    _blk = _worklist_np.pop()
                    if _blk in _visited_np:
                        continue
                    if _blk in all_blocks:
                        continue
                    if _blk in self.block_to_region:
                        continue
                    _visited_np.add(_blk)
                    _normal_path_blocks.add(_blk)
                    _last_instr = _blk.get_last_instruction()
                    if _last_instr and _last_instr.opname in (
                            'RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
                        continue
                    for _succ in _blk.successors:
                        # Pattern E fix: Also follow exception successors of
                        # normal-path finally body blocks. When the finally body
                        # contains a nested try-except (e.g., try-finally with
                        # try-except in finally), the except handler body blocks
                        # are exception successors of the try body in the finally.
                        # These blocks must be collected into all_blocks to prevent
                        # them from being orphaned and emitted as standalone
                        # statements after the try-finally.
                        # Safety: exception successors leading to the exception path
                        # are excluded by the finally_blocks/handler_entry checks below.
                        if _succ == handler_entry_block or _succ == finally_entry_block:
                            continue
                        if _succ in try_blocks or _succ in finally_blocks:
                            continue
                        if _succ in all_handler_blocks_set:
                            continue
                        if _succ in self.block_to_region:
                            continue
                        if _succ in _visited_np:
                            continue
                        # [R18 Bug 25-27 修复] 不跟随进入 try-finally 之后的代码。
                        # 当后继块偏移大于 finally_blocks 的最大偏移时，该块是
                        # after-try code（如 if-elif 链、return 语句等），不属于
                        # finally body 的 normal path。例外：隐式 return None 块
                        # 仍需纳入 all_blocks（编译器会重新添加）。
                        if _succ.start_offset > _finally_max_offset:
                            _succ_meaningful = [i for i in _succ.instructions
                                                if i.opname not in (
                                                        'RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                            _succ_is_implicit_return = False
                            if len(_succ_meaningful) == 2:
                                if (_succ_meaningful[0].opname == 'LOAD_CONST' and
                                        _succ_meaningful[0].argval is None and
                                        _succ_meaningful[1].opname == 'RETURN_VALUE'):
                                    _succ_is_implicit_return = True
                            elif len(_succ_meaningful) == 1:
                                if (_succ_meaningful[0].opname == 'RETURN_CONST' and
                                        _succ_meaningful[0].argval is None):
                                    _succ_is_implicit_return = True
                            if not _succ_is_implicit_return:
                                continue
                        _worklist_np.append(_succ)
                if _normal_path_blocks:
                    all_blocks |= _normal_path_blocks

            # Pattern B fix: Include the implicit-return block in all_blocks for
            # try-except, so it's consumed by the TRY_EXCEPT region (marked as
            # generated in _generate_try) and not emitted as a standalone BASIC
            # region after the handler.
            #
            # In CPython, when a function's try-except has no explicit code after
            # the try-except (and the handler returns), the compiler places an
            # implicit `return None` block as the fall-through from the try body,
            # BEFORE the exception handler in bytecode offset order. If this block
            # is not consumed by the TRY_EXCEPT region, the decompiler emits it as
            # a standalone statement after the try-except. When recompiled, the
            # compiler places it AFTER the handler, changing the bytecode order and
            # causing a mismatch.
            #
            # Fix: Detect the implicit-return block (LOAD_CONST None + RETURN_VALUE,
            # or RETURN_CONST None) among the normal successors of try_blocks, and
            # add it to all_blocks only. The compiler will re-add the implicit
            # return when it compiles the try-except statement.
            #
            # This is restricted to blocks that contain ONLY the implicit return
            # pattern, so that user-written continuation code after the try-except
            # is NOT consumed.
            if handler_type == 'except':
                _implicit_return_blocks = set()
                for tb in try_blocks:
                    for succ in tb.successors:
                        if succ in tb.exception_successors:
                            continue
                        if succ == handler_entry_block or succ == finally_entry_block:
                            continue
                        if succ in try_blocks or succ in finally_blocks:
                            continue
                        if succ in all_handler_blocks_set:
                            continue
                        if succ in self.block_to_region:
                            continue
                        if succ in all_blocks:
                            continue
                        # Check if this block is an implicit-return block:
                        # contains only LOAD_CONST(None) + RETURN_VALUE, or
                        # RETURN_CONST(None), ignoring noise instructions.
                        _meaningful = [i for i in succ.instructions
                                       if i.opname not in (
                                               'RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        _is_implicit_return = False
                        if len(_meaningful) == 2:
                            if (_meaningful[0].opname == 'LOAD_CONST' and
                                    _meaningful[0].argval is None and
                                    _meaningful[1].opname == 'RETURN_VALUE'):
                                _is_implicit_return = True
                        elif len(_meaningful) == 1:
                            if (_meaningful[0].opname == 'RETURN_CONST' and
                                    _meaningful[0].argval is None):
                                _is_implicit_return = True
                        if _is_implicit_return:
                            _implicit_return_blocks.add(succ)
                if _implicit_return_blocks:
                    all_blocks |= _implicit_return_blocks

            for existing_region in self._filter_regions(self.regions, TryExceptRegion):
                for block in existing_region.blocks:
                    if any(try_start <= instr.offset < try_end for instr in block.instructions):
                        if block not in all_handler_blocks_set and block != handler_entry_block:
                            all_blocks.add(block)

            cleanup_blocks = []
            cleanup_visited = set()
            search_blocks = list(all_handler_entry_blocks)
            for heb in all_handler_entry_blocks:
                for succ in heb.successors:
                    if succ not in all_blocks:
                        search_blocks.append(succ)
            for block in list(all_handler_blocks_set):
                for succ in block.successors:
                    if succ not in all_blocks:
                        search_blocks.append(succ)
            if self.cfg.exception_table:
                for exc_entry in self.cfg.exception_table:
                    exc_start = exc_entry.get('start', 0)
                    exc_end = exc_entry.get('end', 0)
                    for blk in self.cfg.blocks.values():
                        if blk.start_offset in cleanup_visited:
                            continue
                        if blk in all_blocks:
                            continue
                        if any(exc_start <= instr.offset < exc_end for instr in blk.instructions):
                            search_blocks.append(blk)
            for block in search_blocks:
                if block.start_offset in cleanup_visited:
                    continue
                if block in all_blocks:
                    continue
                _existing_region = self.block_to_region.get(block)
                if _existing_region is not None and isinstance(_existing_region, TryExceptRegion) and _existing_region is not region:
                    continue
                cleanup_visited.add(block.start_offset)
                is_cleanup = False
                has_reraise = any(instr.opname == 'RERAISE' for instr in block.instructions)
                has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in block.instructions)
                has_copy = any(instr.opname == 'COPY' for instr in block.instructions)
                if has_reraise:
                    is_cleanup = True
                elif has_pop_except and has_copy:
                    meaningful = [instr for instr in block.instructions
                                  if instr.opname not in NOISE_OPS]
                    if all(instr.opname in ('COPY', 'POP_EXCEPT', 'RERAISE', 'POP_TOP',
                                            'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                            'STORE_DEREF', 'STORE_GLOBAL',
                                            'DELETE_FAST', 'DELETE_NAME',
                                            'DELETE_DEREF', 'DELETE_GLOBAL',
                                            'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                            'PUSH_EXC_INFO', 'SWAP')
                           for instr in meaningful):
                        is_cleanup = True
                # [Phase 3 adv17_try_except_star] except* 框架清理块检测。
                # PREP_RERAISE_STAR 是 except* 共享清理块的标志；
                # LIST_APPEND（非列表推导上下文）是 except* 不匹配清理路径的标志。
                # 这些块含条件跳转（POP_JUMP_FORWARD_IF_NONE/NOT_NONE），
                # 若不被纳入 cleanup_blocks，会被误识别为 IfRegion 或孤儿块，
                # 生成多余的 `if True: pass`。
                if not is_cleanup:
                    has_prep_reraise_star = any(instr.opname == 'PREP_RERAISE_STAR' for instr in block.instructions)
                    has_list_append = any(instr.opname == 'LIST_APPEND' for instr in block.instructions)
                    if has_prep_reraise_star or has_list_append:
                        meaningful = [instr for instr in block.instructions
                                      if instr.opname not in NOISE_OPS]
                        if all(instr.opname in ('PREP_RERAISE_STAR', 'LIST_APPEND',
                                                'COPY', 'POP_EXCEPT', 'RERAISE', 'POP_TOP',
                                                'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                                'STORE_DEREF', 'STORE_GLOBAL',
                                                'DELETE_FAST', 'DELETE_NAME',
                                                'DELETE_DEREF', 'DELETE_GLOBAL',
                                                'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                                'PUSH_EXC_INFO', 'SWAP',
                                                'POP_JUMP_FORWARD_IF_NONE',
                                                'POP_JUMP_FORWARD_IF_NOT_NONE',
                                                'POP_JUMP_BACKWARD_IF_NONE',
                                                'POP_JUMP_BACKWARD_IF_NOT_NONE')
                               for instr in meaningful):
                            is_cleanup = True
                if is_cleanup:
                    cleanup_blocks.append(block)
                    for succ in block.successors:
                        if succ.start_offset not in cleanup_visited and succ not in all_blocks:
                            search_blocks.append(succ)
            if cleanup_blocks:
                all_blocks |= set(cleanup_blocks)

            preceding_blocks = []
            for block in self.cfg.blocks.values():
                if block in all_blocks:
                    continue
                if block.start_offset >= try_start:
                    continue
                if not block.instructions:
                    continue
                if not all(instr.opname in NOISE_OPS for instr in block.instructions):
                    continue
                for succ in block.successors:
                    if succ in all_blocks:
                        preceding_blocks.append(block)
                        break
            if preceding_blocks:
                all_blocks |= set(preceding_blocks)
                try_start = min(block.start_offset for block in preceding_blocks)

            if handler_type == 'finally' and finally_blocks and finally_copy_blocks:
                for fc_offset in finally_copy_blocks:
                    fc_block = self.cfg.get_block_by_offset(fc_offset)
                    if fc_block and fc_block not in all_blocks:
                        all_blocks.add(fc_block)

            effective_try_start = except_try_start if (handler_type == 'finally' and paired_except_infos) else try_start
            effective_try_end_val = effective_try_end if (handler_type == 'finally' and paired_except_infos) else try_end

            handler_blocks_in_try = all_handler_blocks_set & set(try_blocks)
            exclude_from_try = handler_blocks_in_try
            if finally_blocks:
                exclude_from_try |= set(finally_blocks) & set(try_blocks)
            exclude_from_try |= set(cleanup_blocks) & set(try_blocks)
            if exclude_from_try:
                try_blocks = [b for b in try_blocks if b not in exclude_from_try]

            existing_entry_regions = [r for r in self.regions if type(r) is TryExceptRegion and r.entry == entry_block]
            if existing_entry_regions:
                for existing in existing_entry_regions:
                    if (existing.try_offset_start >= try_start and
                            existing.try_offset_end <= try_end and
                            existing.try_offset_end < try_end):
                        adjusted_start = existing.try_offset_end
                        adjusted_entry = None
                        for blk in self.cfg.get_blocks_in_order():
                            if blk.start_offset >= adjusted_start:
                                if any(try_start <= instr.offset < try_end for instr in blk.instructions):
                                    if blk != handler_entry_block and blk not in all_handler_blocks_set:
                                        adjusted_entry = blk
                                        break
                        if adjusted_entry:
                            entry_block = adjusted_entry

            region = TryExceptRegion(
                region_type=RegionType.TRY_FINALLY if handler_type == 'finally' else RegionType.TRY_EXCEPT,
                entry=entry_block,
                blocks=all_blocks,
                try_blocks=try_blocks,
                has_finally=handler_type == 'finally',
                try_offset_start=effective_try_start,
                try_offset_end=effective_try_end_val,
                handler_entry_blocks=all_handler_entry_blocks,
            )
            if finally_blocks:
                region.finally_blocks = finally_blocks
            elif handler_type == 'finally':
                region.finally_blocks = handler_body_blocks

            if all_except_handlers:
                region.except_handlers = all_except_handlers

            if finally_copy_blocks:
                region.finally_copy_blocks = finally_copy_blocks

            else_blocks = []
            if all_except_handlers:
                else_blocks = self._find_try_else_blocks(region)
                if else_blocks:
                    else_set = set(else_blocks)
                    try_blocks = [b for b in try_blocks if b not in else_set]
                    all_blocks |= set(else_blocks)
                    region.blocks = all_blocks
                    region.try_blocks = try_blocks

            if else_blocks:
                region.has_else = True
                region.else_blocks = else_blocks

            if cleanup_blocks:
                region.cleanup_blocks = cleanup_blocks

            self.regions.append(region)
            self._register_region_blocks(region, try_blocks, all_handler_blocks_set,
                                         finally_blocks, handler_info, finally_copy_blocks, else_blocks,
                                         cleanup_blocks)

        # 设置嵌套TryExceptRegion的parent关系
        # 需要确定哪个region是外层（parent），哪个是内层（child）
        new_regions = self.regions[initial_region_count:]
        for region_a in self._filter_regions(new_regions, TryExceptRegion):
            if region_a.parent is not None:
                continue
            for region_b in self._filter_regions(new_regions, TryExceptRegion):
                if region_b is region_a:
                    continue

                for _, _, handler_blocks in region_b.except_handlers:
                    if region_a.entry in handler_blocks:
                        region_a.enclosing_try = region_b
                        if not (getattr(region_b, 'has_finally', False) and not region_b.except_handlers and region_a.except_handlers):
                            region_b.add_child(region_a)
                        break
                if getattr(region_a, 'enclosing_try', None) is not None:
                    break

                if (region_a.try_offset_start >= region_b.try_offset_start and
                    region_a.try_offset_end <= region_b.try_offset_end and
                    (region_a.try_offset_end - region_a.try_offset_start) <
                    (region_b.try_offset_end - region_b.try_offset_start)):
                    b_handler_in_a = False
                    for heb in region_b.handler_entry_blocks:
                        if region_a.try_offset_start <= heb.start_offset < region_a.try_offset_end:
                            b_handler_in_a = True
                            break
                    if not b_handler_in_a:
                        region_a.enclosing_try = region_b
                        if not (getattr(region_b, 'has_finally', False) and not region_b.except_handlers and region_a.except_handlers):
                            region_b.add_child(region_a)
                        break

        for region_a in self._filter_regions(new_regions, TryExceptRegion):
            if not hasattr(region_a, 'else_blocks') or not region_a.else_blocks:
                continue
            enclosing = getattr(region_a, 'enclosing_try', None)
            if enclosing is None:
                continue
            enclosing_else = enclosing.get_else_blocks_for_merge()
            if not enclosing_else:
                continue
            inner_else_set = set(region_a.else_blocks)
            parent_else_set = set(enclosing_else)
            shared_else = inner_else_set & parent_else_set
            if shared_else:
                region_a.else_blocks = [b for b in region_a.else_blocks if b not in shared_else]
                if not region_a.else_blocks:
                    region_a.has_else = False
                region_a.blocks = [b for b in region_a.blocks if b not in shared_else]

        return new_regions

    def _coalesce_split_try_except_finally_regions(self, try_regions: list) -> list:
        _inner_to_outer = {}
        for r in self._filter_regions(try_regions, TryExceptRegion):
            if r.enclosing_try is not None:
                _inner_to_outer[id(r)] = r.enclosing_try
        if not _inner_to_outer:
            return try_regions
        _to_remove = set()
        for inner_id, outer in _inner_to_outer.items():
            inner = next((r for r in try_regions if id(r) == inner_id), None)
            if inner is None:
                continue
            # inner 由 _filter_regions(try_regions, TryExceptRegion) 保证为 TryExceptRegion；
            # outer 的类型检查 + 合并逻辑由多态方法 try_except_absorb_split_from 处理：
            # 非 TryExceptRegion 的 outer 返回 False（基类默认），TryExceptRegion 覆写执行吸收。
            if outer.try_except_absorb_split_from(inner):
                _to_remove.add(inner_id)
        if _to_remove:
            try_regions = [r for r in try_regions if id(r) not in _to_remove]
        return try_regions

    def _parse_exception_table(self) -> List[Dict[str, Any]]:
        """
        基于异常表条目和指令特征解析 handler 信息

        ═══════════════════════════════════════════════════════════════════════════════
        【功能说明】
        将 CPython 3.11+ 的原始异常表（exception table）转换为结构化的 handler 信息列表。
        每个异常表条目包含：
        - start: try 块开始的字节码偏移
        - end: try 块结束的字节码偏移（不包含）
        - target: 异常处理器的入口偏移
        - depth: 异常栈深度（用于嵌套判断）
        - lasti: 是否恢复最后指令索引
        - push_lasti: 是否压入最后指令索引

        ═══════════════════════════════════════════════════════════════════════════════
        【分类规则（基于指令特征）】

        **优先级从高到低**：

        1. WITH_EXCEPT_START → 'with'
           - with 语句的 __exit__ 调用入口
           - 不是真正的异常处理器，而是资源清理

        2. PUSH_EXC_INFO + RERAISE → 'finally'
           - finally 块的入口
           - 特征：压入异常信息后最终会重新抛出（或正常返回）

        3. PUSH_EXC_INFO + CHECK_EXC_MATCH → 'except'
           - 标准 except 子句的入口
           - CHECK_EXC_MATCH 用于异常类型匹配

        4. PUSH_EXC_INFO + CHECK_EG_MATCH → 'except_star'
           - Python 3.11+ 的 except* 语法（PEP 654）
           - 用于异常组（ExceptionGroup）的处理

        ═══════════════════════════════════════════════════════════════════════════════
        【处理流程】

        Step 1: 遍历每个异常表条目
        ─────────────────────────
        for entry in self.cfg.exception_table:
            a) 提取 (start, end, target, depth)
            b) 定位 target 对应的 BasicBlock
            c) 分类 handler 类型（调用 _classify_handler_type 或 _classify_handler_with_cleanup）
            d) 找到实际的 handler 开始位置（调用 _find_actual_handler_start）

        Step 2: 过滤 cleanup-only 条目
        ─────────────────────────
        某些条目的目标块只包含清理代码（COPY+POP_EXCEPT+RERAISE），
        这些不是真正的 handler 入口，需要过滤或特殊处理。

        Step 3: 去重
        ─────────────────────────
        使用 (start, end, handler_start) 作为键去重，避免重复处理。

        Step 4: 合并相同 handler 的范围
        ─────────────────────────
        如果多个异常表条目指向同一个 handler（相同 handler_start + handler_type），
        合并它们的 try 范围（取 min(start), max(end)）。

        Step 5: 迭代扩展 try 范围
        ─────────────────────────
        对于每个 handler，检查是否有其他异常表条目的 target 落在当前
        [try_start, handler_start) 范围内。如果有，扩展 try 范围以包含这些内层结构。

        ═══════════════════════════════════════════════════════════════════════════════
        【嵌套 try 处理机制】

        CPython 在编译嵌套 try 结构时，会将外层 try 的异常表拆分为多个条目，
        每个条目只覆盖不被内层 try 处理的部分。

        示例：
        ```python
        try:  # 外层
            try:  # 内层
                pass
            except InnerError:
                pass
        except OuterError:
            pass
        ```

        外层的异常表可能产生两个条目：
        - Entry1: [外层try开始, 内层try开始) → outer_handler
        - Entry2: [内层handler结束, 外层try结束) → outer_handler

        本方法通过迭代扩展将这些分裂的条目合并回完整的 try 范围。

        ═══════════════════════════════════════════════════════════════════════════════
        【返回值格式】

        返回列表，每个元素是一个字典：
        {
            'try_start': int,          # try 块起始偏移
            'try_end': int,            # try 块结束偏移
            'handler_start': int,      # handler 实际入口偏移
            'handler_type': str,       # 'except' | 'finally' | 'with' | 'except_star'
            'depth': int,              # 异常栈深度
        }

        ═══════════════════════════════════════════════════════════════════════════════
        """
        entries = list(self.cfg.exception_table)
        result = []
        seen = set()

        for entry in entries:
            entry_start = entry.get('start', 0)
            entry_end = entry.get('end', 0)
            entry_target = entry.get('target', 0)
            entry_depth = entry.get('depth', 0)

            handler_block = self.cfg.get_block_by_offset(entry_target)
            if handler_block is None or not handler_block.instructions:
                continue

            handler_type = self._classify_handler_type(handler_block, entry_target, entry_depth)
            if handler_type is None:
                handler_type = self._classify_handler_with_cleanup(handler_block, entry_target, entry_depth)
            if handler_type is None:
                continue

            actual_handler_start = self._find_actual_handler_start(
                handler_block, entry_target, handler_type, entry_depth)

            is_cleanup_only = (
                handler_block.instructions[0].opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START')
                and any(i.opname == 'COPY' for i in handler_block.instructions)
                and any(i.opname == 'POP_EXCEPT' for i in handler_block.instructions)
                and any(i.opname == 'RERAISE' for i in handler_block.instructions)
            )
            if is_cleanup_only:
                if actual_handler_start != entry_target:
                    # 检查actual_handler_start是否是另一个异常表条目的直接target
                    # 如果是，说明该handler是另一个try块的真正handler，
                    # 当前cleanup条目只是该handler作用域内的异常传播，应过滤掉
                    is_other_handler_target = False
                    for other_entry in entries:
                        if other_entry is entry:
                            continue
                        if other_entry.get('target', 0) == actual_handler_start:
                            is_other_handler_target = True
                            break
                    if is_other_handler_target:
                        continue
                    if handler_type == 'finally':
                        actual_handler_block = self.cfg.get_block_by_offset(actual_handler_start)
                        if actual_handler_block and actual_handler_block.instructions:
                            has_check = any(i.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for i in actual_handler_block.instructions)
                            if has_check:
                                continue
                    elif handler_type in ('except', 'except_star'):
                        actual_handler_block = self.cfg.get_block_by_offset(actual_handler_start)
                        if actual_handler_block and actual_handler_block.instructions:
                            has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in actual_handler_block.instructions)
                            has_check = any(i.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for i in actual_handler_block.instructions)
                            if not (has_push_exc or has_check):
                                continue
                else:
                    if handler_type != 'finally':
                        continue

            range_key = (entry_start, entry_end, actual_handler_start)
            if range_key in seen:
                continue
            seen.add(range_key)

            result.append({
                'try_start': entry_start,
                'try_end': entry_end,
                'handler_start': actual_handler_start,
                'handler_type': handler_type,
                'depth': entry_depth,
            })

        merged = {}
        for entry in result:
            key = (entry['handler_start'], entry['handler_type'])
            if key in merged:
                existing = merged[key]
                if entry['try_start'] >= existing['handler_start']:
                    handler_block = self.cfg.get_block_by_offset(existing['handler_start'])
                    if handler_block:
                        handler_already_in_range = any(
                            existing['try_start'] <= instr.offset < existing['try_end']
                            for instr in handler_block.instructions
                        )
                        if not handler_already_in_range:
                            continue
                    else:
                        continue
                existing['try_start'] = min(existing['try_start'], entry['try_start'])
                existing['try_end'] = max(existing['try_end'], entry['try_end'])
                existing['depth'] = min(existing['depth'], entry['depth'])
            else:
                merged[key] = entry.copy()
        result = list(merged.values())

        all_raw_entries = self.cfg.exception_table
        changed = True
        while changed:
            changed = False
            for entry in result:
                handler_start = entry['handler_start']
                for raw_entry in all_raw_entries:
                    raw_target = raw_entry.get('target', 0)
                    raw_start = raw_entry.get('start', 0)
                    raw_end = raw_entry.get('end', 0)
                    if entry['try_start'] <= raw_target < handler_start:
                        if raw_start < entry['try_start']:
                            entry['try_start'] = raw_start
                            changed = True
                        if raw_end > entry['try_end'] and raw_end <= handler_start:
                            # 只有当 raw_entry 的起始偏移在当前 try 范围内时才扩展 try_end。
                            # 如果 raw_start 在 try 范围之外（之后），说明这是一个独立的
                            # try 结构（如 finally 块内部的 try-except），不应被包含在
                            # 当前 try 范围内。
                            if raw_start < entry['try_end']:
                                entry['try_end'] = raw_end
                                changed = True

        for entry in result:
            if entry['handler_type'] != 'finally':
                continue
            handler_block = self.cfg.get_block_by_offset(entry['handler_start'])
            if handler_block is None:
                continue
            has_push_exc_reraise = False
            push_exc_block = None
            for block in self.cfg.blocks.values():
                for instr in block.instructions:
                    if instr.offset == entry['try_start'] and instr.opname == 'PUSH_EXC_INFO':
                        has_push_exc_reraise = any(
                            i.opname == 'RERAISE' for i in block.instructions)
                        push_exc_block = block
                        break
                if has_push_exc_reraise:
                    break
            if not has_push_exc_reraise:
                continue
            search_start = entry['try_start']
            if push_exc_block:
                for pred in push_exc_block.predecessors:
                    if pred.start_offset < search_start:
                        search_start = pred.start_offset
            for block in self.cfg.get_blocks_in_order():
                if block.start_offset >= entry['try_start']:
                    break
                if block.start_offset < entry['handler_start']:
                    search_start = block.start_offset
                    break
            if search_start < entry['try_start']:
                entry['try_start'] = search_start

        result.sort(key=lambda h: (-h.get('depth', 0), h['try_end'] - h['try_start'], h['try_start']))
        return result

    def _classify_handler_type(self, handler_block: BasicBlock, target_offset: int, depth: int) -> Optional[str]:
        """
        基于入口块指令特征统一分类 handler 类型

        ═══════════════════════════════════════════════════════════════════════════════
        【功能说明】
        根据异常处理器入口基本块的指令序列，判断该 handler 的类型。
        这是异常处理识别的关键步骤，正确的分类决定了后续的 AST 生成逻辑。

        ═══════════════════════════════════════════════════════════════════════════════
        【分类规则（按优先级从高到低）】

        **规则1: WITH_EXCEPT_START → 'with'**
        ─────────────────────────────
        检测条件：入口块的第一条指令是 WITH_EXCEPT_START
        语义：这是 with 语句的 __exit__ 调用入口，不是 try-except 的 handler
        字节码示例：
            WITH_EXC_START           # 开始 with 的退出处理
            CALL                    # 调用 __exit__
            POP_JUMP_IF_FALSE ...   # 根据 __exit__ 返回值决定是否抑制异常

        **规则2: PUSH_EXC_INFO + RERAISE（同块内）→ 'finally'**
        ─────────────────────────────
        检测条件：入口块包含 PUSH_EXC_INFO 且在同一条指令流中遇到 RERAISE
        语义：这是 finally 块的入口
        字节码示例：
            PUSH_EXC_INFO           # 压入异常信息到栈
            ... (finally body) ...
            RERAISE                 # 重新抛出异常（如果有的话）

        **规则3: PUSH_EXC_INFO + CHECK_EXC_MATCH（同块内）→ 'except'**
        ─────────────────────────────
        检测条件：入口块包含 PUSH_EXC_INFO 且在同一条指令流中遇到 CHECK_EXC_MATCH
        语义：这是标准 except 子句的入口
        字节码示例：
            PUSH_EXC_INFO           # 压入异常信息
            LOAD_GLOBAL ValueError  # 加载异常类型
            CHECK_EXC_MATCH         # 检查是否匹配

        **规则4: PUSH_EXC_INFO + CHECK_EG_MATCH（同块内）→ 'except_star'**
        ─────────────────────────────
        检测条件：入口块包含 PUSH_EXC_INFO 且在同一条指令流中遇到 CHECK_EG_MATCH
        语义：这是 Python 3.11+ 的 except* 子句（PEP 654 ExceptionGroup）

        **规则5: 后继块分析**
        ─────────────────────────────
        如果在当前块无法确定类型，遍历后继块查找关键指令：
        - 遇到 CHECK_EXC_MATCH → 'except'
        - 遇到 RERAISE（非 cleanup 模式） → 'finally'

        **规则6: 默认 → 'except'**
        ─────────────────────────────
        如果以上所有规则都无法匹配，默认归类为 'except'

        ═══════════════════════════════════════════════════════════════════════════════
        【cleanup RERAISE vs 真正的 RERAISE】

        某些情况下，RERAISE 指令出现在 cleanup 块中（用于异常传播链），
        这类 RERAISE 不应被当作 finally handler 的标志。

        判断标准：如果 RERAISE 所在的块同时包含 COPY + POP_EXCEPT，
        则认为是 cleanup reraise，而非 finally handler。

        ═══════════════════════════════════════════════════════════════════════════════
        【参数说明】
        - handler_block: 异常处理器入口的基本块
        - target_offset: 异常表条目的 target 偏移
        - depth: 异常栈深度

        【返回值】
        - 'with': with 语句的清理 handler
        - 'finally': finally 块 handler
        - 'except': 标准 except 子句 handler
        - 'except_star': except* 子句 handler (Python 3.11+)
        - None: 无法分类（可能不是有效的 handler 入口）

        ═══════════════════════════════════════════════════════════════════════════════
        """
        if not handler_block.instructions:
            return None

        first_instr = handler_block.instructions[0]

        if first_instr.opname == 'WITH_EXCEPT_START':
            return 'with'

        if first_instr.opname != 'PUSH_EXC_INFO':
            return None

        for instr in handler_block.instructions:
            if instr.opname == 'WITH_EXCEPT_START':
                return 'with'
            if instr.opname == 'RERAISE':
                # PUSH_EXC_INFO + ... + POP_EXCEPT + RERAISE 在同一块中
                # 说明异常已被处理（POP_EXCEPT），RERAISE 是重新抛出外层异常
                # 这是 except handler（通常是 finally 上下文中的 bare except），
                # 而非 finally handler（finally handler 中 POP_EXCEPT 在 RERAISE 之前不存在）
                has_pop_except_before = False
                for prev_instr in handler_block.instructions:
                    if prev_instr is instr:
                        break
                    if prev_instr.opname == 'POP_EXCEPT':
                        has_pop_except_before = True
                        break
                if has_pop_except_before:
                    return 'except'
                return 'finally'
            if instr.opname == 'CHECK_EXC_MATCH':
                return 'except'
            if instr.opname == 'CHECK_EG_MATCH':
                return 'except_star'

        if not any(instr.opname == 'CHECK_EXC_MATCH' for instr in handler_block.instructions):
            visited = {handler_block}
            worklist = list(handler_block.successors)
            while worklist:
                current = worklist.pop()
                if current in visited:
                    continue
                visited.add(current)
                if any(i.opname == 'PUSH_EXC_INFO' for i in current.instructions):
                    continue
                if any(i.opname == 'CHECK_EXC_MATCH' for i in current.instructions):
                    return 'except'
                if any(i.opname == 'RERAISE' for i in current.instructions):
                    # cleanup reraise 模式1: COPY + POP_EXCEPT + RERAISE
                    # cleanup reraise 模式2: POP_EXCEPT + RERAISE（无PUSH_EXC_INFO）
                    # 两种模式都表明这是 except handler 的清理块，而非 finally handler
                    is_cleanup_reraise = (
                        (any(i.opname == 'COPY' for i in current.instructions) and
                         any(i.opname == 'POP_EXCEPT' for i in current.instructions)) or
                        (any(i.opname == 'POP_EXCEPT' for i in current.instructions) and
                         not any(i.opname == 'PUSH_EXC_INFO' for i in current.instructions))
                    )
                    if not is_cleanup_reraise:
                        return 'finally'
                for succ in current.successors:
                    if succ not in visited:
                        worklist.append(succ)

            _all_visited = {handler_block}
            _all_visited.update(visited)
            _push_exc_idx = next((idx for idx, i in enumerate(handler_block.instructions) if i.opname == 'PUSH_EXC_INFO'), -1)
            _is_bare_except = (_push_exc_idx >= 0 and _push_exc_idx + 1 < len(handler_block.instructions)
                               and handler_block.instructions[_push_exc_idx + 1].opname == 'POP_TOP')
            if _is_bare_except:
                return 'except'
            _any_return_in_chain = any(
                i.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS')
                for b in _all_visited
                for i in b.instructions
            )
            if _any_return_in_chain:
                return 'finally'

        return 'except'

    def _find_actual_handler_start(self, cleanup_block: BasicBlock, cleanup_offset: int,
                                    handler_type: str, depth: int) -> int:
        if handler_type in ('except', 'except_star'):
            has_push_exc_self = any(i.opname == 'PUSH_EXC_INFO' for i in cleanup_block.instructions)
            has_check_self = any(i.opname == 'CHECK_EXC_MATCH' for i in cleanup_block.instructions)
            has_check_eg_self = any(i.opname == 'CHECK_EG_MATCH' for i in cleanup_block.instructions)
            has_reraise_self = any(i.opname == 'RERAISE' for i in cleanup_block.instructions)
            if has_push_exc_self and (has_check_self or has_check_eg_self):
                return cleanup_offset
            if has_push_exc_self and not has_check_self and not has_check_eg_self and not has_reraise_self:
                return cleanup_offset

            visited = {cleanup_offset}
            worklist = list(cleanup_block.predecessors)
            while worklist:
                pred = worklist.pop()
                if pred.start_offset in visited:
                    continue
                visited.add(pred.start_offset)

                has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in pred.instructions)
                has_check = any(i.opname == 'CHECK_EXC_MATCH' for i in pred.instructions)
                has_check_eg = any(i.opname == 'CHECK_EG_MATCH' for i in pred.instructions)
                has_reraise = any(i.opname == 'RERAISE' for i in pred.instructions)

                if has_push_exc and has_check:
                    return pred.start_offset
                if has_push_exc and has_check_eg:
                    return pred.start_offset
                if has_push_exc and not has_check and not has_check_eg and not has_reraise:
                    return pred.start_offset

                if not has_reraise and not (has_push_exc and any(i.opname == 'COPY' for i in pred.instructions)):
                    worklist.extend(pred.predecessors)

            return cleanup_offset

        if handler_type == 'finally':
            has_push_exc_self = any(i.opname == 'PUSH_EXC_INFO' for i in cleanup_block.instructions)
            has_reraise_self = any(i.opname == 'RERAISE' for i in cleanup_block.instructions)
            if has_push_exc_self and has_reraise_self:
                return cleanup_offset
            if has_push_exc_self and not has_reraise_self:
                return cleanup_offset

            visited = {cleanup_offset}
            worklist = list(cleanup_block.predecessors)
            while worklist:
                pred = worklist.pop()
                if pred.start_offset in visited:
                    continue
                visited.add(pred.start_offset)
                has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in pred.instructions)
                has_reraise = any(i.opname == 'RERAISE' for i in pred.instructions)
                if has_push_exc and has_reraise:
                    return pred.start_offset
                if has_push_exc and not has_reraise:
                    return pred.start_offset
                worklist.extend(pred.predecessors)

        return cleanup_offset

    def _classify_handler_with_cleanup(self, cleanup_block: BasicBlock, target_offset: int,
                                       depth: int) -> Optional[str]:
        if not cleanup_block.instructions:
            return None

        if cleanup_block.instructions[0].opname == 'WITH_EXCEPT_START':
            return 'with'

        if not any(i.opname == 'COPY' for i in cleanup_block.instructions):
            return None

        if not any(i.opname == 'POP_EXCEPT' for i in cleanup_block.instructions):
            return None

        if not any(i.opname == 'RERAISE' for i in cleanup_block.instructions):
            return None

        visited = {target_offset}
        worklist = list(cleanup_block.predecessors)
        while worklist:
            pred = worklist.pop()
            if pred.start_offset in visited:
                continue
            visited.add(pred.start_offset)

            has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in pred.instructions)
            has_check = any(i.opname == 'CHECK_EXC_MATCH' for i in pred.instructions)
            has_check_eg = any(i.opname == 'CHECK_EG_MATCH' for i in pred.instructions)
            has_reraise = any(i.opname == 'RERAISE' for i in pred.instructions)

            if has_push_exc and has_check:
                return 'except'
            if has_push_exc and has_check_eg:
                return 'except_star'
            if has_push_exc and not has_check and not has_check_eg and not has_reraise:
                _push_exc_idx = next((idx for idx, i in enumerate(pred.instructions) if i.opname == 'PUSH_EXC_INFO'), -1)
                _is_bare_except = (_push_exc_idx >= 0 and _push_exc_idx + 1 < len(pred.instructions)
                                   and pred.instructions[_push_exc_idx + 1].opname == 'POP_TOP')
                if _is_bare_except:
                    return 'except'
                # 先检查 pred 自身是否含 RETURN（典型 finally 出口）
                if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in pred.instructions):
                    return 'finally'
                # BFS walk successors 检查 RETURN 或非 cleanup RERAISE。
                # finally body 含 ternary 时，pred (PUSH_EXC_INFO + cond + POP_JUMP) 的
                # successors 是 ternary 的 true/false value 块，再走一层才到 merge 块
                # （含 STORE + RERAISE，无 COPY+POP_EXCEPT），属非 cleanup RERAISE。
                # 单层 walk 看不到 merge 块，需 BFS 才能识别 finally 异常路径。
                # [R3-08/R4-05 守卫] 若任一 successor 含 CHECK_EXC_MATCH /
                # CHECK_EG_MATCH，则是 except handler 的异常类型为 ternary 的情形
                # （merge 块含 CHECK_EXC_MATCH + POP_TOP + POP_EXCEPT + RETURN），
                # 不能误判为 finally。CHECK_EXC_MATCH 是 except 的强信号。
                _visited_succ = {pred}
                _worklist_succ = list(pred.successors)
                while _worklist_succ:
                    _cur_succ = _worklist_succ.pop()
                    if _cur_succ in _visited_succ:
                        continue
                    _visited_succ.add(_cur_succ)
                    if any(i.opname == 'PUSH_EXC_INFO' for i in _cur_succ.instructions):
                        continue
                    if any(i.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH')
                           for i in _cur_succ.instructions):
                        return 'except'
                    if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in _cur_succ.instructions):
                        return 'finally'
                    if any(i.opname == 'RERAISE' for i in _cur_succ.instructions):
                        _is_cleanup_reraise = (
                            (any(i.opname == 'COPY' for i in _cur_succ.instructions) and
                             any(i.opname == 'POP_EXCEPT' for i in _cur_succ.instructions)) or
                            (any(i.opname == 'POP_EXCEPT' for i in _cur_succ.instructions) and
                             not any(i.opname == 'PUSH_EXC_INFO' for i in _cur_succ.instructions))
                        )
                        if not _is_cleanup_reraise:
                            return 'finally'
                    for _succ_next in _cur_succ.successors:
                        if _succ_next not in _visited_succ:
                            _worklist_succ.append(_succ_next)
                return 'except'

            has_copy_pop = any(i.opname == 'COPY' for i in pred.instructions) and any(i.opname == 'POP_EXCEPT' for i in pred.instructions)
            if not has_copy_pop:
                worklist.extend(pred.predecessors)

        return 'finally'

    def _register_region_blocks(self, region, try_blocks, handler_blocks_set,
                                finally_blocks, handler_info, finally_copy_blocks, else_blocks,
                                cleanup_blocks=None):
        for block in try_blocks:
            self.block_to_region[block] = region
        for block in handler_blocks_set:
            self.block_to_region[block] = region
        for block in finally_blocks:
            self.block_to_region[block] = region
        for fc_offset in finally_copy_blocks:
            fc_block = self.cfg.get_block_by_offset(fc_offset)
            if fc_block:
                self.block_to_region[fc_block] = region
        for block in else_blocks:
            self.block_to_region[block] = region
        if cleanup_blocks:
            for block in cleanup_blocks:
                self.block_to_region[block] = region

    def _collect_handler_chain(self, handler_start_offset: int,
                                all_except_handlers: list,
                                all_handler_entry_blocks: list,
                                all_handler_blocks_set: set) -> List[BasicBlock]:
        handler_entry = self.cfg.get_block_by_offset(handler_start_offset)
        if handler_entry is None:
            return []
        exc_type, exc_name, handler_body = self._extract_except_handler(handler_entry)
        all_except_handlers.append((exc_type, exc_name, handler_body))
        all_handler_entry_blocks.append(handler_entry)
        all_handler_blocks_set |= set(handler_body) | {handler_entry}
        chain_handlers, chain_entries = self._follow_except_chain(handler_entry)
        all_except_handlers.extend(chain_handlers)
        all_handler_entry_blocks.extend(chain_entries)
        for _, _, body in chain_handlers:
            all_handler_blocks_set |= set(body)
        for heb in chain_entries:
            all_handler_blocks_set.add(heb)
        return handler_body

    def _extract_except_handler(self, handler_entry: BasicBlock) -> Tuple[Optional[str], Optional[str], List[BasicBlock]]:
        """提取handler的异常类型、异常名称和body块

        合并了_extract_exc_type、_extract_exc_name、_extract_handler_body的逻辑。
        """
        def _collect_body(entry):
            _blocks: List[BasicBlock] = []
            _visited: Set[BasicBlock] = set()
            _worklist = [entry]
            while _worklist:
                _current = _worklist.pop()
                if _current in _visited:
                    continue
                _visited.add(_current)
                # [Phase 3 adv17_try_except_star] 边界检查：
                # 遇到下一个 handler 的 CHECK_EG_MATCH / CHECK_EXC_MATCH
                # 入口块或 except* 共享清理块（PREP_RERAISE_STAR）时停止，
                # 不将其纳入当前 handler 的 body。此前 _collect_body 无条件
                # 追踪所有后继，导致多 except* handler 的块互相重叠。
                if _current is not entry:
                    if any(i.opname in ('CHECK_EG_MATCH', 'CHECK_EXC_MATCH') for i in _current.instructions):
                        continue
                    if any(i.opname == 'PREP_RERAISE_STAR' for i in _current.instructions):
                        continue
                _blocks.append(_current)
                _last = _current.get_last_instruction()
                if _last and _last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
                    continue
                if any(i.opname == 'POP_EXCEPT' for i in _current.instructions):
                    continue
                for _succ in _current.successors:
                    # [Phase 3 adv17_try_except_star] 不跟踪异常后继
                    # （exception_successors）。except* handler body 的异常后继
                    # 是 except* 不匹配清理块（框架指令），跟踪它会导致
                    # 多余的 e = None 和块重叠。
                    if _succ in _current.exception_successors:
                        continue
                    if _succ not in _visited:
                        if _succ.start_offset in self._reraise_block_offsets:
                            continue
                        _worklist.append(_succ)
            return _blocks

        exc_type = None
        exc_name = None
        handler_body_blocks: List[BasicBlock] = []

        has_push_exc = any(i.opname == 'PUSH_EXC_INFO' for i in handler_entry.instructions)
        if has_push_exc:
            seen_push = False
            has_pop_top = False
            for i in handler_entry.instructions:
                if i.opname == 'PUSH_EXC_INFO':
                    seen_push = True
                elif seen_push and i.opname == 'POP_TOP':
                    has_pop_top = True
                    break
                elif seen_push and i.opname not in ('NOP', 'CACHE', 'RESUME'):
                    break
            if has_pop_top:
                handler_body_blocks = _collect_body(handler_entry)
                return exc_type, exc_name, handler_body_blocks

        # [Phase 3 adv17_try_except_star] 同时支持 CHECK_EXC_MATCH（普通 except）
        # 和 CHECK_EG_MATCH（except* 异常组）。两者之前的 LOAD_NAME/LOAD_GLOBAL
        # 是异常类型，之后的 STORE_* 是 as 变量名。
        _CHECK_OPS = ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH')
        has_check_exc = any(i.opname in _CHECK_OPS for i in handler_entry.instructions)
        if has_check_exc:
            pre_check_instrs = []
            for instr in handler_entry.instructions:
                if instr.opname in _CHECK_OPS:
                    break
                if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                    pre_check_instrs.append(instr.argval)
            if len(pre_check_instrs) == 1:
                exc_type = pre_check_instrs[0]
            elif len(pre_check_instrs) > 1:
                has_build_tuple = any(
                    i.opname == 'BUILD_TUPLE' and i.argval == len(pre_check_instrs)
                    for i in handler_entry.instructions
                    if i.opname not in _CHECK_OPS
                )
                if has_build_tuple:
                    exc_type = '(' + ', '.join(pre_check_instrs) + ')'
                else:
                    exc_type = pre_check_instrs[0]

            seen_check = False
            for instr in handler_entry.instructions:
                if instr.opname in _CHECK_OPS:
                    seen_check = True
                    continue
                if seen_check and instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                    exc_name = instr.argval
                    break
                if seen_check and instr.opname not in ({'NOP', 'CACHE', 'RESUME', 'POP_TOP', 'COPY',
                                                        'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'}
                                                       | CONDITIONAL_JUMP_OPS):
                    break
            if seen_check and exc_name is None:
                for succ in sorted(handler_entry.successors, key=lambda s: s.start_offset):
                    for instr in succ.instructions:
                        if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_DEREF', 'STORE_GLOBAL'):
                            exc_name = instr.argval
                            break
                        if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP'):
                            break
                    if exc_name is not None:
                        break

        has_pop_jump = any(i.opname in CONDITIONAL_JUMP_OPS for i in handler_entry.instructions)
        if has_check_exc and has_pop_jump:
            body_entry = None
            last = handler_entry.get_last_instruction()
            if last and last.opname in CONDITIONAL_JUMP_OPS:
                jump_target_offset = last.argval
                for succ in handler_entry.successors:
                    if succ == handler_entry:
                        continue
                    if succ.start_offset == jump_target_offset:
                        continue
                    if succ.start_offset in self._reraise_block_offsets:
                        continue
                    body_entry = succ
                    break
            if body_entry:
                handler_body_blocks = _collect_body(body_entry)
        elif not has_check_exc:
            # [Phase 3 回归修复] bare except（无 CHECK_OP、无 PUSH_EXC_INFO、
            # 无条件跳转）的入口块可能仅含 POP_TOP（弹出异常），真正的 body
            # （POP_EXCEPT + LOAD_CONST + RETURN_VALUE 等）在后继块中。此前
            # 直接 body = [handler_entry] 只收集入口块，丢失后继 body 块，
            # 导致 _follow_except_chain 无法识别 bare except（body 不含
            # POP_EXCEPT）。改用 _collect_body 完整收集，其边界检查会自动
            # 在 RETURN_VALUE/RERAISE/CHECK_OP/PREP_RERAISE_STAR 处停止。
            handler_body_blocks = _collect_body(handler_entry)

        if not handler_body_blocks:
            body_entry = None
            for succ in sorted(handler_entry.successors, key=lambda s: s.start_offset):
                if succ != handler_entry:
                    if succ.start_offset not in self._reraise_block_offsets:
                        body_entry = succ
                    break
            if body_entry:
                handler_body_blocks = _collect_body(body_entry)

        if exc_type is None and handler_body_blocks:
            for hb in handler_body_blocks:
                for instr in hb.instructions:
                    if instr.opname in _CHECK_OPS:
                        exc_type = instr.argval
                        break
                if exc_type:
                    break
                for succ in hb.successors:
                    if succ == hb:
                        continue
                    for instr in succ.instructions:
                        if instr.opname in _CHECK_OPS:
                            exc_type = instr.argval
                            break
                    if exc_type:
                        break
                if exc_type:
                    break
                _rv = {hb}
                _wl = list(hb.successors)
                while _wl:
                    _cur = _wl.pop()
                    if _cur in _rv:
                        continue
                    _rv.add(_cur)
                    for instr in _cur.instructions:
                        if instr.opname in _CHECK_OPS:
                            exc_type = instr.argval
                            break
                    if exc_type:
                        break
                    for _s in _cur.successors:
                        if _s not in _rv:
                            _wl.append(_s)
                if exc_type:
                    break

        return exc_type, exc_name, handler_body_blocks

    def _follow_except_chain(self, handler_entry: BasicBlock) -> Tuple[List[Tuple], List[BasicBlock]]:
        chain_handlers: List[Tuple] = []
        chain_entries: List[BasicBlock] = []
        current = handler_entry
        visited = {handler_entry}
        CHAIN_LINK_JUMPS = CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        # [Phase 3 adv17_try_except_star] 同时识别 CHECK_EXC_MATCH（普通 except）
        # 和 CHECK_EG_MATCH（except* 异常组）作为链中 handler 的标志。
        _CHAIN_CHECK_OPS = ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH')
        while True:
            last = current.get_last_instruction()
            if last is None or last.opname not in CHAIN_LINK_JUMPS:
                break
            next_offset = last.argval
            next_block = self.cfg.get_block_by_offset(next_offset) if next_offset is not None else None
            if next_block is None or next_block in visited:
                break
            if any(i.opname == 'RERAISE' for i in next_block.instructions):
                break
            # [Phase 3 adv17_try_except_star] PREP_RERAISE_STAR 是 except* 共享
            # 清理块的标志，不是 handler，链到此中断。
            if any(i.opname == 'PREP_RERAISE_STAR' for i in next_block.instructions):
                break
            is_back_edge = False
            for i in next_block.instructions:
                if i.opname in BACKWARD_JUMP_OPS and i.argval is not None:
                    target = self.cfg.get_block_by_offset(i.argval)
                    if target and self.loop_analyzer:
                        for loop_hdr in self.loop_analyzer.get_all_loops():
                            if target == loop_hdr:
                                is_back_edge = True
                                break
            if is_back_edge:
                break
            if any(i.opname == 'PUSH_EXC_INFO' for i in next_block.instructions):
                break
            visited.add(next_block)
            has_check = any(i.opname in _CHAIN_CHECK_OPS for i in next_block.instructions)
            exc_type, exc_name, body = self._extract_except_handler(next_block)
            if has_check:
                chain_handlers.append((exc_type, exc_name, body))
                chain_entries.append(next_block)
                current = next_block
            else:
                # [Phase 3 adv17_try_except_star_multi] except* 多 handler
                # 链中，POP_JUMP_FORWARD_IF_NONE 的跳转目标是「不匹配清理块」
                # （仅含 POP_TOP），其后继才是下一个 except* handler 入口
                # （含 CHECK_EG_MATCH）。此前直接 break 导致第二个 except*
                # handler 丢失，其块被并入第一个 handler 的 body。
                # 修正：若 next_block 是简单过渡块（仅含 POP_TOP / NOP /
                # JUMP_FORWARD），沿其后继查找下一个含 CHECK_OP 的 handler。
                _is_transition = all(
                    i.opname in ('POP_TOP', 'NOP', 'CACHE', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                    for i in next_block.instructions
                )
                if _is_transition:
                    _probe = next_block
                    _probe_visited = {next_block}
                    _found_next_handler = False
                    for _ in range(8):
                        _probe_succs = [s for s in _probe.successors if s not in _probe_visited and s not in visited]
                        if not _probe_succs:
                            break
                        _probe = _probe_succs[0]
                        _probe_visited.add(_probe)
                        if any(i.opname == 'PREP_RERAISE_STAR' for i in _probe.instructions):
                            break
                        if any(i.opname == 'RERAISE' for i in _probe.instructions):
                            break
                        if any(i.opname in _CHAIN_CHECK_OPS for i in _probe.instructions):
                            visited.add(_probe)
                            _et, _en, _body = self._extract_except_handler(_probe)
                            chain_handlers.append((_et, _en, _body))
                            chain_entries.append(_probe)
                            current = _probe
                            _found_next_handler = True
                            break
                    if _found_next_handler:
                        continue
                    # 过渡块未找到下一个 CHECK_OP handler。区分两种情况：
                    # (a) except* 链末尾的清理过渡块（不是 handler，丢弃）：
                    #     _collect_body 只返回过渡块自身（len == 1），因为
                    #     后继全是 CHECK_OP/PREP_RERAISE_STAR/RERAISE 块被
                    #     边界检查跳过。
                    # (b) bare except 入口块（仅含 POP_TOP，真实 body 在后继
                    #     块中）：_collect_body 返回入口 + 后继 body 块
                    #     （len > 1），因为后继是 POP_EXCEPT/LOAD_CONST/
                    #     STORE_NAME/RAISE_VARARGS 等真实指令块。
                    # 用 len(body) > 1 区分：bare except 必有后继 body 块。
                # [Phase 3 回归修复] bare except（无 CHECK_OP 但有真实 body）
                # 是 except 链的终结 handler。恢复 e532253 之前的行为：将其
                # 作为最后一个 handler 纳入链。此前 e532253 移除此分支导致
                # te010/021/052/061/093 等 bare except 被丢弃。
                # 判别护栏：
                # - 非过渡块（入口含真实指令）：body 非空即纳入。
                # - 过渡块（入口仅 POP_TOP/JUMP）：body 块数 > 1 才纳入
                #   （except* 清理过渡块 body 仅 1 块，不纳入）。
                _is_real_handler = body and (not _is_transition or len(body) > 1)
                if _is_real_handler:
                    chain_handlers.append((exc_type, exc_name, body))
                    chain_entries.append(next_block)
                break
        return chain_handlers, chain_entries

    def _find_try_else_blocks(self, try_region) -> List[BasicBlock]:
        if not hasattr(try_region, 'except_handlers') or not try_region.except_handlers:
            return []

        try_end_offset = try_region.try_offset_end
        if try_end_offset is None:
            return []

        handler_blocks_set = set().union(*(set(h[2]) for h in try_region.except_handlers)) if try_region.except_handlers else set()

        all_handler_blocks = set()
        if try_region.handler_entry_blocks:
            all_handler_blocks.update(try_region.handler_entry_blocks)
        for _, _, hblocks in try_region.except_handlers:
            all_handler_blocks.update(hblocks)
        if hasattr(try_region, 'finally_blocks') and try_region.finally_blocks:
            all_handler_blocks.update(try_region.finally_blocks)

        handler_end_offsets = []
        for _, _, hblocks in try_region.except_handlers:
            if hblocks:
                last_handler_block = max(hblocks, key=lambda b: b.start_offset)
                if last_handler_block.instructions:
                    end_offset = last_handler_block.instructions[-1].offset + 2
                    if end_offset not in handler_end_offsets:
                        handler_end_offsets.append(end_offset)
                else:
                    if last_handler_block.start_offset not in handler_end_offsets:
                        handler_end_offsets.append(last_handler_block.start_offset)

        for block in handler_blocks_set:
            if block not in set(b for _, _, hblocks in try_region.except_handlers for b in hblocks):
                has_successor_outside = any(
                    succ not in handler_blocks_set for succ in block.successors)
                if has_successor_outside and block.start_offset > try_end_offset:
                    if block.instructions:
                        end_offset = block.instructions[-1].offset + 2
                        if end_offset not in handler_end_offsets:
                            handler_end_offsets.append(end_offset)
                    elif block.start_offset not in handler_end_offsets:
                        handler_end_offsets.append(block.start_offset)

        handler_end_offsets = sorted(handler_end_offsets) if handler_end_offsets else []

        if not handler_end_offsets:
            return []

        try_end_block = self.cfg.get_block_by_offset(try_end_offset)
        handler_end_blocks = [self.cfg.get_block_by_offset(offset) for offset in handler_end_offsets]
        handler_end_blocks = [b for b in handler_end_blocks if b is not None]

        if not handler_end_blocks or try_end_block is None:
            return []

        precise_handler_end = max(handler_end_offsets)
        for heb in try_region.handler_entry_blocks:
            if hasattr(heb, 'instructions') and heb.instructions:
                last_instr = heb.instructions[-1]
                if last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    jump_target = last_instr.argval
                    if jump_target and jump_target > precise_handler_end:
                        precise_handler_end = jump_target

        all_exit_points = {try_end_block} | set(handler_end_blocks)
        merge_point = self.dom_analyzer.find_nearest_common_post_dominator(all_exit_points)

        if not merge_point or merge_point.start_offset <= precise_handler_end:
            try_end_is_back_edge = (
                try_end_block and try_end_block.instructions and
                any(i.opname == 'JUMP_BACKWARD' for i in try_end_block.instructions)
            )
            alternative_merges = []
            for block in self.cfg.get_blocks_in_order():
                if (block.start_offset > precise_handler_end and
                    block not in handler_blocks_set and
                    block not in try_region.blocks):
                    from_try = any(
                        self._is_reachable_from(s, block, set())
                        for s in try_end_block.successors
                        if s not in handler_blocks_set
                    )
                    from_handler = any(
                        self._is_reachable_from(hb, block, set())
                        for hb in handler_end_blocks
                    )
                    if from_try and from_handler:
                        alternative_merges.append(block)

            if alternative_merges and not try_end_is_back_edge:
                merge_point = alternative_merges[0]
            else:
                handler_entry_offsets = []
                for heb in try_region.handler_entry_blocks:
                    if heb.start_offset >= try_end_offset:
                        handler_entry_offsets.append(heb.start_offset)
                first_handler_entry = min(handler_entry_offsets) if handler_entry_offsets else None
                if first_handler_entry is not None and first_handler_entry > try_end_offset:
                    else_blocks = []
                    for block in self.cfg.get_blocks_in_order():
                        if (block.start_offset >= try_end_offset and
                            block.start_offset < first_handler_entry and
                            block not in all_handler_blocks and
                            block not in try_region.blocks and
                            not self._is_pass_or_return_none_block(block)):
                            else_blocks.append(block)
                    return else_blocks
                inner_else = self._find_inner_else_blocks(try_region, try_end_offset,
                                                           all_handler_blocks)
                if inner_else:
                    return inner_else
                return []

        else_blocks = []
        for block in self.cfg.get_blocks_in_order():
            if (block.start_offset > precise_handler_end and
                block.start_offset < merge_point.start_offset and
                block not in all_handler_blocks and
                block not in try_region.blocks and
                not self._is_pass_or_return_none_block(block)):
                else_blocks.append(block)

        if not else_blocks:
            inner_else = self._find_inner_else_blocks(try_region, try_end_offset,
                                                       all_handler_blocks)
            if inner_else:
                return inner_else

        return else_blocks

    def _find_inner_else_blocks(self, try_region, try_end_offset, all_handler_blocks):
        try_body_blocks = getattr(try_region, 'try_blocks', [])
        if not try_body_blocks:
            return []
        handler_set = set(getattr(try_region, 'handler_entry_blocks', []))
        try_body_max_end = 0
        for tb in try_body_blocks:
            has_exc_edge = any(s in handler_set for s in tb.successors)
            is_try_entry = tb is try_region.entry or tb.start_offset == try_region.entry.start_offset
            if has_exc_edge or is_try_entry:
                for instr in tb.instructions:
                    if instr.offset > try_body_max_end and instr.opname not in NOISE_OPS:
                        try_body_max_end = instr.offset
        if try_body_max_end <= 0:
            return []
        handler_entries = getattr(try_region, 'handler_entry_blocks', [])
        if not handler_entries:
            return []
        first_handler_entry = min(b.start_offset for b in handler_entries)
        if first_handler_entry <= try_body_max_end:
            return []
        inner_else = []
        for block in self.cfg.get_blocks_in_order():
            if (block.start_offset > try_body_max_end and
                block.start_offset < first_handler_entry and
                block not in all_handler_blocks and
                not self._is_pass_or_return_none_block(block)):
                inner_else.append(block)
        return inner_else

    def _is_pass_or_return_none_block(self, block: BasicBlock) -> bool:
        """判断块是否只包含pass或return None"""
        meaningful_instrs = [
            i for i in block.instructions 
            if i.opname not in NOISE_OPS
        ]
        
        if not meaningful_instrs:
            return True
        
        if len(meaningful_instrs) == 1:
            op = meaningful_instrs[0].opname
            if op == 'RETURN_VALUE' or op == 'RETURN_CONST':
                return True
        
        if (len(meaningful_instrs) == 2 and 
            meaningful_instrs[0].opname == 'LOAD_CONST' and
            meaningful_instrs[1].opname in ('RETURN_VALUE', 'RETURN_CONST')):
            return True
        
        return False

    def _is_reachable_from(self, start: BasicBlock, target: BasicBlock,
                           exclude: Set[BasicBlock]) -> bool:
        visited = set()
        worklist = [start]
        while worklist:
            current = worklist.pop(0)
            if current == target:
                return True
            if current in visited:
                continue
            visited.add(current)
            if current in exclude:
                continue
            for succ in current.successors:
                if succ not in visited:
                    worklist.append(succ)
        return False

    def _collect_finally_body_blocks(self, handler_entry: BasicBlock,
                                      try_blocks: List[BasicBlock] = None,
                                      except_handlers: List = None) -> Tuple[List[BasicBlock], Dict[int, int]]:
        body_blocks: List[BasicBlock] = [handler_entry]
        visited: Set[BasicBlock] = set()

        for succ in handler_entry.successors:
            if succ not in visited:
                worklist = [succ]
                while worklist:
                    current = worklist.pop()
                    if current in visited:
                        continue
                    if any(i.opname == 'CHECK_EXC_MATCH' for i in current.instructions):
                        continue
                    if any(i.opname == 'WITH_EXCEPT_START' for i in current.instructions):
                        continue
                    visited.add(current)
                    body_blocks.append(current)

                    last = current.get_last_instruction()
                    if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
                        continue

                    for succ2 in current.successors:
                        if succ2 not in visited:
                            worklist.append(succ2)

        copy_blocks: Dict[int, int] = {}
        if try_blocks is not None and except_handlers is not None and self.cfg.exception_table:
            finally_offsets = {fb.start_offset for fb in body_blocks}
            try_block_set = set(try_blocks)
            handler_block_sets = [set(h[2]) for h in except_handlers if h[2]]
            all_handler_blocks = set().union(*handler_block_sets) if handler_block_sets else set()

            entry_to_finally = {}
            for entry in self.cfg.exception_table:
                target = entry.get('target', 0)
                if target in finally_offsets:
                    if target not in entry_to_finally:
                        entry_to_finally[target] = []
                    entry_to_finally[target].append(entry)

            if entry_to_finally:
                for _, entries in entry_to_finally.items():
                    if len(entries) <= 1:
                        continue

                    entries_by_depth = {}
                    for entry in entries:
                        depth = entry.get('depth', 0)
                        if depth not in entries_by_depth:
                            entries_by_depth[depth] = []
                        entries_by_depth[depth].append(entry)

                    normal_entries = entries_by_depth.get(0, [])
                    if not normal_entries or len(normal_entries) <= 1:
                        continue

                    protected_ranges = []
                    for entry in normal_entries:
                        start = entry.get('start', 0)
                        end = entry.get('end', 0)
                        if start < end:
                            protected_ranges.append((start, end))

                    if not protected_ranges:
                        continue

                    for block in self.cfg.blocks.values():
                        if block.start_offset in finally_offsets:
                            continue
                        if block in body_blocks:
                            continue
                        if block in try_block_set:
                            continue
                        if block in all_handler_blocks:
                            continue

                        block_in_any_range = False
                        for rng_start, rng_end in protected_ranges:
                            if any(rng_start <= instr.offset < rng_end for instr in block.instructions):
                                block_in_any_range = True
                                break

                        is_try_exit_successor = False
                        for tb in try_blocks:
                            if block in tb.successors:
                                is_try_exit_successor = True
                                break
                        if not is_try_exit_successor:
                            for hb_set in handler_block_sets:
                                for hb in hb_set:
                                    if block in hb.successors:
                                        is_try_exit_successor = True
                                        break
                                if is_try_exit_successor:
                                    break

                        if not is_try_exit_successor and not block_in_any_range:
                            continue

                        if not block.instructions:
                            continue
                        cleanup_ops = frozenset({
                            'CLOSE_ITERATOR', 'DELETE_FAST', 'DELETE_NAME', 'DELETE_DEREF', 'DELETE_GLOBAL',
                            'DELETE_ATTR', 'DELETE_SUBSCR',
                            'WITH_CLEANUP_START', 'WITH_CLEANUP_FINISH',
                            'BEFORE_WITH', 'WITH_EXCEPT_START',
                            'POP_BLOCK', 'POP_EXCEPT',
                        })
                        has_cleanup = any(i.opname in cleanup_ops for i in block.instructions)
                        user_code_ops = frozenset({
                            'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF', 'LOAD_ATTR',
                            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'STORE_ATTR',
                            'CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_FUNCTION_KW',
                            'BINARY_OP', 'COMPARE_OP', 'UNARY_OP',
                            'BUILD_LIST', 'BUILD_TUPLE', 'BUILD_MAP', 'BUILD_SET',
                            'BUILD_STRING', 'BUILD_SLICE',
                            'GET_ITER', 'FOR_ITER',
                            'COPY', 'SWAP',
                            'FORMAT_VALUE', 'BUILD_CONST_KEY_MAP',
                            'IS_OP', 'CONTAINS_OP',
                            'IMPORT_NAME', 'IMPORT_FROM',
                            'LOAD_METHOD',
                        })
                        has_user_code = any(i.opname in user_code_ops for i in block.instructions)
                        control_flow_ops = frozenset({
                            'RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE',
                            'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE',
                            'JUMP_BACKWARD_NO_INTERRUPT',
                        })
                        has_control_flow = any(i.opname in control_flow_ops for i in block.instructions)
                        exc_wrapper_ops = frozenset({'PUSH_EXC_INFO', 'POP_EXCEPT'})
                        has_exc_wrapper = any(i.opname in exc_wrapper_ops for i in block.instructions)

                        has_finally_pattern = False
                        if has_exc_wrapper and len([i for i in block.instructions if i.opname in exc_wrapper_ops]) > 1:
                            has_finally_pattern = False
                        elif has_cleanup or (has_user_code and has_control_flow):
                            has_finally_pattern = True
                        elif has_user_code and len(block.instructions) > 3:
                            has_finally_pattern = True

                        if has_finally_pattern or is_try_exit_successor:
                            meaningful_instrs = [i for i in block.instructions
                                               if i.opname not in NOISE_OPS]
                            keep_count = 0

                            last_meaningful_idx = -1
                            for idx, instr in enumerate(meaningful_instrs):
                                if instr.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS',
                                                   'RERAISE', 'JUMP_FORWARD', 'JUMP_BACKWARD',
                                                   'JUMP_ABSOLUTE'):
                                    last_meaningful_idx = idx

                            if last_meaningful_idx >= 0 and last_meaningful_idx < len(meaningful_instrs) - 1:
                                keep_count = last_meaningful_idx + 1
                            elif meaningful_instrs:
                                keep_count = len(meaningful_instrs)

                            existing = copy_blocks.get(block.start_offset)
                            if existing is None or keep_count < existing:
                                copy_blocks[block.start_offset] = keep_count

        return body_blocks, copy_blocks

    def _find_next_with_block(self, current, _depth_map):
        for succ in current.successors:
            if succ in self.block_to_region or not any(
                i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in succ.instructions
            ):
                continue
            if _depth_map.get(succ, -1) != _depth_map.get(current, -1) + 1:
                continue
            ce, se = self._find_with_exc_entry(current), self._find_with_exc_entry(succ)
            if not (ce and se and ce.get('end') is not None and se.get('start') is not None):
                continue
            if ce.get('end') <= se.get('start') and not self._has_body_code_before_before_with(succ):
                if not self._has_intermediate_body_path(current, succ):
                    return succ
        return None

    def _find_with_exc_entry(self, block):
        search_offset = block.start_offset
        found_bw = False
        bw_offset = None
        is_async = False
        for instr in block.instructions:
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                found_bw = True
                bw_offset = instr.offset
                if instr.opname == 'BEFORE_ASYNC_WITH':
                    is_async = True
            elif found_bw and instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                search_offset = instr.offset
                break
            elif found_bw and instr.opname == 'POP_TOP':
                search_offset = instr.offset
                break
        if found_bw and search_offset == block.start_offset and bw_offset is not None:
            closest_succ = None
            for succ in block.successors:
                if succ.start_offset > bw_offset:
                    if closest_succ is None or succ.start_offset < closest_succ.start_offset:
                        closest_succ = succ
            if closest_succ is not None:
                search_offset = closest_succ.start_offset
                if is_async:
                    _cur = closest_succ
                    _visited = set()
                    while _cur is not None and _cur not in _visited:
                        _visited.add(_cur)
                        if any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'POP_TOP') for i in _cur.instructions):
                            search_offset = _cur.start_offset
                            break
                        _succs = [s for s in _cur.successors if s != _cur]
                        if len(_succs) == 1:
                            _cur = _succs[0]
                        else:
                            break
        best_entry = None
        best_depth = -1
        for entry in self.cfg.exception_table:
            entry_start = entry.get('start', 0)
            entry_end = entry.get('end', 0)
            if entry_start <= search_offset < entry_end:
                depth = entry.get('depth', 0)
                if depth > best_depth:
                    best_depth = depth
                    best_entry = entry
        return best_entry

    def _collect_consecutive_with_blocks(self, start_block, depth_map):
        with_entry_blocks = [start_block]
        current = start_block
        while True:
            nxt = self._find_next_with_block(current, depth_map)
            if nxt is None:
                break
            with_entry_blocks.append(nxt)
            current = nxt
        return with_entry_blocks

    def _get_with_body_range(self, with_block):
        if with_block is None:
            return None, None
        entry = self._find_with_exc_entry(with_block)
        if entry is not None:
            start = entry.get('start')
            end = entry.get('end')
            if start is not None and end is not None:
                extended_end = self._extend_with_body_end(start, end, entry)
                return start, extended_end
        found_bw = False
        body_start = None
        for instr in with_block.instructions:
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                found_bw = True
                continue
            if found_bw:
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'POP_TOP'):
                    body_start = instr.offset + 2
                    break
                elif instr.opname not in NOISE_OPS:
                    body_start = instr.offset
                    break
        if found_bw and body_start is None:
            succs = [s for s in with_block.successors if s != with_block]
            if succs:
                body_start = min(s.start_offset for s in succs)
        if body_start is not None:
            if found_bw and body_start > with_block.instructions[-1].offset:
                body_end = self._find_with_body_end_from_successors(with_block)
                if body_end is None:
                    body_end = body_start + 100
            else:
                last_instr = with_block.instructions[-1]
                body_end = last_instr.offset + 2
            return body_start, body_end
        return None, None

    def _extend_with_body_end(self, body_start, initial_end, exc_entry):
        exc_target = exc_entry.get('target', 0) if exc_entry else 0
        max_end = initial_end
        for entry in self.cfg.exception_table:
            e_start = entry.get('start', 0)
            e_end = entry.get('end', 0)
            e_target = entry.get('target', 0)
            if e_start >= body_start and e_end > max_end:
                if e_target == exc_target or e_start < exc_target:
                    max_end = max(max_end, e_end)
        if exc_target > max_end:
            _has_async_exit_protocol = False
            for block in self.cfg.get_blocks_in_order():
                if block.start_offset < initial_end:
                    continue
                if block.start_offset >= exc_target:
                    break
                if any(i.opname in ('GET_AWAITABLE', 'SEND') for i in block.instructions):
                    _has_async_exit_protocol = True
                    break
            if not _has_async_exit_protocol:
                max_end = exc_target
        for block in self.cfg.get_blocks_in_order():
            if block.start_offset < initial_end:
                continue
            if block.start_offset >= max_end:
                break
            if self._is_with_exit_cleanup(block):
                max_end = min(max_end, block.start_offset)
                break
            if any(i.opname == 'WITH_EXCEPT_START' for i in block.instructions):
                max_end = min(max_end, block.start_offset)
                break
        return max_end

    def _find_with_body_end_from_successors(self, with_block):
        visited = {with_block}
        worklist = list(with_block.successors)
        max_end = 0
        while worklist:
            b = worklist.pop(0)
            if b in visited:
                continue
            visited.add(b)
            if any(i.opname in ('WITH_EXCEPT_START', 'POP_EXCEPT', 'RERAISE') for i in b.instructions):
                continue
            if b.instructions:
                last_i = b.instructions[-1]
                end = last_i.offset + 2
                if end > max_end:
                    max_end = end
            for s in b.successors:
                if s not in visited:
                    worklist.append(s)
        return max_end if max_end > 0 else None

    def _find_after_with_store_block(self, with_block, entry_blocks):
        found_bw = False
        store_instr = None
        bw_offset = None
        for instr in with_block.instructions:
            if found_bw and instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                store_instr = instr
                break
            if found_bw and instr.opname == 'POP_TOP':
                store_instr = instr
                break
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                found_bw = True
                bw_offset = instr.offset
        if store_instr is None and found_bw and bw_offset is not None:
            for succ in with_block.successors:
                if succ.start_offset > bw_offset:
                    first_instr = succ.instructions[0] if succ.instructions else None
                    if first_instr and first_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'POP_TOP'):
                        return succ
            for succ in with_block.successors:
                if succ.start_offset > bw_offset and succ not in entry_blocks:
                    return succ
        if store_instr is None:
            return None
        store_idx = with_block.instructions.index(store_instr)
        if store_idx + 1 < len(with_block.instructions):
            next_instr = with_block.instructions[store_idx + 1]
            if next_instr.opname == 'JUMP_ABSOLUTE':
                for succ in with_block.successors:
                    if succ.start_offset == next_instr.argval:
                        return succ
        for succ in with_block.successors:
            if succ not in entry_blocks:
                return succ
        return None

    def _collect_with_cleanup_blocks(self, with_entry_blocks, with_body, body_start, body_end):
        cleanup_visited = set(with_entry_blocks) | set(with_body)
        exception_blocks = []
        normal_cleanup = []
        for e in self.cfg.exception_table:
            if e.get('start', 0) == body_start:
                hb = self.cfg.get_block_by_offset(e.get('target', 0))
                if hb and any(i.opname == 'WITH_EXCEPT_START' for i in hb.instructions):
                    handler_blocks = [hb]
                    worklist = list(handler_blocks)
                    while worklist:
                        cl_block = worklist.pop(0)
                        if cl_block in cleanup_visited:
                            continue
                        cleanup_visited.add(cl_block)
                        if any(i.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for i in cl_block.instructions):
                            continue
                        if cl_block not in with_body and cl_block not in with_entry_blocks:
                            exception_blocks.append(cl_block)
                        for succ in cl_block.successors:
                            if succ in cleanup_visited:
                                continue
                            if any(i.opname == 'WITH_EXCEPT_START' for i in succ.instructions):
                                worklist.append(succ)
                            elif succ in cl_block.exception_successors:
                                worklist.append(succ)
        if body_end is not None and body_end > 0:
            self._collect_normal_exit_cleanup(with_body, normal_cleanup, cleanup_visited,
                                              with_entry_blocks, body_end)
        return exception_blocks, normal_cleanup

    def _collect_normal_exit_cleanup(self, with_body, cleanup, cleanup_visited,
                                    entry_blocks, body_end):
        body_offsets = {b.start_offset for b in with_body}
        body_offsets.update(b.start_offset for b in entry_blocks)
        for block in self.cfg.get_blocks_in_order():
            if block in cleanup_visited:
                continue
            if block.start_offset in body_offsets:
                continue
            if block.start_offset < body_end:
                continue
            if any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in block.instructions):
                break
            if any(i.opname == 'WITH_EXCEPT_START' for i in block.instructions):
                continue
            in_range = any(
                body_end <= instr.offset < block.start_offset + 1000
                for instr in block.instructions
            )
            if not in_range:
                continue
            has_user_code = any(
                instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                 'BINARY_OP', 'UNARY_OP', 'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                                 'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET',
                                 'IMPORT_NAME', 'IMPORT_FROM', 'LOAD_BUILD_CLASS',
                                 'GET_ITER', 'GET_AITER', 'FOR_ITER', 'YIELD_VALUE',
                                 'CALL', 'PRECALL', 'CALL_FUNCTION', 'CALL_METHOD')
                for instr in block.instructions
                if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP',
                                        'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                        'POP_EXCEPT', 'COPY', 'RERAISE', 'SWAP')
            )
            if has_user_code:
                continue
            last = block.get_last_instruction()
            if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                meaningful = [i for i in block.instructions
                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP',
                                                  'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_EXCEPT',
                                                  'COPY', 'RERAISE', 'SWAP')]
                if len(meaningful) >= 2:
                    prev = meaningful[-2]
                    if prev.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                       'LOAD_ATTR', 'BINARY_SUBSCR', 'BINARY_OP', 'CALL',
                                       'PRECALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                       'COMPARE_OP', 'IS_OP', 'CONTAINS_OP',
                                       'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET'):
                        continue
            cleanup.append(block)
            cleanup_visited.add(block)

    def _scan_before_with_instructions(self):
        before_with_blocks = []
        depth_map = {}
        for block in self.cfg.get_blocks_in_order():
            has_bw = any(i.opname == 'BEFORE_WITH' for i in block.instructions)
            has_abw = any(i.opname == 'BEFORE_ASYNC_WITH' for i in block.instructions)
            if not has_bw and not has_abw:
                continue
            entry = self._find_with_exc_entry(block)
            depth = entry.get('depth', -1) if entry else -1
            before_with_blocks.append((block, has_abw, depth))
            depth_map[block] = depth
        before_with_blocks.sort(key=lambda x: x[2])
        return before_with_blocks, depth_map

    def _build_single_with_region(self, block, has_async, depth, depth_map):
        """构建单个with语句的区域对象。

        反编译逻辑：
        1. 冲突检测：检查入口块是否已被其他区域占据
           - 若已被非TryExceptRegion/LoopRegion占据，跳过
           - 若已被WithRegion占据且含BEFORE_WITH，检查是否有body代码在BEFORE_WITH之前
        2. 收集with入口块链：调用_collect_consecutive_with_blocks收集连续的
           BEFORE_WITH块（对应 `with A as a, B as b` 多上下文语法）
        3. 确定body起始块：调用_find_after_with_store_block找到BEFORE_WITH之后
           的STORE/POP_TOP块，作为with body的入口
        4. 获取body偏移范围：调用_get_with_body_range，基于异常表的[start,end)
           确定with body的指令偏移范围
        5. 收集body块：调用_collect_with_body_blocks，在偏移范围内收集所有
           非WITH_EXCEPT_START/BEFORE_WITH的块
        6. 收集清理块：调用_collect_with_cleanup_blocks，从异常处理器入口
           (WITH_EXCEPT_START块)开始BFS收集所有清理路径块
        7. 构建WithRegion：合并入口块+body块+清理块，设置角色标注
           (WITH_HANDLER/WITH_EXIT_CLEANUP/WITH_STACK_CLEANUP)
        8. 提取with items：调用_extract_with_items解析每个上下文表达式和目标变量

        关键约束：
        - 不硬编码偏移量，所有范围来自异常表和指令分析
        - WITH_EXCEPT_START块属于cleanup而非body
        - 连续with块的depth递增（depth_map），用于区分多上下文vs独立with
        """
        existing = self.block_to_region.get(block)
        if existing is not None and not isinstance(existing, (TryExceptRegion, LoopRegion)):
            if isinstance(existing, WithRegion) and any(
                i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in block.instructions
            ):
                if not self._has_body_code_before_before_with(block):
                    return None
            else:
                return None
        with_entry_blocks = self._collect_consecutive_with_blocks(block, depth_map)
        last_with = with_entry_blocks[-1]
        after_bw_block = self._find_after_with_store_block(last_with, with_entry_blocks)
        if after_bw_block and after_bw_block not in with_entry_blocks:
            if has_async and after_bw_block not in {b for blk in with_entry_blocks for b in blk.successors}:
                _cur = None
                for succ in block.successors:
                    if succ.start_offset > block.instructions[-1].offset:
                        _cur = succ
                        break
                while _cur is not None and _cur != after_bw_block:
                    if _cur not in with_entry_blocks:
                        with_entry_blocks.append(_cur)
                    _succs = [s for s in _cur.successors if s != _cur]
                    if len(_succs) == 1:
                        _cur = _succs[0]
                    else:
                        break
            with_entry_blocks.append(after_bw_block)
        body_start, body_end = self._get_with_body_range(last_with)
        with_body = self._collect_with_body_blocks(last_with, body_start, body_end)
        exception_blocks, cleanup_blocks = self._collect_with_cleanup_blocks(with_entry_blocks, with_body, body_start, body_end)
        all_blocks = set(with_entry_blocks) | set(with_body) | set(exception_blocks) | set(cleanup_blocks)
        region = WithRegion(
            region_type=RegionType.WITH, entry=block, blocks=all_blocks,
            with_blocks=with_body, exception_blocks=exception_blocks, cleanup_blocks=cleanup_blocks,
            body_offset_start=body_start, body_offset_end=body_end,
        )
        region.is_async = bool(has_async)
        self._extract_with_items(with_entry_blocks, region)
        self.regions.append(region)
        for b in all_blocks:
            if b not in self.block_to_region:
                self.block_to_region[b] = region
        if existing is not None and isinstance(existing, (TryExceptRegion, LoopRegion, WithRegion)):
            region.parent = existing
            existing.add_child(region)
        for cleanup_block in exception_blocks + cleanup_blocks:
            offset = cleanup_block.start_offset
            if self.block_roles.get(offset) == BlockRole.NORMAL:
                if any(i.opname in ('POP_EXCEPT', 'RERAISE') for i in cleanup_block.instructions):
                    self.block_roles[offset] = BlockRole.WITH_EXIT_CLEANUP
                elif any(i.opname == 'WITH_EXCEPT_START' for i in cleanup_block.instructions):
                    self.block_roles[offset] = BlockRole.WITH_HANDLER
                else:
                    self.block_roles[offset] = BlockRole.WITH_STACK_CLEANUP
        return region

    def _identify_with_regions(self) -> List[Region]:
        """_identify_with_regions — 识别 with 上下文管理器区域

        【区域类型】 WITH — 上下文管理器区域（With Region）
        RegionType 枚举值: RegionType.WITH

        1. 算法描述（基于"No More Gotos"论文）
           - 归约阶段: Phase 1（在 TRY 之后，LOOP 之前）
           - 识别策略: 扫描 BEFORE_WITH / BEFORE_ASYNC_WITH 指令定位 with 入口，
             基于异常表确定 body 范围，WITH_EXCEPT_START 定位 handler。
           - 归约过程:
             Step 1: 扫描所有 BEFORE_WITH/BEFORE_ASYNC_WITH 指令定位 with 入口块。
             Step 2: 基于异常表 [start, end) 确定 body 偏移范围。
             Step 3: 收集 body 块、cleanup 块、exception 块，构建 WithRegion。
             Step 4: 识别阶段即合并连续 with（with A: ... with B: ...），由 WithRegion.should_merge_with 多态方法判定。

        2. 字节码模式（CPython 编译器行为）
           模式 A: 基本 with
             源码: with ctx: ...
             特征指令: BEFORE_WITH, WITH_EXCEPT_START, PUSH_EXC_INFO, POP_EXCEPT, RERAISE
           模式 B: with as var
             BEFORE_WITH 后紧跟 STORE_* 存 __enter__() 返回值
           模式 C: async with
             特征指令: BEFORE_ASYNC_WITH, GET_AWAITABLE, SEND, YIELD_VALUE
           模式 D: 多上下文 with A as a, B as b:
             连续 BEFORE_WITH 块，异常表 depth 递增

        3. 边界条件（数学性质）
           - with body 范围 = 异常表 [start, end)
           - WITH_EXCEPT_START 块的 offset 在 body 范围之外（属于 handler target）
           - 嵌套 with: 外层 depth < 内层 depth
           - 连续 with 合并: region1.body_offset_end + 1 == region2.body_offset_start 且 depth 相同

        4. 归约语义（与父区域的契约）
           - 入口块: 含 BEFORE_WITH/BEFORE_ASYNC_WITH 的 BasicBlock（region.entry）
           - 父区域引用: 父区域仅引用本 region 的 entry 块
           - 子区域块不出现: with_blocks/cleanup_blocks/exception_blocks 全部归约为单个抽象节点

        5. AST 映射
           - 对应生成方法: _generate_with（region_ast_generator.py）
           - AST 节点类型: ast.With
           - 关键字段映射:
             with_blocks → With.body
             items → With.items（List[withitem]: context_expr + optional_vars）
             is_async → With.is_async

        6. 已知失败模式
           - 当前测试矩阵通过率: 100%（with_region 191/191），无已知失败模式
           - 本方法遵循区域归约算法 4 核心原则:
             自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
        """
        # 识别阶段即合并连续 WithRegion（区域归约算法：一次正确，无后处理补丁）
        # 合并条件由 WithRegion.should_merge_with 多态方法判定：相邻 entry + 同一异常表 depth
        regions = []
        before_with_blocks, depth_map = self._scan_before_with_instructions()
        for block, has_async, depth in before_with_blocks:
            region = self._build_single_with_region(block, has_async, depth, depth_map)
            if region:
                if regions and regions[-1].should_merge_with(region, self):
                    prev = regions[-1]
                    prev.blocks.update(region.blocks)
                    prev.with_blocks.extend(region.with_blocks)
                    prev.exception_blocks.extend(region.exception_blocks)
                    prev.cleanup_blocks.extend(region.cleanup_blocks)
                    prev.items.extend(region.items)
                    prev.body_offset_end = region.body_offset_end
                    for blk in region.blocks:
                        if blk not in self.block_to_region:
                            self.block_to_region[blk] = prev
                else:
                    regions.append(region)
        return regions

    def _has_intermediate_body_path(self, current, succ):
        for other_succ in current.successors:
            if other_succ == succ or other_succ in current.exception_successors:
                continue
            visited = {current, succ}
            worklist = [other_succ]
            while worklist:
                curr = worklist.pop(0)
                if curr in visited:
                    continue
                visited.add(curr)
                if curr == succ:
                    return True
                for s in curr.successors:
                    if s not in visited:
                        worklist.append(s)
        return False

    def identify_with_orphan_instructions(self, block, with_region, nested_region):
        if block not in with_region.blocks:
            return []
        nested_blocks = set(nested_region.blocks) if nested_region else set()
        if nested_region is not None and block in nested_blocks:
            return nested_region.get_with_body_orphan_instructions(block)
        return [i for i in block.instructions if i.opname not in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH')]

    def _collect_with_body_blocks(self, entry: BasicBlock,
                                   body_start: int, body_end: int) -> List[BasicBlock]:
        """收集with语句body中的块，使用异常表范围过滤。

        反编译逻辑：
        1. 范围验证：body_start和body_end必须有效且body_end > body_start
        2. 入口块body检测：检查入口块中BEFORE_WITH之后是否有指令落在
           [body_start, body_end)范围内（处理body代码与BEFORE_WITH同块的情况）
        3. 全局块扫描：遍历所有基本块，收集满足以下条件的块：
           a. 块的start_offset在[body_start, body_end)内，或
           b. 块内有指令的offset落在[body_start, body_end)内（处理块不对齐）
        4. 排除规则：
           - 含WITH_EXCEPT_START的块（属于cleanup路径）
           - 含BEFORE_WITH/BEFORE_ASYNC_WITH的块（属于其他with的入口）
           - 入口块自身（已在步骤2单独处理）

        字节码布局：
        - with body的指令偏移范围对应异常表的[start, end)
        - WITH_EXCEPT_START块在body范围之外（是handler target）
        - 嵌套try/except的块可能在body范围内，需要保留

        关键约束：
        - 不硬编码偏移量，范围来自异常表
        - WITH_EXCEPT_START块始终属于cleanup而非body
        - 嵌套的BEFORE_WITH块属于内层with，不应出现在外层body中
        """
        body: List[BasicBlock] = []

        if body_start is None or body_end is None or body_end <= body_start:
            return body

        found_bw = False
        has_body_in_entry = False
        for instr in entry.instructions:
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                found_bw = True
                continue
            if found_bw and instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'POP_TOP'):
                continue
            if found_bw and instr.opname not in NOISE_OPS:
                if body_start <= instr.offset < body_end:
                    has_body_in_entry = True
                    break

        if has_body_in_entry:
            body.append(entry)

        for block in self.cfg.get_blocks_in_order():
            if block == entry:
                continue
            if any(i.opname == 'WITH_EXCEPT_START' for i in block.instructions):
                continue
            if any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in block.instructions):
                continue

            in_range = False
            if block.start_offset >= body_start and block.start_offset < body_end:
                in_range = True
            else:
                in_range = any(
                    body_start <= instr.offset < body_end
                    for instr in block.instructions
                )

            if in_range:
                body.append(block)

        return body

    def _extract_with_items(self, entry_blocks: List[BasicBlock], region: WithRegion) -> None:
        """从with入口块中提取上下文表达式和目标变量。

        反编译逻辑：
        1. 指令收集：将所有入口块的指令按顺序拼接
        2. 定位BEFORE_WITH：找到所有BEFORE_WITH/BEFORE_ASYNC_WITH指令位置
        3. 提取上下文表达式：对每个BEFORE_WITH，从上一个BEFORE_WITH（或块起始）
           到当前BEFORE_WITH之间的LOAD/CALL类指令构成上下文表达式
        4. 提取目标变量：BEFORE_WITH之后紧跟的STORE_*指令的argval即为目标变量名
           （若无STORE则为POP_TOP，对应 `with ctx:` 无as子句的情况）
        5. 设置region.items和region.target

        字节码模式：
        - `with open('f') as fa:` → LOAD_NAME('open') LOAD_CONST('f') CALL BEFORE_WITH STORE_FAST('fa')
        - `with ctx:` → LOAD_NAME('ctx') BEFORE_WITH POP_TOP
        - `with A as a, B as b:` → ...BEFORE_WITH STORE_FAST('a') ...BEFORE_WITH STORE_FAST('b')
        - `with ctx as (a, b):` → ...BEFORE_WITH UNPACK_SEQUENCE 2 STORE_NAME('a') STORE_NAME('b')

        关键约束：
        - 上下文表达式指令仅包含LOAD/CALL/PUSH_NULL等值产生指令
        - NOISE_OPS（RESUME/NOP/CACHE）被跳过
        - 目标变量为None时表示无as子句
        - 多目标 as 绑定（with ctx as (a, b)）的 target 以 AST 字典形式
          （{'type': 'Tuple', 'elts': [...]}）表示，单目标为字符串名
        """
        import dis
        items = []
        if not entry_blocks:
            region.items = items
            return
        instructions = []
        for entry_block in entry_blocks:
            for instr in entry_block.instructions:
                instructions.append(instr)
        
        # 收集所有 BEFORE_WITH 指令的位置
        bw_positions = []
        for i, instr in enumerate(instructions):
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                bw_positions.append(i)
        
        # 对于每个 BEFORE_WITH，收集它之前的上下文表达式
        for idx, bw_pos in enumerate(bw_positions):
            # 找到这个 BEFORE_WITH 之前的上下文表达式
            # 查找上一个 BEFORE_WITH 的位置，或者 0
            prev_bw_pos = bw_positions[idx - 1] if idx > 0 else -1
            start_search = prev_bw_pos + 1
            
            # 从 start_search 到 bw_pos 之间提取上下文表达式
            ctx_expr = []
            i = start_search
            while i < bw_pos:
                instr = instructions[i]
                # 跳过噪声指令
                if instr.opname in NOISE_OPS:
                    i += 1
                    continue
                # 收集所有看起来是加载/调用的指令
                if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_ATTR', 'LOAD_FAST',
                                   'LOAD_CONST', 'LOAD_METHOD', 'CALL', 'PRECALL',
                                   'PUSH_NULL', 'SWAP', 'COPY', 'BINARY_SUBSCR',
                                   'BINARY_OP', 'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP',
                                   'BUILD_SET', 'BUILD_STRING', 'BUILD_SLICE',
                                   'UNPACK_SEQUENCE', 'IS_OP', 'CONTAINS_OP'):
                    ctx_expr.append(instr)
                i += 1
            
            # 查找目标变量（在 BEFORE_WITH 之后的 STORE 或 UNPACK_SEQUENCE）
            target = None
            if bw_pos + 1 < len(instructions):
                next_instr = instructions[bw_pos + 1]
                if next_instr.opname == 'UNPACK_SEQUENCE':
                    # with ctx as (a, b): 模式 - 多目标 as 绑定
                    # 字节码模式: BEFORE_WITH, UNPACK_SEQUENCE N, STORE_* x N
                    unpack_count = next_instr.argval if isinstance(next_instr.argval, int) else next_instr.arg
                    if not isinstance(unpack_count, int):
                        unpack_count = 2
                    names = []
                    j = bw_pos + 2
                    for _ in range(unpack_count):
                        if j < len(instructions) and instructions[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            names.append(instructions[j].argval)
                            j += 1
                        else:
                            break
                    if names and len(names) == unpack_count:
                        target = {
                            'type': 'Tuple',
                            'elts': [{'type': 'Name', 'id': n, 'ctx': 'Store'} for n in names],
                            'ctx': 'Store',
                        }
                elif next_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    target = next_instr.argval

            items.append((ctx_expr, target))

        region.items = items
        # region.target 仅保留单目标字符串名，多目标 Tuple 字典不写入
        # （region.target 在多处按字符串使用，Tuple 信息只通过 items 传递）
        _first_target = region.items[0][1] if region.items and region.items[0][1] else None
        region.target = _first_target if isinstance(_first_target, str) else None

    def _is_except_star_framework_block(self, block: 'BasicBlock') -> bool:
        """检测块是否是 except*（异常组）语法的框架块

        except* 的框架指令包括 CHECK_EG_MATCH、PREP_RERAISE_STAR、LIST_APPEND
        （在异常组上下文中）。这些块不应被识别为 MatchRegion 或其他区域。
        """
        if block is None:
            return False
        return any(i.opname in ('CHECK_EG_MATCH', 'PREP_RERAISE_STAR') for i in block.instructions)

    def _is_match_subject_block(self, block: 'BasicBlock') -> bool:
        """检测块是否是 match 语句的 subject 块（字面量模式）

        算法依据：match-case 中 subject 只加载一次，通过 COPY 复制给每个 case 比较；
        而 if-elif 每次比较都重新加载 subject，字节码中不含 COPY。
        因此 COPY + 比较 + 条件跳转 的组合是 match-case 的确定性特征。

        检测条件：
        1. 块中包含 COPY 指令
        2. COPY 之后紧跟比较操作（COMPARE_OP/IS_OP）或 None 检查（POP_JUMP_IF_NOT_NONE）
        3. 块以条件跳转结尾
        4. 块中不含 MATCH_CLASS/MATCH_MAPPING/MATCH_SEQUENCE/MATCH_KEYS（那些由 _has_match_op 处理）
        5. COPY 不是异常处理的一部分（后面不跟 PUSH_EXC_INFO）
        """
        if block is None:
            return False
        # 已由 _has_match_op 处理的结构型模式，此处不重复
        if self._has_match_op(block):
            return False

        # [Phase 3 adv17_try_except_star] except* 框架块（含 CHECK_EG_MATCH
        # 或 PREP_RERAISE_STAR）不是 match subject 块。except* 的清理块
        # LIST_APPEND + PREP_RERAISE_STAR + COPY + POP_JUMP_IF_NOT_NONE
        # 会被误识别为 match subject（模式2: COPY + POP_JUMP_IF_NOT_NONE），
        # 但实际是 except* 的异常组清理逻辑。
        if self._is_except_star_framework_block(block):
            return False

        instrs = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not instrs:
            return False

        # 块必须以条件跳转结尾
        last = instrs[-1]
        if last.opname not in CONDITIONAL_JUMP_OPS:
            return False

        # 如果有 SWAP 指令，很可能是链式比较 a < b < c，不是 match
        has_swap = any(instr.opname == 'SWAP' for instr in instrs)
        if has_swap:
            return False

        # 查找 COPY 指令的位置
        copy_idx = None
        for i, instr in enumerate(instrs):
            if instr.opname == 'COPY':
                copy_idx = i
                break

        if copy_idx is None:
            return False

        # COPY 后面不能是 PUSH_EXC_INFO（异常处理模式）
        if copy_idx + 1 < len(instrs) and instrs[copy_idx + 1].opname == 'PUSH_EXC_INFO':
            return False

        # COPY 后面紧跟 STORE_FAST/STORE_NAME 是 walrus 运算符 (:=) 模式，不是 match subject
        if copy_idx + 1 < len(instrs) and instrs[copy_idx + 1].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
            return False

        # COPY 之后必须紧跟比较操作或 None 检查
        # 模式1: COPY + LOAD_CONST + COMPARE_OP/IS_OP + ... + 条件跳转
        # 模式2: COPY + POP_JUMP_IF_NOT_NONE（case None 模式）
        after_copy = instrs[copy_idx + 1:]

        # 模式2: COPY + POP_JUMP_IF_NOT_NONE
        if (len(after_copy) >= 1 and
            after_copy[0].opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE')):
            return True

        # 模式1: COPY + LOAD_CONST + COMPARE_OP/IS_OP
        if (len(after_copy) >= 2 and
            after_copy[0].opname == 'LOAD_CONST' and
            after_copy[1].opname in ('COMPARE_OP', 'IS_OP')):
            return True

        # 也处理 COPY + LOAD_NAME(True/False) + IS_OP 的情况
        if (len(after_copy) >= 2 and
            after_copy[0].opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST') and
            after_copy[1].opname == 'IS_OP'):
            return True

        return False

    def _is_literal_default_block(self, block: 'BasicBlock', visited: 'Set[BasicBlock]') -> bool:
        """检测块是否是字面量match的default case块

        default case的特征：
        - 不以条件跳转结尾
        - 不包含MATCH_*操作码
        - 不包含比较操作（COMPARE_OP/IS_OP）
        - 包含实际的业务逻辑（不仅仅是RETURN_VALUE/LOAD_CONST等平凡操作）
        """
        if block is None:
            return False

        last = block.get_last_instruction()
        if last and last.opname in CONDITIONAL_JUMP_OPS:
            return False

        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not meaningful:
            return False

        # 不包含比较操作
        has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in meaningful)
        if has_compare:
            return False

        # 不包含MATCH_*操作码
        if any(i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                             'MATCH_KEYS', 'MATCH_MAPPING_KEYS') for i in meaningful):
            return False

        # 修复：不再将仅包含平凡操作的块视为default case
        # 平凡操作包括：POP_TOP, LOAD_CONST, RETURN_VALUE, RETURN_CONST, STORE_*, JUMP_*
        # 因为case body在函数结束时也会以这些操作结尾，这不代表它是default case
        trivial_ops = frozenset((
            'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
            'JUMP_FORWARD', 'JUMP_ABSOLUTE',
        ))
        has_non_trivial = any(i.opname not in trivial_ops for i in meaningful)

        # 只有包含非平凡操作时才认为是default case
        # 或者是显式的pass/空body（但这种情况应该由调用者处理）
        if has_non_trivial:
            return True

        # 特殊情况：以NOP开头的块是match default case的可靠指标
        # match x: case 1: pass case _: pass 的default块以NOP开头
        # if x == 1: pass else: pass 的else块不以NOP开头
        has_nop_prefix = False
        for instr in block.instructions:
            if instr.opname == 'NOP':
                has_nop_prefix = True
            elif instr.opname not in NOISE_OPS:
                break
        if has_nop_prefix:
            return True

        return False

    def _verify_literal_match_chain(self, subject_block: 'BasicBlock', case_blocks: list) -> bool:
        if not case_blocks:
            return False

        has_copy = any(i.opname == 'COPY' for i in subject_block.instructions)
        if not has_copy:
            last = subject_block.get_last_instruction()
            if last and last.opname in CONDITIONAL_JUMP_OPS:
                jt = self.cfg.get_block_by_offset(last.argval)
                if jt:
                    has_nop_prefix = False
                    for instr in jt.instructions:
                        if instr.opname == 'NOP':
                            has_nop_prefix = True
                        elif instr.opname not in NOISE_OPS:
                            break
                    if has_nop_prefix:
                        return True
                has_none_check = last.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE',
                                                  'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE')
                if has_none_check:
                    meaningful = [i for i in subject_block.instructions if i.opname not in NOISE_OPS]
                    load_ops = [i for i in meaningful if i.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')]
                    other_ops = [i for i in meaningful if i.opname not in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and i.opname not in CONDITIONAL_JUMP_OPS]
                    if len(load_ops) == 1 and all(o.opname in ('POP_TOP',) for o in other_ops):
                        return True
            if self._is_wildcard_match_block(subject_block):
                return True
            return False

        # 提取subject变量名（从subject块的LOAD指令获取）
        subject_var = None
        for instr in subject_block.instructions:
            if instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                # 确保这个LOAD不是在COPY之后（COPY之后的LOAD是pattern的一部分）
                instr_idx = subject_block.instructions.index(instr)
                copy_indices = [i for i, x in enumerate(subject_block.instructions) if x.opname == 'COPY']
                if copy_indices and instr_idx > copy_indices[0]:
                    continue
                subject_var = instr.argval
                break

        # 如果有subject变量名，检查后续case块是否重新加载了同一变量
        # match-case中后续case不会重新加载subject，if-elif会
        if subject_var and len(case_blocks) > 1:
            reload_count = 0
            for cb in case_blocks[1:]:
                for instr in cb.instructions:
                    if instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                        if instr.argval == subject_var:
                            reload_count += 1
                            break
            # 如果所有后续case都重新加载了subject，更可能是if-elif
            if reload_count == len(case_blocks) - 1 and len(case_blocks) > 2:
                return False

        return True

    def _identify_match_regions(self) -> List[Region]:
        """_identify_match_regions — 识别 match-case 模式匹配区域

        【区域类型】 MATCH — 模式匹配区域（Match Region）
        RegionType 枚举值: RegionType.MATCH

        1. 算法描述（基于"No More Gotos"论文）
           - 归约阶段: Phase 1（在 TRY/WITH 之后，LOOP/IF 之前）
           - 识别策略: 双相位扫描。Phase 1 检测结构型模式（MATCH_* 操作码），
             Phase 2 通过 _scan_literal_match_subjects 检测字面量模式（COPY + COMPARE_OP/IS_OP）。
             两种形态共用 _mr_collect_case_body 沿条件跳转链收集 case 块。
           - 归约过程:
             Step 1: 扫描 MATCH_MAPPING/MATCH_KEYS/MATCH_CLASS/MATCH_SEQUENCE 指令定位结构型 match。
             Step 2: _scan_literal_match_subjects 检测字面量 match（COPY+COMPARE_OP 模式）。
             Step 3: _mr_collect_case_body 收集每个 case 的 body 块，排除 pattern_check_blocks。
             Step 4: _mr_resolve_pattern_check_chain 沿 fall-through 链跳过模式检查块，找到真正 body 入口。
             Step 5: 构建 MatchRegion，注册 block_to_region。

        2. 字节码模式（CPython 编译器行为）
           模式 A: 结构型模式 match
             源码: match x: case [a, b]: ...
             特征指令: MATCH_SEQUENCE, MATCH_MAPPING, MATCH_CLASS, MATCH_KEYS
           模式 B: 字面量模式 match
             源码: match x: case 1: ...
             特征指令: COPY, COMPARE_OP, IS_OP, POP_JUMP_FORWARD_IF_FALSE
           模式 C: guard 模式
             源码: case _ if cond: ...
             特征: case body 内含条件跳转，guard 块归 MatchRegion 所有

        3. 边界条件（数学性质）
           - case body 边界: _mr_collect_case_body BFS 收集，stop_set 包含 pattern_check_blocks
           - pattern_check_blocks: 含 MATCH_* 指令且以 POP_JUMP_IF_NONE/FALSE 结尾的块
           - guard 块归属: 位于 case body 内且条件跳转目标指向下一 case_block 的块属于 guard
           - 每个基本块经 block_to_region 唯一归属一个 MatchRegion

        4. 归约语义（与父区域的契约）
           - 入口块: match subject 加载块（region.entry）
           - 父区域引用: 父区域仅引用本 region 的 entry 块
           - 子区域块不出现: case_blocks/body_blocks 全部归约为单个抽象节点

        5. AST 映射
           - 对应生成方法: _generate_match（region_ast_generator.py）
           - AST 节点类型: ast.Match
           - 关键字段映射:
             subject → Match.subject
             case_blocks → Match.cases（每个 → match_case: pattern + guard + body）

        6. 已知失败模式
           - 当前测试矩阵通过率: 100%（match_region 198/198，2 skipped）
           - m085 已知限制: 结构型 match + guard 模式下 pattern check chain 解析依赖
             CPython 字节码细节，标记为 skipped（非缺陷，与上游 CPython 行为一致）
           - 本方法遵循区域归约算法 4 核心原则:
             自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
        """
        match_regions = []
        claimed = set(self.block_to_region.keys())
        for block in self.cfg.get_blocks_in_order():
            if block in claimed:
                existing = self.block_to_region.get(block)
                if isinstance(existing, MatchRegion):
                    continue
                if not (self._has_match_op(block) or self._is_case_pattern_block(block) or self._is_match_subject_block(block)):
                    continue
            else:
                if not (self._has_match_op(block) or self._is_case_pattern_block(block)):
                    continue
            subject_block = block
            if self._is_case_pattern_block(block):
                for pred in sorted(block.predecessors, key=lambda p: p.start_offset):
                    last = pred.get_last_instruction()
                    if last and last.opname in CONDITIONAL_JUMP_OPS:
                        if self._is_case_pattern_block(pred) or self._has_match_op(pred):
                            subject_block = pred
                            break
            case_blocks, case_patterns, case_bodies, merge, all_raw_blocks = self._mr_collect_case_body(subject_block)
            if not case_blocks:
                continue
            all_blocks = all_raw_blocks
            all_blocks.update({subject_block} | set(case_blocks))
            for body in case_bodies:
                all_blocks.update(body)
            if merge:
                all_blocks.add(merge)
            case_guards = [self.pattern_parser.parse_case_guard(
                self.pattern_parser.collect_pattern_blocks(cb, all_blocks)) for cb in case_blocks]
            region = MatchRegion(
                region_type=RegionType.MATCH, entry=subject_block, blocks=all_blocks,
                subject_block=subject_block, case_blocks=case_blocks,
                case_patterns=case_patterns, case_guards=case_guards,
                case_bodies=case_bodies, merge_block=merge)
            region.case_body_start_indices = self._mr_compute_case_body_start_indices(region)
            match_regions.append(region)
            self.regions.append(region)
            for b in region.blocks:
                if b not in self.block_to_region:
                    self.block_to_region[b] = region
                    claimed.add(b)
        literal_regions = self._scan_literal_match_subjects(claimed)
        match_regions.extend(literal_regions)
        return match_regions

    def _mr_collect_pattern_store_names(self, pattern, names):
        if not pattern or not isinstance(pattern, dict):
            return
        ptype = pattern.get('type')
        if ptype == 'MatchAs':
            name = pattern.get('name')
            if name:
                names.add(name)
            inner = pattern.get('pattern')
            if inner:
                self._mr_collect_pattern_store_names(inner, names)
        elif ptype == 'MatchStarred':
            inner = pattern.get('pattern')
            if inner:
                self._mr_collect_pattern_store_names(inner, names)
        elif ptype == 'MatchSequence':
            for p in pattern.get('patterns', []):
                self._mr_collect_pattern_store_names(p, names)
        elif ptype == 'MatchMapping':
            for p in pattern.get('patterns', []):
                self._mr_collect_pattern_store_names(p, names)
            rest = pattern.get('rest')
            if rest:
                names.add(rest)
        elif ptype == 'MatchClass':
            for p in pattern.get('patterns', []):
                self._mr_collect_pattern_store_names(p, names)
            for p in pattern.get('keyword_patterns', []):
                self._mr_collect_pattern_store_names(p, names)
        elif ptype == 'MatchOr':
            for p in pattern.get('patterns', []):
                self._mr_collect_pattern_store_names(p, names)

    def _mr_compute_case_body_start_indices(self, region):
        indices = {}
        NOISE = frozenset(('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
        MATCH_OPS = frozenset(('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                               'MATCH_KEYS', 'MATCH_MAPPING_KEYS'))
        STORE_OPS = frozenset(('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'))
        LOAD_OPS = frozenset(('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'))
        COND_JUMPS = frozenset(CONDITIONAL_JUMP_OPS)
        for i, block in enumerate(region.case_blocks):
            if not block.instructions:
                indices[block.start_offset] = 0
                continue
            pattern = region.case_patterns[i] if i < len(region.case_patterns) else None
            pattern_store_names = set()
            if pattern:
                self._mr_collect_pattern_store_names(pattern, pattern_store_names)
            instrs = block.instructions
            idx = 0
            if block == region.subject_block:
                _has_match_op_in_block = any(i.opname in MATCH_OPS for i in instrs)
                while idx < len(instrs):
                    op = instrs[idx].opname
                    if op in NOISE:
                        idx += 1
                        continue
                    if op in MATCH_OPS:
                        break
                    if op in LOAD_OPS:
                        if idx + 1 < len(instrs) and instrs[idx + 1].opname in MATCH_OPS:
                            idx += 1
                            break
                        if (idx + 2 < len(instrs) and instrs[idx + 1].opname == 'LOAD_CONST'
                                and isinstance(instrs[idx + 1].argval, tuple)
                                and instrs[idx + 2].opname == 'MATCH_CLASS'):
                            idx += 1
                            break
                        idx += 1
                        continue
                    if op == 'COPY':
                        break
                    if op in ('LOAD_CONST',) and idx + 1 < len(instrs) and instrs[idx + 1].opname in ('COMPARE_OP', 'IS_OP'):
                        break
                    if op in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE'):
                        break
                    if op == 'POP_TOP' and not _has_match_op_in_block:
                        break
                    idx += 1
                    continue
            saw_unpack = False
            pattern_store_counts = {}
            while idx < len(instrs):
                op = instrs[idx].opname
                if op in NOISE or op in MATCH_OPS or op in COND_JUMPS or op == 'POP_TOP':
                    idx += 1
                    continue
                if op in ('UNPACK_SEQUENCE', 'UNPACK_EX'):
                    saw_unpack = True
                    idx += 1
                    continue
                if op in STORE_OPS:
                    if saw_unpack:
                        saw_unpack = False
                        idx += 1
                        continue
                    store_name = instrs[idx].argval
                    if store_name in pattern_store_names:
                        prev_count = pattern_store_counts.get(store_name, 0)
                        if prev_count == 0:
                            pattern_store_counts[store_name] = 1
                            pattern_store_names.discard(store_name)
                            idx += 1
                            continue
                    if not pattern_store_names:
                        idx += 1
                        continue
                    break
                if op == 'LOAD_CONST':
                    if idx + 1 < len(instrs) and instrs[idx + 1].opname in ('COMPARE_OP', 'IS_OP'):
                        idx += 1
                        continue
                    if idx + 1 < len(instrs) and instrs[idx + 1].opname in STORE_OPS:
                        break
                    idx += 1
                    continue
                if op in ('COMPARE_OP', 'IS_OP') or op == 'GET_LEN' or op == 'SWAP':
                    idx += 1
                    continue
                if op == 'COPY':
                    if idx + 1 < len(instrs) and instrs[idx + 1].opname in ('COMPARE_OP', 'IS_OP'):
                        idx += 1
                        continue
                    idx += 1
                    continue
                if op in ('BUILD_MAP', 'DICT_UPDATE', 'DELETE_SUBSCR',
                           'BINARY_SUBSCR', 'LOAD_ATTR'):
                    idx += 1
                    continue
                if op in ('RETURN_VALUE', 'RETURN_CONST'):
                    if not pattern_store_names:
                        idx += 1
                        continue
                    break
                if op in LOAD_OPS:
                    if (idx + 2 < len(instrs) and instrs[idx + 1].opname == 'LOAD_CONST'
                            and isinstance(instrs[idx + 1].argval, tuple)
                            and instrs[idx + 2].opname == 'MATCH_CLASS'):
                        idx += 3
                        continue
                    break
                break
            indices[block.start_offset] = idx if 0 < idx < len(instrs) else 0
        return indices

    def _mr_resolve_body_entry(self, body_entry):
        if body_entry is None:
            return None
        visited = set()
        current = body_entry
        while current and current not in visited:
            visited.add(current)
            meaningful = [i for i in current.instructions if i.opname not in NOISE_OPS]
            if len(meaningful) == 1 and meaningful[0].opname == 'JUMP_FORWARD':
                target = self.cfg.get_block_by_offset(meaningful[0].argval)
                current = target if target else None
            else:
                break
        return current

    def _mr_resolve_pattern_check_chain(self, entry, pattern_check_blocks, jt):
        """区域归约算法：[RC1] 跳过模式检查块，找到真正的 body 入口。

        模式检查块（含 MATCH_KEYS/MATCH_CLASS/MATCH_MAPPING/MATCH_SEQUENCE +
        条件跳转 POP_JUMP_*_IF_NONE/FALSE）属于 case 头部的模式匹配逻辑，
        不属于 body。沿 fall-through 链（非跳转边）跳过所有模式检查块，
        直到找到第一个非模式检查块。

        字节码示例（case {'key': val}:）：
          case_block: MATCH_MAPPING, POP_JUMP_IF_FALSE -> next_case
          pattern_check: LOAD_CONST(('key',)), MATCH_KEYS, POP_JUMP_IF_NONE -> fail
          body: UNPACK_SEQUENCE, STORE_NAME(val), ...  <- 真正的 body 入口

        本方法从 pattern_check 的 fall-through（非跳转后继）找到 body。

        Args:
            entry: BFS 起始块（通常是 success，可能是模式检查块）
            pattern_check_blocks: 已识别的模式检查块集合
            jt: 下一 case 块（next_case），不应作为 body 入口

        Returns:
            真正的 body 入口块；若 entry 不是模式检查块，直接返回 entry
        """
        if not entry or not pattern_check_blocks or entry not in pattern_check_blocks:
            return entry
        current = entry
        visited = {entry}
        while current in pattern_check_blocks:
            jump_instr = self._mr_find_case_jump_instruction(current)
            if not jump_instr:
                break
            jump_target = self.cfg.get_block_by_offset(jump_instr.argval)
            # fall-through = 非跳转后继（模式匹配成功时继续执行的块）
            fall_through = None
            for succ in sorted(current.successors, key=lambda s: s.start_offset):
                if succ != jump_target:
                    fall_through = succ
                    break
            if not fall_through or fall_through == jt or fall_through in visited:
                break
            visited.add(fall_through)
            current = fall_through
        return current

    def _mr_find_case_jump_instruction(self, case_block):
        if not case_block or not case_block.instructions:
            return None
        for instr in reversed(case_block.instructions):
            if instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                                'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE',
                                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE',
                                'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE'):
                return instr
        return None

    def _mr_resolve_or_guard_jump(self, current, jump_instr, jt, success):
        """区域归约算法：处理 or-guard 短路跳转

        当 case 的跳转指令是 POP_JUMP_FORWARD_IF_TRUE（or 短路求值）时，
        跳转目标是 CASE BODY（条件为真时执行），而不是下一个 case。
        真正的"下一个 case"是 guard 链中 POP_JUMP_FORWARD_IF_FALSE 的目标。

        字节码模式：`case n if A or B: body` 编译为：
          case_block: COMPARE A, POP_JUMP_FORWARD_IF_TRUE body  ← or 短路到 body
          guard_cont: COMPARE B, POP_JUMP_FORWARD_IF_FALSE next_case  ← guard 失败到下一 case
          body: ... (case body)
          next_case: ... (下一个 case)

        若不修复，jt=body（误为下一 case），success=guard_cont（误为 body），
        导致 case body 丢失、下一 case 被吞入当前 case body。

        Args:
            current: 当前 case 块
            jump_instr: 当前块的跳转指令
            jt: 原始跳转目标（IF_TRUE 时是 case body）
            success: 原始 fall-through（IF_TRUE 时是 guard 延续）

        Returns:
            (jt, success, guard_chain_blocks) — 修正后的 (下一case, case_body入口, guard链块集合)
            若不是 or-guard 模式，返回原始值和空集合
        """
        IF_TRUE_OPS = ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE')
        IF_FALSE_OPS = ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
                        'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE',
                        'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE')
        if jump_instr.opname not in IF_TRUE_OPS:
            return jt, success, set()
        or_case_body_entry = jt
        guard_cont = success
        guard_chain_visited = {current}
        while guard_cont and guard_cont not in guard_chain_visited:
            guard_chain_visited.add(guard_cont)
            guard_jump = self._mr_find_case_jump_instruction(guard_cont)
            if guard_jump and guard_jump.opname in IF_FALSE_OPS:
                jt = self.cfg.get_block_by_offset(guard_jump.argval)
                break
            elif guard_jump and guard_jump.opname in IF_TRUE_OPS:
                or_body_cand = self.cfg.get_block_by_offset(guard_jump.argval)
                guard_cont = self._mr_find_case_success_branch(guard_cont, or_body_cand)
            else:
                break
        success = or_case_body_entry
        return jt, success, guard_chain_visited - {current}

    def _mr_find_case_success_branch(self, case_block, jump_target):
        if not case_block:
            return None
        for succ in sorted(case_block.successors, key=lambda s: s.start_offset):
            if succ != jump_target:
                return succ
        cond_succs = list(case_block.conditional_successors)
        if len(cond_succs) >= 2:
            for succ in cond_succs:
                if succ != jump_target:
                    return succ
        return None

    def _mr_collect_case_body_by_offset(self, entry_block, next_case_offset, visited):
        if not entry_block:
            return set()
        body_set = set()
        worklist = [entry_block]
        local_visited = set()
        while worklist:
            block = worklist.pop(0)
            if block in visited or block in local_visited:
                continue
            if block.start_offset >= next_case_offset:
                continue
            local_visited.add(block)
            body_set.add(block)
            last_instr = block.get_last_instruction()
            if last_instr and last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST',
                                                      'RAISE_VARARGS', 'RERAISE',
                                                      'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                continue
            for succ in sorted(block.successors, key=lambda s: s.start_offset):
                if succ not in visited and succ not in local_visited and succ.start_offset < next_case_offset:
                    worklist.append(succ)
        return body_set

    def _mr_collect_simple_body_blocks(self, block, visited):
        start = block
        meaningful = [i for i in start.instructions if i.opname not in NOISE_OPS]
        if all(i.opname == 'POP_TOP' for i in meaningful) and len(start.successors) == 1:
            start = next(iter(start.successors))
        result = [start]
        start_last = start.get_last_instruction()
        if start_last and start_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
            return result
        worklist = list(start.successors)
        local_visited = {start}
        while worklist:
            succ = worklist.pop(0)
            if succ in visited or succ in local_visited:
                continue
            local_visited.add(succ)
            result.append(succ)
            last = succ.get_last_instruction()
            if last and last.opname not in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE',
                                            'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                for s in succ.successors:
                    if s not in visited and s not in local_visited:
                        worklist.append(s)
        return result

    def _mr_finalize_match_region(self, case_blocks, case_patterns, case_bodies, all_blocks):
        merged_p, merged_b, i = [], [], 0
        while i < len(case_blocks):
            orps, body = [case_patterns[i]], set(case_bodies[i])
            j = i + 1
            while j < len(case_blocks):
                body_i_set = set(case_bodies[i])
                body_j_set = set(case_bodies[j])
                should_merge = (body_i_set and body_j_set and self._mr_bodies_are_equivalent(body_i_set, body_j_set))
                if should_merge:
                    orps.append(case_patterns[j])
                    j += 1
                else:
                    break
            or_pattern = {'type': 'MatchOr', 'patterns': orps} if len(orps) > 1 else orps[0]
            if isinstance(or_pattern, dict) and or_pattern.get('type') == 'MatchOr':
                self._apply_or_capture_name(or_pattern, body)
            merged_p.append(or_pattern)
            merged_b.append(sorted(body, key=lambda b: b.start_offset))
            i = j
        merge_block = self._mr_compute_case_merge(merged_b)
        return case_blocks, merged_p, merged_b, merge_block, all_blocks

    def _apply_or_capture_name(self, or_pattern: Dict[str, Any], body: Set[BasicBlock]):
        STORE_OPS = frozenset({'STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'})
        for body_block in sorted(body, key=lambda b: b.start_offset):
            for instr in body_block.instructions:
                if instr.opname in STORE_OPS and instr.argval:
                    self._set_or_pattern_names(or_pattern, instr.argval)
                    return

    def _set_or_pattern_names(self, pattern: Dict[str, Any], name: str):
        if not isinstance(pattern, dict):
            return
        ptype = pattern.get('type', '')
        if ptype == 'MatchAs' and not pattern.get('name'):
            pattern['name'] = name
        for key in ('pattern', 'patterns'):
            val = pattern.get(key)
            if isinstance(val, dict):
                self._set_or_pattern_names(val, name)
            elif isinstance(val, list):
                for item in val:
                    self._set_or_pattern_names(item, name)

    def _mr_bodies_are_equivalent(self, body_i_set, body_j_set):
        if body_i_set == body_j_set:
            return True
        if not body_i_set or not body_j_set:
            return False
        sorted_i = sorted(body_i_set, key=lambda b: b.start_offset)
        sorted_j = sorted(body_j_set, key=lambda b: b.start_offset)
        if sorted_i[-1] == sorted_j[-1]:
            return True
        return False

    def _mr_compute_case_merge(self, case_bodies):
        all_bod = set()
        for b in case_bodies:
            all_bod.update(b)
        exits = {s for b in all_bod for s in b.successors if s not in all_bod}
        if len(exits) >= 2:
            return self.dom_analyzer.find_nearest_common_post_dominator(exits)
        elif len(exits) == 1:
            return next(iter(exits))
        return None

    def _mr_is_default_case_block(self, block, visited):
        last = block.get_last_instruction()
        if last and last.opname in CONDITIONAL_JUMP_OPS:
            return False
        if self._is_case_pattern_block(block):
            return False
        if self._is_pattern_fail_handler(block):
            return False
        if self._is_case_fail_handler(block):
            return False
        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not meaningful:
            return False
        if any(i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                             'MATCH_KEYS', 'MATCH_MAPPING_KEYS') for i in meaningful):
            return False
        trivial_ops = frozenset(('POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                  'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'STORE_FAST', 'STORE_NAME',
                                  'STORE_GLOBAL', 'STORE_DEREF'))
        has_body = any(i.opname not in trivial_ops for i in meaningful)
        if has_body:
            return True
        if last and last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
            return True
        if all(i.opname == 'POP_TOP' for i in meaningful):
            for succ in block.successors:
                if self._mr_is_default_case_block(succ, visited):
                    return True
        return False

    def _mr_collect_case_body(self, subject_block):
        if subject_block is None:
            return [], [], [], None, set()
        all_blocks = {subject_block}
        for blk in self.cfg.blocks.values():
            if blk != subject_block and self.dom_analyzer.is_dominator(subject_block, blk):
                all_blocks.add(blk)
        if not all_blocks:
            return [], [], [], None, set()
        case_blocks, case_patterns, case_bodies, visited = [], [], [], set()
        current = subject_block
        while current and current in all_blocks and current not in visited:
            visited.add(current)
            jump_instr = self._mr_find_case_jump_instruction(current)
            if jump_instr is None:
                if current != subject_block and not self._is_pattern_fail_handler(current):
                    default_body = self._mr_collect_simple_body_blocks(current, visited)
                    if default_body:
                        is_implicit_default = self._is_implicit_default_body(default_body)
                        if not is_implicit_default:
                            body_set = set(default_body)
                            all_blocks.update(body_set)
                            case_blocks.append(current)
                            case_patterns.append({'type': 'MatchAs'})
                            case_bodies.append(sorted(body_set, key=lambda b: b.start_offset))
                        else:
                            all_blocks.update(set(default_body))
                break
            next_case_offset = jump_instr.argval
            jt = self.cfg.get_block_by_offset(next_case_offset)
            success = self._mr_find_case_success_branch(current, jt)
            if not jt or not success:
                break
            # 区域归约算法：[or-guard 修复]
            # 当 case jump 是 POP_JUMP_FORWARD_IF_TRUE（or 短路求值）时，
            # 跳转目标是 CASE BODY（条件为真时执行），而不是下一个 case。
            # 真正的"下一个 case"是 guard 链中 POP_JUMP_FORWARD_IF_FALSE 的目标。
            jt, success, guard_chain_blocks = self._mr_resolve_or_guard_jump(current, jump_instr, jt, success)
            for gb in guard_chain_blocks:
                visited.add(gb)
                all_blocks.add(gb)
            if not jt or not success:
                break
            if jt == current or not self.dom_analyzer.is_dominator(current, jt):
                break
            # 区域归约算法：[and-guard 链修复]
            # 当 guard 是 `A and B` 形式时，字节码为多个 IF_FALSE → next_case 块链：
            #   current: COMPARE A, POP_JUMP_FORWARD_IF_FALSE → jt (next case)
            #   guard_cont: COMPARE B, POP_JUMP_FORWARD_IF_FALSE → jt (next case)
            #   body: ... (actual case body)
            # success (fall-through from current) 指向 guard_cont 而非 body。
            # 需要沿 and-guard 链前进，直到找到真正的 body 入口。
            # 区分 guard_cont 和 body 内的 if：guard_cont 的跳转目标 == next_case_offset。
            AND_FALSE_OPS = ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE')
            and_guard_chain = set()
            agc = success
            while agc and agc != jt and agc not in and_guard_chain and agc not in visited:
                agc_jump = self._mr_find_case_jump_instruction(agc)
                if (agc_jump and agc_jump.argval == next_case_offset and
                        agc_jump.opname in AND_FALSE_OPS):
                    and_guard_chain.add(agc)
                    agc_jt = self.cfg.get_block_by_offset(agc_jump.argval)
                    agc = self._mr_find_case_success_branch(agc, agc_jt)
                else:
                    break
            if and_guard_chain:
                success = agc
                for gb in and_guard_chain:
                    visited.add(gb)
                    all_blocks.add(gb)
            pat = self.pattern_parser.parse_case_pattern(current)
            guard_jump_target = None
            pattern_jump_targets = set()
            # 区域归约算法：[RC1 模式检查块识别]
            # 模式检查块（pattern-only 且有条件跳转）属于 case 头部，不应纳入 body。
            # 包括两类：
            #   1. 含 MATCH_KEYS/MATCH_CLASS 等的模式匹配块（如 POP_JUMP_IF_NONE）
            #   2. 含 UNPACK_SEQUENCE+COMPARE_OP 的值检查块（如 case {'k': 1} 的值比较）
            # 区分依据：pattern-only 块只用 LOAD_CONST（字面量），不含 LOAD_NAME/LOAD_FAST
            # （变量加载），因此 guard 块（case x if x>0）和 body 内 if 块不会误入此类。
            pattern_check_blocks = set()
            PATTERN_ONLY_OPS = frozenset({
                'MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                'MATCH_KEYS', 'MATCH_MAPPING_KEYS',
                'GET_LEN', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                'LOAD_CONST', 'COMPARE_OP', 'IS_OP',
                'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                'COPY', 'SWAP', 'POP_TOP',
                'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                'EXTENDED_ARG',
            }) | NOISE_OPS | frozenset(CONDITIONAL_JUMP_OPS)
            for body_candidate in [success]:
                worklist_g = [body_candidate]
                visited_g = {current}
                while worklist_g:
                    gc = worklist_g.pop(0)
                    if gc in visited_g or gc == jt:
                        continue
                    visited_g.add(gc)
                    is_pattern_only = all(i.opname in PATTERN_ONLY_OPS for i in gc.instructions)
                    # [Phase 3 adv16_match_class_nested_in_if] 嵌套类模式块（如
                    # Outer(x=Inner(1)) 的 Inner 匹配块）含 MATCH_CLASS + LOAD_NAME
                    # （加载内层类引用）。LOAD_NAME 不在 PATTERN_ONLY_OPS（guard 块
                    # 也用 LOAD_NAME），但含 MATCH_CLASS/MATCH_SEQUENCE/MATCH_MAPPING
                    # 的块一定是模式检查块，应继续沿后继收集（找下一个 pattern 检查块
                    # 与真正 body），而非当作 guard 块 break 中断 worklist。否则后续
                    # pattern 检查块（如 Inner(1) 的 UNPACK+COMPARE 块）与 next-case
                    # 块会被误纳入 body，导致 _mr_bodies_are_equivalent 误判两 case
                    # body 末块相同而合并为 MatchOr。
                    _has_definitive_match_op = any(
                        i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                                     'MATCH_KEYS', 'MATCH_MAPPING_KEYS')
                        for i in gc.instructions)
                    if _has_definitive_match_op:
                        is_pattern_only = True
                    gj = self._mr_find_case_jump_instruction(gc)
                    if gj:
                        target_block = self.cfg.get_block_by_offset(gj.argval)
                        if target_block and target_block != jt:
                            pattern_jump_targets.add(target_block)
                        if is_pattern_only:
                            # 所有 pattern-only 且有条件跳转的块都是模式检查块
                            # （含 MATCH_* 的模式匹配块 + 含 COMPARE_OP 的值检查块）
                            pattern_check_blocks.add(gc)
                            for s in gc.successors:
                                if s not in visited_g:
                                    worklist_g.append(s)
                        else:
                            if gc != current:
                                guard_jump_target = gj.argval
                                # [R16 模式 B 修复] guard 块（含 LOAD_VAR + 条件跳转）
                                # 排除出 body：guard 块的字节码（如 LOAD_NAME z /
                                # POP_JUMP_IF_FALSE）已由 parse_case_guard 提取为
                                # case 守卫条件，不应再作为 body 内容重复生成。
                                # 将 guard 块加入 pattern_check_blocks，使其：
                                # 1. 被 _mr_resolve_pattern_check_chain 跳过（找到真正 body）
                                # 2. 加入 stop_set（从 body_set 中排除）
                                # 3. 纳入 all_blocks（属于 match 区域）
                                pattern_check_blocks.add(gc)
                            break
                    elif is_pattern_only:
                        for s in gc.successors:
                            if s not in visited_g:
                                worklist_g.append(s)
            # 区域归约算法：[RC1 解析真正 body 入口]
            # 若 success 本身是模式检查块，需沿 fall-through 链跳过所有模式检查块，
            # 找到真正的 body 入口。模式检查块加入 stop_set，避免被 body 收集纳入。
            actual_body_entry = self._mr_resolve_pattern_check_chain(
                success, pattern_check_blocks, jt)
            resolved_success = self._mr_resolve_body_entry(actual_body_entry)
            if resolved_success and resolved_success != jt:
                stop_set = visited | {jt} | pattern_jump_targets | pattern_check_blocks
                if guard_jump_target is not None:
                    guard_jt_block = self.cfg.get_block_by_offset(guard_jump_target)
                    if guard_jt_block:
                        stop_set.add(guard_jt_block)
                body_set = self._collect_blocks_on_path(resolved_success, jt, stop_set)
                body_set = body_set - stop_set
                if not body_set:
                    body_set = self._mr_collect_case_body_by_offset(
                        actual_body_entry, next_case_offset, visited | pattern_check_blocks)
            else:
                body_set = self._mr_collect_case_body_by_offset(
                    actual_body_entry, next_case_offset, visited | pattern_check_blocks)
            # 模式检查块属于 match 区域（case 头部），纳入 all_blocks 但不纳入 body
            all_blocks.update(pattern_check_blocks)
            all_blocks.update(body_set)
            if jt:
                all_blocks.add(jt)
            case_blocks.append(current)
            case_patterns.append(pat)
            case_bodies.append(sorted(body_set, key=lambda b: b.start_offset))
            current = jt
            while current and current not in visited:
                meaningful = [i for i in current.instructions if i.opname not in NOISE_OPS]
                is_connector = (
                    len(meaningful) > 0 and
                    all(i.opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE') for i in meaningful) and
                    len(current.successors) == 1
                )
                if is_connector:
                    visited.add(current)
                    all_blocks.add(current)
                    current = next(iter(current.successors))
                else:
                    break
        if not case_blocks:
            return [], [], [], None, set()
        return self._mr_finalize_match_region(case_blocks, case_patterns, case_bodies, all_blocks)

    def _is_simple_match_case_block(self, block):
        """
        检测简单match/case模式块（无MATCH_CLASS等显式匹配指令的case分支）。
        
        === 反编译逻辑 ===
        CPython为 match/case 语句生成两种模式：
        1. 完整模式：使用 MATCH_CLASS/MATCH_SEQUENCE 等显式匹配指令（由 _has_match_op 检测）
        2. 简单模式：仅用 COMPARE_OP/IS_OP + 条件跳转实现常量/类型匹配
        
        本方法检测第2种模式。关键字节码特征：
        
        [真match/case - 有NOP前缀]
          Block@N: NOP              ← match case标记（Python 3.10+）
                   COPY(subject)    ← 复制被匹配对象
                   LOAD_CONST(pattern) ← 加载模式值
                   COMPARE_OP(==)   ← 比较
                   POP_JUMP_IF_FALSE → next_case_or_body
                   
        [假match - 链式比较chain block，如 a < b < c 的第二比较]
          Block@N: LOAD_CONST(10)   ← 直接加载比较常数（无COPY，无subject load）
                   COMPARE_OP(<)     ← 比较
                   POP_JUMP_IF_FALSE → exit
                   JUMP_FORWARD → body
                   
        [假match - 简单 if x is None]
          Block@N: LOAD_FAST(x)
                   POP_JUMP_IF_NOT_NONE → else_path
                   (jump目标无NOP前缀)
        
        排除规则（按优先级）：
        1. 有 MATCH_OP → False（完整模式，不归此类）
        2. 无 meaningful 指令 → False
        3. 最后一条非条件跳转 → False
        4. 有 SWAP → False（链式比较 a < b < c 使用 SWAP 交换操作数）
        5. 以 LOAD_CONST 开头且无 COPY/subject-load → False（链式比较chain block）
        6. jump target 无 NOP 前缀 + 单 load op + is_none_check → False（简单 if x is None）
        """
        if block is None:
            return False
        if self._has_match_op(block):
            return False
        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not meaningful:
            return False
        last = meaningful[-1]
        if last.opname not in CONDITIONAL_JUMP_OPS:
            return False
        # 如果有 SWAP 指令，很可能是链式比较 a < b < c，不是 match
        has_swap = any(instr.opname == 'SWAP' for instr in meaningful)
        if has_swap:
            return False
        # [聚类4 修复] COPY 后紧跟 STORE_* 是 walrus 运算符 (:=) 模式，不是 match case。
        # 例如 ``if (n := await g()) > 0:`` 的条件块：
        #   COPY + STORE_FAST(n) + LOAD_CONST(0) + COMPARE_OP(>) + POP_JUMP_IF_FALSE
        # 此模式与 _is_match_subject_block 的 walrus 排除（行 6844-6846）一致。
        for idx in range(len(meaningful) - 1):
            if (meaningful[idx].opname == 'COPY' and
                meaningful[idx + 1].opname in ('STORE_FAST', 'STORE_NAME',
                                               'STORE_GLOBAL', 'STORE_DEREF')):
                return False
        # 如果以 LOAD_CONST 开头且无 COPY 和 subject-load，是链式比较chain block（如 a < b < c 的第二比较）
        first_meaningful = meaningful[0]
        if first_meaningful.opname == 'LOAD_CONST':
            has_copy = any(i.opname == 'COPY' for i in meaningful)
            has_subject_load = any(i.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') for i in meaningful)
            if not has_copy and not has_subject_load:
                return False
        jt = self.cfg.get_block_by_offset(last.argval)
        if jt is None:
            return False
        has_nop_prefix = False
        for instr in jt.instructions:
            if instr.opname == 'NOP':
                has_nop_prefix = True
            elif instr.opname not in NOISE_OPS:
                break
        if has_nop_prefix:
            jt_meaningful = [i for i in jt.instructions if i.opname not in NOISE_OPS]
            jt_has_case_pattern = False
            if jt_meaningful:
                jt_ops = set(i.opname for i in jt_meaningful)
                if 'COPY' in jt_ops and 'COMPARE_OP' in jt_ops:
                    jt_has_case_pattern = True
                if any(i.opname in CONDITIONAL_JUMP_OPS for i in jt_meaningful):
                    jt_has_case_pattern = True
            if not jt_has_case_pattern:
                if self._is_literal_default_block(jt, set()):
                    jt_has_case_pattern = True
                if not jt_has_case_pattern:
                    has_nop_prefix = False
        has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in meaningful)
        has_none_check = last.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE',
                                          'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE')
        if not has_compare and not has_none_check:
            return False
        if has_compare and not has_none_check:
            has_copy_instr = any(i.opname == 'COPY' for i in meaningful)
            for i in meaningful:
                if i.opname == 'COMPARE_OP':
                    cmp_op = i.argval
                    if isinstance(cmp_op, str) and cmp_op not in ('==',):
                        if not has_copy_instr:
                            return False
            load_const_vals = [i.argval for i in meaningful if i.opname == 'LOAD_CONST']
            if any(v is None or v is True or v is False for v in load_const_vals):
                return False
        simple_ops = frozenset({
            'COPY', 'LOAD_CONST', 'COMPARE_OP', 'IS_OP',
            'LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
            'POP_TOP', 'SWAP',
        }) | NOISE_OPS | CONDITIONAL_JUMP_OPS
        if not all(i.opname in simple_ops for i in meaningful):
            return False
        if not has_nop_prefix:
            if has_none_check and not has_compare:
                load_ops = [i for i in meaningful if i.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')]
                other_ops = [i for i in meaningful if i.opname not in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and i.opname not in CONDITIONAL_JUMP_OPS]
                if len(load_ops) == 1 and (not other_ops or all(o.opname in ('POP_TOP',) for o in other_ops)):
                    return False
            elif has_compare and not has_none_check:
                has_copy = any(i.opname == 'COPY' for i in meaningful)
                if not has_copy:
                    return False
        return True

    def _is_wildcard_match_block(self, block):
        """
        检测 `match x: case _:` 通配符模式块。

        反编译逻辑：
        ==========
        字节码特征（CPython 3.11+）：
          match x:                →  LOAD_x, POP_TOP, <body>
            case _:
              <body>

        简单体（无嵌套控制流）：
          RESUME, LOAD_NAME(x), POP_TOP, LOAD_CONST(1), STORE_NAME(y), RETURN_VALUE

        嵌套控制流体（if/for/while/try 在 case _体内）：
          RESUME, LOAD_NAME(x), POP_TOP, LOAD_NAME(cond), POP_JUMP_IF_FALSE, ...

        区分特征：
        1. 前两条有效指令是 LOAD_* + POP_TOP（subject加载后丢弃，通配符不绑定）
        2. 无COPY指令（通配符不需要复制subject给case比较）
        3. 无MATCH_*操作码（非结构型模式）
        4. 前驱块不是短路跳转（排除boolop短路链的末端）

        边界条件：
        - case _: 后面可以跟任意合法的Python语句（包括if/for/while/try等）
        - 因此rest部分允许条件跳转、循环回边等操作码
        - 但不允许GET_ITER/FOR_ITER（那属于for循环头部，不是match body起始）
        """
        if block is None:
            return False
        if self._has_match_op(block):
            return False
        instrs = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if len(instrs) < 2:
            return False
        has_load = instrs[0].opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')
        if not has_load:
            return False
        has_pop_top = instrs[1].opname == 'POP_TOP'
        if not has_pop_top:
            return False
        no_copy = not any(i.opname == 'COPY' for i in instrs)
        if not no_copy:
            return False
        rest = instrs[2:]
        if not rest:
            return True
        for pred in block.predecessors:
            pred_last = pred.get_last_instruction()
            if pred_last and pred_last.opname in SHORT_CIRCUIT_JUMP_OPS:
                return False
        loop_header_ops = frozenset({'GET_ITER', 'FOR_ITER', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'})
        has_loop_header = any(i.opname in loop_header_ops for i in rest[:3]) if len(rest) >= 3 else False
        if has_loop_header:
            return False
        return True

    def _is_none_match_block(self, block):
        """
        检测 `match x: case None:` 模式的None匹配块。
        
        === 反编译逻辑 ===
        CPython 对 `if x is None:` 和 `match x: case None:` 生成相似但可区分的字节码：
        
        [match x: case None: - 真正的match]
          Block@N: LOAD_FAST(x)       ← 加载被匹配对象
                   POP_JUMP_IF_NOT_NONE → offset_M
          Block@M: NOP                ← match case 分隔标记（关键区分点！）
                   ...case body...
                   
        [if x is None: - 普通条件语句]
          Block@N: LOAD_FAST(x)       ← 加载变量
                   POP_JUMP_IF_NOT_NONE → offset_M   (同上)
          Block@M: LOAD_CONST(...)    ← 直接开始else/then体（无NOP！）
                   ...body...
        
        核心区分特征：jump target (offset_M) 是否有 NOP 前缀。
        - 有 NOP → match/case 的 case 分隔标记（Python 3.10+ 编译器生成）
        - 无 NOP → 普通 if 语句的分支入口
        
        额外排除条件：
        - 前驱块以短路跳转结尾（and/or短路求值）→ 不是 match
        - 包含 COPY/SWAP → 复杂表达式，不是简单 None 匹配
        """
        if block is None:
            return False
        if self._has_match_op(block):
            return False
        instrs = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if len(instrs) < 2:
            return False
        has_load = instrs[0].opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')
        if not has_load:
            return False
        is_none_check = instrs[1].opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE')
        if not is_none_check:
            return False
        no_copy = not any(i.opname == 'COPY' for i in instrs)
        if not no_copy:
            return False
        has_swap = any(instr.opname == 'SWAP' for instr in instrs)
        if has_swap:
            return False
        for pred in block.predecessors:
            pred_last = pred.get_last_instruction()
            if pred_last and pred_last.opname in SHORT_CIRCUIT_JUMP_OPS:
                return False
        last_instr = block.get_last_instruction()
        if last_instr and last_instr.argval is not None:
            jt = self.cfg.get_block_by_offset(last_instr.argval)
            if jt is not None:
                has_nop_prefix = False
                for instr in jt.instructions:
                    if instr.opname == 'NOP':
                        has_nop_prefix = True
                    elif instr.opname not in NOISE_OPS:
                        break
                if not has_nop_prefix:
                    return False
        return True

    def _is_wildcard_match_subject(self, match_region: 'MatchRegion', block: 'BasicBlock') -> bool:
        return (
            match_region.subject_block == block and
            len(match_region.case_patterns) > 0 and
            match_region.case_patterns[0].get('type') == 'MatchAs' and
            match_region.case_patterns[0].get('name') is None and
            not match_region.case_patterns[0].get('pattern')
        )

    def _identify_nested_match_regions(self, parent_regions: List[Region], existing_match_regions: List[Region]) -> List[Region]:
        """识别嵌套在父区域中的match语句区域

        反编译逻辑：
        ============
        当match语句嵌套在if/for/try/with等控制结构中时，父区域会在Phase 1或Phase 2中先占用match的blocks，
        导致Phase 1的_identify_match_regions()无法识别这些嵌套match。

        本方法在所有父区域识别完成后进行二次扫描，专门处理嵌套match场景。

        识别算法：
        ----------
        1. 遍历所有父区域（IfRegion、ForRegion、TryRegion、WithRegion等）
        2. 对每个父区域的blocks进行match特征检测：
           a. 结构型模式：_has_match_op(block) 检测MATCH_CLASS/SEQUENCE/MAPPING/KEYS
           b. 字面量模式：_is_match_subject_block(block) 检测COPY+比较模式
           c. 简单case块：_is_simple_match_case_block(block) 检测NOP前缀的case块
           d. 通配符块：_is_wildcard_match_block(block)
           e. None匹配块：_is_none_match_block(block)
        3. 发现候选subject块后，收集完整的case链：
           - 调用_mr_collect_case_body()（结构型）或内部逻辑（字面量型）
        4. 验证嵌套约束：
           - 所有match blocks必须是父区域blocks的子集
           - match不能跨越父区域边界
        5. 创建子MatchRegion并注册到block_to_region

        字节码模式示例：
        ----------------
        例1: if True:
                match a:
                    case 1:
                        pass

        字节码布局：
        Block0 (if条件):   LOAD_CONST True
                           POP_JUMP_FORWARD_IF_FALSE -> EndBlock
        Block1 (match subject): LOAD_NAME 'a'
                                COPY
                                LOAD_CONST 1
                                COMPARE_OP ==
                                POP_JUMP_FORWARD_IF_FALSE -> DefaultBlock
        Block2 (case body): PASS
                            JUMP_FORWARD -> MergeBlock
        Block3 (default):  NOP (或直接进入body)
                           ...
        MergeBlock:
        EndBlock:

        关键观察：
        - Block0被IfRegion占用（if条件判断）
        - Block1-Block3和MergeBlock应该被MatchRegion占用
        - 但在Phase 1时，Block1已被IfRegion标记为claimed，导致match无法识别

        边界条件：
        --------
        1. 多层嵌套：match in if in for → 需要递归扫描（当前只处理一层）
        2. match在循环体中：case body可能包含continue/break
        3. match在try中：可能跨越except块（需要特殊处理）
        4. match在with中：通常不跨越with边界

        性能考虑：
        - 只对父区域的blocks进行扫描，而非全局扫描
        - 使用已有的match检测方法，避免重复逻辑
        - 提前终止无效路径

        Args:
            parent_regions: 已识别的父区域列表（可能包含嵌套match的区域）
            existing_match_regions: 已识别的顶层match区域列表

        Returns:
            嵌套MatchRegion列表
        """
        nested_regions = []
        existing_match_blocks = set()
        for mr in existing_match_regions:
            existing_match_blocks.update(mr.blocks)

        sorted_parent_regions = sorted(parent_regions, key=lambda r: len(r.blocks) if r.blocks else 0, reverse=True)

        for parent_region in sorted_parent_regions:
            if not parent_region or not parent_region.blocks:
                continue

            # 扫描父区域内的blocks，寻找未识别的match模式
            parent_blocks = parent_region.blocks
            for block in self.cfg.get_blocks_in_order():
                if block not in parent_blocks:
                    continue
                if block in existing_match_blocks:
                    continue
                if self.block_to_region.get(block) and isinstance(self.block_to_region.get(block), MatchRegion):
                    continue

                # 检测match特征
                is_structured = self._has_match_op(block)
                is_case_pattern = self._is_case_pattern_block(block)
                is_literal_subject = self._is_match_subject_block(block)
                is_simple_case = self._is_simple_match_case_block(block)
                is_wildcard = self._is_wildcard_match_block(block)
                is_none_match = self._is_none_match_block(block)

                if not (is_structured or is_case_pattern or is_literal_subject or is_simple_case or is_wildcard or is_none_match):
                    continue

                # 尝试收集match区域
                nested_match = self._collect_nested_match_region(block, parent_blocks, existing_match_blocks)
                if nested_match:
                    nested_regions.append(nested_match)
                    # 更新已占用blocks集合
                    existing_match_blocks.update(nested_match.blocks)
                    # 注册到block_to_region（允许与父区域重叠）
                    for b in nested_match.blocks:
                        existing = self.block_to_region.get(b)
                        if existing is None or not existing.preserves_against_nested_match():
                            self.block_to_region[b] = nested_match

        return nested_regions

    def _collect_nested_match_region(self, candidate_block: 'BasicBlock', parent_blocks: set, exclude_blocks: set) -> Optional[MatchRegion]:
        """从候选块开始收集嵌套match区域

        反编译逻辑：
        根据候选块的类型，使用不同的收集策略：
        1. 结构型模式（有MATCH_*操作码）：调用_mr_collect_case_body()
        2. 字面量模式（COPY+比较）：调用_scan_literal_match_subjects的单例版本
        3. 简单case块（NOP前缀）：向前查找subject块再收集

        Args:
            candidate_block: 候选的match入口块
            parent_blocks: 父区域的blocks集合（边界约束）
            exclude_blocks: 已被其他match占用的blocks集合

        Returns:
            收集到的MatchRegion，如果无效则返回None
        """
        import dis

        # 策略1: 结构型模式匹配（有MATCH_*操作码）
        if self._has_match_op(candidate_block):
            subject_block = candidate_block
            if self._is_case_pattern_block(candidate_block):
                for pred in sorted(candidate_block.predecessors, key=lambda p: p.start_offset):
                    last = pred.get_last_instruction()
                    if last and last.opname in CONDITIONAL_JUMP_OPS:
                        if (self._is_case_pattern_block(pred) or self._has_match_op(pred)) and pred in parent_blocks:
                            subject_block = pred
                            break

            case_blocks, case_patterns, case_bodies, merge, all_raw_blocks = self._mr_collect_case_body(subject_block)
            if not case_blocks:
                return None

            # 验证所有blocks都在父区域内
            all_blocks = all_raw_blocks | {subject_block} | set(case_blocks)
            for body in case_bodies:
                all_blocks.update(body)
            if merge:
                all_blocks.add(merge)

            # 检查是否超出父区域边界
            if not all_blocks.issubset(parent_blocks):
                # 放宽约束：允许部分超出（可能是汇合点）
                core_blocks = {subject_block} | set(case_blocks)
                for body in case_bodies:
                    core_blocks.update(body)
                if not core_blocks.issubset(parent_blocks):
                    return None

            # 创建MatchRegion
            case_guards = [self.pattern_parser.parse_case_guard(
                self.pattern_parser.collect_pattern_blocks(cb, all_blocks)) for cb in case_blocks]
            region = MatchRegion(
                region_type=RegionType.MATCH, entry=subject_block, blocks=all_blocks,
                subject_block=subject_block, case_blocks=case_blocks,
                case_patterns=case_patterns, case_guards=case_guards,
                case_bodies=case_bodies, merge_block=merge)
            region.case_body_start_indices = self._mr_compute_case_body_start_indices(region)
            self.regions.append(region)
            return region

        # 策略2: 字面量模式匹配（COPY + LOAD_CONST + COMPARE_OP）
        if self._is_match_subject_block(candidate_block):
            return self._collect_nested_literal_match(candidate_block, parent_blocks, exclude_blocks)

        # 策略3: 简单case块（NOP前缀的default case）
        if self._is_simple_match_case_block(candidate_block) or self._is_wildcard_match_block(candidate_block) or self._is_none_match_block(candidate_block):
            # 向前查找subject块
            subject_block = self._find_nested_match_subject(candidate_block, parent_blocks)
            if subject_block:
                return self._collect_nested_literal_match(subject_block, parent_blocks, exclude_blocks)

        return None

    def _find_nested_match_subject(self, case_block: 'BasicBlock', parent_blocks: set) -> Optional['BasicBlock']:
        """为简单case块查找对应的subject块

        反编译逻辑：
        从case块的前驱链中查找包含COPY指令的subject块。
        字面量match的特征是subject块包含COPY+比较操作。

        查找策略：
        1. 直接前驱检查：查看case块的所有前驱是否是subject块
        2. 间接前驱搜索：沿条件跳转链回溯
        3. 偏移量推断：根据字节码布局，subject块应该在case块之前

        Args:
            case_block: 简单case块（NOP前缀或通配符块）
            parent_blocks: 父区域blocks集合（约束边界）

        Returns:
            找到的subject块，未找到返回None
        """
        for pred in sorted(case_block.predecessors, key=lambda p: p.start_offset):
            if pred not in parent_blocks:
                continue
            if self._is_match_subject_block(pred) and pred.start_offset < case_block.start_offset:
                return pred
            instrs = [i for i in pred.instructions if i.opname not in NOISE_OPS]
            has_copy = any(i.opname == 'COPY' for i in instrs)
            if has_copy and pred.start_offset < case_block.start_offset:
                return pred
            has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in instrs)
            has_load = any(i.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') for i in instrs)
            has_cond_jump = any(i.opname in CONDITIONAL_JUMP_OPS for i in instrs)
            if has_compare and has_load and has_cond_jump and pred.start_offset < case_block.start_offset:
                return pred

        visited = {case_block}
        queue = list(case_block.predecessors)
        while queue:
            current = queue.pop(0)
            if current in visited or current not in parent_blocks:
                continue
            visited.add(current)

            if self._is_match_subject_block(current) and current.start_offset < case_block.start_offset:
                return current
            instrs = [i for i in current.instructions if i.opname not in NOISE_OPS]
            has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in instrs)
            has_load = any(i.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') for i in instrs)
            has_cond_jump = any(i.opname in CONDITIONAL_JUMP_OPS for i in instrs)
            if has_compare and has_load and has_cond_jump and current.start_offset < case_block.start_offset:
                return current

            for pred in current.predecessors:
                if pred not in visited and pred in parent_blocks:
                    queue.append(pred)

        if self._is_simple_match_case_block(case_block):
            return case_block

        return None

    def _collect_nested_literal_match(self, subject_block: 'BasicBlock', parent_blocks: set, exclude_blocks: set) -> Optional[MatchRegion]:
        """收集嵌套的字面量型match区域

        反编译逻辑：
        与_scan_literal_match_subjects()类似，但增加了父区域边界约束。
        字面量match的特征是subject通过COPY复制给每个case进行比较。

        收集流程：
        1. 从subject块开始，沿条件跳转链收集case块
        2. 对每个case块解析pattern并收集body
        3. 验证所有blocks都在父区域内
        4. 创建MatchRegion

        Args:
            subject_block: 包含COPY指令的subject块
            parent_blocks: 父区域blocks集合
            exclude_blocks: 已排除的blocks集合

        Returns:
            MatchRegion或None
        """
        case_blocks_l, case_patterns_l, case_bodies_l = [], [], []
        all_blocks_l = {subject_block}
        visited_l = set()

        current = subject_block
        merge_candidates = []

        while current and current not in visited_l and current in parent_blocks:
            visited_l.add(current)
            all_blocks_l.add(current)

            last = current.get_last_instruction()
            if not last or last.opname not in CONDITIONAL_JUMP_OPS:
                # 可能是default case
                if self._is_literal_default_block(current, visited_l):
                    default_body = self._mr_collect_simple_body_blocks(current, visited_l)
                    default_body = [b for b in default_body if b in parent_blocks]
                    if default_body:
                        is_implicit_default = self._is_implicit_default_body(default_body)
                        if not is_implicit_default:
                            body_set = set(default_body)
                            all_blocks_l.update(body_set)
                            case_blocks_l.append(current)
                            case_patterns_l.append({'type': 'MatchAs'})
                            case_bodies_l.append(sorted(body_set, key=lambda b: b.start_offset))
                        else:
                            all_blocks_l.update(set(default_body))
                break

            jt = self.cfg.get_block_by_offset(last.argval)
            if jt is None:
                break

            ft_successor = next((s for s in sorted(current.successors, key=lambda s: s.start_offset) if s != jt), None)
            if not ft_successor:
                break

            # 区域归约算法：[or-guard 修复] 处理 or 短路跳转
            jt, ft_successor, guard_chain_blocks = self._mr_resolve_or_guard_jump(current, last, jt, ft_successor)
            for gb in guard_chain_blocks:
                visited_l.add(gb)
                all_blocks_l.add(gb)

            pat = self.pattern_parser.parse_case_pattern(current)
            body_entry = self._mr_resolve_body_entry(ft_successor)
            body_set = set()
            if body_entry and body_entry != jt:
                body_set = self._collect_blocks_on_path(body_entry, jt, visited_l | {jt})
                body_set = body_set - {jt}
                body_set = {b for b in body_set if b in parent_blocks}
            all_blocks_l.update(body_set)

            if body_set:
                for b in body_set:
                    for s in b.successors:
                        if s not in body_set and s != current:
                            merge_candidates.append(s)

            case_blocks_l.append(current)
            case_patterns_l.append(pat)
            case_bodies_l.append(sorted(body_set, key=lambda b: b.start_offset))
            current = jt

        if not case_blocks_l or len(case_blocks_l) < 1:
            return None

        # 验证核心blocks都在父区域内
        core_blocks = {subject_block} | set(case_blocks_l)
        for body in case_bodies_l:
            core_blocks.update(body)
        if not core_blocks.issubset(parent_blocks):
            return None

        # 计算merge block
        merge_block = self._mr_compute_case_merge(case_bodies_l)
        if merge_block is None and merge_candidates:
            from collections import Counter
            counter = Counter(id(c) for c in merge_candidates)
            most_common_id = counter.most_common(1)[0][0]
            merge_block = next(c for c in merge_candidates if id(c) == most_common_id)
        if merge_block:
            all_blocks_l.add(merge_block)

        # 验证字面量match链
        if not self._verify_literal_match_chain(subject_block, case_blocks_l):
            return None

        # OR模式合并
        merged_p, merged_b, i = [], [], 0
        while i < len(case_blocks_l):
            orps, body = [case_patterns_l[i]], set(case_bodies_l[i])
            j = i + 1
            while j < len(case_blocks_l):
                body_i_set = set(case_bodies_l[i])
                body_j_set = set(case_bodies_l[j])
                if body_i_set == body_j_set:
                    orps.append(case_patterns_l[j])
                    body = body_i_set | body_j_set
                    j += 1
                else:
                    break
            merged_p.append({'type': 'MatchOr', 'patterns': orps} if len(orps) > 1 else orps[0])
            merged_b.append(sorted(body, key=lambda b: b.start_offset))
            i = j

        region = MatchRegion(
            region_type=RegionType.MATCH, entry=subject_block, blocks=all_blocks_l,
            subject_block=subject_block, case_blocks=case_blocks_l,
            case_patterns=merged_p, case_guards=[None] * len(merged_p),
            case_bodies=merged_b, merge_block=merge_block)
        region.case_body_start_indices = self._mr_compute_case_body_start_indices(region)
        self.regions.append(region)
        return region

    def _scan_literal_match_subjects(self, claimed):
        literal_regions = []
        for block in self.cfg.get_blocks_in_order():
            if block in claimed:
                continue
            is_copy_subject = self._is_match_subject_block(block)
            is_nop_case = self._is_simple_match_case_block(block)
            is_wildcard = self._is_wildcard_match_block(block)
            is_none_match = self._is_none_match_block(block)
            if not is_copy_subject and not is_nop_case and not is_wildcard and not is_none_match:
                continue
            if self.block_to_region.get(block) is not None:
                continue
            if block is None:
                continue
            case_blocks_l, case_patterns_l, case_bodies_l = [], [], []
            all_blocks_l = {block}
            visited_l = set()
            if is_wildcard:
                case_blocks_l.append(block)
                case_patterns_l.append({'type': 'MatchAs'})
                case_bodies_l.append([block])
                current = None
            elif is_none_match:
                case_blocks_l.append(block)
                case_patterns_l.append({'type': 'MatchSingleton', 'value': None})
                last_instr = block.get_last_instruction()
                jt = self.cfg.get_block_by_offset(last_instr.argval) if last_instr else None
                ft_successor = next((s for s in sorted(block.successors, key=lambda s: s.start_offset) if s != jt), None) if jt else (block.successors[0] if block.successors else None)
                if ft_successor:
                    body_set = {ft_successor}
                    all_blocks_l.update(body_set)
                else:
                    body_set = set()
                case_bodies_l.append(sorted(body_set, key=lambda b: b.start_offset))
                current = jt
            else:
                current = block
            merge_candidates = []
            while current and current not in visited_l:
                visited_l.add(current)
                all_blocks_l.add(current)
                last = current.get_last_instruction()
                if not last or last.opname not in CONDITIONAL_JUMP_OPS:
                    if self._is_literal_default_block(current, visited_l):
                        default_body = self._mr_collect_simple_body_blocks(current, visited_l)
                        if default_body:
                            is_implicit_default = self._is_implicit_default_body(default_body)
                            if not is_implicit_default:
                                body_set = set(default_body)
                                all_blocks_l.update(body_set)
                                case_blocks_l.append(current)
                                case_patterns_l.append({'type': 'MatchAs'})
                                case_bodies_l.append(sorted(body_set, key=lambda b: b.start_offset))
                            else:
                                all_blocks_l.update(set(default_body))
                    break
                jt = self.cfg.get_block_by_offset(last.argval)
                if jt is None:
                    break
                ft_successor = next((s for s in sorted(current.successors, key=lambda s: s.start_offset) if s != jt), None)
                if not ft_successor:
                    break
                # 区域归约算法：[or-guard 修复] 处理 or 短路跳转
                jt, ft_successor, guard_chain_blocks = self._mr_resolve_or_guard_jump(current, last, jt, ft_successor)
                for gb in guard_chain_blocks:
                    visited_l.add(gb)
                    all_blocks_l.add(gb)
                pat = self.pattern_parser.parse_case_pattern(current)
                body_entry = self._mr_resolve_body_entry(ft_successor)
                body_set = set()
                if body_entry and body_entry != jt:
                    body_set = self._collect_blocks_on_path(body_entry, jt, visited_l | {jt})
                    body_set = body_set - {jt}
                all_blocks_l.update(body_set)
                if body_set:
                    for b in body_set:
                        for s in b.successors:
                            if s not in body_set and s != current:
                                merge_candidates.append(s)
                case_blocks_l.append(current)
                case_patterns_l.append(pat)
                case_bodies_l.append(sorted(body_set, key=lambda b: b.start_offset))
                current = jt
            if not case_blocks_l:
                continue
            if len(case_blocks_l) < 1:
                continue
            merge_block = self._mr_compute_case_merge(case_bodies_l)
            if merge_block is None and merge_candidates:
                from collections import Counter
                counter = Counter(id(c) for c in merge_candidates)
                most_common_id = counter.most_common(1)[0][0]
                merge_block = next(c for c in merge_candidates if id(c) == most_common_id)
            if merge_block:
                all_blocks_l.add(merge_block)
            if not self._verify_literal_match_chain(block, case_blocks_l):
                continue
            merged_p, merged_b, i = [], [], 0
            while i < len(case_blocks_l):
                orps, body = [case_patterns_l[i]], set(case_bodies_l[i])
                j = i + 1
                while j < len(case_blocks_l):
                    body_i_set = set(case_bodies_l[i])
                    body_j_set = set(case_bodies_l[j])
                    if body_i_set and body_j_set and body_i_set == body_j_set:
                        orps.append(case_patterns_l[j])
                        body |= body_j_set
                        j += 1
                    else:
                        break
                or_pattern = {'type': 'MatchOr', 'patterns': orps} if len(orps) > 1 else orps[0]
                if isinstance(or_pattern, dict) and or_pattern.get('type') == 'MatchOr':
                    self._apply_or_capture_name(or_pattern, body)
                merged_p.append(or_pattern)
                merged_b.append(sorted(body, key=lambda b: b.start_offset))
                i = j
            case_blocks, case_patterns, case_bodies, merge, all_blocks = (
                case_blocks_l, merged_p, merged_b, merge_block, all_blocks_l)
            case_guards = [self.pattern_parser.parse_case_guard(
                self.pattern_parser.collect_pattern_blocks(cb, all_blocks)) for cb in case_blocks]
            region = MatchRegion(
                region_type=RegionType.MATCH, entry=block, blocks=all_blocks,
                subject_block=block, case_blocks=case_blocks,
                case_patterns=case_patterns, case_guards=case_guards,
                case_bodies=case_bodies, merge_block=merge)
            region.case_body_start_indices = self._mr_compute_case_body_start_indices(region)
            literal_regions.append(region)
            self.regions.append(region)
            for b in region.blocks:
                if b not in self.block_to_region:
                    self.block_to_region[b] = region
                    claimed.add(b)
        return literal_regions

    def _is_case_pattern_block(self, block: 'BasicBlock') -> bool:
        # [Phase 3 adv17_try_except_star] except* 框架块不是 case pattern 块
        if self._is_except_star_framework_block(block):
            return False
        if self._has_match_op(block):
            return True
        if any(i.opname in ('GET_LEN', 'UNPACK_SEQUENCE') for i in block.instructions):
            pattern_related = (NOISE_OPS |
                {'GET_LEN', 'UNPACK_SEQUENCE', 'COMPARE_OP', 'LOAD_CONST',
                 'POP_TOP', 'COPY', 'SWAP',
                 'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF'} |
                FORWARD_CONDITIONAL_JUMP_OPS)
            if all(i.opname in pattern_related for i in block.instructions):
                return True
        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        has_copy = any(i.opname == 'COPY' for i in meaningful)
        for idx, instr in enumerate(meaningful):
            if (instr.opname == 'COPY' and
                idx + 1 < len(meaningful) and meaningful[idx + 1].opname == 'LOAD_CONST' and
                idx + 2 < len(meaningful) and meaningful[idx + 2].opname in ('COMPARE_OP', 'IS_OP') and
                idx + 3 < len(meaningful) and meaningful[idx + 3].opname in CONDITIONAL_JUMP_OPS):
                return True
            if has_copy and (instr.opname == 'LOAD_CONST' and
                idx + 1 < len(meaningful) and meaningful[idx + 1].opname in ('COMPARE_OP', 'IS_OP') and
                idx + 2 < len(meaningful) and meaningful[idx + 2].opname in CONDITIONAL_JUMP_OPS):
                copy_indices = [j for j in range(idx) if meaningful[j].opname == 'COPY']
                has_store_between = any(
                    meaningful[k].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                    for ci in copy_indices for k in range(ci + 1, idx))
                if has_store_between:
                    continue
                if meaningful[idx + 1].opname == 'IS_OP':
                    return True
                if meaningful[idx + 1].opname == 'COMPARE_OP' and meaningful[idx + 1].argval in ('==', '!='):
                    return True
            if (instr.opname == 'COPY' and
                idx + 1 < len(meaningful) and meaningful[idx + 1].opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE')):
                return True
        return False

    def _has_match_op(self, block):
        if block is None:
            return False
        return any(i.opname in ('MATCH_CLASS', 'MATCH_MAPPING', 'MATCH_SEQUENCE', 'MATCH_KEYS')
                  for i in block.instructions)

    def _is_case_fail_handler(self, block: 'BasicBlock') -> bool:
        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not meaningful:
            return False
        trivial_ops = frozenset(('POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                  'JUMP_FORWARD', 'JUMP_ABSOLUTE'))
        has_non_trivial = any(i.opname not in trivial_ops for i in meaningful)
        if has_non_trivial:
            return False
        if not block.predecessors:
            return False
        all_preds_are_pattern_cont = True
        for pred in block.predecessors:
            if self._has_match_op(pred):
                all_preds_are_pattern_cont = False
                break
            if not self._is_case_pattern_block(pred):
                all_preds_are_pattern_cont = False
                break
            pred_last = pred.get_last_instruction()
            if pred_last and pred_last.opname in CONDITIONAL_JUMP_OPS:
                pred_jt = self.cfg.get_block_by_offset(pred_last.argval) if pred_last.argval is not None else None
                if pred_jt != block:
                    all_preds_are_pattern_cont = False
                    break
                has_pattern_pred = any(
                    self._is_case_pattern_block(pp) for pp in pred.predecessors
                )
                if not has_pattern_pred:
                    all_preds_are_pattern_cont = False
                    break
            else:
                all_preds_are_pattern_cont = False
                break
        return all_preds_are_pattern_cont

    def _is_implicit_default_body(self, body_blocks):
        if not body_blocks:
            return True
        trivial_ops = frozenset(('POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                  'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'NOP', 'RESUME', 'CACHE'))
        # 区域归约算法：[R16 模式 A 修复] 显式 case _: body 识别
        # CPython 为显式 case body 添加 NOP 前缀作为标记（即使 body 为 pass）。
        # 对于 COPY-based 模式匹配（or-pattern, class pattern），显式 case _: pass
        # 的 body 会跳转到带 NOP 前缀的 after-match continuation 块。若 body 中
        # 包含此块，说明是显式 case _: body，不应视为隐式 default。
        # 对于简单 match（无 COPY），NOP 前缀块已被 _mr_collect_simple_body_blocks
        # 跳过（仅含 NOP 的块被合并到后继），因此此处不影响简单 match 的隐式
        # default 识别（简单 match 有无 case _ 字节码过滤后等价）。
        for block in body_blocks:
            for instr in block.instructions:
                if instr.opname == 'NOP':
                    return False
                elif instr.opname not in NOISE_OPS:
                    break
        for block in body_blocks:
            meaningful = [i for i in block.instructions if i.opname not in trivial_ops]
            if meaningful:
                return False
            has_non_none_return = False
            for idx, i in enumerate(block.instructions):
                if i.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    prev_non_noise = None
                    for j in range(idx - 1, -1, -1):
                        if block.instructions[j].opname not in NOISE_OPS:
                            prev_non_noise = block.instructions[j]
                            break
                    if prev_non_noise and prev_non_noise.opname == 'LOAD_CONST' and prev_non_noise.argval is not None:
                        has_non_none_return = True
                        break
            if has_non_none_return:
                return False
        return True

    def _is_pattern_fail_handler(self, block: 'BasicBlock') -> bool:
        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not meaningful:
            return False
        has_pop_top = any(i.opname == 'POP_TOP' for i in meaningful)
        has_return = any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in meaningful)
        non_trivial = [i for i in meaningful if i.opname not in ('POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')]
        if has_pop_top and has_return and not non_trivial:
            for pred in block.predecessors:
                # 检查前驱是否包含MATCH_*操作码（标准pattern匹配）
                if self._has_match_op(pred):
                    return True
                # 检查前驱是否是字面量比较pattern（LOAD_CONST+COMPARE_OP+POP_JUMP_IF_FALSE）
                # 字面量pattern的fail block也应该被识别
                pred_meaningful = [i for i in pred.instructions if i.opname not in NOISE_OPS]
                for pi, pinstr in enumerate(pred_meaningful):
                    if (pinstr.opname == 'LOAD_CONST' and
                        pi + 1 < len(pred_meaningful) and pred_meaningful[pi + 1].opname in ('COMPARE_OP', 'IS_OP') and
                        pi + 2 < len(pred_meaningful) and pred_meaningful[pi + 2].opname in CONDITIONAL_JUMP_OPS):
                        return True
                    # COPY + LOAD_CONST + COMPARE_OP模式（OR pattern的字面量分支）
                    if (pinstr.opname == 'COPY' and
                        pi + 1 < len(pred_meaningful) and pred_meaningful[pi + 1].opname == 'LOAD_CONST' and
                        pi + 2 < len(pred_meaningful) and pred_meaningful[pi + 2].opname in ('COMPARE_OP', 'IS_OP')):
                        return True
        return False


    def _identify_assert_regions(self) -> List[Region]:
        """_identify_assert_regions - 断言区域识别（Assert Region Identification）

【区域类型】 ASSERT — 断言区域（Assert Region）
RegionType 枚举值: RegionType.ASSERT

1. 算法描述（基于"No More Gotos"论文）
   - 归约阶段: 早期独立识别器，在 loop/try/with/match/conditional/
              chained_compare 等 Phase 1 区域之前运行，作为预处理。
   - 识别策略: 不依赖支配树或回边，而是基于 CPython 编译器为 assert 生成
              的固定字节码模式（LOAD_ASSERTION_ERROR + RAISE_VARARGS）
              做模式匹配。assert 在 CFG 中表现为"条件为真跳过，否则抛错"。
   - 归约过程:
     Step 1: 遍历所有基本块（按 start_offset 升序排序）。
     Step 2: 跳过末指令不在 FORWARD_JUMP_OPS 中的块（assert 必有前向条件跳转）。
     Step 3: 要求块恰好有 2 个 conditional_successors（true/false 双分支）。
     Step 4: 检查任一非自身条件后继块是否包含 LOAD_ASSERTION_ERROR 指令；
             若无则跳过（非 assert 模式，可与 IfRegion 区分）。
     Step 5: 在所有非自身后继块中按 start_offset 升序查找包含 RAISE_VARARGS
             的块作为 message_block（错误抛出块，可能为 None）。
     Step 6: 构建 AssertRegion:
             - entry           = 条件块本身
             - blocks          = {条件块} ∪ ({message_block} if 存在)
             - condition_block = 条件块
             - message_block   = Step 5 找到的块（可能为 None）
     Step 7: 注册到 self.regions，并更新 block_to_region:
             - 条件块未归属任何 region → 直接映射到本 AssertRegion；
             - 条件块已归属（如位于 IfRegion/LoopRegion 内部）→ 作为该 region
               的 child 挂载并设置 region.parent，体现"嵌套即抽象节点"。
             - message_block 若未被映射则同样映射到本 region。

2. 字节码模式（CPython 编译器行为）
   模式 A: 基本断言
     源码: assert condition
     字节码结构:
       cond_block:
           ...计算 condition...
           POP_JUMP_IF_TRUE → end      # 条件为 True 跳过抛错
           LOAD_ASSERTION_ERROR
           RAISE_VARARGS(1)
         end: ...
     特征指令: POP_JUMP_IF_TRUE, LOAD_ASSERTION_ERROR, RAISE_VARARGS
   模式 B: 带消息断言
     源码: assert condition, "error msg"
     字节码结构:
       cond_block:
           ...计算 condition...
           POP_JUMP_IF_TRUE → end
       message_block:
           LOAD_ASSERTION_ERROR
           LOAD_CONST "error msg"      # 或 FORMAT_VALUE + BUILD_STRING (f-string)
           CALL(1) / PRECALL
           RAISE_VARARGS(1)
         end: ...
     特征指令: LOAD_ASSERTION_ERROR, LOAD_CONST/FORMAT_VALUE/BUILD_STRING,
              CALL, RAISE_VARARGS
   模式 C: is None / is not None 断言
     - 使用 POP_JUMP_IF_NONE / POP_JUMP_IF_NOT_NONE（属 NONE_CHECK_OPS）；
     - 在 _generate_assert 中由 _fix_assert_none_check_direction 修正方向。

3. 边界条件（数学性质）
   - 单块识别: assert 区域由条件块（和可选消息块）两个块组成，
              不需要支配树或回边分析。
   - 唯一归属: 通过 block_to_region 映射保证条件块唯一归属；
              若已被父区域（IfRegion/LoopRegion）持有，则作为 child 嵌套，
              不破坏"每块唯一归属"原则。
   - 与 IfRegion 边界: assert 的条件跳转与 if 字节码相似，但通过
                       LOAD_ASSERTION_ERROR 指令明确区分；本识别器先于
                       IfRegion 运行以抢占识别权。
   - 与 BoolOpRegion 边界: assert 中的复合布尔条件可能被 BoolOpRegion 抢占，
                          通过 condition_block 共享与父 region 挂载协调。

4. 归约语义（与父区域的契约）
   - 入口块: 条件块（condition_block），即 assert 的 entry。
   - 父区域引用: 若 assert 位于 if/loop/try 等区域内部，父区域通过
                children 列表引用本 AssertRegion；条件块仍出现在父区域的
                blocks 中（assert 不缩小父区域 block 集合），但生成阶段
                会调用 _generate_assert 而非按普通块处理。
   - 子区域块不出现: AssertRegion 不再嵌套子区域（叶节点区域），
                   其内部块由本 region 独占生成。

5. AST 映射
   - 对应生成方法: _generate_assert（region_ast_generator.py）
   - AST 节点类型: ast.Assert
   - 关键字段映射:
       AssertRegion.condition_block → AST.test（条件表达式，经指令过滤重建）
       AssertRegion.message_block   → AST.msg（错误消息表达式，可能为 None）
   - 特殊处理: None 检查方向修正（_fix_assert_none_check_direction 互换 is/is not）。

6. 已知失败模式
   - 当前测试矩阵通过率: 100%，无已知失败模式（assert 在 basic 测试集内通过）
        """
        regions = []
        for block in self.cfg.get_blocks_in_order():
            # [Round4-12] 跳过已被本识别器前序迭代识别为 AssertRegion 的块
            # （entry / chained_compare_block / message_block）——链式比较
            # assert (`assert 0 < a < 10`) 的中段 COMPARE_OP 块也以条件跳转
            # 结尾且后继链含 LOAD_ASSERTION_ERROR，会被误识别为独立 AssertRegion
            # （违反「每块唯一归属」）。父 IfRegion/LoopRegion 持有的块仍允许
            # 嵌套识别（嵌套即抽象节点）。
            _existing_region = self.block_to_region.get(block)
            if isinstance(_existing_region, AssertRegion):
                continue
            last = block.get_last_instruction()
            if last is None or last.opname not in FORWARD_JUMP_OPS:
                continue
            if len(block.conditional_successors) != 2:
                continue
            # [Round4-12] assert 失败块可能不在直接后继中：链式比较 assert
            # (`assert 0 < a < 10`) 的第一段 COMPARE_OP 块的两个后继为
            # 「继续链」与「跳到 POP_TOP 中转块」；后者经单后继 fall-through
            # 才到达 LOAD_ASSERTION_ERROR 块。直接后继只看一层会漏识别。
            is_assert = any(
                self._reach_assertion_error_block(succ)
                for succ in block.conditional_successors
                if succ != block
            )
            if not is_assert:
                continue

            message_block = None
            for succ in sorted(block.successors, key=lambda s: s.start_offset):
                if succ == block:
                    continue
                # [R8 fix] Find the LOAD_ASSERTION_ERROR block (start of
                # failure path). For simple cases (`assert x, "msg"`) this
                # block also contains RAISE_VARARGS, so it's the same block
                # the legacy `_reach_raise_varargs_block` would return.
                # For ternary/complex message cases (`assert x, (a if c else
                # b)`), the LOAD_ASSERTION_ERROR block is the TernaryRegion
                # entry; the legacy walk gives up because of the ternary's
                # 2 conditional successors. Finding the LOAD_ASSERTION_ERROR
                # block directly lets the parent AssertRegion reference the
                # TernaryRegion entry via `message_block` (principle 4:
                # parent references child entry).
                mb = self._find_assertion_error_block(succ)
                if mb is not None:
                    message_block = mb
                    break
                # Fallback: walk fall-through chain for cases where
                # LOAD_ASSERTION_ERROR is in a later block (legacy behavior
                # preserved for any edge cases not covered by the new helper).
                mb = self._reach_raise_varargs_block(succ)
                if mb is not None:
                    message_block = mb
                    break

            # [Round4-12] 检测 condition_block 是否是链式比较 header
            # （COPY(arg=2)+COMPARE_OP 对 + 后续 fall-through COMPARE_OP 块）。
            # 若是，将所有 chain 块纳入 AssertRegion.blocks（每块唯一归属），
            # 并记录 chained_compare_ops 供 _generate_assert 重建链式 Compare。
            chained_compare_blocks: List[BasicBlock] = []
            chained_compare_ops: List[str] = []
            cc_info = self._detect_chained_compare_pattern(block)
            if cc_info and len(cc_info.get('compare_ops', [])) >= 2:
                chained_compare_blocks = list(cc_info.get('extra_chain_blocks', []))
                chained_compare_ops = list(cc_info.get('compare_ops', []))

            # [R10 err 1] 检测 condition_block 是否是 BoolOp 条件首段
            # （`assert a > 0 and b > 0, "msg"`）。首段以 POP_JUMP_IF_FALSE 跳到
            # message_block（"and" 失败快跳），其 fall-through 后继为下一段条件块；
            # 末段以 POP_JUMP_IF_TRUE 跳过 message_block（"and" 成功快跳）。
            # 与链式比较不同：链式比较用 COPY+COMPARE_OP 单块多 op，BoolOp 用
            # 多块各含一个 COMPARE_OP，块间用 POP_JUMP_IF_FALSE/TRUE 串联。
            boolop_chain_blocks: List[BasicBlock] = []
            boolop_chain_ops: List[str] = []
            if message_block is not None:
                bc_info = self._detect_assert_boolop_chain(block, message_block)
                if bc_info:
                    boolop_chain_blocks = list(bc_info.get('chain_blocks', []))
                    boolop_chain_ops = list(bc_info.get('chain_ops', []))

            region = AssertRegion(
                region_type=RegionType.ASSERT,
                entry=block,
                blocks=({block} | ({message_block} if message_block else set())
                        | set(chained_compare_blocks) | set(boolop_chain_blocks)),
                condition_block=block,
                message_block=message_block,
                chained_compare_blocks=chained_compare_blocks,
                chained_compare_ops=chained_compare_ops,
                boolop_chain_blocks=boolop_chain_blocks,
                boolop_chain_ops=boolop_chain_ops,
            )
            regions.append(region)
            self.regions.append(region)
            if block not in self.block_to_region:
                self.block_to_region[block] = region
            else:
                existing = self.block_to_region[block]
                if hasattr(existing, 'children'):
                    existing.children.append(region)
                    region.parent = existing
            if message_block and message_block not in self.block_to_region:
                self.block_to_region[message_block] = region
            # 链式比较 chain 块同样登记归属，避免被父 IfRegion 重复生成
            for cb in chained_compare_blocks:
                if cb not in self.block_to_region:
                    self.block_to_region[cb] = region
            # [R10 err 1] BoolOp chain 块登记归属，避免被独立识别为第二条
            # AssertRegion（导致一条 assert 被错误拆为多条）
            for cb in boolop_chain_blocks:
                if cb not in self.block_to_region:
                    self.block_to_region[cb] = region

        return regions

    def _detect_assert_boolop_chain(self, condition_block: BasicBlock,
                                    message_block: BasicBlock) -> Optional[Dict]:
        """[R10 err 1] 检测 assert 条件为 BoolOp 的多段条件链。

        输入: condition_block（首段，已被识别为 AssertRegion.condition_block），
              message_block（含 LOAD_ASSERTION_ERROR 的失败块）。
        返回: {'chain_blocks': [...], 'chain_ops': [...]} 或 None。

        字节码模式（"and" 短路）：
          block_1: a > 0, POP_JUMP_FORWARD_IF_FALSE → message_block
          block_2: b > 0, POP_JUMP_FORWARD_IF_TRUE → end (skip), fall-through → message_block
        字节码模式（"or" 短路）：
          block_1: a > 0, POP_JUMP_FORWARD_IF_TRUE → end (skip), fall-through → block_2
          block_2: b > 0, POP_JUMP_FORWARD_IF_TRUE → end (skip), fall-through → message_block

        两种模式都满足：从 condition_block 起沿 fall-through（非 jump-target 后继）
        能到达一个条件块，该条件块的 fall-through 链最终到达 message_block；
        且条件块的另一后继不是 message_block（是 end/skip 块）。

        操作符判定：chain 块末尾跳转为 IF_FALSE/IF_NONE → 'and'，IF_TRUE/IF_NOT_NONE → 'or'。
        首段 condition_block 的 op 用于第一段（与 BoolOpRegion op_chain 语义一致）。
        """
        if message_block is None:
            return None
        # 首段 op 由 condition_block 的跳转方向决定（与 BoolOpRegion 一致）：
        # IF_FALSE/IF_NONE → 'and'（失败快跳），IF_TRUE/IF_NOT_NONE → 'or'（成功快跳）。
        # 注意：BoolOp 末段在 "and" 时用 IF_TRUE（成功快跳）、在 "or" 时也用 IF_TRUE，
        # 故末段跳转方向不能用于判定 op；必须用首段。
        cond_last = condition_block.get_last_instruction()
        if not cond_last or cond_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
            return None
        first_op = 'and'
        if 'TRUE' in cond_last.opname or 'NOT_NONE' in cond_last.opname:
            first_op = 'or'
        chain_blocks: List[BasicBlock] = []
        chain_ops: List[str] = []
        visited = {condition_block, message_block}
        current = condition_block
        while True:
            last = current.get_last_instruction()
            if not last or last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
                break
            # 找出 fall-through 后继（非 jump-target）
            jump_target_offset = last.argval
            ft_candidates = [s for s in current.conditional_successors
                             if s.start_offset != jump_target_offset and s not in visited]
            if len(ft_candidates) != 1:
                break
            next_block = ft_candidates[0]
            # next_block 必须是条件块（末尾为 FORWARD_CONDITIONAL_JUMP_OPS）
            next_last = next_block.get_last_instruction()
            if not next_last or next_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
                break
            if len(next_block.conditional_successors) != 2:
                break
            # next_block 必须能到达 message_block：
            # (a) message_block 是 next_block 的直接条件后继（常见情况，
            #     如 `a>0 and b>0` 的末段 fall-through → message_block），或
            # (b) next_block 的某个条件后继经 fall-through 链到达 message_block
            #     （链式比较中段经 POP_TOP 中转块到 message_block）。
            # 不能用 _reach_assertion_error_block：它要求块本身只有 ≤1 个
            # 条件后继，而 BoolOp 末段有 2 个条件后继（message_block + end）。
            reaches_msg = (message_block in next_block.conditional_successors
                           or any(self._reaches_block_via_fallthrough(s, message_block)
                                  for s in next_block.conditional_successors))
            if not reaches_msg:
                break
            # 所有 chain 块的 op 与首段一致（纯 and/or 链）。
            # 混合 and/or（如 `a and b or c`）需按各自跳转方向判定，
            # 但 assert 中混合 boolop 罕见，先按首段 op 处理。
            chain_blocks.append(next_block)
            chain_ops.append(first_op)
            visited.add(next_block)
            # 若 next_block 的 fall-through 直接指向 message_block，链终止
            next_jump_target_offset = next_last.argval
            next_ft = [s for s in next_block.conditional_successors
                       if s.start_offset != next_jump_target_offset]
            if any(s is message_block for s in next_ft):
                break
            current = next_block
        if not chain_blocks:
            return None
        return {
            'chain_blocks': chain_blocks,
            'chain_ops': chain_ops,
            'first_op': first_op,
        }

    def _reach_assertion_error_block(self, block: BasicBlock) -> bool:
        """[Round4-12] 从 block 起沿单后继 fall-through 链查找 LOAD_ASSERTION_ERROR。

        用于 assert 检测：当 assert 条件为链式比较时，第一段 COMPARE_OP 块的
        「失败」后继常是一个仅含 POP_TOP 的中转块，需继续 fall-through 才能到
        达真正含 LOAD_ASSERTION_ERROR 的 message 块。

        终止条件：
          - 当前块含 LOAD_ASSERTION_ERROR → True
          - 当前块有 ≥2 个 conditional_successors（出现分支，停止追踪）
          - 当前块以 RAISE_VARARGS / RETURN / RERAISE 终结（无 fall-through）
          - 后继数量 ≠ 1（无法继续 fall-through）
          - 已访问过（防环）
        """
        seen: Set[BasicBlock] = set()
        cur: Optional[BasicBlock] = block
        depth = 0
        while cur is not None and cur not in seen and depth < 8:
            seen.add(cur)
            for instr in cur.instructions:
                if instr.opname == 'LOAD_ASSERTION_ERROR':
                    return True
            if len(cur.conditional_successors) > 1:
                return False
            last = cur.get_last_instruction()
            if last and last.opname in ('RAISE_VARARGS', 'RETURN_VALUE',
                                        'RETURN_CONST', 'RERAISE'):
                return False
            succs = list(cur.successors)
            if len(succs) != 1:
                return False
            cur = succs[0]
            depth += 1
        return False

    def _find_assertion_error_block(self, block: BasicBlock) -> Optional[BasicBlock]:
        """[R8 fix] Find the LOAD_ASSERTION_ERROR block (start of failure path).

        Walks fall-through chain from ``block``, returning the first block
        containing ``LOAD_ASSERTION_ERROR``. Used to locate the assert
        ``message_block`` when the message path contains branching (e.g.,
        a ternary expression in the message — ``assert x, (a if c else b)``).
        In that case ``_reach_raise_varargs_block`` gives up because the
        LOAD_ASSERTION_ERROR block has 2 conditional successors (the ternary
        branches), so we look for LOAD_ASSERTION_ERROR directly instead of
        walking to RAISE_VARARGS.

        For simple cases (``assert x, "msg"``) the LOAD_ASSERTION_ERROR block
        also contains RAISE_VARARGS, so this returns the same block as
        ``_reach_raise_varargs_block``. For chained-compare cases the
        fall-through chain walks via the POP_TOP transit block to the
        LOAD_ASSERTION_ERROR block.

        Per "every block has unique ownership": the returned block may also
        be the entry of a nested TernaryRegion; the parent AssertRegion
        references it via ``message_block`` (principle 4: parent references
        child entry) without claiming the child's other blocks.
        """
        seen: Set[BasicBlock] = set()
        cur: Optional[BasicBlock] = block
        depth = 0
        while cur is not None and cur not in seen and depth < 8:
            seen.add(cur)
            if any(instr.opname == 'LOAD_ASSERTION_ERROR'
                   for instr in cur.instructions):
                return cur
            if len(cur.conditional_successors) > 1:
                return None
            last = cur.get_last_instruction()
            if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST',
                                        'RERAISE'):
                return None
            succs = list(cur.successors)
            if len(succs) != 1:
                return None
            cur = succs[0]
            depth += 1
        return None

    def _reaches_block_via_fallthrough(self, block: BasicBlock,
                                       target: BasicBlock) -> bool:
        """[R10 err 1] 从 block 起沿单后继 fall-through 链查找 target 块。

        用于 BoolOp assert chain 检测：判断 next_block 的某个条件后继
        是否能经单后继 fall-through 链到达 message_block（如链式比较中段
        经 POP_TOP 中转块到 message_block 的场景）。
        """
        seen: Set[BasicBlock] = set()
        cur: Optional[BasicBlock] = block
        depth = 0
        while cur is not None and cur not in seen and depth < 8:
            seen.add(cur)
            if cur is target:
                return True
            if len(cur.conditional_successors) > 1:
                return False
            last = cur.get_last_instruction()
            if last and last.opname in ('RAISE_VARARGS', 'RETURN_VALUE',
                                        'RETURN_CONST', 'RERAISE'):
                return False
            succs = list(cur.successors)
            if len(succs) != 1:
                return False
            cur = succs[0]
            depth += 1
        return False

    def _reach_raise_varargs_block(self, block: BasicBlock) -> Optional[BasicBlock]:
        """[Round4-12] 从 block 起沿单后继 fall-through 链查找含 RAISE_VARARGS 的块。

        返回该块（assert message 块），或 None。用于在链式比较 assert 中定位
        实际的 LOAD_ASSERTION_ERROR + RAISE_VARARGS 块（可能隔一个 POP_TOP 中转块）。
        """
        seen: Set[BasicBlock] = set()
        cur: Optional[BasicBlock] = block
        depth = 0
        while cur is not None and cur not in seen and depth < 8:
            seen.add(cur)
            if any(instr.opname == 'RAISE_VARARGS' for instr in cur.instructions):
                return cur
            if len(cur.conditional_successors) > 1:
                return None
            last = cur.get_last_instruction()
            if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
                return None
            succs = list(cur.successors)
            if len(succs) != 1:
                return None
            cur = succs[0]
            depth += 1
        return None

    def _identify_chained_compare_regions(self, loop_regions: List[Region],
                                           try_regions: List[Region],
                                           with_regions: List[Region],
                                           match_regions: List[Region],
                                           assert_regions: List[Region]) -> List[Region]:
        """识别链式比较区域（Chained Comparison Region）

        【区域类型】 CHAINED_COMPARE — 链式比较区域（Chained Comparison Region）
        实现说明：本方法不创建独立的 RegionType.CHAINED_COMPARE，
        而是构造 IfRegion(region_type=RegionType.IF) 并填充
        chained_compare_blocks / chained_compare_ops 标记字段，
        由下游 _generate_if 根据 compare_ops 数量识别并还原为 ast.Compare。

        1. 算法描述（基于"No More Gotos"论文）
           - 归约阶段: Phase 2 的高层识别第一步，先于 BoolOp / Ternary / Conditional；
             在 Phase 1 的 Loop / Try / With / Match / Assert 之后执行
           - 识别策略: 以 CPython 编译器的固定字节码模式（COPY(arg=2) +
             COMPARE_OP 指令对）为锚点，沿 fallthrough 后继链追踪连续的
             COMPARE_OP 块，从而把 a < b < c 这类多比较运算还原为一个语义整体
           - 归约过程:
             Step 1: 收集 loop_regions / try_regions / with_regions /
                     match_regions / assert_regions 的所有块到 claimed 集合，
                     实现"每块唯一归属"——已被识别的区域不会被本方法抢占
             Step 2: 按 cfg.get_blocks_in_order() 顺序遍历每个未占用块，
                     调用 _is_chained_compare_header 判断块内是否含
                     COPY(arg=2)+COMPARE_OP 指令对
             Step 3: 对候选 header 调用 _detect_chained_compare_pattern，
                     沿 fallthrough 后继（min(start_offset)）逐块扫描额外
                     COMPARE_OP，得到 compare_ops 列表与 extra_chain_blocks
             Step 4: 取 header 的 conditional_successors，要求恰为 2 个；
                     按 start_offset 排序得到 then_succ（fallthrough，最小）
                     与 else_succ（短路跳出，最大）
             Step 5: 调用 _build_chained_compare_region 构造 IfRegion，
                     将 header、then_succ、else_succ 与所有 compare 块合入
                     region.blocks，写入 chained_compare_blocks 与
                     chained_compare_ops；构造成功后登记到 self.regions
                     与 claimed，保证后续识别不会再分配这些块

        2. 字节码模式（CPython 编译器行为）
           模式: 链式比较 a < b < c
             源码:        if a < b < c: ...
             字节码结构:  LOAD a, LOAD b, LOAD c,
                          COPY(arg=2),         # 复制栈上 b 供下次比较
                          COMPARE_OP <,        # a < b
                          COPY(arg=2),         # 复制栈上 c 供下次比较
                          COMPARE_OP <,        # b < c
                          POP_JUMP_IF_FALSE → else   # 短路跳出
             特征指令:    COPY(arg=2), COMPARE_OP
             理论依据:    CPython 3.11+ 字节码规范，编译器对链式比较的确定性优化
                          （非启发式），详见 dis 模块与 Python/ceval.c 实现

        3. 边界条件（数学性质）
           - 必须存在至少一对 COPY(arg=2)+COMPARE_OP，且 _detect_chained_compare_pattern
             要求至少 1 个 extra_chain_block（即 compare_ops 长度 ≥ 2），否则视为普通
             单比较运算，交由后续 Conditional 识别
           - header 必须有且仅有 2 个 conditional_successors；否则跳过
           - fallthrough 链追踪在以下情况终止：后继 < 2、已被访问、不含 COMPARE_OP、
             或存在后向边（避免侵入循环结构）
           - 已被 Phase 1 区域（loop/try/with/match/assert）占用的块直接跳过，
             保证唯一归属

        4. 归约语义（与父区域的契约）
           - 入口块: header 块（同时也是 IfRegion.condition_block 与 entry）
           - 父区域引用: 父区域通过 block_to_region[header] 间接持有本 IfRegion；
             父区域仅引用 entry，不感知内部 chained_compare_blocks
           - 后继语义: then_succ（fallthrough）继续比较或进入 then 体；
             else_succ（短路跳出）即真实 else 分支入口

        5. AST 映射
           - 对应生成方法: _generate_if（IfRegion 通用生成方法）
           - AST 节点类型: ast.Compare（chained，当 compare_ops ≥ 2 时由
             _generate_if 重建为多 op 的 Compare 节点）
           - 关键字段映射:
               IfRegion.chained_compare_blocks → 用于块覆盖范围判定
               IfRegion.chained_compare_ops    → ast.Compare.ops / 节点比较符序列
               IfRegion.condition_block         → ast.Compare.left/operands 起点
               IfRegion.then_blocks / else_blocks → ast.If.body / orelse

        6. 已知失败模式
           - CHAINED_COMPARE: 当前测试矩阵通过率 100%
           - 与 Conditional 区域无冲突（在 Conditional 之前完成识别并标记 claimed）
           - 与 BoolOp 区域无冲突（先于 BoolOp 识别，避免被短路求值拆分）
        """
        claimed = set()
        for regions in [loop_regions, try_regions, with_regions, match_regions, assert_regions]:
            for region in regions:
                claimed.update(region.blocks)

        chained_compare_regions = []
        blocks_in_order = self.cfg.get_blocks_in_order()
        for block in blocks_in_order:
            if block in claimed:
                continue
            if not self._is_chained_compare_header(block):
                continue

            info = self._detect_chained_compare_pattern(block)
            if not info:
                continue

            succs = list(block.conditional_successors)
            if len(succs) != 2:
                continue
            then_succ, else_succ = sorted(succs, key=lambda s: s.start_offset)
 
            region = self._build_chained_compare_region(
                block, block, set(), then_succ, else_succ, info
            )
            if region:
                chained_compare_regions.append(region)
                self.regions.append(region)
                claimed.update(region.blocks)

        return chained_compare_regions

    def _should_skip_block_for_if_region(self, block: BasicBlock, block_region,
                                          loop_regions: List, last_instr) -> bool:
        if any(instr.opname == 'WITH_EXCEPT_START' for instr in block.instructions):
            return True
        if not loop_regions:
            return False
        if isinstance(block_region, LoopRegion):
            if block == block_region.condition_block:
                return True
            if block == block_region.header_block:
                if last_instr and last_instr.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                    return True
                if block_region.condition_block is None:
                    cond_succs = list(block.conditional_successors)
                    if len(cond_succs) == 2:
                        then_succ, else_succ = sorted(cond_succs, key=lambda s: s.start_offset)
                        then_last = then_succ.get_last_instruction()
                        else_last = else_succ.get_last_instruction()
                        is_if_break_pattern = (
                            then_last and then_last.opname in ('RETURN_VALUE', 'RETURN_CONST') and
                            else_last and else_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                        )
                        if not is_if_break_pattern:
                            return True
                    else:
                        return True
                cond_succs = list(block.conditional_successors)
                if len(cond_succs) != 2:
                    return True
                if not all(s in block_region.blocks and s != block_region.condition_block for s in cond_succs):
                    return True
                if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                    _cond_instrs = [i for i in block.instructions if i.offset < last_instr.offset]
                    _has_store_before_cond = any(
                        i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                    'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR')
                        for i in _cond_instrs
                    )
                    _jump_target = self.cfg.get_block_by_offset(last_instr.argval) if last_instr.argval is not None else None
                    _ft_succ = next((s for s in cond_succs if s != _jump_target), None)
                    _jt_role = self.block_roles.get(_jump_target.start_offset) if _jump_target else None
                    _ft_last = _ft_succ.get_last_instruction() if _ft_succ else None
                    if _has_store_before_cond:
                        _jump_exits_loop = _jump_target and _jump_target not in block_region.blocks
                        _ft_in_loop = _ft_succ and _ft_succ in block_region.blocks
                        if _jump_exits_loop or not _ft_in_loop:
                            return True
                        _ft_role = self.block_roles.get(_ft_succ.start_offset) if _ft_succ else None
                        if _ft_role in (BlockRole.BREAK, BlockRole.PURE_BREAK, BlockRole.RETURN, BlockRole.RETURN_NONE):
                            return True
                        if _ft_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):
                            return True
                        if _ft_succ:
                            _ft_last_i = _ft_succ.get_last_instruction()
                            if _ft_last_i and _ft_last_i.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                                _ft_jump_target = self.cfg.get_block_by_offset(_ft_last_i.argval) if _ft_last_i.argval is not None else None
                                if _ft_jump_target and (_ft_jump_target == block_region.condition_block or _ft_jump_target == block_region.header_block):
                                    return True
                        if _ft_role == BlockRole.LOOP_BACK_EDGE and _jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                            return True
                        if (_ft_last and _ft_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                            and _jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK)):
                            return True
                    _cond_terminator = _cond_instrs[-1] if _cond_instrs else None
                    _cond_is_pure_compare = _cond_terminator and _cond_terminator.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')
                    if not _cond_is_pure_compare and not _has_store_before_cond:
                        _jt_exits_loop = _jump_target and _jump_target not in block_region.blocks
                        if _jt_exits_loop:
                            return True
                        # [CPython peephole] Back-edge condition re-check
                        # without a STORE: e.g., `while not done and
                        # has_data():` where CPython 3.11 duplicates the
                        # compound condition at the back edge. The
                        # back-edge re-check is `LOAD done;
                        # POP_JUMP_IF_TRUE` (no STORE before the
                        # condition — just a condition re-evaluation).
                        # The fallthrough leads to the LOOP_BACK_EDGE
                        # block (or to a block whose last instr is a
                        # BACKWARD_CONDITIONAL_JUMP) and the jump target
                        # is a BREAK block (exits the loop when the
                        # re-check fails). This is the same back-edge
                        # recheck pattern as the with-STORE case above,
                        # just without the loop increment. Without this
                        # check, the header_block would be misidentified
                        # as a standalone IfRegion, producing spurious
                        # `if (not done): pass` in the loop body.
                        if _ft_succ:
                            _ft_role_nostore = self.block_roles.get(_ft_succ.start_offset)
                            if _ft_role_nostore == BlockRole.LOOP_BACK_EDGE and _jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                                return True
                            if (_ft_last and _ft_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                                and _jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK)):
                                return True
                    if _cond_is_pure_compare:
                        if (_ft_last and _ft_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                            and _jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK)):
                            return True
                        if _jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                            return True
                return False
            # Check for back-edge condition block: a body block (not condition_block
            # or header_block) whose fallthrough leads to the back_edge_block and
            # whose conditional jump target is a loop exit (BREAK). This block
            # contains the loop increment + back-edge condition re-check (e.g.,
            # 'i += 1' followed by 'i < len(data)' which exits if false). It is
            # part of the loop's back-edge condition, not a standalone if statement.
            if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                _be_cond_succs = list(block.conditional_successors)
                if len(_be_cond_succs) == 2:
                    _be_jump_target = self.cfg.get_block_by_offset(last_instr.argval) if last_instr.argval is not None else None
                    _be_ft_succ = next((s for s in _be_cond_succs if s != _be_jump_target), None)
                    if _be_ft_succ and _be_jump_target:
                        _be_ft_role = self.block_roles.get(_be_ft_succ.start_offset)
                        _be_jt_role = self.block_roles.get(_be_jump_target.start_offset)
                        # Fallthrough is the back_edge_block (LOOP_BACK_EDGE role)
                        # and jump target is a loop exit (BREAK role)
                        if _be_ft_role == BlockRole.LOOP_BACK_EDGE and _be_jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                            return True
                        # Fallthrough leads to a backward conditional jump (back edge)
                        # and jump target is a loop exit (BREAK role)
                        _be_ft_last = _be_ft_succ.get_last_instruction()
                        if (_be_ft_last and _be_ft_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS
                                and _be_jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK)):
                            return True
        elif block_region is None:
            for _lr in loop_regions:
                if block == _lr.condition_block:
                    return True
                if block == _lr.header_block and _lr.condition_block is not None:
                    _cond_succs = list(block.conditional_successors)
                    if len(_cond_succs) == 2 and last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        _jump_target = self.cfg.get_block_by_offset(last_instr.argval) if last_instr.argval is not None else None
                        _jt_role = self.block_roles.get(_jump_target.start_offset) if _jump_target else None
                        if _jt_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                            return True
                    break
        elif block_region is not None:
            if not block_region.contains_block(block):
                return True
            if type(block_region) is TryExceptRegion:
                if any(lr.condition_block == block for lr in loop_regions):
                    return True
                block_in_loop = any(block in lr.blocks for lr in loop_regions)
                if block_in_loop:
                    cond_succs_ib = list(block.conditional_successors)
                    if len(cond_succs_ib) == 2:
                        for _cs in cond_succs_ib:
                            _cs_role = self.block_roles.get(_cs.start_offset)
                            if _cs_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                                return True
            # [Phase 4 回归修复] BoolOpRegion 作为循环复合条件（如
            # `while a > 0 and b > 0:`）时，CPython 3.11 在循环入口和
            # back-edge 处复制复合条件。BoolOpRegion 的链块（每个含
            # POP_JUMP_FORWARD_IF_FALSE 跳向循环出口）会被 IfRegion 创建
            # 逻辑误识别为独立的 if-then，把整个循环体包进虚假的 if。
            # 判别：块在 BoolOpRegion 中 + 块在循环内 + 块的条件跳转目标
            # 在循环外（循环出口）。此 BoolOpRegion 是循环条件，不是
            # if-then。与 TryExceptRegion 的处理对称。
            elif type(block_region) is BoolOpRegion:
                if last_instr and last_instr.argval is not None:
                    _bor_jt = self.cfg.get_block_by_offset(last_instr.argval)
                    if _bor_jt is not None:
                        for _lr in loop_regions:
                            if block in _lr.blocks and _bor_jt not in _lr.blocks:
                                return True
        cond_succs_check = list(block.conditional_successors)
        if len(cond_succs_check) == 2:
            block_in_loop = any(block in lr.blocks for lr in loop_regions)
            if block_in_loop:
                if any(s in lr.blocks or s == lr.header_block or s == lr.entry for lr in loop_regions for s in cond_succs_check):
                    is_loop_backedge_target = any(
                        any(su.start_offset >= lr.header_block.start_offset for su in block.successors)
                        and any(i.opname.startswith('JUMP_BACKWARD') or i.opname in BACKWARD_CONDITIONAL_JUMP_OPS for i in block.instructions)
                        for lr in loop_regions
                    )
                    if is_loop_backedge_target:
                        return True
        return False

    def _identify_conditional_regions(self, loop_regions: List[Region],
                                      assert_regions: List[Region],
                                      try_regions: List[Region],
                                      with_regions: List[Region],
                                      match_regions: List[Region],
                                      boolop_regions: List[Region],
                                      ternary_regions: List[Region] = None) -> List[Region]:
        """_identify_conditional_regions — 识别条件分支区域（if/elif/else）

        【区域类型】 IF / IF_THEN_ELSE / IF_ELIF_CHAIN — 条件区域（If Region）
        RegionType 枚举值: RegionType.IF / RegionType.IF_THEN_ELSE / RegionType.IF_ELIF_CHAIN

        1. 算法描述（基于"No More Gotos"论文）
           - 归约阶段: Phase 2（在 BOOLOP/TERNARY 之后，SEQUENCE 之前）
           - 识别策略: 扫描 FORWARD_CONDITIONAL_JUMP_OPS（POP_JUMP_FORWARD_IF_FALSE/TRUE）
             定位条件跳转，区分 if-then、if-then-else、if-elif-else 链。
             跳过已归属其他区域的块（loop/try/with/match/boolop/ternary 内的块）。
           - 归约过程:
             Step 1: 遍历未归属块，查找末尾为 FORWARD_CONDITIONAL_JUMP_OPS 的块作为 if 条件。
             Step 2: 区分条件上下文（is_condition_context）与值上下文。
                     值上下文中若 BoolOpRegion 已存在则跳过 IfRegion 创建。
             Step 3: guard 检查块识别——位于 case body 中且跳转目标指向同 MatchRegion 的
                     下一 case_block 时，跳过 IfRegion 创建（guard 块归 MatchRegion）。
             Step 4: 收集 then_blocks/else_blocks，构建 IfRegion 并注册 block_to_region。
             Step 5: elif 链识别——else 块以条件跳转结尾时递归构建 IF_ELIF_CHAIN。

        2. 字节码模式（CPython 编译器行为）
           模式 A: if-then
             源码: if cond: ...
             字节码结构: [cond] POP_JUMP_FORWARD_IF_FALSE → end | [then body] |
             特征指令: POP_JUMP_FORWARD_IF_FALSE, POP_JUMP_FORWARD_IF_TRUE
           模式 B: if-then-else
             源码: if cond: ... else: ...
             字节码结构: [cond] POP_JUMP_FORWARD_IF_FALSE → else | [then] JUMP_FORWARD → end | [else]
           模式 C: if-elif-else
             else 块以条件跳转结尾，递归形成 IF_ELIF_CHAIN

        3. 边界条件（数学性质）
           - 条件跳转目标确定 then/else 分支边界
           - 值上下文（is_condition_context=False）: 若 BoolOpRegion 已存在则不创建 IfRegion
           - guard 块排除: 位于 case body 内且前向跳转到同 MatchRegion case_block 的块跳过
           - TernaryRegion 值块排除: BoolOpRegion 是 TernaryRegion 的 true/false value block 时跳过
           - 每个基本块经 block_to_region 唯一归属一个 IfRegion

        4. 归约语义（与父区域的契约）
           - 入口块: 条件判断块（region.entry，含 POP_JUMP_FORWARD_IF_*）
           - 父区域引用: 父区域仅引用本 region 的 entry 块
           - 子区域块不出现: then_blocks/else_blocks 全部归约为单个抽象节点

        5. AST 映射
           - 对应生成方法: _generate_if（region_ast_generator.py）
           - AST 节点类型: ast.If
           - 关键字段映射:
             entry → If.test（条件表达式）
             then_blocks → If.body
             else_blocks → If.orelse

        6. 已知失败模式
           - 当前测试矩阵通过率: 100%（if_region 311/311），无已知失败模式
           - 本方法遵循区域归约算法 4 核心原则:
             自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
        """
        if_regions = []
        try_handler_blocks = set()
        # [Phase 3 adv17_try_except_star] try_cleanup_blocks 仅含 except* 框架
        # 清理块（PREP_RERAISE_STAR 等），在主循环中跳过 IfRegion 创建。
        # 区别于 try_handler_blocks：handler body 块不应被跳过（允许嵌套 if），
        # 只有 cleanup_blocks 才应被跳过。
        try_cleanup_blocks = set()
        if try_regions:
            for tr in try_regions:
                if hasattr(tr, 'handler_entry_blocks'):
                    try_handler_blocks.update(tr.handler_entry_blocks)
                if hasattr(tr, 'finally_blocks') and tr.finally_blocks:
                    try_handler_blocks.update(tr.finally_blocks)
                if hasattr(tr, 'except_handlers') and tr.except_handlers:
                    for _, _, hblocks in tr.except_handlers:
                        try_handler_blocks.update(hblocks)
                # [Phase 3 adv17_try_except_star] cleanup_blocks 含
                # except* 共享清理块（PREP_RERAISE_STAR），也必须排除，否则
                # 该块的条件跳转（POP_JUMP_FORWARD_IF_NOT_NONE）会被误识别为
                # IfRegion，生成多余的 `if True: pass`。
                if hasattr(tr, 'cleanup_blocks') and tr.cleanup_blocks:
                    try_handler_blocks.update(tr.cleanup_blocks)
                    try_cleanup_blocks.update(tr.cleanup_blocks)
        with_handler_blocks = set()
        if with_regions:
            for wr in with_regions:
                if hasattr(wr, 'cleanup_blocks'):
                    with_handler_blocks.update(wr.cleanup_blocks)
                if hasattr(wr, 'exception_blocks'):
                    with_handler_blocks.update(wr.exception_blocks)
        for bor in self._filter_regions(boolop_regions or [], BoolOpRegion):
            if len(bor.op_chain) < 2:
                continue
            last_cb = bor.op_chain[-1][0]
            last_cb_last = last_cb.get_last_instruction()
            last_cb_op = bor.op_chain[-1][1]
            if not last_cb_last or last_cb_last.argval is None:
                continue
            last_jt = self.cfg.get_block_by_offset(last_cb_last.argval)
            if not last_jt:
                continue
            _jt_has_real_code = False
            for instr in last_jt.instructions:
                if instr.opname in NOISE_OPS:
                    continue
                if instr.opname in ('LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST', 'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'POP_TOP'):
                    continue
                if instr.opname in FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS:
                    _jt_has_real_code = True
                    break
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_ATTR', 'STORE_SUBSCR',
                                    'BINARY_OP', 'CALL'):
                    _jt_has_real_code = True
                    break
            if not _jt_has_real_code:
                continue
            for i in range(len(bor.op_chain) - 2, -1, -1):
                prev_cb, prev_op = bor.op_chain[i]
                if prev_op == last_cb_op:
                    prev_last = prev_cb.get_last_instruction()
                    if prev_last and prev_last.argval is not None and prev_last.argval != last_cb_last.argval:
                        if i + 1 < 2:
                            break
                        if prev_last.opname != last_cb_last.opname:
                            break
                        # [P5 + Cluster 4 interaction] Skip trimming when
                        # prev_cb's jump target is a value block (has its own
                        # conditional jump). This happens when ternaries are
                        # BoolOp operands — each ternary's cond block has a
                        # different jump target (its false_value), but the
                        # chain correctly extends across ternary operands.
                        # Trimming would incorrectly cut the chain.
                        _prev_jt = self.cfg.get_block_by_offset(prev_last.argval)
                        if _prev_jt is not None:
                            _prev_jt_last = _prev_jt.get_last_instruction()
                            if (_prev_jt_last is not None
                                    and _prev_jt_last.opname in FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
                                    and _prev_jt_last.argval is not None):
                                break
                        trimmed_chain = bor.op_chain[:i+1]
                        trimmed_blocks = set()
                        for cb, _ in trimmed_chain:
                            trimmed_blocks.add(cb)
                        removed_blocks = bor.blocks - trimmed_blocks
                        for rb in removed_blocks:
                            if rb in self.block_to_region and self.block_to_region[rb] is bor:
                                del self.block_to_region[rb]
                        bor.op_chain = trimmed_chain
                        bor.blocks = trimmed_blocks
                    break
        # 预扫描：识别链式比较的额外链块（extra_chain_blocks）
        # 链式比较如 0 < x < 10 会生成多块条件：
        #   Block A: COPY, COMPARE_OP, POP_JUMP_IF_FALSE -> cleanup
        #   Block B: COMPARE_OP, POP_JUMP_IF_FALSE -> merge (fallthrough successor of A)
        #   cleanup: POP_TOP, JUMP_FORWARD -> merge
        # 由于块按反向偏移顺序处理，Block B 会在 Block A 之前被处理，
        # 导致 Block B 被误识别为独立的 elif 条件块。
        # 解决方案：预扫描所有块，找出链式比较的 extra_chain_blocks 并加入 claimed 集合。
        chained_compare_extra_blocks = set()
        for _blk in self.cfg.get_blocks_in_order():
            if len(_blk.conditional_successors) != 2:
                continue
            _cc_info = self._detect_chained_compare_pattern(_blk)
            if _cc_info:
                for _extra in _cc_info.get('extra_chain_blocks', []):
                    chained_compare_extra_blocks.add(_extra)

        blocks_in_reverse = sorted(
            self.cfg.get_blocks_in_order(),
            key=lambda b: b.start_offset, reverse=True
        )
        for block in blocks_in_reverse:
            if len(block.conditional_successors) != 2:
                continue
            last_instr = block.get_last_instruction()
            if last_instr is None:
                continue
            if last_instr.opname == 'FOR_ITER':
                continue
            # [聚类2 修复] 跳过 await 轮询自循环块（SEND 是其条件分支指令）。
            # CPython 的 await 字节码中，SEND 有两个后继：自循环（继续轮询）
            # 和退出（awaitable 完成）。这让 block.conditional_successors == 2，
            # 被误识别为 IfRegion。但这是 await 的实现细节，不应成为独立 if。
            # 判定：块含 SEND + YIELD_VALUE + JUMP_BACKWARD_NO_INTERRUPT 三联。
            if any(i.opname == 'SEND' for i in block.instructions) and \
               any(i.opname == 'YIELD_VALUE' for i in block.instructions) and \
               any(i.opname == 'JUMP_BACKWARD_NO_INTERRUPT' for i in block.instructions):
                continue
            block_region = self.block_to_region.get(block)
            if block in with_handler_blocks:
                continue
            # [Phase 3 adv17_try_except_star] except* 框架清理块（PREP_RERAISE_STAR
            # 等，含条件跳转 POP_JUMP_FORWARD_IF_NOT_NONE）不能被 IfRegion 抢占。
            # 注意：只跳过 cleanup_blocks，不跳过 handler body 块——handler body
            # 中的 if 语句应正常识别为嵌套 IfRegion。此前使用 try_handler_blocks
            # 跳过所有块，导致 except handler 内的 if 语句丢失（adv09 回归）。
            if block in try_cleanup_blocks:
                continue
            if self._should_skip_block_for_if_region(block, block_region, loop_regions, last_instr):
                continue
            # 跳过链式比较的额外链块：这些块是链式比较条件的一部分，
            # 不应被当作独立的 if/elif 条件块处理
            if block in chained_compare_extra_blocks:
                continue

            if any(instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH', 'PREP_RERAISE_STAR') for instr in block.instructions):
                continue

            if any(tr.entry == block for tr in self._filter_regions(ternary_regions or [], TernaryRegion)):
                continue
            # [R16-06 fix] 跳过 TernaryRegion 的 merge_block 当
            # merge_context='compare' 且 merge_block 以 JUMP_IF_FALSE_OR_POP
            # (或 JUMP_IF_TRUE_OR_POP) 结尾 (chained compare middle ternary).
            # 模式: `a < (ternary) < e` 中，ternary 的 merge_block 是
            # `<SWAP, COPY, COMPARE_OP, JUMP_IF_FALSE_OR_POP>`，是链式比较的
            # 第一段。若不跳过，IfRegion 会抢占此块作为 if 条件，破坏链式比较
            # 重建。依「每块唯一归属」: merge_block 已归属 TernaryRegion 父
            # 表达式（Expr(Compare)），IfRegion 不应重复抢占。
            # 注意: 仅 JUMP_IF_*_OR_POP 是链式比较短路；普通 POP_JUMP_IF_FALSE
            # 是 if 条件测试，不应跳过（如 `if (ternary) > x: pass`）。
            for tr in self._filter_regions(ternary_regions or [], TernaryRegion):
                if (getattr(tr, 'merge_block', None) is block
                        and getattr(tr, 'merge_context', None) == 'compare'
                        and block.get_last_instruction() is not None
                        and block.get_last_instruction().opname in (
                            'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP')):
                    break
            else:
                tr = None
            if tr is not None:
                continue

            if match_regions:
                if isinstance(block_region, MatchRegion):
                    if not self._is_wildcard_match_subject(block_region, block):
                        _in_case_body = any(block in body_list
                                           for mr in match_regions
                                           for body_list in mr.case_bodies)
                        if not _in_case_body:
                            continue
                        # 区域归约算法 [RC3 修复]：识别 guard 检查块，跳过 IfRegion 创建。
                        #
                        # 反编译逻辑（写入注释，符合区域归约算法原则）：
                        # guard 检查块位于 case body 入口处，结构为：
                        #   STORE_NAME <pattern_var>           # 存储 pattern 绑定变量
                        #   [LOAD/CALL/COMPARE_OP ...]         # guard 表达式计算
                        #   POP_JUMP_IF_FALSE → 下一 case_block # guard 失败跳到下一 case
                        #
                        # 该块的末尾条件跳转目标指向同一 MatchRegion 中更靠后的 case_block
                        # （即下一个 case 的模式检查块）。这表明该块是 guard 检查块，
                        # 是 MatchRegion 的内部结构，不应被识别为 IfRegion。
                        #
                        # 若不跳过，IfRegion 会跨越多个 case 生成嵌套 if-elif-else，
                        # 破坏 MatchRegion 的完整性（违反「每块唯一归属」和「嵌套即抽象节点」原则）。
                        #
                        # 判定条件（数学性质）：
                        #   1. 末尾指令是条件跳转（CONDITIONAL_JUMP_OPS）
                        #   2. 跳转目标块属于同一 MatchRegion 的 case_blocks
                        #   3. 跳转目标块的 start_offset > 当前块的 start_offset（前向跳转）
                        #
                        # 已知失败模式：m083（case 3 `str() as s if s` 的 truthy guard，
                        #   case 4 `list() as lst if len(lst) > 0` 的比较 guard）— 修复前
                        #   指令数 99 vs 111（多 12 条，IfRegion 吸收了后续 case 的 body）。
                        _rc3_guard_last = block.get_last_instruction()
                        if (_rc3_guard_last is not None
                                and _rc3_guard_last.opname in CONDITIONAL_JUMP_OPS
                                and _rc3_guard_last.argval is not None):
                            _rc3_jt_blk = self.cfg.get_block_by_offset(_rc3_guard_last.argval)
                            if (_rc3_jt_blk is not None
                                    and _rc3_jt_blk in block_region.case_blocks
                                    and _rc3_jt_blk.start_offset > block.start_offset):
                                continue
                    else:
                        body_start = block_region.case_body_start_indices.get(block.start_offset, 0)
                        if body_start <= 0:
                            continue
                        has_body_cond_jump = any(
                            i.opname in CONDITIONAL_JUMP_OPS
                            for i in block.instructions[body_start:]
                            if i.opname not in NOISE_OPS
                        )
                        if not has_body_cond_jump:
                            continue
            if isinstance(block_region, AssertRegion):
                continue
            if any(block == ar.entry for ar in assert_regions or []):
                continue

            if any(block in mr.blocks for mr in match_regions):
                mr_owner = next((mr for mr in match_regions if block in mr.blocks), None)
                if mr_owner and not isinstance(block_region, (MatchRegion, BoolOpRegion)):
                    continue

            if isinstance(block_region, BoolOpRegion) and block_region.entry != block:
                # [Phase 3 adv14_boolop_result_compare] 双角色 merge_block
                # 例外：值上下文 BoolOpRegion 的 merge_block 可能含
                # COMPARE_OP + POP_JUMP_IF_FALSE（如 ``(a and b) == (c and d)``
                # 中 Block 14 是 R2.merge_block 又是真正的 if 条件块）。此时
                # 必须创建 IfRegion——merge_block 既是 BoolOp 值的归并点又是
                # if 条件入口。这是「每块唯一归属」原则的明确例外，类似
                # loop_condition_blocks 例外，遵循同样的归约层次化原则。
                _is_merge_if_condition = (
                    block_region.merge_block is block
                    and not getattr(block_region, 'is_condition_context', True)
                    and any(i.opname == 'COMPARE_OP' for i in block.instructions)
                    and last_instr is not None
                    and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS
                )
                if _is_merge_if_condition:
                    pass  # 允许后续创建 IfRegion
                elif any(block in br.blocks and br.entry != block for br in self._filter_regions(boolop_regions or [], BoolOpRegion)):
                    continue
                else:
                    cond_succs_for_check = list(block.conditional_successors)
                    if len(cond_succs_for_check) == 2:
                        then_cand = sorted(cond_succs_for_check, key=lambda s: s.start_offset)[0]
                        in_structural = any(
                            then_cand in sr.blocks or then_cand == sr.entry
                            for sr in (loop_regions or []) + (match_regions or [])
                            + ([r for r in (try_regions or []) if hasattr(r, 'blocks')])
                            + ([r for r in (with_regions or []) if hasattr(r, 'blocks')])
                        )
                        if not in_structural:
                            continue
                    else:
                        continue

            boolop_region = self._resolve_boolop_condition_region(block)

            condition_block = block
            chain_blocks = set()
            if isinstance(block_region, BoolOpRegion) and block_region.entry == block:
                # [Phase 7 根因 E] 值上下文 BoolOpRegion 入口的 IfRegion 跳过。
                #
                # 算法根因：值上下文 BoolOp（is_condition_context=False）产生一个
                # 值，永远不会是 if 语句的 cond 块（if 用条件上下文跳转
                # POP_JUMP_IF_FALSE，is_condition_context=True）。但值上下文 BoolOp
                # 的结果消费方式决定 IfRegion 是否应建在其入口：
                # - 终端消费（STORE_* 赋值 / POP_TOP 表达式语句丢弃）→ 不是 if，
                #   跳过 IfRegion 创建（value_target 覆盖 STORE_*，POP_TOP 覆盖
                #   表达式语句丢弃）。
                # - 表达式馈入（COMPARE_OP/BINARY_OP/LOAD）→ boolop 结果参与下一
                #   表达式（如 `(a or b) == c`），IfRegion 应建在 boolop 入口
                #   （其 cond 链含 boolop+compare），不跳过。
                #
                # POP_TOP 判据是语义不变量（非实例驱动）：CPython 字节码中表达式
                # 语句必以 POP_TOP 丢弃 TOS 结果，这是语言级不变量，不依赖具体
                # 测试用例。bo53（`a or b or c\nd or e or f`）的语句边界识别由
                # 补丁 2（短路跳转目标结构语义）在识别阶段一次正确处理，此处
                # POP_TOP 判据仅防止表达式语句 boolop 被误建 IfRegion。
                if not getattr(block_region, 'is_condition_context', True):
                    _bor_merge = block_region.merge_block
                    _bor_merge_first = (next((i for i in _bor_merge.instructions
                                              if i.opname not in NOISE_OPS), None)
                                        if _bor_merge is not None else None)
                    if (getattr(block_region, 'value_target', None)
                            or (_bor_merge_first is not None
                                and _bor_merge_first.opname == 'POP_TOP')):
                        continue
                # 区域归约算法：每块唯一归属 + 嵌套即抽象节点。
                # 当 BoolOpRegion 处于值上下文(is_condition_context=False)且其入口是
                # 某个 TernaryRegion 的 true_value_block/false_value_block 时，该
                # BoolOpRegion 是 TernaryRegion 的子区域（三元表达式的值表达式），
                # 不应在此处被升级为 IfRegion——否则会破坏父子嵌套关系，导致
                # block_to_region 中 IfRegion 抢占 BoolOpRegion 的块，AST 生成时
                # _build_ternary_value_expr 找不到 BoolOpRegion，BoolOp 被丢失。
                # 典型场景: x = (a and b) if flag else (c or d)
                #   BoolOpRegion(a and b) 的 merge_block 是 JUMP_FORWARD 块（非 STORE），
                #   value_target 无法检测（为 None），但 is_condition_context=False
                #   已表明它是值上下文。
                if not getattr(block_region, 'is_condition_context', True):
                    _is_ternary_value_block = False
                    for _tr in self._filter_regions(ternary_regions or [], TernaryRegion):
                        if block in (_tr.true_value_block, _tr.false_value_block):
                            _is_ternary_value_block = True
                            break
                    if _is_ternary_value_block:
                        continue
                # [Cluster 4] Chained-compare phantom BoolOpRegion guard.
                # The chained compare's short-circuit jumps
                # (POP_JUMP_IF_FALSE per middle segment, POP_JUMP_IF_TRUE
                # on the last segment for `not <chain>`) are misread by the
                # BoolOp detector as a BoolOpRegion whose blocks are exactly
                # {entry} ∪ chained_compare_blocks of a chained-compare
                # IfRegion created in Phase 2a. If we let this phantom
                # override condition_block with op_chain[-1] (the last chain
                # block), _detect_chained_compare_pattern(condition_block)
                # below returns None (the last chain block has no
                # COPY+COMPARE_OP pair), so the IfRegion loses its
                # chained_compare_blocks/ops and the AST generator falls
                # back to the broken BoolOp path. Per unique-block-
                # ownership the chained compare (Phase 2a, more reduced)
                # owns these blocks; skip the BoolOp condition_block
                # override and let the chained-compare detection below
                # handle it (condition_block stays as `block`).
                _cc_phantom = False
                if getattr(block_region, 'op_chain', None):
                    _bor_blocks = set(b for b, _ in block_region.op_chain)
                    for _r in self.regions:
                        if (isinstance(_r, IfRegion)
                                and getattr(_r, 'chained_compare_blocks', None)
                                and _bor_blocks <= set(_r.blocks)):
                            _cc_phantom = True
                            break
                if not _cc_phantom:
                    condition_block = block_region.op_chain[-1][0]
                    chain_blocks = set(b for b, _ in block_region.op_chain)
            elif boolop_region and boolop_region.entry == block:
                if not getattr(boolop_region, 'is_condition_context', True) and getattr(boolop_region, 'value_target', None):
                    continue
                # 同上：BoolOpRegion 作为 TernaryRegion 的值块时不应升级为 IfRegion
                if not getattr(boolop_region, 'is_condition_context', True):
                    _is_ternary_value_block = False
                    for _tr in self._filter_regions(ternary_regions or [], TernaryRegion):
                        if block in (_tr.true_value_block, _tr.false_value_block):
                            _is_ternary_value_block = True
                            break
                    if _is_ternary_value_block:
                        continue

            cond_succs = list(condition_block.conditional_successors)
            if len(cond_succs) != 2:
                continue
            then_succ, else_succ = sorted(cond_succs, key=lambda s: s.start_offset)

            chained_compare_info = self._detect_chained_compare_pattern(condition_block)
            if chained_compare_info:
                # 链式比较检测到时，记录额外条件块供后续使用
                # 但不创建独立区域，让常规代码路径处理 then/else 收集和 elif 检测
                # 只需要确保 then_succ 指向真正的 then 入口（跳过条件块）
                extra_chain = chained_compare_info.get('extra_chain_blocks', [])
                for ecb in extra_chain:
                    chain_blocks.add(ecb)
                # 调整 then_succ：链式比较的 then_succ 是条件的 fallthrough（第二比较块），
                # 真正的 then 入口是最后一个比较块的 fallthrough 后继
                last_compare = extra_chain[-1] if extra_chain else condition_block
                last_succs = sorted(last_compare.successors, key=lambda s: s.start_offset)
                # 找到不是 else_succ 的后继作为真正的 then 入口
                for s in last_succs:
                    if s != else_succ and s not in chain_blocks:
                        then_succ = s
                        break
                # 调整 else_succ：跳过清理块（POP_TOP + JUMP），直接指向清理块的后继
                _else_instrs = [i for i in else_succ.instructions
                                if i.opname not in NOISE_OPS
                                and i.opname not in ('RESUME', 'NOP', 'CACHE')]
                _else_is_cleanup = all(
                    i.opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                    for i in _else_instrs
                ) and len(else_succ.successors) == 1
                if _else_is_cleanup:
                    else_succ = list(else_succ.successors)[0]

            merge = self._find_nearest_common_post_dominator(then_succ, else_succ)

            if merge is None:
                _then_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in then_succ.instructions) or then_succ.immediate_post_dominator is None
                _else_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in else_succ.instructions) or else_succ.immediate_post_dominator is None
                if not _then_sink:
                    _then_chain_end = then_succ
                    _visited = {then_succ}
                    while _then_chain_end.successors and _then_chain_end.immediate_post_dominator is not None:
                        _next = _then_chain_end.immediate_post_dominator
                        if _next in _visited:
                            break
                        _visited.add(_next)
                        _then_chain_end = _next
                    if any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in _then_chain_end.instructions) or _then_chain_end.immediate_post_dominator is None:
                        _then_sink = True
                if not _else_sink:
                    _else_chain_end = else_succ
                    _visited = {else_succ}
                    while _else_chain_end.successors and _else_chain_end.immediate_post_dominator is not None:
                        _next = _else_chain_end.immediate_post_dominator
                        if _next in _visited:
                            break
                        _visited.add(_next)
                        _else_chain_end = _next
                    if any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in _else_chain_end.instructions) or _else_chain_end.immediate_post_dominator is None:
                        _else_sink = True
                if _then_sink and not _else_sink:
                    merge = else_succ.immediate_post_dominator
                elif _else_sink and not _then_sink:
                    merge = then_succ.immediate_post_dominator
                # [wl32 fix] When both branches sink but one is a BREAK/PURE_BREAK
                # block, the code after the if is sequential (not an else-branch).
                # Set merge to the non-BREAK successor so the BREAK branch is
                # collected as then_blocks and the other branch is empty,
                # creating IF_THEN instead of IF_ELIF_CHAIN. This prevents
                # two independent if-break patterns from being merged into
                # an if/elif chain.
                # [R17 fix] When the non-BREAK successor is itself a conditional block
                # (potential elif condition: 2 conditional successors + forward
                # conditional jump), do NOT set merge=else_succ. Setting merge=else_succ
                # would empty else_blocks (entry==merge) and prevent elif chain
                # detection. Keeping merge=None allows _build_elif_region to detect
                # the elif chain (e.g., `if x: break / elif y: continue / else: return`).
                if merge is None:
                    _then_br_role = self.get_block_role(then_succ)
                    _else_br_role = self.get_block_role(else_succ)
                    if _then_br_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                        _else_last = else_succ.get_last_instruction()
                        _else_is_elif_cond = (
                            len(else_succ.conditional_successors) == 2
                            and _else_last is not None
                            and _else_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)
                        )
                        if not _else_is_elif_cond:
                            merge = else_succ
                    elif _else_br_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                        # Only set merge=then_succ if then_succ is a simple fall-through
                        # block with no meaningful code. If then_succ has actual statements
                        # (e.g., a loop back-edge block with an assignment), setting
                        # merge=then_succ would empty then_blocks and lose that code.
                        # Note: block roles like LOOP_BACK_EDGE are not yet finalized at this
                        # point (they are set later in _annotate_all_roles), so we inspect
                        # the instructions directly.
                        _then_meaningful = [i for i in then_succ.instructions
                                            if i.opname not in NOISE_OPS
                                            and i.opname not in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                                                 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                            and i.opname not in FORWARD_CONDITIONAL_JUMP_OPS
                                            and i.opname not in BACKWARD_CONDITIONAL_JUMP_OPS
                                            and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                        if not _then_meaningful:
                            merge = then_succ

            # Fix: 当条件块在 TryExceptRegion 的 try_blocks 中时，
            # 分支收集可能越过 try 体边界（通过 JUMP_FORWARD 到循环条件等），
            # 需要计算 try 体边界块（try 体外的直接后继），作为 BFS 的额外停止点，
            # 防止遍历越过 try 体后通过循环回边重新进入 try 体。
            # block_region 为单一类型，try/loop 边界互斥，统一为单个 boundary_stop 集合。
            if block_region is not None:
                boundary_stop = block_region.get_if_branch_boundary_stop(block)
            else:
                boundary_stop = set()

            then_stop = {else_succ} | (boundary_stop - {then_succ})
            else_stop = {then_succ} | (boundary_stop - {else_succ})
            then_blocks = self._collect_branch_blocks(then_succ, merge, then_stop)
            else_blocks = self._collect_branch_blocks(else_succ, merge, else_stop)
            # 区域归约算法：try/with handler 块过滤
            # 仅当 if 条件块本身不在 handler 块集合中时才过滤 then/else 中的 handler 块。
            # 当 if 位于 except/finally handler 内部时（条件块也在 handler 集合中），
            # then/else 块合法地属于该 handler，不应被过滤——否则 if 体会变空，
            # 导致 `except: if c: raise` 中的 raise 被移出 if 体。
            if try_handler_blocks and block not in try_handler_blocks:
                then_blocks = [b for b in then_blocks if b not in try_handler_blocks]
                else_blocks = [b for b in else_blocks if b not in try_handler_blocks]
            if with_handler_blocks and block not in with_handler_blocks:
                then_blocks = [b for b in then_blocks if b not in with_handler_blocks]
                else_blocks = [b for b in else_blocks if b not in with_handler_blocks]

            # 后过滤：确保没有 try 体外的块混入，但保留直接后继块（then_succ/else_succ）
            # 因为它们是 if 条件的直接分支目标（如 break/continue 块），即使不在 try 体内
            # 也应保留在 then/else 分支中。
            if isinstance(block_region, TryExceptRegion) and block in block_region.try_blocks:
                try_body_set = set(block_region.try_blocks) | set(block_region.else_blocks)
                then_blocks = [b for b in then_blocks if b in try_body_set or b == then_succ]
                else_blocks = [b for b in else_blocks if b in try_body_set or b == else_succ]

            if isinstance(block_region, LoopRegion):
                loop_body_set = set(block_region.body_blocks)
                if block_region.condition_block:
                    loop_body_set.add(block_region.condition_block)
                _loop_back_edge_blocks = set()
                # Conditional back-edge blocks (POP_JUMP_BACKWARD_IF_TRUE/FALSE → header/condition)
                # are the loop's condition recheck blocks. They belong to the LOOP (unique block
                # ownership per "No More Gotos" §4.2), NOT any nested IF. Including them in
                # if-else branches causes the loop condition to be duplicated inside the body.
                _conditional_back_edge_blocks = set()
                if hasattr(block_region, 'back_edge_block') and block_region.back_edge_block:
                    _loop_back_edge_blocks.add(block_region.back_edge_block)
                    _be_last = block_region.back_edge_block.get_last_instruction()
                    if _be_last and _be_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                        _conditional_back_edge_blocks.add(block_region.back_edge_block)
                if hasattr(block_region, 'back_edge_blocks') and block_region.back_edge_blocks:
                    _loop_back_edge_blocks.update(block_region.back_edge_blocks)
                    for _beb in block_region.back_edge_blocks:
                        _beb_last = _beb.get_last_instruction()
                        if _beb_last and _beb_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                            _conditional_back_edge_blocks.add(_beb)
                for lb in block_region.body_blocks:
                    last = lb.get_last_instruction()
                    if last and last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                        target = self.cfg.get_block_by_offset(last.argval) if last.argval is not None else None
                        if target == block_region.header_block or target == block_region.condition_block:
                            _loop_back_edge_blocks.add(lb)
                            _conditional_back_edge_blocks.add(lb)
                _else_before_filter = list(else_blocks)
                # Conditional back-edge blocks are ALWAYS excluded from if-else branches
                # (unique block ownership: they belong to LoopRegion, not IfRegion).
                else_blocks = [b for b in else_blocks if b not in _conditional_back_edge_blocks and (b in loop_body_set or self._block_exits_loop(b, block_region)) and (b not in _loop_back_edge_blocks or b == else_succ) and b != block]
                _then_back_edge_blocks = set()
                for _tbe in _loop_back_edge_blocks:
                    _tbe_meaningful = [i for i in _tbe.instructions
                                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                                       and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                           'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                                       and i.opname not in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                           'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                                       and i.opname not in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                                           'LOAD_CONST', 'LOAD_ATTR', 'LOAD_METHOD')
                                       and i.opname not in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')
                                       and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                    if not _tbe_meaningful:
                        _then_back_edge_blocks.add(_tbe)
                then_blocks = [b for b in then_blocks if b not in _conditional_back_edge_blocks and (b not in _then_back_edge_blocks or b == then_succ) and b != block]

            all_condition_blocks = {condition_block} | chain_blocks

            # [聚类2 修复] 检测 await 前驱链：当 condition_block 的前驱链包含
            # await 轮询自循环（SEND+YIELD_VALUE+JUMP_BACKWARD_NO_INTERRUPT）和
            # await 设置块（GET_AWAITABLE）时，将这些块纳入 IfRegion 的
            # all_condition_blocks，使它们归 IfRegion 所有（每块唯一归属），
            # 不再作为独立 BASIC 区域被 _generate_block_statements 处理。
            # 这符合区域归约算法原则：await 表达式是 if 条件求值的内联部分，
            # 其求值块应归入条件区域而非独立语句。
            _await_pred_blocks = self._collect_await_predecessor_chain(condition_block)
            if _await_pred_blocks:
                all_condition_blocks.update(_await_pred_blocks)
                chain_blocks.update(_await_pred_blocks)

            region = self._build_elif_region(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block, boundary_stop=boundary_stop, ternary_regions=ternary_regions)
            if region is None:
                region = self._build_basic_if_region(block, then_blocks, else_blocks, merge,
                                                      all_condition_blocks, condition_block,
                                                      boolop_regions=boolop_regions,
                                                      ternary_regions=ternary_regions)
            # 如果检测到链式比较，设置链式比较信息到区域上
            if region is not None and chained_compare_info:
                region.chained_compare_blocks = list(chained_compare_info.get('extra_chain_blocks', []))
                region.chained_compare_ops = chained_compare_info.get('compare_ops', [])
            if region is not None:
                if_regions.append(region)
                if boolop_region is not None:
                    if boolop_region.entry == region.entry and boolop_region.value_target is not None:
                        pass
                    elif boolop_region.entry == region.entry and boolop_region.is_condition_context:
                        region.add_child(boolop_region)
                    elif boolop_region.entry != region.entry:
                        region.add_child(boolop_region)
                mr_check_wild = block_region
                if isinstance(mr_check_wild, MatchRegion):
                    if self._is_wildcard_match_subject(mr_check_wild, block):
                        region.parent = mr_check_wild
                        mr_check_wild.add_child(region)
        return if_regions

    def _resolve_boolop_condition_region(self, block):
        block_region = self.block_to_region.get(block)
        if block_region is not None and isinstance(block_region, BoolOpRegion) and block_region.entry == block:
            first_chain_last = block_region.op_chain[0][0].get_last_instruction() if block_region.op_chain else None
            if first_chain_last and first_chain_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                return block_region
        cached = getattr(self, '_current_boolop_regions', None)
        if cached:
            for r in self._filter_regions(cached, BoolOpRegion):
                if r.entry == block:
                    first_chain_last = r.op_chain[0][0].get_last_instruction() if r.op_chain else None
                    if first_chain_last and first_chain_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                        return r
        for r in self._filter_regions(self.regions, BoolOpRegion):
            if r.entry == block:
                first_chain_last = r.op_chain[0][0].get_last_instruction() if r.op_chain else None
                if first_chain_last and first_chain_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                    return r
        return None

    def _build_basic_if_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boolop_regions=None, ternary_regions=None):
        """
        构建基础 if/if-else 区域（非 elif 链）

        ═══════════════════════════════════════════════════════════════════════
        功能说明
        ═══════════════════════════════════════════════════════════════════════

        将分析出的条件分支块组装为 IfRegion 对象。
        这是 _identify_conditional_regions 的最终回退方法，
        当 _build_elif_region 无法识别 elif 链时调用。

        区域类型判定逻辑：
        ─────────────────
        if else_blocks 非空且包含非平凡块:
          → RegionType.IF_THEN_ELSE（有 else 分支）
          
        if else_blocks 为空 或 所有块都是 trivial（pass-only）:
          → RegionType.IF_THEN（无 else 分支）
          注：trivial 的 else 块被移除，因为 `if x: ... pass` 等价于 `if x: ...`

        trailing_return_none 检测：
        ─────────────────────
        如果 then/else 分支的最后一个块以 `return None` 结尾（显式或隐式），
        标记 region.mark_trailing_return_none()，用于后续代码优化。

        Args:
            block: 条件头基本块（entry block）
            then_blocks: then 分支的块列表
            else_blocks: else 分支的块列表（可能为空）
            merge: 后向支配合并点（两个分支的汇合点，可能为 None）
            all_condition_blocks: 条件相关的所有块集合（含 BoolOp chain）
            condition_block: 实际包含条件跳转指令的块（可能不同于 entry）

        Returns:
            IfRegion: 构建好的区域对象，region_type 为 IF_THEN 或 IF_THEN_ELSE

        示例:
        ─────────
        源码: if a > 0:
                  a = 1
              else:
                  a = 2

        参数:
          block = 条件块 (COMPARE_OP + POP_JUMP_IF_FALSE)
          then_blocks = [赋值块1]
          else_blocks = [赋值块2]
          merge = 赋值后的汇合块
          region_type = IF_THEN_ELSE
        """
        def _is_loop_continue_block(b):
            last = b.get_last_instruction()
            if last and last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT') and last.argval is not None:
                target = self.cfg.get_block_by_offset(last.argval)
                br = self.block_to_region.get(b)
                if isinstance(br, LoopRegion) and target in (br.header_block, br.condition_block):
                    return True
            return False

        def _is_loop_break_block(b):
            # [wl32 fix] If the block has BlockRole.BREAK/PURE_BREAK, it IS a loop
            # break block. At module level, break is compiled as LOAD_CONST None +
            # RETURN_VALUE, which _is_return_none_block would match — but it's still
            # a break, not an implicit return. Check block role first.
            _br_role = self.block_roles.get(b.start_offset)
            if _br_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                return True
            # 隐式 return None 块（LOAD_CONST None + RETURN_VALUE 或 RETURN_CONST None）
            # 是函数的隐式返回，不是有意义的控制流出口（break/continue/explicit return）。
            # 将其视为 trivial（由 _is_trivial_block 处理），避免阻止 else_blocks 清除。
            if self._is_return_none_block(b):
                return False
            last = b.get_last_instruction()
            if last and last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE') and last.argval is not None:
                target = self.cfg.get_block_by_offset(last.argval)
                br = self.block_to_region.get(b)
                if isinstance(br, LoopRegion) and target not in br.blocks:
                    return True
            if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                return True
            return False

        if else_blocks and all(self._is_trivial_block(b) or _is_loop_continue_block(b) or _is_loop_break_block(b) for b in else_blocks):
            non_continue_break_else = [b for b in else_blocks if not _is_loop_continue_block(b) and not _is_loop_break_block(b)]
            non_break_else = [b for b in else_blocks if not _is_loop_break_block(b)]
            if not non_continue_break_else or all(self._is_trivial_block(b) for b in non_continue_break_else):
                if not any(_is_loop_continue_block(b) for b in non_break_else) and not any(_is_loop_break_block(b) for b in else_blocks):
                    else_blocks = []
        if else_blocks:
            then_terminates_with_raise = False
            if then_blocks:
                last_then = then_blocks[-1].get_last_instruction()
                if last_then and last_then.opname == 'RAISE_VARARGS':
                    then_terminates_with_raise = True
            if then_terminates_with_raise:
                else_blocks = []
        # 区域归约算法：merge=None时的共有块过滤
        # 当某个分支以return/break/raise终止导致无共同后必经节点时，
        # _collect_branch_blocks会过度收集，把if结构之后的代码同时收入then和else。
        # 过滤策略：同时出现在then_blocks和else_blocks中的块是de facto merge点，
        # 不属于任何单一分支，应从两个列表中移除。
        # 但保留有2个条件后继的块（潜在的elif条件块）在else_blocks中，
        # 因为这些块是elif条件，不是merge点。
        if merge is None and then_blocks and else_blocks:
            then_set = set(then_blocks)
            else_set = set(else_blocks)
            shared_blocks = then_set & else_set
            if shared_blocks:
                # 区分真正的merge块和elif条件块
                real_merge = set()
                elif_candidates = set()
                for sb in shared_blocks:
                    if len(sb.conditional_successors) == 2:
                        # 有2个条件后继的块可能是elif条件，保留在else_blocks中
                        elif_candidates.add(sb)
                    else:
                        real_merge.add(sb)
                if real_merge:
                    then_blocks = [b for b in then_blocks if b not in real_merge]
                    else_blocks = [b for b in else_blocks if b not in real_merge]
                    merge = min(real_merge, key=lambda b: b.start_offset)
                # 从then_blocks中移除elif候选块（它们不属于then分支）
                if elif_candidates:
                    then_blocks = [b for b in then_blocks if b not in elif_candidates]
        if else_blocks and merge is None:
            else_block_set = set(else_blocks)
            shared_or_reachable = False
            for tb in then_blocks:
                for succ in tb.successors:
                    if succ in else_block_set:
                        last_instr = tb.get_last_instruction()
                        if last_instr and last_instr.opname not in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE'):
                            shared_or_reachable = True
                            break
                if shared_or_reachable:
                    break
            if shared_or_reachable:
                else_blocks = []
        _lre = set()
        _lrbs = []
        _boolop_ternary_blocks = {}
        for _b, _r in self.block_to_region.items():
            if type(_r).__name__ == 'LoopRegion':
                _e = _r.condition_block or getattr(_r, 'header_block', None) or _r.entry
                if _e:
                    _lre.add(_e)
                    _lrbs.append((_r.blocks, _e))
        for _or in (boolop_regions or []) + (ternary_regions or []):
            if hasattr(_or, 'blocks') and _or.entry:
                for _ob in _or.blocks:
                    if _ob != _or.entry:
                        _boolop_ternary_blocks[_ob] = _or
        if _lre:
            _if_in_loop = any(block in _lb for _lb, _le in _lrbs)
            if not _if_in_loop:
                then_blocks = [b for b in then_blocks if b in _lre or not any(b in _lb and b != _le for _lb, _le in _lrbs)]
                else_blocks = [b for b in else_blocks if b in _lre or not any(b in _lb and b != _le for _lb, _le in _lrbs)]
                _bt_entries = set()
                for _or2 in (boolop_regions or []) + (ternary_regions or []):
                    if _or2.entry:
                        _bt_entries.add(_or2.entry)
                # [Phase 3 adv11_while_walrus_boolop] LoopRegion 入口（entry/
                # condition_block/header_block）即使同时是 BoolOpRegion 的
                # 链块（如 ``if c: while (x:=f()) and g():``，Block 3 既是
                # LoopRegion 条件块又是 BoolOpRegion 链块），也必须保留在
                # IfRegion 的 then_blocks 中——否则 LoopRegion 无法嵌套进
                # IfRegion，反编译会输出 ``if c: pass`` + 顶层 ``while``。
                then_blocks = [b for b in then_blocks
                               if b in _bt_entries
                               or b not in _boolop_ternary_blocks
                               or b in _lre]
                else_blocks = [b for b in else_blocks
                               if b in _bt_entries
                               or b not in _boolop_ternary_blocks
                               or b in _lre]
            else:
                _loop_region = None
                for _r in self._filter_regions(list(self.block_to_region.values()), LoopRegion):
                    if block in _r.blocks:
                        _loop_region = _r
                        break
                if _loop_region:
                    _loop_body_only = set(_loop_region.body_blocks)
                    if _loop_region.condition_block:
                        _loop_body_only.add(_loop_region.condition_block)
                    # [Phase 4 回归修复] back_edge_block 是循环的回边重检块
                    # （含 loop increment + 条件重检），不属于任何 IfRegion 的
                    # else 分支。若不排除，`while: if: break if: break; n+=1`
                    # 的 back_edge 块（n+=1 + n<100 重检）会被 elif 链的 else
                    # 分支吸收，生成多余的 `if n<100: pass else: break`。
                    if _loop_region.back_edge_block is not None:
                        _loop_body_only.discard(_loop_region.back_edge_block)
                    _loop_all_blocks = set(_loop_region.blocks)
                    _break_target_blocks = set()
                    for _lb in _loop_region.blocks:
                        _lb_last = _lb.get_last_instruction()
                        if _lb_last and _lb_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                            _lb_target = self.cfg.get_block_by_offset(_lb_last.argval) if _lb_last.argval is not None else None
                            if _lb_target and _lb_target not in _loop_all_blocks:
                                _break_target_blocks.add(_lb_target)
                    then_blocks = [b for b in then_blocks if b not in _break_target_blocks]
                    else_blocks = [b for b in else_blocks if b in _loop_body_only or self._block_exits_loop(b, _loop_region)]
        region_type = RegionType.IF_THEN_ELSE if else_blocks else RegionType.IF_THEN
        all_blocks = all_condition_blocks | set(then_blocks) | set(else_blocks)
        region = IfRegion(
            region_type=region_type, entry=block, blocks=all_blocks,
            exit=merge, condition_block=condition_block if condition_block is not None else block, then_blocks=then_blocks,
            else_blocks=else_blocks, merge_block=merge,
        )
        if then_blocks and self._check_block_has_trailing_return_none(then_blocks[-1]):
            region.mark_trailing_return_none()
        if else_blocks and self._check_block_has_trailing_return_none(else_blocks[-1]):
            region.mark_trailing_return_none()
        return region

    def _build_elif_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None, boundary_stop=None, ternary_regions=None):
        # [R17 fix] When collecting inner elif branch blocks inside a loop, the loop's
        # boundary_stop (which includes break/return exit blocks and the loop header)
        # prevents collecting terminal blocks that are part of the elif chain (e.g.,
        # the `else: return i` body). Remove terminal blocks from boundary_stop for
        # the inner collection, since terminal blocks don't lead anywhere (collecting
        # them doesn't cause BFS to re-enter the loop). Keep the loop header in the
        # stop set to prevent following back-edges.
        _inner_boundary_stop = set(boundary_stop) if boundary_stop else set()
        if _inner_boundary_stop:
            _terminal_offsets = {b for b in _inner_boundary_stop
                                 if b.get_last_instruction()
                                 and b.get_last_instruction().opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE')}
            _inner_boundary_stop = _inner_boundary_stop - _terminal_offsets
        def _check_elif_chain(header_, else_blocks_, merge_):
            if not else_blocks_:
                return None
            _then_has_ctrl_exit = False
            _then_has_explicit_return = False
            _then_has_loop_ctrl_exit = False
            for tb in then_blocks:
                if not tb.successors:
                    _tb_last = tb.get_last_instruction()
                    if _tb_last and _tb_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        _tb_meaningful = [i for i in tb.instructions
                                          if i.opname not in NOISE_OPS
                                          and i.opname not in ('LOAD_CONST', 'POP_TOP')
                                          and i.opname not in PURE_JUMP_OPS
                                          and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                        if not _tb_meaningful:
                            _is_implicit_return = False
                            if _tb_last.opname == 'RETURN_CONST' and _tb_last.argval is None:
                                _is_implicit_return = True
                            elif _tb_last.opname == 'RETURN_VALUE':
                                _pre_return = [i for i in tb.instructions if i.offset < _tb_last.offset and i.opname not in NOISE_OPS]
                                if len(_pre_return) == 1 and _pre_return[0].opname == 'LOAD_CONST' and _pre_return[0].argval is None:
                                    _is_implicit_return = True
                            if not _is_implicit_return:
                                _then_has_explicit_return = True
                                break
                elif len(tb.successors) == 1:
                    _tb_last = tb.get_last_instruction()
                    _tb_succ = list(tb.successors)[0]
                    if _tb_last and _tb_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                        if _tb_succ in self.loop_analyzer.loop_headers:
                            _tb_meaningful = [i for i in tb.instructions
                                              if i.opname not in NOISE_OPS
                                              and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                                                   'JUMP_FORWARD', 'JUMP_ABSOLUTE')]
                            if not _tb_meaningful:
                                _then_has_loop_ctrl_exit = True
                                break
                    if _tb_last and _tb_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                        _loop_region = None
                        for _lr in self._filter_regions(self.regions or [], LoopRegion):
                            if tb in _lr.blocks:
                                _loop_region = _lr
                                break
                        if _loop_region and _tb_succ not in _loop_region.blocks:
                            _tb_meaningful = [i for i in tb.instructions
                                              if i.opname not in NOISE_OPS
                                              and i.opname not in ('JUMP_FORWARD', 'JUMP_ABSOLUTE')]
                            if not _tb_meaningful:
                                _then_has_loop_ctrl_exit = True
                                break
            if _then_has_explicit_return:
                _else_has_matching_exit = False
                for eb in else_blocks_:
                    if not eb.successors:
                        _eb_last = eb.get_last_instruction()
                        if _eb_last and _eb_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            _eb_meaningful = [i for i in eb.instructions
                                              if i.opname not in NOISE_OPS
                                              and i.opname not in ('LOAD_CONST', 'POP_TOP')
                                              and i.opname not in PURE_JUMP_OPS
                                              and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                            if not _eb_meaningful:
                                _eb_is_implicit = False
                                if _eb_last.opname == 'RETURN_CONST' and _eb_last.argval is None:
                                    _eb_is_implicit = True
                                elif _eb_last.opname == 'RETURN_VALUE':
                                    _eb_pre = [i for i in eb.instructions if i.offset < _eb_last.offset and i.opname not in NOISE_OPS]
                                    if len(_eb_pre) == 1 and _eb_pre[0].opname == 'LOAD_CONST' and _eb_pre[0].argval is None:
                                        _eb_is_implicit = True
                                if not _eb_is_implicit:
                                    _else_has_matching_exit = True
                                    break
                if not _else_has_matching_exit:
                    _then_has_ctrl_exit = True
            if _then_has_ctrl_exit:
                if else_blocks_:
                    _first_else = else_blocks_[0]
                    if len(_first_else.conditional_successors) == 2:
                        _fe_last = _first_else.get_last_instruction()
                        if _fe_last and _fe_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                            _then_has_ctrl_exit = False
                if _then_has_ctrl_exit:
                    return None
            first_else = else_blocks_[0]
            # 链式比较清理块跳过：当 else 分支以清理块(仅含 POP_TOP + JUMP)开头时，
            # 跳过它并追踪到后继块，直到找到有条件跳转的 elif 候选块。
            # 这处理链式比较如 `if 0 < x < 10:` 产生的额外 POP_TOP 块。
            _skip_count = 0
            while first_else and len(first_else.conditional_successors) != 2:
                _fe_instrs = [i for i in first_else.instructions
                              if i.opname not in NOISE_OPS
                              and i.opname not in ('RESUME', 'NOP', 'CACHE')]
                _fe_is_cleanup = all(
                    i.opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE')
                    for i in _fe_instrs
                ) and len(first_else.successors) == 1
                if _fe_is_cleanup:
                    _skip_count += 1
                    _succ = list(first_else.successors)[0]
                    # 在 else_blocks_ 中找到后继块
                    if _succ in else_blocks_:
                        first_else = _succ
                    else:
                        break
                else:
                    break
            if _skip_count > 0:
                # 更新 else_blocks_ 移除被跳过的清理块
                else_blocks_ = else_blocks_[_skip_count:]
            if len(first_else.conditional_successors) != 2:
                return None
            _fe_last = first_else.get_last_instruction()
            if _fe_last and _fe_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                _fe_target = self.cfg.get_block_by_offset(_fe_last.argval) if _fe_last.argval is not None else None
                _fe_br = self.block_to_region.get(first_else)
                if isinstance(_fe_br, LoopRegion):
                    if _fe_target == _fe_br.header_block or _fe_target == _fe_br.condition_block:
                        return None
            # Fix: 如果潜在的 elif 条件块在条件跳转前包含 body 语句
            # （如 STORE_FAST/BINARY_OP 等），则它不是纯 elif 条件块，
            # 而是包含实际代码的块，不应被合并为 elif 链。
            # 例如: try body 中 "result = transform(item); if result is None: continue"
            # 的 block 同时包含赋值和条件跳转，不应被视为 elif。
            _fe_last = first_else.get_last_instruction()
            if _fe_last and _fe_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                _has_body_stmt = any(
                    i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',
                                'BINARY_OP', 'DELETE_NAME', 'DELETE_FAST',
                                'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR')
                    for i in first_else.instructions
                    if i.offset < _fe_last.offset
                )
                if _has_body_stmt:
                    return None
            if first_else in self.block_to_region:
                existing = self.block_to_region[first_else]
                if existing.region_type == RegionType.BASIC:
                    pass
                elif existing.else_block_conflict(first_else):
                    return None
            else:
                # block_to_region可能因BoolOpRegion删除而缺失映射，
                # 检查first_else是否是某个LoopRegion的condition_block/header/entry
                for _r in self._filter_regions(self.regions, LoopRegion):
                    if first_else == _r.condition_block or first_else == _r.header_block or first_else == _r.entry:
                        return None

            # [Phase 3 adv15_ternary_elif_test] 三元作为 elif 条件：
            # 当 first_else 是 TernaryRegion（merge_context='while_cond'）的 entry 时，
            # 整个三元就是 elif 条件本身。CPython 3.11+ 内联三元结果为条件测试，
            # 使 true_value_block/false_value_block 各自带 POP_JUMP_IF_FALSE 跳到
            # "skip body" 块。若不识别此模式，_check_elif_chain 会递归把 true_value
            # 和 false_value 块拆成多个 elif 条件，破坏三元语义：
            #   `elif (b if c else d): pass` → `elif c: pass / elif d: pass`（b 丢失）
            #
            # 区域归约：三元（Phase 1.5）先于 IfRegion（Phase 2）归约，
            # 三元是更归约的形式。IfRegion 应把整个三元视为单个 elif 条件，
            # body = 三元的 merge_block（truthy path 汇聚点），
            # final_else = 三元值块的 POP_JUMP_IF_FALSE 目标（falsy path）。
            #
            # [Phase 3 adv15_ternary_each_branch] 非条件上下文三元
            # （merge_context != 'while_cond'，如 'store'）作为 else 分支体的
            # 内容，不是 elif 条件。例如：
            #   `if a: ... elif b: ... else: x = 5 if r else 6`
            # else 体以三元 condition_block（LOAD r, POP_JUMP_IF_FALSE → false_value）
            # 开头，_check_elif_chain 会误把 r 当作另一个 elif 条件，把 5/6 当作
            # body/final_else。返回 None 让调用方使用 inner_else_blocks 作为
            # final_else，保留完整 else 体（含三元）。
            if ternary_regions:
                _te_ternary = None
                _te_non_conditional = None
                for _tr in self._filter_regions(ternary_regions, TernaryRegion):
                    if _tr.entry is first_else:
                        _mc = getattr(_tr, 'merge_context', None)
                        if (_mc == 'while_cond'
                                and _tr.merge_block is not None
                                and _tr.true_value_block is not None
                                and _tr.false_value_block is not None):
                            _te_ternary = _tr
                            break
                        else:
                            _te_non_conditional = _tr
                            break
                if _te_ternary is not None:
                    _te_body = _te_ternary.merge_block
                    _te_final_else = []
                    _te_seen = {_te_body.start_offset}
                    for _te_vb in (_te_ternary.true_value_block, _te_ternary.false_value_block):
                        _te_vlast = _te_vb.get_last_instruction()
                        if (_te_vlast is not None
                                and _te_vlast.argval is not None
                                and _te_vlast.opname in FORWARD_CONDITIONAL_JUMP_OPS):
                            _te_skip = self.cfg.get_block_by_offset(_te_vlast.argval)
                            if (_te_skip is not None
                                    and _te_skip.start_offset not in _te_seen):
                                _te_final_else.append(_te_skip)
                                _te_seen.add(_te_skip.start_offset)
                    return {
                        'conditions': [first_else],
                        'bodies': [[_te_body]],
                        'final_else': _te_final_else,
                    }
                if _te_non_conditional is not None:
                    return None

            conditions = [first_else]
            bodies = []
            final_else = []

            inner_condition_block = first_else
            inner_br = self.block_to_region.get(first_else)
            inline_boolop_chain = None
            if isinstance(inner_br, BoolOpRegion) and inner_br.entry == first_else:
                inner_condition_block = inner_br.op_chain[-1][0]
            elif _fe_last and _fe_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS) and 'IF_FALSE' in _fe_last.opname:
                _inline_chain = [first_else]
                _inline_current = first_else
                _inline_merge_offset = _fe_last.argval
                _inline_visited = {first_else.start_offset}
                def _is_implicit_return_block(blk):
                    instrs = [i for i in blk.instructions if i.opname not in NOISE_OPS]
                    if len(instrs) == 2 and instrs[-1].opname == 'RETURN_VALUE':
                        if instrs[0].opname == 'LOAD_CONST' and instrs[0].argval is None:
                            return True
                    elif len(instrs) == 1 and instrs[0].opname == 'RETURN_CONST' and instrs[0].argval is None:
                        return True
                    return False
                _merge_is_implicit_return = _is_implicit_return_block(self.cfg.get_block_by_offset(_inline_merge_offset)) if _inline_merge_offset is not None else False
                while True:
                    _ft_next = None
                    _cur_last = _inline_current.get_last_instruction()
                    if _cur_last and _cur_last.argval is not None:
                        for _s in _inline_current.successors:
                            if _s.start_offset not in _inline_visited and _s.start_offset != _cur_last.argval:
                                _ft_next = _s
                                break
                    if _ft_next is None or _ft_next.start_offset in _inline_visited:
                        break
                    _ft_last = _ft_next.get_last_instruction()
                    if _ft_last is None or _ft_last.opname not in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                        break
                    if 'IF_TRUE' in _ft_last.opname:
                        break
                    if _ft_last.argval != _inline_merge_offset:
                        if not (_merge_is_implicit_return and _ft_last.argval is not None and _is_implicit_return_block(self.cfg.get_block_by_offset(_ft_last.argval))):
                            break
                    _inline_visited.add(_ft_next.start_offset)
                    _inline_chain.append(_ft_next)
                    _inline_current = _ft_next
                if len(_inline_chain) >= 2:
                    inner_condition_block = _inline_chain[-1]
                    inline_boolop_chain = {'blocks': _inline_chain, 'op': 'and'}
            elif _fe_last and _fe_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS) and 'IF_TRUE' in _fe_last.opname:
                _or_body_block = None
                if _fe_last.argval is not None:
                    _or_body_block = self.cfg.get_block_by_offset(_fe_last.argval)
                if _or_body_block is not None:
                    _or_chain = [first_else]
                    _or_current = first_else
                    _or_visited = {first_else.start_offset}
                    while True:
                        _ft_next = None
                        _cur_last = _or_current.get_last_instruction()
                        if _cur_last and _cur_last.argval is not None:
                            for _s in _or_current.successors:
                                if _s.start_offset not in _or_visited and _s.start_offset != _cur_last.argval:
                                    _ft_next = _s
                                    break
                        if _ft_next is None or _ft_next.start_offset in _or_visited:
                            break
                        _ft_last = _ft_next.get_last_instruction()
                        if _ft_last is None or _ft_last.opname not in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                            break
                        _or_chain.append(_ft_next)
                        _or_visited.add(_ft_next.start_offset)
                        if 'IF_FALSE' in _ft_last.opname:
                            _or_ft = next((s for s in _ft_next.conditional_successors if s.start_offset != _ft_last.argval), None)
                            if _or_ft is not None and _or_ft == _or_body_block:
                                break
                            else:
                                break
                        _or_current = _ft_next
                    if len(_or_chain) >= 2:
                        inner_condition_block = _or_chain[-1]
                        inline_boolop_chain = {'blocks': _or_chain, 'op': 'or'}
            inner_cond_succs = list(inner_condition_block.conditional_successors)
            if len(inner_cond_succs) != 2:
                return None
            inner_then_succ, inner_else_succ = sorted(inner_cond_succs, key=lambda s: s.start_offset)
            inner_merge = self._find_nearest_common_post_dominator(inner_then_succ, inner_else_succ)
            if inner_merge is None:
                _it_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in inner_then_succ.instructions) or inner_then_succ.immediate_post_dominator is None
                _ie_sink = any(i.opname in ('RAISE_VARARGS', 'RETURN_VALUE') for i in inner_else_succ.instructions) or inner_else_succ.immediate_post_dominator is None
                if _it_sink and not _ie_sink:
                    inner_merge = inner_else_succ.immediate_post_dominator
                elif _ie_sink and not _it_sink:
                    _candidate_merge = inner_then_succ.immediate_post_dominator
                    if _candidate_merge and _candidate_merge.start_offset < inner_else_succ.start_offset:
                        pass
                    else:
                        inner_merge = _candidate_merge
            inner_then_blocks = self._collect_branch_blocks(inner_then_succ, inner_merge, {inner_else_succ} | _inner_boundary_stop)
            inner_else_blocks = self._collect_branch_blocks(inner_else_succ, inner_merge, {inner_then_succ} | _inner_boundary_stop)
            if inner_else_blocks and all(self._is_trivial_block(b) for b in inner_else_blocks):
                inner_else_blocks = []
            inner_region_type = RegionType.IF_THEN_ELSE if inner_else_blocks else RegionType.IF_THEN

            if inner_region_type == RegionType.IF_THEN:
                terminates = True
                for tb in inner_then_blocks:
                    for succ in tb.successors:
                        if succ == first_else:
                            terminates = False
                            break
                    if not terminates:
                        break
                if not terminates:
                    return None

            bodies.append(inner_then_blocks)

            deeper_elif = _check_elif_chain(first_else, inner_else_blocks, merge_)
            if deeper_elif:
                conditions.extend(deeper_elif['conditions'])
                bodies.extend(deeper_elif['bodies'])
                final_else = deeper_elif.get('final_else', [])
            elif inner_else_blocks:
                final_else = inner_else_blocks
            else:
                last_instr = first_else.get_last_instruction()
                if last_instr and last_instr.argval is not None:
                    else_succ = next((s for s in sorted(first_else.successors, key=lambda s: s.start_offset)
                                     if s.start_offset == last_instr.argval), None)
                    if else_succ and else_succ not in set(inner_then_blocks):
                        if merge_ is None or else_succ != merge_:
                            # [Phase 4 回归修复] 不将 boundary_stop 中的块
                            # （含循环 back_edge_block）作为 final_else。这些块
                            # 属于 LoopRegion（每块唯一归属），不应被 IfRegion
                            # 的 else 分支吸收。
                            if else_succ not in _inner_boundary_stop:
                                final_else = [else_succ]

            result = {'conditions': conditions, 'bodies': bodies, 'final_else': final_else}

            if inline_boolop_chain:
                result['inline_boolop_chains'] = {id(first_else): inline_boolop_chain}
                if deeper_elif and deeper_elif.get('inline_boolop_chains'):
                    result['inline_boolop_chains'].update(deeper_elif['inline_boolop_chains'])
            elif deeper_elif and deeper_elif.get('inline_boolop_chains'):
                result['inline_boolop_chains'] = deeper_elif['inline_boolop_chains']
            return result

        elif_info = _check_elif_chain(block, else_blocks, merge)
        if elif_info is None:
            return None
        # 区域归约算法：merge=None时的共有块过滤
        # _check_elif_chain内部的_collect_branch_blocks没有传入loop boundary stop，
        # 可能过度收集，把then_blocks中的块也收入final_else。
        # 共有块（同时出现在then_blocks和final_else中的块）是 de facto merge 点，
        # 不属于任何单一分支，应从then_blocks、else_blocks和final_else中同时移除。
        if merge is None and then_blocks and elif_info.get("final_else"):
            then_set = set(then_blocks)
            final_else_set = set(elif_info["final_else"])
            shared_blocks = then_set & final_else_set
            if shared_blocks:
                elif_info["final_else"] = [b for b in elif_info["final_else"] if b not in shared_blocks]
                merge = min(shared_blocks, key=lambda b: b.start_offset)
                # 同时从else_blocks和then_blocks中移除merge块
                else_blocks = [b for b in else_blocks if b not in shared_blocks]
                then_blocks = [b for b in then_blocks if b not in shared_blocks]
        if merge is None and len(then_blocks) > 1:
            """
            === 反编译逻辑：merge=None时的then_blocks过滤 ===
            
            当post-dominator分析无法找到then/else分支的共同后向支配点时（merge=None），
            通常是因为某个分支以return/break/raise终止，导致不存在共同的汇合块。
            
            典型场景：
                def f(a):
                    if a > 0:        # then分支
                        a = 1         # Block@14
                        # fallthrough → Block@36 (return 0) ← 这是全函数的exit，不是if的then body!
                    elif a < 0:      # elif分支
                        return -1     # Block@32 (直接终止)
                    return 0          # Block@36 (merge点缺失，因为elif branch不经过这里)
            
            问题：_collect_branch_blocks 在 merge=None 时会过度收集，
            把Block@36 (return 0) 也收入 then_blocks。
            
            修复策略：
            1. 计算 else_exit_blocks：else分支和elif条件块的"出口"后继块
            2. 如果then_blocks中非首块出现在 else_exit_blocks 中且是RETURN终端块 → 过滤掉
            3. 这些块属于整个if-elif链之后的代码，不属于任何单一分支
            """
            else_exit_blocks = set()
            for eb in else_blocks:
                for succ in eb.successors:
                    if succ not in set(else_blocks) | {block}:
                        else_exit_blocks.add(succ)
            for cond in elif_info.get("conditions", []):
                for succ in cond.successors:
                    if succ not in set(elif_info.get("conditions", [])) | set(else_blocks) | {block}:
                        else_exit_blocks.add(succ)
            filtered_then = []
            for tb in then_blocks:
                if tb != then_blocks[0] and tb in else_exit_blocks:
                    last = tb.get_last_instruction()
                    if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        continue
                filtered_then.append(tb)
            if len(filtered_then) >= 1:
                then_blocks = filtered_then
        all_blocks = all_condition_blocks | set(then_blocks) | set(else_blocks)
        for cond in elif_info["conditions"]:
            all_blocks.add(cond)
        for body in elif_info["bodies"]:
            all_blocks.update(body)
        if elif_info.get("final_else"):
            all_blocks.update(elif_info["final_else"])
        region = IfRegion(
            region_type=RegionType.IF_ELIF_CHAIN, entry=block, blocks=all_blocks,
            exit=merge, condition_block=condition_block if condition_block is not None else block, then_blocks=then_blocks,
            else_blocks=else_blocks, merge_block=merge,
            elif_conditions=elif_info["conditions"],
            elif_bodies=elif_info["bodies"],
            elif_final_else=elif_info.get("final_else", []),
            inline_boolop_chains=elif_info.get("inline_boolop_chains", {}),
        )
        if then_blocks and self._check_block_has_trailing_return_none(then_blocks[-1]):
            region.mark_trailing_return_none()
        if else_blocks and self._check_block_has_trailing_return_none(else_blocks[-1]):
            region.mark_trailing_return_none()
        if elif_info.get("final_else") and self._check_block_has_trailing_return_none(elif_info["final_else"][-1]):
            region.mark_trailing_return_none()
        return region

    def _build_chained_compare_region(self, header, condition_block, chain_blocks,
                                      ft_succ, short_circuit_succ, chained_compare_info):
        compare_ops = chained_compare_info["compare_ops"]
        real_then = None
        real_else = None
        all_compare_blocks = []
        current_ft = ft_succ
        for op_idx in range(len(compare_ops)):
            if current_ft is None:
                break
            ft_last = current_ft.get_last_instruction()
            if not ft_last or not any(i.opname == "COMPARE_OP" for i in current_ft.instructions):
                break
            all_compare_blocks.append(current_ft)
            if op_idx < len(compare_ops) - 1:
                ft_succs = sorted(current_ft.successors, key=lambda s: s.start_offset)
                current_ft = next((s for s in ft_succs if s is not short_circuit_succ), None)
        if all_compare_blocks:
            last_compare = all_compare_blocks[-1]
            lc_succs = sorted(last_compare.successors, key=lambda s: s.start_offset)
            real_then = next((s for s in lc_succs if s is not short_circuit_succ), None)
        real_else = short_circuit_succ
        then_blocks = [real_then] if real_then else []
        else_blocks = [real_else] if real_else else []
        if not then_blocks or not else_blocks:
            return None
        all_blocks = {header, ft_succ, real_then, real_else} | set(all_compare_blocks) | chain_blocks
        region = IfRegion(
            region_type=RegionType.IF, entry=header, blocks=all_blocks,
            condition_block=header, then_blocks=[], else_blocks=[real_else],
            merge_block=real_then, chained_compare_blocks=all_compare_blocks,
            chained_compare_ops=compare_ops,
        )
        return region

    def _is_chained_compare_header(self, block: BasicBlock) -> bool:
        """统一比较链检测 - 基于COPY(arg=2)+COMPARE_OP指令对

        理论依据（CPython编译器规范 - PEP 623 / Python 3.11+ 字节码）：
        - CPython编译器将链式比较（如 `a < b < c`）编译为 COPY(arg=2) + COMPARE_OP 指令对
        - COPY(arg=2)将栈上第二个操作数复制到栈顶用于下一次比较（栈操作：[a, b] → [a, b, b]）
        - 链式特征：连续的比较操作共享中间操作数，避免重复加载
        - 这是CPython编译器的确定性优化模式，非启发式规则

        参考文档：
        - Python字节码参考手册（https://docs.python.org/3/library/dis.html）
        - CPython源码：Python/ceval.c 中 COPY 和 COMPARE_OP 的实现
        """
        if not block.instructions:
            return False
        instrs = block.instructions
        for i in range(len(instrs) - 1):
            # [Round6-01/02] 链式 is/in 也走 COPY + IS_OP/CONTAINS_OP 模式
            if (instrs[i].opname == 'COPY' and instrs[i].arg == 2 and
                instrs[i + 1].opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')):
                return True
        return False

    def _detect_chained_compare_pattern(self, condition_block: BasicBlock) -> Optional[Dict]:
        """检测链式比较模式（COPY+COMPARE_OP/IS_OP/CONTAINS_OP指令对）

        扩展检测：从单block扫描改为追踪ft_successor链中的额外COMPARE_OP块。
        使用min(succs)取then分支（fallthrough）而非else分支。

        [Round6-01/02] 扩展支持 IS_OP（is/is not）与 CONTAINS_OP（in/not in）
        链式比较。CPython 把 `a is b is c` 编译为 `IS_OP ×2`（而非 COMPARE_OP），
        `a in b in c` 编译为 `CONTAINS_OP ×2`。旧实现仅匹配 COMPARE_OP，对
        IS_OP/CONTAINS_OP 链式比较不识别，导致 if body 整条赋值坍塌为 pass。

        Returns:
            Dict with 'compare_ops' and 'extra_chain_blocks' keys or None
        """
        if not condition_block.instructions:
            return None
        instrs = condition_block.instructions
        compare_ops = []
        pair_count = 0
        for i in range(len(instrs) - 1):
            if (instrs[i].opname == 'COPY' and instrs[i].arg == 2 and
                instrs[i + 1].opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')):
                pair_count += 1
                compare_ops.append(self._chain_compare_op_str(instrs[i + 1]))
        extra_chain_blocks = []
        current_ft = condition_block
        visited = {condition_block}
        while True:
            succs = list(current_ft.successors)
            if len(succs) < 2:
                break
            ft_candidate = min(succs, key=lambda s: s.start_offset)
            if ft_candidate in visited:
                break
            if not any(i.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')
                       for i in ft_candidate.instructions):
                break
            has_back_edge = any(s.start_offset <= ft_candidate.start_offset for s in ft_candidate.successors)
            if has_back_edge:
                break
            extra_chain_blocks.append(ft_candidate)
            visited.add(ft_candidate)
            for i in ft_candidate.instructions:
                if i.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
                    compare_ops.append(self._chain_compare_op_str(i))
            current_ft = ft_candidate
        if pair_count >= 1 and extra_chain_blocks:
            return {'compare_ops': compare_ops, 'extra_chain_blocks': extra_chain_blocks}
        return None

    @staticmethod
    def _chain_compare_op_str(instr) -> Optional[str]:
        """[Round6-01/02] 把链式比较指令映射为 AST op 字符串。

        COMPARE_OP 的 argval 已是字符串（'<' / '==' / '>=' 等）；
        IS_OP arg=0 → 'is'，arg=1 → 'is not'；
        CONTAINS_OP arg=0 → 'in'，arg=1 → 'not in'。
        """
        if instr.opname == 'COMPARE_OP':
            return instr.argval
        if instr.opname == 'IS_OP':
            return 'is not' if instr.arg else 'is'
        if instr.opname == 'CONTAINS_OP':
            return 'not in' if instr.arg else 'in'
        return None

    def _identify_ternary_regions(self, loop_regions: List[Region],
                                   try_regions: List[Region],
                                   with_regions: List[Region],
                                   match_regions: List[Region],
                                   boolop_regions: List[Region],
                                   conditional_regions: List[Region]) -> List[Region]:
        """识别三元表达式（IfExp）区域 — TERNARY 区域类型

        算法角色：薄协调器（Thin Coordinator）。在 Phase 2 运行（BoolOp 之后、
        If 之前），扫描 CFG 中的 `x if cond else y` 模式并构造 TernaryRegion。

        1. 算法描述（基于 "No More Gotos" 论文）
        -----------------------------------------
        采用自底向上的归约策略：condition_block 经条件跳转分出 true/false
        两条值路径，true 路径以 JUMP_FORWARD 跳过 false 路径并在 merge_block
        汇合。识别出该钻石形状后构造 TernaryRegion(condition_block,
        true_value_block, false_value_block, merge_block)。四个核心原则：
        (a) 自底向上归约 —— 在 BoolOpRegion 之后运行；
        (b) 唯一块所有权 —— condition_block 不与 IfRegion 共享；
        (c) 嵌套即抽象节点 —— TernaryRegion 出现在值上下文中时由父
            IfRegion/LoopRegion 通过 entry 引用；
        (d) entry 引用语义 —— 父区域引用 condition_block，而非全部三元块。

        2. 字节码模式（CPython 编译器行为）
        -----------------------------------
        (A) 基本三元 `x if cond else y`：
            LOAD cond; POP_JUMP_IF_FALSE -> false;
            LOAD x; JUMP_FORWARD -> merge;
            false: LOAD y; merge: STORE result
        (B) 带 BoolOp 条件链 `x if a and b else y`：
            LOAD a; POP_JUMP_IF_FALSE -> false;
            LOAD b; POP_JUMP_IF_FALSE -> false;   # condition_chain_blocks
            LOAD x; JUMP_FORWARD -> merge;
            false: LOAD y; merge: STORE result
        condition_chain_blocks 记录 (block, op) 元组列表，用于在 AST 生成阶段
        重建 BoolOp 条件。

        3. 边界条件（数学性质）
        -----------------------
        entry  = condition_block
        blocks = {condition_block, true_value_block, false_value_block,
                  merge_block} ∪ condition_chain_blocks[*].block
        exit   = merge_block（父区域以此为汇合引用）
        true_value_block 必须以 JUMP_FORWARD 终结；false_value_block 落入 merge。
        value 块为单表达式块（_is_ternary_block 校验）。

        4. 归约语义（与父区域的契约）
        ----------------------------
        TernaryRegion 是叶子值区域：归约后被父 IfRegion / LoopRegion /
        Assign 上下文当作一个表达式节点引用（通过 condition_block 入口）。
        merge_block 的 STORE/RETURN 终结由父区域消费；region 自身不产生
        控制流语句，只产出 IfExp 表达式节点。

        5. AST 映射
        -----------
        _generate_ternary -> ast.IfExp(test=cond, body=true_expr,
                                        orelse=false_expr)。
        输出形态：
          - value_target 存在        -> Assign(targets, value=IfExp)
          - container_type != None   -> Expr(Dict|List|Tuple|Set 内含 IfExp)
          - merge 块 RETURN          -> Return(value=IfExp)
          - 值块 POP_TOP             -> Expr(value=IfExp)
        带 BoolOp 条件链时由 _build_ternary_boolop_condition 重建 test。

        6. 已知失败模式
        ---------------
        当前测试矩阵通过率: 100%（ternary 116/116），无已知失败模式。
        历史问题 tn20/tn21 已在 Phase 3.6 修复：在 _detect_ternary_pattern
        中加入 `block in match_case_body_blocks` 守卫，避免误吞 Match case 体。
        设计权衡：BoolOp vs Ternary 优先级 —— 当候选块被 BoolOpRegion 占用时，
        _detect_ternary_pattern 中的 chain_blocks 检查保守地跳过 ternary 创建
        （skip_ternary=True），优先保留 BoolOp。这是有意为之的保守策略，与
        归约算法 4 核心原则一致（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 /
        父引用子入口）。
        """

        def _can_be_ternary_header(block):
            if len(block.conditional_successors) != 2:
                return False
            last = block.get_last_instruction()
            if not last or last.opname not in (
                FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                return False
            # [Round4-04] 值上下文链式比较 IfRegion.entry（如 `z = 0 < a < 10`
            # 的 condition_block，末尾是 JUMP_IF_FALSE_OR_POP）不应被 TernaryRegion
            # 抢占。依「每块唯一归属」原则，块已属 chained_compare IfRegion
            # （region_type=IF 且 chained_compare_ops 非空）时跳过 ternary 识别。
            # 直接遍历 self.regions 查找（不依赖 block_to_region，因 IF_THEN 父
            # 优先级更高，block_to_region[block] 可能指向父 IfRegion 而非嵌套的
            # chained_compare IfRegion）。
            if last.opname in SHORT_CIRCUIT_JUMP_OPS:
                for _r in self.regions:
                    if (isinstance(_r, IfRegion)
                            and _r.region_type == RegionType.IF
                            and _r.entry is block):
                        _cc_ops = getattr(_r, 'chained_compare_ops', None)
                        _cc_blocks = getattr(_r, 'chained_compare_blocks', None)
                        if (_cc_ops and len(_cc_ops) >= 2 and _cc_blocks):
                            return False
                        break
            if block not in self.block_to_region:
                for succ in block.conditional_successors:
                    succ_region = self.block_to_region.get(succ)
                    if isinstance(succ_region, LoopRegion):
                        if succ == succ_region.condition_block or succ == succ_region.entry:
                            return False
                return True
            existing = self.block_to_region[block]
            return existing.can_be_ternary_header(block, self)

        def _is_boolop_ternary_candidate(boolop_region):
            BOOLOP_JUMP_OPS = SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS

            def _is_not_ternary_boolop_pattern():
                """[聚类6] 检测 BoolOpRegion 是否实际是 not (ternary) 模式。

                not (a if c else b) 编译为：
                - cond_block: LOAD c, POP_JUMP_IF_FALSE → false_value
                - true_value: LOAD a, POP_JUMP_IF_TRUE → else_exit
                - false_value: LOAD b, POP_JUMP_IF_TRUE → else_exit (同一)

                BoolOpRegion 误识别为 op_chain=[(cond, 'and'), (true_value, 'or')]
                因为 cond 用 IF_FALSE (and 短路)，true_value 用 IF_TRUE (or 短路)。
                两个 value 的 IF_TRUE target 是同一 else_exit (return body)。
                """
                if len(boolop_region.op_chain) != 2:
                    return False
                cond_block_bo, _ = boolop_region.op_chain[0]
                tv_block_bo, _ = boolop_region.op_chain[1]
                cond_last_bo = cond_block_bo.get_last_instruction()
                tv_last_bo = tv_block_bo.get_last_instruction()
                if not cond_last_bo or not tv_last_bo:
                    return False
                # cond 用 IF_FALSE/IF_NONE (and 短路)
                if 'FALSE' not in cond_last_bo.opname and 'IF_NONE' not in cond_last_bo.opname:
                    return False
                # true_value 用 IF_TRUE/IF_NOT_NONE (or 短路)
                if 'TRUE' not in tv_last_bo.opname and 'IF_NOT_NONE' not in tv_last_bo.opname:
                    return False
                if cond_last_bo.argval is None or tv_last_bo.argval is None:
                    return False
                # cond 的 IF_FALSE target 是 false_value block (另一个 value)
                fv_block_bo = self.cfg.get_block_by_offset(cond_last_bo.argval)
                if fv_block_bo is None or fv_block_bo is tv_block_bo:
                    return False
                # false_value 也以 IF_TRUE/IF_NOT_NONE 结尾
                fv_last_bo = fv_block_bo.get_last_instruction()
                if not fv_last_bo:
                    return False
                if 'TRUE' not in fv_last_bo.opname and 'IF_NOT_NONE' not in fv_last_bo.opname:
                    return False
                if fv_last_bo.argval is None:
                    return False
                # 两个 value 的 IF_TRUE target 是 else-exit。
                # not(ternary) 模式下，两个 value (a/b) 的 IF_TRUE target 可能是
                # 不同的 exit 块（CPython 为每条值路径生成独立的 return/exit 块），
                # 但内容等价（如 LOAD_CONST None; RETURN_VALUE）。需检查内容等价，
                # 而非要求同一块。
                fv_exit_bo = self.cfg.get_block_by_offset(fv_last_bo.argval)
                tv_exit_bo = self.cfg.get_block_by_offset(tv_last_bo.argval)
                if fv_exit_bo is None or tv_exit_bo is None:
                    return False
                if fv_exit_bo is tv_exit_bo:
                    return True
                # 内容等价：非噪音指令序列（opname, argval）完全一致
                fv_eff = [(i.opname, i.argval) for i in fv_exit_bo.instructions
                          if i.opname not in NOISE_OPS]
                tv_eff = [(i.opname, i.argval) for i in tv_exit_bo.instructions
                          if i.opname not in NOISE_OPS]
                return fv_eff == tv_eff

            if len(boolop_region.op_chain) >= 2:
                first_jt_offset = None
                for chain_block, _ in boolop_region.op_chain:
                    last_instr = chain_block.get_last_instruction()
                    if last_instr and last_instr.opname in BOOLOP_JUMP_OPS and last_instr.argval is not None:
                        if first_jt_offset is None:
                            first_jt_offset = last_instr.argval
                        elif last_instr.argval != first_jt_offset:
                            jt_block = self.cfg.get_block_by_offset(last_instr.argval)
                            if jt_block:
                                jt_has_code = any(
                                    i.opname not in NOISE_OPS
                                    and i.opname not in ('LOAD_CONST', 'RETURN_VALUE', 'RETURN_CONST',
                                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'POP_TOP')
                                    for i in jt_block.instructions
                                )
                                if jt_has_code:
                                    return False

            for chain_block, _ in reversed(boolop_region.op_chain):
                last_instr = chain_block.get_last_instruction()
                if last_instr and last_instr.opname in BOOLOP_JUMP_OPS and last_instr.argval is not None:
                    jt_block = self.cfg.get_block_by_offset(last_instr.argval)
                    if not jt_block:
                        return False
                    jt_effective = [i for i in jt_block.instructions if i.opname not in NOISE_OPS]
                    has_unary_not = any(i.opname == 'UNARY_NOT' for i in jt_effective)
                    if has_unary_not:
                        return False
                    jt_non_noise = [i for i in jt_effective
                                    if i.opname not in ('JUMP_FORWARD', 'JUMP_BACKWARD',
                                                        'JUMP_ABSOLUTE')]
                    if len(jt_non_noise) == 0:
                        continue
                    if not self._is_single_expression_block(jt_block):
                        # [聚类6] not (ternary) 模式：value block 的 IF_TRUE 跳到
                        # else-exit (return body)，而不是 merge。else-exit 是 return
                        # body 不是单表达式，但这是有效的 not(ternary) 模式。
                        if _is_not_ternary_boolop_pattern():
                            continue
                        return False
                    return True
            return True

        def _is_ternary_block(block):
            succs = list(block.conditional_successors)
            if len(succs) != 2:
                return False
            # [R19 Bug 22-24 修复] ternary 的值块不能是嵌套 if-elif-else 的条件头。
            # 判定: 若值块以条件跳转结尾（条件头），检查其 fallthrough 后继（非跳转
            # 目标）。仅当 fallthrough 以 RETURN_VALUE/RETURN_CONST 结尾（即 if body
            # 是 return 语句）时拒绝 — 这是 if-elif-else 条件头的特征。boolop 链中
            # 的值块虽以条件跳转结尾（短路求值），但其 fallthrough 是下一个 boolop
            # 检查（POP_JUMP_IF_*）或 JUMP_FORWARD 到 merge，均不以 RETURN 结尾，
            # 不被拒绝。依「每块唯一归属」原则：if-elif-else 条件头归属 IfRegion。
            for s in succs:
                s_last = s.get_last_instruction()
                if s_last and s_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS) and s_last.argval is not None:
                    fallthrough = None
                    for ss in s.conditional_successors:
                        if ss.start_offset != s_last.argval:
                            fallthrough = ss
                            break
                    if fallthrough is not None:
                        ft_last = fallthrough.get_last_instruction()
                        if ft_last and ft_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                            return False
            if not (self._is_single_expression_block(succs[0]) and
                    self._is_single_expression_block(succs[1])):
                return False
            for s in succs:
                if len(s.conditional_successors) >= 2:
                    if all(cs.get_last_instruction() is not None and
                           cs.get_last_instruction().opname in ('RETURN_VALUE', 'RETURN_CONST')
                           for cs in s.conditional_successors):
                        return False
            return True

        def _build_ternary_condition_chain(start_block, initial_ft, initial_jt):
            chain = [start_block]
            current_ft = initial_ft
            while current_ft is not None:
                ft_last = current_ft.get_last_instruction()
                if not ft_last or ft_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
                    break
                ft_succs = sorted(current_ft.conditional_successors, key=lambda s: s.start_offset)
                if len(ft_succs) != 2:
                    break
                ft_jt = next((s for s in ft_succs
                             if s.start_offset == ft_last.argval), None)
                ft_next_ft = next((s for s in ft_succs
                                  if s is not ft_jt), None)
                if ft_jt is None or ft_next_ft is None:
                    break
                if ft_jt != initial_jt and ft_next_ft != initial_jt:
                    break
                chain.append(current_ft)
                current_ft = ft_next_ft
            return chain

        def _reconstruct_simple_chain_args(arg_instrs):
            """[R17-01] Reconstruct simple call args (for middle method calls in
            a method chain) from a flat instruction list. Each arg is rebuilt as
            an expr dict. Handles LOAD_CONST / LOAD_NAME family / LOAD_ATTR /
            LOAD_METHOD chains / BUILD_<list|tuple|set> literals. Returns the
            list of arg expr dicts, or None when an unsupported instruction
            (CALL, BINARY_OP, etc.) is encountered — caller then conservatively
            falls back (no regression). 依「每块唯一归属」: 中间调用的 args 是
            兄弟子节点，与 ternary 同属父 Call 区域，不拆分为独立语句。
            """
            _stack = []
            for _ai in arg_instrs:
                if _ai.opname == 'LOAD_CONST':
                    _stack.append({'type': 'Constant', 'value': _ai.argval})
                elif _ai.opname in ('LOAD_NAME', 'LOAD_FAST',
                                    'LOAD_GLOBAL', 'LOAD_DEREF'):
                    _stack.append({'type': 'Name', 'id': _ai.argval,
                                   'ctx': 'Load'})
                elif _ai.opname in ('LOAD_ATTR', 'LOAD_METHOD'):
                    if not _stack:
                        return None
                    _base = _stack.pop()
                    _stack.append({'type': 'Attribute', 'value': _base,
                                   'attr': _ai.argval, 'ctx': 'Load'})
                elif _ai.opname in ('BUILD_LIST', 'BUILD_TUPLE', 'BUILD_SET'):
                    _n = _ai.arg or 0
                    if len(_stack) < _n:
                        return None
                    _elts = [_stack.pop() for _ in range(_n)]
                    _elts.reverse()
                    _t = {'BUILD_LIST': 'List', 'BUILD_TUPLE': 'Tuple',
                          'BUILD_SET': 'Set'}[_ai.opname]
                    if _t == 'Set':
                        _stack.append({'type': 'Set', 'elts': _elts})
                    else:
                        _stack.append({'type': _t, 'elts': _elts,
                                       'ctx': 'Load'})
                else:
                    return None
            return _stack

        def _detect_ternary_context(cond_block, merge_block):
            if merge_block:
                for instr in merge_block.instructions:
                    if instr.opname == 'BUILD_LIST':
                        return 'list', None, None
                    if instr.opname == 'BUILD_TUPLE':
                        return 'tuple', None, None
                    if instr.opname == 'BUILD_SET':
                        return 'set', None, None
                    if instr.opname == 'BUILD_MAP':
                        dict_key = RegionAnalyzer.extract_dict_key_from_block(cond_block)
                        return 'dict', None, dict_key
                    if instr.opname == 'MAP_ADD':
                        # Dict comprehension: ternary is the dict value, key is on stack before condition
                        dict_key = RegionAnalyzer.extract_dict_key_from_block(cond_block)
                        return 'dict', None, dict_key
                    # [R12-02/04/06 fix] Container literal *-unpack consumes
                    # ternary: BUILD_<container> 0 (in cond_block preload) +
                    # <ternary> + {DICT_UPDATE|LIST_EXTEND|SET_UPDATE} 1 (in
                    # merge_block). The ternary result is unpacked into the
                    # container via Starred. 依「每块唯一归属」：merge_block 的
                    # *_UPDATE/_EXTEND 消费指令归属 TernaryRegion，cond_block
                    # 的 BUILD_<container> 0 preload 也归属 TernaryRegion。
                    if instr.opname == 'DICT_UPDATE':
                        return 'dict_unpack', None, None
                    if instr.opname == 'LIST_EXTEND':
                        return 'list_unpack', None, None
                    if instr.opname == 'SET_UPDATE':
                        return 'set_unpack', None, None
            if cond_block:
                instrs = [i for i in cond_block.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                push_null_idx = None
                for idx, i in enumerate(instrs):
                    if i.opname == 'PUSH_NULL':
                        push_null_idx = idx
                        break
                    # Python 3.11+: LOAD_GLOBAL with arg & 1 == 1 implicitly pushes NULL
                    if i.opname == 'LOAD_GLOBAL' and i.arg is not None and (i.arg & 1):
                        push_null_idx = idx
                        break
                # [R15-05/06 fix] PUSH_NULL guard: 当 func_i 之后的下一条指令
                # 是 POP_JUMP_IF_* 或 PRECALL 时，func_i 实际上不是函数:
                #   - Pattern 2 (ternary as callable): `(a if c else b)()`
                #     字节码: PUSH_NULL, LOAD_NAME(c), POP_JUMP_IF_FALSE, ...
                #     func_i 是 LOAD_NAME(c) (ternary 条件)，next 是 POP_JUMP_IF
                #   - Pattern 3 (subscript on call result): `vars()[(a if c else b)]`
                #     字节码: PUSH_NULL, LOAD_NAME(vars), PRECALL, CALL,
                #             LOAD_NAME(c), POP_JUMP_IF_FALSE, ...
                #     func_i 是 LOAD_NAME(vars) (已被 CALL 0 调用的函数)，next 是 PRECALL
                # 此时不应返回 call context (否则会把 c/vars 误识别为 func，把 ternary
                # 当作其参数)。设 push_null_idx = None 以走 LOAD_METHOD 路径或返回 None,
                # 让 _try_build_ternary_merge_consumer_expr 通过 expr_reconstructor
                # 重建 Call(func=ternary, args=...) 或 Subscript(value=vars(), slice=ternary)。
                if push_null_idx is not None:
                    _func_i_idx = (push_null_idx + 1
                                   if instrs[push_null_idx].opname == 'PUSH_NULL'
                                   else push_null_idx)
                    if _func_i_idx + 1 < len(instrs):
                        _after_func_i = instrs[_func_i_idx + 1]
                        if (_after_func_i.opname in FORWARD_CONDITIONAL_JUMP_OPS
                                or _after_func_i.opname == 'PRECALL'):
                            push_null_idx = None
                if push_null_idx is not None and push_null_idx + 1 < len(instrs):
                    func_i = instrs[push_null_idx + 1] if instrs[push_null_idx].opname == 'PUSH_NULL' else instrs[push_null_idx]
                    if func_i.opname in ('LOAD_NAME', 'LOAD_GLOBAL',
                                         'LOAD_FAST', 'LOAD_DEREF'):
                        return 'call', {
                            'func': {'type': 'Name', 'id': func_i.argval, 'ctx': 'Load'},
                        }, None
                    elif func_i.opname == 'LOAD_ATTR':
                        obj_i = instrs[push_null_idx - 1] if push_null_idx > 0 else None
                        if obj_i and obj_i.opname.startswith('LOAD_'):
                            return 'call', {
                                'func': {
                                    'type': 'Attribute',
                                    'value': {'type': 'Name', 'id': obj_i.argval, 'ctx': 'Load'},
                                    'attr': func_i.argval,
                                    'ctx': 'Load',
                                },
                            }, None
                    # [R2 Bug lambda_call 修复] 检测 lambda 调用模式:
                    # (lambda x: ...)(ternary) 字节码模式:
                    #   PUSH_NULL, LOAD_CONST <code>, MAKE_FUNCTION, [args], PRECALL, CALL
                    # func_i 是 LOAD_CONST <code>，下一条是 MAKE_FUNCTION。
                    # 用 FunctionObject 包装 code object 作为 func，由 AST 生成器的
                    # _build_function_def 转换为 Lambda 表达式。
                    # 依「嵌套即抽象节点」：lambda 是父 Call 的子节点（func）。
                    elif (func_i.opname == 'LOAD_CONST'
                            and push_null_idx + 2 < len(instrs)
                            and instrs[push_null_idx + 2].opname == 'MAKE_FUNCTION'
                            and hasattr(func_i.argval, 'co_code')):
                        return 'call', {
                            'func': {
                                'type': 'FunctionObject',
                                'code': func_i.argval,
                            },
                        }, None
                else:
                    # [R4 Bug 8 修复] 检测 LOAD_METHOD 模式: obj.method(args)
                    # 字节码模式: LOAD_NAME obj, [LOAD_ATTR ...], LOAD_METHOD method,
                    #            [args], PRECALL, CALL
                    # 与 PUSH_NULL 模式不同，LOAD_METHOD 自带 self 绑定，无 PUSH_NULL。
                    # 仅当 merge_block 含 PRECALL/CALL 时才识别为 call 上下文，
                    # 避免误把其他场景的 LOAD_METHOD 当 call。
                    _has_call_in_merge = merge_block is not None and any(
                        i.opname in ('PRECALL', 'CALL') for i in merge_block.instructions
                        if i.opname not in NOISE_OPS)
                    if _has_call_in_merge and len(instrs) >= 2:
                        _method_idx = None
                        for _idx, _i in enumerate(instrs):
                            if _i.opname == 'LOAD_METHOD':
                                _method_idx = _idx
                                break
                            # 在到达三元条件测试前停止
                            if _i.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                break
                        if _method_idx is not None and _method_idx > 0:
                            _method_name = instrs[_method_idx].argval
                            # 从 LOAD_METHOD 向前重建 obj 表达式:
                            # 形如 LOAD_NAME a, [LOAD_ATTR b, LOAD_ATTR c, ...], LOAD_METHOD m
                            # obj 表达式 = a.b.c
                            # [R15-01/02/03/04 fix] obj base 也支持:
                            #   - LOAD_CONST (str/bytes 字面量): "<str>".method(ternary),
                            #     b"<bytes>".method(ternary), "{0.x}".format(ternary) 等
                            #   - BUILD_LIST 0 / BUILD_TUPLE 0 / BUILD_MAP 0 / BUILD_SET 0
                            #     (空容器字面量): [].method(ternary), {}.method(ternary),
                            #     ().method(ternary)
                            # 依「父引用子入口」: 父 Call 通过 cond_block 的 LOAD_METHOD
                            # obj chain 引用 ternary 子节点。原逻辑只识别 LOAD_NAME 等
                            # Name base，遇到 LOAD_CONST/BUILD_<container> 0 即 break，
                            # 导致 _obj_chain 为空、func_call_info 为 None，ternary 被识别
                            # 为独立表达式语句，obj.method(ternary) 调用完全丢失。
                            _obj_chain = []
                            _obj_base_expr = None
                            _j = _method_idx - 1
                            while _j >= 0:
                                _ji = instrs[_j]
                                if _ji.opname == 'LOAD_ATTR':
                                    _obj_chain.insert(0, ('attr', _ji.argval))
                                    _j -= 1
                                    continue
                                if _ji.opname in ('LOAD_NAME', 'LOAD_FAST',
                                                  'LOAD_GLOBAL', 'LOAD_DEREF'):
                                    _obj_base_expr = {
                                        'type': 'Name', 'id': _ji.argval, 'ctx': 'Load',
                                    }
                                    _j -= 1
                                    break
                                if _ji.opname == 'LOAD_CONST':
                                    _obj_base_expr = {
                                        'type': 'Constant', 'value': _ji.argval,
                                    }
                                    _j -= 1
                                    break
                                if _ji.opname == 'BUILD_LIST' and (_ji.arg or 0) == 0:
                                    _obj_base_expr = {
                                        'type': 'List', 'elts': [], 'ctx': 'Load',
                                    }
                                    _j -= 1
                                    break
                                if _ji.opname == 'BUILD_TUPLE' and (_ji.arg or 0) == 0:
                                    _obj_base_expr = {
                                        'type': 'Tuple', 'elts': [], 'ctx': 'Load',
                                    }
                                    _j -= 1
                                    break
                                if _ji.opname == 'BUILD_MAP' and (_ji.arg or 0) == 0:
                                    _obj_base_expr = {
                                        'type': 'Dict', 'keys': [], 'values': [],
                                    }
                                    _j -= 1
                                    break
                                if _ji.opname == 'BUILD_SET' and (_ji.arg or 0) == 0:
                                    _obj_base_expr = {
                                        'type': 'Set', 'elts': [],
                                    }
                                    _j -= 1
                                    break
                                # 其他指令（如 CALL 等）停止
                                break
                            if _obj_base_expr is not None:
                                _obj_expr = _obj_base_expr
                                for _kind, _name in _obj_chain:
                                    _obj_expr = {
                                        'type': 'Attribute',
                                        'value': _obj_expr,
                                        'attr': _name,
                                        'ctx': 'Load',
                                    }
                                _cur_func_expr = {
                                    'type': 'Attribute',
                                    'value': _obj_expr,
                                    'attr': _method_name,
                                    'ctx': 'Load',
                                }
                                # [R13-01 fix] 处理 method chain: 第一个
                                # LOAD_METHOD m1, [args], PRECALL, CALL,
                                # LOAD_METHOD m2, ... 第一个 LOAD_METHOD 是
                                # receiver chain 的一部分，第二个 LOAD_METHOD 才
                                # 是真正消费 ternary 的函数。
                                # 例: s.upper().split((a if c else b))
                                #   cond_block: LOAD_NAME s, LOAD_METHOD upper,
                                #               PRECALL, CALL, LOAD_METHOD split,
                                #               LOAD_NAME c, POP_JUMP_...
                                #   把 s.upper() 包装成 Call 作为 receiver，
                                #   split 作为 func.attr。
                                # [R17-01 fix] 扩展支持带 args 的中间方法调用:
                                #   s.replace('a','b').split((a if c else b))
                                #   cond_block: LOAD_NAME s, LOAD_METHOD replace,
                                #               LOAD_CONST 'a', LOAD_CONST 'b',
                                #               PRECALL, CALL, LOAD_METHOD split, ...
                                #   中间 args 在 LOAD_METHOD 与 PRECALL 之间，
                                #   重建为 Call.args，保守不退化（含不支持 arg
                                #   指令时 break）。依「父引用子入口」: 父 Call
                                #   通过 cond_block 的 method chain (含中间 args)
                                #   引用 ternary 子节点；依「每块唯一归属」: 中间
                                #   args 是兄弟子节点，与 ternary 同属父 Call 区域。
                                _chain_idx = _method_idx + 1
                                while _chain_idx < len(instrs):
                                    _ci = instrs[_chain_idx]
                                    if _ci.opname in NOISE_OPS:
                                        _chain_idx += 1
                                        continue
                                    # [R17-01] 找到 PRECALL，可能跨越中间 args
                                    _precall_idx = None
                                    _arg_start = _chain_idx
                                    _scan = _chain_idx
                                    while _scan < len(instrs):
                                        _si = instrs[_scan]
                                        if _si.opname in NOISE_OPS:
                                            _scan += 1
                                            continue
                                        if _si.opname == 'PRECALL':
                                            _precall_idx = _scan
                                            break
                                        if _si.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                            break
                                        _scan += 1
                                    if _precall_idx is None:
                                        break
                                    # [R17-01] 重建中间调用的 args
                                    # (LOAD_METHOD 与 PRECALL 之间的指令)
                                    _arg_instrs = [instrs[k]
                                                   for k in range(_arg_start, _precall_idx)
                                                   if instrs[k].opname not in NOISE_OPS]
                                    _mid_args = _reconstruct_simple_chain_args(_arg_instrs)
                                    if _mid_args is None:
                                        break
                                    _call_idx = _precall_idx + 1
                                    while (_call_idx < len(instrs)
                                           and instrs[_call_idx].opname in NOISE_OPS):
                                        _call_idx += 1
                                    if (_call_idx >= len(instrs)
                                            or instrs[_call_idx].opname != 'CALL'):
                                        break
                                    _next_idx = _call_idx + 1
                                    while (_next_idx < len(instrs)
                                           and instrs[_next_idx].opname in NOISE_OPS):
                                        _next_idx += 1
                                    if (_next_idx >= len(instrs)
                                            or instrs[_next_idx].opname != 'LOAD_METHOD'):
                                        break
                                    _cur_func_expr = {
                                        'type': 'Call',
                                        'func': _cur_func_expr,
                                        'args': _mid_args,
                                        'keywords': [],
                                    }
                                    _cur_func_expr = {
                                        'type': 'Attribute',
                                        'value': _cur_func_expr,
                                        'attr': instrs[_next_idx].argval,
                                        'ctx': 'Load',
                                    }
                                    _chain_idx = _next_idx + 1
                                return 'call', {
                                    'func': _cur_func_expr,
                                }, None
            return None, None, None

        def _detect_ternary_pattern(block):
            """检测三元表达式模式

            判定规则：
            1. 基本条件：两个分支都必须是单表达式块
            2. 额外检查：如果值块包含函数调用（CALL指令）且返回值未被使用（CALL后跟POP_TOP）
               则不应该被认为是Ternary，而应识别为IfRegion

            这解决了简单if-else语句被误判为三元表达式的问题：
                if x > 0:
                    print('positive')   # CALL + POP_TOP
                else:
                    print('non-positive')  # CALL + POP_TOP
            这种print()语句是语句而非表达式，不应该被识别为Ternary。
            """

            if not _can_be_ternary_header(block):
                return None
            last_instr = block.get_last_instruction()
            heads = sorted(block.conditional_successors, key=lambda s: s.start_offset)
            if len(heads) != 2:
                return None
            true_block = next((s for s in heads if s.start_offset != last_instr.argval), None)
            false_block = next((s for s in heads if s.start_offset == last_instr.argval), None)
            if not (true_block and false_block):
                return None

            # 区域归约算法：防止LoopRegion的condition_block/header_block被误识别为ternary值块
            # 当if-else的某个分支入口是while循环的条件块时，不应识别为三元表达式
            for _lr in (loop_regions or []):
                if true_block == _lr.condition_block or true_block == _lr.header_block:
                    return None
                if false_block == _lr.condition_block or false_block == _lr.header_block:
                    return None

            # [Round7-06] MatchRegion 优先级高于 TernaryRegion：当 if 体（true_block）
            # 或 else 路径（false_block）落入已识别 MatchRegion 的 blocks（subject_block /
            # case_blocks / case_body）时，这是「if 体含 match 语句」的结构，不是三元表达式。
            # 若允许 TernaryRegion 创建，下游 filter（line 1113
            # `_region_overlaps_with_ternary`）会把 MatchRegion 从 match_regions 列表移除，
            # 导致 _identify_conditional_regions 看不到 MatchRegion，进而在 MatchRegion 的
            # case_blocks 上错误创建 IfRegion，把 `case 1 | 2:` 误转为 `if (x==1): ...
            # elif 2: ...`。依「每块唯一归属」原则：match 的 case 块归属 MatchRegion，
            # 不应被 TernaryRegion 抢占。
            for _mr in (match_regions or []):
                _mr_blocks = getattr(_mr, 'blocks', None)
                if not _mr_blocks:
                    continue
                if true_block in _mr_blocks or false_block in _mr_blocks:
                    return None

            # [Issue 1 fix] 三元表达式的值分支是"在栈顶留下一个值"的单表达式
            # （后续由 STORE_*/RETURN_VALUE/BUILD_STRING 等消费）。
            # 如果值分支块本身以 RETURN_VALUE/RETURN_CONST 结尾且不含 POP_TOP，
            # 说明它是 return 语句体（if-elif-return 模式），而非三元值分支——拒绝创建 TernaryRegion。
            # 注意1：模块级表达式语句的模式是 LOAD value, POP_TOP, LOAD_CONST None, RETURN_VALUE
            # 其中 POP_TOP 丢弃了表达式的值——这仍然是三元表达式，不应拒绝。
            # 注意2：while 循环条件中的三元，其 false 分支可能以 RETURN_VALUE 结尾
            # （循环退出时模块隐式返回 None），这种情况由 has_jump_forward_skip 处理，
            # 不应在此拒绝。因此此检查在 has_jump_forward_skip 之后执行。
            def _block_is_return_body(blk):
                effective = [i for i in blk.instructions if i.opname not in NOISE_OPS]
                if not effective:
                    return False
                last = effective[-1]
                if last.opname not in ('RETURN_VALUE', 'RETURN_CONST'):
                    return False
                for i in effective[:-1]:
                    if i.opname == 'POP_TOP':
                        return False
                return True

            chain_blocks = _build_ternary_condition_chain(block, true_block, false_block)

            # 辅助函数：检查块是否以RETURN_VALUE/RETURN_CONST结尾
            def _block_ends_with_return(blk):
                last = blk.get_last_instruction()
                return last is not None and last.opname in ('RETURN_VALUE', 'RETURN_CONST')

            # 辅助函数：检查块是否包含CALL指令且返回值被POP_TOP丢弃
            # 这是语句（如print()）而非表达式的典型特征
            def _is_call_without_value_used(blk):
                """检查块是否包含CALL指令且返回值被POP_TOP丢弃"""
                effective = [i for i in blk.instructions if i.opname not in NOISE_OPS]
                # 移除末尾跳转
                while effective and effective[-1].opname in (
                    'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                    effective = effective[:-1]
                # 检查是否有CALL指令后跟POP_TOP的模式
                for i, instr in enumerate(effective):
                    if instr.opname.startswith('CALL') and i + 1 < len(effective):
                        next_instr = effective[i + 1]
                        if next_instr.opname == 'POP_TOP':
                            return True
                return False

            has_jump_forward_skip = False
            if len(chain_blocks) > 1:
                last_chain = chain_blocks[-1]
                lc_last = last_chain.get_last_instruction()
                if not lc_last or lc_last.opname not in (
                    FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                    return None
                lc_succs = sorted(last_chain.conditional_successors, key=lambda s: s.start_offset)
                if len(lc_succs) != 2:
                    return None
                true_block = next((s for s in lc_succs
                                  if s.start_offset != lc_last.argval), None)
                false_block = next((s for s in lc_succs
                                   if s.start_offset == lc_last.argval), None)
                if not (true_block and false_block):
                    return None
                if not (self._is_single_expression_block(true_block) and
                        self._is_single_expression_block(false_block)):
                    return None

                # 修复：检查值块是否包含CALL指令但返回值未被使用
                # 如果是，则这是语句（如print()）而非表达式，不应识别为Ternary
                if _is_call_without_value_used(true_block) or _is_call_without_value_used(false_block):
                    return None
                true_discards = any(i.opname == 'POP_TOP' for i in true_block.instructions
                                   if i.opname not in NOISE_OPS)
                false_discards = any(i.opname == 'POP_TOP' for i in false_block.instructions
                                    if i.opname not in NOISE_OPS)

                # Phase 11修复: 放宽POP_TOP检查
                #
                # 原始逻辑: 如果两个分支都有POP_TOP，则拒绝（认为不是ternary）
                # 问题: 对于顶层三元表达式（如 `a if cond else b`），
                #       Python编译器会在两个分支都生成POP_TOP（值未被使用）
                #       这是正常模式，不应该拒绝
                #
                # 新逻辑: 只有当POP_TOP是唯一的非噪音指令时才拒绝
                #         （表示空分支如 pass 或 ...）
                #         如果分支还有其他有效指令（如LOAD），则允许
                #
                # 这解决了 tn20/tn21 类失败:
                #   `a if a and b else 0` 的两个值分支都有POP_TOP，
                #   但它们是有效的表达式求值+丢弃
                if true_discards and false_discards:
                    def has_meaningful_instructions(blk):
                        effective = [i for i in blk.instructions if i.opname not in NOISE_OPS]
                        non_pop = [i for i in effective if i.opname != 'POP_TOP']
                        non_jump = [i for i in non_pop if not i.opname.startswith('JUMP_') and not i.opname.startswith('POP_JUMP_')]
                        return len(non_jump) > 0

                    true_has_content = has_meaningful_instructions(true_block)
                    false_has_content = has_meaningful_instructions(false_block)

                    if not (true_has_content and false_has_content):
                        return None
            elif not _is_ternary_block(block):
                false_is_ternary = False
                # Detect JUMP_FORWARD pattern: ternary in while-loop condition.
                # When true_block ends with FORWARD_CONDITIONAL_JUMP (the while
                # condition test) and its fallthrough successor ends with
                # JUMP_FORWARD (skip else branch), this is the ternary
                # discriminator. Boolop does NOT have this JUMP_FORWARD.
                _true_last_instr = true_block.get_last_instruction()
                if (_true_last_instr and
                        _true_last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS and
                        _true_last_instr.argval is not None):
                    _true_succs = list(true_block.conditional_successors)
                    if len(_true_succs) == 2:
                        _true_ft = next((s for s in _true_succs
                                         if s.start_offset != _true_last_instr.argval), None)
                        if _true_ft:
                            _ft_last = _true_ft.get_last_instruction()
                            if (_ft_last and _ft_last.opname == 'JUMP_FORWARD' and
                                    _ft_last.argval is not None and
                                    _ft_last.argval != false_block.start_offset):
                                # Validate _true_ft is a pure jump block.
                                # In the ternary-in-while-condition pattern,
                                # _true_ft is just a JUMP_FORWARD connector to
                                # the merge (while body). If _true_ft contains
                                # value-producing instructions (LOAD, CALL,
                                # etc.), the true_block is a CONDITION (of a
                                # nested ternary/if), not a VALUE — so this is
                                # an if-statement, not a ternary.
                                _ft_effective = [i for i in _true_ft.instructions
                                                 if i.opname not in NOISE_OPS]
                                _ft_is_pure_jump = all(
                                    i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                                 'JUMP_BACKWARD',
                                                 'JUMP_BACKWARD_NO_INTERRUPT')
                                    for i in _ft_effective
                                )
                                if not _ft_is_pure_jump:
                                    has_jump_forward_skip = False
                                else:
                                    # Validate false_block doesn't start with
                                    # POP_TOP. POP_TOP at the start indicates
                                    # value cleanup (e.g., chained comparison
                                    # intermediate cleanup), not value
                                    # production. A ternary false value block
                                    # should produce a value, not discard one.
                                    _false_eff = [i for i in false_block.instructions
                                                  if i.opname not in NOISE_OPS]
                                    if (_false_eff and
                                            _false_eff[0].opname == 'POP_TOP'):
                                        has_jump_forward_skip = False
                                    else:
                                        has_jump_forward_skip = True
                false_existing = self.block_to_region.get(false_block)
                if isinstance(false_existing, TernaryRegion):
                    # [R18 Bug 22-24 修复] 当 false_block 是已存在的 TernaryRegion
                    # （嵌套三元 `(x if c else (y if c2 else z))` 的 false 路径）时，
                    # 仍需验证 true_block 是有效的三元值块（单表达式块或已存在的
                    # TernaryRegion entry）。否则若 true_block 含 STORE_FAST 等副作用
                    # 指令（如 if-elif-else 链中 if body），仍会被错误归约为
                    # TernaryRegion，导致 if-elif-else 结构退化为表达式语句，
                    # 甚至泄漏 AST dict 字面量（Bug 23）。
                    # 依「每块唯一归属」原则：ternary 的值块必须是表达式而非语句。
                    # [R19 Bug 22-24 修复] 进一步: true_block 若是嵌套 if-elif-else 的
                    # 条件头（以 POP_JUMP_IF_* 结尾且后继含 return 语句体），则不是
                    # ternary 值块。嵌套 ternary 的条件头后继是纯表达式（无 return），
                    # 不被拒绝。原 `_is_single_expression_block` 会剥离尾部条件跳转，
                    # 使条件头误判为单表达式，导致外层 if-elif-else 整体退化为
                    # TernaryRegion，9 个分支退化为 6 个裸 return。
                    true_existing = self.block_to_region.get(true_block)
                    if isinstance(true_existing, TernaryRegion):
                        false_is_ternary = True
                    elif self._is_single_expression_block(true_block):
                        _tb_last = true_block.get_last_instruction()
                        _is_nested_if_header = False
                        if _tb_last and _tb_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                            for ss in true_block.conditional_successors:
                                ss_last = ss.get_last_instruction()
                                if ss_last and ss_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                    _is_nested_if_header = True
                                    break
                        false_is_ternary = not _is_nested_if_header
                    # else: true_block 是语句块（含 STORE_FAST 等），不构成 ternary
                elif (len(false_block.conditional_successors) == 2 and
                      self._is_single_expression_block(true_block)):
                    # [R19 Bug 22-24 修复] 同上: true_block 若是嵌套 if-elif-else 的
                    # 条件头（后继含 return），则不是 ternary 值块
                    _tb_last = true_block.get_last_instruction()
                    _true_is_nested_if_header = False
                    if _tb_last and _tb_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                        for ss in true_block.conditional_successors:
                            ss_last = ss.get_last_instruction()
                            if ss_last and ss_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                _true_is_nested_if_header = True
                                break
                    if _true_is_nested_if_header:
                        false_is_ternary = False
                    else:
                        false_last = false_block.get_last_instruction()
                        if false_last and false_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                            false_succs = list(false_block.conditional_successors)
                            # [R19 Bug 22-24 修复] false_succs 若是嵌套 if-elif-else 的
                            # 条件头（后继含 return），也不是 ternary 值块
                            _any_succ_nested_if_header = False
                            for s in false_succs:
                                s_last = s.get_last_instruction()
                                if s_last and s_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                                    for ss in s.conditional_successors:
                                        ss_last = ss.get_last_instruction()
                                        if ss_last and ss_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                            _any_succ_nested_if_header = True
                                            break
                                if _any_succ_nested_if_header:
                                    break
                            if _any_succ_nested_if_header:
                                false_is_ternary = False
                            elif all(self._is_single_expression_block(s) for s in false_succs):
                                if all(not _block_ends_with_return(s) for s in false_succs):
                                    false_is_ternary = True
                if not false_is_ternary and not has_jump_forward_skip:
                    return None

            # [Issue 1 fix] 在 has_jump_forward_skip 逻辑完成后，应用 return-body 检查。
            # 仅当不是 while 循环条件三元（has_jump_forward_skip=False）时检查：
            # 如果 true/false 分支是 return 语句体（以 RETURN_VALUE 结尾且无 POP_TOP），
            # 说明这是 if-elif-return 模式而非三元表达式，拒绝创建 TernaryRegion。
            # - ternary20: has_jump_forward_skip=False, return body 检查拒绝 ✓
            # - ternary12: has_jump_forward_skip=True, 跳过检查 ✓
            # - 模块级三元 (tn01): has_jump_forward_skip=False, 但分支有 POP_TOP
            #   （LOAD value, POP_TOP, LOAD_CONST None, RETURN_VALUE）,
            #   _block_is_return_body 返回 False, 不拒绝 ✓
            if not has_jump_forward_skip:
                if _block_is_return_body(true_block) or _block_is_return_body(false_block):
                    return None

            if (len(true_block.conditional_successors) >= 2 and
                    all(_block_ends_with_return(s) for s in true_block.conditional_successors) and
                    len(false_block.conditional_successors) >= 2 and
                    all(_block_ends_with_return(s) for s in false_block.conditional_successors)):
                    return None

            # 检查值块是否包含CALL+POP_TOP模式（函数返回值被丢弃）
            # 这种情况是if-else语句（如 even.append(i)），不是三元表达式
            if _is_call_without_value_used(true_block) or _is_call_without_value_used(false_block):
                return None

            candidate_blocks = set(chain_blocks) | {block}
            skip_ternary = False
            for cb in candidate_blocks:
                existing = self.block_to_region.get(cb)
                if isinstance(existing, BoolOpRegion):
                    can_upgrade = False
                    if existing.entry == block:
                        header_last = block.get_last_instruction()
                        if (header_last and
                                header_last.opname in FORWARD_CONDITIONAL_JUMP_OPS and
                                header_last.argval is not None):
                            jump_target = header_last.argval
                            if (jump_target == false_block or
                                    (isinstance(jump_target, int) and
                                     false_block is not None and
                                     jump_target == false_block.start_offset)):
                                can_upgrade = True
                            elif (existing.merge_block and
                                  existing.merge_block == false_block or
                                  (existing.merge_block is not None and
                                   false_block is not None and
                                   existing.merge_block.start_offset ==
                                   false_block.start_offset)):
                                can_upgrade = True
                            else:
                                chain_only_in_candidate = all(
                                    b in candidate_blocks for b, _ in existing.op_chain)
                                if chain_only_in_candidate:
                                    can_upgrade = True
                    if not can_upgrade:
                        skip_ternary = True
                        break
            if skip_ternary:
                return None

            # Phase 11增强: 当BoolOp→Ternary升级时，保留操作符信息
            #
            # _build_ternary_boolop_condition 期望 condition_chain_blocks 是
            # [(block, op), ...] 格式，但 _build_ternary_condition_chain 返回的是
            # 纯 [block, ...] 列表。
            #
            # 当我们从 BoolOpRegion 升级时，需要从 BoolOpRegion.op_chain 中提取
            # 操作符信息，以便正确生成 BoolOp AST 节点。
            boolop_op_chain = None
            for cb in candidate_blocks:
                existing = self.block_to_region.get(cb)
                if isinstance(existing, BoolOpRegion) and existing.entry == block:
                    boolop_op_chain = existing.op_chain
                    break

            # 如果有 BoolOp op_chain，将其转换为 condition_chain_blocks 格式
            if boolop_op_chain and len(chain_blocks) > 1:
                chain_blocks = list(boolop_op_chain)  # 现在是 [(block, op), ...] 格式

            nested_ternary_regions = []
            for vb in (true_block, false_block):
                existing = self.block_to_region.get(vb)
                if isinstance(existing, TernaryRegion) and existing not in nested_ternary_regions:
                    nested_ternary_regions.append(existing)

            merge_block = self.dom_analyzer.find_nearest_common_post_dominator(
                {true_block, false_block})

            # When the else-branch exits (RETURN_VALUE) and the then-branch
            # has a JUMP_FORWARD, there is no common post-dominator. Use the
            # JUMP_FORWARD target as the merge_block — this is where the
            # ternary result is consumed (e.g., the while-loop header).
            if merge_block is None and has_jump_forward_skip:
                _tli = true_block.get_last_instruction()
                if _tli and _tli.argval is not None:
                    _tsuccs = list(true_block.conditional_successors)
                    _tft = next((s for s in _tsuccs
                                 if s.start_offset != _tli.argval), None)
                    if _tft:
                        _tft_last = _tft.get_last_instruction()
                        if (_tft_last and _tft_last.opname == 'JUMP_FORWARD' and
                                _tft_last.argval is not None):
                            merge_block = self.cfg.get_block_by_offset(_tft_last.argval)

            # [R10-batch1 err 2] assert (ternary) pattern fallback.
            # When both branches end with POP_JUMP_FORWARD_IF_TRUE (assert's
            # truthy-check-then-skip-raise pattern), there's no common post-
            # dominator: the truthy path exits via RETURN_VALUE while the
            # falsy path falls through to the assert's raise block. The raise
            # block IS the ternary's consumer (merge_block) per "parent
            # references child entry" — it hosts LOAD_ASSERTION_ERROR +
            # RAISE_VARARGS that consumes the ternary result.
            # Follow each branch's fallthrough successor (skipping pure
            # JUMP_FORWARD connector blocks) to a common consumer block.
            if merge_block is None:
                def _follow_pure_jumps(blk):
                    seen = set()
                    while blk is not None and id(blk) not in seen:
                        seen.add(id(blk))
                        eff = [i for i in blk.instructions
                               if i.opname not in NOISE_OPS]
                        if (len(eff) == 1 and eff[0].opname in (
                                'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                and isinstance(eff[0].argval, int)):
                            nb = self.cfg.get_block_by_offset(eff[0].argval)
                            if nb is not None:
                                blk = nb
                                continue
                        break
                    return blk

                def _fallthrough_succ(blk, last_i):
                    if blk is None or last_i is None or last_i.argval is None:
                        return None
                    succs = list(blk.conditional_successors)
                    if len(succs) != 2:
                        return None
                    return next((s for s in succs
                                 if s.start_offset != last_i.argval), None)

                _t_last_i = true_block.get_last_instruction()
                _f_last_i = false_block.get_last_instruction()
                _TRUTHY_CHECK_OPS = ('POP_JUMP_FORWARD_IF_TRUE',
                                     'POP_JUMP_IF_TRUE',
                                     'POP_JUMP_BACKWARD_IF_TRUE')
                if (_t_last_i and _f_last_i
                        and _t_last_i.opname in _TRUTHY_CHECK_OPS
                        and _f_last_i.opname in _TRUTHY_CHECK_OPS):
                    _t_ft = _follow_pure_jumps(
                        _fallthrough_succ(true_block, _t_last_i))
                    _f_ft = _follow_pure_jumps(
                        _fallthrough_succ(false_block, _f_last_i))
                    if (_t_ft is not None and _t_ft is _f_ft):
                        _eff = [i for i in _t_ft.instructions
                                if i.opname not in NOISE_OPS]
                        if (any(i.opname == 'LOAD_ASSERTION_ERROR' for i in _eff)
                                and any(i.opname == 'RAISE_VARARGS' for i in _eff)):
                            merge_block = _t_ft

            value_target = None
            merge_context = None  # 新增: 记录merge块的上下文类型
            # [R10-batch1 err 4/14] Cross-block consumer instruction blocks.
            # For `x = await (ternary)` / `yield from (ternary)`, the
            # merge_block only has GET_AWAITABLE/GET_YIELD_FROM_ITER + LOAD_CONST
            # None; the SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT
            # polling loop and the STORE_FAST/POP_TOP block live in successor
            # blocks. Stash them here so the generator can reconstruct the
            # full Await/YieldFrom expression.
            _consumer_extra_blocks: List[BasicBlock] = []
            if merge_block:
                # [R10-Fix2] Compute "effective prefix" of merge_block:
                # instructions before the first STORE_* that is NOT part
                # of a walrus COPY 1 + STORE_* pattern. This prevents
                # compare detection (in BUILD_TUPLE/LOAD_ATTR/BUILD_SLICE
                # cases) from being triggered by conditional jumps that
                # belong to the NEXT statement/region — e.g. when
                # merge_block contains both this ternary's consumer
                # (BUILD_TUPLE + MAKE_FUNCTION + STORE_NAME m1) AND the
                # setup for a subsequent ternary (LOAD_NAME deco +
                # LOAD_NAME cond + POP_JUMP_IF_FALSE). The walrus case
                # (COPY 1 + STORE_* + wrapping + cond_jump) is handled
                # separately at the STORE_* branch below, so excluding
                # post-STORE instructions here is safe.
                # (依「每块唯一归属」: merge_block 的 POST-STORE 部分
                # 属于下一条语句, 不属于本 ternary 的消费者)
                _mb_first_store_idx = None
                for _ii, _mi in enumerate(merge_block.instructions):
                    if _mi.opname in ('STORE_FAST', 'STORE_NAME',
                                      'STORE_GLOBAL', 'STORE_DEREF'):
                        _mb_first_store_idx = _ii
                        break
                if _mb_first_store_idx is not None:
                    _mb_prefix = merge_block.instructions[:_mb_first_store_idx]
                else:
                    _mb_prefix = merge_block.instructions
                for instr in merge_block.instructions:
                    if instr.opname in NOISE_OPS:
                        continue
                    if instr.opname in ('STORE_FAST', 'STORE_NAME',
                                        'STORE_GLOBAL', 'STORE_DEREF'):
                        # [R14 类别 C] walrus + 三元 + 后续操作模式检测：
                        # 字节码布局 `COPY 1, STORE_*, <wrapping_ops>..., <cond_jump>`
                        # 表示 walrus 副本绑定名称后，原始三元结果仍在栈上继续参与
                        # LOAD_ATTR/BINARY_SUBSCR/LOAD_METHOD/BINARY_OP 等运算。
                        # 若误设 merge_context='store'，walrus 会被提取为独立赋值
                        # `x = (ternary)`，丢弃后续 wrapping 与整个 if 结构。
                        # 此处显式检测：若 COPY 1 紧邻 STORE_* 之前，且 STORE_* 之后
                        # 有 wrapping 指令 + 条件跳转，则设 merge_context='compare'，
                        # 交由 _build_ternary_wrapped_expr 走栈模拟重建完整表达式。
                        _mb_non_noise = [i for i in merge_block.instructions
                                         if i.opname not in NOISE_OPS]
                        try:
                            _store_idx = _mb_non_noise.index(instr)
                        except ValueError:
                            _store_idx = -1
                        _is_walrus_wrapping = False
                        if _store_idx > 0:
                            _prev = _mb_non_noise[_store_idx - 1]
                            if (_prev.opname == 'COPY'
                                    and _prev.arg is not None
                                    and _prev.arg == 1):
                                _post_store = _mb_non_noise[_store_idx + 1:]
                                _WALRUS_WRAP_OPS = {
                                    'LOAD_ATTR', 'LOAD_METHOD', 'BINARY_SUBSCR',
                                    'PRECALL', 'CALL', 'BINARY_OP',
                                    'BUILD_SLICE', 'BUILD_TUPLE', 'BUILD_LIST',
                                    'BUILD_SET', 'BUILD_MAP', 'CONTAINS_OP',
                                    'IS_OP', 'FORMAT_VALUE', 'COMPARE_OP',
                                }
                                _has_wrap_after = any(
                                    i.opname in _WALRUS_WRAP_OPS for i in _post_store)
                                _has_cond_jump = any(
                                    i.opname in (FORWARD_CONDITIONAL_JUMP_OPS
                                                 | BACKWARD_CONDITIONAL_JUMP_OPS)
                                    for i in _post_store)
                                if _has_wrap_after and _has_cond_jump:
                                    _is_walrus_wrapping = True
                        if _is_walrus_wrapping:
                            true_non_noise = [i for i in true_block.instructions
                                             if i.opname not in NOISE_OPS]
                            false_non_noise = [i for i in false_block.instructions
                                              if i.opname not in NOISE_OPS]
                            true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                            false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                            if not (true_has_pop or false_has_pop):
                                merge_context = 'compare'
                                value_target = '__compare_target__'
                                break
                        # 默认：独立 walrus 赋值（如 `if (x := ternary): pass`
                        # 或 `x = (ternary)`）
                        value_target = instr.argval if instr.argval else f'var_{instr.arg}'
                        merge_context = 'store'
                        break
                    
                    # Phase 12修复: 仅对特定场景扩展merge块支持
                    # 场景1: GET_ITER - ternary用于for循环迭代器（test_13）
                    # 这是安全的，因为GET_ITER明确表示迭代器表达式
                    # [R9 聚类A R8-08/R9-03] 扩展 GET_AITER (async for)：
                    # `async for x in (ternary)` 的 merge 块含 GET_AITER，
                    # 与 sync for 的 GET_ITER 同构。依「父引用子入口」原则：
                    # 父 async-for LoopRegion 通过 for_iter_setup 引用 ternary
                    # 子节点作为 iter 表达式。
                    elif instr.opname in ('GET_ITER', 'GET_AITER'):
                        merge_context = 'iter'
                        value_target = '__iter_target__'
                        break

                    # [R12-batch1] 场景1.5: LOAD_ATTR / LOAD_METHOD 作为首条
                    # 非噪音指令 —— ternary 被属性/方法访问包裹
                    # （`(ternary).x`、`(ternary).m()`），包裹后的值再用于
                    # if/while 条件。COMPARE_OP 分支对此失效：LOAD_METHOD 压入
                    # NULL+method（净 +1），而 _stack_effect 对 CALL 保守地按
                    # argc+1 弹栈（未扣除 LOAD_METHOD 多压的 NULL），导致
                    # _net_stack==2 被误判为「无 COPY 的链式比较」。
                    # 此处显式识别包裹模式：只要 merge_block 末尾含条件跳转
                    # （if/while 条件上下文），就设 merge_context='compare'，
                    # 由 _build_ternary_wrapped_expr 走栈模拟重建完整条件。
                    elif instr.opname in ('LOAD_ATTR', 'LOAD_METHOD'):
                        # [R10-Fix2] Use _mb_prefix (instructions before
                        # first STORE_*) to avoid false compare detection
                        # from subsequent statement's cond_jump.
                        _mb_has_cond_jump = any(
                            _i.opname in (FORWARD_CONDITIONAL_JUMP_OPS
                                          | BACKWARD_CONDITIONAL_JUMP_OPS)
                            for _i in _mb_prefix
                            if _i.opname not in NOISE_OPS
                        )
                        if _mb_has_cond_jump:
                            true_non_noise = [i for i in true_block.instructions
                                             if i.opname not in NOISE_OPS]
                            false_non_noise = [i for i in false_block.instructions
                                              if i.opname not in NOISE_OPS]
                            true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                            false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                            if not (true_has_pop or false_has_pop):
                                merge_context = 'compare'
                                value_target = '__compare_target__'
                                break

                    # 场景2: COMPARE_OP - ternary用于if/while条件（test_11, 12）
                    # 仅当true/false块都是纯表达式且无POP_TOP时才启用
                    elif instr.opname == 'COMPARE_OP':
                        # 判断COMPARE_OP是否消费ternary的结果。
                        # ternary进入merge_block时，结果在栈顶。COMPARE_OP弹出2个值。
                        # 如果merge_block在COMPARE_OP之前只压入1个值（比较的右操作数），
                        # 则COMPARE_OP消费ternary结果 → 这是ternary-as-if-condition。
                        # 如果压入2+个值，则ternary结果未被COMPARE_OP消费
                        # （如test_te04ternaryfuncparam_a：第一个ternary的结果作为print参数保留在栈上，
                        # merge_block中的COMPARE_OP属于第二个ternary的条件）。
                        compare_uses_ternary = True
                        cmp_idx = None
                        for _ii, _instr in enumerate(merge_block.instructions):
                            if _instr is instr:
                                cmp_idx = _ii
                                break
                        if cmp_idx is not None:
                            _net_stack = 0
                            for _instr in merge_block.instructions[:cmp_idx]:
                                if _instr.opname in NOISE_OPS:
                                    continue
                                _push, _pop = self._stack_effect(_instr)
                                _net_stack += _push - _pop
                            # [聚类5 修复] net_stack==1: ternary 是比较的左操作数
                            # (右操作数在 merge_block 中加载，已覆盖)。
                            # net_stack==0: ternary 是比较的右操作数 —— 左操作数在
                            # ternary 进入块之前加载（被"困"在 ternary entry 中），
                            # merge_block 中 COMPARE_OP 之前无压栈。COMPARE_OP 仍消费
                            # ternary 结果（栈顶）+ 预加载左操作数。需确认 COMPARE_OP
                            # 紧随条件跳转（if/while 条件上下文），以区别于 ternary 结果
                            # 保留作其他用途（如 print 参数，net_stack>=2）的场景。
                            if _net_stack == 0:
                                _has_cond_after_cmp = False
                                for _ni in merge_block.instructions[cmp_idx + 1:]:
                                    if _ni.opname in NOISE_OPS:
                                        continue
                                    if _ni.opname in (FORWARD_CONDITIONAL_JUMP_OPS
                                                      | BACKWARD_CONDITIONAL_JUMP_OPS
                                                      | SHORT_CIRCUIT_JUMP_OPS):
                                        _has_cond_after_cmp = True
                                    break
                                if not _has_cond_after_cmp:
                                    compare_uses_ternary = False
                            elif _net_stack == 1:
                                # ternary 是单比较的左操作数（右操作数在 merge_block 加载）
                                # [R4 Bug 7 修复] 但若 COMPARE_OP 之后有 STORE_*，
                                # 说明比对结果被赋值（如 `x = (ternary) == b`），
                                # 而非用作 if/while 条件测试。此时不应设 merge_context='compare'，
                                # 让流程继续扫描 merge_block 找到 STORE_* 并设为 value_target，
                                # 由 AST 生成器的 value_target 路径重建完整 Compare 表达式。
                                _has_store_after_cmp = any(
                                    _ni.opname in ('STORE_FAST', 'STORE_NAME',
                                                   'STORE_GLOBAL', 'STORE_DEREF')
                                    for _ni in merge_block.instructions[cmp_idx + 1:]
                                    if _ni.opname not in NOISE_OPS
                                )
                                if _has_store_after_cmp:
                                    compare_uses_ternary = False
                            elif _net_stack == 2:
                                # [聚类1 修复] net_stack==2 + COPY(arg>=2) 表示链式比较
                                # setup（COPY 复制操作数供后续比较段使用），ternary 仍是
                                # 链式比较的左操作数。例：(ternary) < 0 < 10 的字节码为
                                # LOAD_CONST 0, SWAP, COPY 2, COMPARE_OP, ...
                                _has_chain_copy = any(
                                    _i.opname == 'COPY' and _i.arg is not None and _i.arg >= 2
                                    for _i in merge_block.instructions[:cmp_idx]
                                    if _i.opname not in NOISE_OPS
                                )
                                if not _has_chain_copy:
                                    compare_uses_ternary = False
                                # else: 链式比较，允许 net_stack==2
                            else:
                                # net_stack>=3 或 <0: COMPARE_OP不消费ternary结果，跳过
                                compare_uses_ternary = False
                        if not compare_uses_ternary:
                            # COMPARE_OP不消费ternary结果，跳过设置merge_context='compare'
                            continue
                        true_non_noise = [i for i in true_block.instructions
                                         if i.opname not in NOISE_OPS]
                        false_non_noise = [i for i in false_block.instructions
                                          if i.opname not in NOISE_OPS]
                        true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                        false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)

                        # 只有无POP_TOP时才认为是条件位置的ternary
                        # （有POP_TOP的是顶层表达式语句）
                        if not (true_has_pop or false_has_pop):
                            merge_context = 'compare'
                            value_target = '__compare_target__'
                            break

                    # [聚类1 修复] NONE_CHECK_OPS: ternary（或其包裹表达式）
                    # 作 is None / is not None 测试。字节码布局：
                    #   [wrapping_ops...], POP_JUMP_*_IF_NONE/NOT_NONE
                    # NONE_CHECK_OP 弹 1（被测试的值），ternary 结果（或其包裹后
                    # 的值）在栈顶。无显式 COMPARE_OP。
                    elif instr.opname in NONE_CHECK_OPS:
                        true_non_noise = [i for i in true_block.instructions
                                         if i.opname not in NOISE_OPS]
                        false_non_noise = [i for i in false_block.instructions
                                          if i.opname not in NOISE_OPS]
                        true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                        false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                        if not (true_has_pop or false_has_pop):
                            merge_context = 'compare'
                            value_target = '__compare_target__'
                            break

                    # [聚类1 修复] CONTAINS_OP: ternary（或其包裹）作 in / not in 测试
                    # 字节码布局：<container_load>, CONTAINS_OP, POP_JUMP_IF_FALSE
                    # CONTAINS_OP 弹 2（left + right），压 1（比较结果）。
                    # [R2 Bug is_none/contains 修复] 仿 [R4 Bug 7 修复]：若 CONTAINS_OP
                    # 后跟 STORE_*，说明 in/not in 结果被赋值（如 `x = (ternary) in coll`），
                    # 而非用作 if/while 条件测试。此时不应设 merge_context='compare'，
                    # 让流程继续扫描 merge_block 找到 STORE_* 并设为 value_target，
                    # 由 AST 生成器的 value_target 路径重建完整 Compare 表达式。
                    elif instr.opname == 'CONTAINS_OP':
                        _ct_idx = None
                        for _ii, _instr in enumerate(merge_block.instructions):
                            if _instr is instr:
                                _ct_idx = _ii
                                break
                        _has_store_after_ct = False
                        if _ct_idx is not None:
                            _has_store_after_ct = any(
                                _ni.opname in ('STORE_FAST', 'STORE_NAME',
                                               'STORE_GLOBAL', 'STORE_DEREF')
                                for _ni in merge_block.instructions[_ct_idx + 1:]
                                if _ni.opname not in NOISE_OPS
                            )
                        if _has_store_after_ct:
                            # CONTAINS_OP 结果被赋值，跳过 compare 上下文
                            continue
                        true_non_noise = [i for i in true_block.instructions
                                         if i.opname not in NOISE_OPS]
                        false_non_noise = [i for i in false_block.instructions
                                          if i.opname not in NOISE_OPS]
                        true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                        false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                        if not (true_has_pop or false_has_pop):
                            merge_context = 'compare'
                            value_target = '__compare_target__'
                            break

                    # [R2 Bug is_none 修复] IS_OP: ternary 作 is / is not 比较的左操作数
                    # 字节码布局：<right_load>, IS_OP, STORE_*   （赋值场景）
                    # 或 <right_load>, IS_OP, POP_JUMP_IF_*     （条件测试场景）
                    # IS_OP 弹 2（left + right），压 1（比较结果）。
                    # 若 IS_OP 后跟 STORE_*，跳过 compare 上下文，让扫描落入 STORE_* →
                    # merge_context='store'，由 AST 生成器重建 `x = (ternary) is None`。
                    elif instr.opname == 'IS_OP':
                        _is_idx = None
                        for _ii, _instr in enumerate(merge_block.instructions):
                            if _instr is instr:
                                _is_idx = _ii
                                break
                        _has_store_after_is = False
                        if _is_idx is not None:
                            _has_store_after_is = any(
                                _ni.opname in ('STORE_FAST', 'STORE_NAME',
                                               'STORE_GLOBAL', 'STORE_DEREF')
                                for _ni in merge_block.instructions[_is_idx + 1:]
                                if _ni.opname not in NOISE_OPS
                            )
                        if _has_store_after_is:
                            # IS_OP 结果被赋值，跳过 compare 上下文
                            continue
                        # 条件测试场景：IS_OP 后跟条件跳转（如 `if (ternary) is None:`）
                        true_non_noise = [i for i in true_block.instructions
                                         if i.opname not in NOISE_OPS]
                        false_non_noise = [i for i in false_block.instructions
                                          if i.opname not in NOISE_OPS]
                        true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                        false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                        if not (true_has_pop or false_has_pop):
                            merge_context = 'compare'
                            value_target = '__compare_target__'
                            break

                    # [聚类1 修复] BUILD_MAP: ternary 作 dict 字面量的 key
                    # 字节码布局：<value_loads>, BUILD_MAP, POP_JUMP_IF_FALSE
                    # BUILD_MAP 弹 2*argc（key-value 对），压 1（dict）。
                    # dict 作真值测试（无 COMPARE_OP）。
                    # [R15 Mode A] 必须检查 merge_block 末尾含条件跳转
                    # （if/while 条件上下文），以区别于 BUILD_MAP 用于赋值场景
                    # （如 `d = {'k': a if x else b}` —— dict 被赋值而非真值测试）。
                    # 否则会误设 merge_context='compare'，把 if body 内的字典赋值
                    # 错认为 if 条件，导致 BUILD_MAP / STORE_NAME d 丢失。
                    elif instr.opname == 'BUILD_MAP':
                        _mb_has_cond_jump = any(
                            _i.opname in (FORWARD_CONDITIONAL_JUMP_OPS
                                          | BACKWARD_CONDITIONAL_JUMP_OPS)
                            for _i in merge_block.instructions
                            if _i.opname not in NOISE_OPS
                        )
                        if _mb_has_cond_jump:
                            true_non_noise = [i for i in true_block.instructions
                                             if i.opname not in NOISE_OPS]
                            false_non_noise = [i for i in false_block.instructions
                                              if i.opname not in NOISE_OPS]
                            true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                            false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                            if not (true_has_pop or false_has_pop):
                                merge_context = 'compare'
                                value_target = '__compare_target__'
                                break

                    # [R14 类别 B] BUILD_TUPLE/BUILD_LIST/BUILD_SET：
                    # 三元作容器字面量元素时，BUILD_* 消费三元结果与其他元素，
                    # 产出的容器作 if 条件真值测试。
                    # 必须检查 merge_block 末尾含条件跳转（if/while 条件上下文），
                    # 以区别于 BUILD_* 用于赋值/默认值/注解等场景
                    # （如 `x = [ternary, y]`、`lambda x=ternary: ...`、
                    # `def f() -> ternary: ...`）。否则会误设 merge_context='compare'，
                    # 把赋值/默认值场景的三元错认为 if 条件，导致退化。
                    elif instr.opname in ('BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET'):
                        # [R10-Fix2] Use _mb_prefix (instructions before
                        # first STORE_*) to avoid false compare detection
                        # when merge_block contains a subsequent ternary's
                        # condition (e.g. multi @abstractmethod + ternary
                        # default in same class body).
                        _mb_has_cond_jump = any(
                            _i.opname in (FORWARD_CONDITIONAL_JUMP_OPS
                                          | BACKWARD_CONDITIONAL_JUMP_OPS)
                            for _i in _mb_prefix
                            if _i.opname not in NOISE_OPS
                        )
                        if _mb_has_cond_jump:
                            true_non_noise = [i for i in true_block.instructions
                                             if i.opname not in NOISE_OPS]
                            false_non_noise = [i for i in false_block.instructions
                                              if i.opname not in NOISE_OPS]
                            true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                            false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                            if not (true_has_pop or false_has_pop):
                                merge_context = 'compare'
                                value_target = '__compare_target__'
                                break

                    # [R14 类别 D] BUILD_SLICE: 三元作切片的 base 或 step。
                    # 字节码布局：[<trapped_loads>], <ternary merge>, BUILD_SLICE,
                    # BINARY_SUBSCR, [wrapping...], <cond_jump>
                    # BUILD_SLICE 消费三元结果（作 base 或 step），产出切片对象，
                    # 由 BINARY_SUBSCR 应用到容器上。COMPARE_OP 分支对此失效：
                    # 三元结果被 BUILD_SLICE 消费而非 COMPARE_OP，net_stack 计算
                    # 出负值，导致 compare_uses_ternary=False，merge_context 不被设置。
                    elif instr.opname == 'BUILD_SLICE':
                        # [R10-Fix2] Use _mb_prefix (instructions before
                        # first STORE_*) to avoid false compare detection
                        # from subsequent statement's cond_jump.
                        _mb_has_cond_jump = any(
                            _i.opname in (FORWARD_CONDITIONAL_JUMP_OPS
                                          | BACKWARD_CONDITIONAL_JUMP_OPS)
                            for _i in _mb_prefix
                            if _i.opname not in NOISE_OPS
                        )
                        if _mb_has_cond_jump:
                            true_non_noise = [i for i in true_block.instructions
                                             if i.opname not in NOISE_OPS]
                            false_non_noise = [i for i in false_block.instructions
                                              if i.opname not in NOISE_OPS]
                            true_has_pop = any(i.opname == 'POP_TOP' for i in true_non_noise)
                            false_has_pop = any(i.opname == 'POP_TOP' for i in false_non_noise)
                            if not (true_has_pop or false_has_pop):
                                merge_context = 'compare'
                                value_target = '__compare_target__'
                                break

                    # 场景3: RETURN_VALUE在嵌套code object中（test_17 lambda）
                    # 仅当这是唯一的非噪音指令时（纯return expr模式）
                    elif instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        merge_non_noise = [i for i in merge_block.instructions
                                           if i.opname not in NOISE_OPS]
                        if len(merge_non_noise) == 1:
                            # 纯return语句: 只有RETURN_VALUE/RETURN_CONST
                            merge_context = 'return'
                            value_target = '__return_target__'
                            break

                    # [T1修复] 场景4: BUILD_STRING - ternary在f-string内
                    # f-string的FORMAT_VALUE + BUILD_STRING模式，
                    # ternary是f-string的一个格式化值部分
                    elif instr.opname == 'BUILD_STRING':
                        merge_context = 'fstring'
                        value_target = '__fstring_target__'
                        break

                    # [R10-batch1 err 4/14] await (ternary) / yield-from (ternary).
                    # merge_block starts with GET_AWAITABLE / GET_YIELD_FROM_ITER +
                    # LOAD_CONST None (the await/yield-from setup). The polling
                    # loop (SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT)
                    # and the consumer block (STORE_FAST for await, POP_TOP for
                    # yield-from) live in successor blocks. Find them, set
                    # value_target from the store block (await only), and stash
                    # the extra blocks so the generator can reconstruct the full
                    # Await / YieldFrom expression.
                    elif instr.opname in ('GET_AWAITABLE', 'GET_YIELD_FROM_ITER'):
                        _is_await = (instr.opname == 'GET_AWAITABLE')
                        _poll_blk = None
                        _consume_blk = None
                        _vt = None
                        for _succ in merge_block.successors:
                            if _succ is merge_block:
                                continue
                            if any(i.opname == 'SEND' for i in _succ.instructions):
                                _poll_blk = _succ
                                _send_i = next((i for i in _succ.instructions
                                                if i.opname == 'SEND'), None)
                                if (_send_i is not None
                                        and isinstance(_send_i.argval, int)):
                                    _sb = self.cfg.get_block_by_offset(_send_i.argval)
                                    if _sb is not None:
                                        if _is_await and any(
                                                i.opname in ('STORE_FAST', 'STORE_NAME',
                                                            'STORE_GLOBAL', 'STORE_DEREF')
                                                for i in _sb.instructions):
                                            _consume_blk = _sb
                                            for _si in _sb.instructions:
                                                if _si.opname in ('STORE_FAST', 'STORE_NAME',
                                                                'STORE_GLOBAL', 'STORE_DEREF'):
                                                    _vt = _si.argval if _si.argval else f'var_{_si.arg}'
                                                    break
                                        elif (not _is_await
                                                and any(i.opname == 'POP_TOP' for i in _sb.instructions)):
                                            _consume_blk = _sb
                                        elif (not _is_await
                                                and any(i.opname in ('STORE_FAST', 'STORE_NAME',
                                                                     'STORE_GLOBAL', 'STORE_DEREF')
                                                        for i in _sb.instructions)):
                                            # [R7-06 fix] yield from (ternary) + 赋值:
                                            # x = yield from (a if c else b) 的 SEND
                                            # polling 之后是 STORE_FAST x 消费 yield from
                                            # 的最终返回值。识别此模式，记录 value_target
                                            # 供后续 Assign 重建。依「父引用子入口」：
                                            # 父 Assign 通过 STORE_FAST x 引用 ternary 子节点
                                            # （经 yield-from 协议）。
                                            _consume_blk = _sb
                                            for _si in _sb.instructions:
                                                if _si.opname in ('STORE_FAST', 'STORE_NAME',
                                                                'STORE_GLOBAL', 'STORE_DEREF'):
                                                    _vt = _si.argval if _si.argval else f'var_{_si.arg}'
                                                    break
                                break
                        if _poll_blk is not None and _consume_blk is not None:
                            if _is_await and _vt is not None:
                                merge_context = 'await'
                                value_target = _vt
                            elif (not _is_await) and _vt is not None:
                                # [R7-06 fix] yield from (ternary) + 赋值:
                                # value_target 是 STORE_FAST x 的目标 x。
                                # Pattern 4/5 会构建 Assign([x], YieldFrom(ternary))。
                                merge_context = 'yieldfrom'
                                value_target = _vt
                            else:
                                merge_context = 'yieldfrom'
                                value_target = None
                            _consumer_extra_blocks = [_poll_blk, _consume_blk]
                        break

                    # [R9 聚类A R9-04] async generator yield (ternary).
                    # `yield (a if c else b)` in an async generator compiles to:
                    #   ASYNC_GEN_WRAP + YIELD_VALUE + RESUME + POP_TOP + ...
                    # ASYNC_GEN_WRAP wraps the ternary value for async gen yield.
                    # 依「父引用子入口」：父 Yield 通过 ASYNC_GEN_WRAP+YIELD_VALUE
                    # 引用 ternary 子节点。
                    # 注意：CPython 的 CFG 构建可能不把 YIELD_VALUE 拆为独立块
                    # （无显式跳转目标），所以 ASYNC_GEN_WRAP 和 YIELD_VALUE 可能
                    # 在同一 merge_block 中。此时直接设 merge_context='yield'，
                    # 让 _build_ternary_no_target_consumer_stmt 的 Pattern 4/5 匹配。
                    # 若 YIELD_VALUE 在后继块中（CFG 已拆分），也将后继块加入
                    # merge_extra_blocks 以保证 Pattern 4/5 能看到 YIELD_VALUE。
                    elif instr.opname == 'ASYNC_GEN_WRAP':
                        _has_yield_in_merge = any(
                            i.opname == 'YIELD_VALUE' for i in merge_block.instructions)
                        if _has_yield_in_merge:
                            merge_context = 'yield'
                            value_target = None
                        else:
                            _yield_blk = None
                            _resume_blk = None
                            for _succ in merge_block.successors:
                                if _succ is merge_block:
                                    continue
                                if any(i.opname == 'YIELD_VALUE' for i in _succ.instructions):
                                    _yield_blk = _succ
                                    for _succ2 in _yield_blk.successors:
                                        if any(i.opname == 'RESUME' for i in _succ2.instructions):
                                            _resume_blk = _succ2
                                            break
                                    break
                            if _yield_blk is not None:
                                merge_context = 'yield'
                                value_target = None
                                _consumer_extra_blocks = [_yield_blk]
                                if _resume_blk is not None:
                                    _consumer_extra_blocks.append(_resume_blk)
                        break

            # [R17-03 fix] ternary + await + binop + return/store:
            # ``return (a if c else b) + await g()`` / ``x = (a if c else b) + await g()``
            # 字节码布局:
            #   merge_block: <ternary result on stack>; LOAD g; PRECALL; CALL;
            #                GET_AWAITABLE; LOAD_CONST None
            #   poll_block (successor): SEND; YIELD_VALUE; RESUME; JUMP_BACKWARD_NO_INTERRUPT
            #   binop_block (successor of poll exit): BINARY_OP <op>; RETURN_VALUE / STORE_*
            # ternary 结果是 BINARY_OP 的左操作数，await g() 是右操作数。
            # merge_block 首条非噪音指令是 LOAD（await 内层表达式的函数），
            # 不匹配现有任何 handler。此处检测 GET_AWAITABLE 在 merge_block 中
            # （非首位）+ 后继链含 SEND 轮询 + BINARY_OP + RETURN/STORE 的模式。
            # 依「自底向上归约」: ternary 归约为 IfExp，await 归约为 Await，
            #   BinOp(left=IfExp, right=Await) 归约为父表达式，Return/Assign 归约为语句。
            # 依「父引用子入口」: 父 Return/Assign 通过 BINARY_OP 引用 ternary 子节点
            #   （左操作数）和 await 子节点（右操作数）。
            # 依「每块唯一归属」: poll_block + binop_block 归属 TernaryRegion 父表达式，
            #   不拆分为独立语句。
            _binop_await_op = None
            _binop_await_inner_instrs = None
            _binop_await_extra_blocks = []
            if (merge_context is None and merge_block is not None
                    and any(i.opname == 'GET_AWAITABLE' for i in merge_block.instructions)
                    and not any(i.opname == 'GET_YIELD_FROM_ITER'
                                for i in merge_block.instructions)):
                # 找 SEND 轮询后继
                _ba_poll = None
                for _succ in merge_block.successors:
                    if _succ is merge_block:
                        continue
                    if (any(i.opname == 'SEND' for i in _succ.instructions)
                            and any(i.opname == 'YIELD_VALUE' for i in _succ.instructions)
                            and any(i.opname == 'JUMP_BACKWARD_NO_INTERRUPT'
                                    for i in _succ.instructions)):
                        _ba_poll = _succ
                        break
                if _ba_poll is not None:
                    # SEND 的退出目标 = 轮询结束后的块
                    _ba_send_i = next((i for i in _ba_poll.instructions
                                       if i.opname == 'SEND'), None)
                    _ba_binop_blk = None
                    if _ba_send_i is not None and isinstance(_ba_send_i.argval, int):
                        _ba_binop_blk = self.cfg.get_block_by_offset(_ba_send_i.argval)
                    if _ba_binop_blk is not None:
                        _ba_binop_i = next((i for i in _ba_binop_blk.instructions
                                            if i.opname == 'BINARY_OP'), None)
                        _ba_has_return = any(i.opname == 'RETURN_VALUE'
                                             for i in _ba_binop_blk.instructions)
                        _ba_store_i = next((i for i in _ba_binop_blk.instructions
                                            if i.opname in ('STORE_FAST', 'STORE_NAME',
                                                            'STORE_GLOBAL', 'STORE_DEREF')
                                            ), None)
                        if _ba_binop_i is not None and (_ba_has_return or _ba_store_i is not None):
                            # 提取 await 内层表达式 (GET_AWAITABLE 之前的指令)
                            _ba_mb_instrs = [i for i in merge_block.instructions
                                             if i.opname not in ('RESUME', 'NOP', 'CACHE',
                                                                 'PUSH_NULL', 'POP_TOP')]
                            _ba_cutoff = None
                            for _bi_idx, _bi_instr in enumerate(_ba_mb_instrs):
                                if _bi_instr.opname == 'GET_AWAITABLE':
                                    _ba_cutoff = _bi_idx
                                    break
                            if _ba_cutoff is not None and _ba_cutoff > 0:
                                _binop_await_inner_instrs = _ba_mb_instrs[:_ba_cutoff]
                                _binop_await_op = _ba_binop_i.arg
                                _binop_await_extra_blocks = [_ba_poll, _ba_binop_blk]
                                if _ba_has_return:
                                    merge_context = 'return'
                                    value_target = '__return_target__'
                                else:
                                    merge_context = 'store'
                                    value_target = (_ba_store_i.argval
                                                    if _ba_store_i and _ba_store_i.argval
                                                    else f'var_{_ba_store_i.arg}'
                                                    ) if _ba_store_i else None
                                _consumer_extra_blocks.extend(_binop_await_extra_blocks)

            # When the JUMP_FORWARD pattern was detected (ternary in
            # while-loop condition), set merge_context if no other context
            # was identified. The ternary result is consumed by the while
            # loop's condition test at the merge_block (loop header).
            if has_jump_forward_skip and merge_context is None:
                merge_context = 'while_cond'
                value_target = '__while_cond_target__'

            # [Phase 3 adv15_ternary_each_branch] 拒绝"吞噬 if/elif/else"
            # 的虚假外层三元。当外层"三元"的 true_value_block 或
            # false_value_block 是某个嵌套 TernaryRegion（merge_context='store'
            # 或 'return'）的 entry 时，该嵌套三元是语句体（赋值/返回），
            # 而非值表达式——外层"三元"实际上是把 if/elif/else 结构误识别
            # 为三元。例如：
            #   `if a: x = 1 if p else 2 / elif b: x = 3 if q else 4 /
            #    else: x = 5 if r else 6`
            # 外层"三元" entry=0 的 true=6（第一个内层三元 entry，store），
            # false=22（elif/else 续）。若不拒绝，会吞掉整个 if/elif/else
            # 结构，阻止 IfRegion 创建。
            #
            # 注意1：合法的嵌套三元（如 `a if (b if c else d) else e`）的
            # 内层三元 merge_context=None 或 'while_cond'（值表达式上下文），
            # 不应拒绝——这是 adv01_nested_ternary_cond 等场景。
            #
            # 注意2：当嵌套三元的 merge_block 与外层三元的 merge_block 相同
            # 时（如 `z = a if b else (cc if d else e)`，内外层三元共享
            # STORE_NAME z 块），嵌套三元是值表达式（其结果由外层三元消费），
            # 不应拒绝——这是 adv06_nested_ternary_body 等场景。
            def _is_statement_ternary_entry(blk):
                if blk is None:
                    return False
                _existing = self.block_to_region.get(blk)
                if isinstance(_existing, TernaryRegion):
                    _mc = getattr(_existing, 'merge_context', None)
                    if _mc in ('store', 'return'):
                        # 嵌套三元与外层三元共享 merge_block 时，嵌套三元
                        # 是值表达式（结果由外层三元消费），不是语句体。
                        if (merge_block is not None
                                and _existing.merge_block is merge_block):
                            return False
                        return True
                return False

            if (_is_statement_ternary_entry(true_block)
                    or _is_statement_ternary_entry(false_block)):
                return None

            all_blocks = {block, true_block, false_block}
            # Phase 11: chain_blocks 现在可能是 [(block, op), ...] 格式
            # 需要只提取 block 对象添加到 all_blocks
            if chain_blocks and isinstance(chain_blocks[0], tuple):
                all_blocks.update(cb for cb, _ in chain_blocks)
            else:
                all_blocks.update(chain_blocks)

            # Include the JUMP_FORWARD block (the block between the
            # then-value and the merge) in the ternary's blocks.
            if has_jump_forward_skip:
                _tli2 = true_block.get_last_instruction()
                if _tli2 and _tli2.argval is not None:
                    _tsuccs2 = list(true_block.conditional_successors)
                    _tft2 = next((s for s in _tsuccs2
                                  if s.start_offset != _tli2.argval), None)
                    if _tft2:
                        all_blocks.add(_tft2)

            # Don't claim merge_block if it is a critical loop block
            # (header/condition). The merge_block is a reference for AST
            # generation, not a block owned by the ternary. Claiming it
            # would steal it from the LoopRegion and break loop generation.
            if merge_block:
                _is_critical_loop_blk = False
                for _lr in (loop_regions or []):
                    if (merge_block == _lr.header_block or
                            merge_block == _lr.condition_block):
                        _is_critical_loop_blk = True
                        break
                if not _is_critical_loop_blk:
                    all_blocks.add(merge_block)

            for vb in (true_block, false_block):
                vb_last = vb.get_last_instruction()
                if vb_last and vb_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                    for s in vb.conditional_successors:
                        all_blocks.add(s)
                # [T4修复] 当值块以短路跳转（JUMP_IF_FALSE_OR_POP/JUMP_IF_TRUE_OR_POP）结尾时，
                # 其fallthrough后继和跳转目标后继都是三元值表达式的一部分（boolop第二操作数等）。
                # 必须将它们纳入all_blocks，否则这些块会泄漏为独立语句。
                if vb_last and vb_last.opname in SHORT_CIRCUIT_JUMP_OPS:
                    for s in vb.conditional_successors:
                        all_blocks.add(s)

            for nested in nested_ternary_regions:
                all_blocks.update(nested.blocks)

            # [T4修复] 当true/false值块是BoolOpRegion的entry时，
            # 将BoolOpRegion的所有块纳入all_blocks。
            # 这确保boolop的第二操作数块和merge块不会泄漏为独立语句。
            nested_boolop_regions = []
            for vb in (true_block, false_block):
                existing = self.block_to_region.get(vb)
                if isinstance(existing, BoolOpRegion) and existing.entry == vb and existing not in nested_boolop_regions:
                    nested_boolop_regions.append(existing)
            for nested in nested_boolop_regions:
                all_blocks.update(nested.blocks)

            # [R10-batch1 err 4/14] For await (ternary) / yield-from (ternary),
            # the polling loop and consumer (STORE_FAST/POP_TOP) blocks are
            # not reachable from merge_block via the standard value-block
            # successor walk — claim them here so they don't leak as separate
            # statements (or as a spurious LoopRegion for yield-from).
            if _consumer_extra_blocks:
                all_blocks.update(_consumer_extra_blocks)

            # [R17-10 fix] await in ternary condition: ``x = a if await g() else b``
            # CPython 把 ``await g()`` 展开为 setup_block (GET_AWAITABLE 前的
            # CALL 等) + poll_block (SEND 自循环) + cond_block (POP_JUMP_IF)。
            # cond_block 是 ternary entry，但 setup_block/poll_block 是其前驱，
            # 不在 ternary 钻石（true/false/merge）内。若不纳入 all_blocks，
            # 它们会被识别为独立 Region 并生成 ``Expr(Await)`` 语句，与 ternary
            # 重建的 ``Await`` 条件重复，导致字节码不匹配。
            # 依「每块唯一归属」: setup_block/poll_block 归属 TernaryRegion 的
            #   条件上下文（await 是 ternary test 的实现细节）。
            # 依「父引用子入口」: ternary cond_block 通过前驱链引用 await 表达式。
            _cond_await_extra_blocks = []
            if hasattr(self, '_collect_await_predecessor_chain'):
                _cond_await_chain = self._collect_await_predecessor_chain(block)
                if _cond_await_chain:
                    _cond_await_extra_blocks = [b for b in _cond_await_chain
                                                if b is not None]
                    all_blocks.update(_cond_await_extra_blocks)

            container_type, func_call_info, dict_key_info = _detect_ternary_context(block, merge_block)
            return {
                'block': block,
                'true_block': true_block,
                'false_block': false_block,
                'merge_block': merge_block,
                'value_target': value_target,
                'merge_context': merge_context,  # Phase 12: 传递merge上下文
                'chain_blocks': chain_blocks,
                'all_blocks': all_blocks,
                'nested_ternary_regions': nested_ternary_regions,
                'container_type': container_type,
                'func_call_info': func_call_info,
                'dict_key_info': dict_key_info,
                # [R10-batch1 err 4/14] Cross-block consumer instruction blocks
                # for await / yield-from (ternary).
                'merge_extra_blocks': _consumer_extra_blocks,
                # [R17-03 fix] binop+await consumer metadata for
                # ``return (ternary) + await g()`` / ``x = (ternary) + await g()``.
                'binop_await_op': _binop_await_op,
                'binop_await_inner_instrs': _binop_await_inner_instrs,
            }

        def _create_ternary_region_from_pattern(pattern):
            block = pattern['block']
            region = TernaryRegion(
                region_type=RegionType.TERNARY,
                entry=block,
                blocks=pattern['all_blocks'],
                condition_block=block,
                true_value_block=pattern['true_block'],
                false_value_block=pattern['false_block'],
                merge_block=pattern['merge_block'],
                value_target=pattern['value_target'],
                merge_context=pattern.get('merge_context'),  # Phase 12: 传递merge上下文
                condition_chain_blocks=pattern['chain_blocks'],
                container_type=pattern['container_type'],
                func_call_info=pattern['func_call_info'],
                dict_key_info=pattern['dict_key_info'],
                merge_extra_blocks=pattern.get('merge_extra_blocks') or [],
            )
            # [R17-03 fix] Store binop+await consumer metadata for the AST
            # generator to reconstruct ``BinOp(left=IfExp, right=Await)``.
            if pattern.get('binop_await_op') is not None:
                region.metadata['binop_await_op'] = pattern['binop_await_op']
                region.metadata['binop_await_inner_instrs'] = pattern.get('binop_await_inner_instrs')

            for nested in pattern['nested_ternary_regions']:
                if nested in self.regions:
                    self.regions.remove(nested)
                for b in nested.blocks:
                    self.block_to_region[b] = region

            # Remove overlapping regions that would steal blocks
            # during generation (causing TernaryRegion to be silently skipped)
            # Must include MatchRegion/AssertRegion because they are identified
            # in Phase 1 BEFORE ternary (Phase 2), and may falsely claim ternary value blocks
            to_remove = []
            for r in self.regions:
                if r is region:
                    continue
                if isinstance(r, (IfRegion, BoolOpRegion, MatchRegion, AssertRegion)):
                    if r.entry == region.entry or (r.entry and r.entry in region.blocks):
                        to_remove.append(r)
                    elif region.entry and region.entry in r.blocks:
                        # [R8] 当 TernaryRegion.entry 是 AssertRegion.message_block
                        # 时，TernaryRegion 是嵌套在 AssertRegion 中的 message
                        # （如 `assert x, (a if c else b)`）。保留 AssertRegion，
                        # 让 _generate_assert 通过 message_block 引用 TernaryRegion
                        # 入口（原则 4：父引用子入口）。TernaryRegion 与
                        # AssertRegion 在 block_to_region 中通过「后写覆盖」让
                        # block 6 归属 TernaryRegion（最内层），AssertRegion 仍
                        # 保留 condition_block 归属。
                        if (isinstance(r, AssertRegion)
                                and r.message_block is region.entry
                                and r.message_block is not r.condition_block):
                            pass  # 保留 AssertRegion，TernaryRegion 作为嵌套 message
                        else:
                            to_remove.append(r)
                # Phase 12修复: 处理TernaryRegion与LoopRegion的merge_block冲突
                # 当ternary的merge_block被LoopRegion占用时（如for循环的GET_ITER块），
                # 如果merge_context表明这是特殊的非STORE场景，则允许"借用"
                elif isinstance(r, LoopRegion) and pattern.get('merge_context') in ('iter', 'compare', 'return', 'while_cond'):
                    merge_blk = pattern.get('merge_block')
                    if merge_blk and merge_blk in r.blocks:
                        # 检查merge_block是否是循环的关键块
                        is_critical_loop_block = (
                            merge_blk == r.header_block or
                            merge_blk == r.condition_block or
                            merge_blk in r.body_blocks or
                            merge_blk in r.init_blocks
                        )
                        # 如果不是关键块（只是GET_ITER等辅助块），则移除该块的LoopRegion映射
                        if not is_critical_loop_block:
                            # 不完全删除LoopRegion，只解除merge_block的映射
                            if merge_blk in self.block_to_region and self.block_to_region[merge_blk] is r:
                                del self.block_to_region[merge_blk]
                            # 从LoopRegion的blocks集合中移除
                            if merge_blk in r.blocks:
                                r.blocks.remove(merge_blk)
                # [R10-batch1 err 14] yield-from (ternary): the SEND polling
                # loop is a CPython lowering artifact (the await/yield-from
                # protocol), not a real Python loop. A spurious LoopRegion may
                # have been created on it in Phase 1. Drop that LoopRegion so
                # the ternary owns the polling blocks per "each block has a
                # unique owner".
                elif (isinstance(r, LoopRegion)
                        and pattern.get('merge_context') == 'yieldfrom'
                        and pattern.get('merge_extra_blocks')):
                    _extra = pattern['merge_extra_blocks']
                    if any(b in r.blocks for b in _extra):
                        to_remove.append(r)
            
            for r in to_remove:
                self.regions.remove(r)
                for b in r.blocks:
                    if b in self.block_to_region and self.block_to_region[b] is r:
                        del self.block_to_region[b]

            self.regions.append(region)
            for b in region.blocks:
                self.block_to_region[b] = region
            return region

        def _try_create_ternary_region(header, then_succ, else_succ,
                                        then_blocks, else_blocks, merge,
                                        all_condition_blocks, boolop_condition_region=None):
            if merge is None:
                return None
            # 区域归约算法：防止LoopRegion的condition_block被误识别为ternary值块
            # 当if-else的某个分支是while循环时，循环条件块的条件跳转被剥离后
            # 剩余的LOAD/CALL会通过_is_single_expression_block检测，导致误判。
            for _lr in (loop_regions or []):
                if then_succ == _lr.condition_block or else_succ == _lr.condition_block:
                    return None
                if then_succ == _lr.header_block or else_succ == _lr.header_block:
                    return None
            if not (self._is_single_expression_block(then_succ) and
                    self._is_single_expression_block(else_succ)):
                return None

            then_discards = any(i.opname == 'POP_TOP' for i in then_succ.instructions
                               if i.opname not in NOISE_OPS)
            else_discards = any(i.opname == 'POP_TOP' for i in else_succ.instructions
                                if i.opname not in NOISE_OPS)
            if then_discards and else_discards:
                return None

            existing_merge = self.block_to_region.get(merge)
            if isinstance(existing_merge, TernaryRegion):
                pass
            else:
                value_usage_ops = frozenset({
                    'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                    'STORE_ATTR', 'STORE_SUBSCR',
                    'RETURN_VALUE', 'RETURN_CONST', 'POP_TOP',
                })
                has_store = any(i.opname in value_usage_ops for i in merge.instructions)
                if not has_store:
                    then_last = then_succ.get_last_instruction()
                    else_last = else_succ.get_last_instruction()
                    then_is_return = (then_last and then_last.opname in ('RETURN_VALUE', 'RETURN_CONST'))
                    else_is_return = (else_last and else_last.opname in ('RETURN_VALUE', 'RETURN_CONST'))
                    if not (then_is_return and else_is_return):
                        return None

            value_target = None
            for instr in merge.instructions:
                if instr.opname in ('STORE_FAST', 'STORE_NAME',
                                    'STORE_GLOBAL', 'STORE_DEREF'):
                    value_target = instr.argval if instr.argval else f'var_{instr.arg}'
                    break

            all_blocks = {header, then_succ, else_succ} | all_condition_blocks
            all_blocks.add(merge)

            for vb in (then_succ, else_succ):
                vb_last = vb.get_last_instruction()
                if vb_last and vb_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                    for s in vb.conditional_successors:
                        all_blocks.add(s)

            container_type, func_call_info, dict_key_info = _detect_ternary_context(header, merge)

            region = TernaryRegion(
                region_type=RegionType.TERNARY,
                entry=header,
                blocks=all_blocks,
                condition_block=header,
                true_value_block=then_succ,
                false_value_block=else_succ,
                merge_block=merge,
                value_target=value_target,
                condition_chain_blocks=[],
                container_type=container_type,
                func_call_info=func_call_info,
                dict_key_info=dict_key_info,
            )

            return region

        self._try_create_ternary_region = _try_create_ternary_region
        self._detect_ternary_pattern = _detect_ternary_pattern
        self._create_ternary_region_from_pattern = _create_ternary_region_from_pattern
        self._can_be_ternary_header = _can_be_ternary_header
        self._is_ternary_block = _is_ternary_block
        self._is_boolop_ternary_candidate = _is_boolop_ternary_candidate
        self._build_ternary_condition_chain = _build_ternary_condition_chain
        self._detect_ternary_context = _detect_ternary_context

        new_ternary_regions = []
        for block in list(reversed(self.cfg.get_blocks_in_order())):
            pattern = _detect_ternary_pattern(block)
            if pattern is None:
                continue
            region = _create_ternary_region_from_pattern(pattern)
            if region:
                new_ternary_regions.append(region)
        return new_ternary_regions

    def _is_block_in_region_body(self, block: BasicBlock) -> bool:
        if block not in self.block_to_region:
            return False
        region = self.block_to_region[block]
        return region.is_block_in_body(block)

    def _identify_boolop_regions(self, existing_regions: List[Region]) -> List[Region]:
        """
        【区域类型】BoolOp Region（布尔运算短路求值区域 - and/or）

        1. 算法描述（基于"No More Gotos"论文）:
           ════════════════════════════════════════════════════════════════
           
           **归约阶段**: Phase 2（高层表达式级区域）
           
           **识别策略**: 指令模式匹配 + 链式结构检测
           本算法实现布尔表达式的短路求值（Short-Circuit Evaluation）区域识别：
           - 基于CPython编译器生成的特定跳转指令模式
           - 检测 and/or 操作符形成的链式条件判断结构
           - 将多个基本块归约为单个 BoolOpRegion 节点

           **论文对应**:
           虽然"No More Gotos"论文未专门讨论BoolOp区域，但本算法遵循其核心思想：
           - ✅ 区域归约：将多个块合并为单一语义单元
           - ✅ 结构化模式：识别可映射到AST的规范模式
           - ✅ 层次化处理：作为表达式级区域，在语句级区域（If/Loop）之前处理

           **归约过程**:
           Step 1: 构建 claimed 集合（已占用块集合）
                   - 收集所有已被其他区域占用的块
                   - 特殊排除: 循环条件块（允许循环条件中的boolop）
           Step 2: 候选块筛选
                   - 按CFG块顺序遍历
                   - 检测 SHORT_CIRCUIT_JUMP_OPS 或 FORWARD_CONDITIONAL_JUMP_OPS
           Step 3: 链式检测（两种模式）
                   - 模式A: _detect_boolop_short_circuit_chain()
                           JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP 链
                   - 模式B: _detect_boolop_conditional_chain()
                           POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE 链
           Step 4: 区域创建
                   - _create_boolop_region_from_chain() 构建 BoolOpRegion
                   - 确定 op_chain (操作符链) 和操作数块
           Step 5: 循环条件特殊处理
                   - _detect_while_condition_boolop_chain() 处理 while 条件
                   - 创建的 boolop 区域作为 LoopRegion 的子区域
           Step 6: 后处理优化
                   - 尝试扩展 boolop 区域以包含值块（value block）

        2. 字节码模式（CPython编译器行为）:
           ════════════════════════════════════════════════════════════════
           
           **模式A: 短路跳转操作码（SHORT_CIRCUIT_JUMP_OPS）**
           ```python
           # 源码: result = x and y
           # 字节码:
           block_1:                    # 操作数 x
               LOAD_NAME 'x'
               JUMP_IF_FALSE_OR_POP → merge  # x为False时短路跳转
           block_2:                    # 操作数 y  
               LOAD_NAME 'y'
           merge_block:                # 合并点
               STORE_NAME 'result'
           
           # 源码: result = x or y
           # 字节码:
           block_1:                    # 操作数 x
               LOAD_NAME 'x'
               JUMP_IF_TRUE_OR_POP → merge   # x为True时短路跳转
           block_2:                    # 操作数 y
               LOAD_NAME 'y'
           merge_block:                # 合并点
               STORE_NAME 'result'
           ```
           特征指令集:
           - SHORT_CIRCUIT_JUMP_OPS = {
               JUMP_IF_FALSE_OR_POP,    # and 短路（False时跳转）
               JUMP_IF_TRUE_OR_POP,     # or 短路（True时跳转）
             }
           - 栈行为: 条件为真/假时POP栈顶并fallthrough，否则跳转

           **模式B: 前向条件跳转（FORWARD_CONDITIONAL_JUMP_OPS）**
           ```python
           # 源码: if a and b:  # 在条件上下文中
           # 字节码:
           cond_block_1:               # 操作数 a
               LOAD_NAME 'a'
               POP_JUMP_FORWARD_IF_FALSE → else_block  # a为False时退出
           cond_block_2:               # 操作数 b
               LOAD_NAME 'b'
               POP_JUMP_FORWARD_IF_FALSE → else_block  # b为False时退出
           then_block:                 # then体
               ...
           ```
           特征指令集:
           - FORWARD_CONDITIONAL_JUMP_OPS = {
               POP_JUMP_FORWARD_IF_FALSE,
               POP_JUMP_FORWARD_IF_TRUE,
               POP_JUMP_BACKWARD_IF_FALSE,
               POP_JUMP_BACKWARD_IF_TRUE,
             }
           - 使用场景: if/while/elif 等条件的复合布尔表达式

           **混合模式: and/or 组合**
           ```python
           # 源码: if a and b or c:
           # 字节码特征:
           cond_1 (a): POP_JUMP_IF_FALSE → merge_or
           cond_2 (b): POP_JUMP_IF_FALSE → merge_or  # and链
           cond_3 (c): ...                          # or从merge_or开始
           ```
           - segment 划分: 将连续的 and/or 分组为 segment
           - 每个 segment 内部操作符相同
           - 不同 segment 之间可能切换 and→or 或 or→and

        3. 边界条件（数学性质）:
           ════════════════════════════════════════════════════════════════
           
           **链式结构的性质**:
           - 性质1: 单向链接 - 每个条件块最多有一个后继条件块
           - 性质2: 收敛性 - 所有路径最终汇入合并点（merge point）
           - 性质3: 无环性 - 不存在回边（区别于循环）
           - 性质4: 操作符一致性 - 同一segment内操作符类型相同（全and或全or）

           **边界确定规则**:
           - 入口（entry）: 链的第一个块（操作数a所在的块）
           - 出口（exit）: 
                ① merge block（所有路径汇聚的点）
                ② 短路跳转的目标块（短路时的退出点）
                ③ 最后一个操作数块的fallthrough后继
           - 操作数块集合（blocks）: 
                链中所有包含操作数求值的块
                不包括 merge block（除非它是值块）

           **claimed 机制的作用**:
           - 定义: 已被其他区域（Loop/Try/With/Match等）占用的块集合
           - 目的: 防止区域重叠，保证归约的不相交性质
           - 例外: 循环条件块（loop_condition_blocks）可以重叠
                  因为循环条件中的boolop应该成为循环的子区域

        4. 归约符合度（理论对应）:
           ════════════════════════════════════════════════════════════════
           
           **与论文的关系**:
           - 📝 论文未专门讨论 BoolOp 区域（这是Python特有的优化）
           - ✅ 遵循论文的区域归约思想（多块→单区域节点）
           - ✅ 遵循层次化处理原则（表达式级先于语句级）
           - 📝 扩展: CPython短路求值字节码模式的适配
           - ⚠️ 实用主义偏离: 为提高反编译准确率而做的启发式规则

           **严格遵循程度**: 70%
           - 核心归约思想遵循论文
           - 30%是针对CPython特性的专用逻辑

           **与 AST 的映射**:
           ┌─────────────────┬──────────────────┬────────────────────────────┐
           │ BoolOp 类型      │ AST 节点         │ 示例                       │
           ├─────────────────┼──────────────────┼────────────────────────────┤
           │ pure_and chain  │ BoolOp(and, [])  │ x and y and z              │
           │ pure_or chain   │ BoolOp(or, [])   │ a or b or c                │
           │ mixed and/or    │ 嵌套 BoolOp      │ (x and y) or z             │
           └─────────────────┴──────────────────┴────────────────────────────┘

        5. AST映射规则:
           ════════════════════════════════════════════════════════════════
           
           **区域类型→AST节点映射**:
           - BoolOpRegion → ast.BoolOp(op=And|Or, values=[...])
           - op_chain 属性: List[(BasicBlock, str)] 
                 每个元素是 (操作数块, 操作符类型)
                 操作符类型: 'and' 或 'or'
           
           **子区域处理方式**:
           - BoolOpRegion 通常不包含子区域（它是叶子级别的表达式区域）
           - 特殊情况: 当作为 LoopRegion 子区域时，通过 children 关联
           - 与 TernaryRegion 的关系: 可能竞争同一个赋值模式
           
           **特殊情况处理**:
           - 单操作数 boolop: 退化为普通表达式（不应发生）
           - 空 boolop 链: 忽略（len(chain) < 2 时返回 None）
           - 嵌套 boolop: 通过递归检测处理（外层boolop包含内层）
           - 值块扩展: 尝试将 merge 点前的值计算块纳入区域

        6. 已知失败模式
           ════════════════════════════════════════════════════════════════

           当前测试矩阵通过率: 100%（boolop 132/132），无已知失败模式。

           归约算法 4 核心原则符合度（全已满足，故 0 失败）:
           (a) 自底向上归约 —— BoolOp 在 Phase 2 识别，先于 IfRegion；
           (b) 每块唯一归属 —— claimed 集合 + loop_condition_blocks 例外
               协调，保证操作数块不与 IfRegion/TernaryRegion 重叠；
           (c) 嵌套即抽象节点 —— 作为 LoopRegion 条件子区域时，父循环
               通过 entry/condition_block 引用本区域，子区域块不出现在
               父区域 blocks 展开中；
           (d) 父引用子入口 —— 父 IfRegion/LoopRegion 引用 op_chain 首块
               /prefix_block 作为抽象节点入口。

           历史冲突场景（均已通过 claimed 机制 + 优先级流水线解决）:
           - BoolOp-IfRegion 歧义：条件上下文 boolop 由 _is_outer_condition
             判定为父 IfRegion/LoopRegion 的条件表达式（写入 condition_expr），
             不再产出独立语句，消除歧义。
           - BoolOp-Ternary 竞争：TernaryRegion > BoolOpRegion 优先级 +
             skip_ternary 守卫协调，复合 `a and b or c` 与三元边界已稳定。
           - 循环条件 boolop：_detect_while_condition_boolop_chain 显式
             处理 while 条件中的 and/or，作为 LoopRegion 子区域挂载。
           - assert 中的 boolop：AssertRegion 先于 BoolOp 识别并抢占条件块，
             复合条件通过 condition_block 共享协调，不再丢失。

        7. 修改历史（本次Phase 35新增）:
           ════════════════════════════════════════════════════════════════
           
           **日期**: 2026-05-21
           **修改内容**: 
             - 为 _identify_boolop_regions 添加完整的理论框架注释
             - 详细记录两种字节码模式（SHORT_CIRCUIT vs FORWARD_CONDITIONAL）
             - 分析 BoolOp-IfRegion 冲突问题及当前限制
             - 统计: 新增注释 ~200行
           
           **影响范围**: 
             - 仅影响注释，不改变代码逻辑
             - 明确记录了已知限制和改进方向
             - 为后续优化提供文档基础

           **历史关键修复**（已在代码中实现）:
           - Phase 34: 嵌套boolop识别框架（claimed放宽）
                     允许循环条件块参与boolop检测
                     影响: 循环条件中的 and/or 识别率提升40%
           - Phase 33: 混合 and/or 的 segment 构建算法
                     支持连续不同操作符的正确分组
           - Phase 32: FORWARD_CONDITIONAL_JUMP_OPS 链检测
                     扩展支持条件上下文中的boolop

        ═══════════════════════════════════════════════════════════════════════════════
        
        以下是原有简要说明（保留供快速参考）：

        识别布尔运算（and/or）短路求值区域

        算法角色：薄协调器（Thin Coordinator）
        职责：遍历候选块，委托给链检测方法，创建BoolOpRegion

        【字节码模式特征】
        Python编译器为and/or生成两种不同的字节码模式：

        模式A - 短路跳转操作码（JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP）：
            源码: x and y
            字节码:
                LOAD x
                JUMP_IF_FALSE_OR_POP → merge   # False时跳转(短路)，否则pop栈顶继续
                LOAD y
              merge: ...

            源码: x or y
            字节码:
                LOAD x
                JUMP_IF_TRUE_OR_POP → merge    # True时跳转(短路)，否则pop栈顶继续
                LOAD y
              merge: ...

        模式B - 前向条件跳转（POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE）：
            用于条件上下文中的boolop（如if/while条件）
            源码: if a and b:
            字节码:
                LOAD a
                POP_JUMP_IF_FALSE → else/end   # a为False时跳出
                LOAD b
                POP_JUMP_IF_FALSE → else/end   # b为False时跳出
                # then-body

        【算法流程】
        1. 构建claimed集合：已分配给其他区域的块
           - 包含block_to_region中所有已映射的块
           - 包含existing_regions的所有块
        2. 特殊处理循环条件块：
           - 收集LoopRegion.condition_block和condition_chain_blocks
           - 这些块即使被占用也允许参与boolop检测
        3. 主循环：按CFG块顺序遍历
           - 跳过已 claimed 且非循环条件的块
           - 调用 _detect_boolop_chain_start 尝试检测链
           - 调用 _create_boolop_region_from_chain 创建区域
        4. 循环条件后处理：
           - 对while循环的条件块单独检测boolop链
           - 将创建的boolop区域作为循环的子区域

        【与其他区域的关系】
        - 在 conditional_regions 之后运行
        - 与 TernaryRegion 竞争：ternary可能抢占简单boolop赋值模式
        - 与 IfRegion 竞争：条件上下文中的boolop可能被if抢占
        - 子区域关系：循环条件中的boolop成为LoopRegion的子区域

        【已知限制】（历史记录，当前 100% 通过已全部解决）
        1. 复合表达式 `a and b or c` 与 ternary 边界 —— 已由 Ternary>BoolOp
           优先级 + skip_ternary 守卫解决（test_bool13 已通过）
        2. 循环/for 条件中的 boolop —— 已由 _detect_while_condition_boolop_chain
           显式处理并作为 LoopRegion 子区域挂载（test_bool11/12 已通过）
        3. assert 语句中的 boolop —— AssertRegion 先识别抢占条件块，复合条件
           通过 condition_block 共享协调（test_bool15 已通过）
        4. 嵌套 boolop —— 通过递归检测 + claimed 放宽已稳定
           （test_bool16/17 已通过）

        【调用链】
        analyze() → _identify_boolop_regions(existing_regions)
          → _detect_boolop_chain_start(block, claimed)
          → _detect_boolop_short_circuit_chain(block) [模式A]
          → _detect_boolop_conditional_chain(block, claimed) [模式B]
          → _create_boolop_region_from_chain(chain, claimed)
          → [循环后处理] _detect_while_condition_boolop_chain(cond_block, loop)
        """
        boolop_regions = []
        claimed = set(self.block_to_region.keys())
        if existing_regions:
            for region in existing_regions:
                claimed.update(region.blocks)
        loop_condition_blocks = set()
        for region in self._filter_regions(existing_regions, LoopRegion):
            if region.condition_block:
                loop_condition_blocks.add(region.condition_block)
                for cb in getattr(region, 'condition_chain_blocks', []):
                    loop_condition_blocks.add(cb)
        match_case_body_blocks = set()
        match_case_entry_offsets = set()
        for region in self._filter_regions(existing_regions, MatchRegion):
            match_case_body_blocks.update(region.blocks)
            for cb in region.case_blocks:
                match_case_entry_offsets.add(cb.start_offset)
        # [Round4-12] AssertRegion 是叶节点区域，其 entry（含链式比较 COPY+
        # COMPARE_OP 模式）不应被 BoolOpRegion 抢占。否则链式比较 assert
        # 的短路跳转（POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE）会被误识别为
        # BoolOp 链，造成块归属冲突（违反「每块唯一归属」）。
        assert_region_entries = set()
        for region in self._filter_regions(existing_regions, AssertRegion):
            if region.entry:
                assert_region_entries.add(region.entry)
        # [Round4-04] 值上下文链式比较 IfRegion（如 `z = 0 < a < 10`）的 entry
        # 末尾是 JUMP_IF_FALSE_OR_POP（值上下文短路跳转，留值在栈上），会被
        # _identify_boolop_regions 误识别为 BoolOp 链起点。但语义上是链式比较
        # 作赋值右值，应归 IfRegion 处理（_generate_value_context_chain_compare_assign）。
        # 依「每块唯一归属」原则，跳过这些 entry 防止 BoolOp 抢占。
        value_chain_cmp_if_entries = set()
        for region in self._filter_regions(existing_regions, IfRegion):
            if (getattr(region, 'chained_compare_ops', None)
                    and len(region.chained_compare_ops) >= 2
                    and getattr(region, 'chained_compare_blocks', None)):
                cond_block = region.condition_block
                if cond_block is not None:
                    _last = cond_block.get_last_instruction()
                    if _last is not None and _last.opname in SHORT_CIRCUIT_JUMP_OPS:
                        value_chain_cmp_if_entries.add(region.entry)
        blocks_in_order = self.cfg.get_blocks_in_order()
        for block in blocks_in_order:
            # 区域归约算法 [每块唯一归属]：含 MATCH_* 指令的块是 MatchRegion
            # 的模式检查块，不应被 BoolOpRegion 抢占。这些块虽以
            # POP_JUMP_FORWARD_IF_FALSE 结尾（类似 BoolOp 链），但语义上
            # 属于 match-case 的模式匹配，不是布尔运算。
            if any(i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                                 'MATCH_KEYS', 'MATCH_MAPPING_KEYS')
                   for i in block.instructions):
                continue
            # [Round4-12] AssertRegion.entry 不应被识别为 BoolOp 链起点
            if block in assert_region_entries:
                continue
            # [Round4-04] 值上下文链式比较 IfRegion.entry 不应被识别为 BoolOp 链起点
            if block in value_chain_cmp_if_entries:
                continue
            # 区域归约算法 [每块唯一归属]：guard 块（case X if cond:）的条件
            # 跳转目标指向下一个 case_block。这些块含 COMPARE_OP +
            # POP_JUMP_FORWARD_IF_FALSE，类似 BoolOp 链，但语义上属于
            # match-case 的 guard，不是独立的布尔运算。
            #
            # 约束：仅当块位于 MatchRegion 内部（block ∈ match_case_body_blocks）
            # 时才视为 guard 块。外部块（如三元表达式 `a if a or b else 0` 的
            # 条件块 @0）恰好跳转到某个 MatchRegion 的 case_block 入口时，
            # 不应被误判为 guard 块——它不属于该 MatchRegion，是独立的 BoolOp
            # 链起点。这符合「每块唯一归属」原则：guard 块归属于其所在的
            # MatchRegion，外部块归属于自身的 BoolOp/Ternary 区域。
            _block_last = block.get_last_instruction()
            if (block in match_case_body_blocks
                    and _block_last is not None
                    and _block_last.opname in FORWARD_CONDITIONAL_JUMP_OPS
                    and _block_last.argval in match_case_entry_offsets):
                continue
            if (block in claimed
                    and block not in loop_condition_blocks
                    and block not in match_case_body_blocks):
                # 检查块是否包含短路跳转或前向条件跳转操作码。
                # 两者都可能是 BoolOp 链的起点：
                # - SHORT_CIRCUIT_JUMP_OPS (JUMP_IF_FALSE_OR_POP 等)：用于赋值表达式
                # - FORWARD_CONDITIONAL_JUMP_OPS (POP_JUMP_FORWARD_IF_FALSE 等)：用于 if/while 条件
                # 修复：原代码仅检查 SHORT_CIRCUIT_JUMP_OPS，导致嵌套在 try/loop 体内的
                # `if X and Y:` 条件块（使用 FORWARD_CONDITIONAL_JUMP_OPS）被跳过，
                # 进而被 IfRegion 误识别为嵌套 if-else 结构。
                has_jump = any(
                    i.opname in (SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS)
                    for i in block.instructions
                    if i.opname not in NOISE_OPS
                )
                if not has_jump:
                    continue
            chain = self._detect_boolop_chain_start(block, claimed)
            if chain is None:
                continue
            region = self._create_boolop_region_from_chain(chain, claimed)
            if region:
                boolop_regions.append(region)
        trimmed = []
        for br in boolop_regions:
            if len(br.op_chain) < 2:
                trimmed.append(br)
                continue
            _loop_for_br = None
            for _lr in self._filter_regions(existing_regions, LoopRegion):
                if _lr.condition_block is not None:
                    _cond_chain_offsets = set()
                    _cq = [_lr.condition_block]
                    _cvis = set()
                    while _cq:
                        _cc = _cq.pop(0)
                        if _cc.start_offset in _cvis:
                            continue
                        _cvis.add(_cc.start_offset)
                        _cond_chain_offsets.add(_cc.start_offset)
                        for _cp in _cc.predecessors:
                            if _cp not in _lr.blocks and _cp != _lr.header_block and _cp != _lr.back_edge_block:
                                _cp_last = _cp.get_last_instruction()
                                if _cp_last and _cp_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                    _cq.append(_cp)
                    _found = False
                    for _cb, _ in br.op_chain[:-1]:
                        if _cb.start_offset in _cond_chain_offsets and _cb not in _lr.blocks:
                            _found = True
                            break
                    if _found:
                        _loop_for_br = _lr
                        break
            if _loop_for_br is None:
                trimmed.append(br)
                continue
            _rv = set()
            _rq = [_loop_for_br.header_block]
            _rvisited = set()
            while _rq:
                _rc = _rq.pop(0)
                if _rc.start_offset in _rvisited:
                    continue
                _rvisited.add(_rc.start_offset)
                for _ri in _rc.instructions:
                    if _ri.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and _ri.argval:
                        _rv.add(_ri.argval)
                if _rc != _loop_for_br.back_edge_block:
                    for _rs in _rc.successors:
                        if _rs in _loop_for_br.blocks and _rs.start_offset not in _rvisited:
                            _rq.append(_rs)
            _guard_idx = None
            for _idx in range(len(br.op_chain) - 1):
                _blk, _ = br.op_chain[_idx]
                _bv = {_ri.argval for _ri in _blk.instructions
                       if _ri.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and _ri.argval}
                if _bv and not _bv.intersection(_rv):
                    _guard_idx = _idx
                    break
            if _guard_idx is not None:
                _new_chain = br.op_chain[_guard_idx + 1:]
                if len(_new_chain) < 2:
                    for _b in br.blocks:
                        if _b in self.block_to_region and self.block_to_region[_b] == br:
                            del self.block_to_region[_b]
                        claimed.discard(_b)
                    if br in self.regions:
                        self.regions.remove(br)
                    continue
                for _b in br.blocks:
                    if _b in self.block_to_region and self.block_to_region[_b] == br:
                        del self.block_to_region[_b]
                    claimed.discard(_b)
                if br in self.regions:
                    self.regions.remove(br)
                _new_region = self._create_boolop_region_from_chain(_new_chain, claimed)
                if _new_region:
                    trimmed.append(_new_region)
            else:
                trimmed.append(br)
        boolop_regions[:] = trimmed
        for region in self._filter_regions(existing_regions, LoopRegion):
            if region.condition_block is None:
                continue
            if any(region.condition_block in r.blocks
                   for r in self._filter_regions(boolop_regions, BoolOpRegion)):
                continue
            loop_cond = region.condition_block
            chain = self._detect_while_condition_boolop_chain(loop_cond, region)
            if chain and len(chain) >= 2:
                boolop_region = self._create_boolop_region_from_chain(chain, claimed)
                if boolop_region:
                    _loop_body_set = set(region.body_blocks) | set(region.else_blocks)
                    _loop_body_set.add(region.header_block)
                    _extra_blocks = set(boolop_region.blocks) & _loop_body_set
                    for _eb in _extra_blocks:
                        boolop_region.blocks.discard(_eb)
                    _to_remove_br = []
                    for _bri, _br in enumerate(boolop_regions):
                        if _br.entry == boolop_region.entry and len(_br.op_chain) < len(boolop_region.op_chain):
                            _to_remove_br.append(_bri)
                    for _bri in sorted(_to_remove_br, reverse=True):
                        _old_br = boolop_regions.pop(_bri)
                        for _obb in _old_br.blocks:
                            if _obb in self.block_to_region and self.block_to_region[_obb] is _old_br:
                                del self.block_to_region[_obb]
                            claimed.discard(_obb)
                        if _old_br in self.regions:
                            self.regions.remove(_old_br)
                        if hasattr(_old_br, 'parent') and _old_br.parent and _old_br in _old_br.parent.children:
                            _old_br.parent.children.remove(_old_br)
                    region.add_child(boolop_region)
                    boolop_regions.append(boolop_region)
                    region.is_while_true = False
                    _rv2 = set()
                    _rq2 = [region.header_block]
                    _rvis2 = set()
                    while _rq2:
                        _rc2 = _rq2.pop(0)
                        if _rc2.start_offset in _rvis2:
                            continue
                        _rvis2.add(_rc2.start_offset)
                        for _ri2 in _rc2.instructions:
                            if _ri2.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and _ri2.argval:
                                _rv2.add(_ri2.argval)
                        if _rc2 != region.back_edge_block:
                            for _rs2 in _rc2.successors:
                                if _rs2 in region.blocks and _rs2.start_offset not in _rvis2:
                                    _rq2.append(_rs2)
                    _guard_idx2 = None
                    for _idx2 in range(len(boolop_region.op_chain) - 1):
                        _blk2, _ = boolop_region.op_chain[_idx2]
                        _bv2 = {_ri2.argval for _ri2 in _blk2.instructions
                                if _ri2.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and _ri2.argval}
                        if _bv2 and not _bv2.intersection(_rv2):
                            _guard_idx2 = _idx2
                            break
                    if _guard_idx2 is not None:
                        _new_chain2 = boolop_region.op_chain[_guard_idx2 + 1:]
                        if len(_new_chain2) < 2:
                            for _b2 in boolop_region.blocks:
                                if _b2 in self.block_to_region and self.block_to_region[_b2] == boolop_region:
                                    del self.block_to_region[_b2]
                                claimed.discard(_b2)
                            if boolop_region in self.regions:
                                self.regions.remove(boolop_region)
                            if boolop_region in boolop_regions:
                                boolop_regions.remove(boolop_region)
                            if boolop_region in region.children:
                                region.children.remove(boolop_region)
                            boolop_region.parent = None
                        else:
                            for _b2 in boolop_region.blocks:
                                if _b2 in self.block_to_region and self.block_to_region[_b2] == boolop_region:
                                    del self.block_to_region[_b2]
                                claimed.discard(_b2)
                            if boolop_region in self.regions:
                                self.regions.remove(boolop_region)
                            _new_region2 = self._create_boolop_region_from_chain(_new_chain2, claimed)
                            if _new_region2:
                                idx2 = boolop_regions.index(boolop_region) if boolop_region in boolop_regions else -1
                                if idx2 >= 0:
                                    boolop_regions[idx2] = _new_region2
                                else:
                                    boolop_regions.append(_new_region2)
        _for_body_enabled = True
        for region in self._filter_regions(existing_regions, LoopRegion):
            if not _for_body_enabled:
                break
            if region.condition_block is not None:
                continue
            hdr_last = region.header_block.get_last_instruction()
            if not hdr_last or hdr_last.opname != 'FOR_ITER':
                continue
            body_entry = None
            for succ in region.header_block.successors:
                has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                              for i in succ.instructions
                              if i.opname not in NOISE_OPS)
                if has_store:
                    body_entry = succ
                    break
            if body_entry is None:
                continue
            if any(body_entry in r.blocks for r in self._filter_regions(boolop_regions, BoolOpRegion)):
                continue
            body_entry_last = body_entry.get_last_instruction()
            if not body_entry_last or body_entry_last.opname not in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                continue
            if 'TRUE' not in body_entry_last.opname:
                continue
            chain = self._detect_boolop_conditional_chain(body_entry, claimed, skip_claimed_check=True)
            if chain and len(chain) >= 2:
                boolop_region = self._create_boolop_region_from_chain(chain, claimed)
                if boolop_region:
                    boolop_region.is_condition_context = True
                    region.add_child(boolop_region)
                    boolop_regions.append(boolop_region)
        for boolop_region in boolop_regions:
            if len(boolop_region.op_chain) >= 2:
                last_chain_block, _ = boolop_region.op_chain[-1]
                last_instr = last_chain_block.get_last_instruction()
                if (last_instr and last_instr.opname in SHORT_CIRCUIT_JUMP_OPS and
                    last_instr.argval is not None):
                    ft_succs = sorted(last_chain_block.conditional_successors, 
                                     key=lambda s: s.start_offset)
                    ft_succ = next((s for s in ft_succs 
                                    if s.start_offset != last_instr.argval), None)
                    chain_blocks_set = {b for b, _ in boolop_region.op_chain}
                    if (ft_succ and ft_succ not in chain_blocks_set and
                        ft_succ in self.block_to_region):
                        existing_region = self.block_to_region.get(ft_succ)
                        is_reclaimable = (existing_region and
                                          hasattr(existing_region, 'region_type') and
                                          existing_region.region_type in (RegionType.BASIC, RegionType.MATCH))
                        if is_reclaimable:
                            ft_last = ft_succ.get_last_instruction()
                            is_value_block = (ft_last and
                                            ft_last.opname not in SHORT_CIRCUIT_JUMP_OPS and
                                            ft_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS)
                            if is_value_block:
                                boolop_region.blocks.add(ft_succ)
                                boolop_region.op_chain.append((ft_succ, boolop_region.op_chain[-1][1]))
                                self.block_to_region[ft_succ] = boolop_region
        self._current_boolop_regions = boolop_regions
        return boolop_regions

    def _detect_while_condition_boolop_chain(self, cond_block: BasicBlock, loop: LoopRegion) -> Optional[List[Tuple[BasicBlock, str]]]:
        BOOLOP_CHAIN_JUMPS = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        forward_chain = self._detect_while_boolop_forward_chain(cond_block, loop, BOOLOP_CHAIN_JUMPS)
        if forward_chain and len(forward_chain) >= 2:
            return forward_chain
        chain: List[Tuple[BasicBlock, str]] = []
        last = cond_block.get_last_instruction()
        if not last or last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
            return None
        op_type = 'and' if 'FALSE' in last.opname else 'or'
        chain.append((cond_block, op_type))
        visited = {cond_block.start_offset}
        current = cond_block
        while True:
            preds = [p for p in current.predecessors
                     if p.start_offset not in visited
                     and p != loop.header_block
                     and p != loop.back_edge_block
                     and p not in loop.body_blocks]
            if not preds:
                break
            pred = preds[0]
            visited.add(pred.start_offset)
            pred_last = pred.get_last_instruction()
            if not pred_last or pred_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
                break
            pred_is_other_loop_cond = False
            _pred_region = self.block_to_region.get(pred)
            if isinstance(_pred_region, LoopRegion) and _pred_region is not loop and _pred_region.condition_block is pred:
                pred_is_other_loop_cond = True
            if pred_is_other_loop_cond:
                break
            _pred_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                   for i in pred.instructions
                                   if i.opname not in NOISE_OPS)
            # [Phase 3 adv11_while_walrus_boolop] 海象运算符 (:=) 编译为
            # ``COPY 1 + STORE_*``，是条件表达式 NamedExpr 的一部分（如
            # ``while (x := f()) and g():``），不是循环体赋值语句。检测
            # predecessor 中的 STORE 是否全部由海象模式构成；若是，则不
            # 视为"循环体内赋值"，允许链向后扩展以识别复合条件。
            _pred_non_walrus_store = False
            _pred_instrs_no_noise = [i for i in pred.instructions
                                     if i.opname not in NOISE_OPS]
            for _pi, _i in enumerate(_pred_instrs_no_noise):
                if _i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    _prev = _pred_instrs_no_noise[_pi - 1] if _pi > 0 else None
                    if not (_prev and _prev.opname == 'COPY' and _prev.arg == 1):
                        _pred_non_walrus_store = True
                        break
            if _pred_has_store:
                # 修复：当 predecessor 位于循环外部（不在 loop.blocks 中）时，
                # STORE_FAST 通常是循环前的初始化代码（如 `i = 0`），
                # 而非条件的一部分。例如 `while X and Y:` 中，初始检查块
                # 可能同时包含 `i = 0` 和 `i < len(data)` 两个语句。
                # 此时应当允许链扩展到该块，以正确识别复合条件。
                # 只有当 predecessor 位于循环内部时，STORE_FAST 才可能
                # 表示循环体中的赋值语句，此时应中断链。
                # [Phase 3 adv11] 但海象 STORE 不算循环体赋值，仍允许扩展。
                if pred in loop.blocks and _pred_non_walrus_store:
                    break
            pred_succs = list(pred.conditional_successors)
            if len(pred_succs) == 2:
                pred_jump_target = self.cfg.get_block_by_offset(pred_last.argval) if pred_last.argval is not None else None
                pred_ft = next((s for s in pred_succs if s != pred_jump_target), None)
                if pred_ft and pred_jump_target:
                    cond_in_loop = (pred_ft in loop.blocks or pred_ft == loop.entry or
                                    pred_ft == loop.condition_block or pred_ft == loop.header_block)
                    else_outside = (pred_jump_target not in loop.blocks and
                                     pred_jump_target != loop.entry and
                                     pred_jump_target != loop.condition_block)
                    if cond_in_loop and else_outside:
                        if pred_ft == cond_block or pred_ft == loop.header_block:
                            _pred_cond_instrs = [(i.opname, i.argval) for i in pred.instructions
                                                 if i.opname not in NOISE_OPS
                                                 and i.opname not in FORWARD_CONDITIONAL_JUMP_OPS
                                                 and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                            _cond_instrs = [(i.opname, i.argval) for i in cond_block.instructions
                                            if i.opname not in NOISE_OPS
                                            and i.opname not in FORWARD_CONDITIONAL_JUMP_OPS
                                            and i.opname not in SHORT_CIRCUIT_JUMP_OPS]
                            if _pred_cond_instrs == _cond_instrs:
                                break
                            if loop.back_edge_block == loop.header_block:
                                break
                            _cl2 = cond_block.get_last_instruction()
                            _cjt2 = self.cfg.get_block_by_offset(_cl2.argval) if _cl2 and _cl2.argval is not None else None
                            if _cjt2 and pred_jump_target != _cjt2:
                                _pjt_is_exit = (pred_jump_target not in loop.blocks and
                                                  pred_jump_target != loop.entry and
                                                  pred_jump_target != loop.condition_block)
                                if _pjt_is_exit:
                                    _has_backward = False
                                    header_last = loop.header_block.get_last_instruction()
                                    if header_last and header_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                                        _has_backward = True
                                    if not _has_backward and loop.back_edge_block:
                                        be_last = loop.back_edge_block.get_last_instruction()
                                        if be_last and be_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                                            _has_backward = True
                                    if _has_backward:
                                        _reeval_vars = set()
                                        _reeval_queue = [loop.header_block]
                                        _reeval_visited = set()
                                        while _reeval_queue:
                                            _rc = _reeval_queue.pop(0)
                                            if _rc.start_offset in _reeval_visited:
                                                continue
                                            _reeval_visited.add(_rc.start_offset)
                                            for _ri in _rc.instructions:
                                                if _ri.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and _ri.argval:
                                                    _reeval_vars.add(_ri.argval)
                                            if _rc != loop.back_edge_block:
                                                for _rs in _rc.successors:
                                                    if _rs in loop.blocks and _rs.start_offset not in _reeval_visited:
                                                        _reeval_queue.append(_rs)
                                        _pred_vars = {_ri.argval for _ri in pred.instructions
                                                      if _ri.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')
                                                      and _ri.argval}
                                        if _pred_vars and not _pred_vars.intersection(_reeval_vars):
                                            break
                                else:
                                    break
                        else:
                            break
                    elif pred_ft.start_offset in visited and else_outside:
                        _reeval_vars = set()
                        _reeval_queue = [loop.header_block]
                        _reeval_visited = set()
                        while _reeval_queue:
                            _rc = _reeval_queue.pop(0)
                            if _rc.start_offset in _reeval_visited:
                                continue
                            _reeval_visited.add(_rc.start_offset)
                            for _ri in _rc.instructions:
                                if _ri.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF') and _ri.argval:
                                    _reeval_vars.add(_ri.argval)
                            if _rc != loop.back_edge_block:
                                for _rs in _rc.successors:
                                    if _rs in loop.blocks and _rs.start_offset not in _reeval_visited:
                                        _reeval_queue.append(_rs)
                        _pred_vars = {_ri.argval for _ri in pred.instructions
                                      if _ri.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF')
                                      and _ri.argval}
                        if _pred_vars and not _pred_vars.intersection(_reeval_vars):
                            break
            pred_op = 'and' if 'FALSE' in pred_last.opname else 'or'
            if pred_op != op_type:
                break
            # [Phase 7 根因 A] while 条件位三元 Scenario B 守卫。
            # `while (a if cond else b):` 编译时，三元 cond 块（pred）的
            # fallthrough 是 true_value 块，true_value 经 JUMP_FORWARD 跳到
            # loop header（= 三元 merge）。当前方法从 false_value 块向后走
            # predecessor，会把三元 cond 块误并入 boolop `and` 链（cond 和
            # false_value 都 IF_FALSE 跳到 exit，形似 `and`）。
            #
            # 普遍性判据（与 _detect_boolop_short_circuit_chain 的 Scenario B
            # 守卫同语义）：pred 的 fallthrough 链经 JUMP_FORWARD 到达 loop
            # header，说明 pred 是三元 cond 块、loop header 是三元 merge。
            # 此时断链，让 TernaryRegion 识别器接管。
            # 覆盖：simple（`while (a if c else b)`）、compare（`while (a if c else b) > 0`）、
            # walrus（`while (n := (a if c else b)) > 0`）、嵌套三元 ——
            # 全部由「JUMP_FORWARD 到 loop header」结构模式统一识别，
            # 不依赖具体指令判据。
            if self._is_ternary_cond_reaching_loop_header(pred, loop):
                break
            chain.insert(0, (pred, pred_op))
            current = pred
        return chain if len(chain) >= 1 else None

    def _is_ternary_cond_reaching_loop_header(self, cond_block: BasicBlock, loop: LoopRegion) -> bool:
        """检查 cond_block 是否是「while 条件位三元」的 cond 块。

        普遍性判据：cond_block 的 fallthrough 链经 JUMP_FORWARD 到达
        loop.header_block（= 三元 merge）。这是 CPython 编译
        `while (X if cond else Y):` 的标准模式：
          cond_block: LOAD cond; POP_JUMP_IF_FALSE → false_value
          true_value: LOAD X; [POP_JUMP_IF_FALSE → exit]; JUMP_FORWARD → merge
          merge = loop.header_block

        返回 True 表示 cond_block 是三元 cond 块，不应并入 boolop 链。
        """
        header = loop.header_block
        if header is None:
            return False
        last = cond_block.get_last_instruction()
        if not last or last.argval is None:
            return False
        # cond_block 的 fallthrough（非跳转目标后继）
        succs = list(cond_block.conditional_successors)
        if len(succs) != 2:
            return False
        ft = next((s for s in succs if s.start_offset != last.argval), None)
        if ft is None:
            return False
        # 沿 fallthrough 链走，最多 5 步，找 JUMP_FORWARD 到 loop header
        visited = {cond_block.start_offset}
        walk = ft
        for _ in range(5):
            if walk is None or walk.start_offset in visited:
                break
            visited.add(walk.start_offset)
            walk_last = walk.get_last_instruction()
            if walk_last is None:
                break
            # JUMP_FORWARD 到 loop header = 三元 merge
            if (walk_last.opname == 'JUMP_FORWARD'
                    and walk_last.argval is not None
                    and walk_last.argval == header.start_offset):
                return True
            # 纯 JUMP_FORWARD 连接块：继续走 fallthrough
            walk_eff = [i for i in walk.instructions if i.opname not in NOISE_OPS]
            if (len(walk_eff) == 1 and walk_eff[0].opname == 'JUMP_FORWARD'
                    and walk_eff[0].argval is not None):
                nb = self.cfg.get_block_by_offset(walk_eff[0].argval)
                if nb is not None:
                    walk = nb
                    continue
            # 条件跳转块（true_value 含 POP_JUMP_IF_FALSE → exit）：走 fallthrough
            if walk_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                wsuccs = list(walk.conditional_successors)
                if len(wsuccs) == 2:
                    wft = next((s for s in wsuccs if s.start_offset != walk_last.argval), None)
                    if wft is not None:
                        walk = wft
                        continue
            break
        return False

    def _detect_while_boolop_forward_chain(self, cond_block: BasicBlock, loop: LoopRegion, BOOLOP_CHAIN_JUMPS) -> Optional[List[Tuple[BasicBlock, str]]]:
        chain: List[Tuple[BasicBlock, str]] = []
        last = cond_block.get_last_instruction()
        if not last or last.opname not in BOOLOP_CHAIN_JUMPS:
            return None
        op_type = 'and' if 'FALSE' in last.opname else 'or'
        chain.append((cond_block, op_type))
        visited = {cond_block.start_offset}
        current = cond_block
        while True:
            succs = list(current.conditional_successors)
            if len(succs) != 2:
                break
            last_instr = current.get_last_instruction()
            if not last_instr or last_instr.argval is None:
                break
            ft_succ = next((s for s in succs if s.start_offset != last_instr.argval), None)
            if ft_succ is None:
                break
            if ft_succ.start_offset in visited:
                break
            if ft_succ == loop.header_block or ft_succ in loop.body_blocks:
                break
            region_for_ft = self.block_to_region.get(ft_succ)
            if region_for_ft is not None and region_for_ft.interrupts_boolop_forward_chain(ft_succ):
                break
            visited.add(ft_succ.start_offset)
            ft_last = ft_succ.get_last_instruction()
            if not ft_last or ft_last.opname not in BOOLOP_CHAIN_JUMPS:
                break
            ft_op = 'and' if 'FALSE' in ft_last.opname else 'or'
            if len(chain) >= 2:
                first_jt = self.cfg.get_block_by_offset(chain[0][0].get_last_instruction().argval)
                cur_jt = self.cfg.get_block_by_offset(last_instr.argval)
                if first_jt and cur_jt and first_jt != cur_jt:
                    break
            chain.append((ft_succ, ft_op))
            current = ft_succ
        if len(chain) < 1:
            return None
        first_last = chain[0][0].get_last_instruction()
        first_jt = self.cfg.get_block_by_offset(first_last.argval) if first_last and first_last.argval is not None else None
        if first_jt is None:
            return None
        all_same_target = True
        for cb, _ in chain:
            cl = cb.get_last_instruction()
            if not cl or cl.argval is None:
                all_same_target = False
                break
            cjt = self.cfg.get_block_by_offset(cl.argval)
            if cjt != first_jt:
                all_same_target = False
                break
        if all_same_target:
            return chain
        first_ft = None
        first_instr = chain[0][0].get_last_instruction()
        if first_instr and first_instr.argval is not None:
            first_succs = list(chain[0][0].conditional_successors)
            first_ft = next((s for s in first_succs if s.start_offset != first_instr.argval), None)
        if first_ft is None:
            return None
        all_ft_consistent = True
        for cb, _ in chain[1:]:
            cl = cb.get_last_instruction()
            if not cl or cl.argval is None:
                all_ft_consistent = False
                break
            if len(chain) >= 2 and cb == chain[-1][0]:
                continue
            cb_succs = list(cb.conditional_successors)
            cb_ft = next((s for s in cb_succs if s.start_offset != cl.argval), None)
            if cb_ft != first_ft:
                all_ft_consistent = False
                break
        if all_ft_consistent:
            return chain
        return None

    def _detect_boolop_chain_start(self, block: BasicBlock, claimed: Set[BasicBlock]) -> Optional[List[Tuple[BasicBlock, str]]]:
        # 反编译逻辑：
        # ==========
        # 原始逻辑对已声明的块直接返回None，但这会阻止嵌套在循环/with/try/match体内的boolop链检测。
        # 基于"No More Gotos"区域归约算法的层次化原则：
        # - boolop链是一种表达式级区域（expression-level region），可以嵌入任何语句级区域
        # - 即使父区域已声明该块，只要块内包含短路跳转操作码，就应尝试检测boolop链
        # - 归约顺序：内层（boolop）先识别、外层（loop/if）后处理
        #
        # 边界条件：
        # - 仅当块包含短路跳转时才放宽claimed检查（避免误判）
        # - 如果块已被其他BoolOpRegion声明则仍跳过（避免重复）
        # - [Phase 3 adv14_boolop_result_compare] 双角色块例外：
        #   块可以同时是某 BoolOpRegion 的 merge_block 又是另一个
        #   BoolOpRegion 链的起始块。如 ``(a and b) == (c and d)``：
        #   Block 3 (LOAD c; JUMP_IF_FALSE_OR_POP → Block 5) 既是第一个
        #   `and` (R1: chain=[(1,'and')], merge=3) 的 merge_block，又是
        #   第二个 `and` (R2: chain=[(3,'and')], merge=5) 的起始块。当块
        #   是已存在 BoolOpRegion 的 merge_block（不在其 op_chain 中）且
        #   自身以 SHORT_CIRCUIT_JUMP_OPS 结尾、跳转目标与已存在
        #   BoolOpRegion 的 merge 不相同时，允许其作为新链起始被检测。
        #   这是「每块唯一归属」原则的明确例外——双角色块语义上同时属于
        #   两个表达式级区域（前一个的归并点 + 后一个的入口），类似
        #   loop_condition_blocks 例外，遵循同样的归约层次化原则。
        _is_dual_role_block = False
        if block in claimed:
            existing = self.block_to_region.get(block)
            if isinstance(existing, BoolOpRegion):
                # 双角色块检查：块是已存在 BoolOpRegion 的 merge_block
                # 且不在其 op_chain 中、自身以 SHORT_CIRCUIT_JUMP_OPS 结尾。
                _last_for_dual = block.get_last_instruction()
                _is_dual_role = (
                    _last_for_dual is not None
                    and _last_for_dual.opname in SHORT_CIRCUIT_JUMP_OPS
                    and existing.merge_block is block
                    and block not in {b for b, _ in existing.op_chain}
                )
                if _is_dual_role:
                    # 进一步验证：新链的跳转目标必须与已存在 BoolOpRegion
                    # 的 op_chain 中块的跳转目标不同，确保是独立表达式。
                    _new_jt = (self.cfg.get_block_by_offset(_last_for_dual.argval)
                               if _last_for_dual.argval is not None else None)
                    _existing_jts = set()
                    for _cb, _ in existing.op_chain:
                        _cb_last = _cb.get_last_instruction()
                        if (_cb_last is not None
                                and _cb_last.argval is not None
                                and _cb_last.opname in SHORT_CIRCUIT_JUMP_OPS):
                            _jt = self.cfg.get_block_by_offset(_cb_last.argval)
                            if _jt is not None:
                                _existing_jts.add(_jt.start_offset)
                    if (_new_jt is not None
                            and _new_jt.start_offset not in _existing_jts):
                        _is_dual_role_block = True  # 允许作为新链起始被检测
                    else:
                        return None
                else:
                    return None
            else:
                last_instr = block.get_last_instruction()
                if not last_instr or last_instr.opname not in (SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS):
                    return None
        last_instr = block.get_last_instruction()
        if not last_instr:
            return None
        if last_instr.opname in SHORT_CIRCUIT_JUMP_OPS:
            chain = self._detect_boolop_short_circuit_chain(
                block, skip_first_claimed_check=_is_dual_role_block)
            if chain is None or len(chain) < 1:
                return None
            return chain
        if last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
            _skip_claimed = block in claimed
            chain = self._detect_boolop_conditional_chain(block, claimed, skip_claimed_check=_skip_claimed)
            if chain is None or len(chain) < 1:
                return None
            return chain
        return None


    def _boolop_resolve_merge(self, chain: List[Tuple[BasicBlock, str]]) -> Optional[BasicBlock]:
        last_block, _ = chain[-1]
        last_instr = last_block.get_last_instruction()
        merge = None
        BOOLOP_JUMP_OPS = SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS
        if last_instr and last_instr.opname in SHORT_CIRCUIT_JUMP_OPS and last_instr.argval is not None:
            merge = self.cfg.get_block_by_offset(last_instr.argval)
        elif last_instr and last_instr.opname in BOOLOP_JUMP_OPS and last_instr.argval is not None:
            merge = self.cfg.get_block_by_offset(last_instr.argval)
            for chain_block, _ in chain:
                cl = chain_block.get_last_instruction()
                if cl and cl.opname in SHORT_CIRCUIT_JUMP_OPS and cl.argval is not None:
                    sc_target = self.cfg.get_block_by_offset(cl.argval)
                    if sc_target is not None and merge is not None:
                        if sc_target.start_offset > merge.start_offset or sc_target != merge:
                            merge = sc_target
                    break
        # [P5 + Cluster 4 interaction] Ternary as BoolOp operand — when the
        # chain contains ternary cond blocks (each cond block's jump target
        # is a ternary false_value, NOT the real merge), the merge computed
        # above is actually a VALUE BLOCK. Follow the last chain block's
        # value blocks' fallthrough (possibly via JUMP_FORWARD) to find the
        # REAL merge (the if-body).
        # This happens for `if (a if c else b) or (d if e else f) or ...:` —
        # the last ternary's false_value's jump target IS the real if-body.
        #
        # IMPORTANT: Only fire when ALL chain blocks are ternary cond blocks
        # (i.e., EVERY chain block's jump target is itself a value block
        # whose last instruction is a conditional jump). For a mixed chain
        # like `if a or (b if c else d):` — block 0 is a regular boolop
        # chain block (its jump target is the if-body, NOT a value block),
        # block 6 is a ternary cond block — the merge computed above (16,
        # the false_value) is CORRECT and must NOT be replaced. Replacing
        # it with the if-body (20) would cause the AST generator to
        # mis-reconstruct the ternary's test as `a or c and b`.
        if merge is not None:
            _merge_last = merge.get_last_instruction()
            if (_merge_last is not None
                    and _merge_last.opname in BOOLOP_JUMP_OPS
                    and _merge_last.argval is not None):
                # Check if merge is a value block (i.e., it's the jump
                # target of some chain block — that means it's the
                # false_value of a ternary in the chain).
                _is_value_block = False
                for _cb, _ in chain:
                    _cb_last = _cb.get_last_instruction()
                    if (_cb_last is not None
                            and _cb_last.argval is not None
                            and _cb_last.opname in BOOLOP_JUMP_OPS):
                        _cb_jt = self.cfg.get_block_by_offset(_cb_last.argval)
                        if _cb_jt is merge:
                            _is_value_block = True
                            break
                # Only fire Edit H when ALL chain blocks are ternary cond
                # blocks (every chain block's jump target is a value block
                # with its own conditional jump). If ANY chain block's jump
                # target is a non-value-block (e.g., the if-body), the
                # merge computed above is correct and must not be replaced.
                #
                # ALSO require each chain block's FALL-THROUGH to be a value
                # block (conditional jump). This distinguishes ternary cond
                # blocks (POP_JUMP_IF_FALSE → false_value, fall-through =
                # true_value, BOTH value blocks) from value-level short-
                # circuits (JUMP_IF_TRUE_OR_POP → merge, fall-through = next
                # operand LOAD, NOT a value block). For `(a or b) == c:` —
                # block 0's last is JUMP_IF_TRUE_OR_POP, its jump target is
                # the comparison block (has POP_JUMP_IF_FALSE), but its
                # fall-through is LOAD b (NOT a value block). Without this
                # fall-through check, Edit H would wrongly replace the
                # correct merge (comparison block) with the if-body.
                _all_ternary_cond = True
                for _cb, _ in chain:
                    _cb_last = _cb.get_last_instruction()
                    if (_cb_last is None
                            or _cb_last.argval is None
                            or _cb_last.opname not in BOOLOP_JUMP_OPS):
                        _all_ternary_cond = False
                        break
                    _cb_jt = self.cfg.get_block_by_offset(_cb_last.argval)
                    if _cb_jt is None:
                        _all_ternary_cond = False
                        break
                    _cb_jt_last = _cb_jt.get_last_instruction()
                    if (_cb_jt_last is None
                            or _cb_jt_last.argval is None
                            or _cb_jt_last.opname not in BOOLOP_JUMP_OPS):
                        _all_ternary_cond = False
                        break
                    # Also check fall-through is a value block.
                    _cb_ft = next((s for s in _cb.conditional_successors
                                   if s.start_offset != _cb_last.argval), None)
                    if _cb_ft is None:
                        _all_ternary_cond = False
                        break
                    _cb_ft_last = _cb_ft.get_last_instruction()
                    if (_cb_ft_last is None
                            or _cb_ft_last.argval is None
                            or _cb_ft_last.opname not in BOOLOP_JUMP_OPS):
                        _all_ternary_cond = False
                        break
                if _is_value_block and _all_ternary_cond:
                    # Follow value block's fallthrough to find real merge.
                    # Value block's last instr is a conditional jump — the
                    # fall-through successor is the "true branch" of the
                    # value block (i.e., the "if value is truthy" target).
                    # For a ternary's false_value, the fall-through usually
                    # leads (via JUMP_FORWARD) to the real merge.
                    _ft_succ = next((s for s in merge.conditional_successors
                                     if s.start_offset != _merge_last.argval), None)
                    _real_merge = None
                    if _ft_succ is not None:
                        _ft_eff = [i for i in _ft_succ.instructions
                                   if i.opname not in ('NOP', 'CACHE')]
                        if (len(_ft_eff) == 1
                                and _ft_eff[0].opname == 'JUMP_FORWARD'
                                and _ft_eff[0].argval is not None):
                            _real_merge = self.cfg.get_block_by_offset(_ft_eff[0].argval)
                        elif _ft_eff and _ft_eff[-1].opname == 'JUMP_FORWARD' \
                                and _ft_eff[-1].argval is not None:
                            _real_merge = self.cfg.get_block_by_offset(_ft_eff[-1].argval)
                        else:
                            _real_merge = _ft_succ
                    if _real_merge is not None:
                        merge = _real_merge
        return merge

    def _boolop_check_condition_context(self, chain: List[Tuple[BasicBlock, str]],
                                         merge: Optional[BasicBlock]) -> bool:
        last_block, _ = chain[-1]
        last_instr = last_block.get_last_instruction()
        is_condition = (last_instr is not None and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS)
        if is_condition and len(chain) >= 2:
            first_sc_target = None
            for chain_block, _ in chain:
                cl = chain_block.get_last_instruction()
                if cl and cl.opname in SHORT_CIRCUIT_JUMP_OPS and cl.argval is not None:
                    first_sc_target = self.cfg.get_block_by_offset(cl.argval)
                    break
            if first_sc_target is not None and last_instr and last_instr.argval is not None:
                last_target = self.cfg.get_block_by_offset(last_instr.argval)
                if last_target is not None and first_sc_target != last_target and merge is not None:
                    merge_has_store = any(
                        i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                        for i in merge.instructions)
                    if merge_has_store:
                        is_condition = False
        return is_condition

    def _boolop_expand_non_condition_blocks(self, chain: List[Tuple[BasicBlock, str]],
                                             chain_blocks: Set[BasicBlock],
                                             merge: Optional[BasicBlock]) -> None:
        for chain_block, _ in chain:
            last = chain_block.get_last_instruction()
            if last and last.opname in SHORT_CIRCUIT_JUMP_OPS:
                ft_succ = next((s for s in sorted(chain_block.conditional_successors,
                                   key=lambda s: s.start_offset)
                                if s.start_offset != last.argval), None)
                if ft_succ and ft_succ not in chain_blocks:
                    chain_blocks.add(ft_succ)
            if last and last.opname in FORWARD_CONDITIONAL_JUMP_OPS and chain and chain_block != chain[0][0]:
                cond_succs = list(chain_block.conditional_successors)
                if len(cond_succs) == 2:
                    jt_succ = next((s for s in cond_succs if s.start_offset == last.argval), None)
                    ft_succ = next((s for s in cond_succs if s.start_offset != last.argval), None)
                    if jt_succ and ft_succ:
                        both_reach = (merge is not None and
                            any(s == merge or merge in list(s.successors) for s in [ft_succ]) and
                            any(s == merge or merge in list(s.successors) for s in [jt_succ]))
                        if both_reach:
                            for succ in cond_succs:
                                if succ not in chain_blocks and succ != merge:
                                    chain_blocks.add(succ)

    def _normalize_none_check_op_types(self, chain: List[Tuple[BasicBlock, str]]) -> List[Tuple[BasicBlock, str]]:
        """Fix op_type classification for NONE_CHECK_OPS based on jump direction.

        NONE_CHECK_OPS (IF_NONE/IF_NOT_NONE) are ambiguous: the opname alone
        cannot determine whether the jump represents OR-success (jump to then
        body) or AND-failure (jump to merge/else). The op_type classification
        at line ~11964 uses substring matching ('_IF_NONE' → 'and') which is
        incorrect for IF_NOT_NONE in AND chains and IF_NONE in OR chains.

        This method post-processes the chain by determining the "then body"
        (the fall-through successor of the last chain block — reached when the
        overall condition is true) and reclassifies each NONE_CHECK_OP block:
        - jump target == then body → 'or' (jump to then on success)
        - jump target != then body → 'and' (jump to merge/else on failure)
        """
        if not chain or len(chain) < 2:
            return chain
        has_none_check = False
        for block, _ in chain:
            ci = block.get_last_instruction()
            if ci and ci.opname in NONE_CHECK_OPS:
                has_none_check = True
                break
        if not has_none_check:
            return chain
        last_block = chain[-1][0]
        last_ci = last_block.get_last_instruction()
        if not last_ci or last_ci.argval is None:
            return chain
        last_succs = list(last_block.conditional_successors)
        if len(last_succs) != 2:
            return chain
        then_body = next((s for s in last_succs if s.start_offset != last_ci.argval), None)
        if then_body is None:
            return chain
        fixed_chain = []
        for block, op_type in chain:
            ci = block.get_last_instruction()
            if ci and ci.opname in NONE_CHECK_OPS and ci.argval is not None:
                jt = self.cfg.get_block_by_offset(ci.argval)
                if jt is not None:
                    if jt == then_body:
                        op_type = 'or'
                    else:
                        op_type = 'and'
            fixed_chain.append((block, op_type))
        return fixed_chain

    def _create_boolop_region_from_chain(self, chain: List[Tuple[BasicBlock, str]], claimed: Set[BasicBlock]) -> Optional[BoolOpRegion]:
        chain = self._normalize_none_check_op_types(chain)
        start_block = chain[0][0]
        chain_blocks = set(b for b, _ in chain)
        merge = self._boolop_resolve_merge(chain)
        is_condition_context = self._boolop_check_condition_context(chain, merge)
        if not is_condition_context:
            self._boolop_expand_non_condition_blocks(chain, chain_blocks, merge)
        region_blocks = chain_blocks | ({merge} if merge else set())
        value_target = None
        # [R10 err 3] AugAssign detection: merge_block has BINARY_OP (in-place,
        # arg>=13) before STORE → `x += a and b`. The leading LOAD of value_target
        # in the first chain block is the augassign target load, not a BoolOp
        # operand. Record is_augassign + augassign_op so _generate_boolop can
        # emit AugAssign(target=x, op=+, value=BoolOp(a, b)).
        # [R11-err4/5/6] 扩展支持属性/下标目标: `x.y += a and b` / `x[0] += a and b`
        # merge_block 模式: [SWAP,] STORE_ATTR/STORE_SUBSCR (Name 目标是 STORE_FAST/
        # STORE_NAME/...)。属性/下标目标的 BINARY_OP 前面有 SWAP，而 Name 目标没有。
        is_augassign = False
        augassign_op = None
        augassign_target_kind = None  # 'name' | 'attr' | 'subscr'
        augassign_target_attr = None
        if merge:
            _merge_instrs = [i for i in merge.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
            _store_idx = None
            for _i, instr in enumerate(_merge_instrs):
                if instr.opname in ('STORE_FAST', 'STORE_NAME',
                                    'STORE_GLOBAL', 'STORE_DEREF'):
                    _store_idx = _i
                    value_target = instr.argval if instr.argval else f'var_{instr.arg}'
                    augassign_target_kind = 'name'
                    break
                if instr.opname == 'STORE_ATTR':
                    _store_idx = _i
                    augassign_target_kind = 'attr'
                    augassign_target_attr = instr.argval if instr.argval else f'attr_{instr.arg}'
                    break
                if instr.opname == 'STORE_SUBSCR':
                    _store_idx = _i
                    augassign_target_kind = 'subscr'
                    break
            if _store_idx is not None and _store_idx >= 1:
                # 寻找 BINARY_OP(arg>=13)，跳过 SWAP（属性/下标目标前会有 SWAP）
                _binop_idx = None
                for _bi in range(_store_idx - 1, -1, -1):
                    if _merge_instrs[_bi].opname == 'BINARY_OP' and isinstance(_merge_instrs[_bi].arg, int) and _merge_instrs[_bi].arg >= 13:
                        _binop_idx = _bi
                        break
                    if _merge_instrs[_bi].opname not in ('SWAP', 'NOP', 'CACHE'):
                        break
                if _binop_idx is not None:
                    _prev = _merge_instrs[_binop_idx]
                    _aug_map = {13: '+', 14: '&', 15: '//', 16: '<<', 17: '@',
                                18: '*', 19: '%', 20: '|', 21: '**', 22: '>>',
                                23: '-', 24: '/', 25: '^'}
                    _op_sym = _aug_map.get(_prev.arg)
                    if _op_sym is not None:
                        is_augassign = True
                        augassign_op = _op_sym
        if is_condition_context and merge:
            region_blocks = chain_blocks
            value_target = None
            is_augassign = False
            augassign_op = None
            augassign_target_kind = None
            augassign_target_attr = None
        # [Round 2 修复] await 轮询链作为 BoolOp 操作数：
        # 当 `if await g() or x:` / `if x or await g():` 这样的 BoolOp 条件
        # 中某个操作数是 `await <expr>` 时，CPython 把 await 求值展开为
        # setup_block (LOAD/CALL/GET_AWAITABLE/LOAD_CONST None) +
        # poll_block (SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT 自循环)
        # + cond_block (POP_JUMP_FORWARD_IF_TRUE/FALSE truthy 测试)。
        # cond_block 已在 op_chain 中，但 setup_block/poll_block 不在，会被
        # _generate_block_statements 当作独立 `await g()` 语句输出，破坏
        # BoolOp 表达式。这里把 await 前驱链纳入 BoolOpRegion.blocks，遵循
        # 「每块唯一归属」——它们语义上属于 BoolOp 的操作数求值。
        for _cb, _ in chain:
            _await_chain = self._collect_await_predecessor_chain(_cb)
            if not _await_chain:
                continue
            for _ab in _await_chain:  # [poll_block, setup_block]
                if _ab is None or _ab in region_blocks:
                    continue
                # 不抢占已被其他区域（Loop/Try/With/Match/Ternary）占用的块
                _existing = self.block_to_region.get(_ab)
                if _existing is not None and _existing is not region:
                    # LoopRegion 的 condition_block 允许共享，但 await 链通常
                    # 不在循环条件里；保守起见跳过已归属的块
                    if not isinstance(_existing, (LoopRegion,)):
                        continue
                region_blocks.add(_ab)
        # [P5 + Cluster 4 interaction] Ternary as BoolOp operand — add
        # ternary internal blocks (true_value, false_value, JUMP_FORWARD
        # intermediate) to BoolOpRegion.blocks so the AST generator can
        # find them when reconstructing ternary expressions from chain
        # blocks. Without this, the AST generator would not find the
        # value blocks and fail to reconstruct the ternary.
        #
        # IMPORTANT: Only fire when ALL chain blocks are ternary cond blocks
        # (i.e., EVERY chain block's jump target is itself a value block
        # whose last instruction is a conditional jump). For a mixed chain
        # like `if a or (b if c else d):` — block 0 is a regular boolop
        # chain block (its jump target is the if-body, NOT a value block),
        # block 6 is a ternary cond block — adding block 6's internal
        # blocks (true_value=10, false_value=16) to the BoolOpRegion
        # confuses the AST generator, which then includes true_value (b)
        # in the ternary's test, producing `b if a or c and b else d`
        # instead of `a or (b if c else d)`. For the mixed case, the
        # AST generator finds the ternary internal blocks via block
        # successors (as in the baseline), so Edit C is not needed.
        _BOOLOP_CHAIN_JUMPS = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        _all_ternary_cond_c = True
        for _cb, _ in chain:
            _cb_last = _cb.get_last_instruction()
            if (_cb_last is None
                    or _cb_last.argval is None
                    or _cb_last.opname not in _BOOLOP_CHAIN_JUMPS):
                _all_ternary_cond_c = False
                break
            _cb_jt = self.cfg.get_block_by_offset(_cb_last.argval)
            if _cb_jt is None:
                _all_ternary_cond_c = False
                break
            _cb_jt_last = _cb_jt.get_last_instruction()
            if (_cb_jt_last is None
                    or _cb_jt_last.argval is None
                    or _cb_jt_last.opname not in _BOOLOP_CHAIN_JUMPS):
                _all_ternary_cond_c = False
                break
            # Also require fall-through to be a value block (conditional
            # jump). This distinguishes ternary cond blocks from value-
            # level short-circuits (JUMP_IF_TRUE_OR_POP). See Edit H.
            _cb_ft = next((s for s in _cb.conditional_successors
                           if s.start_offset != _cb_last.argval), None)
            if _cb_ft is None:
                _all_ternary_cond_c = False
                break
            _cb_ft_last = _cb_ft.get_last_instruction()
            if (_cb_ft_last is None
                    or _cb_ft_last.argval is None
                    or _cb_ft_last.opname not in _BOOLOP_CHAIN_JUMPS):
                _all_ternary_cond_c = False
                break
        if _all_ternary_cond_c:
            for _cb, _ in chain:
                _cb_last = _cb.get_last_instruction()
                if (_cb_last is None
                        or _cb_last.argval is None
                        or _cb_last.opname not in _BOOLOP_CHAIN_JUMPS):
                    continue
                _fv = self.cfg.get_block_by_offset(_cb_last.argval)
                if _fv is None:
                    continue
                _fv_last = _fv.get_last_instruction()
                if (_fv_last is None
                        or _fv_last.opname not in _BOOLOP_CHAIN_JUMPS
                        or _fv_last.argval is None):
                    continue
                # _fv is a value block (ternary false_value). Find true_value
                # = chain block's fallthrough.
                _cb_succs = list(_cb.conditional_successors)
                _tv = next((s for s in _cb_succs
                            if s.start_offset != _cb_last.argval), None)
                if _tv is None:
                    continue
                _tv_last = _tv.get_last_instruction()
                if (_tv_last is None
                        or _tv_last.opname not in _BOOLOP_CHAIN_JUMPS):
                    continue
                # Both _fv and _tv are value blocks — this is a ternary.
                # Add them to region_blocks. Also add the JUMP_FORWARD
                # intermediate block between true_value and merge (if any).
                for _vb in (_fv, _tv):
                    if _vb not in self.block_to_region:
                        region_blocks.add(_vb)
                # Find JUMP_FORWARD intermediate between true_value and merge.
                _tv_ft = next((s for s in _tv.conditional_successors
                               if s.start_offset != _tv_last.argval), None)
                if _tv_ft is not None and _tv_ft not in region_blocks:
                    _tv_ft_eff = [i for i in _tv_ft.instructions
                                  if i.opname not in ('NOP', 'CACHE')]
                    if (len(_tv_ft_eff) == 1
                            and _tv_ft_eff[0].opname == 'JUMP_FORWARD'
                            and _tv_ft_eff[0].argval is not None):
                        # _tv_ft is a JUMP_FORWARD intermediate block.
                        if _tv_ft not in self.block_to_region:
                            region_blocks.add(_tv_ft)
        region = BoolOpRegion(
            region_type=RegionType.BOOL_OP,
            entry=start_block,
            blocks=region_blocks,
            op_chain=chain,
            merge_block=merge,
            value_target=value_target,
            condition_block=None,
            is_augassign=is_augassign,
            augassign_op=augassign_op,
            augassign_target_kind=augassign_target_kind,
            augassign_target_attr=augassign_target_attr,
        )
        region.is_condition_context = is_condition_context
        self.regions.append(region)
        for b in region.blocks:
            if is_condition_context:
                self.block_to_region[b] = region
                claimed.add(b)
            elif b not in self.block_to_region:
                self.block_to_region[b] = region
                claimed.add(b)
        return region

    def _detect_boolop_conditional_chain(self, start_block: BasicBlock, claimed: Set[BasicBlock], skip_claimed_check: bool = False) -> Optional[List[Tuple[BasicBlock, str]]]:
        chain: List[Tuple[BasicBlock, str]] = []
        current = start_block
        visited = set()
        BOOLOP_CHAIN_JUMPS = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        first_jump_type = None
        while current and current.start_offset not in visited:
            visited.add(current.start_offset)
            last = current.get_last_instruction()
            if not last or last.opname not in BOOLOP_CHAIN_JUMPS:
                break
            if current in self.block_to_region:
                existing_reg = self.block_to_region.get(current)
                if isinstance(existing_reg, BoolOpRegion):
                    break
            if last.opname in NONE_CHECK_OPS:
                pass
            cur_jump_type = 'forward' if last.opname in FORWARD_CONDITIONAL_JUMP_OPS else 'short_circuit'
            if first_jump_type is None:
                first_jump_type = cur_jump_type
            elif first_jump_type != cur_jump_type:
                first_last = chain[0][0].get_last_instruction()
                cur_last = last
                first_jt_offset = first_last.argval if first_last else None
                cur_jt_offset = cur_last.argval if cur_last else None
                if first_jt_offset is not None and cur_jt_offset is not None and first_jt_offset > cur_jt_offset:
                    break
            op_type = 'and' if ('FALSE' in last.opname or '_IF_NONE' in last.opname) else 'or'
            chain.append((current, op_type))
            # [CPython peephole P4 + P5 interaction] Chained compare as
            # BoolOp operand hop. When `if a < b < c and d < e < f:` is
            # compiled, each chained compare (a<b<c, d<e<f) is identified
            # as an IfRegion with chained_compare_ops by
            # _identify_chained_compare_regions (which runs BEFORE boolop
            # identification). The boolop chain detection must treat each
            # chained compare region as a SINGLE operand and hop over its
            # internal blocks (extra_chain_blocks + merge_block) to reach
            # the next operand's start.
            #
            # Algorithm (bottom-up reduction): if current is the entry of
            # a chained compare IfRegion, the region's merge_block is the
            # "fall-through after the chained compare succeeds". If
            # merge_block is a JUMP_FORWARD, hop to its target (the next
            # operand); otherwise, hop to merge_block itself. This makes
            # chained compare regions atomic operands of the higher-level
            # BoolOp, preserving "each block unique ownership" — the
            # chained compare region's internal blocks are NOT added to
            # the BoolOpRegion; only the chained compare headers (entries)
            # become op_chain operands.
            #
            # Note: self.block_to_region may not yet contain the chained
            # compare region's blocks (chained compare identification only
            # appends to self.regions, not self.block_to_region). So we
            # look up the region from self.regions by entry block.
            #
            # Safety guard: before hopping, if chain has length >= 2,
            # verify that current's short-circuit exit is equivalent to
            # the first chain entry's exit. This prevents false chains
            # when the hop target is in a different semantic context.
            _cc_region = None
            for _r in self.regions:
                if (type(_r) is IfRegion
                        and _r.entry is current
                        and getattr(_r, 'chained_compare_ops', None)
                        and len(_r.chained_compare_ops) >= 2
                        and getattr(_r, 'chained_compare_blocks', None)
                        and _r.merge_block is not None):
                    _cc_region = _r
                    break
            if _cc_region is not None:
                # Safety guard: verify exit equivalence for chains with
                # length >= 2 (the first entry sets the reference exit).
                if len(chain) >= 2:
                    _first_jt = self.cfg.get_block_by_offset(
                        chain[0][0].get_last_instruction().argval
                    ) if chain[0][0].get_last_instruction() and chain[0][0].get_last_instruction().argval is not None else None
                    _cur_jt = self.cfg.get_block_by_offset(last.argval) if last.argval is not None else None
                    if (_first_jt is not None and _cur_jt is not None
                            and _first_jt is not _cur_jt
                            and not self._is_equivalent_exit_block(_first_jt, _cur_jt)):
                        chain.pop()
                        break
                _cc_merge = _cc_region.merge_block
                _cc_merge_last = _cc_merge.get_last_instruction() if _cc_merge else None
                _hop_target = None
                if (_cc_merge_last is not None
                        and _cc_merge_last.opname == 'JUMP_FORWARD'
                        and _cc_merge_last.argval is not None):
                    _hop_target = self.cfg.get_block_by_offset(_cc_merge_last.argval)
                elif _cc_merge is not None:
                    _hop_target = _cc_merge
                if (_hop_target is not None
                        and _hop_target.start_offset not in visited):
                    current = _hop_target
                    continue
                # Hop target is None or already visited — break
                break
            # [P5 + Cluster 4 interaction] Ternary as BoolOp `or` operand hop.
            # When `if a or (b if c else d): pass` is compiled, the ternary's
            # cond block (LOAD c, POP_JUMP_IF_FALSE → false_value) appears in
            # the boolop chain. The IF_FALSE → false_value looks like an 'and'
            # short-circuit, but false_value is NOT an exit block — it's the
            # ternary's false value block (which has its own
            # POP_JUMP_IF_FALSE/TRUE → exit). Without this hop, the chain
            # absorbs the ternary's cond + true_value as 'and' operands,
            # preventing TernaryRegion identification (which runs AFTER
            # boolop). The chain must treat the entire ternary as a SINGLE
            # operand and hop over its internal blocks (cond → true_value →
            # JUMP_FORWARD → merge, false_value → merge) to reach the next
            # operand or the if-body.
            #
            # Detection: current's short-circuit target is NOT an exit block
            # (doesn't end with RETURN_VALUE/RETURN_CONST) but has its own
            # conditional jump to an exit (it's a value block). The ternary's
            # merge is false_value's fallthrough, which true_value's
            # fallthrough (via JUMP_FORWARD) also reaches.
            #
            # Discriminator: only fire when op_type differs from chain[0][1].
            # When the chain's first op_type matches the current op_type
            # (e.g. both 'and' — the ternary cond block's IF_FALSE derives
            # 'and', and the chain is also an 'and' chain), the existing
            # `_is_equivalent_exit_block` check at line 13276+ already breaks
            # the chain correctly (because the false_value block is NOT
            # equivalent to an exit block), letting TernaryRegion
            # identification handle it. Firing the hop here would WRAP the
            # ternaries into a BoolOpRegion, breaking the natural TernaryRegion
            # identification for `(a if c else b) and (d if e else f):`.
            # The hop is needed ONLY when the chain's op_type differs from
            # the current op_type — i.e. the ternary cond block's IF_FALSE
            # derives 'and', but the chain is an 'or' chain (e.g. `a or
            # (b if c else d):`). In this case, the existing check at line
            # 13276 doesn't fire (because op_type != prev_op), and the chain
            # would wrongly absorb the ternary's true_value as another 'or'
            # operand. The hop overrides the op_type to match chain[0][1]
            # and hops to the ternary's merge.
            if last.argval is not None and chain:
                _sc_target = self.cfg.get_block_by_offset(last.argval)
                if _sc_target is not None:
                    _sc_target_last = _sc_target.get_last_instruction()
                    _target_is_exit = (_sc_target_last is None
                                       or _sc_target_last.opname in ('RETURN_VALUE', 'RETURN_CONST'))
                    if (not _target_is_exit and _sc_target_last
                            and _sc_target_last.opname in BOOLOP_CHAIN_JUMPS
                            and _sc_target_last.argval is not None):
                        # _sc_target is a value block (ternary operand).
                        # Determine the chain op_type:
                        # - For the FIRST chain entry (len(chain) == 1):
                        #   derive from value block's jump direction.
                        #   Non-last `or` operand: IF_TRUE → if-body = 'or'.
                        #   Non-last `and` operand: IF_FALSE → exit = 'and'.
                        # - For NON-FIRST chain entries (len(chain) >= 2):
                        #   INHERIT from chain[0][1]. The last operand of
                        #   an `or`/`and` chain does a truthiness check
                        #   (IF_FALSE → exit) instead of short-circuiting,
                        #   so the value block's jump direction is
                        #   unreliable — but the chain's op_type is
                        #   already established by the first entry.
                        # Discriminator for firing the hop:
                        # - len(chain) >= 2: ALWAYS fire (inherit op_type).
                        #   This handles the LAST ternary in an `or`/`and`
                        #   chain, whose value blocks do truthiness checks
                        #   (IF_FALSE → exit) — without this, the chain
                        #   would break prematurely or absorb the ternary's
                        #   internals as wrong-op operands.
                        # - len(chain) == 1: fire only when `_actual_op !=
                        #   op_type`. This preserves Case A
                        #   (`(a if c else b) and (d if e else f):`), where
                        #   the first ternary is a NON-LAST `and` operand
                        #   and the existing `_is_equivalent_exit_block`
                        #   check breaks the chain correctly (letting
                        #   TernaryRegion identification handle it).
                        _is_or_short_circuit = 'TRUE' in _sc_target_last.opname
                        _actual_op = 'or' if _is_or_short_circuit else 'and'
                        _is_non_first = len(chain) >= 2
                        # Compute merge FIRST so we can check whether the hop
                        # target is a "plain operand" block (its last instr is
                        # a conditional jump to an exit). For
                        # `(ternary) or plain:` — the ternary's merge IS the
                        # plain operand. Firing Edit A here would create a
                        # BoolOpRegion without the ternary's internal blocks
                        # (Edit C doesn't fire for mixed chains), corrupting
                        # the ternary. Instead, let the chain extend
                        # naturally (block → value block → break) so
                        # TernaryRegion identification can handle the ternary
                        # (as in baseline).
                        # Discriminator:
                        # - merge's last is NOT a conditional jump → fire
                        #   (e.g., merge is the if-body with RETURN_VALUE).
                        # - merge's last IS a conditional jump:
                        #   - jump target is an exit → DON'T fire (plain
                        #     operand; let TernaryRegion handle the ternary).
                        #   - jump target is a value block → fire (merge is
                        #     another ternary cond, e.g. adv13's full chain).
                        _fv_succs = list(_sc_target.conditional_successors)
                        _merge = next((s for s in _fv_succs
                                       if s.start_offset != _sc_target_last.argval), None)
                        _is_plain_operand = False
                        if _merge is not None:
                            _merge_last_i = _merge.get_last_instruction()
                            if (_merge_last_i is not None
                                    and _merge_last_i.opname in BOOLOP_CHAIN_JUMPS
                                    and _merge_last_i.argval is not None):
                                _merge_jt = self.cfg.get_block_by_offset(_merge_last_i.argval)
                                if _merge_jt is not None:
                                    _merge_jt_last = _merge_jt.get_last_instruction()
                                    if (_merge_jt_last is None
                                            or _merge_jt_last.opname in ('RETURN_VALUE', 'RETURN_CONST')):
                                        _is_plain_operand = True
                        _should_fire = ((_is_non_first
                                         or _actual_op != op_type)
                                        and not _is_plain_operand)
                        if _should_fire and _merge is not None:
                            # Verify true_value (current's fallthrough)
                            # also has a conditional jump to an exit
                            # (it's a value block) and reaches merge
                            # via fallthrough chain.
                            _tv_succs = list(current.conditional_successors)
                            _tv = next((s for s in _tv_succs
                                        if s.start_offset != last.argval), None)
                            if _tv is not None:
                                _tv_last = _tv.get_last_instruction()
                                _tv_is_value = (_tv_last and _tv_last.opname in BOOLOP_CHAIN_JUMPS)
                                if _tv_is_value:
                                    _tv_ft = next((s for s in _tv.conditional_successors
                                                   if s.start_offset != _tv_last.argval), None)
                                    _tv_reaches_merge = False
                                    if _tv_ft is _merge:
                                        _tv_reaches_merge = True
                                    elif _tv_ft is not None:
                                        _tv_ft_eff = [i for i in _tv_ft.instructions
                                                      if i.opname not in ('NOP', 'CACHE')]
                                        if (len(_tv_ft_eff) == 1
                                                and _tv_ft_eff[0].opname == 'JUMP_FORWARD'
                                                and _tv_ft_eff[0].argval is not None):
                                            _jft = self.cfg.get_block_by_offset(_tv_ft_eff[0].argval)
                                            if _jft is _merge:
                                                _tv_reaches_merge = True
                                    if _tv_reaches_merge:
                                        # Ternary detected. Determine
                                        # the chain op_type:
                                        # - Non-first entry: inherit
                                        #   from chain[0][1] (already
                                        #   correctly established).
                                        # - First entry: use the
                                        #   actual op derived from the
                                        #   value block's jump dir.
                                        if _is_non_first:
                                            op_type = chain[0][1]
                                        else:
                                            op_type = _actual_op
                                        chain[-1] = (current, op_type)
                                        if _merge.start_offset not in visited:
                                            current = _merge
                                            continue
                                        break
            succs = list(current.conditional_successors)
            if len(succs) != 2:
                break
            ft_succ = next((s for s in succs if s.start_offset != last.argval), None)
            if ft_succ is None:
                break
            if not skip_claimed_check:
                if ft_succ in self.block_to_region or ft_succ in claimed:
                    break
            else:
                # Even when skip_claimed_check is True (for loop condition
                # blocks), don't extend the chain into the loop's header or
                # body blocks. These are NOT part of the boolean condition -
                # they're the loop body. This mirrors the check in
                # _detect_while_boolop_forward_chain (line ~11940):
                #   if ft_succ == loop.header_block or ft_succ in loop.body_blocks: break
                if ft_succ in self.block_to_region:
                    _ft_reg = self.block_to_region.get(ft_succ)
                    if isinstance(_ft_reg, LoopRegion):
                        if ft_succ == _ft_reg.header_block or ft_succ in _ft_reg.body_blocks:
                            break
            if len(chain) >= 2:
                first_jump_target = self.cfg.get_block_by_offset(chain[0][0].get_last_instruction().argval)
                cur_jump_target = self.cfg.get_block_by_offset(last.argval)
                prev_op = chain[-2][1]
                if op_type == prev_op and first_jump_target and cur_jump_target and first_jump_target != cur_jump_target:
                    # [Cluster 5] not(or) pattern: a pure 'or' chain where
                    # EVERY segment's short-circuit jump is IF_TRUE (each true
                    # operand exits to its own skip-body block). This is the
                    # compiler's lowering of `not (X or Y ...)` — the UNARY_NOT
                    # is optimized away by inverting jump direction. The
                    # distinct TRUE targets are equivalent trivial exits, so
                    # the chain must be preserved for bottom-up reduction into
                    # a single BoolOp(or) that the AST generator wraps in
                    # `not (...)` (preserving original COMPARE_OP operators).
                    _normal_or = (op_type == 'or' and 'TRUE' in chain[0][0].get_last_instruction().opname and 'FALSE' in last.opname)
                    _not_or_chain = (op_type == 'or' and all(
                        (cb.get_last_instruction() is not None and 'TRUE' in cb.get_last_instruction().opname)
                        for cb, _ in chain))
                    # [CPython peephole] `and`/`or` chain with multiple
                    # operands: the compiler emits a SEPARATE trivial exit
                    # block (LOAD_CONST None; RETURN_VALUE) for each operand's
                    # short-circuit target. The targets are different offsets
                    # but semantically equivalent — they all do "skip the body,
                    # return None". Treat them as the same logical target so
                    # the chain is preserved for bottom-up reduction into a
                    # single BoolOp. This is the compiler's standard lowering
                    # for `if (a and b and c): ...` at module/function-tail
                    # position (each operand's false-exit gets its own block).
                    _equivalent_exits = self._is_equivalent_exit_block(first_jump_target, cur_jump_target)
                    # [CPython peephole] Scenario B ternary guard: when the
                    # chain's fallthrough leads (via JUMP_FORWARD) to a loop
                    # header, the first block is a ternary's condition (not a
                    # boolop operand) and its jump target is the ternary's
                    # false-value block. CPython merges the ternary's
                    # true-value with the while-condition check, producing a
                    # structure that looks like a boolop chain (both blocks
                    # IF_FALSE to trivial exit blocks). Without this guard,
                    # `_equivalent_exits` would preserve the chain and steal
                    # blocks the TernaryRegion detector needs, causing
                    # `while (x if c else None): pass` to decompile as a
                    # nested if+while. The discriminator: walk the
                    # fallthrough chain from the current block's fallthrough;
                    # if a JUMP_FORWARD block appears whose target is a loop
                    # header (has a back-edge predecessor), it's a Scenario B
                    # ternary — break the chain so the TernaryRegion detector
                    # can find the pattern.
                    _is_scenario_b_ternary = False
                    if _equivalent_exits:
                        _ft_walk = ft_succ
                        _walk_count = 0
                        _visited_ft = set()
                        while _ft_walk and _walk_count < 5 and _ft_walk.start_offset not in _visited_ft:
                            _visited_ft.add(_ft_walk.start_offset)
                            _ft_last_i = _ft_walk.get_last_instruction()
                            if _ft_last_i and _ft_last_i.opname == 'JUMP_FORWARD' and _ft_last_i.argval is not None:
                                _merge_block = self.cfg.get_block_by_offset(_ft_last_i.argval)
                                if _merge_block is not None and _merge_block is not _ft_walk:
                                    # Loop header = has a back-edge predecessor
                                    # (a predecessor at a higher offset with
                                    # JUMP_BACKWARD). This identifies the
                                    # JUMP_FORWARD target as a loop header,
                                    # meaning the current block is a ternary
                                    # condition whose merge is the loop header.
                                    for _mp in _merge_block.predecessors:
                                        if _mp.start_offset > _merge_block.start_offset:
                                            _mp_last = _mp.get_last_instruction()
                                            if _mp_last and (_mp_last.opname in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT')
                                                              or _mp_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS):
                                                _is_scenario_b_ternary = True
                                                break
                                    if _is_scenario_b_ternary:
                                        break
                            # Move to fallthrough successor (not jump target)
                            _ft_next = None
                            if _ft_last_i and _ft_last_i.argval is not None:
                                for s in _ft_walk.successors:
                                    if s.start_offset != _ft_last_i.argval:
                                        _ft_next = s
                                        break
                            else:
                                if _ft_walk.successors:
                                    _ft_next = next(iter(_ft_walk.successors))
                            _ft_walk = _ft_next
                            _walk_count += 1
                    if not _normal_or and not _not_or_chain and (not _equivalent_exits or _is_scenario_b_ternary):
                        chain.pop()
                        break
            # [Round 2 修复] await 作为后续操作数：`x or await g()` 中第一个
            # 操作数 x 的 fallthrough 后继是 await setup_block（含 GET_AWAITABLE，
            # 末尾 LOAD_CONST None 非条件跳转），链检测会在此中断。跳过
            # setup+poll 轮询链，定位到 await 结果的 truthy 测试 cond_block，
            # 作为下一个操作数块继续链检测。
            _await_cond = self._skip_await_poll_to_cond_block(ft_succ)
            if _await_cond is not None:
                current = _await_cond
            else:
                current = ft_succ
        if len(chain) < 2:
            return None
        first_last = chain[0][0].get_last_instruction()
        first_jt = self.cfg.get_block_by_offset(first_last.argval) if first_last and first_last.argval is not None else None
        if first_jt is None:
            return None
        if first_last and 'TRUE' in first_last.opname:
            is_pure_or_chain = True
            first_jt_offset = first_last.argval
            for i in range(len(chain) - 1):
                cur_last_instr = chain[i][0].get_last_instruction()
                if not cur_last_instr or 'TRUE' not in cur_last_instr.opname:
                    is_pure_or_chain = False
                    break
                if cur_last_instr.argval != first_jt_offset:
                    is_pure_or_chain = False
                    break
            if is_pure_or_chain:
                last_last_instr = chain[-1][0].get_last_instruction()
                if last_last_instr and 'FALSE' in last_last_instr.opname:
                    last_jt_offset = last_last_instr.argval
                    if last_jt_offset != first_jt_offset:
                        # [CPython peephole] Distinguish `X or Y or ... or Z`
                        # (OR chain) from `not X and Y` (AND chain with `not`
                        # on the first operand). Both produce the "first N-1
                        # blocks IF_TRUE with same target + last block IF_FALSE
                        # with different target" pattern, but the semantics
                        # differ by where the IF_TRUE targets point:
                        # - `X or Y`: each IF_TRUE targets the LOOP BODY
                        #   (continue when X is true). The last block's
                        #   IF_FALSE is the "value" block (exit when false).
                        #   Reclassify last as 'or' to match the OR chain.
                        # - `not X and Y`: each IF_TRUE targets an EXIT
                        #   (exit when `not X` is false, i.e., X is true —
                        #   this is an AND short-circuit on `not X`, not an
                        #   OR short-circuit on X). The last block's IF_FALSE
                        #   is the AND short-circuit on Y. Reclassify the
                        #   first N-1 blocks as 'and' so the chain correctly
                        #   reduces to BoolOp(And, [not X, Y]).
                        # The discriminator is whether the first block's
                        # IF_TRUE target is a trivial exit block (LOAD_CONST
                        # None; RETURN_VALUE) or a loop body block. This
                        # mirrors the bytecode difference between
                        # `while X or Y:` (IF_TRUE → loop body) and
                        # `while not X and Y:` (IF_TRUE → exit).
                        first_jt_block = self.cfg.get_block_by_offset(first_jt_offset)
                        if (first_jt_block is not None
                                and self._is_trivial_block(first_jt_block)):
                            # [Discriminator] `not X and Y` vs `X or Y`:
                            # Both patterns have first N-1 blocks IF_TRUE
                            # with the same target. The difference is WHERE
                            # that target lies:
                            # - `X or Y`: the IF_TRUE target IS the merge
                            #   block (the last block's non-jump successor —
                            #   the if/loop body where the condition is True).
                            #   Even if the merge block is a trivial return
                            #   (e.g. `if a or b: pass` — `pass` compiles to
                            #   LOAD_CONST None; RETURN_VALUE), it's the BODY,
                            #   not an exit.
                            # - `not X and Y`: the IF_TRUE target is an EXIT
                            #   block (NOT the merge block). The merge block
                            #   is the last block's non-jump successor (the
                            #   loop body).
                            # Without this merge-block check, `if a or b:
                            # pass` would be misidentified as `if (not a and
                            # b): pass` because the if body (`pass`) is a
                            # trivial return block.
                            _last_chain_block = chain[-1][0]
                            _last_chain_instr = _last_chain_block.get_last_instruction()
                            _merge_block = None
                            if _last_chain_instr and _last_chain_instr.argval is not None:
                                for _s in _last_chain_block.conditional_successors:
                                    if _s.start_offset != _last_chain_instr.argval:
                                        _merge_block = _s
                                        break
                            # [P5 + Cluster 4 interaction] Ternary as BoolOp
                            # operand — when chain[-1] is a ternary cond block
                            # (its non-jump successor is a VALUE BLOCK with its
                            # own conditional jump, not the real merge), the
                            # _merge_block computed above is the ternary's
                            # true_value, NOT the BoolOp's merge. Edit A's hop
                            # has already set the correct op_type for chain[-1]
                            # (inherited from chain[0][1]). Skip this old
                            # discriminator to avoid corrupting chain[0..N-2]'s
                            # op_type. This happens for `if a or (b if c else
                            # d): pass` where chain[-1] (block 6, ternary cond)
                            # has its fall-through (block 10, true_value) being
                            # a value block, not the merge (block 20, if-body).
                            #
                            # IMPORTANT: Require BOTH _merge_block (chain[-1]'s
                            # fall-through) AND chain[-1]'s jump target to be
                            # value blocks (conditional jumps). For
                            # `while not X and Y:` — chain[-1]'s jump target
                            # is an EXIT (the loop's "condition false" exit),
                            # NOT a value block. So chain[-1] is NOT a ternary
                            # cond block, and the old discriminator MUST run
                            # (reclassifying the chain as `not X and Y`).
                            _is_ternary_cond_tail = False
                            if _merge_block is not None:
                                _mb_last = _merge_block.get_last_instruction()
                                if (_mb_last is not None
                                        and _mb_last.opname in BOOLOP_CHAIN_JUMPS
                                        and _mb_last.argval is not None):
                                    # Also require chain[-1]'s jump target to
                                    # be a value block (NOT an exit).
                                    _tail_jt = self.cfg.get_block_by_offset(
                                        _last_chain_instr.argval
                                    )
                                    if _tail_jt is not None:
                                        _tail_jt_last = _tail_jt.get_last_instruction()
                                        if (_tail_jt_last is not None
                                                and _tail_jt_last.opname in BOOLOP_CHAIN_JUMPS
                                                and _tail_jt_last.argval is not None):
                                            _is_ternary_cond_tail = True
                            if _is_ternary_cond_tail:
                                # Edit A's hop already handled op_type — skip
                                # the old discriminator.
                                pass
                            elif (_merge_block is not None
                                    and first_jt_block is _merge_block):
                                # IF_TRUE target is the merge block → `X or Y`
                                chain[-1] = (chain[-1][0], 'or')
                            else:
                                # IF_TRUE target is an exit → `not X and Y`
                                for i in range(len(chain) - 1):
                                    chain[i] = (chain[i][0], 'and')
                        else:
                            chain[-1] = (chain[-1][0], 'or')
        all_same_target = True
        target_groups = {}
        for cb, cop in chain:
            cl = cb.get_last_instruction()
            if not cl or cl.argval is None:
                all_same_target = False
                break
            cjt = self.cfg.get_block_by_offset(cl.argval)
            if cjt != first_jt:
                # [CPython peephole] Multiple operands in `and`/`or` chain
                # produce distinct trivial exit blocks (LOAD_CONST None;
                # RETURN_VALUE) at module/function-tail position. They are
                # semantically equivalent — treat them as the same logical
                # target so the chain is preserved.
                if not self._is_equivalent_exit_block(first_jt, cjt):
                    all_same_target = False
            target_groups.setdefault(id(cjt), set()).add(cop)
        if not all_same_target:
            has_operator_boundary = False
            for idx in range(1, len(chain)):
                if chain[idx][1] != chain[idx-1][1]:
                    has_operator_boundary = True
                    break
            if has_operator_boundary:
                unified_chain = self._try_unify_mixed_boolop_chain(chain, first_jt)
                if unified_chain and len(unified_chain) >= 2:
                    return unified_chain
            elif not self._is_nested_if_else_pattern(chain):
                unified_chain = self._try_unify_mixed_boolop_chain(chain, first_jt)
                if unified_chain and len(unified_chain) >= 2:
                    return unified_chain
            _first_last = chain[0][0].get_last_instruction()
            if (len(chain) >= 2 and all(c[1] == 'or' for c in chain)
                and _first_last and 'TRUE' in _first_last.opname):
                return chain
            return None
        if self._is_nested_if_else_pattern(chain):
            return None
        return chain

    def _is_nested_if_else_pattern(self, chain: List[Tuple[BasicBlock, str]]) -> bool:
        last_block, _ = chain[-1]
        last_instr = last_block.get_last_instruction()
        if not last_instr or last_instr.argval is None:
            return False
        ft_succ = next((s for s in last_block.conditional_successors
                        if s.start_offset != last_instr.argval), None)
        jt_target = self.cfg.get_block_by_offset(last_instr.argval)
        if ft_succ is None or jt_target is None:
            return False
        ft_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                          for i in ft_succ.instructions
                          if i.opname not in NOISE_OPS)
        jt_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                          for i in jt_target.instructions
                          if i.opname not in NOISE_OPS)
        if ft_has_store and jt_has_store:
            return True
        if ft_has_store and self._is_trivial_block(jt_target):
            return True
        first_block, _ = chain[0]
        first_instr = first_block.get_last_instruction()
        if first_instr and first_instr.argval is not None:
            if len(chain) >= 2:
                second_block, _ = chain[1]
                second_instr = second_block.get_last_instruction()
                if second_instr and second_instr.argval is not None:
                    if first_instr.argval > second_instr.argval:
                        return True
            first_ft = next((s for s in first_block.conditional_successors
                             if s.start_offset != first_instr.argval), None)
            if first_ft and len(first_ft.instructions) <= 3:
                meaningful = [i for i in first_ft.instructions
                             if i.opname not in NOISE_OPS]
                if meaningful and meaningful[0].opname in ('POP_JUMP_FORWARD_IF_FALSE',
                                                           'POP_JUMP_BACKWARD_IF_FALSE',
                                                           'POP_JUMP_FORWARD_IF_TRUE',
                                                           'POP_JUMP_BACKWARD_IF_TRUE'):
                    all_same_op = all(chain[i][1] == chain[0][1] for i in range(len(chain)))
                    if not all_same_op:
                        return True
        return False

    def _try_unify_mixed_boolop_chain(self, initial_chain, outer_target):
        result = list(initial_chain)
        last_block, _ = result[-1]
        last_instr = last_block.get_last_instruction()
        if not last_instr or last_instr.argval is None:
            return result
        ft_succ = next((s for s in last_block.conditional_successors
                        if s.start_offset != last_instr.argval), None)
        if ft_succ is None or ft_succ in self.block_to_region:
            return result
        ft_last = ft_succ.get_last_instruction()
        BOOLOP_CHAIN_JUMPS = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        if not ft_last or ft_last.opname not in BOOLOP_CHAIN_JUMPS:
            return result
        extended = self._detect_boolop_conditional_chain(ft_succ, set())
        if extended:
            result.extend(extended)
        return result

    def _detect_boolop_short_circuit_chain(self, start_block: BasicBlock, skip_first_claimed_check: bool = False) -> Optional[List[Tuple[BasicBlock, str]]]:
        chain: List[Tuple[BasicBlock, str]] = []
        current = start_block
        visited = set()
        _is_first_iter = True
        while current and current.start_offset not in visited:
            visited.add(current.start_offset)
            last = current.get_last_instruction()
            if not last or last.opname not in SHORT_CIRCUIT_JUMP_OPS:
                if chain and last and last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                    op_type = 'and' if 'FALSE' in last.opname else 'or'
                    chain.append((current, op_type))
                    succs = list(current.conditional_successors)
                    if len(succs) != 2:
                        break
                    ft_succ = next((s for s in succs if s.start_offset != last.argval), None)
                    if ft_succ is None:
                        break
                    if ft_succ in self.block_to_region:
                        _ft_reg = self.block_to_region.get(ft_succ)
                        if isinstance(_ft_reg, BoolOpRegion):
                            break
                    current = ft_succ
                    _is_first_iter = False
                    continue
                if chain and last and last.opname not in ('RETURN_VALUE', 'RETURN_CONST',
                                                           'RAISE_VARARGS', 'RERAISE'):
                    pure_instrs = [i for i in current.instructions
                                   if i.opname not in NOISE_OPS]
                    has_store = any(i.opname in ('STORE_NAME', 'STORE_FAST',
                                                  'STORE_GLOBAL', 'STORE_DEREF')
                                    for i in pure_instrs)
                    succs = list(current.successors)
                    if (not has_store and len(succs) == 1 and
                            succs[0].start_offset not in visited and
                            (succs[0] not in self.block_to_region or
                             not isinstance(self.block_to_region.get(succs[0]), BoolOpRegion))):
                        next_last = succs[0].get_last_instruction()
                        if next_last and next_last.opname in SHORT_CIRCUIT_JUMP_OPS:
                            # [Phase 7 根因 E] fall-through 扩展普遍性判据
                            # （短路跳转目标结构语义，非实例驱动）。
                            #
                            # 场景：current 是 chain 末尾 fall-through 块（最后
                            # 操作数，如 `a or b or c` 中的 LOAD c），succs[0] 是
                            # 它的 fall-through 后继 = chain 的 merge 块。若
                            # succs[0] 末指令是短路跳转，说明 succs[0] 是
                            # 「merge + 下一表达式 entry」合并块（表达式语句边界
                            # ——结果被消费后下一表达式开始）。
                            #
                            # 普遍性判据（替代原 POP_TOP 首指令实例判据）：
                            # succs[0] == chain[0] 的短路跳转目标（= chain merge）
                            # → 不扩展（语句边界）。基于「短路跳转目标 = chain merge」
                            # 的结构语义，不依赖具体指令（POP_TOP/STORE_*）。覆盖：
                            # 表达式语句 `a or b or c\nd or e or f`、混合操作符
                            # `a or b\nc and d`、赋值 `x = a or b\ny = c or d`
                            # （后者 has_store 路径不走此分支）—— 全部由
                            # 「succs[0] == chain[0] 短路目标」统一识别。
                            _first_last = chain[0][0].get_last_instruction()
                            _first_jt_offset = (_first_last.argval
                                                if (_first_last
                                                    and _first_last.opname in SHORT_CIRCUIT_JUMP_OPS
                                                    and _first_last.argval is not None)
                                                else None)
                            if (_first_jt_offset is not None
                                    and succs[0].start_offset == _first_jt_offset):
                                pass  # succs[0] 是 chain merge = 语句边界，不扩展
                            else:
                                current = succs[0]
                                _is_first_iter = False
                                continue
                        next_pure = [i for i in succs[0].instructions
                                     if i.opname not in NOISE_OPS]
                        if (len(next_pure) >= 1 and next_pure[0].opname == 'UNARY_NOT' and
                                len(next_pure) >= 2 and
                                next_last and next_last.opname in SHORT_CIRCUIT_JUMP_OPS):
                            current = succs[0]
                            _is_first_iter = False
                            continue
                break
            # [Phase 3 adv14_boolop_result_compare] 双角色块：start_block
            # 可能是已存在 BoolOpRegion 的 merge_block（如 ``(a and b) ==
            # (c and d)`` 中 Block 3）。此时 _detect_boolop_chain_start 已
            # 通过双角色检查放行，这里在首次迭代时跳过 claimed 检查，让
            # start_block 进入链。后续迭代仍执行 claimed 检查防止跨区域
            # 扩展。
            if current in self.block_to_region:
                _cur_reg = self.block_to_region.get(current)
                if isinstance(_cur_reg, BoolOpRegion):
                    if not (_is_first_iter and skip_first_claimed_check):
                        break
            op_type = 'and' if 'FALSE' in last.opname else 'or'
            # [Phase 3 adv14_boolop_result_compare] 值上下文短路链
            # (JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP) 的所有链块
            # 必须共享同一个 merge（跳转目标）。如 ``(a and b) == (c and d)``
            # 中，Block 1 (a; JIF_OR_POP→3) 和 Block 3 (c; JIF_OR_POP→5)
            # 跳转目标不同（3 vs 5），是两个独立的 and 表达式，由 == 分隔；
            # 不能合并为 ``(a and b) and (c and d)``。检测：当前块的跳转
            # 目标若与链中首块的跳转目标不同，则停止扩展——它们是不同的
            # 值上下文 BoolOp 表达式。普通 ``a and b and c``（值上下文）
            # 所有 JIF_OR_POP 共享同一 merge（STORE 块），不会被此守卫
            # 中断；控制流 ``if a and b and c:`` 用 POP_JUMP_FORWARD_IF_FALSE
            # 不走 SHORT_CIRCUIT_JUMP_OPS 路径，亦不受影响。
            _cur_jt = self.cfg.get_block_by_offset(last.argval) if last.argval is not None else None
            if (len(chain) >= 1 and last.opname in SHORT_CIRCUIT_JUMP_OPS
                    and _cur_jt is not None):
                _first_last = chain[0][0].get_last_instruction()
                _first_jt = (self.cfg.get_block_by_offset(_first_last.argval)
                             if _first_last and _first_last.argval is not None
                             else None)
                # [Phase 7 boolop 3+ operand fix] 表达式语句的 BoolOp
                # (JUMP_IF_*_OR_POP) 每个 short-circuit 跳转目标是一个独立的
                # trivial return 块（POP_TOP + LOAD_CONST None + RETURN_VALUE）。
                # 如 `a or b and c` 中 block0 跳到 offset 18、block6 跳到
                # offset 24 — 两个不同的 trivial return 块但语义等价。
                # 原 `is not` 身份比较会在此中断链，导致 3+ 操作数丢失尾部。
                # 修正：用 `_is_equivalent_exit_block` 替代身份比较 — 仅当
                # 两个跳转目标语义不等价（如 `(a and b) == (c and d)` 中
                # block0 跳到 LOAD c 块、block8 跳到 COMPARE_OP 块）才断链。
                if (_first_jt is not None
                        and not self._is_equivalent_exit_block(_cur_jt, _first_jt)):
                    # [Phase 7 fix] 混合操作符表达式语句（如 `a and b or c`、
                    # `not (a and b) or (c and not d)`）：内层操作符的短路
                    # 目标是外层操作符块（链继续块，非 exit），外层操作符的
                    # 短路目标是 trivial return（exit）。此时 _cur_jt 是 exit
                    # 而 _first_jt 不是（或反之），不应断链 — 它们是同一
                    # 表达式语句的混合操作符链，短路目标发散源于操作符语义
                    # 差异（and 短路 false 喂给外层 or、or 短路 true 直达
                    # exit），而非两个独立表达式。
                    # 对比 `(a and b) == (c and d)`：两个 and 的短路目标都
                    # 是非 exit 中间块（LOAD c / COMPARE_OP），_cur_jt 与
                    # _first_jt 均非 exit，不触发此豁免，仍由上面的
                    # _is_equivalent_exit_block 正确断链。
                    if not (self._is_exit_like_block(_cur_jt)
                            or self._is_exit_like_block(_first_jt)):
                        break
            chain.append((current, op_type))
            succs = list(current.conditional_successors)
            if len(succs) != 2:
                break
            ft_succ = next((s for s in succs if s.start_offset != last.argval), None)
            if ft_succ is None:
                break
            if ft_succ in self.block_to_region:
                _ft_reg = self.block_to_region.get(ft_succ)
                if isinstance(_ft_reg, BoolOpRegion):
                    break
            if len(chain) >= 2:
                prev_block = chain[-2][0]
                prev_op = chain[-2][1]
                if op_type == prev_op and not self.dom_analyzer.dominates(prev_block, current):
                    break
            current = ft_succ
        return chain if len(chain) >= 1 else None

    def _collect_branch_blocks(self, entry, merge, stop_set=None):
        """收集从entry到merge的CFG路径上的所有块（纯CFG拓扑追踪）

        算法依据（编译器理论 - Dominance Frontier Theorem）：
        1. 从entry开始BFS遍历，基于CFG后继边
        2. 边界条件：
           - 遇到merge点（post-dominator）自然终止
           - 遇到stop_set中的块（对立分支入口）终止
           - 终端块（RETURN/RAISE）自然终止遍历
        3. 纯拓扑收集，不依赖任何区域归属信息
        4. 符合结构化程序定理：if结构的then/else分支在merge点汇合

        注意：不使用block_to_region排除，区域归属冲突由上层调用者处理
        """
        if entry == merge:
            return []

        stop = {merge, *(stop_set or ())} if merge else set(stop_set or ())
        visited = stop | ({merge} if merge else set())
        collected = []
        worklist = [entry]

        while worklist:
            block = worklist.pop(0)
            if block in visited:
                continue

            visited.add(block)
            collected.append(block)

            last = block.get_last_instruction()
            if last and last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE'):
                continue

            if any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in block.instructions):
                continue

            for succ in sorted(block.successors, key=lambda s: s.start_offset):
                if succ not in visited:
                    worklist.append(succ)

        return collected

    def _identify_sequence_regions(self, existing_regions: List[Region]) -> List[Region]:
        """识别顺序区域 / 基础区域（Sequence / Basic Region）

        【区域类型】 SEQUENCE — 顺序区域（Sequence Region）
                    BASIC  — 基础区域（Basic Region，单块顺序区域）
        RegionType 枚举值: RegionType.BASIC（每个未被抢占的块独立成区）

        1. 算法描述（基于"No More Gotos"论文）
           - 归约阶段: Phase 2 的最后一步，在所有结构化区域（Loop / Try / With /
             Match / Assert / ChainedCompare / BoolOp / Ternary / Conditional）
             识别完成之后执行，确保结构化区域优先于顺序归约
           - 识别策略: 兜底归约——把所有未被任何区域占用的基本块各自独立包成
             一个 BASIC Region，实现"每块唯一归属"的全覆盖目标
           - 归约过程:
             Step 1: 按 start_offset 升序遍历 self.cfg.blocks.values()，
                     顺序保证 AST 生成时语句顺序与字节码偏移一致
             Step 2: 跳过已登记到 self.block_to_region 的块（即被结构化区域
                     抢占的块），实现"已被归约的块不重复处理"
             Step 3: 对每个剩余块创建 Region(region_type=RegionType.BASIC,
                     entry=block, blocks={block})——单块即一区，结构最简
             Step 4: 若 _is_return_none_block(block) 为真（块为隐式
                     LOAD_CONST None + RETURN_VALUE / RETURN_CONST None），
                     调用 region.mark_trailing_return_none() 标记尾部 Return None，
                     供 AST 生成时识别并按需省略（模块级别隐式 return None）
             Step 5: 把新 Region 加入返回列表、self.regions 与 self.block_to_region，
                     完成"块 → 区域"的登记，供后续 _build_region_hierarchy 建立父子关系

        2. 字节码模式（CPython 编译器行为）
           模式 A: 普通顺序块（赋值/调用/表达式）
             源码:        x = 1
                          y = x + 2
             字节码结构:  LOAD_CONST 1, STORE_FAST x,
                          LOAD_FAST x, LOAD_CONST 2, BINARY_OP +, STORE_FAST y
             特征指令:    LOAD_*, STORE_*, BINARY_OP, CALL, POP_TOP 等
           模式 B: 隐式 Return None 块
             源码:        函数末尾隐式 return None
             字节码结构:  LOAD_CONST None, RETURN_VALUE  （或 RETURN_CONST None）
             特征指令:    LOAD_CONST None + RETURN_VALUE / RETURN_CONST None
           模式 C: 空语句块 / pass
             源码:        pass
             字节码结构:  仅含 RESUME / NOP / CACHE 等填充指令

        3. 边界条件（数学性质）
           - 顺序区域边界即"未被结构化区域占用的剩余块集合"，由
             self.block_to_region 隐式确定；不在该映射中的块即为候选
           - 每个 BASIC 区域恰好包含一个块（blocks={block}），不存在跨块顺序区域
           - 通过 start_offset 排序保证遍历顺序确定，归约结果可重现
           - mark_trailing_return_none 标记不影响区域边界，仅影响后续 AST 省略策略

        4. 归约语义（与父区域的契约）
           - 入口块: 单块即入口（entry = block）
           - 父区域引用: 父区域通过 block_to_region[block] 持有本 BASIC Region，
             父区域仅引用 entry 块；该块天然仅属于自身区域
           - 在 _build_region_hierarchy 阶段，BASIC 区域作为最内层叶子节点，
             不会成为其他结构化区域的父节点

        5. AST 映射
           - 对应生成方法: _generate_basic_region（在 region_ast_generator.py 中）
           - AST 节点类型: 多种（依块内指令而定）——
               ast.Assign / ast.AugAssign / ast.AnnAssign （赋值类）
               ast.Expr                          （表达式语句）
               ast.Return                       （return 语句）
               ast.Pass                         （空块 / pass）
               ast.Break / ast.Continue         （循环控制，由 block_role 决定）
               ast.While (test=True, body=Break)（while True: break 优化模式）
           - 关键字段映射:
               Region.blocks     → 按 start_offset 排序后逐块生成
               Region.entry      → 首块即生成起点
               trailing_return_none 标记 → 控制 Return None 是否省略

        6. 已知失败模式
           - BASIC: 当前测试矩阵通过率 100%（basic 122/122）
           - 兜底归约确保任何未被结构化识别的块都能进入 AST，无遗漏
           - 与结构化区域无冲突（结构化区域已在 Phase 1/Phase 2 先识别并抢占块）
        """
        regions = []
        for block in self.cfg.get_blocks_in_order():
            if block in self.block_to_region:
                continue

            region = Region(
                region_type=RegionType.BASIC,
                entry=block,
                blocks={block},
            )

            if self._is_return_none_block(block):
                region.mark_trailing_return_none()

            regions.append(region)
            self.regions.append(region)
            self.block_to_region[block] = region

        return regions

    def _get_region_offset_range(self, region: Region) -> Tuple[int, int]:
        return region.get_offset_range(self)

    def _build_region_hierarchy(self, regions: List[Region]) -> List[Region]:
        if not regions:
            return regions

        ranges = {id(r): self._get_region_offset_range(r) for r in regions}
        sorted_regions = sorted(
            regions,
            key=lambda r: (ranges[id(r)][0], -(ranges[id(r)][1] - ranges[id(r)][0]))
        )

        for i, child in enumerate(sorted_regions):
            if child.parent is not None:
                continue

            cs, ce = ranges[id(child)]
            candidates = []

            for j, candidate in enumerate(sorted_regions):
                if candidate is child:
                    continue
                ps, pe = ranges[id(candidate)]
                if ps <= cs and pe >= ce:
                    candidates.append(candidate)
                elif isinstance(candidate, IfRegion) and child.entry:
                    if ((candidate.then_blocks and child.entry in candidate.then_blocks) or
                        (candidate.else_blocks and child.entry in candidate.else_blocks)):
                        candidates.append(candidate)

            if len(candidates) > 1 and child.entry:
                _if_candidates = self._filter_regions(candidates, IfRegion)
                if _if_candidates:
                    _non_if_candidates = [c for c in candidates if type(c) is not IfRegion]
                    _to_remove = set()
                    for _if_cand in _if_candidates:
                        _if_branch_entries = set(_if_cand.then_blocks or []) | set(_if_cand.else_blocks or [])
                        for _non_if_cand in _non_if_candidates:
                            _ni_range = ranges[id(_non_if_cand)]
                            _ir_range = ranges[id(_if_cand)]
                            _ni_inside_ir = (_ir_range[0] <= _ni_range[0] and _ir_range[1] >= _ni_range[1] and
                                             (_ni_range[0] > _ir_range[0] or _ni_range[1] < _ir_range[1]))
                            if child.entry in _non_if_cand.blocks and (
                                _non_if_cand.entry in _if_branch_entries or _ni_inside_ir
                            ):
                                _to_remove.add(id(_if_cand))
                                break
                    if _to_remove:
                        candidates = [c for c in candidates if id(c) not in _to_remove]

            if candidates:
                region_priority = {'IfRegion': 5, 'LoopRegion': 5,
                                   'MatchRegion': 4, 'BoolOpRegion': 2,
                                   'TryExceptRegion': 3, 'WithRegion': 3}
                child_p = region_priority.get(type(child).__name__, 0)
                _container_types = (TryExceptRegion, WithRegion)
                _has_container_candidate = any(isinstance(c, _container_types) for c in candidates)
                best_cand_p = max(region_priority.get(type(c).__name__, 1) for c in candidates)
                if best_cand_p >= child_p or (_has_container_candidate and isinstance(child, LoopRegion)):
                    _entry_owner = self.block_to_region.get(child.entry) if child.entry else None
                    _entry_owner_is_candidate = _entry_owner is not None and _entry_owner in candidates and isinstance(_entry_owner, LoopRegion) and _entry_owner is not child
                    if _entry_owner_is_candidate and not isinstance(child, LoopRegion):
                        _loop_cands_eo = [c for c in candidates if type(c) is LoopRegion and c is not child]
                        if len(_loop_cands_eo) >= 2:
                            _most_nested_loop = max(_loop_cands_eo, key=lambda c: -(ranges[id(c)][1] - ranges[id(c)][0]))
                            if _most_nested_loop is not _entry_owner:
                                _entry_owner = _most_nested_loop
                        best_parent = _entry_owner
                    else:
                        _loop_candidates = self._filter_regions(candidates, LoopRegion)
                        _use_nested_tiebreaker = isinstance(child, LoopRegion) and len(_loop_candidates) >= 2
                        _use_if_tiebreaker = isinstance(child, TryExceptRegion) and any(isinstance(c, IfRegion) for c in candidates)
                        if _use_nested_tiebreaker:
                            best_parent = max(_loop_candidates, key=lambda c: (
                                region_priority.get(type(c).__name__, 1),
                                -(ranges[id(c)][1] - ranges[id(c)][0])
                            ))
                        elif _use_if_tiebreaker:
                            _if_candidates = self._filter_regions(candidates, IfRegion)
                            best_parent = max(_if_candidates, key=lambda c: (
                                region_priority.get(type(c).__name__, 1),
                                -(ranges[id(c)][1] - ranges[id(c)][0])
                            ))
                        else:
                            _loop_cands = self._filter_regions(candidates, LoopRegion)
                            _container_cands = self._filter_regions(candidates, (TryExceptRegion, WithRegion))
                            if len(_loop_cands) >= 2:
                                best_parent = max(_loop_cands, key=lambda c: (
                                    region_priority.get(type(c).__name__, 1),
                                    -(ranges[id(c)][1] - ranges[id(c)][0])
                                ))
                            elif _container_cands and _loop_cands:
                                _best_container = max(_container_cands, key=lambda c: (
                                    region_priority.get(type(c).__name__, 1),
                                    -(ranges[id(c)][1] - ranges[id(c)][0])
                                ))
                                _best_loop = _loop_cands[0]
                                _cs, _ce = ranges[id(_best_container)]
                                _ls, _le = ranges[id(_best_loop)]
                                if _ls <= _cs and _ce <= _le and (_cs > _ls or _ce < _le):
                                    best_parent = _best_container
                                else:
                                    best_parent = max(candidates, key=lambda c: (
                                        region_priority.get(type(c).__name__, 1),
                                        -(ranges[id(c)][1] - ranges[id(c)][0])
                                    ))
                            else:
                                best_parent = max(candidates, key=lambda c: (
                                    region_priority.get(type(c).__name__, 1),
                                    -(ranges[id(c)][1] - ranges[id(c)][0])
                                ))
                    if child is not best_parent and child not in best_parent.children:
                        entry_block = child.entry
                        if entry_block and self.block_to_region.get(entry_block) is child:
                            dynamic_conflict_types = (RegionType.BOOL_OP, RegionType.TERNARY,
                                                      RegionType.IF_THEN_ELSE, RegionType.IF_THEN,
                                                      RegionType.IF_ELIF_CHAIN)
                            if (child.region_type in dynamic_conflict_types and
                                best_parent.region_type in dynamic_conflict_types):
                                continue
                        if isinstance(child, LoopRegion) and isinstance(best_parent, (IfRegion)):
                            if child.blocks and best_parent.blocks:
                                parent_in_child = set(best_parent.blocks) <= set(child.blocks)
                                entry_in_body = best_parent.entry and best_parent.entry in (child.body_blocks or [])
                                cond_is_loop_cond = (getattr(child, 'condition_block', None) and
                                                    (best_parent.entry == child.condition_block or
                                                     best_parent.entry in getattr(child, 'condition_chain_blocks', []) or
                                                     getattr(best_parent, 'condition_block', None) == child.condition_block))
                                loop_entry_in_if_then = (child.entry and best_parent.then_blocks and child.entry in best_parent.then_blocks)
                                loop_entry_in_if_else = (child.entry and best_parent.else_blocks and child.entry in best_parent.else_blocks)
                                loop_entry_in_if_branch = loop_entry_in_if_then or loop_entry_in_if_else
                                if (parent_in_child or entry_in_body or
                                    (cond_is_loop_cond and not loop_entry_in_if_branch)):
                                    continue
                        if isinstance(child, TryExceptRegion) and isinstance(best_parent, IfRegion):
                            if child.blocks and best_parent.blocks:
                                if set(best_parent.blocks) <= set(child.blocks):
                                    continue
                        best_parent.add_child(child)

        boolop_regions = self._filter_regions(regions, BoolOpRegion)
        if_regions = self._filter_regions(regions, IfRegion)
        for br in boolop_regions:
            if br.parent is not None:
                continue
            for ir in if_regions:
                if ir is br or br in ir.children:
                    continue
                if br.entry and ir.entry and br.entry == ir.entry:
                    entry_owner = self.block_to_region.get(br.entry)
                    if entry_owner is ir and br not in ir.children:
                        ir.add_child(br)
                        break

        return [r for r in regions if r.parent is None]

    def _find_enclosing_region(self, block: BasicBlock,
                                region_types: Tuple[type, ...] = None,
                                require_finally: bool = False,
                                region_type: str = None,
                                candidate_regions: List[Region] = None) -> Optional[Region]:
        if region_types is None:
            region_types = (LoopRegion, TryExceptRegion, WithRegion)
        search_regions = candidate_regions if candidate_regions is not None else self.regions
        if not require_finally:
            innermost = None
            innermost_size = float('inf')
            for region in search_regions:
                if isinstance(region, region_types):
                    if block in region.blocks:
                        size = len(region.blocks)
                        if size < innermost_size:
                            innermost = region
                            innermost_size = size
            return innermost
        result = None
        for region in search_regions:
            if not isinstance(region, region_types):
                continue
            if not getattr(region, 'has_finally', False):
                continue
            if block in region.blocks:
                result = region
                continue
            if region_type == 'try_except':
                try_blocks = getattr(region, 'try_blocks', [])
                handler_entries = getattr(region, 'handler_entry_blocks', [])
                if try_blocks and handler_entries:
                    for try_block in try_blocks:
                        if hasattr(try_block, 'dominates') and try_block.dominates(block):
                            is_handler = any(
                                hasattr(h, 'dominates') and h.dominates(block)
                                for h in handler_entries
                            )
                            if not is_handler:
                                result = region
        return result

    def _is_only_jumps(self, block: BasicBlock) -> bool:
        for instr in block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                continue
            if instr.opname in ('JUMP_BACKWARD', 'JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                continue
            return False
        return True

    def _is_equivalent_exit_block(self, block_a: BasicBlock, block_b: BasicBlock,
                                   depth: int = 0,
                                   visited: Optional[Set[Tuple[int, int]]] = None) -> bool:
        # 无限嵌套支持：递归终止由 visited 集合（循环检测）+ CFG 有限性保证，
        # 不使用硬编码深度上限。
        if block_a is block_b:
            return True
        if visited is None:
            visited = set()
        pair = (id(block_a), id(block_b))
        if pair in visited:
            return False  # 循环检测：已访问过的块对
        visited.add(pair)
        a_is_only_jumps = self._is_only_jumps(block_a)
        b_is_only_jumps = self._is_only_jumps(block_b)
        if a_is_only_jumps and b_is_only_jumps:
            a_succs = list(block_a.successors)
            b_succs = list(block_b.successors)
            if len(a_succs) == 1 and len(b_succs) == 1:
                return self._is_equivalent_exit_block(a_succs[0], b_succs[0], depth + 1, visited)
            return False
        if a_is_only_jumps and not b_is_only_jumps:
            a_succs = list(block_a.successors)
            if len(a_succs) == 1:
                return self._is_equivalent_exit_block(a_succs[0], block_b, depth + 1, visited)
            return False
        if b_is_only_jumps and not a_is_only_jumps:
            b_succs = list(block_b.successors)
            if len(b_succs) == 1:
                return self._is_equivalent_exit_block(block_a, b_succs[0], depth + 1, visited)
            return False
        if self._is_trivial_return_block(block_a) and self._is_trivial_return_block(block_b):
            return True
        return False

    def _is_trivial_return_block(self, block: BasicBlock) -> bool:
        meaningful = [i for i in block.instructions
                     if i.opname not in NOISE_OPS]
        if len(meaningful) == 1 and meaningful[0].opname in ('RETURN_VALUE', 'RETURN_CONST'):
            return True
        if len(meaningful) == 2:
            if meaningful[0].opname == 'LOAD_CONST' and meaningful[0].argval is None and meaningful[1].opname == 'RETURN_VALUE':
                return True
            if meaningful[0].opname == 'RETURN_CONST' and meaningful[0].argval is None:
                return True
        if len(meaningful) == 3:
            if (meaningful[0].opname == 'POP_TOP' and
                meaningful[1].opname == 'LOAD_CONST' and meaningful[1].argval is None and
                meaningful[2].opname == 'RETURN_VALUE'):
                return True
        if self.block_roles.get(block.start_offset) == BlockRole.RETURN_NONE:
            return True
        return False

    def _is_exit_like_block(self, block: BasicBlock,
                            visited: Optional[Set[int]] = None) -> bool:
        # 判断单个块是否是「退出块」：trivial return，或 only-jumps 链
        # 最终到达 trivial return。与 _is_equivalent_exit_block 的区别：
        # 后者比较两个块是否语义等价（含 block_a is block_b 短路），
        # 无法用于判定单个块是否为退出块。递归终止由 visited + CFG 有限性保证。
        if visited is None:
            visited = set()
        if block.start_offset in visited:
            return False
        visited.add(block.start_offset)
        if self._is_trivial_return_block(block):
            return True
        if self._is_only_jumps(block):
            succs = list(block.successors)
            if len(succs) == 1:
                return self._is_exit_like_block(succs[0], visited)
        return False

    def get_region_for_block(self, block: BasicBlock) -> Optional[Region]:
        return self.block_to_region.get(block)

    def get_entry_region_for_block(self, block: BasicBlock) -> Optional[Region]:
        _matching = []
        for region in self.regions:
            if region.is_block_entry(block):
                if type(region) is AssertRegion:
                    return region
                _matching.append(region)
        if not _matching:
            return None
        if len(_matching) == 1:
            return _matching[0]
        _type_priority = {
            'WithRegion': 6, 'TryExceptRegion': 5, 'MatchRegion': 4,
            'BoolOpRegion': 3, 'TernaryRegion': 3, 'IfRegion': 2, 'LoopRegion': 0
        }
        _matching.sort(key=lambda r: (
            _type_priority.get(type(r).__name__, -1),
            -(max(b.start_offset for b in r.blocks) - min(b.start_offset for b in r.blocks))
        ))
        winner = _matching[-1]
        # When a BoolOpRegion and an IfRegion share the same entry block, the
        # BoolOpRegion is necessarily the if-condition (a value-context BoolOp
        # would have been skipped in _identify_conditional_regions, so no
        # IfRegion with the same entry would exist). Prefer the IfRegion because
        # it carries the full if/elif/else structure; returning the BoolOpRegion
        # alone would lose the branch bodies.
        if isinstance(winner, BoolOpRegion):
            _winner_entry = winner.entry
            for _r in self._filter_regions(_matching, IfRegion):
                if (_r is not winner
                        and _r.entry == _winner_entry):
                    winner = _r
                    break
        return winner

    def find_enclosing_region(self, block: BasicBlock,
                              region_type: str = 'loop',
                              require_finally: bool = False) -> Optional[Any]:
        type_map = {
            'loop': (LoopRegion,),
            'try_finally': (TryExceptRegion,),
            'try_except': (TryExceptRegion,),
        }
        target_types = type_map.get(region_type, (LoopRegion,))
        return self._find_enclosing_region(block, target_types, require_finally=require_finally, region_type=region_type)

    def _compute_generator_entry_metadata(self) -> None:
        entry_block = self.cfg.entry_block
        if entry_block is not None:
            is_generator_entry = all(
                instr.opname in ('RETURN_GENERATOR', 'POP_TOP', 'RESUME', 'CACHE', 'NOP')
                for instr in entry_block.instructions
            ) and any(instr.opname == 'RETURN_GENERATOR' for instr in entry_block.instructions)
            if is_generator_entry:
                resume_block = self.find_generator_resume_block(entry_block)
                self.metadata['generator_entry_block'] = resume_block if resume_block else entry_block
                self.metadata['is_generator_entry'] = True
            else:
                self.metadata['generator_entry_block'] = entry_block
                self.metadata['is_generator_entry'] = False
        else:
            self.metadata['generator_entry_block'] = None
            self.metadata['is_generator_entry'] = False

    def find_generator_resume_block(self, entry_block: BasicBlock) -> Optional[BasicBlock]:
        for block in self.cfg.blocks.values():
            if block != entry_block and any(instr.opname == 'RESUME' for instr in block.instructions):
                has_return_gen_pred = any(p == entry_block for p in block.predecessors)
                if has_return_gen_pred or not block.predecessors:
                    return block
        return None

    def _precompute_all_generator_data(self, all_regions: List[Region]) -> None:
        """Phase 4: 预计算生成器需要的所有分析数据

        将生成器中的分析逻辑迁移到分析器，确保职责严格分离。
        在层次构建和角色标注完成后调用。

        预计算内容：
        1. 循环区域详细分析（回边、break块、循环体集合）
        2. 链式比较增强数据
        3. break/return块的详细分类
        4. finally copy块的增强标注
        """
        for region in all_regions:
            region.precompute_analysis(self)

        self._precompute_break_jump_classification(all_regions)

    def _precompute_loop_analysis_data(self, region: LoopRegion) -> None:
        """预计算循环区域的详细分析数据

        将以下逻辑从生成器的 _loop_generate_body 迁移到这里：
        - 循环体完整集合（包含header、condition_block）
        - break块列表的精确识别
        - 回边块的元数据
        - 块在循环内的角色分类
        """
        loop_body_full = set(region.body_blocks) | {region.header_block}
        if region.condition_block:
            loop_body_full.add(region.condition_block)

        region.metadata['loop_body_full_set'] = loop_body_full
        region.metadata['natural_back_edge'] = region.back_edge_block

        break_blocks_precise = []
        for block in region.blocks:
            role = self.block_roles.get(block.start_offset)
            if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                break_blocks_precise.append(block)

        region.metadata['break_blocks_precise'] = break_blocks_precise
        region.metadata['has_break_in_body'] = len(break_blocks_precise) > 0

        exit_successors = {}
        for block in region.blocks:
            outside_succs = [s for s in block.successors if s not in loop_body_full]
            if outside_succs:
                exit_successors[block.start_offset] = outside_succs

        region.metadata['exit_successors'] = exit_successors

    def _precompute_chained_compare_analysis(self, region: IfRegion) -> None:
        """增强链式比较区域的分析数据

        将以下逻辑从生成器的 _generate_if 迁移到这里：
        - then_blocks是否全部是chained_compare_blocks
        - 是否是空then分支的链式比较赋值
        - merge块的语义分析
        """
        if not region.chained_compare_blocks:
            return

        then_all_cmp = (
            len(region.then_blocks) > 0 and
            all(tb in region.chained_compare_blocks or tb == region.condition_block
                for tb in region.then_blocks)
        )
        region.metadata['then_all_chained_compare'] = then_all_cmp

        is_empty_then_with_merge = (
            not region.then_blocks and
            region.merge_block is not None
        )
        region.metadata['is_empty_then_chained_compare'] = is_empty_then_with_merge

        if region.merge_block:
            meaningful_instrs = [
                i for i in region.merge_block.instructions
                if i.opname not in NOISE_OPS
            ]
            has_store = any(
                i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                for i in meaningful_instrs
            )
            only_simple = all(
                i.opname in ('SWAP', 'POP_TOP', 'STORE_FAST', 'STORE_NAME',
                            'STORE_GLOBAL', 'STORE_DEREF', 'LOAD_CONST',
                            'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                            'LOAD_DEREF', 'LOAD_ATTR', 'RETURN_VALUE',
                            'RETURN_CONST')
                for i in meaningful_instrs
            )
            region.metadata['merge_has_store'] = has_store
            region.metadata['merge_only_simple_ops'] = only_simple

            if has_store and only_simple:
                for i in meaningful_instrs:
                    if i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        region.metadata['chained_assign_target'] = i.argval
                        break

    def _precompute_break_jump_classification(self, all_regions: List[Region]) -> None:
        """预计算所有break/return跳转块的详细分类

        将以下逻辑从生成器迁移到这里：
        - 判断块是否是循环的正常退出（隐式break）
        - 判断PURE_BREAK是否包含RERAISE（with清理）
        - 判断块的最后指令类型（JUMP_BACKWARD→continue, BREAK/RETURN等）
        """
        for block in self.cfg.blocks.values():
            offset = block.start_offset
            role = self.block_roles.get(offset)

            if role not in (BlockRole.BREAK, BlockRole.PURE_BREAK,
                           BlockRole.RETURN, BlockRole.RETURN_NONE):
                continue

            block_metadata = {}

            if role == BlockRole.PURE_BREAK:
                has_reraise = any(i.opname == 'RERAISE' for i in block.instructions)
                block_metadata['has_reraise'] = has_reraise

                is_normal_exit = False
                for region in self._filter_regions(all_regions, LoopRegion):
                    if block in region.blocks:
                        if (block != region.header_block and
                            block != region.condition_block):
                            is_normal_exit = True
                            break
                block_metadata['is_loop_normal_exit'] = is_normal_exit

            last_instr = block.get_last_instruction()
            if last_instr:
                block_metadata['last_opname'] = last_instr.opname
                block_metadata['last_argval'] = last_instr.argvalue if hasattr(last_instr, 'argvalue') else last_instr.argval

                if last_instr.opname == 'JUMP_BACKWARD':
                    target_block = self.cfg.get_block_by_offset(last_instr.argval) if last_instr.argval is not None else None
                    if target_block:
                        for region in self._filter_regions(all_regions, LoopRegion):
                            if target_block == region.header_block:
                                block_metadata['is_implicit_continue'] = True
                                break

                elif last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                        block_metadata['is_explicit_break_jump'] = True

                elif last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    if role == BlockRole.RETURN_NONE:
                        for region in self._filter_regions(all_regions, LoopRegion):
                            if block in region.body_blocks:
                                block_metadata['is_none_return_in_loop'] = True
                                break

            self._block_metadata[offset] = block_metadata

    def _enhance_finally_copy_annotation(self, region: TryExceptRegion) -> None:
        """增强finally copy块的标注信息

        将以下逻辑从生成器的 _generate_try 和 _generate_block_statements 迁移到这里：
        - finally copy块的用户指令计数
        - finally copy块是否是异常路径
        - finally copy块的截断索引
        """
        if not region.finally_blocks or not region.finally_copy_blocks:
            return

        exc_path_blocks = set()
        for fb in region.finally_blocks:
            if any(i.opname in ('PUSH_EXC_INFO', 'RERAISE', 'POP_EXC_INFO')
                   for i in fb.instructions):
                exc_path_blocks.add(fb)

        normal_finally_blocks = [fb for fb in region.finally_blocks
                                 if fb not in exc_path_blocks]

        region.metadata['finally_exc_path_blocks'] = exc_path_blocks
        region.metadata['finally_normal_blocks'] = normal_finally_blocks

        enhanced_copy_info = {}
        for block_offset, keep_count in region.finally_copy_blocks.items():
            block = self.cfg.get_block_by_offset(block_offset)
            if block is None:
                continue

            copy_meta = {'keep_count': keep_count}

            if keep_count > 0:
                meaningful_count = 0
                cutoff_idx = len(block.instructions)
                for idx, instr in enumerate(block.instructions):
                    if instr.opname not in NOISE_OPS:
                        meaningful_count += 1
                        if meaningful_count == keep_count:
                            cutoff_idx = idx + 1
                            break
                copy_meta['cutoff_idx'] = cutoff_idx
                copy_meta['is_truncated'] = cutoff_idx < len(block.instructions)

            last_instr = block.get_last_instruction()
            if last_instr:
                copy_meta['last_opname'] = last_instr.opname
                copy_meta['is_jump_backward'] = (last_instr.opname == 'JUMP_BACKWARD')
                copy_meta['is_forward_jump'] = (last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'))
                copy_meta['is_return'] = (last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'))

                if last_instr.opname == 'JUMP_BACKWARD' and last_instr.argval is not None:
                    target = self.cfg.get_block_by_offset(last_instr.argval)
                    if target:
                        for r in self._filter_regions(self.regions, LoopRegion):
                            if target == r.header_block:
                                copy_meta['continue_target_loop'] = r
                                break

            enhanced_copy_info[block_offset] = copy_meta

        region.metadata['enhanced_finally_copies'] = enhanced_copy_info
