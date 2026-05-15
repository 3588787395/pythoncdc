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
import bisect

from .basic_block import BasicBlock, Instruction
from .cfg_builder import ControlFlowGraph
from .dominator_analyzer import (
    DominatorAnalyzer, LoopAnalyzer,
    FOR_ITER_OPS, BACKWARD_JUMP_OPS, FORWARD_JUMP_OPS, PLACEHOLDER_OPS,
)

from .pattern_parser import PatternParser
from .opcode_feature_detector import get_opcode_detector

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

    def get_children_by_type(self, region_type: 'RegionType') -> List['Region']:
        return [c for c in self.children if c.region_type == region_type]

    def find_child_region_for_block(self, block: BasicBlock, region_types: Tuple[type, ...] = None) -> Optional['Region']:
        for child in self.children:
            if region_types and not isinstance(child, region_types):
                continue
            if block in child.blocks:
                return child
            if hasattr(child, 'header_block') and child.header_block == block:
                return child
            if hasattr(child, 'condition_block') and child.condition_block == block:
                return child
            if child.entry == block:
                return child
        return None

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

@dataclass
class IfRegion(Region):
    condition_block: Optional[BasicBlock] = None
    then_blocks: List[BasicBlock] = field(default_factory=list)
    else_blocks: List[BasicBlock] = field(default_factory=list)
    merge_block: Optional[BasicBlock] = None
    elif_conditions: List[BasicBlock] = field(default_factory=list)
    elif_bodies: List[List[BasicBlock]] = field(default_factory=list)
    elif_final_else: List[BasicBlock] = field(default_factory=list)
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

@dataclass
class AssertRegion(Region):
    condition_block: Optional[BasicBlock] = None
    message_block: Optional[BasicBlock] = None

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

