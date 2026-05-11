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
        conditional_regions = self._identify_conditional_regions(
            loop_regions=loop_regions,
            assert_regions=assert_regions,
            try_regions=try_regions,
            with_regions=with_regions,
            match_regions=match_regions,
            boolop_regions=boolop_regions,
            ternary_regions=ternary_regions
        )

        elif_chain_entries = set()
        for cr in conditional_regions:
            if isinstance(cr, IfRegion) and cr.region_type == RegionType.IF_ELIF_CHAIN:
                elif_chain_entries.add(cr.entry)
        ternary_regions = [tr for tr in ternary_regions
                          if not (tr.entry and tr.entry in elif_chain_entries)]

        all_phase12_regions = (
            loop_regions + try_regions + with_regions +
            match_regions + assert_regions + chained_compare_regions + boolop_regions + ternary_regions + conditional_regions
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
                    existing_priority = self.REGION_TYPE_PRIORITY.get(
                        existing.region_type, 0)
                    if current_priority > existing_priority:
                        self.block_to_region[block] = region

        hierarchy = self._build_region_hierarchy(regions=all_regions)

        self._annotate_all_roles(all_regions)

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
        """检测是否是单表达式块（改进版）

        允许的情况：
        1. 纯表达式指令（LOAD/CALL/BINARY_OP等）
        2. 最后一个指令可以是：JUMP_FORWARD/RETURN_VALUE/RETURN_CONST/POP_TOP
        3. 不允许：STORE/DELETE/RAISE/YIELD/IMPORT等副作用操作
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
                return False

        if len(effective) == 2:
            if (effective[0].opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME',
                                        'LOAD_GLOBAL', 'LOAD_DEREF') and
                    effective[1].opname in ('RETURN_VALUE', 'RETURN_CONST')):
                ret_val = effective[1].argval if effective[1].opname == 'RETURN_CONST' else None
                load_val = effective[0].argval if effective[0].opname == 'LOAD_CONST' else None
                if ret_val is None and load_val is None:
                    return False

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
                        self._assign_region_role(block.start_offset,
                                                 BlockRole.CONTINUE)
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
        while result:
            last = result[-1]
            if last.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_DEREF',
                               'LOAD_ATTR', 'LOAD_METHOD'):
                has_iter = any(i.opname in ('GET_ITER', 'GET_AITER', 'FOR_ITER')
                              for i in block.instructions if i.offset > last.offset)
                if has_iter:
                    result.pop()
                    continue
            break
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
        regions = []

        for header, _ in sorted_loops:
            back_edge_sources = [src for src, tgt in self.loop_analyzer.back_edges
                                if tgt == header and self.dom_analyzer.is_dominator(header, src)]
            if not back_edge_sources:
                continue

            body = self._collect_natural_loop_body(header, back_edge_sources)

            body_key = frozenset(body)
            if body_key in seen_bodies:
                continue
            seen_bodies.add(body_key)

            is_fake_loop = self._is_fake_loop(header, body, back_edge_sources)
            if is_fake_loop:
                continue

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
            else_blocks, natural_exit = self._find_loop_else(header, body, loop_type, for_iter_exit)
            else_blocks = else_blocks or []
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

        return regions


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
                        if any(detector.is_iterator_setup_opcode(i) for i in pred.instructions) or \
                           any(i.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE') and
                               self.cfg.get_block_by_offset(i.argval) == header for i in pred.instructions):
                            for_iter_setup = pred
                            break
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
        """检测 while True 循环

        判断依据：
        1. header块无有意义指令 → while True
        2. header块无条件跳转 → while True
        3. header块含STORE指令后跟条件跳转 → while True + break模式
        4. header块仅有条件评估和条件跳转 → while <condition>
        """
        meaningful = [i for i in header.instructions 
                    if i.opname not in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL')]
        
        if not meaningful:
            return True
        
        has_conditional_jump = False
        has_store_before_jump = False
        for i in meaningful:
            if i.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                          'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                          'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                          'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                          'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE',
                          'FORWARD_JUMP_IF_TRUE', 'FORWARD_JUMP_IF_FALSE'):
                has_conditional_jump = True
                break
            if i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                has_store_before_jump = True
        
        if not has_conditional_jump:
            return True
        
        if has_store_before_jump:
            return True
        
        return False


    def _find_loop_else(self, header: BasicBlock, loop_body: Set[BasicBlock], loop_type: RegionType,
                        for_iter_exit: Optional[BasicBlock] = None) -> Tuple[Optional[List[BasicBlock]], Optional[BasicBlock]]:
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
        detector = get_opcode_detector()
        for block in body_set:
            if block == header:
                continue
            for succ in block.successors:
                if succ not in body_set and succ != header and succ not in loop_successors:
                    block_last = block.get_last_instruction()
                    if block_last and detector.is_conditional_jump(block_last):
                        loop_successors.append(succ)
        loop_successors = list(set(loop_successors))

        if not loop_successors:
            return None, None

        natural_exit = self.dom_analyzer.find_nearest_common_post_dominator(set(loop_successors))
        if not natural_exit or natural_exit in body_set:
            if not natural_exit and len(loop_successors) > 1:
                non_return_successors = [s for s in loop_successors
                                        if not self._check_block_has_trailing_return_none(s)]
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

        result = sorted(else_blocks, key=lambda b: b.start_offset) if else_blocks else None
        return result, natural_exit

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
                    if not any(i.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START') for i in s.instructions):
                        if not any(i.opname in ('RETURN_VALUE', 'RETURN_CONST') for i in b.instructions):
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
                                    back_edge_sources: List[BasicBlock]) -> Set[BasicBlock]:
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
        for idx, instr in enumerate(cond_instrs):
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                store_idx = idx
        
        if store_idx is not None:
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
        识别异常处理区域（try-except-finally）
        
        算法说明：
        1. 解析异常表，识别每个异常处理区域的结构
        2. 区分 try-except、try-finally 和 try-except-finally 结构
        3. 处理嵌套异常结构
        4. 构建 TryExceptRegion 对象，包含：
           - try 块：被保护的代码块
           - except 处理器：异常类型、异常名、处理代码块
           - finally 块：清理代码块
           - else 块：无异常时执行的块
        
        字节码模式：
        - 异常表中包含：
          - 保护范围（start/end offsets）
          - 处理器入口（handler offset）
          - 深度信息（depth）
        - 字节码特征：
          - PUSH_EXC_INFO：异常处理开始
          - CHECK_EXC_MATCH：异常类型匹配
          - POP_EXCEPT：异常处理结束
          - RERAISE：重新抛出异常
          - WITH_EXCEPT_START：with 语句的异常处理
        
        边界条件：
        - 处理嵌套的异常表条目（通过 depth 字段）
        - 识别与 finally 配对的 except 块
        - 正确处理清理块和异常传播链
        - 区分 with 语句的异常处理器
        
        区域归约算法符合度：
        - 自底向上构建异常处理区域
        - 正确建立父子关系
        - 不重叠区域覆盖
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
        """基于异常表条目和指令特征解析handler信息

        分类规则（基于指令特征）：
        - WITH_EXCEPT_START → with cleanup handler
        - PUSH_EXC_INFO + RERAISE → finally handler
        - PUSH_EXC_INFO + CHECK_EXC_MATCH → except handler
        - PUSH_EXC_INFO + CHECK_EG_MATCH → except* handler

        depth字段关联嵌套关系：depth大的嵌套在depth小的内部。

        嵌套try处理：CPython将外层try拆分为多个异常表条目（仅覆盖内层handler
        未捕获的间隙），需要合并指向同一handler的条目，并通过迭代扩展try范围
        以包含内层try-except区域。
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
            if is_cleanup_only and actual_handler_start == entry_target:
                if handler_type == 'finally':
                    is_cleanup_only = False
                else:
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
        """基于入口块指令特征统一分类handler类型

        分类规则（按优先级）：
        1. WITH_EXCEPT_START → with cleanup handler
        2. PUSH_EXC_INFO + RERAISE → finally handler
        3. PUSH_EXC_INFO + CHECK_EXC_MATCH → except handler
        4. PUSH_EXC_INFO + CHECK_EG_MATCH → except* handler
        5. PUSH_EXC_INFO + 后继块含RERAISE(非cleanup) → finally handler
        6. PUSH_EXC_INFO + 其他 → except handler（默认）
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
                return []

        else_blocks = []
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
            if (block.start_offset > precise_handler_end and
                block.start_offset < merge_point.start_offset and
                block not in all_handler_blocks and
                block not in try_region.blocks and
                not self._is_pass_or_return_none_block(block)):
                else_blocks.append(block)

        return else_blocks

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

        反编译逻辑：
        1. 扫描BEFORE_WITH指令：遍历所有基本块，找到含BEFORE_WITH/BEFORE_ASYNC_WITH
           的块，记录其depth信息（来自异常表）
        2. 按depth排序：确保嵌套的with语句从外到内处理
        3. 逐个构建WithRegion：对每个BEFORE_WITH块调用_build_single_with_region
        4. 合并连续with区域：调用_merge_consecutive_with_regions将相邻的
           独立with语句合并（当它们的body_offset_end和下一个的body_offset_start
           连续且depth相同时，对应 `with A: ... with B: ...` 的连续with语句）

        与其他区域识别器的交互：
        - 在_identify_try_except_regions之后执行，try识别器会跳过with类型的handler
        - 在_identify_conditional_regions之前执行，with区域信息传递给条件识别器
          以避免将WITH_EXCEPT_START块误识别为IfRegion

        关键约束：
        - 连续with语句（w091/w092/w093）：第二个with的BEFORE_WITH块不应被
          _identify_conditional_regions识别为IfRegion的条件头
        - with+try/except（w097/w102）：TryExceptRegion不应与WithRegion重叠
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
            merged_p.append({'type': 'MatchOr', 'patterns': orps} if len(orps) > 1 else orps[0])
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
                    idx += 1
                    continue
            saw_unpack = False
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
                        pattern_store_names.discard(store_name)
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
                rbody = case_bodies[i][0] if case_bodies[i] else None
                nrbody = case_bodies[j][0] if case_bodies[j] else None
                should_merge = (rbody and nrbody and rbody == nrbody)
                if should_merge:
                    current_block = case_blocks[i]
                    next_block = case_blocks[j]
                    has_structural_pattern_op = (
                        any(i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                                         'MATCH_KEYS', 'MATCH_MAPPING_KEYS')
                            for i in current_block.instructions) or
                        any(i.opname in ('MATCH_CLASS', 'MATCH_SEQUENCE', 'MATCH_MAPPING',
                                         'MATCH_KEYS', 'MATCH_MAPPING_KEYS')
                            for i in next_block.instructions))
                    if has_structural_pattern_op:
                        break
                    orps.append(case_patterns[j])
                    body |= set(case_bodies[j])
                    j += 1
                else:
                    break
            merged_p.append({'type': 'MatchOr', 'patterns': orps} if len(orps) > 1 else orps[0])
            merged_b.append(sorted(body, key=lambda b: b.start_offset))
            i = j
        merge_block = self._mr_compute_case_merge(merged_b)
        return case_blocks, merged_p, merged_b, merge_block, all_blocks

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
            for body_candidate in [success]:
                worklist_g = [body_candidate]
                visited_g = {current}
                while worklist_g:
                    gc = worklist_g.pop(0)
                    if gc in visited_g or gc == jt:
                        continue
                    visited_g.add(gc)
                    gj = self._mr_find_case_jump_instruction(gc)
                    if gj and gc != current:
                        guard_jump_target = gj.argval
                        break
                    meaningful_g = [i for i in gc.instructions if i.opname not in NOISE_OPS]
                    if all(i.opname in ('POP_TOP', 'LOAD_CONST', 'STORE_FAST', 'STORE_NAME',
                                        'STORE_GLOBAL', 'STORE_DEREF', 'UNPACK_SEQUENCE', 'UNPACK_EX',
                                        'COPY', 'SWAP', 'GET_LEN', 'COMPARE_OP', 'IS_OP',
                                        'JUMP_FORWARD', 'JUMP_ABSOLUTE') or
                           i.opname in CONDITIONAL_JUMP_OPS or
                           i.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'EXTENDED_ARG')
                           for i in gc.instructions):
                        for s in gc.successors:
                            if s not in visited_g:
                                worklist_g.append(s)
                if guard_jump_target is not None:
                    break
            resolved_success = self._mr_resolve_body_entry(success)
            if resolved_success and resolved_success != jt:
                stop_set = visited | {jt}
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
        jt = self.cfg.get_block_by_offset(last.argval)
        if jt is None:
            return False
        has_nop_prefix = False
        for instr in jt.instructions:
            if instr.opname == 'NOP':
                has_nop_prefix = True
            elif instr.opname not in NOISE_OPS:
                break
        if not has_nop_prefix:
            return False
        has_compare = any(i.opname in ('COMPARE_OP', 'IS_OP') for i in meaningful)
        has_none_check = last.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_IF_NOT_NONE',
                                          'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_IF_NONE')
        if not has_compare and not has_none_check:
            return False
        simple_ops = frozenset({
            'COPY', 'LOAD_CONST', 'COMPARE_OP', 'IS_OP',
            'LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
            'POP_TOP', 'SWAP',
        }) | NOISE_OPS | CONDITIONAL_JUMP_OPS
        if not all(i.opname in simple_ops for i in meaningful):
            return False
        return True

    def _scan_literal_match_subjects(self, claimed):
        literal_regions = []
        for block in self.cfg.get_blocks_in_order():
            if block in claimed:
                continue
            is_copy_subject = self._is_match_subject_block(block)
            is_nop_case = self._is_simple_match_case_block(block)
            if not is_copy_subject and not is_nop_case:
                continue
            if self.block_to_region.get(block) is not None:
                continue
            if block is None:
                continue
            case_blocks_l, case_patterns_l, case_bodies_l = [], [], []
            all_blocks_l = {block}
            visited_l = set()
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
                merged_p.append({'type': 'MatchOr', 'patterns': orps} if len(orps) > 1 else orps[0])
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
        识别条件区域（if/if-else/if-elif-else）
        
        算法说明：
        1. 从后向前遍历基本块，识别条件跳转
        2. 识别具有两个条件后继的块作为条件头
        3. 构建 IfRegion 对象，区分：
           - if-then：只有 then 分支
           - if-then-else：有两个分支
           - if-elif-else：多个条件链
        4. 使用合并块检测：
           - 判断一个块被两个分支都跳向的共同出口
           - 正确处理嵌套条件
        
        字节码模式：
        - POP_JUMP_FORWARD_IF_*：条件前向跳转
        - POP_JUMP_BACKWARD_IF_*：条件后向跳转
        - 条件块作为入口
        - 合并块作为共同出口
        
        边界条件：
        - 避免与循环、异常处理等结构冲突
        - 正确识别 elif 链结构
        - 处理空的 then/else 分支
        - 区分 if 语句后的语句块
        
        区域归约算法符合度：
        - 自底向上识别条件区域
        - 基于支配边界分析
        - 正确建立嵌套关系
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
                if br_check is not None or any(block in lr.blocks for lr in loop_regions):
                    continue
                cond_succs_check = list(block.conditional_successors)
                if len(cond_succs_check) == 2:
                    if any(s in lr.blocks or s == lr.header_block or s == lr.entry for lr in loop_regions for s in cond_succs_check):
                        continue

            if try_regions:
                if any(instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH') for instr in block.instructions):
                    continue

            if ternary_regions and any(
                isinstance(tr, TernaryRegion) and tr.entry == block
                for tr in ternary_regions
            ):
                continue

            br_check = self.block_to_region.get(block)
            if isinstance(br_check, BoolOpRegion) and br_check.entry != block:
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
                    if_regions.append(region)
                    if boolop_region is not None:
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
        if else_blocks and all(self._is_trivial_block(b) for b in else_blocks):
            else_blocks = []
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
            if not ft_last or ft_last.opname != "COMPARE_OP":
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

        Returns:
            Dict with 'compare_ops' key or None
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
        if pair_count >= 1:
            return {'compare_ops': compare_ops}
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
        """识别三元表达式区域（薄协调器）

        算法流程：
        1. 遍历所有可能的header块（从偏移量最大开始）
        2. 检测三元模式
        3. 创建TernaryRegion并注册
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
            for chain_block, _ in reversed(boolop_region.op_chain):
                last_instr = chain_block.get_last_instruction()
                if last_instr and last_instr.opname in SHORT_CIRCUIT_JUMP_OPS and last_instr.argval is not None:
                    jt_block = self.cfg.get_block_by_offset(last_instr.argval)
                    if not jt_block:
                        return False
                    return self._is_single_expression_block(jt_block)
            return False

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
                         if i.opname not in NOISE_OPS]
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
                if true_discards and false_discards:
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
                    skip_ternary = True
                    break
            if skip_ternary:
                return None

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

    def _identify_boolop_regions(self, existing_regions: List[Region]) -> List[Region]:
        """遍历候选块检测短路链（薄协调器）

        算法流程：
        1. 收集已占用块集合
        2. 遍历所有候选块
        3. 检测短路链并创建区域
        4. 为while循环条件块创建BoolOpRegion
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
            if region.is_while_true:
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
        return boolop_regions

    def _detect_while_condition_boolop_chain(self, cond_block: BasicBlock, loop: LoopRegion) -> Optional[List[Tuple[BasicBlock, str]]]:
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
            pred_op = 'and' if 'FALSE' in pred_last.opname else 'or'
            if pred_op != op_type:
                break
            chain.insert(0, (pred, pred_op))
            current = pred
        return chain if len(chain) >= 2 else None

    def _detect_boolop_chain_start(self, block: BasicBlock, claimed: Set[BasicBlock]) -> Optional[List[Tuple[BasicBlock, str]]]:
        if block in claimed:
            return None
        last_instr = block.get_last_instruction()
        if not last_instr:
            return None
        if last_instr.opname in SHORT_CIRCUIT_JUMP_OPS:
            chain = self._detect_boolop_short_circuit_chain(block)
            if chain is None or len(chain) < 2:
                return None
            return chain
        if last_instr.opname in FORWARD_CONDITIONAL_JUMP_OPS:
            chain = self._detect_boolop_conditional_chain(block, claimed)
            if chain is None or len(chain) < 2:
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
        while current and current.start_offset not in visited:
            visited.add(current.start_offset)
            last = current.get_last_instruction()
            if not last or last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
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
                if op_type == 'and' and first_jump_target and cur_jump_target and first_jump_target != cur_jump_target:
                    break
                if op_type == 'or' and first_jump_target and cur_jump_target and first_jump_target != cur_jump_target:
                    break
            current = ft_succ
        if len(chain) < 2:
            return None
        first_last = chain[0][0].get_last_instruction()
        first_jt = self.cfg.get_block_by_offset(first_last.argval) if first_last and first_last.argval is not None else None
        if first_jt is None:
            return None
        all_same_target = True
        for cb, cop in chain:
            cl = cb.get_last_instruction()
            if not cl or cl.argval is None:
                all_same_target = False
                break
            cjt = self.cfg.get_block_by_offset(cl.argval)
            if cjt != first_jt:
                all_same_target = False
                break
        if not all_same_target:
            unified_chain = self._try_unify_mixed_boolop_chain(chain, first_jt)
            if unified_chain and len(unified_chain) >= 2:
                return unified_chain
            return None
        return chain

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
        if not ft_last or ft_last.opname not in FORWARD_CONDITIONAL_JUMP_OPS:
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
                if not self.dom_analyzer.dominates(prev_block, current):
                    break
            current = ft_succ
        return chain if len(chain) >= 2 else None

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
            best_parent = None
            best_end = float('inf')

            for j in range(i - 1, -1, -1):
                candidate = sorted_regions[j]
                ps, pe = ranges[id(candidate)]
                if ps <= cs and pe >= ce and pe < best_end:
                    best_parent = candidate
                    best_end = pe

            if best_parent is not None and best_parent is not child and child not in best_parent.children:
                best_parent.add_child(child)

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