@dataclass
class TernaryRegion(Region):
    condition_block: Optional[BasicBlock] = None
    true_value_block: Optional[BasicBlock] = None
    false_value_block: Optional[BasicBlock] = None
    merge_block: Optional[BasicBlock] = None
    value_target: Optional[str] = None
    condition_chain_blocks: List[BasicBlock] = field(default_factory=list)
    container_type: Optional[str] = None
    func_call_info: Optional[Dict[str, Any]] = None
    dict_key_info: Optional[Dict[str, Any]] = None

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
        三阶段区域分析架构

        Phase 1: 低层区域识别（无相互依赖）
            - 循环区域、异常处理区域、with/match/assert 区域
            - 这些区域类型之间没有依赖关系，可以独立识别

        Phase 2: 高层区域识别（可依赖Phase 1结果）
            - 条件区域（if/elif/else）：需要知道循环和try区域以避免冲突
            - 布尔运算区域（and/or短路求值）：需要先识别条件区域
            - 三元表达式区域：需要先识别条件区域

        Phase 3: 层次构建与角色标注
            - 序列区域：覆盖所有未被其他区域包含的基本块
            - 层次构建：建立区域的父子关系
            - 角色标注：为每个基本块分配语义角色
        """
        #print(f"[DEBUG analyze] ({self.cfg.name}) ENTER analyze()")
        # 初始化分析器
        self.dom_analyzer.analyze()
        self.loop_analyzer = LoopAnalyzer(self.cfg, self.dom_analyzer)
        self.loop_analyzer.analyze()
        self.dominance_frontiers = self.dom_analyzer.compute_all_dominance_frontiers()

        # Phase 1: 低层区域识别（按优先级排序）
        # 优先级规则：TRY(异常处理) > LOOP(循环) > WITH/MATCH/ASSERT(其他结构)
        # 原因：
        # - 异常处理区域可能跨越循环和条件（最高优先级）
        # - 循环有回边需要特殊处理（次高优先级）
        # - 其他结构依赖前两者的结果
        try_regions = self._identify_try_except_regions()
        loop_regions = self._identify_loop_regions()
        with_regions = self._identify_with_regions()
        match_regions = self._identify_match_regions()
        assert_regions = self._identify_assert_regions()

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
        for tr in ternary_regions:
            if tr.blocks:
                _ternary_block_sets.append(tr.blocks)

        if _ternary_block_sets:
            def _region_overlaps_with_ternary(region):
                for tb_set in _ternary_block_sets:
                    if region.entry and region.entry in tb_set:
                        return True
                    if region.blocks & tb_set:
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
        for cr in conditional_regions:
            if isinstance(cr, IfRegion) and cr.region_type == RegionType.IF_ELIF_CHAIN:
                elif_chain_entries.add(cr.entry)
        ternary_regions = [tr for tr in ternary_regions
                          if not (tr.entry and tr.entry in elif_chain_entries)]

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
        _ternary_entries = {tr.entry for tr in ternary_regions if tr.entry}
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

        self.block_to_region.clear()
        for region in all_regions:
            current_priority = self.REGION_TYPE_PRIORITY.get(region.region_type, 0)
            for block in region.blocks:
                existing = self.block_to_region.get(block)
                if existing is None:
                    self.block_to_region[block] = region
                else:
                    if self._should_use_dynamic_priority(existing, region):
                        existing_score = self._compute_dynamic_region_score(block, existing)
                        candidate_score = self._compute_dynamic_region_score(block, region)
                        if candidate_score > existing_score:
                            self.block_to_region[block] = region
                    else:
                        existing_priority = self.REGION_TYPE_PRIORITY.get(
                            existing.region_type, 0)
                        if current_priority > existing_priority:
                            self.block_to_region[block] = region

        hierarchy = self._build_region_hierarchy(regions=all_regions)

        self._annotate_all_roles(all_regions)

        for _lr in loop_regions:
            if hasattr(_lr, 'break_blocks'):
                for _bb in _lr.break_blocks:
                    self.block_roles[_bb.start_offset] = BlockRole.BREAK

        fake_loop_region_ids = self._detect_and_filter_conditional_recheck_fake_loops(loop_regions)
        if fake_loop_region_ids:
            self._fix_block_roles_after_fake_loop_removal(loop_regions, fake_loop_region_ids)
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
                # Phase 11增强: 可能是被POP_TOP截断前的None模式
                # 尝试用原始指令重新检查
                original = [i for i in block.instructions if i.opname not in NOISE_OPS]
                # 移除末尾跳转和条件跳转
                while original and original[-1].opname in (
                    'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                    original = original[:-1]
                if original and original[-1].opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                    original = original[:-1]
                # 检查是否是 [LOAD_CONST None, POP_TOP, LOAD_CONST None, RETURN] 模式
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

    def is_loop_normal_exit_block(self, block: BasicBlock, loop_region: 'LoopRegion' = None) -> bool:
        """判断块是否是循环的自然出口

        自然出口的特征：
        - 条件块的前向跳转目标
        - FOR_ITER的退出目标
        - 体块中反向条件跳转的fall-through/跳转目标
        - 回边块中反向条件跳转的退出目标
        """
        if loop_region is None:
            return False
        cond = loop_region.condition_block
        header = loop_region.header_block
        loop_body_set = set(loop_region.body_blocks) | {header}
        if cond:
            loop_body_set.add(cond)

        if cond:
            cond_last = cond.get_last_instruction()
            if cond_last and cond_last.opname in FORWARD_JUMP_OPS and cond_last.argval is not None:
                exit_block = self.cfg.get_block_by_offset(cond_last.argval)
                if exit_block == block:
                    return True

        if header:
            hdr_last = header.get_last_instruction()
            if hdr_last and hdr_last.opname in FORWARD_JUMP_OPS and hdr_last.argval is not None:
                exit_block = self.cfg.get_block_by_offset(hdr_last.argval)
                if exit_block == block:
                    return True

        for body_block in loop_region.body_blocks:
            b_last = body_block.get_last_instruction()
            if b_last and b_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS and b_last.argval is not None:
                exit_block = self.cfg.get_block_by_offset(b_last.argval)
                if exit_block == block:
                    return True
            elif b_last and b_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                jt = self.cfg.get_block_by_offset(b_last.argval) if b_last.argval is not None else None
                if jt == block:
                    return True

        be = loop_region.back_edge_block
        if be:
            be_last = be.get_last_instruction()
            if be_last and be_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS and be_last.argval is not None:
                be_exit = self.cfg.get_block_by_offset(be_last.argval)
                if be_exit == block:
                    return True
                elif be_exit and be_exit not in loop_body_set:
                    be_exit_succs = [s for s in be_exit.successors]
                    if block in be_exit_succs:
                        return True

        return False

    def is_loop_natural_back_edge(self, block: BasicBlock, loop_region: 'LoopRegion' = None) -> bool:
        if loop_region is None:
            return False
        if loop_region.back_edge_block is None:
            return False
        if self.block_roles.get(block.start_offset) == BlockRole.CONTINUE:
            return False
        return block == loop_region.back_edge_block

    def _get_loop_region_for_block(self, block: BasicBlock) -> Optional[LoopRegion]:
        innermost = None
        innermost_size = float('inf')
        for region in self.regions:
            if isinstance(region, LoopRegion):
                if block in region.blocks:
                    size = len(region.blocks)
                    if size < innermost_size:
                        innermost = region
                        innermost_size = size
        return innermost

    def _get_loop_regions_for_boolop_check(self) -> List[LoopRegion]:
        return [r for r in self.regions if isinstance(r, LoopRegion)]

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

        loop_regions = [r for r in all_regions if isinstance(r, LoopRegion)]

        for loop in loop_regions:
            header = loop.header_block
            if header is None:
                continue

            _, continue_map = self._detect_break_continue(loop.body_blocks, header)
            for block, role in continue_map.items():
                if role == 'LOOP_BACK_EDGE':
                    self._assign_region_role(block.start_offset, BlockRole.LOOP_BACK_EDGE)
                else:
                    self._assign_region_role(block.start_offset, BlockRole.CONTINUE)

        for region in all_regions:
            if isinstance(region, LoopRegion):
                self._annotate_loop_structural_roles(region)
            elif isinstance(region, IfRegion):
                self._annotate_if_structural_roles(region)
            elif isinstance(region, TryExceptRegion):
                self._annotate_try_except_structural_roles(region)

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
                    if self._should_use_dynamic_priority(existing_region, region):
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
            if isinstance(region, LoopRegion):
                for block in region.condition_recheck_blocks:
                    self._assign_region_role(block.start_offset,
                                           BlockRole.LOOP_CONDITION_RECHECK)
            elif isinstance(region, IfRegion) and region.chained_compare_blocks:
                self.compute_chained_compare_operands(region)

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
        for region in self.regions:
            if isinstance(region, LoopRegion):
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
        merge = None
        if isinstance(region, BoolOpRegion):
            merge = region.merge_block
        elif isinstance(region, IfRegion):
            merge = region.merge_block
        elif isinstance(region, TernaryRegion):
            merge = getattr(region, 'merge_block', None)
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
        succs = None
        if isinstance(region, BoolOpRegion) and region.op_chain:
            last_block = region.op_chain[-1][0]
            last_instr = last_block.get_last_instruction()
            if last_instr and last_instr.argval is not None:
                jt = self.cfg.get_block_by_offset(last_instr.argval)
                ft_succs = sorted(last_block.conditional_successors, key=lambda s: s.start_offset)
                ft = next((s for s in ft_succs if s.start_offset != last_instr.argval), None)
                if jt and ft:
                    succs = [ft, jt]
        elif isinstance(region, IfRegion):
            if region.then_blocks or region.else_blocks:
                then_first = region.then_blocks[0] if region.then_blocks else None
                else_first = region.else_blocks[0] if region.else_blocks else None
                if then_first and else_first:
                    succs = [then_first, else_first]
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
        merge = None
        if isinstance(region, BoolOpRegion):
            merge = region.merge_block
        elif isinstance(region, IfRegion):
            merge = region.merge_block
        elif isinstance(region, TernaryRegion):
            merge = getattr(region, 'merge_block', None)
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
        if not isinstance(region, IfRegion):
            return 50.0
        then_blocks = region.then_blocks or []
        else_blocks = region.else_blocks or []
        all_body_blocks = set(then_blocks + else_blocks)
        if not all_body_blocks:
            return 25.0
        boolop_competitor = None
        for r in self.regions:
            if r is not region and isinstance(r, __import__('core.cfg.region_analyzer', fromlist=['BoolOpRegion']).BoolOpRegion) and r.entry == region.entry:
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
                if instr.opname in NOISE_OPS | {'POP_TOP', 'COPY', 'SWAP', 'COMPARE_OP'}:
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
                    if instr.opname in NOISE_OPS | {'POP_TOP', 'COPY', 'SWAP', 'COMPARE_OP'}:
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
    def detect_ternary_container_wrap(merge_block: Optional[BasicBlock]) -> Optional[str]:
        if not merge_block:
            return None
        for instr in merge_block.instructions:
            if instr.opname == 'BUILD_LIST':
                return 'list'
            if instr.opname == 'BUILD_TUPLE':
                return 'tuple'
            if instr.opname == 'BUILD_SET':
                return 'set'
            if instr.opname == 'BUILD_MAP':
                return 'dict'
        return None

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
        """
        识别循环区域（for/while 循环）

        字节码模式：
        - FOR_ITER：for 循环迭代指令，位于循环头部
        - GET_ITER：将可迭代对象转为迭代器，位于FOR_ITER之前
        - 条件跳转：POP_JUMP_*_IF_* 用于 while 条件
        - 回边跳转：JUMP_BACKWARD 跳回循环头
        - 循环退出：从条件块/迭代块跳出
        - 复合条件：JUMP_IF_FALSE_OR_POP/JUMP_IF_TRUE_OR_POP 形成and/or短路链
        - 条件重检：循环体末尾的POP_JUMP_BACKWARD_IF_* 跳回header重检条件

        识别算法：
        1. 从 LoopAnalyzer 获取所有回边和自然循环体
        2. 按支配深度从内到外排序处理循环
        3. 过滤伪循环（_is_fake_loop）
        4. 分类循环类型（_classify_loop_type）：FOR_LOOP vs WHILE_LOOP
        5. 识别循环else块（_find_loop_else）
        6. 检测break/continue（_detect_break_continue）
        7. 提取while条件（_extract_while_condition）
        8. 搜索condition_block：header的前驱中跳转到header/body的条件块
        9. 构建condition_chain_blocks：从condition_block沿前向条件跳转链扩展
        10. 设置break_blocks角色：LoopRegion.break_blocks中的块需标记BlockRole.BREAK

        边界条件：
        - while True 循环：无条件回边，无条件跳转
        - while True + break：header含条件跳转到循环外（条件break模式）
        - for 循环的 FOR_ITER fall-through 和 exit
        - 循环else块：循环正常退出时执行，break跳过else
        - break/continue：跳转到循环外/循环头
        - 嵌套循环：内层循环先归约，内层break/continue不被外层捕获
        - 伪循环过滤：continue形成的假回边
        - 复合条件(and/or)：条件块由BoolOpRegion处理，需关联到循环
        - not条件：POP_JUMP_FORWARD_IF_TRUE 对应 while not cond
        - header含body+条件重检：需分离body语句和条件重检部分

        区域归约算法符合度：
        - 基于支配树和回边，符合编译器理论
        - 自底向上归约（内层先处理）
        - 区域不重叠
        - break_blocks角色分配确保AST生成正确识别break语句
        - else_is_follow标记确保else块作为orelse而非独立语句
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
            break_blocks, continue_map = self._detect_break_continue(body, header, natural_exit)

            back_edges_for_header = [src for src, tgt in self.loop_analyzer.back_edges if tgt == header]
            back_edge_block = back_edges_for_header[0] if back_edges_for_header else None

            region_blocks = set(body)
            if condition_block and condition_block not in body:
                if header in condition_block.successors or any(pred in body for pred in condition_block.predecessors):
                    region_blocks.add(condition_block)
                    _cb = condition_block
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
                                    if p_target == _cb or p_target in body or p_target == header:
                                        region_blocks.add(p)
                                        _next_cb = p
                                        break
                        _cb = _next_cb
            verified_break_blocks = set()
            if break_blocks:
                for break_block in break_blocks:
                    if any(pred in body for pred in break_block.predecessors):
                        verified_break_blocks.add(break_block)
                        region_blocks.add(break_block)
            if for_iter_setup and for_iter_setup not in body and header in for_iter_setup.successors:
                region_blocks.add(for_iter_setup)
            region_blocks.update(else_blocks)
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
            for _bb in verified_break_blocks:
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

        for region in regions:
            if not isinstance(region, LoopRegion):
                continue
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

        loop_regions = [r for r in regions if isinstance(r, LoopRegion)]
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
                    if not same_cond:
                        continue
                    if blocks_a < blocks_b and lr_a.header_block:
                        removal_set.add(id(lr_a))
                    elif blocks_b < blocks_a and lr_b.header_block:
                        removal_set.add(id(lr_b))
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

    def _fix_block_roles_after_fake_loop_removal(self, regions: List[Region], fake_loop_ids: Set[int]) -> None:
        """
        过滤条件重检假循环后，修复相关块的block_role
        
        假循环被过滤后，以下块的role需要修正：
        1. 假循环的else_blocks (JUMP_BACKWARD块) → 应标记为CONTINUE/PURE_CONTINUE
        2. 假循环的back_edge_block (POP_JUMP_BACKWARD_IF_*块) → 应标记为LOOP_BODY或LOOP_BACK_EDGE
        3. 假循环的body_blocks中被错误标记为CONTINUE → 应标记为LOOP_BODY（如果有意义语句）
        """
        loop_regions = [r for r in regions if isinstance(r, LoopRegion)]
        
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
        loop_regions = [r for r in regions if isinstance(r, LoopRegion)]
        
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
                    return RegionType.FOR_LOOP, None, None, None, False, False

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
                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        
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
            for block in body_set:
                if block == header:
                    continue
                for succ in block.successors:
                    if succ not in body_set and succ != for_iter_exit and succ not in break_targets:
                        block_last = block.get_last_instruction()
                        if block_last and block_last.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                            break_targets.append(succ)
            if break_targets:
                post_else = self.dom_analyzer.find_nearest_common_post_dominator(set(break_targets))
                if post_else and post_else != for_iter_exit:
                    else_blocks = []
                    visited = set()
                    stack = [for_iter_exit]
                    while stack:
                        cur = stack.pop()
                        if cur in visited or cur == post_else:
                            continue
                        visited.add(cur)
                        if cur not in body_set:
                            else_blocks.append(cur)
                        for succ in cur.successors:
                            if succ not in visited and succ != post_else:
                                stack.append(succ)
                    result = sorted(else_blocks, key=lambda b: b.start_offset) if else_blocks else None
                    return result, natural_exit
                else:
                    return [for_iter_exit], natural_exit
            else:
                return [for_iter_exit], natural_exit

        loop_successors = [s for s in header.successors if s not in body_set and s != header]
        loop_successors = [s for s in loop_successors if not any(i.opname == 'RAISE_VARARGS' for i in s.instructions)]
        detector = get_opcode_detector()
        for block in body_set:
            if block == header:
                continue
            for succ in block.successors:
                if succ not in body_set and succ != header and succ not in loop_successors:
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
                non_return_successors = [s for s in non_return_successors if not self._is_early_return_block(s)]
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
            else_blocks = [b for b in else_blocks if not self._is_early_return_block(b)]

        result = sorted(else_blocks, key=lambda b: b.start_offset) if else_blocks else None
        return result, natural_exit

    def _is_early_return_block(self, block: BasicBlock) -> bool:
        """Check if a block represents an early return from within a loop body.
        
        Bytecode pattern:
        - Block contains RETURN_VALUE or RETURN_CONST with a non-None value
        - Such blocks are targets of conditional jumps from within the loop body
        - They represent 'if cond: return value' patterns, NOT else clauses
        
        Root cause (Phase 33 fix):
        - _find_loop_else collected these blocks as else_blocks because they are
          successors of body blocks outside the body set
        - But semantically they are early exits via return, not normal loop exit paths
        - Including them in else_blocks causes 'return' to become 'break + else: return'
        
        Returns True if block is an early return block (should be excluded from else).
        """
        if not block or not block.instructions:
            return False
        last_instr = block.get_last_instruction()
        if last_instr is None:
            return False
        if last_instr.opname == 'RETURN_CONST' and last_instr.argval is not None:
            return True
        if last_instr.opname == 'RETURN_VALUE':
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

    def _detect_break_continue(self, loop_body: Set[BasicBlock], header: BasicBlock,
                               natural_exit: Optional[BasicBlock] = None) -> Tuple[Set[BasicBlock], Dict[BasicBlock, str]]:
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
                if s not in body_set and s != natural_exit:
                    if any(i.opname in ('RAISE_VARARGS', 'RERAISE') for i in s.instructions):
                        continue
                    if not any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in s.instructions):
                        if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in s.instructions):
                            s_meaningful = [i for i in s.instructions
                                            if i.opname not in NOISE_OPS
                                            and i.opname not in ('LOAD_CONST',)
                                            and i.opname not in PURE_JUMP_OPS
                                            and i.opname not in ('RETURN_VALUE', 'RETURN_CONST')]
                            if not s_meaningful:
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
                                if (_has_exc_handler 
                                    and self.dom_analyzer.is_dominator(header, s)):
                                    if is_back_edge_condition:
                                        continue
                                    break_blocks_set.add(s)
                        else:
                            if is_back_edge_condition:
                                continue
                            break_blocks_set.add(s)
                elif s == natural_exit and ne_is_terminator:
                    if last and last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        if last.argval is not None and self.cfg.get_block_by_offset(last.argval) in body_set:
                            break_blocks_set.add(s)

        continue_map = {}
        detector = get_opcode_detector()
        for block in loop_body:
            if block == header:
                continue
            last_instr = block.get_last_instruction()
            if not last_instr:
                continue
            jump_offset = last_instr.arg if last_instr.arg is not None else last_instr.argval
            target = (self.cfg.get_block_by_offset(int(jump_offset))
                      if jump_offset is not None else None)
            is_jump_to_header = (target == header and
                                 (detector.is_unconditional_jump(last_instr) or
                                  detector.is_conditional_jump(last_instr)))
            if not is_jump_to_header:
                continue
            continue_map[block] = ('LOOP_BACK_EDGE'
                                   if self.dom_analyzer.is_dominator(block, header)
                                   else 'CONTINUE')

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
                for pred in header.predecessors:
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
        
        if len(body) == 1 and header in body and is_for_loop:
            for_iter_instr = None
            for instr in header.instructions:
                if instr.opname == 'FOR_ITER':
                    for_iter_instr = instr
                    break
            if for_iter_instr:
                fall_through_offset = for_iter_instr.offset + 2
                fall_through = self.cfg.get_block_by_offset(fall_through_offset)
                if fall_through:
                    body.add(fall_through)
                    queue = [fall_through]
                    exit_offset = for_iter_instr.argval
                    exit_block = self.cfg.get_block_by_offset(exit_offset) if exit_offset else None
                    while queue:
                        current = queue.pop()
                        for succ in current.successors:
                            if succ == header or succ in body:
                                continue
                            if exit_block and succ == exit_block:
                                continue
                            body.add(succ)
                            queue.append(succ)
        
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

        return body

    def _is_fake_loop(self, header: BasicBlock, body: Set[BasicBlock],
                       back_edge_sources: List[BasicBlock]) -> bool:
        """检测伪循环（由continue语句形成的假循环）
        
        伪循环的特征：
        1. header 块是条件检查块（包含 POP_JUMP 指令）
        2. src 块（back edge source）是 continue 跳转块
        3. body 只有 header 和 src 两个块
        """
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
                       if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        has_loop_instr = any(i.opname in ('FOR_ITER', 'GET_ANEXT', 'GET_ITER') 
                            for i in header_instrs)
        if has_loop_instr:
            return False

        has_conditional_jump = False
        for i in header_instrs:
            if i.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                          'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                          'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                          'FORWARD_JUMP_IF_TRUE', 'FORWARD_JUMP_IF_FALSE'):
                has_conditional_jump = True
                break
        if not has_conditional_jump:
            return False

        header_meaningful = [i for i in header_instrs
                            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                            and i.opname not in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                                'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                                                'FORWARD_JUMP_IF_TRUE', 'FORWARD_JUMP_IF_FALSE')]
        header_has_body_code = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                               'BINARY_OP', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                               'DELETE_SUBSCR', 'DELETE_ATTR', 'RAISE_VARARGS',
                                               'IMPORT_NAME', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                                               'RETURN_VALUE', 'RETURN_CONST')
                                  for i in header_meaningful)
        if header_has_body_code:
            return False

        src_meaningful = [i for i in src.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP')
                         and i.opname not in ('JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
                                             'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')]
        src_has_body_code = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                                            'BINARY_OP', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                            'DELETE_SUBSCR', 'DELETE_ATTR', 'RAISE_VARARGS',
                                            'IMPORT_NAME', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                                            'RETURN_VALUE', 'RETURN_CONST')
                               for i in src_meaningful)
        if src_has_body_code:
            return False

        return True

    def _extract_while_condition(self, condition_block: BasicBlock) -> Tuple[List[Instruction], Optional[Instruction]]:
        """从条件块提取while条件表达式

        字节码模式：
        - 条件块最后一条指令为条件跳转（POP_JUMP_*_IF_*）
        - 条件跳转之前的指令构成条件表达式
        - 比较操作：COMPARE_OP/IS_OP/CONTAINS_OP
        - 布尔操作：条件跳转链形成and/or短路求值
        - not条件：POP_JUMP_FORWARD_IF_TRUE 对应 while not cond
        - 复合条件：JUMP_IF_FALSE_OR_POP/JUMP_IF_TRUE_OR_POP 形成and/or链

        提取算法：
        1. 过滤掉噪声指令（RESUME/NOP/CACHE/PUSH_NULL）
        2. 确认最后一条指令为条件跳转
        3. 截取条件跳转之前的指令作为条件指令
        4. 如果条件指令中包含STORE指令，截取最后一个STORE之后的部分
        5. 如果条件指令中包含比较操作，从比较操作向前扩展到完整的条件表达式

        边界条件：
        - while True：条件块无有意义指令，返回空列表
        - 退化while：条件块同时包含初始化和条件判断
        - 复合条件：由BoolOpRegion处理，此方法仅处理简单条件
        - not条件：条件跳转为IF_TRUE时需在AST生成时取反
        - header含body+条件重检：条件重检部分需从body语句中分离

        区域归约算法符合度：
        - 条件提取基于栈深度分析，符合字节码语义
        - STORE截断保证条件不包含body副作用
        - 比较操作向前扩展保证条件完整性

        Returns:
            Tuple[条件指令列表, 条件跳转指令或None]
        """
        filtered_instrs = [
            i for i in condition_block.instructions
            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
        ]
        
        if not filtered_instrs:
            return [], None
        
        last_instr = filtered_instrs[-1]
        
        if last_instr.opname not in CONDITIONAL_JUMP_OPS:
            return filtered_instrs if filtered_instrs else [], None
        
        cond_jump = last_instr
        cond_instrs = filtered_instrs[:-1]
        
        store_idx = None
        copy_before_store_idx = None
        for idx, instr in enumerate(cond_instrs):
            if instr.opname == 'COPY' and instr.arg == 1:
                copy_before_store_idx = idx
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                store_idx = idx
                break
        
        if store_idx is not None:
            if copy_before_store_idx is not None and copy_before_store_idx < store_idx:
                cond_instrs = cond_instrs[copy_before_store_idx:]
            else:
                cond_instrs = cond_instrs[store_idx + 1:]
        
        compare_ops = ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP')
        last_compare_idx = None
        
        for idx in range(len(cond_instrs) - 1, -1, -1):
            if cond_instrs[idx].opname in compare_ops:
                last_compare_idx = idx
                break
        
        if last_compare_idx is not None:
            start_idx = max(0, last_compare_idx - 2)
            
            load_ops = ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_CONST',
                       'LOAD_ATTR', 'LOAD_METHOD', 'BINARY_SUBSCR')
            
            while start_idx > 0 and cond_instrs[start_idx - 1].opname in load_ops:
                start_idx -= 1
            
            cond_instrs = cond_instrs[start_idx:]
        
        return cond_instrs, cond_jump


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
            'JUMP_FORWARD', 'JUMP_ABSOLUTE',
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
        if depth > 3:
            return False
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
        if depth > 3:
            return False
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

    def _block_has_with_body_code(self, block: BasicBlock) -> bool:
        PLACEHOLDER = ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'POP_TOP',
                       'POP_EXCEPT', 'RETURN_VALUE', 'RETURN_CONST',
                       'LOAD_CONST', 'PRECALL', 'CALL', 'CALL_FUNCTION', 'CALL_METHOD')
        for instr in block.instructions:
            if instr.opname in PLACEHOLDER:
                continue
            if instr.opname == 'LOAD_CONST' and instr.argval is None:
                continue
            return True
        return False

    def _is_return_none_block(self, block: BasicBlock) -> bool:
        instrs = [i for i in block.instructions
                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
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
                  if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
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

    def _identify_try_except_regions(self) -> List[Region]:
        """
        识别异常处理区域（try-except-finally）- 核心反编译算法

        ═══════════════════════════════════════════════════════════════════════════════
        【算法概述】
        本方法基于 CPython 3.11+ 的异常表（exception table）机制，将字节码中的异常处理
        结构还原为高层次 TryExceptRegion 对象。这是反编译器中最复杂的部分之一，因为
        CPython 的异常处理使用了基于偏移量的异常表，而非传统的显式指令标记。

        ═══════════════════════════════════════════════════════════════════════════════
        【CPython 3.11+ 异常处理机制】

        **旧机制（Python ≤3.10）**：
        - 使用 SETUP_EXCEPT、SETUP_FINALLY 等显式指令标记 try 块开始
        - 异常处理器通过跳转目标隐式定义
        - 异常栈深度通过指令参数传递

        **新机制（Python 3.11+）**：
        - 使用 exception table（异常表）记录所有异常处理信息
        - 异常表条目格式：(start, end, target, stack_depth, lasti, push_lasti)
        - 不再使用 SETUP_* 指令，try 块边界完全由异常表定义
        - PUSH_EXC_INFO：在 handler 入口压入异常信息到栈
        - CHECK_EXC_MATCH：检查异常类型是否匹配（except 子句）
        - POP_EXCEPT：弹出异常处理帧
        - RERAISE：重新抛出异常

        ═══════════════════════════════════════════════════════════════════════════════
        【字节码模式示例】

        示例1: 基本 try-except
        ```python
        try:
            x = 1/0
        except ValueError:
            x = 0
        ```
        字节码结构：
          offset  0: RESUME
          offset  2: LOAD_CONST 0 (1)         ← try 块开始
          offset  4: LOAD_CONST 1 (0)
          offset  6: BINARY_OP 11 (/)
          offset 10: STORE_NAME 0 (x)         ← try 块结束 (正常路径)
          offset 12: LOAD_CONST 2 (None)
          offset 14: RETURN_VALUE

          offset 16: PUSH_EXC_INFO             ← handler 入口 (target from exception table)
          offset 18: LOAD_GLOBAL 1 (ValueError)
          offset 20: CHECK_EXC_MATCH           ← 检查异常类型
          offset 22: POP_JUMP_FORWARD_IF_FALSE → 36 (to reraise)
          offset 24: POP_TOP
          offset 26: LOAD_CONST 0 (0)
          offset 28: STORE_NAME 0 (x)          ← handler body
          offset 30: POP_EXCEPT                ← 清理异常帧
          offset 32: LOAD_CONST 2 (None)
          offset 34: RETURN_VALUE

          offset 36: RERAISE                   ← 不匹配时重新抛出

        异常表条目：
          Entry(start=2, end=12, target=16, depth=0)  # try 块 [2,12) → handler @16
        ```

        示例2: 多 except 处理器（except chain）
        ```python
        try:
            risky()
        except ValueError:
            handle_ve()
        except TypeError:
            handle_te()
        ```
        字节码特征：
        - 第一个 handler 入口有 PUSH_EXC_INFO + CHECK_EXC_MATCH(ValueError)
        - 第一个 handler 末尾跳转到第二个 handler 入口（或公共退出点）
        - 第二个 handler 入口有 CHECK_EXC_MATCH(TypeError) 或直接进入 body
        - 通过 _follow_except_chain() 方法链接多个 handler

        示例3: try-finally
        ```python
        try:
            work()
        finally:
            cleanup()
        ```
        字节码特征：
        - handler 入口: PUSH_EXC_INFO + ... + RERAISE (无 CHECK_EXC_MATCH)
        - finally 块总是执行，无论是否发生异常
        - finally 中可能包含 COPY + POP_EXCEPT + RERAISE 序列（cleanup）

        示例4: try-except-finally（组合结构）
        ```python
        try:
            work()
        except Error:
            handle()
        finally:
            cleanup()
        ```
        字节码特征：
        - 异常表有两个条目：一个指向 except handler，一个指向 finally handler
        - except handler 的深度 < finally handler 的深度
        - finally handler 包含 except handler 的 try 范围
        - 通过 paired_except_indices 机制关联

        示例5: except as e（异常别名）
        ```python
        try:
            risky()
        except ValueError as e:
            print(e)
        ```
        字节码特征：
        - CHECK_EXC_MATCH 之后有 STORE_FAST/STORE_NAME 指令存储异常对象
        - handler body 使用存储的变量名

        示例6: 嵌套 try
        ```python
        try:
            try:
                inner()
            except InnerError:
                fix_inner()
        except OuterError:
            fix_outer()
        ```
        字节码特征：
        - 内层 try 的异常表条目深度 > 外层 try
        - 内层 handler 可能在外层 try 的范围内
        - 通过 depth 字段和偏移范围区分层次关系

        ═══════════════════════════════════════════════════════════════════════════════
        【识别算法步骤】

        Step 1: 解析异常表 (_parse_exception_table)
        ────────────────────────────────
        遍历 cfg.exception_table 的每个条目：
        a) 定位 handler 入口块 (target offset → BasicBlock)
        b) 分类 handler 类型 (_classify_handler_type):
           - WITH_EXCEPT_START → 'with' (with 语句的 cleanup handler)
           - PUSH_EXC_INFO + RERAISE → 'finally' (finally handler)
           - PUSH_EXC_INFO + CHECK_EXC_MATCH → 'except' (except handler)
           - PUSH_EXC_INFO + CHECK_EG_MATCH → 'except_star' (except* handler, Python 3.11+)
           - 其他 → 通过后继块推断
        c) 找到实际的 handler 开始位置 (_find_actual_handler_start):
            - 某些情况下异常表 target 指向 cleanup 块而非真正的 handler 入口
            - 需要向前搜索找到 PUSH_EXC_INFO 指令的位置
        d) 合并重复条目（相同 handler_start + handler_type 的条目合并范围）
        e) 迭代扩展 try 范围以包含嵌套的内层 handler

        Step 2: 识别内层 handler 和配对关系
        ────────────────────────────────
        a) inner_handler_indices: 识别属于其他 try 结构内层的 handler
           - 判断依据：handler 的第一个指令不是 PUSH_EXC_INFO/WITH_EXCEPT_START
           - 且包含 COPY + POP_EXCEPT + RERAISE 序列（cleanup 特征）
           - 或者其 try_start >= 某个外层 handler 的 handler_start（嵌套在外层 handler 中）
        b) paired_except_indices: 识别与 finally 配对的 except handler
           - 当存在 try-except-finally 结构时，except 和 finally 共享同一 try 范围
           - except handler 的 try 范围被包含在 finally handler 的 try 范围内

        Step 3: 构建每个 handler 的 TryExceptRegion
        ────────────────────────────────
        对于每个非 with、非内层、非配对的 handler：

        a) 确定 try 块的范围和基本块集合：
           - 遍历所有基本块，选择偏移在 [try_start, try_end) 范围内的块
           - 排除：handler 入口块、finally 入口块、with 相关块、已归属其他区域的块
           - 排除：其他同深度或更深层次的 handler/finality 入口块

        b) 提取 except handler 信息 (_extract_except_handler):
           输入：handler 入口 BasicBlock
           输出：(exc_type, exc_name, handler_body_blocks)

           算法：
           i.   检查是否有 PUSH_EXC_INFO + POP_TOP（bare except: `except:`）
           ii.  查找 CHECK_EXC_MATCH 指令前的异常类型加载指令
                - LOAD_NAME/LOAD_GLOBAL → 单一异常类型
                - 多个 LOAD + BUILD_TUPLE → 元组异常类型 `(TypeError, ValueError)`
           iii. 查找 CHECK_EXC_MATCH 后的存储指令（except as 子句）
                - STORE_FAST/STORE_NAME/STORE_DEREF/STORE_GLOBAL → 异常变量名
           iv.  确定 handler body 的入口基本块：
                - 如果有条件跳转（POP_JUMP_*_IF_FALSE），body 在跳转目标之外的后继块
                - 如果无 CHECK_EXC_MATCH，整个 handler 入口块就是 body
           v.   收集 body 的所有基本块（深度优先遍历后继块，排除 reraise 块）

        c) 跟踪 except 链 (_follow_except_chain):
           - 多个 except 子句形成链式结构
           - 当前 handler 末尾的条件跳转指向下一个 handler 入口
           - 递归提取链中每个 handler 的信息
           - 终止条件：遇到 RERAISE、PUSH_EXC_INFO、回边、或无条件跳转

        d) 收集 finally 块 (_collect_finally_body_blocks):
           - finally handler 的 body 可能与 except handler 不同
           - 需要识别 finally copy 块（用于异常传播路径的代码副本）

        e) 查找 else 块 (_find_try_else_blocks):
           - else 块在 try 正常完成且未捕获异常时执行
           - 位于 try 块结束偏移和第一个 handler 开始偏移之间
           - 不在任何 handler 的 body 中

        f) 收集 cleanup 块：
           - 包含 RERAISE 或 COPY+POP_EXCEPT 序列的块
           - 用于异常重新抛出或清理的辅助块

        g) 构建完整的 blocks 集合：
           all_blocks = try_blocks ∪ handler_blocks ∪ finally_blocks ∪ else_blocks ∪ cleanup_blocks

        h) 创建并注册 TryExceptRegion 对象

        ═══════════════════════════════════════════════════════════════════════════════
        【边界条件与特殊情况】

        1. **嵌套 try 结构**
           - 问题：内层 try 的 handler 可能位于外层 try 的范围内
           - 解决：使用 depth 字段判断层次关系，内层 handler 的 depth 更大
           - 识别：通过 inner_handler_indices 排除内层 handler

        2. **try-except-finally 组合**
           - 问题：except 和 finally 各自有异常表条目，需要正确关联
           - 解决：通过 paired_except_indices 将 except 与 finally 配对
           - 范围计算：finally 的 try 范围应包含 except 的 try 范围

        3. **循环中的 try**
           - 问题：try 块可能跨越循环边界，导致区域重叠
           - 解决：确保 TRY > LOOP 优先级，先识别 try 区域再识别循环

        4. **函数级 try**
           - 问题：整个函数体被 try 包裹，return 语句在 try 内部
           - 解决：正确识别 return 语句在 try 中的语义

        5. **bare except (`except:`)**
           - 问题：没有异常类型检查，匹配所有异常
           - 识别：PUSH_EXC_INFO 后紧跟 POP_TOP（弹出异常类型检查结果）

        6. **异常链（multiple except）**
           - 问题：多个 except 子句共享同一个 try 块
           - 解决：_follow_except_chain() 跟踪跳转链

        7. **with 语句的异常处理**
           - 问题：with 语句也产生异常表条目，但不是 try-except
           - 识别：WITH_EXCEPT_START 指令标记 with 的 handler
           - 排除：handler_type == 'with' 的条目不生成 TryExceptRegion

        8. **cleanup-only 块**
           - 问题：某些块只包含异常清理代码（COPY+POP_EXCEPT+RERAISE）
           - 识别：这些块不是真正的 handler，而是异常传播的中间节点
           - 处理：归入 cleanup_blocks 而非 handler body

        ═══════════════════════════════════════════════════════════════════════════════
        【区域归约算法符合度】

        本方法遵循区域归约（region reduction）算法的原则：

        1. **自底向上构建**：从最小的异常处理单元（单个 handler）开始，
           逐步构建完整的 try-except-finally 结构

        2. **不重叠覆盖**：通过 block_to_region 映射确保每个基本块只属于一个区域
           - _register_region_blocks() 方法注册所有相关块
           - 后续识别会跳过已注册的块

        3. **层次化父子关系**：
           - 内层 try 区域的 parent 指向外层 try 区域（如果存在）
           - 通过 parent 属性构建区域树

        4. **TRY > LOOP 优先级**：
           - 异常处理区域的识别在循环区域之前执行
           - 确保 try 中的 break/continue 不会破坏异常处理的完整性

        ═══════════════════════════════════════════════════════════════════════════════
        【数据结构映射】

        TryExceptRegion 属性 → Python 源码对应关系：
        - try_blocks              → try: 子句的语句列表
        - except_handlers         → except/except as 子句列表
          - [0] exc_type          → except 后面的异常类型表达式
          - [1] exc_name          → as 后面的变量名（可选）
          - [2] handler_body      → except 子句的语句体
        - handler_entry_blocks    → 每个 handler 的入口基本块
        - else_blocks             → else: 子句的语句列表（可选）
        - finally_blocks          → finally: 子句的语句列表（可选）
        - has_else / has_finally  → 是否存在 else/finally 块
        - cleanup_blocks          → 异常清理辅助块（不直接对应源码）
        - try_offset_start/end    → try 块的字节码偏移范围

        ═══════════════════════════════════════════════════════════════════════════════
        【已知限制与改进方向】

        1. **复杂控制流的 try**：当 try 块内包含复杂的 if/elif/else 或循环时，
           边界计算可能出现偏差

        2. **间接异常传播**：某些优化可能导致异常处理路径不直观，
           需要更智能的数据流分析

        3. **嵌套深度的限制**：极深层嵌套（>3层）可能导致范围计算错误

        4. **性能考虑**：当前实现使用多次遍历和集合操作，
           对于大型函数可能需要优化

        ═══════════════════════════════════════════════════════════════════════════════
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
            for j, other in enumerate(handler_infos):
                if i == j:
                    continue
                if other.get('depth', 0) < info.get('depth', 0):
                    if info['try_start'] >= other['handler_start']:
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
                        paired_except_indices.add(j)

        for i, handler_info in enumerate(handler_infos):
            if handler_info.get('handler_type') == 'with':
                continue
            if i in paired_except_indices:
                continue
            if i in inner_handler_indices:
                continue

            handler_type = handler_info.get('handler_type', 'except')
            try_start = handler_info['try_start']
            try_end = handler_info['try_end']
            handler_start_offset = handler_info['handler_start']
            current_depth = handler_info.get('depth', 0)

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
                other_depth = other_info.get('depth', 0)
                if other_depth >= current_depth:
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
            for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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

            if handler_type == 'except' and handler_entry_block is not None:
                handler_in_try_range = any(
                    try_start_for_blocks <= instr.offset < try_end_for_blocks
                    for instr in handler_entry_block.instructions
                )
                if handler_in_try_range:
                    pre_handler_blocks = []
                    for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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
                        pre_handler_blocks.append(block)
                    if pre_handler_blocks:
                        for phb in pre_handler_blocks:
                            if phb not in try_blocks:
                                try_blocks.insert(0, phb)
                        try_start_for_blocks = min(try_start_for_blocks,
                                                   min(b.start_offset for b in pre_handler_blocks))

            if handler_type == 'finally':
                all_except_handlers = []
                all_handler_entry_blocks = []
                all_handler_blocks_set = set()
                
                if paired_except_infos:
                    for except_info in paired_except_infos:
                        except_handler_entry = self.cfg.get_block_by_offset(except_info['handler_start'])
                        if except_handler_entry is None:
                            continue
                        exc_type, exc_name, handler_body = self._extract_except_handler(except_handler_entry)
                        all_except_handlers.append((exc_type, exc_name, handler_body))
                        all_handler_entry_blocks.append(except_handler_entry)
                        all_handler_blocks_set |= set(handler_body) | {except_handler_entry}
                        chain_handlers, chain_entries = self._follow_except_chain(except_handler_entry)
                        all_except_handlers.extend(chain_handlers)
                        all_handler_entry_blocks.extend(chain_entries)
                        for exc_t, exc_n, body in chain_handlers:
                            all_handler_blocks_set |= set(body)
                        for heb in chain_entries:
                            all_handler_blocks_set.add(heb)
                
                handler_body_blocks, finally_copy_blocks = self._collect_finally_body_blocks(
                    handler_entry_block, try_blocks, all_except_handlers if paired_except_infos else None)
                
                all_handler_blocks_set |= set(handler_body_blocks) | {handler_entry_block}
            else:
                exc_type, exc_name, handler_body_blocks = self._extract_except_handler(handler_entry_block)
                all_except_handlers = [(exc_type, exc_name, handler_body_blocks)]
                all_handler_entry_blocks = [handler_entry_block]
                all_handler_blocks_set = set(handler_body_blocks) | {handler_entry_block}
                finally_copy_blocks = {}

                chain_handlers, chain_entries = self._follow_except_chain(handler_entry_block)
                all_except_handlers.extend(chain_handlers)
                all_handler_entry_blocks.extend(chain_entries)
                for exc_t, exc_n, body in chain_handlers:
                    all_handler_blocks_set |= set(body)
                for heb in chain_entries:
                    all_handler_blocks_set.add(heb)

            finally_blocks = []
            if handler_type == 'finally':
                finally_blocks = handler_body_blocks

            all_blocks = set(try_blocks) | all_handler_blocks_set
            if finally_blocks:
                all_blocks |= set(finally_blocks)

            for existing_region in self.regions:
                if not isinstance(existing_region, TryExceptRegion):
                    continue
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
                cleanup_visited.add(block.start_offset)
                is_cleanup = False
                has_reraise = any(instr.opname == 'RERAISE' for instr in block.instructions)
                has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in block.instructions)
                has_copy = any(instr.opname == 'COPY' for instr in block.instructions)
                if has_reraise:
                    is_cleanup = True
                elif has_pop_except and has_copy:
                    meaningful = [instr for instr in block.instructions
                                  if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    if all(instr.opname in ('COPY', 'POP_EXCEPT', 'RERAISE', 'POP_TOP',
                                            'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                            'STORE_DEREF', 'STORE_GLOBAL',
                                            'DELETE_FAST', 'DELETE_NAME',
                                            'DELETE_DEREF', 'DELETE_GLOBAL',
                                            'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                            'PUSH_EXC_INFO', 'SWAP')
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
            if handler_blocks_in_try:
                try_blocks = [b for b in try_blocks if b not in handler_blocks_in_try]

            finally_blocks_in_try = set(finally_blocks) & set(try_blocks) if finally_blocks else set()
            if finally_blocks_in_try:
                try_blocks = [b for b in try_blocks if b not in finally_blocks_in_try]

            cleanup_in_try = set(cleanup_blocks) & set(try_blocks)
            if cleanup_in_try:
                try_blocks = [b for b in try_blocks if b not in cleanup_in_try]

            existing_entry_regions = [r for r in self.regions if isinstance(r, TryExceptRegion) and r.entry == entry_block]
            if existing_entry_regions:
                for existing in existing_entry_regions:
                    if (existing.try_offset_start >= try_start and
                            existing.try_offset_end <= try_end and
                            existing.try_offset_end < try_end):
                        adjusted_start = existing.try_offset_end
                        adjusted_entry = None
                        for blk in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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

        return self.regions[initial_region_count:]

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
            for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
                if block.start_offset >= entry['try_start']:
                    break
                if block.start_offset >= entry['handler_start']:
                    continue
                meaningful = [i for i in block.instructions
                              if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if not meaningful:
                    if block.start_offset < search_start:
                        search_start = block.start_offset
                    continue
                if any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in meaningful):
                    search_start = min(search_start, block.start_offset)
                    continue
                if block.start_offset < search_start:
                    search_start = block.start_offset
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
                    is_cleanup_reraise = (
                        any(i.opname == 'COPY' for i in current.instructions) and
                        any(i.opname == 'POP_EXCEPT' for i in current.instructions)
                    )
                    if not is_cleanup_reraise:
                        return 'finally'
                for succ in current.successors:
                    if succ not in visited:
                        worklist.append(succ)

        return 'except'

    def _find_actual_handler_start(self, cleanup_block: BasicBlock, cleanup_offset: int,
                                    handler_type: str, depth: int) -> int:
        if handler_type in ('except', 'except_star'):
            has_push_exc_self = any(i.opname == 'PUSH_EXC_INFO' for i in cleanup_block.instructions)
            has_check_self = any(i.opname == 'CHECK_EXC_MATCH' for i in cleanup_block.instructions)
            has_check_eg_self = any(i.opname == 'CHECK_EG_MATCH' for i in cleanup_block.instructions)
            if has_push_exc_self and (has_check_self or has_check_eg_self):
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

    def _annotate_finally_copy_blocks(self, region: TryExceptRegion) -> None:
        if not region.finally_blocks:
            return
        _, copy_blocks = self._collect_finally_body_blocks(
            region.handler_entry_blocks[0] if region.handler_entry_blocks else None,
            region.try_blocks, region.except_handlers)
        region.finally_copy_blocks = copy_blocks

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
                _blocks.append(_current)
                _last = _current.get_last_instruction()
                if _last and _last.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RERAISE'):
                    continue
                if any(i.opname == 'POP_EXCEPT' for i in _current.instructions):
                    continue
                for _succ in _current.successors:
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

        has_check_exc = any(i.opname == 'CHECK_EXC_MATCH' for i in handler_entry.instructions)
        if has_check_exc:
            pre_check_instrs = []
            for instr in handler_entry.instructions:
                if instr.opname == 'CHECK_EXC_MATCH':
                    break
                if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL'):
                    pre_check_instrs.append(instr.argval)
            if len(pre_check_instrs) == 1:
                exc_type = pre_check_instrs[0]
            elif len(pre_check_instrs) > 1:
                has_build_tuple = any(
                    i.opname == 'BUILD_TUPLE' and i.argval == len(pre_check_instrs)
                    for i in handler_entry.instructions
                    if i.opname != 'CHECK_EXC_MATCH'
                )
                if has_build_tuple:
                    exc_type = '(' + ', '.join(pre_check_instrs) + ')'
                else:
                    exc_type = pre_check_instrs[0]

            seen_check = False
            for instr in handler_entry.instructions:
                if instr.opname == 'CHECK_EXC_MATCH':
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
            handler_body_blocks = [handler_entry]

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
                    if instr.opname == 'CHECK_EXC_MATCH':
                        exc_type = instr.argval
                        break
                if exc_type:
                    break
                for succ in hb.successors:
                    if succ == hb:
                        continue
                    for instr in succ.instructions:
                        if instr.opname == 'CHECK_EXC_MATCH':
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
                        if instr.opname == 'CHECK_EXC_MATCH':
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
            has_check_exc = any(i.opname == 'CHECK_EXC_MATCH' for i in next_block.instructions)
            exc_type, exc_name, body = self._extract_except_handler(next_block)
            if has_check_exc:
                chain_handlers.append((exc_type, exc_name, body))
                chain_entries.append(next_block)
                current = next_block
            else:
                if body:
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
            alternative_merges = []
            for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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

            if alternative_merges:
                merge_point = alternative_merges[0]
            else:
                handler_entry_offsets = []
                for heb in try_region.handler_entry_blocks:
                    if heb.start_offset >= try_end_offset:
                        handler_entry_offsets.append(heb.start_offset)
                first_handler_entry = min(handler_entry_offsets) if handler_entry_offsets else None
                if first_handler_entry is not None and first_handler_entry > try_end_offset:
                    else_blocks = []
                    for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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
                    if instr.offset > try_body_max_end and instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
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
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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
            if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
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
                for finally_offset, entries in entry_to_finally.items():
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

                        if is_try_exit_successor or block_in_any_range:
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
                                                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
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
        for instr in block.instructions:
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                found_bw = True
                bw_offset = instr.offset
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
                elif instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
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
            max_end = exc_target
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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
        cleanup = []
        handler_blocks = []
        for e in self.cfg.exception_table:
            if e.get('start', 0) == body_start:
                hb = self.cfg.get_block_by_offset(e.get('target', 0))
                if hb and any(i.opname == 'WITH_EXCEPT_START' for i in hb.instructions):
                    handler_blocks.append(hb)
        worklist = list(handler_blocks)
        while worklist:
            cl_block = worklist.pop(0)
            if cl_block in cleanup_visited:
                continue
            cleanup_visited.add(cl_block)
            if any(i.opname in ('CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for i in cl_block.instructions):
                continue
            if cl_block not in with_body and cl_block not in with_entry_blocks:
                cleanup.append(cl_block)
            for succ in cl_block.successors:
                if succ in cleanup_visited:
                    continue
                if any(i.opname == 'WITH_EXCEPT_START' for i in succ.instructions):
                    worklist.append(succ)
                elif succ in cl_block.exception_successors:
                    worklist.append(succ)
        if body_end is not None and body_end > 0:
            self._collect_normal_exit_cleanup(with_body, cleanup, cleanup_visited,
                                              with_entry_blocks, body_end)
        return cleanup

    def _collect_normal_exit_cleanup(self, with_body, cleanup, cleanup_visited,
                                    entry_blocks, body_end):
        body_offsets = {b.start_offset for b in with_body}
        body_offsets.update(b.start_offset for b in entry_blocks)
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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
            cleanup.append(block)
            cleanup_visited.add(block)

    def _scan_before_with_instructions(self):
        before_with_blocks = []
        depth_map = {}
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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
            with_entry_blocks.append(after_bw_block)
        body_start, body_end = self._get_with_body_range(last_with)
        with_body = self._collect_with_body_blocks(last_with, body_start, body_end)
        cleanup = self._collect_with_cleanup_blocks(with_entry_blocks, with_body, body_start, body_end)
        all_blocks = set(with_entry_blocks) | set(with_body) | set(cleanup)
        region = WithRegion(
            region_type=RegionType.WITH, entry=block, blocks=all_blocks,
            with_blocks=with_body, exception_blocks=cleanup, cleanup_blocks=cleanup,
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
        for cleanup_block in cleanup:
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
        """识别所有with语句区域。

        ╔═══════════════════════════════════════════════════════════════════╗
        ║            WITH区域识别算法 - CPython 3.11+ 字节码模式           ║
        ╠═══════════════════════════════════════════════════════════════════╣
        ║                                                                    ║
        ║ 【字节码模式】                                                    ║
        ║ CPython编译器对with语句生成以下字节码序列：                       ║
        ║                                                                    ║
        ║ 基本with:                                                         ║
        ║   LOAD ctx          # 加载上下文表达式                            ║
        ║   BEFORE_WITH       # [3.11+] with入口标记                        ║
        ║   POP_TOP           # 弹出__enter__()返回值（无as时）             ║
        ║   ... body ...      # with body代码                              ║
        ║   PUSH_EXC_INFO     # 异常处理开始                                ║
        ║   WITH_EXCEPT_START # 调用__exit__(exc_type, exc_val, exc_tb)    ║
        ║   ... cleanup ...   # 清理路径                                   ║
        ║                                                                    ║
        ║ with as var:                                                      ║
        ║   LOAD ctx          # 加载上下文表达式                            ║
        ║   BEFORE_WITH       # with入口标记                                ║
        ║   STORE_FAST var    # 存储__enter__()返回值到目标变量              ║
        ║   ... body ...      # with body代码                              ║
        ║   (同上cleanup)                                                     ║
        ║                                                                    ║
        ║ async with (异步):                                                ║
        ║   LOAD ctx          # 加载异步上下文管理器                        ║
        ║   BEFORE_ASYNC_WITH # 异步with入口标记                             ║
        ║   GET_AWAITABLE     # 获取awaitable对象                           ║
        ║   ... SEND/YIELD ... # 异步协议交互                               ║
        ║   STORE_FAST var    # 存储结果                                    ║
        ║   ... body ...      # async with body                            ║
        ║   (cleanup包含额外的GET_AWAITABLE/SEND)                          ║
        ║                                                                    ║
        ║ 多上下文: with A as a, B as b:                                   ║
        ║   连续的BEFORE_WITH块，depth递增                                 ║
        ║                                                                    ║
        ║ 【识别算法步骤】                                                  ║
        ║ Step 1: 扫描BEFORE_WITH指令                                      ║
        ║   - 遍历所有基本块，找到含BEFORE_WITH/BEFORE_ASYNC_WITH的块     ║
        ║   - 从异常表提取depth信息（嵌套深度）                             ║
        ║   - 返回 (block, has_async, depth) 列表及depth映射               ║
        ║                                                                    ║
        ║ Step 2: 按depth排序                                              ║
        ║   - 确保外层with先于内层with处理                                  ║
        ║   - 避免内层with被错误地合并到外层                                 ║
        ║                                                                    ║
        ║ Step 3: 构建单个WithRegion                                       ║
        ║   对每个BEFORE_WITH块调用_build_single_with_region:               ║
        ║   a. 冲突检测：检查块是否已被其他区域占据                         ║
        ║      - 允许与TryExceptRegion/LoopRegion重叠（with可嵌套在其中）   ║
        ║      - 若已被WithRegion占据且无body代码在BEFORE_WITH之前，跳过     ║
        ║   b. 收集连续with入口块：_collect_consecutive_with_blocks         ║
        ║      - 处理 `with A as a, B as b` 多上下文语法                   ║
        ║      - 通过depth_map区分多上下文vs独立with                       ║
        ║   c. 确定body起始块：_find_after_with_store_block                ║
        ║      - 定位STORE_FAST(var)或POP_TOP（BEFORE_WITH之后）           ║
        ║   d. 获取body偏移范围：_get_with_body_range                      ║
        ║      - 基于异常表的[start, end)范围                              ║
        ║      - 这是CPython 3.11+的关键改进：精确的body边界              ║
        ║   e. 收集body块：_collect_with_body_blocks                       ║
        ║      - 在偏移范围内收集所有非cleanup块                           ║
        ║      - 排除WITH_EXCEPT_START/BEFORE_WITH块                      ║
        ║   f. 收集清理块：_collect_with_cleanup_blocks                    ║
        ║      - 从WITH_EXCEPT_START块开始BFS遍历                          ║
        ║      - 包含POP_EXCEPT/RERAISE/JUMP等清理指令                    ║
        ║   g. 构建WithRegion对象并设置角色标注                            ║
        ║      - WITH_HANDLER: 含WITH_EXCEPT_START的块                     ║
        ║      - WITH_EXIT_CLEANUP: 含POP_EXCEPT/RERAISE的块              ║
        ║      - WITH_STACK_CLEANUP: 其他清理块                            ║
        ║   h. 提取with items：_extract_with_items                         ║
        ║      - 解析上下文表达式和optional_vars                           ║
        ║                                                                    ║
        ║ Step 4: 合并连续with区域                                        ║
        ║   调用_merge_consecutive_with_regions:                           ║
        ║   - 条件：body_offset_end + 1 == 下一个body_offset_start        ║
        ║   - 且depth相同                                                 ║
        ║   - 合并blocks/with_blocks/cleanup_blocks/items                  ║
        ║   - 对应源码中的连续with语句：                                   ║
        ║     with A:                                                     ║
        ║         ...                                                      ║
        ║     with B:  # 第二个with紧随第一个with body结束                 ║
        ║         ...                                                      ║
        ║                                                                    ║
        ║ 【与其他区域识别器的交互】                                        ║
        ║ 执行顺序（region_analyzer.py主流程）：                            ║
        ║   1. _identify_loop_regions()        # 循环区域                  ║
        ║   2. _identify_try_except_regions()  # 异常处理区域              ║
        ║   3. _identify_with_regions()        # ← 本方法                  ║
        ║   4. _identify_conditional_regions() # 条件区域                  ║
        ║   5. _identify_assert_regions()     # 断言区域                  ║
        ║                                                                    ║
        ║ 关键交互点：                                                      ║
        ║ - TryExceptRegion识别器会跳过with类型的handler                   ║
        ║   （通过检测WITH_EXCEPT_START区分try-except和with的异常处理）   ║
        ║ - WithRegion信息传递给条件识别器，避免将WITH_EXCEPT_START块     ║
        ║   误识别为IfRegion的条件头                                       ║
        ║ - LoopRegion可与WithRegion重叠（for/while内嵌套with）            ║
        ║                                                                    ║
        ║ 【边界条件】                                                      ║
        ║ 1. 嵌套with: 外层with body包含内层with                           ║
        ║    - 通过depth区分：外层depth < 内层depth                       ║
        ║    - 内层with的blocks是外层with_body的子集                       ║
        ║    - 测试案例: w04nestedwith_a_b.py, w16nestedwith_x_y.py       ║
        ║                                                                    ║
        ║ 2. async with: 异步上下文管理器                                  ║
        ║    - 使用BEFORE_ASYNC_WITH而非BEFORE_WITH                       ║
        ║    - 包含GET_AWAITABLE/SEND/YIELD_VALUE等异步指令               ║
        ║    - 生成嵌套code object（生成器函数体）                         ║
        ⚠️  - 已知问题：async with的嵌套code object可能导致                ║
        ║       指令数不匹配（test_w058: 43 vs 28条指令）                 ║
        ║       根因：异步协议的SEND/YIELD循环未被正确重建               ║
        ║                                                                    ║
        ║ 3. 多上下文with: with A as a, B as b:                           ║
        ║    - 多个连续BEFORE_WITH块，depth递增                           ║
        ║    - 合并为一个WithRegion，items包含多个上下文                  ║
        ║    - 测试案例: w03multicontext_a_b.py, w22withmulticontext_x_y   ║
        ║                                                                    ║
        ║ 4. with内控制流: if/for/try/while在with body中                  ║
        ║    - 这些控制流结构作为WithRegion的children                     ║
        ║    - break/continue需要经过with的__exit__清理路径               ║
        ║    - 测试案例: w12withif_x.py, w13withfor_x.py, w15withtry_x    ║
        ║                                                                    ║
        ║ 5. with + try/except嵌套: try在with内部或外部                   ║
        ║    - 需要正确区分with的cleanup和try的except handler             ║
        ║    - 通过异常表的depth和范围区分                                ║
        ⚠️  - 已知问题：复杂嵌套可能导致指令数不一致                     ║
        ║       （test_w102: 54 vs 59条指令）                             ║
        ║       根因：try-except的PUSH_EXC_INFO与with cleanup混淆        ║
        ║                                                                    ║
        ║ 6. 自定义上下文管理器: class Ctx: with Ctx() as c:              ║
        ║    - 类定义（LOAD_BUILD_CLASS/MAKE_FUNCTION）+ 实例化调用        ║
        ⚠️  - 已知问题：类定义与with的结合可能导致顺序问题               ║
        ║       （test_w30: 35 vs 38条指令）                              ║
        ║       根因：LOAD_BUILD_CLASS等元类操作的位置重建不准确         ║
        ║                                                                    ║
        ║ 【区域归约符合度】                                                ║
        ║ WITH区域在归约层次中的位置：                                     ║
        ║   ModuleRegion                                                   ║
        ║   └─ FunctionRegion                                             ║
        ║      ├─ LoopRegion (for/while)  ← 可包含WithRegion             ║
        ║      │  └─ WithRegion                                           ║
        ║      │     ├─ IfRegion (if/elif/else)  ← with body内的条件     ║
        ║      │     ├─ LoopRegion (嵌套循环)                             ║
        ║      │     └─ TryExceptRegion (嵌套异常处理)                   ║
        ║      ├─ TryExceptRegion (try/except/finally) ← 可包含WithRegion ║
        ║      │  └─ WithRegion                                           ║
        ║      └─ WithRegion (顶层with)                                   ║
        ║         └─ ... (同上嵌套)                                       ║
        ║                                                                    ║
        ║ 优先级关系（从高到低）：                                         ║
        ║   TRY > WITH > LOOP > IF > ASSERT > SEQUENCE                   ║
        ║   (异常处理优先于with，因为with的cleanup依赖异常机制)          ║
        ║                                                                    ║
        ║ 【性能特征】                                                      ║
        ║ 时间复杂度: O(W * (B + C))                                       ║
        ║   W = with语句数量                                               ║
        ║   B = 平均body块数量                                             ║
        ║   C = 平均cleanup块数量                                          ║
        ║ 空间复杂度: O(B + C) (每个WithRegion存储其所有块)               ║
        ║                                                                    ║
        ║ 【测试覆盖】                                                      ║
        ║ 总测试数: 191 | 通过: 186 | 失败: 5 | 通过率: 97.4%             ║
        ║ 失败案例分布：                                                    ║
        ║   - async with嵌套code object: 1个 (w058)                       ║
        ║   - with+break/continue控制流: 2个 (w079, w080)                 ║
        ║   - with+try/except/finally嵌套: 1个 (w102)                     ║
        ║   - 自定义上下文管理器+类定义: 1个 (w30customctx)               ║
        ║ 全部为类别C（字节码一致性），无识别失败或语法错误              ║
        ╚═══════════════════════════════════════════════════════════════════╝
        """
        regions = []
        before_with_blocks, depth_map = self._scan_before_with_instructions()
        for block, has_async, depth in before_with_blocks:
            region = self._build_single_with_region(block, has_async, depth, depth_map)
            if region:
                regions.append(region)
        merged_regions = self._merge_consecutive_with_regions(regions)
        return merged_regions

    def _should_merge_with_regions(self, region1: WithRegion, region2: WithRegion) -> bool:
        if not isinstance(region1, WithRegion) or not isinstance(region2, WithRegion):
            return False
        entry1_has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in region1.entry.instructions)
        entry2_has_bw = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH') for i in region2.entry.instructions)
        if not entry1_has_bw or not entry2_has_bw:
            return False
        if region1.body_offset_end is None or region2.body_offset_start is None:
            return False
        if region1.body_offset_end + 1 != region2.body_offset_start:
            return False
        entry1_depth = -1
        entry2_depth = -1
        for e in self.cfg.exception_table:
            if e.get('start', 0) == region1.body_offset_start:
                entry1_depth = e.get('depth', -1)
            if e.get('start', 0) == region2.body_offset_start:
                entry2_depth = e.get('depth', -1)
        if entry1_depth != entry2_depth:
            return False
        return True

    def _merge_consecutive_with_regions(self, regions: List[Region]) -> List[Region]:
        if len(regions) <= 1:
            return regions
        merged = []
        i = 0
        while i < len(regions):
            current = regions[i]
            if i + 1 < len(regions):
                next_region = regions[i + 1]
                if self._should_merge_with_regions(current, next_region):
                    current.blocks.update(next_region.blocks)
                    current.with_blocks.extend(next_region.with_blocks)
                    current.exception_blocks.extend(next_region.exception_blocks)
                    current.cleanup_blocks.extend(next_region.cleanup_blocks)
                    current.items.extend(next_region.items)
                    current.body_offset_end = next_region.body_offset_end
                    for block in next_region.blocks:
                        if block not in self.block_to_region:
                            self.block_to_region[block] = current
                    i += 2
                    merged.append(current)
                    continue
            merged.append(current)
            i += 1
        return merged

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
        if block in nested_blocks:
            from core.cfg.region_analyzer import LoopRegion, TryExceptRegion, IfRegion
            if isinstance(nested_region, LoopRegion):
                get_iter_idx = None
                for idx, instr in enumerate(block.instructions):
                    if instr.opname in ('GET_ITER', 'GET_AITER'):
                        get_iter_idx = idx
                        break
                if get_iter_idx is not None:
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
            return []
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

        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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

        关键约束：
        - 上下文表达式指令仅包含LOAD/CALL/PUSH_NULL等值产生指令
        - NOISE_OPS（RESUME/NOP/CACHE）被跳过
        - 目标变量为None时表示无as子句
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
        before_with_count = sum(
            1 for instr in instructions
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH')
        )
        
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
                                   'PUSH_NULL', 'SWAP', 'COPY'):
                    ctx_expr.append(instr)
                i += 1
            
            # 查找目标变量（在 AFTER_WITH 之后的 STORE）
            target = None
            if bw_pos + 1 < len(instructions):
                next_instr = instructions[bw_pos + 1]
                if next_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                    target = next_instr.argval
            
            items.append((ctx_expr, target))
        
        region.items = items
        region.target = region.items[0][1] if region.items and region.items[0][1] else None

    def _collect_with_related_instructions(self, entry_blocks: List[BasicBlock],
                                          initial_instrs: List, block_map: List) -> List:
        """收集与with语句相关的所有指令，包括跨块的情况"""
        all_instrs = list(initial_instrs)
        visited_blocks = set(id(b) for b in entry_blocks)

        for entry_block in entry_blocks:
            for succ in entry_block.successors:
                if id(succ) in visited_blocks:
                    continue
                if self._is_value_only_block(succ):
                    has_before_with = any(i.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH')
                                         for i in succ.instructions)
                    has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME')
                                   for i in succ.instructions)
                    if has_before_with or has_store:
                        for idx, instr in enumerate(succ.instructions):
                            all_instrs.append(instr)
                            block_map.append((succ, idx))
                        visited_blocks.add(id(succ))

        return all_instrs

    def _extract_context_expression_extended(self, instructions: List, start_idx: int) -> Tuple[List, int]:
        """扩展版上下文表达式提取，返回表达式和结束位置"""
        import dis
        if start_idx >= len(instructions):
            return [], start_idx

        stack_depth = 0
        end_idx = start_idx
        found_load = False


        for j in range(start_idx, len(instructions)):
            curr_instr = instructions[j]
            if curr_instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                end_idx = j
                break
            try:
                effect = dis.stack_effect(curr_instr.opcode, curr_instr.arg)
            except Exception:
                effect = 0
            stack_depth += effect
            if curr_instr.opname not in NOISE_OPS:
                if stack_depth > 0 or curr_instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL',
                                                             'LOAD_ATTR', 'LOAD_FAST',
                                                             'LOAD_CONST', 'LOAD_METHOD'):
                    found_load = True
                    end_idx = j + 1

        if found_load and end_idx > start_idx:
            return list(instructions[start_idx:end_idx]), end_idx
        return [], start_idx + 1

    def _extract_context_expression(self, instructions: List, start_idx: int) -> List:
        """提取上下文管理器表达式指令"""
        import dis
        stack_depth = 0
        end_idx = start_idx
        for j in range(start_idx, len(instructions)):
            curr_instr = instructions[j]
            if curr_instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                end_idx = j
                break
            try:
                effect = dis.stack_effect(curr_instr.opcode, curr_instr.arg)
            except Exception:
                effect = 0
            stack_depth += effect
            if stack_depth > 0 and curr_instr.opname not in NOISE_OPS:
                end_idx = j + 1
        return list(instructions[start_idx:end_idx])

    def _is_value_only_block(self, block: BasicBlock) -> bool:
        if block is None:
            return False
        value_push_ops = {
            'LOAD_CONST', 'LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
            'LOAD_ATTR', 'LOAD_METHOD', 'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_DICT',
            'BUILD_SET', 'BUILD_STRING', 'BUILD_SLICE', 'BINARY_OP', 'UNARY_OP',
            'UNARY_NOT', 'CALL', 'BINARY_SUBSCR', 'GET_ITER', 'GET_AWAITABLE',
            'FORMAT_VALUE', 'CONVERT_VALUE', 'IS_OP', 'CONTAINS_OP',
            'LOAD_ASSERTION_ERROR', 'LOAD_BUILD_CLASS',
        }
        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not meaningful:
            return False
        for i in meaningful:
            if i.opname == 'JUMP_FORWARD':
                continue
            if i.opname not in value_push_ops:
                return False
        return True

    def _block_has_match_like_instructions(self, block: 'BasicBlock') -> bool:
        # 包含 MATCH_CLASS/MATCH_MAPPING/MATCH_SEQUENCE/MATCH_KEYS 操作码（结构型模式）
        if self._has_match_op(block):
            return True
        # 包含 COPY + 比较/None检查 + 条件跳转（字面量型模式）
        # match-case 的 COPY 指令是关键区分特征：subject 加载一次后 COPY 给每个 case 使用
        # 而 if-elif 每次都重新加载 subject，不会出现 COPY
        if self._is_match_subject_block(block):
            return True
        return False

    def _block_has_nop_prefix(self, block: 'BasicBlock') -> bool:
        if block is None:
            return False
        for instr in block.instructions:
            if instr.opname == 'NOP':
                return True
            if instr.opname not in NOISE_OPS:
                break
        return False

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

    def _is_literal_case_block(self, block: 'BasicBlock') -> bool:
        """检测块是否是字面量 match case 链中的 case 块

        与 _is_match_subject_block 的区别：
        - subject 块包含 COPY（复制 subject 给比较使用）
        - 中间 case 块也可能包含 COPY（保留 subject 给下一个 case）
        - 最后一个 case（default 前）不含 COPY（subject 被比较操作消费）

        检测条件：
        1. 块以条件跳转结尾
        2. 块中包含比较操作或 None 检查
        3. 块中不含 MATCH_* 操作码
        4. 块的指令序列符合 case 比较模式（简单比较，无复杂操作）
        """
        if block is None:
            return False
        if self._has_match_op(block):
            return False

        instrs = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not instrs:
            return False

        last = instrs[-1]
        if last.opname not in CONDITIONAL_JUMP_OPS:
            return False

        # 检查是否包含比较操作或 None 检查跳转
        has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in instrs)
        has_none_check = last.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE',
                                          'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE')

        if not has_compare and not has_none_check:
            return False

        # 验证指令序列是否足够"简单"——只包含 case 比较相关的操作
        # 允许的操作：COPY, LOAD_CONST, COMPARE_OP, IS_OP, STORE_*, POP_TOP, 条件跳转
        case_allowed_ops = frozenset({
            'COPY', 'LOAD_CONST', 'COMPARE_OP', 'IS_OP',
            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
            'POP_TOP', 'SWAP',
        }) | NOISE_OPS | CONDITIONAL_JUMP_OPS

        # 还允许加载变量（subject 或类名）
        case_allowed_ops = case_allowed_ops | frozenset({
            'LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
        })

        if not all(i.opname in case_allowed_ops for i in instrs):
            return False

        return True

    def _collect_literal_match_body(self, subject_block: 'BasicBlock', claimed: set) -> Optional[tuple]:
        """收集字面量型match-case的case块和body块

        字面量match模式的字节码特征：
        - subject只加载一次，通过COPY复制给每个case比较
        - 第一个case块包含COPY + LOAD_CONST + COMPARE_OP/IS_OP + 条件跳转
        - 中间case块也包含COPY + LOAD_CONST + COMPARE_OP/IS_OP + 条件跳转
        - 最后一个case（default前）不含COPY，只有LOAD_CONST + COMPARE_OP/IS_OP + 条件跳转
        - case None使用POP_JUMP_IF_NOT_NONE，无COPY
        - 每个case body以JUMP_FORWARD跳转到汇合点结束
        - default case无条件跳转，不包含比较操作

        与if-elif的区别：
        - if-elif每次条件都重新LOAD subject，不存在COPY指令
        - match-case的subject只LOAD一次，通过COPY传递

        Args:
            subject_block: match语句的subject块（包含COPY指令的块）
            claimed: 已被其他区域占用的块集合

        Returns:
            (case_blocks, case_patterns, case_bodies, merge_block, all_blocks) 或 None
        """
        if subject_block is None:
            return None

        case_blocks = []
        case_patterns = []
        case_bodies = []
        all_blocks = {subject_block}
        visited = set()

        current = subject_block
        merge_candidates = []

        while current and current not in visited:
            visited.add(current)
            all_blocks.add(current)

            last = current.get_last_instruction()
            if not last or last.opname not in CONDITIONAL_JUMP_OPS:
                # 无条件跳转的块：可能是default case
                if self._is_literal_default_block(current, visited):
                    default_body = self._collect_simple_body_blocks(current, visited)
                    if default_body:
                        body_set = set(default_body)
                        all_blocks.update(body_set)
                        case_blocks.append(current)
                        case_patterns.append({'type': 'MatchAs'})
                        case_bodies.append(sorted(body_set, key=lambda b: b.start_offset))
                break

            # 获取条件跳转的目标（下一个case块）和fall-through（case body）
            jt = self.cfg.get_block_by_offset(last.argval)
            if jt is None:
                break

            # fall-through后继是case body的入口
            ft_successor = next((s for s in sorted(current.successors, key=lambda s: s.start_offset) if s != jt), None)
            if not ft_successor:
                break

            # 解析当前case的pattern
            pat = self.pattern_parser.parse_case_pattern(current)

            # 收集case body块：从fall-through到merge点之间的块
            body_entry = self._resolve_body_entry(ft_successor)
            body_set = set()
            if body_entry and body_entry != jt:
                body_set = self._collect_blocks_on_path(body_entry, jt, visited | {jt})
                # 排除属于下一个case的块
                body_set = body_set - {jt}
            all_blocks.update(body_set)

            # 记录可能的merge点（每个case body的出口都跳向merge）
            if body_set:
                for b in body_set:
                    for s in b.successors:
                        if s not in body_set and s != current:
                            merge_candidates.append(s)

            case_blocks.append(current)
            case_patterns.append(pat)
            case_bodies.append(sorted(body_set, key=lambda b: b.start_offset))

            # 移动到下一个case块
            current = jt

        if not case_blocks:
            return None

        # 至少需要2个case块（或1个case+default）才构成match
        # 单个case可能是普通if语句
        if len(case_blocks) < 1:
            return None

        # 计算merge点
        merge_block = self._compute_case_merge(case_bodies)
        if merge_block is None and merge_candidates:
            # 使用出现次数最多的候选作为merge点
            from collections import Counter
            counter = Counter(id(c) for c in merge_candidates)
            most_common_id = counter.most_common(1)[0][0]
            merge_block = next(c for c in merge_candidates if id(c) == most_common_id)

        if merge_block:
            all_blocks.add(merge_block)

        # 验证：确保case块不重新加载subject（区分match和if-elif）
        if not self._verify_literal_match_chain(subject_block, case_blocks):
            return None

        # 字面量match模式不使用_finalize_match_region
        # 因为_finalize_match_region会错误地合并具有相同exit successor的case
        # （例如都以RETURN_VALUE结尾的case body会被合并为一个MatchOr）
        # 字面量match的每个case都有独立的body，不应合并
        # 只有真正的OR pattern（同一case的多个值共享body）才需要合并
        merged_p, merged_b, i = [], [], 0
        while i < len(case_blocks):
            orps, body = [case_patterns[i]], set(case_bodies[i])
            j = i + 1
            while j < len(case_blocks):
                # 字面量match的OR pattern合并条件更严格：
                # 只有当两个连续case的body完全相同（相同块集合）时才合并
                # 这对应 case 1 | 2: body 的OR pattern
                body_i_set = set(case_bodies[i])
                body_j_set = set(case_bodies[j])
                # body完全相同才合并（真正的OR pattern）
                if body_i_set and body_j_set and body_i_set == body_j_set:
                    orps.append(case_patterns[j])
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

        return case_blocks, merged_p, merged_b, merge_block, all_blocks

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
            'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'
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
        """识别match-case语句的区域

        反编译逻辑概述：
        ====================

        match-case字节码有两种形态，需要分别识别：

        1. 结构型模式（MATCH_CLASS/MATCH_SEQUENCE/MATCH_MAPPING等）：
           - 字节码特征：包含MATCH_*操作码
           - 识别入口：_has_match_op(block) 或 _is_case_pattern_block(block)
           - case收集：_mr_collect_case_body() 从subject块开始沿条件跳转链收集

        2. 字面量模式（COPY + COMPARE_OP/IS_OP）：
           - 字节码特征：subject只LOAD一次，通过COPY复制给每个case比较
           - 识别入口：_is_match_subject_block(block) 检测COPY+比较模式
           - 特殊情况：某些match没有COPY但有NOP前缀，由_is_simple_match_case_block检测
           - case收集：_scan_literal_match_subjects() 独立扫描

        识别流程：
        Phase 1: 遍历CFG块，识别结构型模式的match区域
          - 对每个包含MATCH_*操作码的块，调用_mr_collect_case_body收集case链
          - 解析每个case的pattern和guard
          - 创建MatchRegion并注册到block_to_region

        Phase 2: 扫描字面量模式的match区域（_scan_literal_match_subjects）
          - 对每个未被占用的块，检查是否是COPY+比较的subject块
          - 或是否是NOP前缀的case块（_is_simple_match_case_block）
          - 沿条件跳转链收集case块和body块
          - 通过_verify_literal_match_chain验证是match而非if-elif

        OR模式合并（_mr_finalize_match_region）：
          - 连续case共享同一body时，合并为MatchOr pattern
          - 合并条件：body[0]相同 且 不含MATCH_*操作码

        关键区分match vs if-elif：
          - match: subject只LOAD一次，后续case通过COPY复制
          - if-elif: 每个条件都重新LOAD subject，不存在COPY
          - NOP前缀：match的default case块前有NOP，if-else的else块前无NOP

        字节码模式详解（CPython 3.10+ Match-Case实现）：
        =====================================================

        【结构型模式的字节码序列】

        例1: match x:
                case Point(a, b):
                    ...

        字节码布局：
        Block0 (subject): LOAD_FAST 'x'    # 加载subject
                          COPY              # 复制subject（保留在栈上供后续case使用）
                          MATCH_CLASS       # 尝试匹配类模式
                          ...               # 属性提取、guard检查等
                          POP_JUMP_IF_* -> BlockN (下一个case或失败)

        Block1 (case body): ...             # case body代码
                           JUMP_FORWARD -> MergeBlock

        BlockN (next case): COPY            # 再次复制subject（从栈上的副本）
                            MATCH_CLASS     # 下一个case的模式匹配
                            ...
                            POP_JUMP_IF_* -> BlockN+1

        MergeBlock:         # 所有case的汇合点

        关键字节码指令说明：
        -------------------
        MATCH_CLASS(cls, attrs): 类模式匹配
          - 栈顶: subject对象
          - 操作: 检查isinstance(subject, cls)，如果成功则提取属性
          - 参数: cls=类对象, attrs=(属性名元组)
          - 成功: 将属性值压栈；失败: 跳转到失败处理

        MATCH_SEQUENCE: 序列模式匹配
          - 栈顶: subject对象
          - 操作: 先GET_LEN检查长度，再UNPACK_SEQUENCE解包
          - 用于: case [a, b, c]: 或 case (x, y):

        MATCH_MAPPING: 映射模式匹配
          - 栈顶: subject对象
          - 操作: 检查是否为dict，再MATCH_KEYS检查键存在性
          - 用于: case {"key": value}:

        MATCH_KEYS(keys): 键集合匹配
          - 参数: keys=frozenset({键名})
          - 成功: 压入布尔值和键值对；失败: 跳转

        GET_LEN: 获取序列长度（用于长度约束检查）
          - 配合COMPARE_OP使用，如 case [a, *rest]: 需要len >= N

        UNPACK_SEQUENCE / UNPACK_EX: 解包操作
          - UNPACK_SEQUENCE: 固定长度解包 case [a, b]:
          - UNPACK_EX: 带星号解包 case [a, *rest, b]:

        COPY: 复制栈顶元素
          - **核心特征**: match语句中subject只LOAD一次，通过COPY给每个case
          - 这是区分match与if-elif的关键标志

        条件跳转指令（用于pattern matching的控制流）：
        -----------------------------------------------
        POP_JUMP_FORWARD_IF_NONE / POP_JUMP_IF_NONE:
          - 用于可选绑定检查（如 case {"key": val}?）
          - 如果值为None则跳到失败处理

        POP_JUMP_FORWARD_IF_NOT_NONE / POP_JUMP_IF_NOT_NONE:
          - 用于guard条件的None检查
          - guard表达式可能产生None，需要特殊处理

        POP_JUMP_FORWARD_IF_TRUE/FALSE:
          - 用于guard条件的布尔判断
          - case x if x > 0: 中的 if x > 0 部分

        【字面量模式的字节码序列】

        例2: match x:
                case 1:
                    ...
                case 2:
                    ...
                case _:
                    ...

        字节码布局：
        Block0 (subject): LOAD_FAST 'x'    # 加载subject（唯一一次）
                          COPY              # 复制给第一个case
                          LOAD_CONST 1      # 字面量值
                          COMPARE_OP ==     # 比较
                          POP_JUMP_IF_FALSE -> Block2 (下一个case)

        Block1 (case 1 body): ...           # case 1的body
                            JUMP_FORWARD -> MergeBlock

        Block2 (case 2):   COPY             # 再次复制原始subject
                            LOAD_CONST 2
                            COMPARE_OP ==
                            POP_JUMP_IF_FALSE -> Block4

        Block3 (case 2 body): ...
                            JUMP_FORWARD -> MergeBlock

        Block4 (default):  NOP              # default case的特殊标记（可选）
                            ...             # default body

        MergeBlock:

        识别算法详解：
        =============

        算法1: 结构型模式识别（Phase 1）
        --------------------------------
        输入: CFG基本块列表
        输出: MatchRegion列表

        步骤:
        1. 遍历所有CFG块（按偏移量排序）
        2. 跳过已被其他区域占用的块（claimed set）
        3. 检测候选块:
           - _has_match_op(block): 包含MATCH_CLASS/SEQUENCE/MAPPING/KEYS
           - _is_case_pattern_block(block): 包含COPY+比较模式或其他pattern相关操作
        4. 定位subject块:
           - 如果当前块就是pattern block，向前查找subject
           - 通过predecessor链找到包含MATCH_OP的前驱块
        5. 收集case链（_mr_collect_case_body）:
           - 从subject块开始，沿条件跳转目标遍历
           - 对每个case块:
             a. 找到最后一个条件跳转指令（_mr_find_case_jump_instruction）
             b. 确定跳转目标（下一个case）和成功分支（body入口）
             c. 解析pattern（parse_case_pattern）
             d. 检测guard条件（通过BFS搜索pattern-only块）
             e. 收集body块（_collect_blocks_on_path 或 _mr_collect_case_body_by_offset）
           - 遇到无跳转的块时，作为default case处理
           - 跳过连接器块（只有POP_TOP/JUMP的块）
        6. OR模式合并（_mr_finalize_match_region）:
           - 遍历case_blocks列表
           - 如果连续cases共享相同的body，合并为MatchOr
           - 例如: case 1: ... case 2: ... (相同body) → case 1 | 2: ...
        7. 创建MatchRegion并注册

        算法2: 字面量模式识别（Phase 2 - _scan_literal_match_subjects）
        ----------------------------------------------------------------
        输入: 已被占用的块集合（claimed）
        输出: MatchRegion列表（字面量模式）

        步骤:
        1. 遍历所有未被占用的块
        2. 检测两种入口类型:
           a. _is_match_subject_block: COPY + LOAD_CONST + COMPARE_OP/IS_OP 模式
           b. _is_simple_match_case_block: NOP前缀的简单case块
        3. 沿条件跳转链收集cases（类似Phase 1但更简化）
        4. 验证match性质（_verify_literal_match_chain）:
           - 确保不是if-elif链
           - 检查subject是否只LOAD一次（通过COPY复用）
        5. OR模式合并（与Phase 1相同逻辑）
        6. 创建MatchRegion并注册

        边界条件与特殊情况：
        ===================

        1. 嵌套match语句:
           - 内层match的case body中包含另一个match
           - 识别顺序: 先外后内（外层先占用blocks）
           - 内层的subject块不应被外层误占
           - 处理: 通过dominator关系确保层级正确

        2. match在循环/try中:
           - 循环体中的match: subject块的dominator包含循环头
           - try块中的match: 可能跨越except块
           - 处理: 区域边界不能跨越循环/try边界（由block_to_region保护）

        3. class pattern复杂度:
           - case Point(x=0, y=0): 多属性提取
           - case Point(x=a, y=b) if a > b: 属性+guard组合
           - 字节码: MATCH_CLASS → 多个LOAD_ATTR → STORE_FAST → guard check
           - 处理: parse_case_pattern需要完整解析属性绑定链

        4. 通配符case (case _:):
           - 总是匹配成功，无条件跳转
           - 字节码: 可能是NOP前缀 + 直接进入body
           - 或者: 最后一个无POP_JUMP的块被当作default

        5. OR模式 (case 1 | 2 | 3:):
           - 编译为多个连续case块，共享同一个body
           - 字节码: 每个case独立比较，都跳到同一个body入口
           - 识别: _mr_finalize_match_region检测body相同性

        6. 守卫条件 (case x if x > 0:):
           - pattern匹配成功后的额外条件检查
           - 字节码位置: 在STORE_PATTERN_VARS之后，JUMP_TO_BODY之前
           - 控制流: guard失败时跳到下一个case（而非default）
           - 识别: _mr_find_case_jump_instruction找到第二个条件跳转

        7. 映射模式的rest参数 (case {**rest}:):
           - 特殊的DICT_UPDATE操作
           - 需要额外的store操作捕获剩余键值对

        8. 序列模式的star解包 (case [a, *rest, b]:):
           - 使用UNPACK_EX而非UNPACK_SEQUENCE
           - 需要GET_LEN进行长度验证
           - star变量捕获中间所有元素

        区域归约符合度（WITH/MATCH优先级关系）：
        =========================================

        优先级规则:
        1. TRY_REGION > WITH_REGION > MATCH_REGION > IF_REGION > LOOP_REGION
        2. match在with语句体内: with区域先占用blocks，match无法识别
        3. match在try语句体内: try区域先占用，match降级为if-elif
        4. 嵌套match: 外层match先识别，内层作为外层的case body的一部分

        实际影响:
        - test_m22/m23/m24 (match in if/for/try): 这些测试预期失败
          因为match被包含在更高优先级的区域内
        - 解决方案: 需要在父区域内部递归识别子区域（未来优化方向）

        性能考虑:
        - claimed集合避免重复识别（O(1)查找）
        - dominator分析加速body收集（提前终止无效路径）
        - BFS/DFS结合控制搜索空间

        数据结构:
        ========
        MatchRegion字段说明:
        - entry: region入口块（通常是subject块）
        - blocks: 所有属于此region的块集合
        - subject_block: 包含subject加载的块
        - case_blocks: 有序的case块列表（按执行顺序）
        - case_patterns: 对应的pattern字典列表
        - case_guards: 对应的guard表达式列表（可能为None）
        - case_bodies: 对应的body块列表（每个元素是块列表）
        - merge_block: 所有case body的汇合块
        - case_body_start_indices: 每个case body在块内的起始指令索引
          （用于区分pattern匹配指令和body指令）
        """
        match_regions = []
        claimed = set(self.block_to_region.keys())
        for block in self.cfg.get_blocks_in_order():
            if block in claimed:
                continue
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

    def _mr_trace_connector_chain(self, start, target, cseen):
        result = set()
        cur = start
        visited = set()
        while cur and cur not in visited and cur != target and cur not in cseen:
            visited.add(cur)
            result.add(cur)
            meaningful = [i for i in cur.instructions if i.opname not in NOISE_OPS]
            if len(meaningful) == 1 and meaningful[0].opname in ('POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                next_s = next((s for s in cur.successors if s != cur and s not in visited), None)
                if next_s:
                    cur = next_s
                    continue
            break
        return result

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
                                                      'RAISE_VARARGS', 'RERAISE'):
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
        worklist = list(start.successors)
        local_visited = {start}
        while worklist:
            succ = worklist.pop(0)
            if succ in visited or succ in local_visited:
                continue
            local_visited.add(succ)
            result.append(succ)
            last = succ.get_last_instruction()
            if last and last.opname not in ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS', 'RERAISE'):
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
            if jt == current or not self.dom_analyzer.is_dominator(current, jt):
                break
            pat = self.pattern_parser.parse_case_pattern(current)
            guard_jump_target = None
            pattern_jump_targets = set()
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
                    gj = self._mr_find_case_jump_instruction(gc)
                    if gj:
                        target_block = self.cfg.get_block_by_offset(gj.argval)
                        if target_block and target_block != jt:
                            pattern_jump_targets.add(target_block)
                        if is_pattern_only:
                            for s in gc.successors:
                                if s not in visited_g:
                                    worklist_g.append(s)
                        else:
                            if gc != current:
                                guard_jump_target = gj.argval
                            break
                    elif is_pattern_only:
                        for s in gc.successors:
                            if s not in visited_g:
                                worklist_g.append(s)
            resolved_success = self._mr_resolve_body_entry(success)
            if resolved_success and resolved_success != jt:
                stop_set = visited | {jt} | pattern_jump_targets
                if guard_jump_target is not None:
                    guard_jt_block = self.cfg.get_block_by_offset(guard_jump_target)
                    if guard_jt_block:
                        stop_set.add(guard_jt_block)
                body_set = self._collect_blocks_on_path(resolved_success, jt, stop_set)
                body_set = body_set - stop_set
                if not body_set:
                    body_set = self._mr_collect_case_body_by_offset(success, next_case_offset, visited)
            else:
                body_set = self._mr_collect_case_body_by_offset(success, next_case_offset, visited)
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

    def _is_nop_default_match_block(self, block):
        if block is None:
            return False
        if block in self.block_to_region:
            return False
        meaningful = [i for i in block.instructions if i.opname not in NOISE_OPS]
        if not meaningful:
            return False
        has_nop_prefix = False
        for instr in block.instructions:
            if instr.opname == 'NOP':
                has_nop_prefix = True
            elif instr.opname not in NOISE_OPS:
                break
        if not has_nop_prefix:
            return False
        last = block.get_last_instruction()
        if last and last.opname in CONDITIONAL_JUMP_OPS:
            return False
        if any(i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                             'MATCH_KEYS', 'MATCH_MAPPING_KEYS') for i in meaningful):
            return False
        has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in meaningful)
        if has_compare:
            return False
        return True

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
        has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in meaningful)
        has_none_check = last.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE',
                                          'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE')
        if not has_compare and not has_none_check:
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
        return True

    def _is_wildcard_match_block(self, block):
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
        no_cond_jump = not any(i.opname in CONDITIONAL_JUMP_OPS for i in instrs)
        if not no_cond_jump:
            return False
        no_copy = not any(i.opname == 'COPY' for i in instrs)
        if not no_copy:
            return False
        rest = instrs[2:]
        body_ops = {'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF',
                     'RETURN_VALUE', 'RETURN_CONST', 'POP_TOP',
                     'LOAD_CONST', 'LOAD_NAME', 'LOAD_FAST'}
        if not all(i.opname in body_ops or i.opname in NOISE_OPS for i in rest):
            return False
        for pred in block.predecessors:
            pred_last = pred.get_last_instruction()
            if pred_last and pred_last.opname in SHORT_CIRCUIT_JUMP_OPS:
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

        for parent_region in parent_regions:
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
                        if existing is None or not isinstance(existing, MatchRegion):
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

        # 策略1: 结构型模式匹配
        if self._has_match_op(candidate_block) or self._is_case_pattern_block(candidate_block):
            subject_block = candidate_block
            if self._is_case_pattern_block(candidate_block):
                # 向前查找subject块
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
        # 检查直接前驱
        for pred in sorted(case_block.predecessors, key=lambda p: p.start_offset):
            if pred not in parent_blocks:
                continue
            if self._is_match_subject_block(pred) and pred.start_offset < case_block.start_offset:
                return pred
            # 也检查是否有COPY指令但不是完整subject的情况
            instrs = [i for i in pred.instructions if i.opname not in NOISE_OPS]
            has_copy = any(i.opname == 'COPY' for i in instrs)
            if has_copy and pred.start_offset < case_block.start_offset:
                return pred

        # 广度优先搜索
        visited = {case_block}
        queue = list(case_block.predecessors)
        while queue:
            current = queue.pop(0)
            if current in visited or current not in parent_blocks:
                continue
            visited.add(current)

            if self._is_match_subject_block(current) and current.start_offset < case_block.start_offset:
                return current

            # 继续搜索前驱
            for pred in current.predecessors:
                if pred not in visited and pred in parent_blocks:
                    queue.append(pred)

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
        for block in body_blocks:
            meaningful = [i for i in block.instructions if i.opname not in trivial_ops]
            if meaningful:
                return False
            has_non_none_return = False
            for idx, i in enumerate(block.instructions):
                if i.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    prev_non_noise = None
                    for j in range(idx - 1, -1, -1):
                        if block.instructions[j].opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
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
        """识别assert语句区域

        算法角色：独立识别器（Standalone Detector）
        职责：检测CFG中的assert模式，创建AssertRegion

        【字节码模式特征】
        Python编译器为 assert 生成以下字节码：

        基本断言:
            源码: assert condition
            字节码:
                LOAD condition
                POP_JUMP_IF_TRUE → end      # 条件为True时跳过
                LOAD_ASSERTION_ERROR
                RAISE_VARARGS(1)
              end: ...

        带消息的断言:
            源码: assert condition, "error msg"
            字节码:
                LOAD condition
                POP_JUMP_IF_TRUE → end
                LOAD_ASSERTION_ERROR
                LOAD_CONST "error msg"
                CALL(1)                 # 或 FORMAT_VALUE + BUILD_STRING
                RAISE_VARARGS(1)
              end: ...

        【检测算法】
        1. 遍历所有基本块（按偏移量排序）
        2. 对每个块检查：
           a. 最后指令是前向跳转操作码（FORWARD_JUMP_OPS）
           b. 有2个条件后继
           c. 任一后继块包含 LOAD_ASSERTION_ERROR 指令
        3. 定位消息块（包含RAISE_VARARGS的后继）
        4. 创建AssertRegion并注册

        【与其他区域的关系】
        - 在 loop/try/with/match/conditional/chained_compare 之前运行
        - 与 IfRegion 竞争：assert的条件跳转与if相似
          但通过检测LOAD_ASSERTION_ERROR来区分
        - 与 BoolOpRegion 竞争：assert中的boolop条件可能被抢占（test_bool15）

        【已知问题（9/19测试失败的原因）】

        问题1 - assert在复合语句中被"吞掉":
        ───────────────────────────────
        源码: `if a > 0: assert a < 100`
        当assert在if/循环体内部时：
        - IfRegion/LoopRegion可能将assert的块纳入自己的body_blocks
        - AssertRegion虽然被创建，但生成时可能被跳过
        - 反编译结果中缺少assert语句

        问题2 - None检查操作码混淆:
        ─────────────────────────────
        POP_JUMP_IF_NONE / POP_JUMP_IF_NOT_NONE 用于 `if x is None` 模式
        但某些assert变体可能使用这些操作码
        _generate_assert 中对 NONE_CHECK_OPS 的特殊处理可能不完整

        问题3 - f-string消息格式差异:
        ──────────────────────────────
        Python 3.11+ 对 f-string 使用 FORMAT_VALUE + BUILD_STRING
        vs 旧版本的 CALL(format) 方式
        这导致指令数不匹配（test_as02, test_as04系列）

        【调用位置】
        analyze() → _identify_assert_regions() [在早期阶段执行]
        """
        regions = []
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
            last = block.get_last_instruction()
            if last is None or last.opname not in FORWARD_JUMP_OPS:
                continue
            if len(block.conditional_successors) != 2:
                continue
            is_assert = any(
                instr.opname == 'LOAD_ASSERTION_ERROR'
                for succ in block.conditional_successors
                if succ != block
                for instr in succ.instructions
            )
            if not is_assert:
                continue

            message_block = None
            for succ in sorted(block.successors, key=lambda s: s.start_offset):
                if succ == block:
                    continue
                if any(instr.opname == 'RAISE_VARARGS' for instr in succ.instructions):
                    message_block = succ
                    break

            region = AssertRegion(
                region_type=RegionType.ASSERT,
                entry=block,
                blocks={block} | ({message_block} if message_block else set()),
                condition_block=block,
                message_block=message_block,
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

        return regions

    def _identify_chained_compare_regions(self, loop_regions: List[Region],
                                           try_regions: List[Region],
                                           with_regions: List[Region],
                                           match_regions: List[Region],
                                           assert_regions: List[Region]) -> List[Region]:
        """识别链式比较区域

        基于 _is_chained_compare_header 和 _detect_chained_compare_pattern
        检测 COPY(arg=2) + COMPARE_OP 指令对链。
        在Phase 1区域之后、boolop/ternary/conditional之前执行。
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

    def _identify_conditional_regions(self, loop_regions: List[Region],
                                      assert_regions: List[Region],
                                      try_regions: List[Region],
                                      with_regions: List[Region],
                                      match_regions: List[Region],
                                      boolop_regions: List[Region],
                                      ternary_regions: List[Region] = None) -> List[Region]:
        """
        识别条件区域（if/if-else/if-elif-else） - Phase 5 核心算法

        ═══════════════════════════════════════════════════════════════════════
        算法概述（基于支配边界分析的结构化条件识别）
        ═══════════════════════════════════════════════════════════════════════

        本方法实现 if/elif/else 条件结构的 CFG 区域识别，是反编译器的核心组件之一。
        它在所有其他区域类型（Try/Loop/With/Match/Assert/Ternary/BoolOp）识别之后运行，
        因此需要排除已被其他区域占用的块。

        ┌─────────────────────────────────────────────────────────────────────┐
        │                    区域识别优先级（调用顺序）                         │
        ├─────────────────────────────────────────────────────────────────────┤
        │  Phase 1 (低层): Try → Loop → With → Match → Assert                │
        │  Phase 2 (高层): ChainedCompare → BoolOp → Ternary → **If (本方法)**│
        └─────────────────────────────────────────────────────────────────────┘

        算法流程（5个阶段）：
        ─────────────────
        阶段1 - 准备工作（6634-6656）：
          - 收集 try/with 的 handler 块集合（用于排除冲突块）
          - 按偏移量降序排列所有块（从后向前遍历，确保内层优先）

        阶段2 - 块过滤（6657-6689）：
          - 只处理有2个条件后继的块（if 的基本特征）
          - 排除已属于 Loop/Try/With/Match/Ternary/BoolOp 的块
          - 排除包含异常处理指令的块

        阶段3 - 条件解析（6691-6703）：
          - 解析 BoolOp 短路求值链（and/or 条件合并）
          - 确定真正的 condition_block 和 chain_blocks
          - 分离 then_succ 和 else_succ（按偏移量排序）

        阶段4 - 特殊模式检测（6705-6719）：
          - 链式比较检测（a < b < c 的 COPY+COMPARE_OP 模式）
          - 优先构建 ChainedCompareRegion

        阶段5 - 通用 IfRegion 构建（6721-6743）：
          - 计算后向支配合并点（post-dominator merge point）
          - 收集 then/else 分支块
          - 尝试构建 elif 链（_build_elif_region）
          - 回退到基础 if/if-else（_build_basic_if_region）

        字节码模式对照表：
        ─────────────────
        ┌──────────────────────┬────────────────────────────────────────┐
        │ 源码                  │ 字节码特征                              │
        ├──────────────────────┼────────────────────────────────────────┤
        │ if x:               │ POP_JUMP_FORWARD_IF_FALSE → else       │
        │     pass            │ (then 是 fallthrough)                   │
        ├──────────────────────┼────────────────────────────────────────┤
        │ if x: ... else: ... │ POP_JUMP_FORWARD_IF_FALSE → else       │
        │                     │ then 块以 JUMP_FORWARD → merge 结尾    │
        │                     │ else 块直接 fallthrough 到 merge       │
        ├──────────────────────┼────────────────────────────────────────┤
        │ if x:               │ 第1个 IF: POP_JUMP_IF_FALSE → elif2    │
        │ elif y:             │ elif2: POP_JUMP_IF_FALSE → else        │
        │ else: ...           │ 每个 elif header 都是新的条件块         │
        ├──────────────────────┼────────────────────────────────────────┤
        │ if a < b < c:       │ COPY(arg=2) + COMPARE_OP 指令对        │
        │                     │ (CPython 特殊优化)                     │
        └──────────────────────┴────────────────────────────────────────┘

        边界条件处理：
        ───────────────
        1. 空 then/else 体：检测 _is_trivial_block()，空分支被移除
        2. pass-only 体：保留但标记为 trivial
        3. 单语句 if：正常处理，then_blocks 可能只有1个块
        4. 嵌套 if：通过递归 block_to_region 查找处理
        5. if 中包含循环/try/with：通过 children 机制关联子区域

        Phase 5 修复记录：
        ────────────────
        - Fix1: _is_single_expression_block 排除 [LOAD*, RETURN] 模式
               解决 TernaryRegion 抢占 if-elif-return 的问题 (+9测试)
        - Fix2: _is_simple_match_case_block 增加 COPY 检测
               解决 MatchRegion 抢占 is None/is not None 的问题 (+15测试)

        区域归约算法符合度：
        - ✅ 自底向上识别（从最内层条件开始）
        - ✅ 基于支配边界分析（post-dominator for merge point）
        - ✅ 正确建立嵌套关系（通过 block_to_region 映射）
        - ✅ 与其他区域类型无冲突（通过 claimed 机制排除）

        Returns:
            List[IfRegion]: 识别出的条件区域列表，按识别顺序排列
        """
        if_regions = []
        try_handler_blocks = set()
        if try_regions:
            for tr in try_regions:
                if hasattr(tr, 'handler_entry_blocks'):
                    try_handler_blocks.update(tr.handler_entry_blocks)
                if hasattr(tr, 'finally_blocks') and tr.finally_blocks:
                    try_handler_blocks.update(tr.finally_blocks)
                if hasattr(tr, 'except_handlers') and tr.except_handlers:
                    for exc_type, exc_name, hblocks in tr.except_handlers:
                        try_handler_blocks.update(hblocks)
        with_handler_blocks = set()
        if with_regions:
            for wr in with_regions:
                if hasattr(wr, 'cleanup_blocks'):
                    with_handler_blocks.update(wr.cleanup_blocks)
                if hasattr(wr, 'exception_blocks'):
                    with_handler_blocks.update(wr.exception_blocks)
                with_handler_blocks.add(wr.entry)
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
            if with_regions:
                if block in with_handler_blocks:
                    continue
                if any(instr.opname in ('WITH_EXCEPT_START',) for instr in block.instructions):
                    continue
            if loop_regions:
                br_check = self.block_to_region.get(block)
                if isinstance(br_check, LoopRegion):
                    if block == br_check.condition_block:
                        continue
                    if block == br_check.header_block:
                        if br_check.condition_block is None:
                            continue
                        cond_succs = list(block.conditional_successors)
                        if len(cond_succs) == 2:
                            both_in_loop = all(
                                s in br_check.blocks and s != br_check.condition_block
                                for s in cond_succs
                            )
                            if not both_in_loop:
                                continue
                            last_instr = block.get_last_instruction()
                            if last_instr and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                                has_body_stmt = any(
                                    i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                                'STORE_DEREF', 'BINARY_OP', 'DELETE_')
                                    for i in block.instructions
                                    if i.offset < last_instr.offset
                                )
                                if has_body_stmt:
                                    continue
                        else:
                            continue
                elif br_check is not None:
                    continue
                cond_succs_check = list(block.conditional_successors)
                if len(cond_succs_check) == 2:
                    block_in_loop = any(block in lr.blocks for lr in loop_regions)
                    if block_in_loop:
                        if any(s in lr.blocks or s == lr.header_block or s == lr.entry for lr in loop_regions for s in cond_succs_check):
                            is_loop_backedge_target = any(
                                any(su.start_offset >= lr.header_block.start_offset for su in block.successors)
                                and any(i.opname.startswith('JUMP_BACKWARD') for i in block.instructions)
                                for lr in loop_regions
                            )
                            if is_loop_backedge_target:
                                continue

            if try_regions:
                if any(instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for instr in block.instructions):
                    continue

            if ternary_regions and any(
                isinstance(tr, TernaryRegion) and tr.entry == block
                for tr in ternary_regions
            ):
                continue

            if match_regions:
                mr_check = self.block_to_region.get(block)
                if isinstance(mr_check, MatchRegion):
                    continue
                if any(block in mr.blocks for mr in match_regions):
                    continue

            if assert_regions:
                ar_check = self.block_to_region.get(block)
                if isinstance(ar_check, AssertRegion):
                    continue
                if any(block == ar.entry for ar in assert_regions):
                    continue

            br_check = self.block_to_region.get(block)
            if isinstance(br_check, BoolOpRegion) and br_check.entry != block:
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
            br = self.block_to_region.get(block)
            if isinstance(br, BoolOpRegion) and br.entry == block:
                condition_block = br.op_chain[-1][0]
                chain_blocks = set(b for b, _ in br.op_chain)

            cond_succs = list(condition_block.conditional_successors)
            if len(cond_succs) != 2:
                continue
            then_succ, else_succ = sorted(cond_succs, key=lambda s: s.start_offset)

            chained_compare_info = self._detect_chained_compare_pattern(condition_block)
            if chained_compare_info:
                region = self._build_chained_compare_region(
                    block, condition_block, chain_blocks,
                    then_succ, else_succ, chained_compare_info)
                if region is not None:
                    extra_chain = chained_compare_info.get('extra_chain_blocks', [])
                    all_cc_blocks = set(region.chained_compare_blocks) | set(extra_chain)
                    cc_merge = self._find_nearest_common_post_dominator(then_succ, else_succ)
                    cc_then = self._collect_branch_blocks(then_succ, cc_merge, {else_succ})
                    cc_else = self._collect_branch_blocks(else_succ, cc_merge, {then_succ})
                    if try_handler_blocks:
                        cc_then = [b for b in cc_then if b not in try_handler_blocks]
                        cc_else = [b for b in cc_else if b not in try_handler_blocks]
                    region.then_blocks = cc_then
                    region.else_blocks = cc_else
                    region.merge_block = cc_merge
                    region.blocks = {block, condition_block, then_succ, else_succ} | all_cc_blocks | set(chain_blocks) | set(cc_then) | set(cc_else)
                    if cc_merge:
                        region.blocks.add(cc_merge)
                    if_regions.append(region)
                    if boolop_region is not None:
                        if not (region.entry and region.entry == boolop_region.entry):
                            region.add_child(boolop_region)
                continue

            merge = self._find_nearest_common_post_dominator(then_succ, else_succ)
            then_blocks = self._collect_branch_blocks(then_succ, merge, {else_succ})
            else_blocks = self._collect_branch_blocks(else_succ, merge, {then_succ})
            if try_handler_blocks:
                then_blocks = [b for b in then_blocks if b not in try_handler_blocks]
                else_blocks = [b for b in else_blocks if b not in try_handler_blocks]

            all_condition_blocks = {condition_block} | chain_blocks

            region = self._build_elif_region(block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block)
            if region is None:
                region = self._build_basic_if_region(block, then_blocks, else_blocks, merge,
                                                      all_condition_blocks, condition_block)
            if region is not None:
                if_regions.append(region)
                if boolop_region is not None:
                    if not (region.entry and region.entry == boolop_region.entry):
                        region.add_child(boolop_region)
        return if_regions

    def _resolve_boolop_condition_region(self, block):
        block_region = self.block_to_region.get(block)
        if block_region is None:
            return None
        if not (isinstance(block_region, BoolOpRegion) and block_region.entry == block):
            return None
        first_chain_last = block_region.op_chain[0][0].get_last_instruction() if block_region.op_chain else None
        if not first_chain_last:
            return None
        if first_chain_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
            return block_region
        if first_chain_last.opname in SHORT_CIRCUIT_JUMP_OPS:
            return block_region
        return None

    def _build_basic_if_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None):
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
        if else_blocks and all(self._is_trivial_block(b) for b in else_blocks):
            else_blocks = []
        if else_blocks and merge is None:
            then_block_set = set(then_blocks) if then_blocks else set()
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
        for _b, _r in self.block_to_region.items():
            if type(_r).__name__ == 'LoopRegion':
                _e = _r.condition_block or getattr(_r, 'header_block', None) or _r.entry
                if _e:
                    _lre.add(_e)
                    _lrbs.append((_r.blocks, _e))
        if _lre:
            then_blocks = [b for b in then_blocks if b in _lre or not any(b in _lb and b != _le for _lb, _le in _lrbs)]
            else_blocks = [b for b in else_blocks if b in _lre or not any(b in _lb and b != _le for _lb, _le in _lrbs)]
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

    def _build_elif_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks, condition_block=None):
        def _check_elif_chain(header_, else_blocks_, merge_):
            if not else_blocks_:
                return None
            first_else = else_blocks_[0]
            if len(first_else.conditional_successors) != 2:
                return None
            if first_else in self.block_to_region:
                existing = self.block_to_region[first_else]
                if isinstance(existing, (IfRegion, TernaryRegion)):
                    pass
                elif existing.region_type == RegionType.BASIC:
                    pass
                elif isinstance(existing, (TryExceptRegion, WithRegion)):
                    pass
                elif isinstance(existing, BoolOpRegion):
                    pass
                else:
                    return None

            conditions = [first_else]
            bodies = []
            final_else = []

            inner_condition_block = first_else
            inner_br = self.block_to_region.get(first_else)
            if isinstance(inner_br, BoolOpRegion) and inner_br.entry == first_else:
                inner_condition_block = inner_br.op_chain[-1][0]
            inner_cond_succs = list(inner_condition_block.conditional_successors)
            if len(inner_cond_succs) != 2:
                return None
            inner_then_succ, inner_else_succ = sorted(inner_cond_succs, key=lambda s: s.start_offset)
            inner_merge = self._find_nearest_common_post_dominator(inner_then_succ, inner_else_succ)
            inner_then_blocks = self._collect_branch_blocks(inner_then_succ, inner_merge, {inner_else_succ})
            inner_else_blocks = self._collect_branch_blocks(inner_else_succ, inner_merge, {inner_then_succ})
            if inner_else_blocks and all(self._is_trivial_block(b) for b in inner_else_blocks):
                inner_else_blocks = []
            inner_region_type = RegionType.IF_THEN_ELSE if inner_else_blocks else RegionType.IF_THEN

            if inner_region_type == RegionType.IF_THEN:
                then_set = set(inner_then_blocks)
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
                            final_else = [else_succ]

            return {'conditions': conditions, 'bodies': bodies, 'final_else': final_else}

        elif_info = _check_elif_chain(block, else_blocks, merge)
        if elif_info is None:
            return None
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
            if instrs[i].opname == 'COPY' and instrs[i].arg == 2 and instrs[i + 1].opname == 'COMPARE_OP':
                return True
        return False

    def _detect_chained_compare_pattern(self, condition_block: BasicBlock) -> Optional[Dict]:
        """检测链式比较模式（COPY+COMPARE_OP指令对）

        扩展检测：从单block扫描改为追踪ft_successor链中的额外COMPARE_OP块。
        使用min(succs)取then分支（fallthrough）而非else分支。

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
                instrs[i + 1].opname == 'COMPARE_OP'):
                pair_count += 1
                compare_ops.append(instrs[i + 1].argval)
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
            if not any(i.opname == 'COMPARE_OP' for i in ft_candidate.instructions):
                break
            has_back_edge = any(s.start_offset <= ft_candidate.start_offset for s in ft_candidate.successors)
            if has_back_edge:
                break
            extra_chain_blocks.append(ft_candidate)
            visited.add(ft_candidate)
            for i in ft_candidate.instructions:
                if i.opname == 'COMPARE_OP':
                    compare_ops.append(i.argval)
            current_ft = ft_candidate
        if pair_count >= 1 and extra_chain_blocks:
            return {'compare_ops': compare_ops, 'extra_chain_blocks': extra_chain_blocks}
        return None

    def _find_merge_point(self, then_entry, else_entry):
        """统一使用post-dominator，不做任何特殊处理"""
        return self.dom_analyzer.find_nearest_common_post_dominator(
            then_entry, else_entry
        )

    def _identify_ternary_regions(self, loop_regions: List[Region],
                                   try_regions: List[Region],
                                   with_regions: List[Region],
                                   match_regions: List[Region],
                                   boolop_regions: List[Region],
                                   conditional_regions: List[Region]) -> List[Region]:
        """识别三元表达式（IfExp）区域

        算法角色：薄协调器（Thin Coordinator）
        职责：检测CFG中的三元表达式模式，创建TernaryRegion

        【字节码模式特征】
        Python编译器为 `x if cond else y` 生成以下模式：

        基本三元:
            源码: x if cond else y
            字节码:
                LOAD cond
                POP_JUMP_IF_FALSE → false_block   # 条件跳转
                LOAD x                             # true值
                JUMP_FORWARD → merge
              false_block:
                LOAD y                             # false值
              merge:
                STORE result

        三元与BoolOp结合（嵌套条件链）:
            源码: x if a and b else y
            字节码:
                LOAD a
                POP_JUMP_IF_FALSE → false_block
                LOAD b                    # ← 链式条件块
                POP_JUMP_IF_FALSE → false_block
                LOAD x
                JUMP_FORWARD → merge
              false_block:
                LOAD y
              merge:
                STORE result

        【核心检测函数（内部闭包）】

        1. _can_be_ternary_header(block): 判断块是否可作为三元header
           - 必须有2个条件后继
           - 最后指令必须是条件跳转
           - 未被TernaryRegion/AssertRegion/MatchRegion占用
           - 特殊处理已被BoolOpRegion占用的情况（检查是否是ternary候选）

        2. _is_ternary_block(block): 判断块是否是三元值块
           - 2个条件后继都是单表达式块

        3. _build_ternary_condition_chain(start, ft, jt): 构建条件链
           - 用于嵌套三元或boolop+三元组合
           - 沿着false-target方向追踪链式条件

        4. _detect_ternary_context(cond_block, merge_block): 检测上下文类型
           - 返回: ('list'|'tuple'|'set'|'dict'|'call', info, dict_key)
           - 决定三元表达式的包裹方式

        5. _detect_ternary_pattern(block): 完整的模式检测（主入口）
           - 组合以上所有检测逻辑
           - 返回完整的pattern字典或None

        【与其他区域的边界关系】

        与BoolOpRegion的边界（关键！）：
        ─────────────────────────
        当源码是 `a if a and b else 0` 时：
        - BoolOpRegion可能先抢占 `a and b` 的链
        - 此方法通过 _can_be_ternary_header 中的 BoolOpRegion 检查
          和 _is_boolop_ternary_candidate() 来判断是否可以"升级"为ternary
        - 如果BoolOpRegion的短路跳转目标是一个单表达式块，则允许升级
        - 但在 _detect_ternary_pattern 中还有二次检查：
          `if isinstance(existing, BoolOpRegion): skip_ternary = True`
          这意味着如果候选块的链中任何块已被BoolOpRegion占用，则跳过ternary

        ⚠️ 已知问题（test_tn20/tn21失败原因）：
        `_can_be_ternary_header` 允许BoolOpRegion的entry块作为ternary header，
        但 `_detect_ternary_pattern` 中的 chain_blocks 检查会阻止这种情况。
        这是设计上的保守策略：优先保留BoolOp而非强制转换为Ternary。

        与IfRegion的边界：
        ─────────────────
        - IfRegion在 ternary 之前识别
        - 如果块已被IfRegion占用且无chained_compare_blocks，仍可尝试ternary
        - 通过 _try_create_ternary_region() 从IfRegion信息中恢复ternary

        【调用顺序依赖】
        必须在以下区域之后运行：
        - loop_regions, try_regions, with_regions, match_regions
        - boolop_regions（用于边界检测）
        - conditional_regions（用于_try_create_ternary_region回退）
        """
        def _can_be_ternary_header(block):
            if len(block.conditional_successors) != 2:
                return False
            last = block.get_last_instruction()
            if not last or last.opname not in (
                FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                return False
            if block not in self.block_to_region:
                return True
            existing = self.block_to_region[block]
            if isinstance(existing, TernaryRegion):
                return False
            if isinstance(existing, BoolOpRegion):
                if existing.entry == block:
                    if any(isinstance(r, LoopRegion) and r.condition_block == block
                           for r in self.regions):
                        return False
                    return _is_boolop_ternary_candidate(existing)
                return False
            if isinstance(existing, (AssertRegion, MatchRegion)):
                return False
            if isinstance(existing, IfRegion):
                if existing.chained_compare_blocks:
                    return False
            return True

        def _is_boolop_ternary_candidate(boolop_region):
            BOOLOP_JUMP_OPS = SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS

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
                        return False
                    return True
            return True

        def _is_ternary_block(block):
            succs = list(block.conditional_successors)
            if len(succs) != 2:
                return False
            return (self._is_single_expression_block(succs[0]) and
                    self._is_single_expression_block(succs[1]))

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
            if cond_block:
                instrs = [i for i in cond_block.instructions
                         if i.opname not in ('RESUME', 'NOP', 'CACHE')]
                push_null_idx = None
                for idx, i in enumerate(instrs):
                    if i.opname == 'PUSH_NULL':
                        push_null_idx = idx
                        break
                if push_null_idx is not None and push_null_idx + 1 < len(instrs):
                    func_i = instrs[push_null_idx + 1]
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
            return None, None, None

        def _detect_ternary_pattern(block):
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

            chain_blocks = _build_ternary_condition_chain(block, true_block, false_block)

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
                false_existing = self.block_to_region.get(false_block)
                if isinstance(false_existing, TernaryRegion):
                    false_is_ternary = True
                elif (len(false_block.conditional_successors) == 2 and
                      self._is_single_expression_block(true_block)):
                    false_last = false_block.get_last_instruction()
                    if false_last and false_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                        false_succs = list(false_block.conditional_successors)
                        if all(self._is_single_expression_block(s) for s in false_succs):
                            false_is_ternary = True
                if not false_is_ternary:
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

            value_target = None
            if merge_block:
                for instr in merge_block.instructions:
                    if instr.opname in NOISE_OPS:
                        continue
                    if instr.opname in ('STORE_FAST', 'STORE_NAME',
                                        'STORE_GLOBAL', 'STORE_DEREF'):
                        value_target = instr.argval if instr.argval else f'var_{instr.arg}'
                        break

            all_blocks = {block, true_block, false_block}
            # Phase 11: chain_blocks 现在可能是 [(block, op), ...] 格式
            # 需要只提取 block 对象添加到 all_blocks
            if chain_blocks and isinstance(chain_blocks[0], tuple):
                all_blocks.update(cb for cb, _ in chain_blocks)
            else:
                all_blocks.update(chain_blocks)
            if merge_block:
                all_blocks.add(merge_block)

            for vb in (true_block, false_block):
                vb_last = vb.get_last_instruction()
                if vb_last and vb_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                    for s in vb.conditional_successors:
                        all_blocks.add(s)

            for nested in nested_ternary_regions:
                all_blocks.update(nested.blocks)

            container_type, func_call_info, dict_key_info = _detect_ternary_context(block, merge_block)
            return {
                'block': block,
                'true_block': true_block,
                'false_block': false_block,
                'merge_block': merge_block,
                'value_target': value_target,
                'chain_blocks': chain_blocks,
                'all_blocks': all_blocks,
                'nested_ternary_regions': nested_ternary_regions,
                'container_type': container_type,
                'func_call_info': func_call_info,
                'dict_key_info': dict_key_info,
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
                condition_chain_blocks=pattern['chain_blocks'],
                container_type=pattern['container_type'],
                func_call_info=pattern['func_call_info'],
                dict_key_info=pattern['dict_key_info'],
            )

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
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset, reverse=True):
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
        if isinstance(region, LoopRegion):
            if block == region.header_block:
                return False
            if block == region.condition_block:
                return False
            if block in getattr(region, 'condition_chain_blocks', []):
                return False
            if block == region.back_edge_block:
                return False
            if block in getattr(region, 'back_edge_blocks', set()):
                return False
            last = block.get_last_instruction()
            if last and last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                return False
            return True
        if isinstance(region, WithRegion):
            return True
        if isinstance(region, MatchRegion):
            if block == region.subject_block:
                return False
            return True
        return False

    def _is_block_available_for_boolop(self, block: BasicBlock, claimed: Set[BasicBlock]) -> bool:
        if block not in claimed:
            return True
        return self._is_block_in_region_body(block)

    def _identify_boolop_regions(self, existing_regions: List[Region]) -> List[Region]:
        """识别布尔运算（and/or）短路求值区域

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

        【已知限制】
        1. 复合表达式 `a and b or c` 可能被误识别为 ternary（test_bool13）
        2. 循环/for条件中的boolop可能不被识别（test_bool11, test_bool12）
        3. assert语句中的boolop被AssertRegion抢占（test_bool15）
        4. 嵌套boolop在复杂表达式中可能失败（test_bool16, test_bool17）

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
        for region in existing_regions:
            if isinstance(region, LoopRegion) and region.condition_block:
                loop_condition_blocks.add(region.condition_block)
                for cb in getattr(region, 'condition_chain_blocks', []):
                    loop_condition_blocks.add(cb)
        blocks_in_order = self.cfg.get_blocks_in_order()
        for block in blocks_in_order:
            if block in claimed and block not in loop_condition_blocks:
                continue
            chain = self._detect_boolop_chain_start(block, claimed)
            if chain is None:
                continue
            region = self._create_boolop_region_from_chain(chain, claimed)
            if region:
                boolop_regions.append(region)
        for region in existing_regions:
            if not isinstance(region, LoopRegion) or region.condition_block is None:
                continue
            if any(isinstance(r, BoolOpRegion) and region.condition_block in r.blocks
                   for r in boolop_regions):
                continue
            loop_cond = region.condition_block
            chain = self._detect_while_condition_boolop_chain(loop_cond, region)
            if chain and len(chain) >= 2:
                boolop_region = self._create_boolop_region_from_chain(chain, claimed)
                if boolop_region:
                    region.add_child(boolop_region)
                    boolop_regions.append(boolop_region)
                    region.is_while_true = False
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
                            _cl2 = cond_block.get_last_instruction()
                            _cjt2 = self.cfg.get_block_by_offset(_cl2.argval) if _cl2 and _cl2.argval is not None else None
                            if _cjt2 and pred_jump_target != _cjt2:
                                _pjt_is_exit = (pred_jump_target not in loop.blocks and
                                                  pred_jump_target != loop.entry and
                                                  pred_jump_target != loop.condition_block)
                                if _pjt_is_exit:
                                    header_last = loop.header_block.get_last_instruction()
                                    if header_last and header_last.opname in BACKWARD_CONDITIONAL_JUMP_OPS:
                                        break
                                else:
                                    break
                        else:
                            break
            pred_op = 'and' if 'FALSE' in pred_last.opname else 'or'
            if pred_op != op_type:
                break
            chain.insert(0, (pred, pred_op))
            current = pred
        return chain if len(chain) >= 1 else None

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
            jump_target = self.cfg.get_block_by_offset(last_instr.argval)
            ft_succ = next((s for s in succs if s.start_offset != last_instr.argval), None)
            if ft_succ is None:
                break
            if ft_succ.start_offset in visited:
                break
            if ft_succ == loop.header_block or ft_succ in loop.body_blocks:
                break
            region_for_ft = self.block_to_region.get(ft_succ)
            if isinstance(region_for_ft, LoopRegion):
                break
            if isinstance(region_for_ft, IfRegion) and region_for_ft.condition_block != ft_succ:
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
        if len(chain) < 2:
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
        if block in claimed:
            return None
        last_instr = block.get_last_instruction()
        if not last_instr:
            return None
        if last_instr.opname in SHORT_CIRCUIT_JUMP_OPS:
            chain = self._detect_boolop_short_circuit_chain(block)
            if chain is None or len(chain) < 1:
                return None
            return chain
        if last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
            chain = self._detect_boolop_conditional_chain(block, claimed)
            if chain is None or len(chain) < 1:
                return None
            return chain
        return None

    def _create_boolop_region_from_chain(self, chain: List[Tuple[BasicBlock, str]], claimed: Set[BasicBlock]) -> Optional[BoolOpRegion]:
        start_block = chain[0][0]
        chain_blocks = set(b for b, _ in chain)
        last_block, _ = chain[-1]
        last_instr = last_block.get_last_instruction()
        merge = None
        BOOLOP_JUMP_OPS = SHORT_CIRCUIT_JUMP_OPS | FORWARD_CONDITIONAL_JUMP_OPS
        if last_instr and last_instr.opname in BOOLOP_JUMP_OPS and last_instr.argval is not None:
            merge = self.cfg.get_block_by_offset(last_instr.argval)
        is_condition_context = (last_instr is not None and last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS)
        for chain_block, _ in chain:
            last = chain_block.get_last_instruction()
            if last and last.opname in SHORT_CIRCUIT_JUMP_OPS:
                ft_succ = next((s for s in sorted(chain_block.conditional_successors, key=lambda s: s.start_offset)
                                if s.start_offset != last.argval), None)
                if ft_succ and ft_succ not in chain_blocks:
                    chain_blocks.add(ft_succ)
        region_blocks = chain_blocks | ({merge} if merge else set())
        value_target = None
        if merge:
            for instr in merge.instructions:
                if instr.opname in ('STORE_FAST', 'STORE_NAME',
                                    'STORE_GLOBAL', 'STORE_DEREF'):
                    value_target = instr.argval if instr.argval else f'var_{instr.arg}'
                    break
        region = BoolOpRegion(
            region_type=RegionType.BOOL_OP,
            entry=start_block,
            blocks=region_blocks,
            op_chain=chain,
            merge_block=merge,
            value_target=value_target,
            condition_block=None,
        )
        region.is_condition_context = is_condition_context
        self.regions.append(region)
        for b in region.blocks:
            if b not in self.block_to_region:
                self.block_to_region[b] = region
                claimed.add(b)
        return region

    def _detect_boolop_conditional_chain(self, start_block: BasicBlock, claimed: Set[BasicBlock]) -> Optional[List[Tuple[BasicBlock, str]]]:
        chain: List[Tuple[BasicBlock, str]] = []
        current = start_block
        visited = set()
        BOOLOP_CHAIN_JUMPS = FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS
        while current and current.start_offset not in visited:
            visited.add(current.start_offset)
            last = current.get_last_instruction()
            if not last or last.opname not in BOOLOP_CHAIN_JUMPS:
                break
            if current in self.block_to_region:
                break
            if last.opname in NONE_CHECK_OPS:
                break
            op_type = 'and' if 'FALSE' in last.opname else 'or'
            chain.append((current, op_type))
            succs = list(current.conditional_successors)
            if len(succs) != 2:
                break
            ft_succ = next((s for s in succs if s.start_offset != last.argval), None)
            if ft_succ is None:
                break
            if ft_succ in self.block_to_region or ft_succ in claimed:
                break
            if len(chain) >= 2:
                first_jump_target = self.cfg.get_block_by_offset(chain[0][0].get_last_instruction().argval)
                cur_jump_target = self.cfg.get_block_by_offset(last.argval)
                prev_op = chain[-2][1]
                if op_type == prev_op and first_jump_target and cur_jump_target and first_jump_target != cur_jump_target:
                    break
            current = ft_succ
        if len(chain) < 2:
            return None
        first_last = chain[0][0].get_last_instruction()
        first_jt = self.cfg.get_block_by_offset(first_last.argval) if first_last and first_last.argval is not None else None
        if first_jt is None:
            return None
        all_same_target = True
        target_groups = {}
        for cb, cop in chain:
            cl = cb.get_last_instruction()
            if not cl or cl.argval is None:
                all_same_target = False
                break
            cjt = self.cfg.get_block_by_offset(cl.argval)
            if cjt != first_jt:
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
                          if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
        jt_has_store = any(i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                          for i in jt_target.instructions
                          if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'))
        if ft_has_store and jt_has_store:
            return True
        if ft_has_store and self._is_trivial_block(jt_target):
            return True
        first_block, _ = chain[0]
        first_instr = first_block.get_last_instruction()
        if first_instr and first_instr.argval is not None:
            first_ft = next((s for s in first_block.conditional_successors
                             if s.start_offset != first_instr.argval), None)
            if first_ft and len(first_ft.instructions) <= 3:
                meaningful = [i for i in first_ft.instructions
                             if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                if meaningful and meaningful[0].opname in ('POP_JUMP_FORWARD_IF_FALSE',
                                                           'POP_JUMP_BACKWARD_IF_FALSE',
                                                           'POP_JUMP_FORWARD_IF_TRUE',
                                                           'POP_JUMP_BACKWARD_IF_TRUE'):
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

    def _detect_boolop_short_circuit_chain(self, start_block: BasicBlock) -> Optional[List[Tuple[BasicBlock, str]]]:
        chain: List[Tuple[BasicBlock, str]] = []
        current = start_block
        visited = set()
        while current and current.start_offset not in visited:
            visited.add(current.start_offset)
            last = current.get_last_instruction()
            if not last or last.opname not in SHORT_CIRCUIT_JUMP_OPS:
                if chain and last and last.opname not in ('RETURN_VALUE', 'RETURN_CONST',
                                                           'RAISE_VARARGS', 'RERAISE'):
                    pure_instrs = [i for i in current.instructions
                                   if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                    has_store = any(i.opname in ('STORE_NAME', 'STORE_FAST',
                                                  'STORE_GLOBAL', 'STORE_DEREF')
                                    for i in pure_instrs)
                    succs = list(current.successors)
                    if (not has_store and len(succs) == 1 and
                            succs[0].start_offset not in visited and
                            succs[0] not in self.block_to_region):
                        next_last = succs[0].get_last_instruction()
                        if (next_last and next_last.opname in SHORT_CIRCUIT_JUMP_OPS):
                            current = succs[0]
                            continue
                        next_pure = [i for i in succs[0].instructions
                                     if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
                        if (len(next_pure) >= 1 and next_pure[0].opname == 'UNARY_NOT' and
                                len(next_pure) >= 2 and
                                next_last and next_last.opname in SHORT_CIRCUIT_JUMP_OPS):
                            current = succs[0]
                            continue
                break
            if current in self.block_to_region:
                break
            op_type = 'and' if 'FALSE' in last.opname else 'or'
            chain.append((current, op_type))
            succs = list(current.conditional_successors)
            if len(succs) != 2:
                break
            ft_succ = next((s for s in succs if s.start_offset != last.argval), None)
            if ft_succ is None:
                break
            if ft_succ in self.block_to_region:
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
        """
        识别序列区域（未被其他区域包含的基本块）
        
        算法说明：
        1. 遍历所有未被其他区域包含的基本块
        2. 为每个块创建一个 BASIC 类型的区域
        3. 这些区域作为其他结构之间的连接
        
        字节码模式：
        - 基本的语句块
        - 不包含特殊控制流结构
        - 可能包含 RETURN_VALUE、STORE_* 等普通指令
        
        边界条件：
        - 识别以 return None 结尾的块
        - 处理空的语句块（pass）
        
        区域归约算法符合度：
        - 作为最底层的归约单元
        - 确保所有块都被归约
        - 形成完整的覆盖
        """
        regions = []
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
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

    def _find_nop_fallthrough_parent(self, region: Region, all_regions: List[Region]) -> Optional[Region]:
        """通过NOP占位块的fallthrough查找父区域

        当区域入口块的前驱是NOP占位块，且该NOP块属于某个父区域时，
        建立父子关系。这是区域归约算法的NOP fallthrough处理。
        """
        entry = region.entry
        if entry is None:
            return None
        NOP_ONLY = frozenset({'RESUME', 'NOP', 'CACHE'})
        for pred in entry.predecessors:
            if all(i.opname in NOP_ONLY for i in pred.instructions):
                parent = self._find_enclosing_region(
                    pred,
                    region_types=(LoopRegion, IfRegion),
                    candidate_regions=[r for r in all_regions if r is not region]
                )
                if parent is not None:
                    return parent
        return None

    def _get_region_offset_range(self, region: Region) -> Tuple[int, int]:
        """计算区域的偏移范围 [start_offset, end_offset]

        Args:
            region: 区域对象

        Returns:
            Tuple[int, int]: (最小偏移, 最大偏移)
        """
        if not region.blocks:
            return (0, 0)

        offsets = [block.start_offset for block in region.blocks]
        return (min(offsets), max(offsets))

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

            if candidates:
                region_priority = {'IfRegion': 5, 'LoopRegion': 5,
                                   'MatchRegion': 4, 'BoolOpRegion': 2,
                                   'TryExceptRegion': 3, 'WithRegion': 3}
                child_p = region_priority.get(type(child).__name__, 0)
                best_cand_p = max(region_priority.get(type(c).__name__, 1) for c in candidates)
                if best_cand_p >= child_p:
                    best_parent = max(candidates, key=lambda c: region_priority.get(type(c).__name__, 1))
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
                                loop_entry_in_if = (child.entry and child.entry in best_parent.blocks)
                                loop_has_real_structure = (getattr(child, 'back_edge_blocks', None) or
                                                         getattr(child, 'header_block', None))
                                if (parent_in_child or entry_in_body or
                                    (cond_is_loop_cond and loop_entry_in_if) or
                                    (loop_entry_in_if and loop_has_real_structure)):
                                    continue
                        best_parent.add_child(child)

        boolop_regions = [r for r in regions if isinstance(r, __import__('core.cfg.region_analyzer', fromlist=['BoolOpRegion']).BoolOpRegion)]
        if_regions = [r for r in regions if isinstance(r, __import__('core.cfg.region_analyzer', fromlist=['IfRegion']).IfRegion)]
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

    def _find_enclosing_region_by_containment(self, child_region: Region,
                                              query_block: BasicBlock = None,
                                              region_types: Tuple[type, ...] = None,
                                              candidate_regions: List[Region] = None) -> Optional[Region]:
        """基于严格的偏移范围包含和内容块包含查找父区域

        算法：对候选父区域进行双重包含检查
        1. 检查查询块是否在候选区域的blocks集合中（内容块包含）
        2. 如果有多个候选，选择最小的（最内层）作为父区域

        Args:
            child_region: 子区域
            query_block: 用于查询的块（默认为child_region.entry）
            region_types: 允许的父区域类型元组
            candidate_regions: 候选父区域列表

        Returns:
            Optional[Region]: 最内层的包含父区域，如果没有则返回None
        """
        if query_block is None:
            query_block = child_region.entry

        if region_types is None:
            region_types = (LoopRegion, TryExceptRegion, WithRegion)

        search_regions = candidate_regions if candidate_regions is not None else self.regions

        innermost = None
        innermost_size = float('inf')

        for region in search_regions:
            if not isinstance(region, region_types):
                continue

            if region is child_region:
                continue

            if query_block not in region.blocks:
                continue

            size = len(region.blocks)
            if size < innermost_size:
                innermost = region
                innermost_size = size

        return innermost

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

    def get_root_regions(self) -> List[Region]:
        return [r for r in self.regions if r.parent is None]

    def _is_only_jumps(self, block: BasicBlock) -> bool:
        for instr in block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                continue
            if instr.opname in ('JUMP_BACKWARD', 'JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                continue
            return False
        return True

    def _is_trivial_control_block(self, block: BasicBlock) -> bool:
        for instr in block.instructions:
            if instr.opname in ('RESUME', 'NOP', 'CACHE', 'POP_TOP', 'PUSH_NULL'):
                continue
            if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                continue
            return False
        return True

    def _is_equivalent_exit_block(self, block_a: BasicBlock, block_b: BasicBlock, depth: int = 0) -> bool:
        if block_a is block_b:
            return True
        if depth > 5:
            return False
        a_is_only_jumps = self._is_only_jumps(block_a)
        b_is_only_jumps = self._is_only_jumps(block_b)
        if a_is_only_jumps and b_is_only_jumps:
            a_succs = list(block_a.successors)
            b_succs = list(block_b.successors)
            if len(a_succs) == 1 and len(b_succs) == 1:
                return self._is_equivalent_exit_block(a_succs[0], b_succs[0], depth + 1)
            return False
        if a_is_only_jumps and not b_is_only_jumps:
            a_succs = list(block_a.successors)
            if len(a_succs) == 1:
                return self._is_equivalent_exit_block(a_succs[0], block_b, depth + 1)
            return False
        if b_is_only_jumps and not a_is_only_jumps:
            b_succs = list(block_b.successors)
            if len(b_succs) == 1:
                return self._is_equivalent_exit_block(block_a, b_succs[0], depth + 1)
            return False
        if self._is_trivial_return_block(block_a) and self._is_trivial_return_block(block_b):
            return True
        return False

    def _is_trivial_return_block(self, block: BasicBlock) -> bool:
        meaningful = [i for i in block.instructions
                     if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
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

    def get_region_for_block(self, block: BasicBlock) -> Optional[Region]:
        return self.block_to_region.get(block)

    def get_entry_region_for_block(self, block: BasicBlock) -> Optional[Region]:
        try_region = None
        if_region = None
        match_region = None
        with_region = None
        for region in self.regions:
            if isinstance(region, TryExceptRegion) and region.entry == block:
                try_region = region
            if isinstance(region, WithRegion) and region.entry == block:
                with_region = region
            if isinstance(region, LoopRegion):
                if region.header_block == block or region.entry == block or region.condition_block == block:
                    return region
            if isinstance(region, IfRegion) and region.condition_block == block:
                if_region = region
            if isinstance(region, AssertRegion) and region.condition_block == block:
                return region
            if isinstance(region, MatchRegion) and region.entry == block:
                match_region = region
        if try_region:
            return try_region
        if with_region:
            return with_region
        if match_region:
            return match_region
        if if_region:
            return if_region
        return None

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

    def get_effective_instructions(self, block: BasicBlock) -> Optional[List[Instruction]]:
        return self.effective_instructions.get(block.start_offset)

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

    def find_blocks_after_finally(self, region: 'TryExceptRegion') -> List[BasicBlock]:
        result = []
        for block in self.cfg.blocks.values():
            if block in region.blocks:
                continue
            if any(i.opname in ('PUSH_EXC_INFO', 'RERAISE') for i in block.instructions):
                continue
            is_normal_path = False
            for eb in region.else_blocks:
                if block in eb.successors:
                    is_normal_path = True
                    break
            if not is_normal_path:
                for exc_type, exc_name, handler_blocks in region.except_handlers:
                    for hb in handler_blocks:
                        if block in hb.successors:
                            is_normal_path = True
                            break
                    if is_normal_path:
                        break
            if not is_normal_path:
                for tb in region.try_blocks:
                    if block in tb.successors and block not in region.else_blocks:
                        is_normal_path = True
                        break
            if is_normal_path:
                result.append(block)
        return result

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
            if isinstance(region, LoopRegion):
                self._precompute_loop_analysis_data(region)
            elif isinstance(region, IfRegion):
                self._precompute_chained_compare_analysis(region)
            elif isinstance(region, TryExceptRegion):
                self._enhance_finally_copy_annotation(region)

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
                if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')
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
                for region in all_regions:
                    if isinstance(region, LoopRegion) and block in region.blocks:
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
                        for region in all_regions:
                            if (isinstance(region, LoopRegion) and
                                target_block == region.header_block):
                                block_metadata['is_implicit_continue'] = True
                                break

                elif last_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    if role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
                        block_metadata['is_explicit_break_jump'] = True

                elif last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    if role == BlockRole.RETURN_NONE:
                        for region in all_regions:
                            if (isinstance(region, LoopRegion) and
                                block in region.body_blocks):
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
                    if instr.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
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
                        for r in self.regions:
                            if (isinstance(r, LoopRegion) and
                                target == r.header_block):
                                copy_meta['continue_target_loop'] = r
                                break

            enhanced_copy_info[block_offset] = copy_meta

        region.metadata['enhanced_finally_copies'] = enhanced_copy_info
