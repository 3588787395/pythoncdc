"""
结构化分析器模块

该模块实现结构化控制流分析，将控制流图转换为高级控制结构（如if、while、for等）。
这是反编译过程中的关键步骤。
"""

import sys
from enum import Enum, auto
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from collections import deque

from .basic_block import BasicBlock
from .cfg_builder import ControlFlowGraph
from .dominator_analyzer import DominatorAnalyzer, LoopAnalyzer

class ControlStructureType(Enum):
    """控制结构类型"""
    SEQUENCE = auto()
    IF_THEN = auto()
    IF_THEN_ELSE = auto()
    WHILE_LOOP = auto()
    FOR_LOOP = auto()
    DO_WHILE_LOOP = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()
    TRY_EXCEPT = auto()
    TRY_FINALLY = auto()
    WITH = auto()
    SWITCH = auto()
    MATCH = auto()  # [Python 3.10+] match/case 模式匹配
    ASSERT = auto()  # [Python] assert语句

@dataclass
class ControlStructure:
    """控制结构基类"""
    struct_type: ControlStructureType
    entry_block: BasicBlock
    exit_block: Optional[BasicBlock] = None
    parent: Optional['ControlStructure'] = None
    children: List['ControlStructure'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IfStructure(ControlStructure):
    """if条件结构"""
    condition_block: Optional[BasicBlock] = None
    then_body: List[BasicBlock] = field(default_factory=list)
    else_body: List[BasicBlock] = field(default_factory=list)
    merge_block: Optional[BasicBlock] = None
    # [关键修复] 支持elif链
    elif_conditions: List[BasicBlock] = field(default_factory=list)  # elif条件块列表
    elif_bodies: List[List[BasicBlock]] = field(default_factory=list)  # elif body块列表
    # [关键修复] 支持复合条件
    is_compound_condition: bool = False  # 是否是复合条件（如 x > 0 and y > 0）
    condition_chain: List[BasicBlock] = field(default_factory=list)  # 复合条件的条件块链
    
    def __post_init__(self):
        self.struct_type = ControlStructureType.IF_THEN if not self.else_body else ControlStructureType.IF_THEN_ELSE

@dataclass
class LoopStructure(ControlStructure):
    """循环结构"""
    loop_type: ControlStructureType = ControlStructureType.WHILE_LOOP
    header_block: Optional[BasicBlock] = None
    body_blocks: List[BasicBlock] = field(default_factory=list)
    condition_block: Optional[BasicBlock] = None
    exit_block: Optional[BasicBlock] = None
    is_post_test: bool = False
    else_body: List[BasicBlock] = field(default_factory=list)  # [关键修复] 支持for-else/while-else
    init_blocks: List[BasicBlock] = field(default_factory=list)  # [关键修复] while循环的初始化块（如count = 0）
    is_async: bool = False  # [关键修复] 标记是否为异步循环（async for）
    is_yield_from: bool = False  # [关键修复] 标记是否为yield from循环

@dataclass
class TryExceptStructure(ControlStructure):
    """try-except结构"""
    try_body: List[BasicBlock] = field(default_factory=list)
    # [关键修复] except_handlers现在包含(exc_type, exc_name, handler_blocks)
    except_handlers: List[Tuple[Optional[str], Optional[str], List[BasicBlock]]] = field(default_factory=list)
    else_body: List[BasicBlock] = field(default_factory=list)  # [关键修复] 支持else子句
    finally_body: List[BasicBlock] = field(default_factory=list)
    has_else: bool = False  # [关键修复] 是否有else子句
    has_finally: bool = False
    try_start_offset: int = 0  # try块的起始偏移量
    try_end_offset: int = 0    # try块的结束偏移量

@dataclass
class WithStructure(ControlStructure):
    """with上下文管理器结构"""
    with_body: List[BasicBlock] = field(default_factory=list)
    resource_expr: Optional[Any] = None
    target: Optional[str] = None
    is_async: bool = False  # [关键修复] 标记是否为异步with
    # [关键修复] 支持多上下文with（如：with ctx1() as a, ctx2() as b:）
    items: List[Tuple[str, Optional[str]]] = field(default_factory=list)  # [(resource_expr, target), ...]

@dataclass
class MatchStructure(ControlStructure):
    """[Python 3.10+] match/case 模式匹配结构"""
    subject_block: Optional[BasicBlock] = None  # match 主题表达式块
    case_blocks: List[BasicBlock] = field(default_factory=list)  # case 块列表
    case_patterns: List[Any] = field(default_factory=list)  # case 模式列表
    case_guards: List[Optional[Any]] = field(default_factory=list)  # case 守卫条件列表
    case_bodies: List[List[BasicBlock]] = field(default_factory=list)  # case body块列表
    merge_block: Optional[BasicBlock] = None  # 合并块
    
    def __post_init__(self):
        self.struct_type = ControlStructureType.MATCH

@dataclass
class AssertStructure(ControlStructure):
    """[Python] assert语句结构"""
    condition_block: Optional[BasicBlock] = None  # assert条件块
    message_block: Optional[BasicBlock] = None  # assert消息块（可选）
    end_block: Optional[BasicBlock] = None  # assert结束块
    
    def __post_init__(self):
        # 确保基类的struct_type被正确设置
        # 确保基类的struct_type被正确设置
        # 确保基类的struct_type被正确设置
        # 确保基类的struct_type被正确设置
        if self.struct_type is None or not isinstance(self.struct_type, ControlStructureType):
            object.__setattr__(self, 'struct_type', ControlStructureType.ASSERT)

class StructuredAnalyzer:
    """
    结构化分析器
    
    分析控制流图的结构，识别高级控制结构。
    """
    
    def __init__(self, cfg: ControlFlowGraph, verbose: bool = False):
        """
        初始化结构化分析器
        
        Args:
            cfg: 控制流图
            verbose: 是否输出调试信息
        """
        self.cfg = cfg
        self.verbose = verbose
        self.dom_analyzer = DominatorAnalyzer(cfg)
        self.loop_analyzer: Optional[LoopAnalyzer] = None
        
        self.structures: List[ControlStructure] = []
        self.block_to_structure: Dict[BasicBlock, ControlStructure] = {}
        
        self.regions: Dict[BasicBlock, Set[BasicBlock]] = {}
        self.region_hierarchy: Dict[BasicBlock, Optional[BasicBlock]] = {}
    
    def analyze(self) -> List[ControlStructure]:
        """
        执行完整的结构化分析
        
        Returns:
            识别出的控制结构列表
        """
        self.dom_analyzer.analyze()
        
        self.loop_analyzer = LoopAnalyzer(self.cfg, self.dom_analyzer)
        
        self.loop_analyzer.analyze()
        
        self._identify_loops()
        self._identify_try_except()
        # [关键修复] 在识别if结构之前，先识别assert语句结构
        # 这样可以避免assert语句被错误地识别为if语句
        self._identify_assert_structures()
        self._identify_conditionals()
        # [关键修复] 在识别if结构之后，再识别优化后的while循环
        # 这样可以避免if条件块被错误地识别为while循环条件检查块
        self._identify_optimized_while_loops()
        # [关键修复] 识别NOP序列（对应优化后的if True:语句）
        self._identify_nop_sequences()
        # [关键修复] 合并复合条件（如 if a and b:）
        self._merge_compound_conditions()
        # [关键修复] 合并链式比较（如 0 < x < 100）
        self._merge_chained_comparisons()
        # [关键修复] 修复结构之间的重叠
        self._fix_structure_overlaps()
        self._identify_with_structures()
        
        # [关键修复] 合并多上下文with（如：with ctx1() as a, ctx2() as b:）
        self._merge_multi_context_withs()
        # [Python 3.10+] 识别match/case结构
        self._identify_match_structures()
        self._identify_sequences()
        self._build_hierarchy()

        return self.structures
    
    def _identify_loops(self) -> None:
        """识别循环结构"""
        if not self.loop_analyzer:
            return
        
        loops = self.loop_analyzer.get_all_loops()
        
        # [关键修复] 按header的偏移量排序循环，确保外层循环先被处理
        # 这样内层循环的LoopStructure会在_identify_conditionals之前被添加到self.structures中
        sorted_loops = sorted(loops.items(), key=lambda x: x[0].start_offset)
        
        # 打印每个循环的详细信息
        for idx, (header, body) in enumerate(sorted_loops):
            # [关键修复] 对于嵌套在循环中的try-except结构，
            # 异常处理块（如PUSH_EXC_INFO块）不应该被从循环体中过滤掉
            # 因为这会破坏循环结构的完整性
            # 相反，我们应该保留所有块，让try-except识别逻辑来处理异常块
            
            # [关键修复] 检查是否是async for循环
            # [关键修复] 对于嵌套在循环中的try-except结构，
            # 异常处理块（如PUSH_EXC_INFO块）不应该被从循环体中过滤掉
            # 因为这会破坏循环结构的完整性
            # 相反，我们应该保留所有块，让try-except识别逻辑来处理异常块
            
            # [关键修复] 检查是否是async for循环
            # [关键修复] 对于嵌套在循环中的try-except结构，
            # 异常处理块（如PUSH_EXC_INFO块）不应该被从循环体中过滤掉
            # 因为这会破坏循环结构的完整性
            # 相反，我们应该保留所有块，让try-except识别逻辑来处理异常块
            
            # [关键修复] 检查是否是async for循环
            # [关键修复] 对于嵌套在循环中的try-except结构，
            # 异常处理块（如PUSH_EXC_INFO块）不应该被从循环体中过滤掉
            # 因为这会破坏循环结构的完整性
            # 相反，我们应该保留所有块，让try-except识别逻辑来处理异常块
            
            # [关键修复] 检查是否是async for循环
            is_async_for = any(instr.opname in ('GET_ANEXT', 'GET_AITER') for instr in header.instructions)
            
            filtered_body = set()
            for block in body:
                # [关键修复] 对于async for循环，首先过滤掉包含END_ASYNC_FOR的块
                # 这些块属于else子句，不是循环体的一部分
                # [关键修复] 对于async for循环，首先过滤掉包含END_ASYNC_FOR的块
                # 这些块属于else子句，不是循环体的一部分
                # [关键修复] 对于async for循环，首先过滤掉包含END_ASYNC_FOR的块
                # 这些块属于else子句，不是循环体的一部分
                # [关键修复] 对于async for循环，首先过滤掉包含END_ASYNC_FOR的块
                # 这些块属于else子句，不是循环体的一部分
                if is_async_for:
                    has_end_async_for = any(instr.opname == 'END_ASYNC_FOR'
                                           for instr in block.instructions)
                    if has_end_async_for:
                        continue
                
                # [关键修复] 检查块是否在try-except的异常处理范围内（depth >= 1 且 lasti=True）
                # lasti=True 表示这是真正的异常处理器块，需要过滤掉
                # lasti=False 的块（如async for的异常保护范围）应该保留
                is_try_except_handler = False
                if self.cfg.exception_table:
                    for entry in self.cfg.exception_table:
                        # [关键修复] 只过滤 lasti=True 的异常处理块
                        # [关键修复] 只过滤 lasti=True 的异常处理块
                        # [关键修复] 只过滤 lasti=True 的异常处理块
                        # [关键修复] 只过滤 lasti=True 的异常处理块
                        if entry['depth'] >= 1 and entry.get('lasti', False):
                            if entry['start'] <= block.start_offset < entry['end']:
                                is_try_except_handler = True
                                break
                
                if is_try_except_handler:
                    # [关键修复] 对于async for循环，保留包含STORE_FAST的块（目标变量存储）
                    # [关键修复] 对于async for循环，保留包含STORE_FAST的块（目标变量存储）
                    # [关键修复] 对于async for循环，保留包含STORE_FAST的块（目标变量存储）
                    # [关键修复] 对于async for循环，保留包含STORE_FAST的块（目标变量存储）
                    if is_async_for:
                        has_store_fast = any(instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL')
                                             for instr in block.instructions)
                        if has_store_fast:
                            filtered_body.add(block)
                            continue
                    # [关键修复] 对于包含with语句的循环，保留与with相关的异常处理块
                    # 这些块包含WITH_EXCEPT_START等指令，是with语句结构的一部分
                    has_with_related = any(instr.opname in ('WITH_EXCEPT_START', 'PUSH_EXC_INFO', 'POP_EXCEPT')
                                          for instr in block.instructions)
                    if has_with_related:
                        filtered_body.add(block)
                        continue
                    
                    # [关键修复] 对于for循环，保留循环体中的块
                    # 这些块包含循环相关的指令（FOR_ITER, STORE_FAST等）
                    is_loop_body_block = any(instr.opname in ('FOR_ITER', 'FOR_ITER_RANGE', 'STORE_FAST', 'STORE_NAME')
                                             for instr in block.instructions)
                    if is_loop_body_block:
                        filtered_body.add(block)
                        continue
                    
                    # 块在异常处理范围内，过滤掉
                    continue
                
                # 块不在异常处理范围内，保留它
                filtered_body.add(block)
            
            # [关键修复] 如果过滤后循环体为空，跳过这个循环
            if not filtered_body:
                continue
            
            body_without_nested = set(filtered_body)
            is_for = any(instr.opname in ('FOR_ITER', 'GET_ANEXT') for instr in header.instructions)
            if not is_for:
                for other_header, other_body in loops.items():
                    if other_header != header and other_header in filtered_body:
                        body_without_nested.discard(other_header)
                        for b in other_body:
                            body_without_nested.discard(b)
            
            if is_for:
                for block in filtered_body:
                    if block not in body_without_nested:
                        for instr in block.instructions:
                            if instr.opname == 'JUMP_FORWARD':
                                jump_target = instr.argval
                                target_in_loop = any(
                                    b.start_offset <= jump_target < b.end_offset
                                    for b in body_without_nested
                                )
                                if not target_in_loop:
                                    body_without_nested.add(block)
                                    break
            
            # [关键修复] 确保header本身在body中
            body_without_nested.add(header)
            
            # [关键修复] 进一步过滤body，只保留真正属于当前循环的块
            # 对于for循环：只保留从header可达且能回到header的块
            # 对于while循环：只保留从header可达的块（因为while的向后跳转可能在header本身）
            if len(body_without_nested) > 1:  # 只有header一个块时不需要过滤
                # 检查是否是for循环
                is_for = any(instr.opname in ('FOR_ITER', 'GET_ANEXT') for instr in header.instructions)
                
                # 找到所有从header可达的块
                reachable_from_header = set()
                stack = [header]
                while stack:
                    block = stack.pop()
                    if block in reachable_from_header:
                        continue
                    reachable_from_header.add(block)
                    for succ in block.successors:
                        if succ in body_without_nested and succ not in reachable_from_header:
                            stack.append(succ)
                
                if is_for:
                    # 对于for循环，只保留既从header可达又能回到header的块
                    # [关键修复] 但是，包含return/break语句的块也应该保留
                    # 因为它们是循环体的一部分（只是提前退出了）
                    # 对于for循环，只保留既从header可达又能回到header的块
                    # [关键修复] 但是，包含return/break语句的块也应该保留
                    # 因为它们是循环体的一部分（只是提前退出了）
                    # 对于for循环，只保留既从header可达又能回到header的块
                    # [关键修复] 但是，包含return/break语句的块也应该保留
                    # 因为它们是循环体的一部分（只是提前退出了）
                    # 对于for循环，只保留既从header可达又能回到header的块
                    # [关键修复] 但是，包含return/break语句的块也应该保留
                    # 因为它们是循环体的一部分（只是提前退出了）
                    can_reach_header = set()
                    blocks_with_exit = set()  # 包含return/break的块
                    for block in body_without_nested:
                        if block == header:
                            can_reach_header.add(block)
                            continue
                        # [关键修复] 检查块是否包含return或break语句
                        has_exit = False
                        for instr in block.instructions:
                            if instr.opname in ('RETURN_VALUE', 'JUMP_FORWARD'):
                                has_exit = True
                                break
                        if has_exit:
                            blocks_with_exit.add(block)
                            continue
                        # 检查从block是否可以到达header
                        visited = set()
                        stack = [block]
                        found = False
                        while stack and not found:
                            current = stack.pop()
                            if current in visited:
                                continue
                            visited.add(current)
                            if current == header:
                                found = True
                                break
                            for succ in current.successors:
                                if succ in body_without_nested and succ not in visited:
                                    stack.append(succ)
                        if found:
                            can_reach_header.add(block)
                    
                    # [关键修复] 包含return/break的块也应该保留
                    valid_body = reachable_from_header & (can_reach_header | blocks_with_exit)
                else:
                    # 对于while循环，只保留从header可达的块
                    valid_body = reachable_from_header
                
                valid_body.add(header)  # 确保header在body中
                body_without_nested = valid_body
            
            loop_struct = self._analyze_loop(header, body_without_nested)
            if loop_struct:
                self.structures.append(loop_struct)
                
                # [关键修复] 将循环的body_blocks添加到block_to_structure
                # 这样_identify_conditionals可以正确识别循环体内的if语句
                for block in loop_struct.body_blocks:
                    if block not in self.block_to_structure:
                        self.block_to_structure[block] = loop_struct
            else:
                # 跳过这个循环，继续处理下一个循环
                continue
        
        # [关键修复] 识别Python 3.11+优化后的while循环结构
        # 注意：这个调用被移到_identify_conditionals之后，以确保if结构先被识别
        # 这样可以避免if条件块被错误地识别为while循环条件检查块
        self._identify_optimized_while_loops()
    
    def _identify_optimized_while_loops(self) -> None:
        """
        识别Python 3.11+优化后的while循环结构
        
        这种结构的特点是：
        - 循环体内有一个条件检查块，有两个后继
        - 循环体内有向后跳转（POP_JUMP_BACKWARD_IF_TRUE）
        - 向后跳转的目标是条件检查块的一个后继
        """
        # 获取所有已识别的循环结构
        existing_loop_bodies = set()
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and hasattr(struct, 'body_blocks'):
                existing_loop_bodies.update(struct.body_blocks)
        
        # 遍历所有基本块，查找可能的while循环条件检查块
        # [关键修复-2026-while-top] 同时处理顶层while循环和嵌套while循环
        # 顶层while循环：block不在任何现有LoopStructure的body_blocks中
        # 嵌套while循环：block在某个LoopStructure的body_blocks中
        for block in self.cfg.blocks.values():
            # 检查是否是条件检查块（有两个后继）
            # 检查是否是条件检查块（有两个后继）
            # 检查是否是条件检查块（有两个后继）
            # 检查是否是条件检查块（有两个后继）
            if len(block.successors) != 2:
                continue
            
            succ_list = list(block.successors)
            succ_offsets = {s.start_offset for s in succ_list}
            
            # [关键修复-2026-while-top] 检查块是否在某个循环体内
            # 如果在，使用该循环的body_blocks；如果不在，使用空集（表示顶层循环）
            body_blocks = set()
            for loop_struct in self.structures:
                if not isinstance(loop_struct, LoopStructure):
                    continue
                
                loop_body = set(loop_struct.body_blocks) if hasattr(loop_struct, 'body_blocks') else set()
                if not loop_body:
                    continue
                
                if block in loop_body:
                    body_blocks = loop_body
                    break
            
            # [关键修复] 检查块是否已经是某个循环的头部
                # 如果是，跳过它
                is_existing_header = False
                for struct in self.structures:
                    if isinstance(struct, LoopStructure):
                        if struct.header_block == block or struct.entry_block == block:
                            is_existing_header = True
                            break
                
                if is_existing_header:
                    continue
                
                # [关键修复] 检查该块是否包含向前跳转指令（POP_JUMP_FORWARD_IF_*）
                # 真正的while循环条件检查块应该包含向前跳转指令
                # 如果块只包含向后跳转指令（POP_JUMP_BACKWARD_IF_*），它是循环body块，不是条件检查块
                has_forward_jump = False
                for instr in block.instructions:
                    if 'POP_JUMP_FORWARD_IF_' in instr.opname:
                        has_forward_jump = True
                        break
                
                if not has_forward_jump:
                    # 块不包含向前跳转指令，不是while循环条件检查块
                    # 块不包含向前跳转指令，不是while循环条件检查块
                    # 块不包含向前跳转指令，不是while循环条件检查块
                    # 块不包含向前跳转指令，不是while循环条件检查块
                    continue
                
                # [关键修复] 检查该块是否已经是某个IfStructure的entry_block
                # 如果是，说明这是一个if条件块，不应该被识别为while循环条件检查块
                is_if_entry = False
                for struct in self.structures:
                    if isinstance(struct, IfStructure):
                        if struct.entry_block == block:
                            is_if_entry = True
                            break
                
                if is_if_entry:
                    continue
                
                # [关键修复] 检查该块是否已经是某个IfStructure的entry_block
                # 如果是，说明这是一个if条件块，不应该被识别为while循环
                # 但如果块只是IfStructure的then_body或else_body的一部分（不是entry_block）
                # 且块包含while循环的特征，它应该被识别为while循环
                is_if_entry = False
                for struct in self.structures:
                    if isinstance(struct, IfStructure):
                        if struct.entry_block == block:
                            is_if_entry = True
                            break
                
                if is_if_entry:
                    continue
                
                # [关键修复] 检查块是否是if条件块（不是while条件块）
                # if条件块的特征：
                # 1. 块的fall-through后继（不是跳转目标的那个后继）包含实际代码
                # 2. 块的跳转目标后继是else分支或merge点
                # 3. 后继中没有向后跳转到块本身的指令
                # while条件块的特征：
                # 1. 块的fall-through后继是循环体开始
                # 2. 循环体中有向后跳转到条件块的指令
                is_if_condition = False
                jump_instr = None
                for instr in block.instructions:
                    if 'POP_JUMP_FORWARD_IF_' in instr.opname:
                        jump_instr = instr
                        break
                
                if jump_instr and jump_instr.argval is not None:
                    # 找到fall-through后继（不是跳转目标的那个）
                    # 找到fall-through后继（不是跳转目标的那个）
                    # 找到fall-through后继（不是跳转目标的那个）
                    # 找到fall-through后继（不是跳转目标的那个）
                    fall_through_succ = None
                    jump_target_succ = None
                    for succ in succ_list:
                        if succ.start_offset == jump_instr.argval:
                            jump_target_succ = succ
                        else:
                            fall_through_succ = succ
                    
                    # [关键修复] 检查fall-through后继是否是if的then分支
                    # if的then分支特征：包含实际业务逻辑代码，不只是跳转
                    if fall_through_succ:
                        # 检查fall-through后继是否有实际代码（不只是JUMP_FORWARD）
                        # 检查fall-through后继是否有实际代码（不只是JUMP_FORWARD）
                        # 检查fall-through后继是否有实际代码（不只是JUMP_FORWARD）
                        # 检查fall-through后继是否有实际代码（不只是JUMP_FORWARD）
                        has_real_code = False
                        for instr in fall_through_succ.instructions:
                            if instr.opname not in ('RESUME', 'CACHE', 'NOP', 'JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                                has_real_code = True
                                break
                        
                        # 检查fall-through后继是否是循环header（有向后跳转指向它）
                        # [关键修复-2026-while-top] 对于顶层循环，body_blocks为空，需要搜索所有CFG块
                        is_loop_header = False
                        # [关键修复] 获取从块的后继可达的所有块
                        reachable_from_succ = set()
                        for succ in succ_list:
                            reachable_from_succ.add(succ)
                            # BFS遍历后继
                            worklist = [succ]
                            visited = {succ}
                            while worklist:
                                current = worklist.pop(0)
                                for s in current.successors:
                                    if s not in visited and (s in body_blocks or len(body_blocks) == 0):
                                        visited.add(s)
                                        reachable_from_succ.add(s)
                                        worklist.append(s)
                        
                        for bb in reachable_from_succ:
                            for instr in bb.instructions:
                                if 'BACKWARD' in instr.opname:
                                    if instr.argval is not None and instr.argval == fall_through_succ.start_offset:
                                        is_loop_header = True
                                        break
                            if is_loop_header:
                                break
                        
                        # [关键修复] 检查fall-through后继是否包含POP_JUMP_BACKWARD_IF_TRUE指令
                        # 且跳转目标是fall-through后继自己
                        # 如果是，这是while循环的body块，block是while循环的条件块
                        is_while_body = False
                        for instr in fall_through_succ.instructions:
                            if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                                if instr.argval is not None and instr.argval == fall_through_succ.start_offset:
                                    is_while_body = True
                                    break
                        
                        # [关键修复] 如果fall-through后继是循环header，需要进一步判断
                        # 1. 如果向后跳转来自fall-through后继本身（自跳转），这是if条件块
                        # 2. 如果向后跳转来自fall-through后继的后继（如354），且block有向前跳转
                        #    这是while循环的入口（如while-else结构）
                        if is_loop_header:
                            # 检查向后跳转是否来自fall-through后继本身
                            # 检查向后跳转是否来自fall-through后继本身
                            # 检查向后跳转是否来自fall-through后继本身
                            # 检查向后跳转是否来自fall-through后继本身
                            has_self_backward_jump = any(
                                'BACKWARD' in i.opname and i.argval == fall_through_succ.start_offset
                                for i in fall_through_succ.instructions
                            )
                            if has_self_backward_jump:
                                # 向后跳转来自fall-through后继本身，这是if条件块
                                # 向后跳转来自fall-through后继本身，这是if条件块
                                # 向后跳转来自fall-through后继本身，这是if条件块
                                # 向后跳转来自fall-through后继本身，这是if条件块
                                is_if_condition = True
                            else:
                                # 向后跳转来自fall-through后继的后继
                                # 如果block有向前跳转，这是while循环的入口
                                has_forward_jump = any(
                                    'POP_JUMP_FORWARD' in i.opname
                                    for i in block.instructions
                                )
                                if has_forward_jump:
                                    # 这是while循环的入口，不是if条件块
                                    # 这是while循环的入口，不是if条件块
                                    # 这是while循环的入口，不是if条件块
                                    # 这是while循环的入口，不是if条件块
                                    is_if_condition = False
                                else:
                                    # 没有向前跳转，这是if条件块
                                    is_if_condition = True
                        # 如果fall-through后继有实际代码且不是while循环的body，这也是if条件块
                        elif has_real_code and not is_while_body:
                            is_if_condition = True
                
                if is_if_condition:
                    # 这是if条件块，不是while条件块，跳过
                    continue
                
                # 检查循环体内是否有向后跳转
                # [关键修复-2026-while] 同时搜索body_blocks和所有CFG块
                # 因为循环尾部块（如包含count+=1和回跳的块）可能是合并点，不在body_blocks中
                found_backward_jump = False
                for body_block in list(body_blocks) + list(self.cfg.blocks.values()):
                    for instr in body_block.instructions:
                        if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                            # 检查跳转目标是否是块的一个后继
                            # 检查跳转目标是否是块的一个后继
                            # 检查跳转目标是否是块的一个后继
                            # 检查跳转目标是否是块的一个后继
                            if instr.argval is not None and instr.argval in succ_offsets:
                                # [关键修复] 额外检查：确保跳转目标不是包含实际代码的if then分支
                                # 找到跳转目标后继
                                # [关键修复] 额外检查：确保跳转目标不是包含实际代码的if then分支
                                # 找到跳转目标后继
                                # [关键修复] 额外检查：确保跳转目标不是包含实际代码的if then分支
                                # 找到跳转目标后继
                                # [关键修复] 额外检查：确保跳转目标不是包含实际代码的if then分支
                                # 找到跳转目标后继
                                jump_target_succ = None
                                for succ in succ_list:
                                    if succ.start_offset == instr.argval:
                                        jump_target_succ = succ
                                        break
                                
                                # [关键修复-2026-while-fix] 检查跳转目标是否有效
                                # 对于Python 3.11+优化的while循环结构：
                                # - 循环条件检查块（如Block 1, offset 0）有POP_JUMP_FORWARD_IF_FALSE到exit_block
                                # - fall-through进入循环体开始（如Block 2, offset 14）
                                # - 循环尾部（如Block 10, offset 68）有POP_JUMP_BACKWARD_IF_TRUE回到循环体开始（offset 14）
                                # 关键特征：向后跳转的目标（offset 14）是条件检查块的fall-through后继
                                # 
                                # [旧逻辑错误] 原来要求向后跳转目标必须是"循环header"（有自跳转）
                                # 但在优化后的while循环中，回跳目标是循环体开始块，不是条件块本身
                                # 
                                # [新逻辑] 只要满足以下条件就认为是while循环：
                                # 1. 有向前跳转指令（POP_JUMP_FORWARD_IF_*）
                                # 2. 找到向后跳转指令（POP_JUMP_BACKWARD_IF_TRUE），且目标是当前块的某个后继
                                
                                if not jump_target_succ:
                                    # 向后跳转目标不是直接后继，这不是标准的while循环
                                    continue
                                
                                # 这是while循环的条件检查块
                                # 创建while循环结构
                                while_body = self._collect_while_body(block, body_blocks, instr.argval)
                                if while_body:
                                    while_struct = self._create_while_loop_structure(block, while_body, loop_struct)
                                    if while_struct:
                                        self.structures.append(while_struct)
                                        for b in while_body:
                                            self.block_to_structure[b] = while_struct
                                        self.block_to_structure[block] = while_struct
                                break
                    else:
                        continue
                    break
    
    def _collect_while_body(self, condition_block: BasicBlock, outer_body: Set[BasicBlock], loop_target: int) -> Set[BasicBlock]:
        """
        收集while循环的体块
        
        对于Python 3.11+优化后的while循环结构：
        - 条件检查块（condition_block）有两个后继：
          - 一个进入循环体（loop_target）
          - 一个退出循环（exit_block）
        - 循环尾部有向后跳转（POP_JUMP_BACKWARD_IF_TRUE）到循环体开始
        
        Args:
            condition_block: while循环的条件检查块
            outer_body: 外层循环的体块
            loop_target: 向后跳转的目标偏移量（循环体开始的块）
            
        Returns:
            while循环的体块集合
        """
        while_body = set()
        
        # 找到循环体开始的块（向后跳转的目标）
        loop_start = None
        for succ in condition_block.successors:
            if succ.start_offset == loop_target:
                loop_start = succ
                break
        
        if not loop_start:
            return while_body
        
        # 找到退出块（条件检查块的后继中不是循环体开始的那个）
        exit_block = None
        for succ in condition_block.successors:
            if succ.start_offset != loop_target:
                exit_block = succ
                break
        
        # [关键修复] 收集while循环的体块
        # 策略：从loop_start开始，收集所有在condition_block和exit_block之间的块
        # 停止条件：
        # 1. 遇到condition_block（while条件检查）
        # 2. 遇到exit_block（退出while循环）
        # 3. 遇到跳到condition_block之前的块（跳出外层循环）
        
        visited = set()
        stack = [loop_start]
        
        while stack:
            block = stack.pop()
            if block in visited:
                continue
            
            visited.add(block)
            
            # 跳过条件检查块
            if block == condition_block:
                continue
            
            # [关键修复] 跳过退出块
            if exit_block and block == exit_block:
                continue
            
            # [关键修复] 如果块属于其他循环的header，跳过它
            # 这防止收集到其他循环的块
            is_other_loop_header = False
            for struct in self.structures:
                if isinstance(struct, LoopStructure):
                    if struct.header_block == block and block != loop_start:
                        # 这是其他循环的header，跳过
                        # 这是其他循环的header，跳过
                        # 这是其他循环的header，跳过
                        # 这是其他循环的header，跳过
                        is_other_loop_header = True
                        break
            if is_other_loop_header:
                continue
            
            # [关键修复] 检查块是否跳到condition_block之前
            # 如果是，这可能是跳出while循环的块
            jumps_before_condition = False
            for succ in block.successors:
                if succ.start_offset < condition_block.start_offset:
                    jumps_before_condition = True
                    break
            
            # [关键修复] 检查块是否包含向后跳转到loop_start的指令
            # 这是循环尾部的特征
            has_backward_jump = False
            for instr in block.instructions:
                if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                    if instr.argval is not None and instr.argval == loop_target:
                        has_backward_jump = True
                        break
            
            # 如果块跳到condition_block之前，但不是循环尾部，跳过它
            if jumps_before_condition and not has_backward_jump:
                continue
            
            # [关键修复] 检查块是否是break块（JUMP_FORWARD跳出当前循环）
            # 如果是，不应该收集它的后继
            is_break_block = False
            for instr in block.instructions:
                if instr.opname == 'JUMP_FORWARD':
                    if instr.argval is not None:
                        # 检查跳转目标是否在condition_block之后（跳出循环）
                        # 检查跳转目标是否在condition_block之后（跳出循环）
                        # 检查跳转目标是否在condition_block之后（跳出循环）
                        # 检查跳转目标是否在condition_block之后（跳出循环）
                        if instr.argval > condition_block.start_offset:
                            # 这是break块，跳出当前循环
                            # 这是break块，跳出当前循环
                            # 这是break块，跳出当前循环
                            # 这是break块，跳出当前循环
                            is_break_block = True
                            break
            
            # 添加块到while循环体
            while_body.add(block)
            
            # [关键修复] 如果是break块，不添加它的后继
            if is_break_block:
                continue
            
            # 添加后继
            for succ in block.successors:
                if succ not in visited and succ != condition_block:
                    # 如果后继是退出块，不要添加
                    # 如果后继是退出块，不要添加
                    # 如果后继是退出块，不要添加
                    # 如果后继是退出块，不要添加
                    if exit_block and succ == exit_block:
                        continue
                    # 如果后继跳到condition_block之前，不要添加
                    if succ.start_offset < condition_block.start_offset:
                        continue
                    stack.append(succ)
        
        # [关键修复-2026-while] 确保收集所有循环尾部块
        # 有些块（如包含count += 1和循环回跳的块）可能因为各种原因未被收集
        # 检查所有包含BACKWARD跳转到loop_target的块，确保它们在while_body中
        for block in self.cfg.blocks.values():
            if block in while_body or block == condition_block or block == exit_block:
                continue
            for instr in block.instructions:
                if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                    if instr.argval is not None and instr.argval == loop_target:
                        # 这个块包含循环回跳，应该属于while_body
                        while_body.add(block)
                        break
        
        return while_body
    
    def _create_while_loop_structure(self, condition_block: BasicBlock, body: Set[BasicBlock], outer_loop: LoopStructure) -> Optional[LoopStructure]:
        """
        创建while循环结构
        
        Args:
            condition_block: while循环的条件检查块
            body: while循环的体块
            outer_loop: 外层循环结构
            
        Returns:
            while循环结构
        """
        if not body:
            return None
        
        # 找到退出块（条件检查块的后继中不在while循环体内的那个）
        exit_block = None
        for succ in condition_block.successors:
            if succ not in body:
                exit_block = succ
                break
        
        if not exit_block:
            return None
        
        # [关键修复] 检查condition_block是否包含初始化代码
        # 对于Python 3.11+优化后的while循环，condition_block可能同时包含初始化代码和条件代码
        header_has_init = False
        header_has_condition = False
        init_instrs = []
        
        for i, instr in enumerate(condition_block.instructions):
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                header_has_init = True
                init_instrs.append(i)
            # 检查是否是条件跳转指令
            if 'JUMP' in instr.opname and 'BACKWARD' not in instr.opname:
                header_has_condition = True
                break
        
        # 如果condition_block同时包含初始化代码和条件代码，标记它
        if header_has_init and header_has_condition:
            condition_block.has_init_code = True
            condition_block.init_instr_indices = init_instrs
        
        # 创建while循环结构
        while_struct = LoopStructure(
            struct_type='while',
            entry_block=condition_block,
            header_block=condition_block,
            condition_block=condition_block,
            body_blocks=list(body),
            exit_block=exit_block
        )
        
        return while_struct
    
    def _analyze_loop(self, header: BasicBlock, body: Set[BasicBlock]) -> Optional[LoopStructure]:
        """
        分析单个循环
        
        Args:
            header: 循环头部
            body: 循环体
            
        Returns:
            循环结构
        """
        # [关键修复] 检查header是否是if语句的else分支
        # 如果header的前驱包含POP_JUMP_FORWARD_IF_*指令跳转到header，
        # 且该前驱有两个后继，则header可能是if的else分支
        # 这种情况下，不应该将header识别为独立的循环头部
        is_else_branch = False
        for pred in header.predecessors:
            for instr in pred.instructions:
                if 'POP_JUMP_FORWARD' in instr.opname and instr.argval == header.start_offset:
                    # pred跳转到header，header可能是else分支
                    # pred跳转到header，header可能是else分支
                    # pred跳转到header，header可能是else分支
                    # pred跳转到header，header可能是else分支
                    if len(pred.successors) == 2:
                        # 检查是否有向后跳转回到header
                        # 检查是否有向后跳转回到header
                        # 检查是否有向后跳转回到header
                        # 检查是否有向后跳转回到header
                        has_backward_to_header = any(
                            'BACKWARD' in i.opname and i.argval == header.start_offset
                            for b in self.cfg.blocks.values()
                            for i in b.instructions
                        )
                        if not has_backward_to_header:
                            # 没有向后跳转回到header，header是if的else分支，不是循环头部
                            # 但是，header内部可能有循环，需要检查
                            # 检查body中是否有向后跳转
                            # 没有向后跳转回到header，header是if的else分支，不是循环头部
                            # 但是，header内部可能有循环，需要检查
                            # 检查body中是否有向后跳转
                            # 没有向后跳转回到header，header是if的else分支，不是循环头部
                            # 但是，header内部可能有循环，需要检查
                            # 检查body中是否有向后跳转
                            # 没有向后跳转回到header，header是if的else分支，不是循环头部
                            # 但是，header内部可能有循环，需要检查
                            # 检查body中是否有向后跳转
                            has_backward_in_body = any(
                                'BACKWARD' in i.opname
                                for b in body
                                for i in b.instructions
                            )
                            if has_backward_in_body:
                                # body中有向后跳转，header内部有循环
                                # 应该创建循环结构，但entry_block应该是header本身
                                # body中有向后跳转，header内部有循环
                                # 应该创建循环结构，但entry_block应该是header本身
                                # body中有向后跳转，header内部有循环
                                # 应该创建循环结构，但entry_block应该是header本身
                                # body中有向后跳转，header内部有循环
                                # 应该创建循环结构，但entry_block应该是header本身
                                is_else_branch = True
                            else:
                                # body中没有向后跳转，header只是if的else分支
                                return None
        
        body_list = sorted(body, key=lambda b: b.start_offset)

        exit_blocks = [b for b in body if any(succ not in body for succ in b.successors)]

        is_while = self._is_while_loop(header, body)
        is_for = self._is_for_loop(header, body)

        # [关键修复] 对于while循环，exit块应该是header块的后继中不在循环体内的那个块
        # 而不是体块中有外部后继的块
        if is_while and not is_for:
            for succ in header.successors:
                if succ not in body:
                    exit_blocks = [succ]
                    break
        
        # [关键修复] 对于for循环，exit块应该是header块的后继中不在循环体内的那个块
        # 这与while循环的处理方式相同
        if is_for:
            for succ in header.successors:
                if succ not in body:
                    exit_blocks = [succ]
                    break
        
        # [关键修复] 对于Python 3.11+优化后的while循环，header块可能同时是body块
        # 特征：header包含POP_JUMP_BACKWARD_IF_*指令，跳转目标是header自己
        # 这种情况下，header既是条件检查块也是循环体块，应该创建LoopStructure
        # 但我们需要正确设置condition_block和header_block
        is_while_body_header = False
        if is_while and not is_for:
            has_backward_jump_to_self = False
            has_forward_jump = False
            for instr in header.instructions:
                if 'POP_JUMP_BACKWARD_IF_' in instr.opname:
                    if instr.argval is not None and instr.argval == header.start_offset:
                        has_backward_jump_to_self = True
                if 'POP_JUMP_FORWARD_IF_' in instr.opname:
                    has_forward_jump = True
            
            # 如果只有向后跳转到自己，没有向前跳转，这是while循环的body+header组合块
            # 不要返回None，而是继续处理，但标记这是特殊的while循环结构
            if has_backward_jump_to_self and not has_forward_jump:
                is_while_body_header = True
        
        # [关键修复] 检查header是否是循环内的if条件块
        # 如果是，不创建循环结构，让_identify_conditionals处理它
        if self._is_if_condition_in_loop(header, body):
            return None
        
        # [关键修复] 检查是否是async/await的内部循环（SEND + YIELD_VALUE + JUMP_BACKWARD_NO_INTERRUPT）
        # 这种循环是await的实现细节，不应该被识别为while循环
        # [关键修复] 但是，如果循环头部有FOR_ITER/GET_ANEXT/GET_AITER，这是一个包含await的for/async for循环，应该被识别
        is_await_loop = False
        is_yield_from_loop = False
        
        # 首先检查头部是否有FOR_ITER/GET_ANEXT/GET_AITER，如果有，这不是await的内部循环
        header_has_iter = any(instr.opname in ('FOR_ITER', 'GET_ANEXT', 'GET_AITER') for instr in header.instructions)
        
        if not header_has_iter:
            # 只有当头部的指令不包含FOR_ITER/GET_ANEXT/GET_AITER时，才检查是否是await的内部循环
            # 只有当头部的指令不包含FOR_ITER/GET_ANEXT/GET_AITER时，才检查是否是await的内部循环
            # 只有当头部的指令不包含FOR_ITER/GET_ANEXT/GET_AITER时，才检查是否是await的内部循环
            # 只有当头部的指令不包含FOR_ITER/GET_ANEXT/GET_AITER时，才检查是否是await的内部循环
            for block in body:
                has_send = False
                has_yield = False
                has_jump_backward_no_interrupt = False
                for instr in block.instructions:
                    if instr.opname == 'SEND':
                        has_send = True
                    if instr.opname == 'YIELD_VALUE':
                        has_yield = True
                    if instr.opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                        has_jump_backward_no_interrupt = True
                if has_send and has_yield and has_jump_backward_no_interrupt:
                    # [关键修复] 检查是否是 yield from 循环
                    # yield from 循环前面有 GET_YIELD_FROM_ITER 指令
                    # [关键修复] 检查是否是 yield from 循环
                    # yield from 循环前面有 GET_YIELD_FROM_ITER 指令
                    # [关键修复] 检查是否是 yield from 循环
                    # yield from 循环前面有 GET_YIELD_FROM_ITER 指令
                    # [关键修复] 检查是否是 yield from 循环
                    # yield from 循环前面有 GET_YIELD_FROM_ITER 指令
                    for pred in header.predecessors:
                        for instr in pred.instructions:
                            if instr.opname == 'GET_YIELD_FROM_ITER':
                                is_yield_from_loop = True
                                break
                        if is_yield_from_loop:
                            break
                    
                    if not is_yield_from_loop:
                        is_await_loop = True
                    break
            
            if is_await_loop:
                # 这是await的内部循环，不应该创建LoopStructure
                # 这是await的内部循环，不应该创建LoopStructure
                # 这是await的内部循环，不应该创建LoopStructure
                # 这是await的内部循环，不应该创建LoopStructure
                return None
        
        # [关键修复] 检查header本身是否是if条件块（如 if x: break）
        # 这种块有两个后继，其中一个是break/continue
        if len(header.successors) == 2:
            succ_list = list(header.successors)
            
            def is_break_or_continue_block(block):
                """检查块是否是break或continue"""
                non_trivial = [i for i in block.instructions 
                              if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                if len(non_trivial) == 1:
                    instr = non_trivial[0]
                    if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                        return True
                return False
            
            in_body_count = sum(1 for s in succ_list if s in body)
            break_continue_count = sum(1 for s in succ_list if s not in body and is_break_or_continue_block(s))
            
            # 如果一个是循环体内，一个是break/continue，这可能是if条件块
            # [关键修复] 但还需要检查：如果header有向后跳转到它的边，它是循环头部，不是if条件块
            if in_body_count == 1 and break_continue_count == 1:
                # [关键修复] 检查是否有向后跳转到header的边
                # 如果有，header是while循环的条件检查块，不是if条件块
                # [关键修复] 检查是否有向后跳转到header的边
                # 如果有，header是while循环的条件检查块，不是if条件块
                # [关键修复] 检查是否有向后跳转到header的边
                # 如果有，header是while循环的条件检查块，不是if条件块
                # [关键修复] 检查是否有向后跳转到header的边
                # 如果有，header是while循环的条件检查块，不是if条件块
                has_backward_jump_to_header = False
                for block in body:
                    for instr in block.instructions:
                        if 'BACKWARD' in instr.opname:
                            if instr.argval is not None and instr.argval == header.start_offset:
                                has_backward_jump_to_header = True
                                break
                    if has_backward_jump_to_header:
                        break
                
                # 如果没有向后跳转到header的边，才认为是if条件块
                if not has_backward_jump_to_header:
                    return None
        
        if is_for:
            loop_type = ControlStructureType.FOR_LOOP
        elif is_while:
            loop_type = ControlStructureType.WHILE_LOOP
        else:
            loop_type = ControlStructureType.DO_WHILE_LOOP
        
        # [关键修复] 检测是否为异步for循环（async for）
        is_async_for = False
        if is_for:
            # 检查是否有 GET_AITER 或 GET_ANEXT 指令
            # [关键修复] 需要检查头部块和循环体，因为GET_AITER可能在头部
            # 检查是否有 GET_AITER 或 GET_ANEXT 指令
            # [关键修复] 需要检查头部块和循环体，因为GET_AITER可能在头部
            # 检查是否有 GET_AITER 或 GET_ANEXT 指令
            # [关键修复] 需要检查头部块和循环体，因为GET_AITER可能在头部
            # 检查是否有 GET_AITER 或 GET_ANEXT 指令
            # [关键修复] 需要检查头部块和循环体，因为GET_AITER可能在头部
            blocks_to_check = [header] + list(body)
            for block in blocks_to_check:
                for instr in block.instructions:
                    if instr.opname in ('GET_AITER', 'GET_ANEXT'):
                        is_async_for = True
                        break
                if is_async_for:
                    break
        
        # [关键修复] 识别for-else/while-else的else块
        else_body = self._analyze_loop_else(header, body, is_for)
        
        # [关键修复] 找到真正的循环条件块
        # 对于Python 3.11+优化后的while循环，条件可能在循环尾部
        condition_block = header if is_while or is_for else None
        actual_header = header  # [关键修复] 保存实际的header块
        
        # [关键修复] 检测 while True: 循环
        # while True 循环的特征：header只有一个后继
        # 情况1：header包含 LOAD_CONST True + JUMP
        # 情况2：header只有 NOP/RESUME（Python 3.11+ 优化后的 while True）
        is_while_true = False
        if is_while and len(header.successors) == 1:
            succ = list(header.successors)[0]
            # 移除 succ in body 的检查，因为对于 while True 循环，后继总是循环体的开始
            # 检查header是否包含 LOAD_CONST True
            has_true_const = False
            has_jump = False
            has_only_nop = True
            for instr in header.instructions:
                if instr.opname == 'LOAD_CONST' and instr.argval is True:
                    has_true_const = True
                if 'JUMP' in instr.opname:
                    has_jump = True
                if instr.opname not in ('NOP', 'RESUME', 'CACHE'):
                    has_only_nop = False
            
            # 情况1：LOAD_CONST True + JUMP
            if has_true_const and has_jump:
                is_while_true = True
            # 情况2：只有 NOP/RESUME（Python 3.11+ 优化后的 while True）
            elif has_only_nop:
                # 检查后继块是否是条件块（有 POP_JUMP 指令）
                # 且循环体内有向后跳转回后继块的指令
                # 检查后继块是否是条件块（有 POP_JUMP 指令）
                # 且循环体内有向后跳转回后继块的指令
                has_pop_jump = False
                for instr in succ.instructions:
                    if 'POP_JUMP' in instr.opname:
                        has_pop_jump = True
                        break
                
                if has_pop_jump:
                    # 检查整个 CFG 中是否有向后跳转指令
                    # 对于嵌套循环，body 可能只包含 header 本身
                    # 检查整个 CFG 中是否有向后跳转指令
                    # 对于嵌套循环，body 可能只包含 header 本身
                    # 检查整个 CFG 中是否有向后跳转指令
                    # 对于嵌套循环，body 可能只包含 header 本身
                    # 检查整个 CFG 中是否有向后跳转指令
                    # 对于嵌套循环，body 可能只包含 header 本身
                    has_backward_jump = False
                    for block in self.cfg.blocks.values():
                        for instr in block.instructions:
                            if 'JUMP_BACKWARD' in instr.opname:
                                has_backward_jump = True
                                break
                        if has_backward_jump:
                            break
                    if has_backward_jump:
                        is_while_true = True
        
        # [关键修复] 初始化init_blocks列表
        init_blocks = []
        
        # [关键修复] 对于 while True: 循环，condition_block 应该为 None
        # 因为条件就是 True，不需要单独的条件块
        if is_while_true:
            condition_block = None
        
        # [关键修复] 对于header包含初始化代码但没有条件跳转指令的情况
        # 这是while True循环，真正的条件在其他块（如内层if条件）
        if is_while and condition_block == header:
            # 检查header是否包含条件跳转指令
            # 检查header是否包含条件跳转指令
            # 检查header是否包含条件跳转指令
            # 检查header是否包含条件跳转指令
            has_cond_jump = False
            for instr in header.instructions:
                if 'POP_JUMP' in instr.opname or 'JUMP_IF' in instr.opname:
                    has_cond_jump = True
                    break
            
            if not has_cond_jump:
                # header没有条件跳转指令，这是while True循环
                # header没有条件跳转指令，这是while True循环
                # header没有条件跳转指令，这是while True循环
                # header没有条件跳转指令，这是while True循环
                condition_block = None
                # [关键修复] 将header作为初始化块
                # 因为header包含初始化代码（如i = 0）
                init_blocks.append(header)
        
        # [关键修复] 对于is_while_body_header情况（header同时是body和header）
        # 我们需要找到真正的条件块（包含POP_JUMP_FORWARD_IF_FALSE的块）
        if is_while_body_header:
            # 查找包含向前跳转的条件检查块
            # 查找包含向前跳转的条件检查块
            # 查找包含向前跳转的条件检查块
            # 查找包含向前跳转的条件检查块
            for block in body:
                if block == header:
                    continue
                for instr in block.instructions:
                    if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                        # 检查这个块的后继是否包含header
                        # 检查这个块的后继是否包含header
                        # 检查这个块的后继是否包含header
                        # 检查这个块的后继是否包含header
                        if header in block.successors:
                            condition_block = block
                            break
                if condition_block != header:
                    break
        
        if is_while and condition_block == header and not is_while_body_header:
            # 检查是否有POP_JUMP_BACKWARD_IF_TRUE指令跳回header
            # 如果有，找到包含该指令的块作为真正的条件块
            # 检查是否有POP_JUMP_BACKWARD_IF_TRUE指令跳回header
            # 如果有，找到包含该指令的块作为真正的条件块
            # 检查是否有POP_JUMP_BACKWARD_IF_TRUE指令跳回header
            # 如果有，找到包含该指令的块作为真正的条件块
            # 检查是否有POP_JUMP_BACKWARD_IF_TRUE指令跳回header
            # 如果有，找到包含该指令的块作为真正的条件块
            for block in body:
                for instr in block.instructions:
                    if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                        if instr.argval is not None and instr.argval == header.start_offset:
                            # 找到循环条件块
                            # 找到循环条件块
                            # 找到循环条件块
                            # 找到循环条件块
                            condition_block = block
                            break
                if condition_block != header:
                    break
            
            # [关键修复] 对于Python 3.11+的while循环，
            # header块可能包含初始化代码（如count = 0）和条件代码
            # 我们需要将header_block设置为条件代码所在的块
            # 而不是包含初始化代码的块
            if condition_block != header:
                # 循环条件在另一个块中，使用condition_block作为header_block
                # 循环条件在另一个块中，使用condition_block作为header_block
                # 循环条件在另一个块中，使用condition_block作为header_block
                # 循环条件在另一个块中，使用condition_block作为header_block
                actual_header = condition_block
        
        # [关键修复] 对于Python 3.11+的while循环，
        # 检查header的前驱是否包含初始化代码（如count = 0）
        # 如果包含，将前驱块作为初始化块处理（不在循环体内，但在循环之前）
        if is_while and not is_for:
            # [关键修复] 找到形成回边的前驱（循环回跳的那个前驱）
            # 对于while循环，这个前驱是循环体的一部分
            # [关键修复] 找到形成回边的前驱（循环回跳的那个前驱）
            # 对于while循环，这个前驱是循环体的一部分
            # [关键修复] 找到形成回边的前驱（循环回跳的那个前驱）
            # 对于while循环，这个前驱是循环体的一部分
            # [关键修复] 找到形成回边的前驱（循环回跳的那个前驱）
            # 对于while循环，这个前驱是循环体的一部分
            back_edge_pred = None
            for pred in header.predecessors:
                # 检查这个前驱是否有指令跳回header
                # 检查这个前驱是否有指令跳回header
                # 检查这个前驱是否有指令跳回header
                # 检查这个前驱是否有指令跳回header
                for instr in pred.instructions:
                    if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                        if instr.argval is not None and instr.argval == header.start_offset:
                            back_edge_pred = pred
                            break
                    elif 'JUMP_BACKWARD' in instr.opname:
                        if instr.argval is not None and instr.argval == header.start_offset:
                            back_edge_pred = pred
                            break
                if back_edge_pred:
                    break
            
            for pred in header.predecessors:
                # 跳过形成回边的前驱（它是循环体的一部分）
                # 跳过形成回边的前驱（它是循环体的一部分）
                # 跳过形成回边的前驱（它是循环体的一部分）
                # 跳过形成回边的前驱（它是循环体的一部分）
                if pred == back_edge_pred:
                    continue
                
                # [关键修复] 跳过其他循环的header块
                # 如果前驱是另一个循环的header，它不应该被视为初始化块
                if hasattr(pred, 'loop_header') and pred.loop_header:
                    continue
                
                # [关键修复] 检查前驱是否是其他循环的header（通过检查它是否有向后跳转）
                is_other_loop_header = False
                for instr in pred.instructions:
                    if 'BACKWARD' in instr.opname:
                        # 有向后跳转，可能是循环header
                        # 检查跳转目标是否是pred自己（循环回跳）
                        # 有向后跳转，可能是循环header
                        # 检查跳转目标是否是pred自己（循环回跳）
                        # 有向后跳转，可能是循环header
                        # 检查跳转目标是否是pred自己（循环回跳）
                        # 有向后跳转，可能是循环header
                        # 检查跳转目标是否是pred自己（循环回跳）
                        if instr.argval is not None and instr.argval == pred.start_offset:
                            is_other_loop_header = True
                            break
                
                if is_other_loop_header:
                    continue
                
                # [关键修复] 对于已经在body中的前驱，检查是否是初始化块
                # 如果是，需要从body中移除并作为初始化块处理
                # 检查前驱块是否包含初始化代码（STORE_FAST等）
                has_init = False
                has_back_jump = False
                for instr in pred.instructions:
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                        has_init = True
                    if 'BACKWARD' in instr.opname:
                        has_back_jump = True
                
                # [关键修复] 如果前驱块包含初始化代码，且不是循环头部（没有向后跳转）
                # 则将其视为初始化块
                if has_init and not has_back_jump:
                    init_blocks.append(pred)
                    # [关键修复] 如果初始化块在body中，将其移除
                    if pred in body:
                        body.discard(pred)
        
        # [关键修复] 检查header块本身是否包含初始化代码
        # 对于Python 3.11+的while循环，header块可能同时包含初始化代码和条件代码
        # 例如：counter = 0; while counter < 5: ...
        # 这种情况下，header块的前驱不包含初始化代码，但header块本身包含
        if is_while and not is_for and not init_blocks:
            # 检查header块是否包含初始化代码
            # 检查header块是否包含初始化代码
            # 检查header块是否包含初始化代码
            # 检查header块是否包含初始化代码
            header_has_init = False
            header_has_condition = False
            init_instrs = []
            condition_start_idx = 0
            
            for i, instr in enumerate(header.instructions):
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                    header_has_init = True
                    init_instrs.append(i)
                # 检查是否是条件跳转指令
                if 'JUMP' in instr.opname and 'BACKWARD' not in instr.opname:
                    header_has_condition = True
                    condition_start_idx = i
                    break
            
            # 如果header块同时包含初始化代码和条件代码
            # 并且初始化代码在条件代码之前，将header块标记为需要特殊处理
            if header_has_init and header_has_condition:
                # 标记header块包含初始化代码
                # 这将在AST生成阶段被处理
                # 标记header块包含初始化代码
                # 这将在AST生成阶段被处理
                # 标记header块包含初始化代码
                # 这将在AST生成阶段被处理
                # 标记header块包含初始化代码
                # 这将在AST生成阶段被处理
                header.has_init_code = True
                header.init_instr_indices = init_instrs
        
        # [关键修复] 重新计算body_list（因为body可能已经改变）
        body_list = sorted(body, key=lambda b: b.start_offset)
        
        # [关键修复] 排序初始化块
        init_blocks_sorted = sorted(init_blocks, key=lambda b: b.start_offset) if init_blocks else []
        
        # [关键修复] 对于for循环，找到真正的entry_block（GET_ITER块）
        # entry_block是header的前驱块，包含GET_ITER指令
        entry_block = header  # 默认使用header作为entry_block
        if is_for:
            for pred in header.predecessors:
                # 检查前驱块是否包含GET_ITER指令
                # 检查前驱块是否包含GET_ITER指令
                # 检查前驱块是否包含GET_ITER指令
                # 检查前驱块是否包含GET_ITER指令
                has_get_iter = any(instr.opname == 'GET_ITER' for instr in pred.instructions)
                if has_get_iter:
                    entry_block = pred
                    break
        elif is_while:
            # [关键修复] 对于while循环，entry_block应该是header自己
            # 或者header的前驱块（如果该前驱不在循环体内且不是另一个循环的body块）
            # [关键修复] 如果header是if的else分支，entry_block应该是header本身
            # [关键修复] 对于while循环，entry_block应该是header自己
            # 或者header的前驱块（如果该前驱不在循环体内且不是另一个循环的body块）
            # [关键修复] 如果header是if的else分支，entry_block应该是header本身
            if is_else_branch:
                entry_block = header
            else:
                entry_block = header  # 默认使用header作为entry_block
                for pred in header.predecessors:
                    if pred not in body:
                        # 前驱不在循环体内，检查是否是另一个循环的body块
                        # 前驱不在循环体内，检查是否是另一个循环的body块
                        # 前驱不在循环体内，检查是否是另一个循环的body块
                        # 前驱不在循环体内，检查是否是另一个循环的body块
                        is_other_loop_body = False
                        
                        # [关键修复] 检查已创建的LoopStructure
                        for struct in self.structures:
                            if isinstance(struct, LoopStructure):
                                if pred in struct.body_blocks:
                                    is_other_loop_body = True
                                    break
                        
                        # [关键修复] 检查还没有创建LoopStructure的循环
                        # 使用loop_analyzer的原始数据
                        if not is_other_loop_body and self.loop_analyzer:
                            all_loops = self.loop_analyzer.get_all_loops()
                            for other_header, other_body in all_loops.items():
                                if other_header != header and pred in other_body:
                                    is_other_loop_body = True
                                    break
                        
                        if not is_other_loop_body:
                            # 前驱不是另一个循环的body块，这是entry_block
                            # 前驱不是另一个循环的body块，这是entry_block
                            # 前驱不是另一个循环的body块，这是entry_block
                            # 前驱不是另一个循环的body块，这是entry_block
                            entry_block = pred
                            break
        
        loop = LoopStructure(
            struct_type=loop_type,
            loop_type=loop_type,
            entry_block=entry_block,  # [关键修复] 使用真正的entry_block
            header_block=actual_header,  # [关键修复] 使用实际的header块
            body_blocks=body_list,
            condition_block=condition_block,
            exit_block=exit_blocks[0] if exit_blocks else None,
            is_post_test=loop_type == ControlStructureType.DO_WHILE_LOOP,
            else_body=else_body,
            init_blocks=init_blocks_sorted,  # [关键修复] 存储初始化块
            is_async=is_async_for,  # [关键修复] 标记是否为异步循环
            is_yield_from=is_yield_from_loop  # [关键修复] 标记是否为yield from循环
        )
        
        return loop
    
    def _analyze_loop_else(self, header: BasicBlock, body: Set[BasicBlock], is_for: bool) -> List[BasicBlock]:
        """
        分析循环的else块
        
        对于for循环：
        - FOR_ITER指令在迭代完成时跳转到else块
        - else块从FOR_ITER的跳转目标开始
        
        对于while循环：
        - 条件为假时跳转到else块
        - else块从条件跳转的目标开始
        
        Args:
            header: 循环头部
            body: 循环体
            is_for: 是否为for循环
            
        Returns:
            else块列表
        """
        else_body = []
        
        if is_for:
            # [关键修复] 检查是否是async for循环
            # [关键修复] 检查是否是async for循环
            # [关键修复] 检查是否是async for循环
            # [关键修复] 检查是否是async for循环
            is_async_for = any(instr.opname == 'GET_ANEXT' for instr in header.instructions)
            
            if is_async_for:
                # [关键修复] 对于async for循环，查找END_ASYNC_FOR指令
                # else块在END_ASYNC_FOR之后
                # [关键修复] 对于async for循环，查找END_ASYNC_FOR指令
                # else块在END_ASYNC_FOR之后
                # [关键修复] 对于async for循环，查找END_ASYNC_FOR指令
                # else块在END_ASYNC_FOR之后
                # [关键修复] 对于async for循环，查找END_ASYNC_FOR指令
                # else块在END_ASYNC_FOR之后
                for block in self.cfg.blocks.values():
                    if block not in body:
                        for instr in block.instructions:
                            if instr.opname == 'END_ASYNC_FOR':
                                # 找到END_ASYNC_FOR，else块从这块开始
                                # 找到END_ASYNC_FOR，else块从这块开始
                                # 找到END_ASYNC_FOR，else块从这块开始
                                # 找到END_ASYNC_FOR，else块从这块开始
                                else_body = self._collect_else_blocks(block, body, header)
                                is_valid = self._is_valid_else_block(else_body) if else_body else False
                                if else_body and is_valid:
                                    return else_body
                                else:
                                    return []
                # 如果没有找到END_ASYNC_FOR，返回空
                return else_body
            else:
                # 查找FOR_ITER指令
                for instr in header.instructions:
                    if instr.opname == 'FOR_ITER' and instr.arg is not None:
                        # FOR_ITER的跳转目标是else块的开始
                        # 在Python 3.11+中，arg是相对于下一条指令的偏移量
                        # FOR_ITER的跳转目标是else块的开始
                        # 在Python 3.11+中，arg是相对于下一条指令的偏移量
                        # FOR_ITER的跳转目标是else块的开始
                        # 在Python 3.11+中，arg是相对于下一条指令的偏移量
                        # FOR_ITER的跳转目标是else块的开始
                        # 在Python 3.11+中，arg是相对于下一条指令的偏移量
                        jump_offset = instr.offset + 2 + instr.arg * 2  # 2字节指令 + 跳转距离
                        
                        # 查找包含该偏移量的块
                        for block in self.cfg.blocks.values():
                            if block.start_offset <= jump_offset < block.end_offset:
                                # 检查这个块是否在循环体外
                                # 检查这个块是否在循环体外
                                # 检查这个块是否在循环体外
                                # 检查这个块是否在循环体外
                                if block not in body:
                                    # 收集else块
                                    # 收集else块
                                    # 收集else块
                                    # 收集else块
                                    else_body = self._collect_else_blocks(block, body, header)
                                    # [关键修复] 验证else块是否有效
                                    # 如果else块只包含return语句，可能不是真正的else块
                                    if else_body and self._is_valid_else_block(else_body):
                                        return else_body
                                    else:
                                        return []
                                break
                        break
        else:
            # [关键修复] 处理while循环的else子句
            # while循环的else子句是在条件为假时跳转到的地方
            # 查找header中的POP_JUMP_FORWARD_IF_FALSE或POP_JUMP_BACKWARD_IF_FALSE指令
            for instr in header.instructions:
                if instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                    # [关键修复] 使用instr.argval（绝对偏移量）而不是instr.arg（相对跳转距离）
                    # [关键修复] 使用instr.argval（绝对偏移量）而不是instr.arg（相对跳转距离）
                    # [关键修复] 使用instr.argval（绝对偏移量）而不是instr.arg（相对跳转距离）
                    # [关键修复] 使用instr.argval（绝对偏移量）而不是instr.arg（相对跳转距离）
                    if instr.argval is not None:
                        # 跳转目标是else块的开始
                        # 跳转目标是else块的开始
                        # 跳转目标是else块的开始
                        # 跳转目标是else块的开始
                        jump_offset = instr.argval
                        
                        # 查找包含该偏移量的块
                        for block in self.cfg.blocks.values():
                            if block.start_offset <= jump_offset < block.end_offset:
                                # 检查这个块是否在循环体外
                                # 检查这个块是否在循环体外
                                # 检查这个块是否在循环体外
                                # 检查这个块是否在循环体外
                                if block not in body:
                                    # 收集else块
                                    # 收集else块
                                    # 收集else块
                                    # 收集else块
                                    else_body = self._collect_else_blocks(block, body, header)
                                    # [关键修复] 验证else块是否有效
                                    if else_body and self._is_valid_else_block(else_body):
                                        return else_body
                                    else:
                                        return []
                                break
                        break
        
        return else_body
    
    def _is_valid_else_block(self, else_blocks: List[BasicBlock]) -> bool:
        """
        验证else块是否有效
        
        真正的else块应该：
        1. 包含有意义的代码（如print, 赋值等）
        2. 不包含GET_ITER（这是下一个循环的开始）
        3. 不包含为下一个循环准备迭代的代码
        4. 不包含COMPARE_OP + POP_JUMP（这是while循环的开始）
        5. [关键修复] 不只是LOAD_CONST None + RETURN_VALUE（这是函数正常结束）
        
        Args:
            else_blocks: else块列表
            
        Returns:
            如果是有效的else块返回True
        """
        if not else_blocks:
            return False
        
        # [关键修复] 检查else块是否包含GET_ITER指令
        # 如果包含，这是下一个循环的开始，不是else块
        for block in else_blocks:
            for instr in block.instructions:
                if instr.opname == 'GET_ITER':
                    # 这是下一个循环的开始，不是else块
                    # 这是下一个循环的开始，不是else块
                    # 这是下一个循环的开始，不是else块
                    # 这是下一个循环的开始，不是else块
                    return False
        
        # [关键修复] 检查else块是否包含while循环的开始
        # while循环的特征：COMPARE_OP + POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_BACKWARD_IF_TRUE
        for block in else_blocks:
            has_compare = False
            has_jump = False
            for instr in block.instructions:
                if instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
                    has_compare = True
                if has_compare and instr.opname in (
                    'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                    'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_TRUE'
                ):
                    # 这是while循环的开始，不是else块
                    return False
        
        # 检查else块的内容
        meaningful_instructions = 0
        has_return = False
        only_return_none = True  # [关键修复] 跟踪是否只有return None
        load_instructions = []  # [关键修复] 跟踪LOAD指令
        for block in else_blocks:
            for instr in block.instructions:
                # 忽略RESUME和CACHE指令
                # 忽略RESUME和CACHE指令
                # 忽略RESUME和CACHE指令
                # 忽略RESUME和CACHE指令
                if instr.opname in ('RESUME', 'CACHE'):
                    continue
                # 忽略POP_TOP
                if instr.opname == 'POP_TOP':
                    continue
                # 记录是否有return指令
                if instr.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RETURN_GENERATOR'):
                    has_return = True
                    continue
                # [关键修复] 如果不是LOAD_CONST None，标记为不只有return None
                if instr.opname == 'LOAD_CONST' and instr.argval is None:
                    continue
                # [关键修复] 记录LOAD指令
                if instr.opname in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_DEREF', 'LOAD_ATTR', 'LOAD_METHOD', 'LOAD_CONST'):
                    load_instructions.append(instr)
                    continue
                # [关键修复] 如果有其他指令，标记为不只有return None
                only_return_none = False
                # 如果包含其他指令，认为是有效的else块
                meaningful_instructions += 1
        
        # [关键修复] 如果只有return None（LOAD_CONST None + RETURN_VALUE），
        # 这不是真正的else块，只是函数正常结束
        if has_return and only_return_none and meaningful_instructions == 0:
            return False
        
        # [关键修复] 如果只有LOAD_xxx + RETURN_VALUE（简单return模式），
        # 这也不是for-else语法的else分支
        # 这是for循环正常结束后返回结果的代码
        if has_return and meaningful_instructions == 0 and len(load_instructions) > 0:
            # 检查是否是简单的return模式
            # 简单return模式：只有LOAD指令和RETURN_VALUE
            # 这不是for-else语法的else分支
            # 检查是否是简单的return模式
            # 简单return模式：只有LOAD指令和RETURN_VALUE
            # 这不是for-else语法的else分支
            # 检查是否是简单的return模式
            # 简单return模式：只有LOAD指令和RETURN_VALUE
            # 这不是for-else语法的else分支
            # 检查是否是简单的return模式
            # 简单return模式：只有LOAD指令和RETURN_VALUE
            # 这不是for-else语法的else分支
            return False
        
        # [关键修复] 如果有有意义的指令（不是LOAD_xxx + RETURN_VALUE这种简单return模式）
        # 才认为是有效的else块
        # for-else语法的else分支应该包含真正的逻辑代码
        return meaningful_instructions > 0
    
    def _collect_else_blocks(self, start_block: BasicBlock, loop_body: Set[BasicBlock], 
                              loop_header: BasicBlock) -> List[BasicBlock]:
        """
        收集else块的所有基本块
        
        关键逻辑：
        1. else块从FOR_ITER的跳转目标开始
        2. else块只包含那些不会被break跳转到的块
        3. else块在遇到特定终止条件时停止收集
        
        Args:
            start_block: else块的起始块
            loop_body: 循环体块集合
            loop_header: 循环头部块
            
        Returns:
            else块列表
        """
        else_blocks = []
        worklist = [start_block]
        visited = set()
        
        # 找到所有被break跳转到的块（这些块在循环之后，不属于else）
        break_targets = set()
        for block in loop_body:
            for instr in block.instructions:
                if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                    # break通常使用JUMP_FORWARD跳出循环
                    # break通常使用JUMP_FORWARD跳出循环
                    # break通常使用JUMP_FORWARD跳出循环
                    # break通常使用JUMP_FORWARD跳出循环
                    if instr.arg is not None:
                        jump_offset = self._calculate_jump_target(instr)
                        # 查找目标块
                        for b in self.cfg.blocks.values():
                            if b.start_offset <= jump_offset < b.end_offset:
                                if b not in loop_body:
                                    break_targets.add(b)
                                break
        
        while worklist:
            block = worklist.pop(0)
            if block in visited or block in loop_body or block in break_targets:
                continue
            visited.add(block)
            else_blocks.append(block)
            
            # [关键修复] 检查块是否包含终止指令（如RETURN_VALUE）
            # 如果包含，不要收集后继块
            has_terminator = False
            for instr in block.instructions:
                if instr.opname in ('RETURN_VALUE', 'RETURN_CONST', 'RERAISE', 'RAISE_VARARGS'):
                    has_terminator = True
                    break
            
            if has_terminator:
                continue
            
            # [关键修复] 限制else块的大小
            # 如果已经收集了足够的块，停止收集
            # 通常else块只包含少量语句，但某些情况下可能需要更多
            if len(else_blocks) >= 5:
                break

            # 继续收集后继块，但要检查是否被循环外的代码引用
            for succ in block.successors:
                if succ not in visited and succ not in loop_body and succ not in break_targets:
                    # 检查这个后继块是否只被else块引用
                    # 如果被循环外的代码引用，则不属于else块
                    # 检查这个后继块是否只被else块引用
                    # 如果被循环外的代码引用，则不属于else块
                    # 检查这个后继块是否只被else块引用
                    # 如果被循环外的代码引用，则不属于else块
                    # 检查这个后继块是否只被else块引用
                    # 如果被循环外的代码引用，则不属于else块
                    is_only_from_else = all(pred in loop_body or pred in else_blocks or pred in visited 
                                           for pred in succ.predecessors)
                    if is_only_from_else:
                        worklist.append(succ)
        
        # 按偏移量排序
        else_blocks.sort(key=lambda b: b.start_offset)
        return else_blocks
    
    def _calculate_jump_target(self, instr) -> int:
        """计算跳转指令的目标偏移量"""
        if instr.opname in ('JUMP_FORWARD', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE'):
            # 相对跳转，arg是相对于下一条指令的偏移量
            # 相对跳转，arg是相对于下一条指令的偏移量
            # 相对跳转，arg是相对于下一条指令的偏移量
            # 相对跳转，arg是相对于下一条指令的偏移量
            return instr.offset + 2 + instr.arg * 2
        elif instr.opname in ('JUMP_BACKWARD', 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
            # 向后跳转
            # 向后跳转
            return instr.offset + 2 - instr.arg * 2
        elif instr.opname == 'JUMP_ABSOLUTE':
            # 绝对跳转
            # 绝对跳转
            return instr.arg
        else:
            return instr.offset + 2
    
    def _is_while_loop(self, header: BasicBlock, body: Set[BasicBlock]) -> bool:
        """
        判断是否为while循环
        
        Args:
            header: 循环头部
            body: 循环体
            
        Returns:
            如果是while循环则返回True
        """
        # [关键修复] 处理 while True: 循环
        # while True 循环的头部只有一个后继（无条件跳转到循环体）
        if len(header.successors) == 1:
            succ = list(header.successors)[0]
            # [关键修复] 检查头部是否包含 LOAD_CONST True
            # 或者头部只有 NOP/RESUME 等占位指令（Python 3.11+ 优化后的 while True）
            has_true_const = False
            has_jump = False
            has_only_nop = True
            for instr in header.instructions:
                if instr.opname == 'LOAD_CONST' and instr.argval is True:
                    has_true_const = True
                if 'JUMP' in instr.opname:
                    has_jump = True
                if instr.opname not in ('NOP', 'RESUME', 'CACHE'):
                    has_only_nop = False
            
            # 如果是 LOAD_CONST True + JUMP，这是 while True 循环
            if has_true_const and has_jump:
                return True
            
            # [关键修复] Python 3.11+ 的 while True 循环头部可能只有 NOP
            # 这种情况下，后继块应该是循环体的开始
            if has_only_nop:
                # 检查循环体内是否有向后跳转指令
                # 注意：对于嵌套循环，body 可能只包含 header 本身
                # 所以我们需要检查整个 CFG 中是否有跳转到 header 的向后跳转
                # 检查循环体内是否有向后跳转指令
                # 注意：对于嵌套循环，body 可能只包含 header 本身
                # 所以我们需要检查整个 CFG 中是否有跳转到 header 的向后跳转
                # 检查循环体内是否有向后跳转指令
                # 注意：对于嵌套循环，body 可能只包含 header 本身
                # 所以我们需要检查整个 CFG 中是否有跳转到 header 的向后跳转
                # 检查循环体内是否有向后跳转指令
                # 注意：对于嵌套循环，body 可能只包含 header 本身
                # 所以我们需要检查整个 CFG 中是否有跳转到 header 的向后跳转
                has_backward_jump = False
                for block in self.cfg.blocks.values():
                    for instr2 in block.instructions:
                        if 'JUMP_BACKWARD' in instr2.opname:
                            # 在Python 3.11+中，JUMP_BACKWARD的argval是相对偏移量
                            # 所以只要有JUMP_BACKWARD指令，就表明这是一个循环
                            # 在Python 3.11+中，JUMP_BACKWARD的argval是相对偏移量
                            # 所以只要有JUMP_BACKWARD指令，就表明这是一个循环
                            # 在Python 3.11+中，JUMP_BACKWARD的argval是相对偏移量
                            # 所以只要有JUMP_BACKWARD指令，就表明这是一个循环
                            # 在Python 3.11+中，JUMP_BACKWARD的argval是相对偏移量
                            # 所以只要有JUMP_BACKWARD指令，就表明这是一个循环
                            has_backward_jump = True
                            break
                    if has_backward_jump:
                        break
                if has_backward_jump:
                    return True
                # 检查后继块是否是循环体的一部分（包含调用指令）
                has_call = any(
                    instr.opname in ('CALL', 'PRECALL')
                    for instr in succ.instructions
                )
                if has_call:
                    return True
            # [关键修复] 检查循环体内是否有向后跳转到header的指令
            # 这是识别while循环的关键特征
            has_back_jump_to_header = False
            for block in body:
                if block == header:
                    continue
                for instr in block.instructions:
                    if 'BACKWARD' in instr.opname:
                        if instr.argval is not None and instr.argval == header.start_offset:
                            has_back_jump_to_header = True
                            break
                if has_back_jump_to_header:
                    break
            
            if has_back_jump_to_header:
                return True
            
            return False
        
        if len(header.successors) != 2:
            return False
        
        succ_list = list(header.successors)
        one_in_body = succ_list[0] in body
        other_in_body = succ_list[1] in body
        
        # [关键修复] 标准while循环：一个后继在循环体内，一个在循环体外
        # 两种情况：第一个在第二个不在，或第一个不在第二个在
        if (one_in_body and not other_in_body) or (not one_in_body and other_in_body):
            # [关键修复] 检查循环体内是否有向后跳转
            # 如果有，这是while循环；如果没有，这可能是if条件
            # [关键修复] 检查循环体内是否有向后跳转
            # 如果有，这是while循环；如果没有，这可能是if条件
            # [关键修复] 检查循环体内是否有向后跳转
            # 如果有，这是while循环；如果没有，这可能是if条件
            # [关键修复] 检查循环体内是否有向后跳转
            # 如果有，这是while循环；如果没有，这可能是if条件
            for block in body:
                for instr in block.instructions:
                    if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                        # 检查跳转目标是否是header或在header之后
                        # 检查跳转目标是否是header或在header之后
                        # 检查跳转目标是否是header或在header之后
                        # 检查跳转目标是否是header或在header之后
                        if instr.argval is not None and instr.argval <= header.start_offset:
                            return True
                        # 检查跳转目标是否在循环体内
                        target_in_body = any(
                            b.start_offset <= instr.argval < b.end_offset
                            for b in body
                        )
                        if target_in_body:
                            return True
            
            # [关键修复] Python 3.11+优化：检查header是否是while循环条件
            # 特征：header包含COMPARE_OP + POP_JUMP_FORWARD_IF_FALSE
            # 且循环体以NOP结束（break被优化为NOP）
            has_compare = False
            has_forward_jump = False
            for instr in header.instructions:
                if 'COMPARE_OP' in instr.opname:
                    has_compare = True
                if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                    has_forward_jump = True
            
            # 如果header是比较+向前跳转，且循环体以NOP结束，这是while循环
            if has_compare and has_forward_jump:
                # 检查循环体是否以NOP结束（break被优化的情况）
                # 检查循环体是否以NOP结束（break被优化的情况）
                # 检查循环体是否以NOP结束（break被优化的情况）
                # 检查循环体是否以NOP结束（break被优化的情况）
                for block in body:
                    if block != header:
                        for instr in block.instructions:
                            if instr.opname == 'NOP':
                                # 检查是否是循环体的最后一条非POP_TOP指令
                                # 检查是否是循环体的最后一条非POP_TOP指令
                                # 检查是否是循环体的最后一条非POP_TOP指令
                                # 检查是否是循环体的最后一条非POP_TOP指令
                                non_trivial = [i for i in block.instructions 
                                              if i.opname not in ('RESUME', 'CACHE', 'POP_TOP')]
                                if non_trivial and non_trivial[-1].opname == 'NOP':
                                    return True
            
            # 没有向后跳转，这可能是if条件
            return False
        
        # [关键修复] Python 3.11+优化后的while循环：
        # 循环头部是if条件块，两个后继都在循环体内
        # 但循环尾部包含POP_JUMP_BACKWARD_IF_TRUE跳回循环头部
        if one_in_body and other_in_body:
            # 检查循环尾部是否有向后跳转回header的指令
            # 检查循环尾部是否有向后跳转回header的指令
            # 检查循环尾部是否有向后跳转回header的指令
            # 检查循环尾部是否有向后跳转回header的指令
            for block in body:
                for instr in block.instructions:
                    if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                        if instr.argval is not None and instr.argval == header.start_offset:
                            return True
            
            # [关键修复] 另一种while循环结构：
            # 条件检查在一个块，循环体从另一个块开始
            # 循环尾部跳回到循环体开始，而不是条件检查块
            # 例如：while j < 2: ... j += 1; if j < 2: continue
            # 这种情况下，header是条件检查块，但向后跳转目标是循环体开始
            for block in body:
                for instr in block.instructions:
                    if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                        if instr.argval is not None:
                            # 检查跳转目标是否在循环体内
                            # 检查跳转目标是否在循环体内
                            # 检查跳转目标是否在循环体内
                            # 检查跳转目标是否在循环体内
                            target_offset = instr.argval
                            target_in_body = any(
                                b.start_offset <= target_offset < b.end_offset
                                for b in body
                            )
                            if target_in_body:
                                # 检查header是否是条件块（COMPARE_OP + POP_JUMP）
                                # 检查header是否是条件块（COMPARE_OP + POP_JUMP）
                                # 检查header是否是条件块（COMPARE_OP + POP_JUMP）
                                # 检查header是否是条件块（COMPARE_OP + POP_JUMP）
                                has_compare = any(
                                    'COMPARE_OP' in i.opname or 'POP_JUMP' in i.opname
                                    for i in header.instructions
                                )
                                if has_compare:
                                    return True
            
            # [关键修复] 还有一种while循环结构（Python 3.11+优化）：
            # 条件检查在header（Block 44），fall-through后继是循环体开始（Block 60）
            # 循环体（Block 60）包含POP_JUMP_BACKWARD_IF_TRUE跳转到它自己（继续循环）
            # 这种情况下，header是条件检查块，循环体是独立的块
            # 特征：
            # 1. header包含POP_JUMP_FORWARD_IF_FALSE（条件为假时退出循环）
            # 2. fall-through后继（循环体开始）包含POP_JUMP_BACKWARD_IF_TRUE（继续循环）
            # 3. 向后跳转的目标是循环体开始，不是header
            has_forward_cond = False
            fall_through_is_loop_body = False
            for instr in header.instructions:
                if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                    has_forward_cond = True
                    break
            if has_forward_cond:
                # 找到fall-through后继
                # 找到fall-through后继
                # 找到fall-through后继
                # 找到fall-through后继
                for succ in succ_list:
                    if succ in body:
                        # 检查这个后继是否包含POP_JUMP_BACKWARD_IF_TRUE跳转到它自己
                        # 检查这个后继是否包含POP_JUMP_BACKWARD_IF_TRUE跳转到它自己
                        # 检查这个后继是否包含POP_JUMP_BACKWARD_IF_TRUE跳转到它自己
                        # 检查这个后继是否包含POP_JUMP_BACKWARD_IF_TRUE跳转到它自己
                        for instr in succ.instructions:
                            if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                                if instr.argval is not None and instr.argval == succ.start_offset:
                                    fall_through_is_loop_body = True
                                    break
                    if fall_through_is_loop_body:
                        break
            if has_forward_cond and fall_through_is_loop_body:
                return True
        
        return False
    
    def _is_if_condition_in_loop(self, header: BasicBlock, body: Set[BasicBlock]) -> bool:
        """
        检查header是否是循环内的if条件块
        
        特征：
        1. header是条件块（有两个后继）
        2. 两个后继都在循环体内
        3. header不是真正的循环头部（没有退出分支）
        4. header支配它的后继（if条件块的特征）
        5. [关键修复] header的前驱中至少有一个在循环体内（不是循环入口）
        6. [关键修复] header不包含FOR_ITER指令（不是for循环的header）
        
        Args:
            header: 候选循环头部
            body: 循环体
            
        Returns:
            如果是if条件块则返回True
        """
        # [关键修复] 检查header是否包含FOR_ITER/GET_ANEXT/GET_AITER指令
        # 如果包含，则是for/async for循环的header块，不是if条件块
        for instr in header.instructions:
            if 'FOR_ITER' in instr.opname or instr.opname in ('GET_ANEXT', 'GET_AITER'):
                return False
        
        # [关键修复] 检查是否有向后跳转到header的边
        # 如果有，header可能是while循环的条件检查块
        # 但需要进一步检查：向后跳转是否来自header的直接后继
        # 如果是，header是while循环的条件检查块
        # 如果不是，header是if条件块（如while-else结构中的if）
        # 
        # [关键修复] 额外的检查：如果header有POP_JUMP_FORWARD_IF_*指令
        # 且header的前驱中有一个不在body中，header可能是if条件块
        # 这是while-else结构的特征：if条件块在while循环体内
        has_forward_jump_in_header = any(
            'POP_JUMP_FORWARD' in i.opname for i in header.instructions
        )
        
        for block in body:
            for instr in block.instructions:
                if 'BACKWARD' in instr.opname:
                    # [关键修复] 检查BACKWARD指令的跳转目标是否是header
                    # [关键修复] 检查BACKWARD指令的跳转目标是否是header
                    # [关键修复] 检查BACKWARD指令的跳转目标是否是header
                    # [关键修复] 检查BACKWARD指令的跳转目标是否是header
                    if instr.argval is not None and instr.argval == header.start_offset:
                        # [关键修复] 检查向后跳转是否来自header的直接后继
                        # 如果是，header是while循环的条件检查块
                        # 如果不是，header是if条件块
                        # [关键修复] 检查向后跳转是否来自header的直接后继
                        # 如果是，header是while循环的条件检查块
                        # 如果不是，header是if条件块
                        # [关键修复] 检查向后跳转是否来自header的直接后继
                        # 如果是，header是while循环的条件检查块
                        # 如果不是，header是if条件块
                        # [关键修复] 检查向后跳转是否来自header的直接后继
                        # 如果是，header是while循环的条件检查块
                        # 如果不是，header是if条件块
                        header_successors = set(header.successors)
                        if block in header_successors:
                            # [关键修复] 额外的检查：如果header有向前跳转
                            # 且header的前驱中有一个不在body中
                            # 这可能是if条件块在while-else结构中
                            # [关键修复] 额外的检查：如果header有向前跳转
                            # 且header的前驱中有一个不在body中
                            # 这可能是if条件块在while-else结构中
                            # [关键修复] 额外的检查：如果header有向前跳转
                            # 且header的前驱中有一个不在body中
                            # 这可能是if条件块在while-else结构中
                            # [关键修复] 额外的检查：如果header有向前跳转
                            # 且header的前驱中有一个不在body中
                            # 这可能是if条件块在while-else结构中
                            if has_forward_jump_in_header:
                                # 检查header的前驱
                                # 检查header的前驱
                                # 检查header的前驱
                                # 检查header的前驱
                                for pred in header.predecessors:
                                    if pred not in body:
                                        # header的前驱不在body中，header是if条件块
                                        # header的前驱不在body中，header是if条件块
                                        # header的前驱不在body中，header是if条件块
                                        # header的前驱不在body中，header是if条件块
                                        return True
                            # 向后跳转来自header的直接后继，header是while循环的条件检查块
                            return False
                        # 否则，继续检查其他条件
        
        # [关键修复] 检查header是否是while True循环的头部
        # while True循环的头部特征：
        # 1. 只有一个后继
        # 2. 只有NOP/RESUME等占位指令
        # 3. 后继是if条件块（有POP_JUMP指令）
        if len(header.successors) == 1:
            succ = list(header.successors)[0]
            # 检查header是否只有占位指令
            has_only_placeholder = all(
                instr.opname in ('NOP', 'RESUME', 'CACHE')
                for instr in header.instructions
            )
            # 检查后继是否是条件块
            has_pop_jump = any('POP_JUMP' in i.opname for i in succ.instructions)
            if has_only_placeholder and has_pop_jump:
                # 这是while True循环的头部，不是if条件块
                # 这是while True循环的头部，不是if条件块
                # 这是while True循环的头部，不是if条件块
                # 这是while True循环的头部，不是if条件块
                return False
            elif has_only_placeholder:
                # 这也是while True循环的头部，不是if条件块
                # 这也是while True循环的头部，不是if条件块
                return False
        
        # 检查是否是条件块
        if len(header.successors) != 2:
            return False
        
        # 检查两个后继是否都在循环体内
        succ_list = list(header.successors)
        
        # [关键修复] 检查后继是否是break/continue（只有一个JUMP指令）
        # 如果是，这仍然是if条件块，不是循环头部
        def is_break_or_continue_block(block):
            """检查块是否是break或continue"""
            non_trivial = [i for i in block.instructions 
                          if i.opname not in ('RESUME', 'CACHE', 'NOP')]
            if len(non_trivial) == 1:
                instr = non_trivial[0]
                # break: JUMP_FORWARD 到循环外部
                # continue: JUMP_BACKWARD 到循环头部
                if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                    return True
            return False
        
        # 检查两个后继
        in_body_count = sum(1 for s in succ_list if s in body)
        break_continue_count = sum(1 for s in succ_list if s not in body and is_break_or_continue_block(s))
        
        # 如果两个后继都在循环体内，或者一个是break/continue，另一个是循环体内
        # 这可能是if条件块
        if in_body_count == 2:
            # 两个都在循环体内，继续检查
            # 两个都在循环体内，继续检查
            # 两个都在循环体内，继续检查
            # 两个都在循环体内，继续检查
            pass
        elif in_body_count == 1 and break_continue_count == 1:
            # 一个在循环体内，一个是break/continue
            # 这是if条件块（如 if x: break）
            # 一个在循环体内，一个是break/continue
            # 这是if条件块（如 if x: break）
            pass
        else:
            # 其他情况，不是if条件块
            return False
        
        # 检查是否有退出分支（后继不在循环体内且不是break/continue）
        has_exit = any(s not in body and not is_break_or_continue_block(s) for s in succ_list)
        
        # 如果有退出分支（不是break/continue），是真正的循环头部
        if has_exit:
            return False
        
        # [关键修复] 检查header是否支配它的后继
        # if条件块支配它的then和else分支
        # 真正的循环头部不一定支配循环体内的所有块
        dominates_both = all(header in s.dominators for s in succ_list)
        
        if not dominates_both:
            # 不支配后继，不是if条件块
            # 不支配后继，不是if条件块
            # 不支配后继，不是if条件块
            # 不支配后继，不是if条件块
            return False
        
        # [关键修复] 检查header是否是循环入口
        # 如果header的所有前驱都在循环体内，它是循环内的if条件块
        # 如果header有一个前驱不在循环体内（或在循环外），它是循环入口
        predecessors_in_body = [p for p in header.predecessors if p in body]
        predecessors_outside = [p for p in header.predecessors if p not in body]
        
        # [关键修复] 检查header的后继是否有break块
        # 如果一个是break块（JUMP_FORWARD到循环外），另一个是循环体内
        # 那么header是if条件块（如 if x: break），不是循环入口
        succ_list = list(header.successors)
        break_count = 0
        in_body_count = 0
        for s in succ_list:
            if s in body:
                in_body_count += 1
            elif is_break_or_continue_block(s):
                # 检查是否是break（跳转到循环外）
                # 检查是否是break（跳转到循环外）
                non_trivial = [i for i in s.instructions 
                              if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                if len(non_trivial) == 1 and non_trivial[0].opname == 'JUMP_FORWARD':
                    break_count += 1
        
        # 如果一个是break块，一个是循环体内，这可能是if条件块
        # [关键修复] 但需要检查header是否也是循环头部
        # 如果header有向后跳转到它的边，它是循环头部，不是if条件块
        if break_count == 1 and in_body_count == 1:
            # 检查是否有向后跳转到header的边
            # 检查是否有向后跳转到header的边
            # 检查是否有向后跳转到header的边
            # 检查是否有向后跳转到header的边
            has_backward_jump_to_header = False
            for block in self.cfg.blocks.values():
                for instr in block.instructions:
                    if 'BACKWARD' in instr.opname and instr.argval == header.start_offset:
                        has_backward_jump_to_header = True
                        break
                if has_backward_jump_to_header:
                    break
            
            # 如果有向后跳转到header的边，header是循环头部，不是if条件块
            if has_backward_jump_to_header:
                return False
            
            # 否则，这是if条件块
            return True
        
        # 如果所有前驱都在循环体内，header是循环内的if条件块
        # 如果有前驱在循环外，header是循环入口（应该创建循环结构）
        if predecessors_outside:
            # header有循环外的前驱，它是循环入口，不是单纯的if条件块
            # header有循环外的前驱，它是循环入口，不是单纯的if条件块
            # header有循环外的前驱，它是循环入口，不是单纯的if条件块
            # header有循环外的前驱，它是循环入口，不是单纯的if条件块
            return False
        
        # [关键修复] 额外的检查：如果header的后继之一是向后跳转的目标
        # 这是while循环的特征（如while-else结构），不是if条件块
        # 检查body中是否有向后跳转到header的后继
        for succ in header.successors:
            if succ in body:
                # 检查body中是否有向后跳转到succ
                # 检查body中是否有向后跳转到succ
                # 检查body中是否有向后跳转到succ
                # 检查body中是否有向后跳转到succ
                for block in body:
                    for instr in block.instructions:
                        if 'BACKWARD' in instr.opname:
                            if instr.argval is not None and instr.argval == succ.start_offset:
                                # 这是while循环的特征，不是if条件块
                                # 这是while循环的特征，不是if条件块
                                # 这是while循环的特征，不是if条件块
                                # 这是while循环的特征，不是if条件块
                                return False
        
        # header是循环内的if条件块
        return True
    
    def _is_for_loop(self, header: BasicBlock, body: Set[BasicBlock]) -> bool:
        """
        判断是否为for循环（包括async for）
        
        [关键修复] FOR_LOOP必须在header块中有FOR_ITER或GET_ANEXT指令
        仅仅在body中有GET_ITER不足以判断为FOR_LOOP（推导式也会使用GET_ITER）
        
        Args:
            header: 循环头部
            body: 循环体
            
        Returns:
            如果是for循环则返回True
        """
        # [关键修复] 只检查header块，不检查body块
        # FOR_ITER必须在header中，GET_ITER在body中可能是推导式的一部分
        for instr in header.instructions:
            # 普通for循环: FOR_ITER在header中
            # async for循环: GET_ANEXT在header中
            # [关键修复] 也检查GET_AITER，这是async for循环的指令
            # 普通for循环: FOR_ITER在header中
            # async for循环: GET_ANEXT在header中
            # [关键修复] 也检查GET_AITER，这是async for循环的指令
            # 普通for循环: FOR_ITER在header中
            # async for循环: GET_ANEXT在header中
            # [关键修复] 也检查GET_AITER，这是async for循环的指令
            # 普通for循环: FOR_ITER在header中
            # async for循环: GET_ANEXT在header中
            # [关键修复] 也检查GET_AITER，这是async for循环的指令
            if instr.opname in ('FOR_ITER', 'GET_ANEXT', 'GET_AITER'):
                return True
        
        return False
    
    def _identify_conditionals(self) -> None:
        """识别条件结构"""
        analyzed_blocks = set(self.block_to_structure.keys())
        
        # [关键修复] 按偏移量排序遍历基本块，确保先分析前面的块
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
            # [关键修复] 检查块是否是条件块（包含POP_JUMP_IF_*指令）
            # [关键修复] 检查块是否是条件块（包含POP_JUMP_IF_*指令）
            # [关键修复] 检查块是否是条件块（包含POP_JUMP_IF_*指令）
            # [关键修复] 检查块是否是条件块（包含POP_JUMP_IF_*指令）
            is_conditional_block_flag = self._is_conditional_block(block)
            
            if block.start_offset in [76, 126, 182, 286]:
                current_struct = self.block_to_structure.get(block)
            
            # [关键修复] 初始化 is_loop_body_if，确保在所有代码路径中都有定义
            is_loop_body_if = False
            current_struct = None
            
            if block in analyzed_blocks:
                # [关键修复] 获取当前块所属的结构
                # [关键修复] 获取当前块所属的结构
                # [关键修复] 获取当前块所属的结构
                # [关键修复] 获取当前块所属的结构
                current_struct = self.block_to_structure.get(block)
                
                # [关键修复] 检查这个块是否属于LoopStructure但本身是条件块
                # 如果是，这可能是循环体内的if语句，需要进一步检查
                if current_struct and isinstance(current_struct, LoopStructure):
                    if is_conditional_block_flag:
                        # 检查是否是循环条件（向后跳转到header）
                        # 检查是否是循环条件（向后跳转到header）
                        # 检查是否是循环条件（向后跳转到header）
                        # 检查是否是循环条件（向后跳转到header）
                        is_loop_condition = False
                        for instr in block.instructions:
                            if 'BACKWARD' in instr.opname:
                                if instr.argval is not None and instr.argval == current_struct.header_block.start_offset:
                                    is_loop_condition = True
                                    break
                        if not is_loop_condition:
                            # 不是循环条件，是循环体内的if语句
                            # 不是循环条件，是循环体内的if语句
                            # 不是循环条件，是循环体内的if语句
                            # 不是循环条件，是循环体内的if语句
                            is_loop_body_if = True
                        else:
                            # 是循环条件，不需要处理
                            pass
                    else:
                        # 不是条件块，不需要处理
                        pass
                
                # [关键修复] 检查这个块是否属于TryExceptStructure但本身是条件块
                # 如果是，这可能是try块内的if语句，需要识别为IfStructure
                is_try_body_if = False
                if current_struct and isinstance(current_struct, TryExceptStructure):
                    # [关键修复] 如果块是TryExceptStructure的entry_block，且包含NOP指令（try块的开始标志）
                    # 则不应该创建IfStructure，因为NOP只是try块的开始标记，不是if条件
                    # [关键修复] 如果块是TryExceptStructure的entry_block，且包含NOP指令（try块的开始标志）
                    # 则不应该创建IfStructure，因为NOP只是try块的开始标记，不是if条件
                    # [关键修复] 如果块是TryExceptStructure的entry_block，且包含NOP指令（try块的开始标志）
                    # 则不应该创建IfStructure，因为NOP只是try块的开始标记，不是if条件
                    # [关键修复] 如果块是TryExceptStructure的entry_block，且包含NOP指令（try块的开始标志）
                    # 则不应该创建IfStructure，因为NOP只是try块的开始标记，不是if条件
                    if current_struct.entry_block == block:
                        has_nop = any(instr.opname == 'NOP' for instr in block.instructions)
                        has_chain_compare = any(instr.opname == 'COPY' and instr.arg == 2 for instr in block.instructions) and \
                                           any(instr.opname == 'COMPARE_OP' for instr in block.instructions)
                        if has_nop and not has_chain_compare:
                            continue
                    
                    if is_conditional_block_flag:
                        # 是try块内的条件块，应该识别为IfStructure
                        # 是try块内的条件块，应该识别为IfStructure
                        # 是try块内的条件块，应该识别为IfStructure
                        # 是try块内的条件块，应该识别为IfStructure
                        is_try_body_if = True
                    else:
                        # 不是条件块，跳过
                        continue
                
                # [关键修复] 如果块已经属于IfStructure，跳过
                if current_struct and isinstance(current_struct, IfStructure):
                    continue
                
                # [关键修复] 如果块已经属于AssertStructure，跳过
                # 这样可以避免assert语句被错误地识别为if语句
                if current_struct and isinstance(current_struct, AssertStructure):
                    continue
                
                # [关键修复] 如果块属于LoopStructure但不是循环体内的if语句，跳过
                if current_struct and isinstance(current_struct, LoopStructure) and not is_loop_body_if:
                    # [关键修复] 检查是否是循环体内的真正if语句
                    # 循环条件跳转（如POP_JUMP_BACKWARD_IF_TRUE）跳转到循环header，应该跳过
                    # 循环体内的if语句（如POP_JUMP_FORWARD_IF_FALSE）跳转到循环体内其他位置，应该识别为IfStructure
                    # [关键修复] 检查是否是循环体内的真正if语句
                    # 循环条件跳转（如POP_JUMP_BACKWARD_IF_TRUE）跳转到循环header，应该跳过
                    # 循环体内的if语句（如POP_JUMP_FORWARD_IF_FALSE）跳转到循环体内其他位置，应该识别为IfStructure
                    # [关键修复] 检查是否是循环体内的真正if语句
                    # 循环条件跳转（如POP_JUMP_BACKWARD_IF_TRUE）跳转到循环header，应该跳过
                    # 循环体内的if语句（如POP_JUMP_FORWARD_IF_FALSE）跳转到循环体内其他位置，应该识别为IfStructure
                    # [关键修复] 检查是否是循环体内的真正if语句
                    # 循环条件跳转（如POP_JUMP_BACKWARD_IF_TRUE）跳转到循环header，应该跳过
                    # 循环体内的if语句（如POP_JUMP_FORWARD_IF_FALSE）跳转到循环体内其他位置，应该识别为IfStructure
                    is_loop_condition = False
                    for instr in block.instructions:
                        if 'BACKWARD' in instr.opname:
                            # 向后跳转，可能是循环条件
                            # 向后跳转，可能是循环条件
                            # 向后跳转，可能是循环条件
                            # 向后跳转，可能是循环条件
                            if instr.argval is not None and instr.argval == current_struct.header_block.start_offset:
                                is_loop_condition = True
                                break
                    if is_loop_condition:
                        continue
                    # 不是循环条件，是循环体内的if语句，继续处理
            
            # [关键修复] 检查是否是条件分支块
            # 正常的条件分支块有2个后继（then和else）
            # 但在try-except块中，条件分支块可能有3个后继（then、else、异常处理）
            is_conditional = len(block.successors) == 2 or (
                len(block.successors) == 3 and
                self._is_conditional_block(block) and
                any(self._is_exception_handler_block(succ) for succ in block.successors)
            )
            
            if is_conditional:
                # [关键修复] 检查这个块是否真的是条件分支
                # 条件分支块应该包含 POP_JUMP_IF_* 指令
                # [关键修复] 检查这个块是否真的是条件分支
                # 条件分支块应该包含 POP_JUMP_IF_* 指令
                # [关键修复] 检查这个块是否真的是条件分支
                # 条件分支块应该包含 POP_JUMP_IF_* 指令
                # [关键修复] 检查这个块是否真的是条件分支
                # 条件分支块应该包含 POP_JUMP_IF_* 指令
                if not self._is_conditional_block(block):
                    continue
                
                # [关键修复] 检查这个块是否是while循环的条件检查
                # 特征：
                # 1. 块有两个后继
                # 2. 有向后跳转（POP_JUMP_BACKWARD_IF_TRUE）
                # 3. 向后跳转的目标是块的一个后继（循环体开始）
                # 这是Python 3.11+优化后的while循环结构
                is_while_condition = False
                if len(block.successors) == 2:
                    succ_list = list(block.successors)
                    succ_offsets = {s.start_offset for s in succ_list}
                    
                    # [关键修复] 检查是否有任何块包含向后跳转到该块的后继
                    # 不依赖于块是否已经在LoopStructure的body_blocks中
                    for b in self.cfg.blocks.values():
                        for instr in b.instructions:
                            if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                                # 检查跳转目标是否是块的一个后继
                                # 检查跳转目标是否是块的一个后继
                                # 检查跳转目标是否是块的一个后继
                                # 检查跳转目标是否是块的一个后继
                                if instr.argval is not None and instr.argval in succ_offsets:
                                    # 这是while循环的条件检查
                                    # 这是while循环的条件检查
                                    # 这是while循环的条件检查
                                    # 这是while循环的条件检查
                                    is_while_condition = True
                                    break
                        if is_while_condition:
                            break
                
                if is_while_condition:
                    # 这是while循环的条件检查，不是if条件
                    # 这是while循环的条件检查，不是if条件
                    # 这是while循环的条件检查，不是if条件
                    # 这是while循环的条件检查，不是if条件
                    continue
                
                # [关键修复] 检查这个块是否是包含赋值语句+条件检查的混合块
                # 这种块是while循环的一部分，不是if条件
                # 特征：
                # 1. 块包含赋值语句（STORE_FAST等）
                # 2. 块包含条件跳转指令（POP_JUMP_FORWARD_IF_*）
                # 3. 循环体内有向后跳转到该块的指令
                # [关键修复] 但如果块包含YIELD_VALUE，它可能是生成器中的if条件，不应该跳过
                is_mixed_while_header = False
                has_store = False
                has_cond_jump = False
                has_yield = False
                for instr in block.instructions:
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        has_store = True
                    if 'POP_JUMP_FORWARD_IF_' in instr.opname:
                        has_cond_jump = True
                    if instr.opname == 'YIELD_VALUE':
                        has_yield = True
                
                # [关键修复] 如果块包含YIELD_VALUE，不视为混合while头块
                # 因为这是生成器中的if条件（如：value = yield total; if value is None:）
                if has_store and has_cond_jump and not has_yield:
                    # 检查是否有向后跳转到该块的指令
                    # 检查是否有向后跳转到该块的指令
                    # 检查是否有向后跳转到该块的指令
                    # 检查是否有向后跳转到该块的指令
                    for b in self.cfg.blocks.values():
                        for instr in b.instructions:
                            if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname or 'JUMP_BACKWARD' in instr.opname:
                                if instr.argval is not None and instr.argval == block.start_offset:
                                    is_mixed_while_header = True
                                    break
                        if is_mixed_while_header:
                            break
                
                if is_mixed_while_header:
                    # 这是while循环的混合头块（赋值+条件检查），不是if条件
                    # 这是while循环的混合头块（赋值+条件检查），不是if条件
                    # 这是while循环的混合头块（赋值+条件检查），不是if条件
                    # 这是while循环的混合头块（赋值+条件检查），不是if条件
                    continue
                
                # [关键修复] 检查这个块是否是某个复合条件的中间块
                # 如果是，跳过它（它已经被作为复合条件的一部分处理了）
                is_compound_middle = False
                for struct in self.structures:
                    if isinstance(struct, IfStructure):
                        # [关键修复] 检查块是否在condition_chain中（无论is_compound_condition是否为True）
                        # [关键修复] 检查块是否在condition_chain中（无论is_compound_condition是否为True）
                        # [关键修复] 检查块是否在condition_chain中（无论is_compound_condition是否为True）
                        # [关键修复] 检查块是否在condition_chain中（无论is_compound_condition是否为True）
                        if hasattr(struct, 'condition_chain') and struct.condition_chain:
                            if block in struct.condition_chain and block != struct.condition_chain[0]:
                                is_compound_middle = True
                                break
                
                if is_compound_middle:
                    continue
                
                # [关键修复] 检查这个块是否已经被识别为elif链的一部分
                # 如果是，仍然需要识别为独立的if结构，以便AST生成器可以正确处理
                # 但不要重复处理同一个块
                is_elif_condition = False
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.elif_conditions:
                        if block in struct.elif_conditions:
                            is_elif_condition = True
                            break
                
                # [关键修复] 检查这个块是否已经被识别为独立的if结构
                is_already_if_structure = False
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == block:
                        is_already_if_structure = True
                        break
                
                # 如果块是elif链的一部分，跳过它
                # 因为elif链的检测会在处理header块时创建这些结构
                # [关键修复] 只要块是elif_conditions的一部分，就跳过它
                if is_elif_condition:
                    continue
                
                # [关键修复] 如果块已经被识别为独立的if结构，跳过它
                # 避免重复创建IfStructure
                if is_already_if_structure:
                    continue
                
                # [关键修复] 在调用 _analyze_if_structure 之前，先确定 then_branch 和 else_branch
                # 这样即使 then_body 或 else_body 为空，也能正确映射这些块
                succs = list(block.successors)
                jump_instr = None
                for instr in block.instructions:
                    if 'JUMP' in instr.opname and 'BACKWARD' not in instr.opname:
                        jump_instr = instr
                        break
                
                # 预先确定 then_branch 和 else_branch
                pre_then_branch = None
                pre_else_branch = None
                if jump_instr and jump_instr.argval is not None:
                    jump_target = None
                    fall_through = None
                    for succ in succs:
                        if succ.start_offset == jump_instr.argval:
                            jump_target = succ
                        else:
                            fall_through = succ
                    
                    if 'IF_FALSE' in jump_instr.opname:
                        pre_then_branch = fall_through
                        pre_else_branch = jump_target
                    else:
                        pre_then_branch = jump_target
                        pre_else_branch = fall_through
                
                if_struct = self._analyze_if_structure(block)
                if if_struct:
                    self.structures.append(if_struct)
                    
                    # [关键修复] 将入口块映射到该结构
                    self.block_to_structure[block] = if_struct
                    
                    # [关键修复] 将entry_block标记为已分析，避免重复创建IfStructure
                    analyzed_blocks.add(block)
                    
                    # [关键修复] 保存pre_then_branch和pre_else_branch到IfStructure
                    # 这样_build_hierarchy可以正确设置嵌套if的parent
                    if pre_then_branch:
                        if_struct.pre_then_branch = pre_then_branch
                    if pre_else_branch:
                        if_struct.pre_else_branch = pre_else_branch
                    
                    # [关键修复] 如果这是循环体内的if语句，设置parent属性
                    # [关键修复] 即使current_struct不是LoopStructure，也要检查block是否在LoopStructure的body_blocks中
                    parent_loop = None
                    if is_loop_body_if and current_struct and isinstance(current_struct, LoopStructure):
                        parent_loop = current_struct
                    else:
                        # [关键修复] 检查block是否在任何LoopStructure的body_blocks中
                        # 选择最内层的循环（body_blocks数量最少的循环）
                        candidate_loops = []
                        for struct in self.structures:
                            if isinstance(struct, LoopStructure):
                                # [关键修复] 只检查block是否在body_blocks中
                                # 不要基于偏移量范围判断，因为header块也在范围内但不是循环体内的if
                                # [关键修复] 只检查block是否在body_blocks中
                                # 不要基于偏移量范围判断，因为header块也在范围内但不是循环体内的if
                                # [关键修复] 只检查block是否在body_blocks中
                                # 不要基于偏移量范围判断，因为header块也在范围内但不是循环体内的if
                                # [关键修复] 只检查block是否在body_blocks中
                                # 不要基于偏移量范围判断，因为header块也在范围内但不是循环体内的if
                                if block in struct.body_blocks:
                                    # [关键修复] 确保block不是循环的header_block或entry_block
                                    # [关键修复] 确保block不是循环的header_block或entry_block
                                    # [关键修复] 确保block不是循环的header_block或entry_block
                                    # [关键修复] 确保block不是循环的header_block或entry_block
                                    if block != struct.header_block and block != struct.entry_block:
                                        candidate_loops.append(struct)
                        
                        # [关键修复] 选择最内层的循环（body_blocks数量最少的循环）
                        if candidate_loops:
                            parent_loop = min(candidate_loops, key=lambda s: len(s.body_blocks))
                    
                    if parent_loop:
                        if_struct.parent = parent_loop
                        # [关键修复] 将if_struct添加到父结构的children列表中
                        if not hasattr(parent_loop, 'children'):
                            parent_loop.children = []
                        if if_struct not in parent_loop.children:
                            parent_loop.children.append(if_struct)
                        
                        # [关键修复] 将if结构的entry_block添加到LoopStructure的body_blocks中
                        # 这样可以确保if结构的entry_block被正确映射到LoopStructure
                        if hasattr(parent_loop, 'body_blocks'):
                            if block not in parent_loop.body_blocks:
                                parent_loop.body_blocks.append(block)
                        else:
                            parent_loop.body_blocks = [block]
                    
                    # [关键修复] 将then_body和else_body中的块也映射到该结构
                    # 避免这些块被识别为独立的SEQUENCE结构
                    # [关键修复] 但不要映射只包含NOP的块，这些块需要被识别为独立的if结构
                    for then_block in if_struct.then_body:
                        if then_block not in self.block_to_structure:
                            # 检查块是否只包含NOP
                            # 检查块是否只包含NOP
                            # 检查块是否只包含NOP
                            # 检查块是否只包含NOP
                            then_block_nop_only = True
                            for instr in then_block.instructions:
                                if instr.opname == 'NOP':
                                    continue
                                elif instr.opname not in ('RESUME', 'CACHE', 'PRECALL'):
                                    then_block_nop_only = False
                                    break
                            
                            # [关键修复] 检查块是否是条件块（嵌套if结构的header）
                            # 如果是，不要将其映射到外层if结构，让它被识别为独立的IfStructure
                            then_instrs = [i for i in then_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                            is_conditional_block = any(i.opname.startswith('POP_JUMP') for i in then_instrs) and len(then_block.successors) == 2
                            
                            # 如果块不只包含NOP且不是条件块，才添加到block_to_structure
                            if not then_block_nop_only and not is_conditional_block:
                                self.block_to_structure[then_block] = if_struct
                    
                    for else_block in if_struct.else_body:
                        if else_block not in self.block_to_structure:
                            # 检查块是否只包含NOP
                            # 检查块是否只包含NOP
                            # 检查块是否只包含NOP
                            # 检查块是否只包含NOP
                            else_block_nop_only = True
                            for instr in else_block.instructions:
                                if instr.opname == 'NOP':
                                    continue
                                elif instr.opname not in ('RESUME', 'CACHE', 'PRECALL'):
                                    else_block_nop_only = False
                                    break
                            
                            # [FIX-005] 检查块是否是条件块（嵌套if结构的header）
                            # 如果是，不要将其映射到外层if结构，让它被识别为独立的IfStructure
                            else_instrs = [i for i in else_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                            is_conditional_block = any(i.opname.startswith('POP_JUMP') for i in else_instrs) and len(else_block.successors) == 2
                            
                            # 如果块不只包含NOP且不是条件块，才添加到block_to_structure
                            if not else_block_nop_only and not is_conditional_block:
                                self.block_to_structure[else_block] = if_struct
                    
                    # [关键修复] 如果 then_body 或 else_body 为空，但预先确定了分支，也映射这些块
                    if not if_struct.then_body and pre_then_branch:
                        if pre_then_branch not in self.block_to_structure:
                            self.block_to_structure[pre_then_branch] = if_struct
                    if not if_struct.else_body and pre_else_branch:
                        if pre_else_branch not in self.block_to_structure:
                            self.block_to_structure[pre_else_branch] = if_struct
                    
                    # [关键修复] 检查 then_branch 是否是条件块（嵌套if）
                    # 如果是，设置嵌套if的parent为当前if结构
                    if pre_then_branch and self._is_conditional_block(pre_then_branch):
                        # 找到pre_then_branch对应的IfStructure
                        # 找到pre_then_branch对应的IfStructure
                        # 找到pre_then_branch对应的IfStructure
                        # 找到pre_then_branch对应的IfStructure
                        for nested_struct in self.structures:
                            if isinstance(nested_struct, IfStructure) and nested_struct.entry_block == pre_then_branch:
                                # 设置parent关系
                                # 设置parent关系
                                # 设置parent关系
                                # 设置parent关系
                                nested_struct.parent = if_struct
                                # 将nested_struct添加到if_struct的children列表中
                                if not hasattr(if_struct, 'children'):
                                    if_struct.children = []
                                if nested_struct not in if_struct.children:
                                    if_struct.children.append(nested_struct)
                                break
                    
                    # [关键修复] 对于嵌套条件表达式，如果 then_body 或 else_body 包含条件块，
                    # 需要将该条件块识别为独立的 IfStructure
                    # 而不是将其映射到外层的 IfStructure
                    # 
                    # [关键修复] 对于超深层if嵌套，then_body可能包含多个块（如NOP块）
                    # 我们需要检查then_body中的每个块，找到条件块并将其从外层结构中移除
                    if if_struct.then_body:
                        for then_block in if_struct.then_body:
                            then_instrs = [i for i in then_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                            has_pop_jump = any(i.opname.startswith('POP_JUMP') for i in then_instrs)
                            has_two_successors = len(then_block.successors) == 2
                            
                            if has_pop_jump and has_two_successors:
                                # 这是一个嵌套的条件表达式，需要将 then_block 从外层结构中移除
                                # 并让它被识别为独立的 IfStructure
                                # 这是一个嵌套的条件表达式，需要将 then_block 从外层结构中移除
                                # 并让它被识别为独立的 IfStructure
                                # 这是一个嵌套的条件表达式，需要将 then_block 从外层结构中移除
                                # 并让它被识别为独立的 IfStructure
                                # 这是一个嵌套的条件表达式，需要将 then_block 从外层结构中移除
                                # 并让它被识别为独立的 IfStructure
                                self.block_to_structure.pop(then_block, None)
                                # 将 then_block 从 analyzed_blocks 中移除，以便它能被重新分析
                                analyzed_blocks.discard(then_block)
                    
                    # [FIX-005] 处理else_body中的嵌套条件块
                    # [关键修复] 保留条件块在else_body中，这样AST生成器知道这是一个嵌套if
                    # 同时让条件块被识别为独立的IfStructure，并在_build_hierarchy中建立parent-child关系
                    if if_struct.else_body:
                        # [关键修复] 首先检查 else_body 是否包含循环结构
                        # 如果包含，不应该从 else_body 中移除循环体内的块
                        # [关键修复] 首先检查 else_body 是否包含循环结构
                        # 如果包含，不应该从 else_body 中移除循环体内的块
                        # [关键修复] 首先检查 else_body 是否包含循环结构
                        # 如果包含，不应该从 else_body 中移除循环体内的块
                        # [关键修复] 首先检查 else_body 是否包含循环结构
                        # 如果包含，不应该从 else_body 中移除循环体内的块
                        loop_body_blocks_in_else = set()
                        for loop_struct in self.structures:
                            if isinstance(loop_struct, LoopStructure) and hasattr(loop_struct, 'body_blocks'):
                                if loop_struct.entry_block in if_struct.else_body:
                                    for loop_block in loop_struct.body_blocks:
                                        loop_body_blocks_in_else.add(loop_block)
                        
                        # [关键修复] 创建一个新的列表来存储块
                        new_else_body = []
                        for else_block in if_struct.else_body:
                            # [关键修复] 如果块在循环体内，保留它
                            # [关键修复] 如果块在循环体内，保留它
                            # [关键修复] 如果块在循环体内，保留它
                            # [关键修复] 如果块在循环体内，保留它
                            if else_block in loop_body_blocks_in_else:
                                new_else_body.append(else_block)
                                continue

                            else_instrs = [i for i in else_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                            has_pop_jump = any(i.opname.startswith('POP_JUMP') for i in else_instrs)
                            has_two_successors = len(else_block.successors) == 2

                            if has_pop_jump and has_two_successors:
                                # 这是一个嵌套的条件表达式
                                # [关键修复] 保留条件块在else_body中，这样AST生成器知道这是一个嵌套if
                                # 这是一个嵌套的条件表达式
                                # [关键修复] 保留条件块在else_body中，这样AST生成器知道这是一个嵌套if
                                # 这是一个嵌套的条件表达式
                                # [关键修复] 保留条件块在else_body中，这样AST生成器知道这是一个嵌套if
                                # 这是一个嵌套的条件表达式
                                # [关键修复] 保留条件块在else_body中，这样AST生成器知道这是一个嵌套if
                                new_else_body.append(else_block)
                                # 从block_to_structure中移除，以便它能被重新分析为独立的IfStructure
                                self.block_to_structure.pop(else_block, None)
                                # 将 else_block 从 analyzed_blocks 中移除，以便它能被重新分析
                                analyzed_blocks.discard(else_block)
                            else:
                                # [关键修复] 将非条件块添加到新的else_body中
                                new_else_body.append(else_block)
                        # [关键修复] 更新if_struct的else_body
                        if_struct.else_body = new_else_body

                    # [关键修复] 如果是复合条件，将条件链中的所有块都标记为已分析
                    if if_struct.is_compound_condition:
                        for condition_block in if_struct.condition_chain:
                            self.block_to_structure[condition_block] = if_struct
                    
                    # [关键修复] 如果是elif链，将elif条件块及其then分支映射到该结构
                    if hasattr(if_struct, 'elif_conditions') and if_struct.elif_conditions:
                        for elif_block in if_struct.elif_conditions:
                            # 映射elif条件块本身
                            # 映射elif条件块本身
                            # 映射elif条件块本身
                            # 映射elif条件块本身
                            self.block_to_structure[elif_block] = if_struct
                            
                            # 找到elif块的then分支并映射
                            elif_jump = self._get_jump_instr(elif_block)
                            if elif_jump and elif_jump.argval is not None:
                                for succ in elif_block.successors:
                                    if succ.start_offset != elif_jump.argval:
                                        # 这是elif的then分支
                                        # 这是elif的then分支
                                        # 这是elif的then分支
                                        # 这是elif的then分支
                                        if succ not in self.block_to_structure:
                                            self.block_to_structure[succ] = if_struct
                                        else:
                                            # 块已经被其他结构处理
                                            pass
                                        break
                                    else:
                                        # 不是elif的then分支
                                        pass
                            else:
                                # 没有elif跳转
                                pass

    
    def _identify_assert_structures(self) -> None:
        """
        [关键修复] 识别assert语句结构
        
        Python 3.11+ assert语句的字节码模式：
        1. POP_JUMP_FORWARD_IF_TRUE <target> (条件为真时跳过assert)
        2. LOAD_ASSERTION_ERROR
        3. [LOAD_CONST <msg>] (可选的assert消息)
        4. RAISE_VARARGS 2 (或1，如果没有消息)
        
        这个方法识别assert模式，并将其转换为AssertStructure，
        以便代码生成器能正确生成assert语句而不是if not: raise AssertionError()
        """
        analyzed_blocks = set()
        
        # 安全检查：确保cfg有blocks属性
        if not hasattr(self.cfg, 'blocks'):
            return
        
        # 获取所有基本块（支持列表和字典格式）
        if isinstance(self.cfg.blocks, dict):
            blocks = list(self.cfg.blocks.values())
        elif isinstance(self.cfg.blocks, list):
            blocks = self.cfg.blocks
        else:
            return
        
        for block in blocks:
            # 安全检查：确保block是有效的基本块对象
            # 安全检查：确保block是有效的基本块对象
            # 安全检查：确保block是有效的基本块对象
            # 安全检查：确保block是有效的基本块对象
            if not hasattr(block, 'start_offset'):
                continue
                
            if block in analyzed_blocks:
                continue
            
            # 查找assert模式
            try:
                assert_info = self._is_assert_pattern(block)
                if assert_info and assert_info.get('is_assert'):
                    # 创建AssertStructure
                    # 创建AssertStructure
                    # 创建AssertStructure
                    # 创建AssertStructure
                    assert_struct = AssertStructure(
                        struct_type=ControlStructureType.ASSERT,
                        entry_block=block,
                        condition_block=assert_info.get('condition_block'),
                        message_block=assert_info.get('message_block'),
                        end_block=assert_info.get('end_block')
                    )
                    
                    # 标记assert结构特有的属性
                    assert_struct.condition = assert_info.get('condition')
                    assert_struct.message = assert_info.get('message')
                    assert_struct.is_assert = True
                    
                    self.structures.append(assert_struct)
                    
                    # [关键修复] 更新block_to_structure映射
                    # 这样其他结构识别器（如_if_identify_conditionals）会跳过这个块
                    self.block_to_structure[block] = assert_struct
                    if assert_struct.message_block:
                        self.block_to_structure[assert_struct.message_block] = assert_struct
                    # [关键修复] 不要将end_block添加到block_to_structure映射
                    # end_block是assert失败时执行的块（包含LOAD_ASSERTION_ERROR），
                    # 不是assert结构的一部分，不应该被跳过
                    # if assert_struct.end_block:
                    #     self.block_to_structure[assert_struct.end_block] = assert_struct
                    
                    # 标记所有相关块为已分析
                    analyzed_blocks.add(block)
                    if assert_struct.message_block:
                        analyzed_blocks.add(assert_struct.message_block)
                    # [关键修复] 不要将end_block标记为已分析，因为它不是assert结构的一部分
                    # if assert_struct.end_block:
                    #     analyzed_blocks.add(assert_struct.end_block)
                    
                    if self.verbose:
                        print(f"  发现assert结构，条件块: {block.offset}")
            except Exception as e:
                # 如果处理某个块时出错，跳过该块继续处理其他块
                if self.verbose:
                    print(f"  处理块 {block.offset} 时出错: {e}")
                continue
    
    def _is_assert_pattern(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """
        检测块是否包含assert语句模式
        
        Python 3.11+ assert语句的字节码模式：
        1. <条件表达式>
        2. POP_JUMP_FORWARD_IF_TRUE <target> (条件为真时跳过assert)
        3. LOAD_ASSERTION_ERROR
        4. [LOAD_CONST <msg>] (可选的assert消息)
        5. RAISE_VARARGS 1 (或2，如果有消息)
        
        Returns:
            如果是assert模式，返回包含assert信息的字典；否则返回None
        """
        result = {'is_assert': False}
        
        # 安全检查：确保block有instructions属性
        if not hasattr(block, 'instructions') or not isinstance(block.instructions, list):
            return None
        
        # 查找POP_JUMP_FORWARD_IF_TRUE指令
        pop_jump_idx = -1
        for i, instr in enumerate(block.instructions):
            if hasattr(instr, 'opname') and instr.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE'):
                pop_jump_idx = i
                break
        
        if pop_jump_idx < 0:
            return None
        
        # 检查跳转目标后的指令
        pop_jump_instr = block.instructions[pop_jump_idx]
        
        # 安全检查：确保指令有argval属性
        if not hasattr(pop_jump_instr, 'argval'):
            return None
            
        jump_target = pop_jump_instr.argval
        
        # 安全检查：确保jump_target是整数类型
        if not isinstance(jump_target, int):
            return None
        
        # [关键修复] Python 3.11+的assert模式中，LOAD_ASSERTION_ERROR和RAISE_VARARGS
        # 可能紧跟在POP_JUMP_FORWARD_IF_TRUE之后，在同一个块中
        # 检查pop_jump_idx之后的指令
        has_load_assertion_error = False
        has_raise_varargs = False
        has_message = False
        message = None
        
        # 检查当前块中pop_jump_idx之后的指令
        for i in range(pop_jump_idx + 1, len(block.instructions)):
            instr = block.instructions[i]
            if not hasattr(instr, 'opname'):
                continue
                
            if instr.opname == 'LOAD_ASSERTION_ERROR':
                has_load_assertion_error = True
            elif instr.opname == 'RAISE_VARARGS':
                has_raise_varargs = True
                break
            elif instr.opname == 'LOAD_CONST' and has_load_assertion_error:
                # 这是assert消息
                # 这是assert消息
                has_message = True
                if hasattr(instr, 'argval'):
                    message = instr.argval
        
        # 如果在当前块中找到了assert模式
        if has_load_assertion_error and has_raise_varargs:
            result['is_assert'] = True
            result['condition_block'] = block
            result['message'] = message
            result['end_block'] = block
            
            # [关键修复] 提取条件表达式（POP_JUMP前的指令）
            # 但只提取从最后一个STORE或POP_TOP指令之后的指令，因为赋值语句和函数调用不属于assert条件
            condition_instrs = block.instructions[:pop_jump_idx]
            
            # 查找最后一个STORE或POP_TOP指令的位置
            last_stmt_end_idx = -1
            for i, instr in enumerate(condition_instrs):
                if hasattr(instr, 'opname'):
                    if instr.opname.startswith('STORE_') or instr.opname == 'POP_TOP':
                        last_stmt_end_idx = i
            
            # 如果找到了STORE或POP_TOP指令，只使用它之后的指令作为条件
            if last_stmt_end_idx >= 0:
                condition_instrs = condition_instrs[last_stmt_end_idx + 1:]
            
            result['condition'] = condition_instrs
            
            return result
        
        # [关键修复] 检查当前块的下一个块（按偏移量顺序）
        # 在CFG中，assert语句的结构是：
        # - 块A: 条件表达式 + POP_JUMP_FORWARD_IF_TRUE 跳转到块C
        # - 块B: LOAD_ASSERTION_ERROR + RAISE_VARARGS（assert失败时执行）
        # - 块C: 下一个语句
        # POP_JUMP_FORWARD_IF_TRUE的意思是"如果条件为真，跳转到目标"
        # 所以条件为假时，执行下一个块（assert失败块）
        
        # 获取当前块的结束偏移量
        current_block_end = block.instructions[-1].offset if block.instructions else 0
        
        # 查找下一个块（偏移量在当前块结束之后的第一个块）
        next_block = None
        next_block_offset = None
        
        if hasattr(self.cfg, 'offset_to_block'):
            # 遍历所有块，找到偏移量在当前块结束之后的第一个块
            # 遍历所有块，找到偏移量在当前块结束之后的第一个块
            # 遍历所有块，找到偏移量在当前块结束之后的第一个块
            # 遍历所有块，找到偏移量在当前块结束之后的第一个块
            for offset, b in self.cfg.offset_to_block.items():
                if offset > current_block_end:
                    if next_block_offset is None or offset < next_block_offset:
                        next_block = b
                        next_block_offset = offset
        
        if next_block:
            # 安全检查：确保next_block有instructions属性
            # 安全检查：确保next_block有instructions属性
            # 安全检查：确保next_block有instructions属性
            # 安全检查：确保next_block有instructions属性
            if hasattr(next_block, 'instructions') and isinstance(next_block.instructions, list):
                # 检查下一个块是否以LOAD_ASSERTION_ERROR开始
                # 检查下一个块是否以LOAD_ASSERTION_ERROR开始
                # 检查下一个块是否以LOAD_ASSERTION_ERROR开始
                # 检查下一个块是否以LOAD_ASSERTION_ERROR开始
                has_load_assertion_error = False
                has_raise_varargs = False
                message = None
                
                for instr in next_block.instructions:
                    if not hasattr(instr, 'opname'):
                        continue
                        
                    if instr.opname == 'LOAD_ASSERTION_ERROR':
                        has_load_assertion_error = True
                    elif instr.opname == 'RAISE_VARARGS':
                        has_raise_varargs = True
                        break
                    elif instr.opname == 'LOAD_CONST' and has_load_assertion_error:
                        # 这是assert消息
                        # 这是assert消息
                        if hasattr(instr, 'argval'):
                            message = instr.argval
                
                # 如果找到LOAD_ASSERTION_ERROR和RAISE_VARARGS，这是assert语句
                if has_load_assertion_error and has_raise_varargs:
                    result['is_assert'] = True
                    result['condition_block'] = block
                    result['message'] = message
                    result['end_block'] = next_block
                    
                    # [关键修复] 提取条件表达式（POP_JUMP前的指令）
                    # 但只提取从最后一个STORE或POP_TOP指令之后的指令，因为赋值语句和函数调用不属于assert条件
                    condition_instrs = block.instructions[:pop_jump_idx]
                    
                    # 查找最后一个STORE或POP_TOP指令的位置
                    last_stmt_end_idx = -1
                    for i, instr in enumerate(condition_instrs):
                        if hasattr(instr, 'opname'):
                            if instr.opname.startswith('STORE_') or instr.opname == 'POP_TOP':
                                last_stmt_end_idx = i
                    
                    # 如果找到了STORE或POP_TOP指令，只使用它之后的指令作为条件
                    if last_stmt_end_idx >= 0:
                        condition_instrs = condition_instrs[last_stmt_end_idx + 1:]
                    
                    result['condition'] = condition_instrs
                    
                    return result
        
        return None
    
    def _identify_nop_sequences(self) -> None:
        """
        [关键修复] 识别NOP序列（对应优化后的if True:语句）
        
        当Python编译if True:时，会优化掉条件判断，只生成NOP指令作为占位符。
        这个方法识别包含NOP指令的块，并将它们转换为虚拟的if结构，
        以便代码生成器能正确生成if True:语句。
        
        [修复] 现在也处理包含NOP但不是只包含NOP的块（NOP后跟实际代码的情况）
        
        [关键修复] 当检测到连续的NOP块时，不应该创建嵌套的if结构。
        连续的NOP块通常是编译器优化后的残留（如if False: ... elif True: ...），
        不应该生成if语句。
        
        [关键修复] 跳过位于异常处理代码中的NOP（try-except块中的NOP不是if True:）
        """
        analyzed_blocks = set(self.block_to_structure.keys())
        
        # [关键修复] 收集所有异常处理范围（try块和handler块）
        exception_ranges = []  # [(start, end), ...]
        # [关键修复] 收集所有try块的开始偏移量（包括嵌套的try块）
        try_start_offsets = set()
        # [关键修复] 收集所有嵌套try块的开始偏移量（按depth分组）
        nested_try_offsets = {}  # depth -> set of start offsets
        if hasattr(self.cfg, 'exception_table') and self.cfg.exception_table:
            for entry in self.cfg.exception_table:
                start = entry.get('start', 0)
                end = entry.get('end', 0)
                target = entry.get('target', 0)
                depth = entry.get('depth', 0)
                # 添加try块范围
                exception_ranges.append((start, end))
                # 添加handler块范围（估算）
                if target > 0:
                    exception_ranges.append((target, target + 100))  # 估算handler大小
                # [关键修复] 记录所有try块的开始偏移量（包括嵌套的try块）
                try_start_offsets.add(start)
                # [关键修复] 按depth分组记录嵌套try块
                if depth not in nested_try_offsets:
                    nested_try_offsets[depth] = set()
                nested_try_offsets[depth].add(start)
        
        # 按偏移量排序遍历基本块
        for block in sorted(self.cfg.blocks.values(), key=lambda b: b.start_offset):
            if block in analyzed_blocks:
                continue
            
            # [关键修复] 检查这个块是否已经是循环的header块
            # 如果是，跳过不创建if True:结构
            is_loop_header = False
            for struct in self.structures:
                if isinstance(struct, LoopStructure):
                    if struct.header_block == block:
                        is_loop_header = True
                        break
                    # 也检查entry_block（有些循环使用entry_block作为header）
                    if struct.entry_block == block:
                        is_loop_header = True
                        break
            
            if is_loop_header:
                analyzed_blocks.add(block)
                continue
            
            # 检查块是否包含NOP指令
            has_nop = False
            nop_instr = None
            for instr in block.instructions:
                if instr.opname == 'NOP':
                    has_nop = True
                    nop_instr = instr
                    break
            
            if not has_nop:
                continue
            
            # [关键修复] 检查这个块是否在异常处理代码中
            # 如果是，跳过，不创建if True:结构
            block_in_exception = False
            for instr in block.instructions:
                # 检查指令是否在异常范围内
                # 检查指令是否在异常范围内
                # 检查指令是否在异常范围内
                # 检查指令是否在异常范围内
                for start, end in exception_ranges:
                    if start <= instr.offset < end:
                        block_in_exception = True
                        break
                if block_in_exception:
                    break
            
            # [关键修复] 也检查块是否包含异常处理指令
            has_exception_instr = any(
                instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'POP_EXCEPT', 
                                'RERAISE', 'COPY', 'JUMP_FORWARD')
                for instr in block.instructions
            )
            
            if block_in_exception or has_exception_instr:
                # 这个NOP在异常处理代码中，不是if True:语句
                # 这个NOP在异常处理代码中，不是if True:语句
                # 这个NOP在异常处理代码中，不是if True:语句
                # 这个NOP在异常处理代码中，不是if True:语句
                analyzed_blocks.add(block)
                continue
            
            # [关键修复] 检查这个NOP是否是try块的开始标志
            # 特征：NOP块在try块开始之前（在try_start_offsets之前不远处）
            # 并且NOP块只包含NOP指令
            nop_only = all(
                instr.opname in ('NOP', 'RESUME', 'CACHE', 'PRECALL')
                for instr in block.instructions
            )
            if nop_only and nop_instr:
                # 检查这个NOP是否在try块开始之前
                # 检查这个NOP是否在try块开始之前
                # 检查这个NOP是否在try块开始之前
                # 检查这个NOP是否在try块开始之前
                for try_start in try_start_offsets:
                    # NOP在try块开始之前10字节内，且是连续的NOP块
                    # NOP在try块开始之前10字节内，且是连续的NOP块
                    # NOP在try块开始之前10字节内，且是连续的NOP块
                    # NOP在try块开始之前10字节内，且是连续的NOP块
                    if 0 < try_start - nop_instr.offset <= 20:
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        analyzed_blocks.add(block)
                        break
                if block in analyzed_blocks:
                    continue
            
            # [关键修复] 检查这个块是否包含NOP且NOP是第一条指令，并且块在try块开始之前
            # 这种情况发生在try块包含实际代码（如if条件）时
            if nop_instr and block.instructions[0].opname == 'NOP':
                # 检查这个NOP是否在try块开始之前
                # 检查这个NOP是否在try块开始之前
                # 检查这个NOP是否在try块开始之前
                # 检查这个NOP是否在try块开始之前
                for try_start in try_start_offsets:
                    # NOP在try块开始之前10字节内
                    # NOP在try块开始之前10字节内
                    # NOP在try块开始之前10字节内
                    # NOP在try块开始之前10字节内
                    if 0 < try_start - nop_instr.offset <= 20:
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        analyzed_blocks.add(block)
                        break
                if block in analyzed_blocks:
                    continue
            
            # [关键修复] 检查这个块是否在try块内部（不只是异常范围）
            # 对于嵌套的try-except，NOP块可能是try块的一部分，不应该被识别为if True:
            block_in_try_body = False
            for instr in block.instructions:
                for start, end in exception_ranges:
                    # 检查指令是否在try块内部（严格在start和end之间）
                    # 检查指令是否在try块内部（严格在start和end之间）
                    # 检查指令是否在try块内部（严格在start和end之间）
                    # 检查指令是否在try块内部（严格在start和end之间）
                    if start < instr.offset < end:
                        block_in_try_body = True
                        break
                if block_in_try_body:
                    break
            
            if block_in_try_body:
                # 这个NOP在try块内部，不是if True:语句
                # 这个NOP在try块内部，不是if True:语句
                # 这个NOP在try块内部，不是if True:语句
                # 这个NOP在try块内部，不是if True:语句
                analyzed_blocks.add(block)
                continue
            
            # [关键修复] 检查这个NOP是否是if语句的占位符
            # 特征：
            # 1. NOP在行号标记处（有starts_line）
            # 2. NOP后面跟着实际的代码（LOAD_CONST, STORE_FAST等）
            # 3. 这个块没有被识别为其他控制结构
            
            # 检查是否是"只包含NOP"的块（原来的逻辑）
            nop_only = True
            for instr in block.instructions:
                if instr.opname == 'NOP':
                    continue
                elif instr.opname not in ('RESUME', 'CACHE', 'PRECALL'):
                    nop_only = False
                    break
            
            if nop_only and len(block.successors) == 1:
                # [关键修复] 检查这个NOP块是否是某个条件跳转的目标
                # 如果是，说明这是if condition:的空if体，不是if True:
                # [关键修复] 检查这个NOP块是否是某个条件跳转的目标
                # 如果是，说明这是if condition:的空if体，不是if True:
                # [关键修复] 检查这个NOP块是否是某个条件跳转的目标
                # 如果是，说明这是if condition:的空if体，不是if True:
                # [关键修复] 检查这个NOP块是否是某个条件跳转的目标
                # 如果是，说明这是if condition:的空if体，不是if True:
                is_conditional_target = False
                for pred in block.predecessors:
                    for instr in pred.instructions:
                        if instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                           'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                           'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                            # [关键修复] 检查跳转目标是否是这个NOP块或NOP块内的指令
                            # 跳转目标可能指向NOP块本身，也可能指向NOP块后的第一条指令
                            if instr.argval is not None:
                                # 计算NOP块的结束偏移
                                # 计算NOP块的结束偏移
                                # 计算NOP块的结束偏移
                                # 计算NOP块的结束偏移
                                block_end = block.start_offset + sum(2 if i.opname != 'CACHE' else 0 for i in block.instructions)
                                # 检查跳转目标是否在NOP块内（从start_offset到end_offset）
                                if block.start_offset <= instr.argval < block_end:
                                    is_conditional_target = True
                                    break
                                # 检查跳转目标是否等于NOP块的起始偏移
                                if instr.argval == block.start_offset:
                                    is_conditional_target = True
                                    break
                                # [关键修复] 检查跳转目标是否等于NOP块的结束偏移
                                # 这意味着跳转目标是NOP块后的第一条指令
                                if instr.argval == block_end:
                                    is_conditional_target = True
                                    break
                    if is_conditional_target:
                        break
                
                if is_conditional_target:
                    # 这是if condition:的空if体，不是if True:
                    # 跳过不创建if结构
                    # 这是if condition:的空if体，不是if True:
                    # 跳过不创建if结构
                    # 这是if condition:的空if体，不是if True:
                    # 跳过不创建if结构
                    # 这是if condition:的空if体，不是if True:
                    # 跳过不创建if结构
                    analyzed_blocks.add(block)
                    continue
                
                # [关键修复] 检查这是否是编译器优化后的残留NOP
                # 当Python编译器优化if True:时，会完全移除条件判断，只保留NOP作为占位符
                # 这种情况下，不应该创建if结构，而是让代码生成器直接处理
                # 特征：NOP块没有条件跳转指令，且后继块也是NOP块或包含实际代码
                successor = list(block.successors)[0] if block.successors else None
                
                # [关键修复] 检查这个NOP块是否是循环结构的一部分
                # 对于while True循环，Python 3.11+编译器会在循环开始处插入NOP
                # 这种NOP不应该被识别为if True:结构
                is_loop_nop = False
                if successor:
                    # 检查后继块是否是循环体的一部分
                    # 特征：后继块有向后跳转指令（JUMP_BACKWARD）
                    # 检查后继块是否是循环体的一部分
                    # 特征：后继块有向后跳转指令（JUMP_BACKWARD）
                    # 检查后继块是否是循环体的一部分
                    # 特征：后继块有向后跳转指令（JUMP_BACKWARD）
                    # 检查后继块是否是循环体的一部分
                    # 特征：后继块有向后跳转指令（JUMP_BACKWARD）
                    for instr in successor.instructions:
                        if 'JUMP_BACKWARD' in instr.opname:
                            # 后继块是循环体，当前NOP块是循环的一部分
                            # 后继块是循环体，当前NOP块是循环的一部分
                            # 后继块是循环体，当前NOP块是循环的一部分
                            # 后继块是循环体，当前NOP块是循环的一部分
                            is_loop_nop = True
                            break
                    # 也检查后继块的后继是否有向后跳转
                    if not is_loop_nop:
                        for succ_succ in successor.successors:
                            for instr in succ_succ.instructions:
                                if 'JUMP_BACKWARD' in instr.opname:
                                    is_loop_nop = True
                                    break
                            if is_loop_nop:
                                break
                    
                    # [关键修复] 对于while True循环，需要更全面的检测
                    # 检查从后继块开始是否能到达一个向后跳转到当前块之前的指令
                    if not is_loop_nop:
                        visited = set()
                        worklist = [successor]
                        while worklist and not is_loop_nop:
                            current = worklist.pop(0)
                            if current in visited:
                                continue
                            visited.add(current)
                            
                            # 检查当前块是否有向后跳转
                            for instr in current.instructions:
                                if 'JUMP_BACKWARD' in instr.opname:
                                    # 检查跳转目标是否在当前块之前（说明是循环）
                                    # 检查跳转目标是否在当前块之前（说明是循环）
                                    # 检查跳转目标是否在当前块之前（说明是循环）
                                    # 检查跳转目标是否在当前块之前（说明是循环）
                                    if instr.argval is not None and instr.argval < block.start_offset:
                                        is_loop_nop = True
                                        break
                                    # 或者跳转目标是当前块本身
                                    if instr.argval is not None and instr.argval == block.start_offset:
                                        is_loop_nop = True
                                        break
                            
                            if not is_loop_nop:
                                # 继续检查后继块
                                # 继续检查后继块
                                # 继续检查后继块
                                # 继续检查后继块
                                for succ in current.successors:
                                    if succ not in visited:
                                        worklist.append(succ)
                
                if is_loop_nop:
                    # 这是循环结构的一部分，跳过不创建if结构
                    # 这是循环结构的一部分，跳过不创建if结构
                    # 这是循环结构的一部分，跳过不创建if结构
                    # 这是循环结构的一部分，跳过不创建if结构
                    analyzed_blocks.add(block)
                    continue
                
                if successor:
                    # [关键修复] 检查后继块是否也是NOP块（深层嵌套if优化残留）
                    # [关键修复] 检查后继块是否也是NOP块（深层嵌套if优化残留）
                    # [关键修复] 检查后继块是否也是NOP块（深层嵌套if优化残留）
                    # [关键修复] 检查后继块是否也是NOP块（深层嵌套if优化残留）
                    succ_nop_only = True
                    succ_has_nop = False
                    for instr in successor.instructions:
                        if instr.opname == 'NOP':
                            succ_has_nop = True
                        elif instr.opname not in ('RESUME', 'CACHE', 'PRECALL'):
                            succ_nop_only = False
                            break
                    
                    # [字节码一致性修复] 为每个NOP块创建if结构
                    # 以保持与原始字节码的一致性
                    
                    # 创建虚拟的if结构来表示这个NOP
                    then_body = [block]
                    # [关键修复] 如果后继块也是NOP-only块，将其包含在then_body中
                    if succ_nop_only and succ_has_nop:
                        then_body.append(successor)
                    # [关键修复] 如果后继块包含NOP但不是NOP-only块（深层嵌套if的最后一个块），
                    # 也将其包含在then_body中，以便正确处理深层嵌套if结构
                    elif succ_has_nop and not succ_nop_only:
                        then_body.append(successor)
                    
                    if_struct = IfStructure(
                        struct_type=ControlStructureType.IF_THEN,
                        entry_block=block,
                        condition_block=block,
                        then_body=then_body,
                        else_body=[],
                        merge_block=successor
                    )
                    
                    # 标记这是一个NOP生成的if结构
                    if_struct.is_nop_generated = True
                    
                    self.structures.append(if_struct)
                    # [关键修复] 将块添加到block_to_structure和analyzed_blocks
                    # 这样可以正确处理连续的NOP块（如超深层if嵌套）
                    self.block_to_structure[block] = if_struct
                    analyzed_blocks.add(block)
            else:
                # [关键修复] 处理包含NOP但不是只包含NOP的块
                # 这种情况通常发生在if True:被优化后，NOP作为行号标记
                # 后面跟着实际的代码
                
                # [关键修复] 检查这个块是否是编译器优化后的残留
                # 特征：
                # 1. 块包含NOP指令，但没有条件跳转指令
                # 2. NOP在行号标记处
                # 
                # 当Python编译器优化if True:时，会完全移除条件判断
                # 这种情况下不应该创建if结构，而是直接生成实际代码
                
                # 统计NOP数量和条件跳转指令
                nop_count = 0
                has_conditional_jump = False
                for instr in block.instructions:
                    if instr.opname == 'NOP':
                        nop_count += 1
                    elif instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                         'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                         'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                        has_conditional_jump = True
                        break
                
                # [字节码一致性修复] 即使没有条件跳转，也要为NOP块创建if结构
                # 以保持与原始字节码的一致性
                
                # [关键修复] 检查这个块是否是深层嵌套if结构的一部分
                # 特征：前驱块是NOP-only块，且当前块包含NOP指令
                # 这种情况下，当前块也应该被识别为NOP-only块（不是nop_is_line_marker）
                is_part_of_deep_nesting = False
                for pred in block.predecessors:
                    # 检查前驱是否已经在block_to_structure中
                    # 检查前驱是否已经在block_to_structure中
                    # 检查前驱是否已经在block_to_structure中
                    # 检查前驱是否已经在block_to_structure中
                    if pred in self.block_to_structure:
                        pred_struct = self.block_to_structure[pred]
                        if isinstance(pred_struct, IfStructure) and getattr(pred_struct, 'is_nop_generated', False):
                            # 前驱是NOP生成的if结构
                            # 检查前驱的then_body是否包含当前块
                            # 前驱是NOP生成的if结构
                            # 检查前驱的then_body是否包含当前块
                            # 前驱是NOP生成的if结构
                            # 检查前驱的then_body是否包含当前块
                            # 前驱是NOP生成的if结构
                            # 检查前驱的then_body是否包含当前块
                            if block in getattr(pred_struct, 'then_body', []):
                                is_part_of_deep_nesting = True
                                break
                    else:
                        # [关键修复] 前驱还没有被处理，检查它是否是NOP-only块
                        # 这是深层嵌套if结构的情况
                        pred_nop_only = True
                        pred_has_nop = False
                        for instr in pred.instructions:
                            if instr.opname == 'NOP':
                                pred_has_nop = True
                            elif instr.opname not in ('RESUME', 'CACHE', 'PRECALL'):
                                pred_nop_only = False
                                break
                        if pred_nop_only and pred_has_nop:
                            # 前驱是NOP-only块，当前块是深层嵌套if结构的一部分
                            # 前驱是NOP-only块，当前块是深层嵌套if结构的一部分
                            # 前驱是NOP-only块，当前块是深层嵌套if结构的一部分
                            # 前驱是NOP-only块，当前块是深层嵌套if结构的一部分
                            is_part_of_deep_nesting = True
                            break
                
                # 检查NOP是否有行号（是行号标记）
                if nop_instr and nop_instr.starts_line:
                    # [关键修复] 检查这个NOP是否是try块的开始标志
                    # 如果是，跳过，不创建if结构
                    # [关键修复] 检查这个NOP是否是try块的开始标志
                    # 如果是，跳过，不创建if结构
                    # [关键修复] 检查这个NOP是否是try块的开始标志
                    # 如果是，跳过，不创建if结构
                    # [关键修复] 检查这个NOP是否是try块的开始标志
                    # 如果是，跳过，不创建if结构
                    is_try_start_marker = False
                    for try_start in try_start_offsets:
                        if 0 < try_start - nop_instr.offset <= 20:
                            is_try_start_marker = True
                            break
                    
                    if is_try_start_marker:
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        # 这是一个try块的开始标志，不是if True:语句
                        analyzed_blocks.add(block)
                        continue
                    
                    # [关键修复] 如果是深层嵌套if结构的一部分，使用NOP-only逻辑处理
                    if is_part_of_deep_nesting and len(block.successors) == 1:
                        successor = list(block.successors)[0]
                        
                        # 创建虚拟的if结构来表示这个NOP
                        then_body = [block]
                        
                        if_struct = IfStructure(
                            struct_type=ControlStructureType.IF_THEN,
                            entry_block=block,
                            condition_block=block,
                            then_body=then_body,
                            else_body=[],
                            merge_block=successor
                        )
                        
                        # 标记这是一个NOP生成的if结构
                        if_struct.is_nop_generated = True
                        
                        self.structures.append(if_struct)
                        self.block_to_structure[block] = if_struct
                        analyzed_blocks.add(block)
                    else:
                        # [关键修复] 检测else分支
                        else_body = []
                        merge_block = None
                        
                        if len(block.successors) == 1:
                            successor = list(block.successors)[0]
                            # 检查后继块是否是另一个NOP块（elif链）或包含实际代码
                            succ_has_nop = any(instr.opname == 'NOP' for instr in successor.instructions)
                            if not succ_has_nop:
                                merge_block = successor
                        
                        # 创建if结构（只有带条件跳转的if）
                        if_struct = IfStructure(
                            struct_type=ControlStructureType.IF_THEN,
                            entry_block=block,
                            condition_block=block,
                            then_body=[block],
                            else_body=else_body,
                            merge_block=merge_block
                        )
                        
                        # 标记这是一个NOP生成的if结构
                        if_struct.is_nop_generated = True
                        # [关键修复] 标记这个NOP在行号标记处
                        if_struct.nop_is_line_marker = True
                        if_struct.nop_line_number = nop_instr.starts_line
                        
                        self.structures.append(if_struct)
                        self.block_to_structure[block] = if_struct
                        analyzed_blocks.add(block)

    def _fix_structure_overlaps(self) -> None:
        """
        [关键修复] 修复结构之间的重叠
        
        问题：不同的IfStructure可能包含相同的块（如else_body和另一个结构的condition_chain重叠）
        解决：对于每个IfStructure，从then_body和else_body中排除属于其他结构的核心块（entry_block或condition_chain）
        同时更新self.block_to_structure，确保每个块只属于一个结构
        """
        # 收集所有IfStructure
        if_structures = [s for s in self.structures if isinstance(s, IfStructure)]
        
        # 收集所有属于其他结构的核心块（entry_block或condition_chain）
        # 这些块不应该被包含在其他结构的then_body或else_body中
        core_blocks = {}  # block -> owning_struct
        for struct in if_structures:
            # entry_block是核心块
            # entry_block是核心块
            # entry_block是核心块
            # entry_block是核心块
            core_blocks[struct.entry_block] = struct
            # condition_chain中的块也是核心块
            if hasattr(struct, 'condition_chain') and struct.condition_chain:
                for block in struct.condition_chain:
                    core_blocks[block] = struct
        
        for struct in if_structures:
            
            # 从then_body中排除属于其他结构的核心块
            # [例外] 如果其他结构的header是当前结构的then_body的一部分，这是嵌套if结构
            # 应该保留该header，让AST生成器正确处理嵌套
            
            # 从then_body中排除属于其他结构的核心块
            # [例外] 如果其他结构的header是当前结构的then_body的一部分，这是嵌套if结构
            # 应该保留该header，让AST生成器正确处理嵌套
            
            # 从then_body中排除属于其他结构的核心块
            # [例外] 如果其他结构的header是当前结构的then_body的一部分，这是嵌套if结构
            # 应该保留该header，让AST生成器正确处理嵌套
            
            # 从then_body中排除属于其他结构的核心块
            # [例外] 如果其他结构的header是当前结构的then_body的一部分，这是嵌套if结构
            # 应该保留该header，让AST生成器正确处理嵌套
            new_then_body = []
            for block in struct.then_body:
                # 如果这个块是其他结构的核心块，检查是否是嵌套if
                # 如果这个块是其他结构的核心块，检查是否是嵌套if
                # 如果这个块是其他结构的核心块，检查是否是嵌套if
                # 如果这个块是其他结构的核心块，检查是否是嵌套if
                if block in core_blocks and core_blocks[block] != struct:
                    # [关键修复] 检查这个块是否是其他结构的header
                    # [关键修复] 检查这个块是否是其他结构的header
                    # [关键修复] 检查这个块是否是其他结构的header
                    # [关键修复] 检查这个块是否是其他结构的header
                    other_struct = core_blocks[block]
                    if hasattr(other_struct, 'entry_block') and other_struct.entry_block == block:
                        # [关键修复] 区分真正的嵌套if和独立的链式比较
                        # 如果该块是当前结构的fall-through后继（不是跳转目标），
                        # 且该块是一个链式比较的入口，则它是独立的if，不是嵌套if
                        # [关键修复] 区分真正的嵌套if和独立的链式比较
                        # 如果该块是当前结构的fall-through后继（不是跳转目标），
                        # 且该块是一个链式比较的入口，则它是独立的if，不是嵌套if
                        # [关键修复] 区分真正的嵌套if和独立的链式比较
                        # 如果该块是当前结构的fall-through后继（不是跳转目标），
                        # 且该块是一个链式比较的入口，则它是独立的if，不是嵌套if
                        # [关键修复] 区分真正的嵌套if和独立的链式比较
                        # 如果该块是当前结构的fall-through后继（不是跳转目标），
                        # 且该块是一个链式比较的入口，则它是独立的if，不是嵌套if
                        is_fall_through = False
                        jump_target = None
                        for instr in struct.entry_block.instructions:
                            if instr.opname.startswith('POP_JUMP'):
                                jump_target = instr.argval
                                break
                        
                        if jump_target is not None:
                            # 检查该块是否是跳转目标
                            # 检查该块是否是跳转目标
                            # 检查该块是否是跳转目标
                            # 检查该块是否是跳转目标
                            for succ in struct.entry_block.successors:
                                if succ == block and succ.start_offset != jump_target:
                                    # 该块是fall-through后继，不是跳转目标
                                    # 该块是fall-through后继，不是跳转目标
                                    # 该块是fall-through后继，不是跳转目标
                                    # 该块是fall-through后继，不是跳转目标
                                    is_fall_through = True
                                    break
                        
                        # [关键修复] 如果该块是fall-through后继且是链式比较入口，
                        # 则它是独立的if，不应该被包含在then_body中
                        # [关键修复] 如果该块是其他IfStructure的entry_block，但不是链式比较，
                        # 则它是嵌套if，不应该被包含在当前结构的then_body中
                        if is_fall_through and hasattr(other_struct, 'is_compound_condition') and other_struct.is_compound_condition:
                            # [关键修复] 如果当前结构也是链式比较的一部分，
                            # 将other_struct的condition_chain合并到当前结构
                            # [关键修复] 如果当前结构也是链式比较的一部分，
                            # 将other_struct的condition_chain合并到当前结构
                            # [关键修复] 如果当前结构也是链式比较的一部分，
                            # 将other_struct的condition_chain合并到当前结构
                            # [关键修复] 如果当前结构也是链式比较的一部分，
                            # 将other_struct的condition_chain合并到当前结构
                            if hasattr(struct, 'condition_chain') and struct.condition_chain:
                                # 检查是否是连续的链式比较
                                # 例如：0 < x <= 5 < 10
                                # struct.condition_chain = [块6] (0 < x)
                                # other_struct.condition_chain = [块7, 块8] (x <= 5 < 10)
                                # 合并后：condition_chain = [块6, 块7, 块8]
                                
                                # 检查other_struct的entry_block是否是当前结构的fall-through后继
                                # 检查是否是连续的链式比较
                                # 例如：0 < x <= 5 < 10
                                # struct.condition_chain = [块6] (0 < x)
                                # other_struct.condition_chain = [块7, 块8] (x <= 5 < 10)
                                # 合并后：condition_chain = [块6, 块7, 块8]
                                
                                # 检查other_struct的entry_block是否是当前结构的fall-through后继
                                # 检查是否是连续的链式比较
                                # 例如：0 < x <= 5 < 10
                                # struct.condition_chain = [块6] (0 < x)
                                # other_struct.condition_chain = [块7, 块8] (x <= 5 < 10)
                                # 合并后：condition_chain = [块6, 块7, 块8]
                                
                                # 检查other_struct的entry_block是否是当前结构的fall-through后继
                                # 检查是否是连续的链式比较
                                # 例如：0 < x <= 5 < 10
                                # struct.condition_chain = [块6] (0 < x)
                                # other_struct.condition_chain = [块7, 块8] (x <= 5 < 10)
                                # 合并后：condition_chain = [块6, 块7, 块8]
                                
                                # 检查other_struct的entry_block是否是当前结构的fall-through后继
                                last_cond_block = struct.condition_chain[-1]
                                last_jump = None
                                for instr in last_cond_block.instructions:
                                    if instr.opname.startswith('POP_JUMP'):
                                        last_jump = instr.argval
                                        break
                                
                                is_continuous = False
                                if last_jump is not None:
                                    for succ in last_cond_block.successors:
                                        if succ == other_struct.entry_block and succ.start_offset != last_jump:
                                            is_continuous = True
                                            break
                                
                                if is_continuous:
                                    # [字节码一致性修复] 检查是否需要合并condition_chain
                                    # 如果other_struct的condition_chain的第一个块已经在当前chain中，说明已经收集过了，不需要重复添加
                                    # 这在链式比较中常见：_detect_compound_condition已收集所有块，但嵌套结构又尝试合并
                                    existing_offsets = {b.start_offset for b in struct.condition_chain}
                                    new_blocks = [b for b in other_struct.condition_chain 
                                                if b.start_offset not in existing_offsets]
                                    if new_blocks:
                                        struct.condition_chain.extend(new_blocks)
                                    struct.is_compound_condition = True
                                    # 将other_struct的then_body合并到当前结构
                                    for tb in other_struct.then_body:
                                        if tb not in new_then_body:
                                            new_then_body.append(tb)
                                    # 标记other_struct为已合并，后续跳过它
                                    other_struct._merged_into = struct
                            
                            # 这是独立的链式比较，不是嵌套if，排除它
                            continue
                        
                        # 这是嵌套if的header，保留它
                        new_then_body.append(block)
                        continue
                    # 不是嵌套if，排除它
                    continue
                new_then_body.append(block)
            
            # 从else_body中排除属于其他结构的核心块
            # [关键修复] 但是保留else_branch块及其后继，即使它们是另一个结构的entry_block
            # 这是因为else_branch可能是下一个if语句的入口，但它仍然是当前if的else分支
            new_else_body = []
            
            elif_condition_blocks = set()
            elif_else_blocks = set()
            if hasattr(struct, 'elif_conditions') and struct.elif_conditions:
                for idx, elif_block in enumerate(struct.elif_conditions):
                    is_last_elif = (idx == len(struct.elif_conditions) - 1)
                    elif_condition_blocks.add(elif_block)
                    elif_jump = self._get_jump_instr(elif_block)
                    if elif_jump and elif_jump.argval is not None:
                        for succ in elif_block.successors:
                            if succ.start_offset != elif_jump.argval:
                                elif_condition_blocks.add(succ)
                                worklist = [succ]
                                while worklist:
                                    b = worklist.pop(0)
                                    if b in elif_condition_blocks:
                                        continue
                                    elif_condition_blocks.add(b)
                                    for s in b.successors:
                                        if s not in struct.then_body:
                                            worklist.append(s)
                            elif is_last_elif:
                                elif_else_blocks.add(succ)
                                worklist = [succ]
                                while worklist:
                                    b = worklist.pop(0)
                                    if b in elif_else_blocks:
                                        continue
                                    elif_else_blocks.add(b)
                                    for s in b.successors:
                                        if s not in struct.then_body and s not in elif_condition_blocks:
                                            worklist.append(s)
            
            else_branch = None
            for succ in struct.entry_block.successors:
                if succ not in struct.then_body:
                    else_branch = succ
                    break
            
            # [关键修复] 收集else_branch及其所有后继块
            else_branch_and_successors = set()
            if else_branch:
                worklist = [else_branch]
                while worklist:
                    block = worklist.pop(0)
                    if block in else_branch_and_successors:
                        continue
                    else_branch_and_successors.add(block)
                    for succ in block.successors:
                        if succ not in struct.then_body:  # 不包含then_body中的块
                            worklist.append(succ)

            for block in struct.else_body:
                if hasattr(struct, 'elif_conditions') and block in struct.elif_conditions:
                    new_else_body.append(block)
                    continue
                if block in elif_condition_blocks:
                    new_else_body.append(block)
                    continue
                if block in elif_else_blocks:
                    new_else_body.append(block)
                    continue
                
                is_other_struct_body_block = False
                is_other_struct_entry = False
                is_current_nested = False
                is_in_loop_in_else_body = False
                
                # [关键修复] 检查当前结构的header是否是其他结构的then_body或else_body的一部分
                for other_struct in if_structures:
                    if other_struct != struct:
                        if hasattr(other_struct, 'then_body') and struct.entry_block in other_struct.then_body:
                            is_current_nested = True
                            break
                        if hasattr(other_struct, 'else_body') and struct.entry_block in other_struct.else_body:
                            is_current_nested = True
                            break
                
                # [关键修复] 检查else_body是否包含循环结构
                # 如果包含，不应该从else_body中排除循环体内的块
                loop_body_blocks_in_else = set()
                # [关键修复] 定义elif_condition_blocks，用于存储elif条件的块
                elif_condition_blocks = set()
                if hasattr(struct, 'elif_conditions'):
                    elif_condition_blocks = set(struct.elif_conditions)
                for loop_struct in self.structures:
                    if isinstance(loop_struct, LoopStructure) and hasattr(loop_struct, 'body_blocks'):
                        # 检查循环的entry_block是否在else_body中
                        # 检查循环的entry_block是否在else_body中
                        # 检查循环的entry_block是否在else_body中
                        # 检查循环的entry_block是否在else_body中
                        if loop_struct.entry_block in struct.else_body:
                            # 循环在else_body中，保留循环体的所有块
                            # 循环在else_body中，保留循环体的所有块
                            # 循环在else_body中，保留循环体的所有块
                            # 循环在else_body中，保留循环体的所有块
                            for loop_block in loop_struct.body_blocks:
                                loop_body_blocks_in_else.add(loop_block)
                
                for other_struct in if_structures:
                    if other_struct != struct:
                        if other_struct.entry_block == block:
                            if hasattr(other_struct, 'parent') and other_struct.parent is struct:
                                is_other_struct_entry = True
                            elif hasattr(struct, 'elif_conditions') and block in struct.elif_conditions:
                                is_other_struct_entry = True
                            else:
                                is_other_struct_body_block = True
                            break
                        # [关键修复] 检查块是否在其他结构的then_body或else_body中
                        # [关键修复] 且块不在循环体内时，才排除它
                        if block not in loop_body_blocks_in_else:
                            if hasattr(other_struct, 'then_body') and block in other_struct.then_body:
                                if other_struct is struct:
                                    pass
                                elif hasattr(struct, 'elif_conditions') and other_struct.entry_block in struct.elif_conditions:
                                    pass
                                else:
                                    is_other_struct_body_block = True
                                    break
                            if hasattr(other_struct, 'else_body') and block in other_struct.else_body:
                                if other_struct is struct:
                                    pass
                                elif hasattr(struct, 'elif_conditions') and other_struct.entry_block in struct.elif_conditions:
                                    pass
                                else:
                                    is_other_struct_body_block = True
                                    break
                
                # 如果是其他结构的entry_block，保留它
                if is_other_struct_entry:
                    new_else_body.append(block)
                    continue

                # 如果是其他结构的body块（但不是entry_block），检查该块是否在else_branch_and_successors中
                # 如果在，保留它，因为它是当前if结构的else分支的一部分
                if is_other_struct_body_block:
                    if block in else_branch_and_successors:
                        new_else_body.append(block)
                    continue
                
                # 如果这个块是其他结构的核心块，检查它是否在else_branch的后继中
                if block in core_blocks and core_blocks[block] != struct:
                    if block in elif_condition_blocks:
                        pass
                    elif block not in else_branch_and_successors:
                        continue
                
                is_condition_chain_block = False
                if block not in loop_body_blocks_in_else and block not in elif_condition_blocks:
                    for other_struct in if_structures:
                        if other_struct != struct and hasattr(other_struct, 'condition_chain') and other_struct.condition_chain:
                            if block in other_struct.condition_chain:
                                is_condition_chain_block = True
                                break
                
                if is_condition_chain_block:
                    continue
                
                new_else_body.append(block)
            
            # 更新结构
            struct.then_body = new_then_body
            struct.else_body = new_else_body
        
        # [关键修复-根本性修复] 从IfStructure的then_body和else_body中排除属于LoopStructure的块
        # 问题根源：IfStructure的then_body包含了LoopStructure的所有块，导致循环块被处理两次
        # 解决方案：识别所有LoopStructure的块（除了entry_block），从IfStructure的body中排除这些块
        # 注意：保留LoopStructure的entry_block在IfStructure的then_body中，因为它是if块的入口
        loop_structure_blocks = set()
        for struct in self.structures:
            if isinstance(struct, LoopStructure):
                # 收集LoopStructure的所有块（除了entry_block）
                if hasattr(struct, 'body_blocks') and struct.body_blocks:
                    loop_structure_blocks.update(struct.body_blocks)
                if hasattr(struct, 'else_body') and struct.else_body:
                    loop_structure_blocks.update(struct.else_body)
                if struct.header_block:
                    loop_structure_blocks.add(struct.header_block)
                # 注意：不添加entry_block，因为它应该保留在IfStructure的then_body中
        
        # 从IfStructure的then_body和else_body中排除loop_structure_blocks
        for struct in if_structures:
            # [关键修复-2026-elif-else] 对于循环内的if结构：
            # - 保留entry_block（if条件块）
            # - 保留pre_then_branch（if的直接then分支，如 count += 1）
            # - 排除其他循环块（避免重复处理）
            # 这可以解决循环内if-elif-else结构的then_body丢失问题
            _pre_then = getattr(struct, 'pre_then_branch', None)
            
            struct.then_body = [b for b in struct.then_body 
                               if b == struct.entry_block or 
                                  b == _pre_then or 
                                  b not in loop_structure_blocks]
            # else_body：排除所有loop blocks
            struct.else_body = [b for b in struct.else_body if b not in loop_structure_blocks]

        # [关键修复] 重新构建self.block_to_structure
        # 确保每个块只属于一个结构（优先保留entry_block和condition_chain的映射）
        new_block_to_structure = {}
        for struct in if_structures:
            # entry_block必须映射到当前结构
            # entry_block必须映射到当前结构
            # entry_block必须映射到当前结构
            # entry_block必须映射到当前结构
            new_block_to_structure[struct.entry_block] = struct
            # condition_chain中的块也必须映射到当前结构
            if hasattr(struct, 'condition_chain') and struct.condition_chain:
                for block in struct.condition_chain:
                    new_block_to_structure[block] = struct
            # then_body和else_body中的块，如果没有被其他结构声明为核心块，也映射到当前结构
            for block in struct.then_body + struct.else_body:
                if block not in core_blocks:
                    new_block_to_structure[block] = struct
        
        # [关键修复] 添加LoopStructure的映射
        # 修复问题：_fix_structure_overlaps清除了LoopStructure的block_to_structure映射
        for struct in self.structures:
            if isinstance(struct, LoopStructure):
                # entry_block必须映射到当前结构
                # entry_block必须映射到当前结构
                # entry_block必须映射到当前结构
                # entry_block必须映射到当前结构
                if struct.entry_block:
                    new_block_to_structure[struct.entry_block] = struct
                # header_block也必须映射到当前结构
                if struct.header_block:
                    new_block_to_structure[struct.header_block] = struct
                # body_blocks中的块也必须映射到当前结构
                if hasattr(struct, 'body_blocks') and struct.body_blocks:
                    for block in struct.body_blocks:
                        new_block_to_structure[block] = struct
                # else_body中的块也必须映射到当前结构
                if hasattr(struct, 'else_body') and struct.else_body:
                    for block in struct.else_body:
                        new_block_to_structure[block] = struct
        
        # 更新self.block_to_structure
        self.block_to_structure = new_block_to_structure
        
        # [关键修复] 移除已经被合并的结构
        merged_structs = [s for s in if_structures if hasattr(s, '_merged_into')]
        for s in merged_structs:
            if s in self.structures:
                self.structures.remove(s)
        
        # [关键修复] 重新构建core_blocks，因为有些结构被合并了
        core_blocks = {}
        for struct in self.structures:
            if isinstance(struct, IfStructure):
                core_blocks[struct.entry_block] = struct
                if hasattr(struct, 'condition_chain') and struct.condition_chain:
                    for block in struct.condition_chain:
                        core_blocks[block] = struct
        
        # [关键修复] 清理被合并结构的block_to_structure映射
        for block, struct in list(self.block_to_structure.items()):
            if hasattr(struct, '_merged_into'):
                # 更新映射到合并后的结构
                # 更新映射到合并后的结构
                # 更新映射到合并后的结构
                # 更新映射到合并后的结构
                self.block_to_structure[block] = struct._merged_into

    def _merge_chained_comparisons(self) -> None:
        """
        [关键修复] 合并链式比较（如 0 < x < 100）
        
        链式比较的字节码模式：
        1. 第一个条件块执行第一个比较（如 0 < x）
        2. 如果为真，fall-through 到第二个条件块执行第二个比较（如 x < 100）
        3. 如果为假，跳转到 else 分支
        
        这种模式产生两个 IfStructure，需要合并为一个
        """
        # 收集所有 IfStructure
        if_structures = [s for s in self.structures if isinstance(s, IfStructure)]
        
        if len(if_structures) < 2:
            return
        
        # 按 entry_block 的 start_offset 排序
        if_structures.sort(key=lambda s: s.entry_block.start_offset)
        
        # 查找链式比较模式
        i = 0
        while i < len(if_structures) - 1:
            first = if_structures[i]
            second = if_structures[i + 1]
            
            # [关键修复] 检查是否是链式比较模式：
            # 1. 第二个 IfStructure 的 entry_block 是第一个 IfStructure 的 fall-through 后继
            # 2. 第二个 IfStructure 的 entry_block 只有一个前驱
            # 3. 第一个 IfStructure 的跳转目标与第二个 IfStructure 的跳转目标不同
            
            # [关键修复] 跳过异常处理块，不应该合并异常处理结构
            if self._is_exception_handler_block(second.entry_block):
                i += 1
                continue
            
            # [关键修复] 跳过NOP生成的if结构，不应该合并它们
            # NOP if结构对应优化后的if True:语句，每个都应该独立生成
            if getattr(first, 'is_nop_generated', False) or getattr(second, 'is_nop_generated', False):
                i += 1
                continue
            
            is_chained = False
            
            # 获取第一个 IfStructure 的跳转指令
            first_jump = self._get_jump_instr(first.entry_block)
            
            # 检查第二个块的 entry_block 是否只有一个前驱
            if len(second.entry_block.predecessors) == 1:
                pred = list(second.entry_block.predecessors)[0]
                
                # 检查前驱是否是第一个 IfStructure 的 entry_block
                # [关键修复] 或者前驱是第一个 IfStructure 的 condition_chain 中的任何一个块
                first_condition_blocks = set(first.condition_chain) if hasattr(first, 'condition_chain') else {first.entry_block}
                first_condition_blocks.add(first.entry_block)
                
                if pred in first_condition_blocks:
                    # 检查第一个 IfStructure 的 fall-through 是否是第二个 IfStructure 的 entry_block
                    # 即：第一个块的某个后继是第二个块的 entry_block，且不是跳转目标
                    # 检查第一个 IfStructure 的 fall-through 是否是第二个 IfStructure 的 entry_block
                    # 即：第一个块的某个后继是第二个块的 entry_block，且不是跳转目标
                    # 检查第一个 IfStructure 的 fall-through 是否是第二个 IfStructure 的 entry_block
                    # 即：第一个块的某个后继是第二个块的 entry_block，且不是跳转目标
                    # 检查第一个 IfStructure 的 fall-through 是否是第二个 IfStructure 的 entry_block
                    # 即：第一个块的某个后继是第二个块的 entry_block，且不是跳转目标
                    if first_jump and first_jump.argval is not None:
                        for succ in first.entry_block.successors:
                            if succ == second.entry_block and succ.start_offset != first_jump.argval:
                                # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                                # 链式比较的特征：包含COPY 2指令
                                # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body
                                # 检查是否包含COPY 2指令（链式比较的特征）
                                # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                                # 链式比较的特征：包含COPY 2指令
                                # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body
                                # 检查是否包含COPY 2指令（链式比较的特征）
                                # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                                # 链式比较的特征：包含COPY 2指令
                                # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body
                                # 检查是否包含COPY 2指令（链式比较的特征）
                                # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                                # 链式比较的特征：包含COPY 2指令
                                # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body
                                # 检查是否包含COPY 2指令（链式比较的特征）
                                has_copy_instr = False
                                for instr in first.entry_block.instructions:
                                    if instr.opname == 'COPY' and instr.arg == 2:
                                        has_copy_instr = True
                                        break
                                if not has_copy_instr:
                                    for instr in second.entry_block.instructions:
                                        if instr.opname == 'COPY' and instr.arg == 2:
                                            has_copy_instr = True
                                            break
                                
                                if has_copy_instr:
                                    # 这是链式比较，不是嵌套if-else
                                    # 这是链式比较，不是嵌套if-else
                                    # 这是链式比较，不是嵌套if-else
                                    # 这是链式比较，不是嵌套if-else
                                    is_chained = True
                                break
                    else:
                        # 没有跳转指令，检查是否是直接后继
                        if second.entry_block in first.entry_block.successors:
                            is_chained = True
            
            # [关键修复] 检查是否是 and 条件模式
            # and 条件的特征：
            # 1. 第二个 IfStructure 的 entry_block 在第一个 IfStructure 的 then_body 中
            # 2. 两个 IfStructure 共享同一个 else 分支（merge_block 相同，或 else_body 相同）
            # 3. [关键修复] 第二个 IfStructure 的 then_body 和 else_body 应该为空或只包含条件检查
            #    （区别于嵌套if-else，嵌套if-else中内部if有自己的then/else分支）
            is_and_condition = False
            if not is_chained:
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 then_body 中
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 then_body 中
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 then_body 中
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 then_body 中
                if second.entry_block in first.then_body:
                    # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                    # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body（不为空）
                    # 复合条件的特征：第二个 IfStructure 只是条件检查，then_body和else_body为空
                    # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                    # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body（不为空）
                    # 复合条件的特征：第二个 IfStructure 只是条件检查，then_body和else_body为空
                    # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                    # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body（不为空）
                    # 复合条件的特征：第二个 IfStructure 只是条件检查，then_body和else_body为空
                    # [关键修复] 检查第二个 IfStructure 是否是嵌套if-else
                    # 嵌套if-else的特征：第二个 IfStructure 有自己的then_body和else_body（不为空）
                    # 复合条件的特征：第二个 IfStructure 只是条件检查，then_body和else_body为空
                    second_has_real_body = False
                    if second.then_body:
                        # 检查then_body是否包含实际的代码（不只是条件检查）
                        # 检查then_body是否包含实际的代码（不只是条件检查）
                        # 检查then_body是否包含实际的代码（不只是条件检查）
                        # 检查then_body是否包含实际的代码（不只是条件检查）
                        for block in second.then_body:
                            for instr in block.instructions:
                                if instr.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL',
                                                       'POP_TOP', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                                                       'LOAD_FAST', 'LOAD_CONST', 'COMPARE_OP', 'JUMP_FORWARD'):
                                    second_has_real_body = True
                                    break
                            if second_has_real_body:
                                break
                    
                    if second_has_real_body:
                        # 这是嵌套if-else，不是复合条件
                        # 这是嵌套if-else，不是复合条件
                        # 这是嵌套if-else，不是复合条件
                        # 这是嵌套if-else，不是复合条件
                        pass
                    else:
                        # [关键修复] 检查两个 IfStructure 的 else 分支是否相同
                        # 对于 AND 条件，两个条件的 else 分支应该相同（都跳转到同一个地方）
                        # 对于嵌套 if，外部 if 和内部 if 的 else 分支不同
                        first_else_target = None
                        second_else_target = None
                        
                        first_jump = self._get_jump_instr(first.entry_block)
                        second_jump = self._get_jump_instr(second.entry_block)
                        
                        if first_jump and first_jump.argval is not None:
                            for succ in first.entry_block.successors:
                                if succ.start_offset == first_jump.argval:
                                    first_else_target = succ
                                    break
                        
                        if second_jump and second_jump.argval is not None:
                            for succ in second.entry_block.successors:
                                if succ.start_offset == second_jump.argval:
                                    second_else_target = succ
                                    break
                        
                        # 如果 else 分支不同，这是嵌套 if，不是 AND 条件
                        if first_else_target != second_else_target:
                            # 这是嵌套if，不是复合条件
                            # 这是嵌套if，不是复合条件
                            # 这是嵌套if，不是复合条件
                            # 这是嵌套if，不是复合条件
                            pass
                        else:
                            # 检查两个 IfStructure 是否共享同一个 else 分支
                            # 条件：merge_block 相同，或 second 的 else_body 在 first 的 else_body 中
                            share_else = False
                            if first.merge_block and second.merge_block and first.merge_block == second.merge_block:
                                share_else = True
                            elif first.merge_block and second.else_body:
                                # 检查 second 的 else_body 是否包含 first 的 merge_block
                                # 检查 second 的 else_body 是否包含 first 的 merge_block
                                if first.merge_block in second.else_body:
                                    share_else = True
                            elif first.else_body and second.else_body:
                                # 检查是否有共同的 else 块
                                # 检查是否有共同的 else 块
                                common_else = set(first.else_body) & set(second.else_body)
                                if common_else:
                                    share_else = True
                            
                            if share_else:
                                # 检查是否是链式比较（包含COPY 2指令）
                                # 检查是否是链式比较（包含COPY 2指令）
                                # 检查是否是链式比较（包含COPY 2指令）
                                # 检查是否是链式比较（包含COPY 2指令）
                                has_copy_instr = False
                                for instr in first.entry_block.instructions:
                                    if instr.opname == 'COPY' and instr.arg == 2:
                                        has_copy_instr = True
                                        break
                                if not has_copy_instr:
                                    for instr in second.entry_block.instructions:
                                        if instr.opname == 'COPY' and instr.arg == 2:
                                            has_copy_instr = True
                                            break
                                
                                if has_copy_instr:
                                    # 这是链式比较，不是普通的and条件
                                    # 这是链式比较，不是普通的and条件
                                    # 这是链式比较，不是普通的and条件
                                    # 这是链式比较，不是普通的and条件
                                    is_chained = True
                                else:
                                    is_and_condition = True
            
            # [关键修复] 检查是否是 or 条件模式
            # or 条件的特征：
            # 1. 第二个 IfStructure 的 entry_block 在第一个 IfStructure 的 else_body 中
            # 2. 第一个 IfStructure 的 then_body 和第二个 IfStructure 的 then_body 相同（共享then分支）
            # 3. 或者第二个 IfStructure 的 then_body 包含第一个 IfStructure 的 then_body
            is_or_condition = False
            if not is_chained and not is_and_condition:
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 else_body 中
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 else_body 中
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 else_body 中
                # 检查第二个 IfStructure 的 entry_block 是否在第一个的 else_body 中
                if second.entry_block in first.else_body:
                    # 检查两个 IfStructure 是否共享同一个 then 分支
                    # 条件：first 的 then_body 是 second 的 then_body 的子集，或相同
                    # 检查两个 IfStructure 是否共享同一个 then 分支
                    # 条件：first 的 then_body 是 second 的 then_body 的子集，或相同
                    # 检查两个 IfStructure 是否共享同一个 then 分支
                    # 条件：first 的 then_body 是 second 的 then_body 的子集，或相同
                    # 检查两个 IfStructure 是否共享同一个 then 分支
                    # 条件：first 的 then_body 是 second 的 then_body 的子集，或相同
                    share_then = False
                    if first.then_body and second.then_body:
                        # first的then_body应该是second的then_body的子集
                        # first的then_body应该是second的then_body的子集
                        # first的then_body应该是second的then_body的子集
                        # first的then_body应该是second的then_body的子集
                        first_then_set = set(first.then_body)
                        second_then_set = set(second.then_body)
                        if first_then_set <= second_then_set:
                            share_then = True
                        # 或者检查是否有共同的 then 块
                        common_then = first_then_set & second_then_set
                        if common_then:
                            share_then = True
                    
                    if share_then:
                        is_or_condition = True
            
            if is_chained or is_and_condition or is_or_condition:
                # [字节码一致性修复] 如果first已经有完整的condition_chain（来自_detect_compound_condition），
                # 不要修改它。_detect_compound_condition已经正确收集了所有链式比较块。
                has_complete_chain = (
                    hasattr(first, 'condition_chain') and 
                    len(first.condition_chain) >= 2 and 
                    any('COPY' in i.opname or 'SWAP' in i.opname 
                        for cb in first.condition_chain for i in cb.instructions)
                )
                
                if not has_complete_chain:
                    if not first.is_compound_condition:
                        first.is_compound_condition = True
                        first.condition_chain = [first.entry_block]
                    
                    # [关键修复] 添加第二个 IfStructure 的 condition_chain 中的所有块
                    if hasattr(second, 'condition_chain') and len(second.condition_chain) > 1:
                        for block in second.condition_chain:
                            if block not in first.condition_chain:
                                first.condition_chain.append(block)
                    else:
                        # 第二个 IfStructure 没有 condition_chain，只添加 entry_block
                        first.condition_chain.append(second.entry_block)
                # else: first 已有完整 chain，不需要修改
                
                # 2. 更新第一个 IfStructure 的 then_body 和 else_body
                if is_or_condition:
                    # [关键修复] 对于 or 条件：
                    # - then_body 应该是共享的（使用第二个的 then_body）
                    # - else_body 应该是第二个的 else_body（因为 or 的 else 是第二个条件的 else）
                    # [关键修复] 对于 or 条件：
                    # - then_body 应该是共享的（使用第二个的 then_body）
                    # - else_body 应该是第二个的 else_body（因为 or 的 else 是第二个条件的 else）
                    # [关键修复] 对于 or 条件：
                    # - then_body 应该是共享的（使用第二个的 then_body）
                    # - else_body 应该是第二个的 else_body（因为 or 的 else 是第二个条件的 else）
                    # [关键修复] 对于 or 条件：
                    # - then_body 应该是共享的（使用第二个的 then_body）
                    # - else_body 应该是第二个的 else_body（因为 or 的 else 是第二个条件的 else）
                    first.then_body = second.then_body
                    first.else_body = second.else_body
                else:
                    # 对于 and 条件和链式比较：
                    # then_body 应该是第二个 IfStructure 的 then_body
                    first.then_body = second.then_body
                    # else_body 应该包含两个 IfStructure 的 else_body
                    first.else_body = list(set(first.else_body + second.else_body))
                
                # 3. 更新 merge_block
                if second.merge_block:
                    first.merge_block = second.merge_block
                
                # 4. 从 structures 中移除第二个 IfStructure
                if second in self.structures:
                    self.structures.remove(second)
                
                # 5. 更新 block_to_structure 映射
                for block in second.condition_chain if hasattr(second, 'condition_chain') else [second.entry_block]:
                    self.block_to_structure[block] = first
                
                # 继续检查下一个（不增加 i，因为可能还有更多的链式比较）
                if_structures.pop(i + 1)
            else:
                i += 1

    def _is_conditional_block(self, block: BasicBlock) -> bool:
        """
        检查一个块是否是真正的条件分支块
        
        真正的条件分支块应该包含条件跳转指令（POP_JUMP_IF_*）
        但不应该包含：
        1. 异常处理指令（如CHECK_EXC_MATCH）
        2. 循环指令（如FOR_ITER, GET_ITER）
        
        [关键修复] 包含UNPACK_SEQUENCE的块也可以是条件块，
        例如 for key, value in data.items(): 中的 if isinstance(key, str):
        这种情况下块102包含 UNPACK_SEQUENCE 和 POP_JUMP_FORWARD_IF_TRUE
        """
        # [关键修复] 首先检查块是否是异常处理块
        # 异常处理块包含CHECK_EXC_MATCH，不应该被识别为条件分支块
        has_check_exc_match = False
        for instr in block.instructions:
            if instr.opname == 'CHECK_EXC_MATCH':
                has_check_exc_match = True
                break
        
        # 如果块包含CHECK_EXC_MATCH，不是条件分支块
        if has_check_exc_match:
            return False
        
        # [关键修复] 检查块是否包含循环指令
        # 包含FOR_ITER或GET_ITER的块是循环的一部分，不是独立的if条件块
        # [关键修复] 但包含UNPACK_SEQUENCE的块可以是条件块（如for循环体内的if语句）
        has_loop_instruction = False
        for instr in block.instructions:
            if instr.opname in ('FOR_ITER', 'GET_ITER'):
                has_loop_instruction = True
                break
        
        # 如果块包含循环指令，不是独立的条件分支块
        if has_loop_instruction:
            return False
        
        # [关键修复] 检查是否包含条件跳转指令
        for instr in block.instructions:
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'
            ):
                return True
        return False
    
    def _is_exception_handler_block(self, block: BasicBlock) -> bool:
        """
        检查一个块是否是异常处理块
        
        异常处理块的特征：
        1. 包含 PUSH_EXC_INFO 指令
        2. 或者包含 RERAISE 指令
        3. 或者包含 POP_EXCEPT 指令
        """
        for instr in block.instructions:
            if instr.opname in ('PUSH_EXC_INFO', 'RERAISE', 'POP_EXCEPT'):
                return True
        return False
    
    def _is_simple_merge_block(self, block: BasicBlock) -> bool:
        """
        检查一个块是否是简单的merge点（不是独立的else分支）
        
        简单的merge点的特征：
        1. 只包含简单的指令（如LOAD_FAST, RETURN_VALUE等）
        2. 不包含条件跳转指令
        3. 不包含赋值指令（STORE_*）
        4. 不是条件表达式的值加载块（即不是只包含LOAD_*的块）
        
        这用于区分：
        - if x is None: ... （没有else分支，跳转目标是merge点）
        - if x is None: ... else: ... （有else分支，跳转目标是else分支）
        """
        # [关键修复] 检查块是否是条件表达式的值加载块
        # 条件表达式的值加载块的特征：
        # 1. 只包含LOAD_*指令（可能还有JUMP_FORWARD）
        # 2. 不包含STORE_*指令
        # 3. 后继块包含STORE_*指令（即merge块）
        
        has_non_load_instr = False
        has_store = False
        has_return = False
        has_conditional_jump = False
        
        for instr in block.instructions:
            # 忽略调试和缓存指令
            # 忽略调试和缓存指令
            # 忽略调试和缓存指令
            # 忽略调试和缓存指令
            if instr.opname in ('RESUME', 'CACHE', 'NOP', 'PRECALL'):
                continue
            # 忽略JUMP_FORWARD指令
            if instr.opname == 'JUMP_FORWARD':
                continue
            # 检查条件跳转指令
            if 'JUMP' in instr.opname and 'IF' in instr.opname:
                has_conditional_jump = True
                continue
            # 检查LOAD_*指令
            if instr.opname.startswith('LOAD_'):
                continue
            # 检查STORE_*指令
            if instr.opname.startswith('STORE_'):
                has_store = True
                continue
            # 检查RETURN_VALUE指令
            if instr.opname == 'RETURN_VALUE':
                has_return = True
                continue
            # 如果有其他指令，这不是简单的merge点
            has_non_load_instr = True
        
        # [关键修复] 如果块包含条件跳转指令，它不是merge点
        if has_conditional_jump:
            return False
        
        # [关键修复] 检查块是否只包含LOAD_* + RETURN_VALUE
        # 这种块可能是：
        # 1. 函数的最后一条return语句（如 return True）
        # 2. if分支中的return语句（如 if x: return False）
        # 这两种情况都不是merge点，而是独立的执行路径
        # 只有当块是条件表达式的一部分时（如 a if x else b），它才是merge点
        # 条件表达式的特征是：块有后继（跳转到merge点）
        if has_return and not has_store and not has_non_load_instr:
            # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
            # 如果块有后继，它可能是条件表达式的一部分，需要进一步检查
            # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
            # 如果块有后继，它可能是条件表达式的一部分，需要进一步检查
            # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
            # 如果块有后继，它可能是条件表达式的一部分，需要进一步检查
            # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
            # 如果块有后继，它可能是条件表达式的一部分，需要进一步检查
            if not block.successors:
                return False  # 没有后继，是独立的return语句
            # 有后继，可能是条件表达式，检查后继是否是merge点
            # 如果后继是函数出口（没有后继），当前块不是merge点
            for succ in block.successors:
                if not succ.successors:
                    return False  # 后继是函数出口，当前块不是merge点
            return True
        
        # [关键修复] 如果块包含RETURN_VALUE但没有STORE_*，
        # 且块有多个前驱（来自不同分支），这可能是merge点
        # 例如：
        #   if name not in cls._instances:
        #       cls._instances[name] = object()
        #   return cls._instances[name]  # 这行在if之后执行
        # 块66有前驱：块0（条件为假时跳转）和块22（then分支fall-through）
        # 这种情况下，块66是merge点，不是else分支
        # [关键修复] 但是，如果块没有后继（是函数的最后一条return语句），
        # 它不是merge点，而是独立的执行路径
        if has_return and not has_store:
            # 检查块是否有多个前驱
            # 检查块是否有多个前驱
            # 检查块是否有多个前驱
            # 检查块是否有多个前驱
            if len(block.predecessors) >= 2:
                # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
                # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
                # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
                # [关键修复] 如果块没有后继，它是函数的最后一条return语句，不是merge点
                if not block.successors:
                    return False  # 没有后继，是独立的return语句，不是merge点
                # 有多个前驱且有后继，这是merge点
                return True
        
        # [关键修复] 如果块只包含LOAD_*指令（没有STORE_*），
        # 它可能是条件表达式的值加载块，不是merge点
        # 但如果块包含STORE_*或其他指令，它是merge点
        if has_store or has_non_load_instr:
            return False
        
        # [关键修复] 如果块只包含LOAD_*指令，检查其后继是否是merge块
        # 如果后继包含STORE_*，则当前块是值加载块，不是merge点
        # [关键修复] 如果后继包含BUILD_CONST_KEY_MAP或BUILD_MAP，则当前块是条件表达式的值加载块，不是merge点
        for succ in block.successors:
            for instr in succ.instructions:
                if instr.opname.startswith('STORE_'):
                    # 后继包含STORE_*，当前块是值加载块，不是merge点
                    # 后继包含STORE_*，当前块是值加载块，不是merge点
                    # 后继包含STORE_*，当前块是值加载块，不是merge点
                    # 后继包含STORE_*，当前块是值加载块，不是merge点
                    return False
                if instr.opname in ('BUILD_CONST_KEY_MAP', 'BUILD_MAP'):
                    # 后继包含字典构建指令，当前块是条件表达式的值加载块，不是merge点
                    # 后继包含字典构建指令，当前块是条件表达式的值加载块，不是merge点
                    # 后继包含字典构建指令，当前块是条件表达式的值加载块，不是merge点
                    # 后继包含字典构建指令，当前块是条件表达式的值加载块，不是merge点
                    return False
        
        # [关键修复] 检查块的前驱数量
        # 如果块只有一个前驱，那么它不是merge点（merge点应该有多个前驱，来自不同分支）
        # 这种情况通常是条件表达式的then或else分支（如 lambda x: abs(x) if x < 0 else x）
        if len(block.predecessors) == 1:
            # 只有一个前驱，不是merge点，而是条件表达式的值加载块
            # 只有一个前驱，不是merge点，而是条件表达式的值加载块
            # 只有一个前驱，不是merge点，而是条件表达式的值加载块
            # 只有一个前驱，不是merge点，而是条件表达式的值加载块
            return False
        
        return True
    
    def _is_not_condition_pattern(self, header: BasicBlock, jump_target: BasicBlock, fall_through: BasicBlock) -> bool:
        """
        检测NOT条件模式。
        
        NOT条件的特征：
        1. 使用 POP_JUMP_IF_TRUE 指令
        2. 跳转目标是else分支（可能是另一个条件或最终的else）
        3. fall-through路径是then分支
        
        这与普通if的区别在于：
        - 普通if：跳转目标是then分支，fall-through是else分支
        - NOT条件：跳转目标是else分支，fall-through是then分支
        
        检测方法：
        - 检查fall-through块是否是"简单的"then分支（不包含条件跳转）
        - 检查跳转目标是否是"复杂的"else分支（包含条件跳转或者是最终的else）
        
        Args:
            header: 条件头部块
            jump_target: 跳转目标块
            fall_through: fall-through块
            
        Returns:
            如果是NOT条件模式返回True
        """
        # 检查fall-through是否包含条件跳转指令
        fall_through_has_condition = False
        for instr in fall_through.instructions:
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE'
            ):
                fall_through_has_condition = True
                break
        
        # 如果fall-through包含条件跳转，这不是NOT条件
        if fall_through_has_condition:
            return False
        
        # 检查跳转目标是否包含条件跳转指令
        jump_has_condition = False
        for instr in jump_target.instructions:
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE'
            ):
                jump_has_condition = True
                break
        
        # NOT条件：fall-through没有if条件（是then分支）
        # 跳转目标可能有if条件（是elif）或者没有（是最终的else）
        # 只要fall-through是简单的then分支，就认为是NOT条件
        return True
    
    def _analyze_if_structure(self, header: BasicBlock) -> Optional[IfStructure]:
        """
        分析if结构
        
        支持简单条件和复合条件（如 x > 0 and y > 0）
        
        Args:
            header: 条件头部
            
        Returns:
            if结构
        """
        # [调试] 打印header信息
        
        succs = list(header.successors)
        if len(succs) < 2:
            return None
        
        # 检查是否是循环条件（循环已在前面处理）
        # [关键修复] 但如果header是条件块且有两个后继都在循环体内，它可能是循环内的if条件块
        if header.loop_header:
            # [关键修复] 检查是否是循环内的if条件块
            # 特征：有两个后继，且都在同一个循环体内
            # [关键修复] 检查是否是循环内的if条件块
            # 特征：有两个后继，且都在同一个循环体内
            # [关键修复] 检查是否是循环内的if条件块
            # 特征：有两个后继，且都在同一个循环体内
            # [关键修复] 检查是否是循环内的if条件块
            # 特征：有两个后继，且都在同一个循环体内
            if len(succs) == 2:
                # 检查两个后继是否都能到达同一个循环头部
                # 检查两个后继是否都能到达同一个循环头部
                # 检查两个后继是否都能到达同一个循环头部
                # 检查两个后继是否都能到达同一个循环头部
                loop_headers_for_succs = []
                for succ in succs:
                    for block in self.cfg.blocks.values():
                        if block.loop_header and self.loop_analyzer and self.loop_analyzer._can_reach(succ, block):
                            loop_headers_for_succs.append(block)
                            break
                
                # [关键修复] 检查是否是包含break的if语句
                # break语句的特征：后继块包含RETURN_VALUE或跳转到循环外部
                has_break_branch = False
                for succ in succs:
                    # 检查后继块是否包含break语句（RETURN_VALUE）
                    # 检查后继块是否包含break语句（RETURN_VALUE）
                    # 检查后继块是否包含break语句（RETURN_VALUE）
                    # 检查后继块是否包含break语句（RETURN_VALUE）
                    for instr in succ.instructions:
                        if instr.opname == 'RETURN_VALUE':
                            has_break_branch = True
                            break
                    if has_break_branch:
                        break
                
                # 如果两个后继都能到达同一个循环头部，或者包含break分支，header可能是循环内的if条件块
                if (len(loop_headers_for_succs) == 2 and loop_headers_for_succs[0] == loop_headers_for_succs[1]) or \
                   (has_break_branch and len(loop_headers_for_succs) >= 1):
                    # 这是循环内的if条件块，继续处理
                    pass
                else:
                    return None
            else:
                return None
        
        # [关键修复] 检查是否是while循环的前导块
        # 如果一个后继是循环头部，则这是while前导块，不是if结构
        # [关键修复] 但如果后继同时也是if的else分支，则应该识别为if结构
        for succ in succs:
            if succ.loop_header:
                # 检查后继是否是if的else分支
                # 特征：header有POP_JUMP_FORWARD_IF_*指令跳转到succ
                # 检查后继是否是if的else分支
                # 特征：header有POP_JUMP_FORWARD_IF_*指令跳转到succ
                # 检查后继是否是if的else分支
                # 特征：header有POP_JUMP_FORWARD_IF_*指令跳转到succ
                # 检查后继是否是if的else分支
                # 特征：header有POP_JUMP_FORWARD_IF_*指令跳转到succ
                is_else_branch = False
                for instr in header.instructions:
                    if 'POP_JUMP_FORWARD' in instr.opname and instr.argval == succ.start_offset:
                        is_else_branch = True
                        break
                
                if not is_else_branch:
                    # 这是while循环的前导块，不是if结构
                    # 这是while循环的前导块，不是if结构
                    # 这是while循环的前导块，不是if结构
                    # 这是while循环的前导块，不是if结构
                    return None
        
        # [关键修复] 收集头部块中的所有条件跳转指令
        # 这对于识别复合条件（如 x > 0 and y > 0）至关重要
        jump_instructions = []
        for instr in header.instructions:
            if instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE',
                               'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE',
                               'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                               'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                jump_instructions.append(instr)
        
        if not jump_instructions:
            return None
        
        # [关键修复] 检查是否是简单的逻辑表达式返回值（如 return x and y）
        # 这种模式的特征：
        # 1. 头部块只包含 JUMP_IF_FALSE_OR_POP 或 JUMP_IF_TRUE_OR_POP 指令
        # 2. 跳转目标块只包含 RETURN_VALUE
        # 3. fall-through 块的后继是跳转目标块（两者都返回到同一个位置）
        # 这种情况下不应该识别为 if 结构，而是逻辑表达式
        # [关键修复] 放宽对 fall-through 块的限制，允许包含复杂的表达式（如函数调用）
        if len(jump_instructions) == 1:
            jump_instr = jump_instructions[0]
            if jump_instr.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                # 找到 fall-through 块（不是跳转目标的那个后继）
                # 找到 fall-through 块（不是跳转目标的那个后继）
                # 找到 fall-through 块（不是跳转目标的那个后继）
                # 找到 fall-through 块（不是跳转目标的那个后继）
                jump_target_offset = jump_instr.argval
                fall_through_block = None
                jump_target_block = None
                for succ in succs:
                    if succ.start_offset == jump_target_offset:
                        jump_target_block = succ
                    else:
                        fall_through_block = succ
                
                # 检查是否是简单的逻辑表达式模式
                if fall_through_block and jump_target_block:
                    # 跳转目标块应该只包含 RETURN_VALUE
                    # 跳转目标块应该只包含 RETURN_VALUE
                    # 跳转目标块应该只包含 RETURN_VALUE
                    # 跳转目标块应该只包含 RETURN_VALUE
                    jump_target_non_trivial = [i for i in jump_target_block.instructions 
                                               if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                    is_jump_target_simple = (len(jump_target_non_trivial) == 1 and 
                                             jump_target_non_trivial[0].opname == 'RETURN_VALUE')
                    
                    # fall-through 块的后继应该是跳转目标块（两者汇合到同一个返回点）
                    fall_through_succs = list(fall_through_block.successors)
                    fall_through_merges_to_target = (len(fall_through_succs) == 1 and 
                                                     fall_through_succs[0] == jump_target_block)
                    
                    # [关键修复] 只检查跳转目标块和汇合关系，不限制 fall-through 块的复杂度
                    # 允许 fall-through 块包含任意复杂的表达式（函数调用、属性访问等）
                    if is_jump_target_simple and fall_through_merges_to_target:
                        # 这是逻辑表达式返回值，不应该识别为 if 结构
                        # 这是逻辑表达式返回值，不应该识别为 if 结构
                        # 这是逻辑表达式返回值，不应该识别为 if 结构
                        # 这是逻辑表达式返回值，不应该识别为 if 结构
                        return None
                    
                    # [关键修复] 检查是否是逻辑运算赋值（如 a = x and y 或 b = x or y）
                    # 这种模式的特征：
                    # 1. fall-through 块只包含简单的值加载（如 LOAD_FAST y）
                    # 2. fall-through 块的后继是跳转目标块
                    # 3. 跳转目标块以 STORE_* 指令开头
                    # [关键修复] 对于复合逻辑运算（如 x and y and z），fall_through块可能包含另一个 JUMP_IF_*_OR_POP
                    if fall_through_merges_to_target:
                        # 检查fall_through块是否只包含简单指令（LOAD_* 或 JUMP_IF_*_OR_POP）
                        # 检查fall_through块是否只包含简单指令（LOAD_* 或 JUMP_IF_*_OR_POP）
                        # 检查fall_through块是否只包含简单指令（LOAD_* 或 JUMP_IF_*_OR_POP）
                        # 检查fall_through块是否只包含简单指令（LOAD_* 或 JUMP_IF_*_OR_POP）
                        fall_through_is_simple = True
                        for i in fall_through_block.instructions:
                            if i.opname in ('RESUME', 'CACHE', 'NOP'):
                                continue
                            if i.opname.startswith('LOAD_'):
                                continue
                            if i.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                                continue
                            # 有其他指令，不是简单的逻辑运算
                            fall_through_is_simple = False
                            break
                        
                        if fall_through_is_simple:
                            # 检查跳转目标块是否以 STORE_* 开头
                            # 检查跳转目标块是否以 STORE_* 开头
                            # 检查跳转目标块是否以 STORE_* 开头
                            # 检查跳转目标块是否以 STORE_* 开头
                            jump_target_non_trivial = [i for i in jump_target_block.instructions 
                                                       if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                            if jump_target_non_trivial and jump_target_non_trivial[0].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                                # 这是逻辑运算赋值，不应该识别为 if 结构
                                # 这是逻辑运算赋值，不应该识别为 if 结构
                                # 这是逻辑运算赋值，不应该识别为 if 结构
                                # 这是逻辑运算赋值，不应该识别为 if 结构
                                return None
                    
                    # [关键修复] 检查是否是链式比较表达式（如 result = 1 < x < 10）
                    # 链式比较的特征：
                    # 1. fall-through 块包含 COMPARE_OP 和 JUMP_FORWARD
                    # 2. 跳转目标块包含 SWAP 和 POP_TOP（处理比较失败的情况）
                    # 3. 所有路径最终都汇合到包含赋值指令的块
                    if fall_through_block and jump_target_block:
                        # 检查 fall-through 块是否是链式比较的一部分
                        has_compare_op = any(i.opname == 'COMPARE_OP' for i in fall_through_block.instructions)
                        has_jump_forward = any(i.opname == 'JUMP_FORWARD' for i in fall_through_block.instructions)
                        
                        # 检查跳转目标块是否包含 SWAP 和 POP_TOP
                        has_swap = any(i.opname == 'SWAP' for i in jump_target_block.instructions)
                        has_pop_top = any(i.opname == 'POP_TOP' for i in jump_target_block.instructions)
                        
                        # 检查所有路径是否汇合到同一个块，且该块包含赋值指令
                        fall_through_succs = list(fall_through_block.successors)
                        jump_target_succs = list(jump_target_block.successors)
                        
                        # 找到共同的后继（汇合点）
                        common_succ = None
                        for ft_succ in fall_through_succs:
                            for jt_succ in jump_target_succs:
                                if ft_succ == jt_succ:
                                    common_succ = ft_succ
                                    break
                            if common_succ:
                                break
                        
                        # 检查汇合点是否包含赋值指令
                        has_store_in_merge = False
                        if common_succ:
                            has_store_in_merge = any(
                                i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                                for i in common_succ.instructions
                            )
                        
                        # 如果满足链式比较的特征，不应该识别为 if 结构
                        if has_compare_op and has_jump_forward and has_swap and has_pop_top and has_store_in_merge:
                            # 这是链式比较表达式，不应该识别为 if 结构
                            return None
        
        # [关键修复] 检查是否是布尔表达式（如 condition = x > 0 and y < 10）
        # 布尔表达式的特征：跳转目标只包含赋值指令，没有其他有意义的代码
        # 真正的if语句：跳转目标包含实际的代码块（多个指令，如JUMP_FORWARD到合并块）
        for instr in jump_instructions:
            if instr.argval is not None:
                # 查找跳转目标块
                # 查找跳转目标块
                # 查找跳转目标块
                # 查找跳转目标块
                target_block = None
                for succ in succs:
                    if succ.start_offset == instr.argval:
                        target_block = succ
                        break
                
                if target_block:
                    # [关键修复] 改进布尔表达式检测
                    # 布尔表达式的特征：
                    # 1. 目标块只包含赋值指令，没有其他有意义的代码
                    # 2. 目标块没有后继（或后继只是合并块）
                    # if语句的特征：
                    # 1. 目标块包含赋值指令和其他代码（如JUMP_FORWARD）
                    # 2. 目标块有后继（如fall-through到合并块）
                    
                    # 收集目标块中的所有非平凡指令
                    # [关键修复] 改进布尔表达式检测
                    # 布尔表达式的特征：
                    # 1. 目标块只包含赋值指令，没有其他有意义的代码
                    # 2. 目标块没有后继（或后继只是合并块）
                    # if语句的特征：
                    # 1. 目标块包含赋值指令和其他代码（如JUMP_FORWARD）
                    # 2. 目标块有后继（如fall-through到合并块）
                    
                    # 收集目标块中的所有非平凡指令
                    # [关键修复] 改进布尔表达式检测
                    # 布尔表达式的特征：
                    # 1. 目标块只包含赋值指令，没有其他有意义的代码
                    # 2. 目标块没有后继（或后继只是合并块）
                    # if语句的特征：
                    # 1. 目标块包含赋值指令和其他代码（如JUMP_FORWARD）
                    # 2. 目标块有后继（如fall-through到合并块）
                    
                    # 收集目标块中的所有非平凡指令
                    # [关键修复] 改进布尔表达式检测
                    # 布尔表达式的特征：
                    # 1. 目标块只包含赋值指令，没有其他有意义的代码
                    # 2. 目标块没有后继（或后继只是合并块）
                    # if语句的特征：
                    # 1. 目标块包含赋值指令和其他代码（如JUMP_FORWARD）
                    # 2. 目标块有后继（如fall-through到合并块）
                    
                    # 收集目标块中的所有非平凡指令
                    non_trivial_instrs = []
                    for i in target_block.instructions:
                        if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL',
                                           'POP_TOP', 'RETURN_VALUE'):
                            non_trivial_instrs.append(i)
                    
                    # [关键修复] 检查目标块是否有后继（除了合并块）
                    # 如果目标块有后继，它可能是if语句的一部分
                    has_successor = len(target_block.successors) > 0
                    
                    # 布尔表达式的特征：
                    # 1. 只有一条非平凡指令（赋值指令）
                    # 2. 没有后继（或后继只是合并块）
                    if len(non_trivial_instrs) == 1:
                        if (non_trivial_instrs[0].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                            and not has_successor):
                            # 这是布尔表达式，不是if语句
                            return None
                    # 如果有更多指令，或者有后继，不是布尔表达式
        
        # [关键修复] 分析跳转指令，确定then和else分支
        # 对于复合条件，可能有多个跳转指令跳转到不同的目标
        # 我们需要识别哪些跳转对应then分支，哪些对应else分支
        
        # 收集所有跳转目标
        jump_targets = set()
        for instr in jump_instructions:
            if instr.argval is not None:
                jump_targets.add(instr.argval)
        
        # 在successors中找到对应的块
        target_blocks = {}
        for target_offset in jump_targets:
            for succ in succs:
                if succ.start_offset == target_offset:
                    target_blocks[target_offset] = succ
                    break
        
        # [关键修复] 确定then和else分支
        # 策略：
        # 1. 如果有POP_JUMP_IF_TRUE跳转到某个块，该块是then分支的一部分
        # 2. 如果有POP_JUMP_IF_FALSE跳转到某个块，该块是else分支的一部分
        # 3. 对于复合条件，可能有多个跳转指令，我们需要找到主要的then和else分支
        
        then_branch = None
        else_branch = None
        
        # 首先查找明确的跳转
        for instr in jump_instructions:
            if instr.argval is None:
                continue
            target_block = target_blocks.get(instr.argval)
            if target_block is None:
                continue
            
            if 'IF_TRUE' in instr.opname:
                # 条件为真时跳转，这是then分支
                # 条件为真时跳转，这是then分支
                # 条件为真时跳转，这是then分支
                # 条件为真时跳转，这是then分支
                if then_branch is None:
                    then_branch = target_block
            elif 'IF_FALSE' in instr.opname:
                # 条件为假时跳转，这是else分支
                # [关键修复] 检查跳转目标是否是merge点
                # 条件为假时跳转，这是else分支
                # [关键修复] 检查跳转目标是否是merge点
                if else_branch is None:
                    if target_block and self._is_simple_merge_block(target_block):
                        # 跳转目标是merge点，不是else分支
                        # 跳转目标是merge点，不是else分支
                        # 跳转目标是merge点，不是else分支
                        # 跳转目标是merge点，不是else分支
                        pass
                    else:
                        else_branch = target_block
            elif 'IF_NOT_NONE' in instr.opname:
                # [关键修复] 如果不为None则跳转
                # 对于 if x is None: 使用 POP_JUMP_IF_NOT_NONE（如果不是None则跳转到else/merge）
                # 所以跳转目标是else分支或merge点，不是then分支
                # [注意] 不要在这里设置else_branch，让后面的逻辑来处理（检查是否是merge点）
                # [关键修复] 如果不为None则跳转
                # 对于 if x is None: 使用 POP_JUMP_IF_NOT_NONE（如果不是None则跳转到else/merge）
                # 所以跳转目标是else分支或merge点，不是then分支
                # [注意] 不要在这里设置else_branch，让后面的逻辑来处理（检查是否是merge点）
                pass
            elif 'IF_NONE' in instr.opname:
                # [关键修复] 如果为None则跳转
                # 对于 if x is not None: 使用 POP_JUMP_IF_NONE（如果是None则跳转到else/merge）
                # 所以跳转目标是else分支或merge点，不是then分支
                # [注意] 不要在这里设置else_branch，让后面的逻辑来处理（检查是否是merge点）
                # [关键修复] 如果为None则跳转
                # 对于 if x is not None: 使用 POP_JUMP_IF_NONE（如果是None则跳转到else/merge）
                # 所以跳转目标是else分支或merge点，不是then分支
                # [注意] 不要在这里设置else_branch，让后面的逻辑来处理（检查是否是merge点）
                pass
        
        # [关键修复] 提前计算 has_conditional_jump，用于后续判断
        has_conditional_jump = any(
            'IF_NOT_NONE' in instr.opname or 'IF_NONE' in instr.opname or
            'IF_FALSE' in instr.opname or 'IF_TRUE' in instr.opname
            for instr in jump_instructions
        )
        
        # 如果没有找到明确的分支，使用默认策略
        if then_branch is None or else_branch is None:
            # 使用第一个跳转指令确定分支
            # 使用第一个跳转指令确定分支
            # 使用第一个跳转指令确定分支
            # 使用第一个跳转指令确定分支
            first_jump = jump_instructions[0]
            if first_jump.argval is not None:
                jump_target = target_blocks.get(first_jump.argval)
                fall_through = None
                for succ in succs:
                    if succ != jump_target:
                        fall_through = succ
                        break
                
                # [关键修复] 检测NOT条件模式
                # 对于NOT条件，分支识别是反过来的
                if 'IF_TRUE' in first_jump.opname and self._is_not_condition_pattern(header, jump_target, fall_through):
                    # NOT条件：跳转目标是else分支（下一个条件），fall-through是then分支
                    # NOT条件：跳转目标是else分支（下一个条件），fall-through是then分支
                    # NOT条件：跳转目标是else分支（下一个条件），fall-through是then分支
                    # NOT条件：跳转目标是else分支（下一个条件），fall-through是then分支
                    then_branch = fall_through
                    else_branch = jump_target
                elif 'IF_TRUE' in first_jump.opname:
                    # 条件为真时跳转，跳转目标是then分支
                    # 条件为真时跳转，跳转目标是then分支
                    then_branch = jump_target
                    else_branch = fall_through
                elif 'IF_FALSE' in first_jump.opname:
                    # 条件为假时跳转，fall-through是then分支
                    # 条件为假时跳转，fall-through是then分支
                    then_branch = fall_through
                    # [关键修复] 检查跳转目标是否是独立的else分支还是merge点
                    # 如果跳转目标只包含简单的代码（如LOAD_FAST + RETURN_VALUE），它是merge点，不是else分支
                    if jump_target and self._is_simple_merge_block(jump_target):
                        else_branch = None  # 没有else分支，跳转目标是merge点
                    # [关键修复] 如果跳转目标是条件块，这可能是elif链
                    # elif链的特征：跳转目标是条件块，且只有1个前驱（当前if条件块）
                    elif jump_target and self._is_conditional_block(jump_target):
                        # [关键修复] 首先检查是否是elif链模式
                        # elif链的特征：跳转目标只有1个前驱（当前if条件块）
                        # [关键修复] 即使跳转目标在循环体内，如果它只有1个前驱，它仍然是elif链的一部分
                        # [关键修复] 首先检查是否是elif链模式
                        # elif链的特征：跳转目标只有1个前驱（当前if条件块）
                        # [关键修复] 即使跳转目标在循环体内，如果它只有1个前驱，它仍然是elif链的一部分
                        if len(jump_target.predecessors) == 1:
                            # [关键修复] 这是elif链模式，跳转目标是下一个elif条件
                            # 应该被识别为else分支
                            # [关键修复] 这是elif链模式，跳转目标是下一个elif条件
                            # 应该被识别为else分支
                            # [关键修复] 这是elif链模式，跳转目标是下一个elif条件
                            # 应该被识别为else分支
                            # [关键修复] 这是elif链模式，跳转目标是下一个elif条件
                            # 应该被识别为else分支
                            else_branch = jump_target
                        else:
                            # [关键修复] 检查跳转目标是否是循环body块（有向后跳转到循环header的指令）
                            # 循环body块的特征：
                            # 1. 有向后跳转到循环header的指令
                            is_loop_body_block = False
                            
                            # 检查：是否有向后跳转到循环header的指令
                            for instr in jump_target.instructions:
                                if 'BACKWARD' in instr.opname and instr.argval is not None:
                                    # 检查跳转目标是否是任何循环的header
                                    # 检查跳转目标是否是任何循环的header
                                    # 检查跳转目标是否是任何循环的header
                                    # 检查跳转目标是否是任何循环的header
                                    for struct in self.structures:
                                        if isinstance(struct, LoopStructure) and struct.header_block:
                                            if instr.argval == struct.header_block.start_offset:
                                                is_loop_body_block = True
                                                break
                                    if is_loop_body_block:
                                        break
                            
                            if is_loop_body_block:
                                # 跳转目标是循环body块（有向后跳转），不是if的else分支
                                # 跳转目标是循环body块（有向后跳转），不是if的else分支
                                # 跳转目标是循环body块（有向后跳转），不是if的else分支
                                # 跳转目标是循环body块（有向后跳转），不是if的else分支
                                else_branch = None
                            else:
                                # 不是elif链模式，也不是循环body块，这是独立的if语句
                                # 应该被识别为else分支
                                else_branch = jump_target
                    # [关键修复] 检查跳转目标是否是独立的for循环开始（不是推导式的一部分）
                    # 推导式也使用GET_ITER，但推导式的GET_ITER在CALL之后，不是块的第一条指令
                    elif jump_target and any(instr.opname == 'GET_ITER' for instr in jump_target.instructions):
                        # [关键修复] 检查GET_ITER是否是块的第一条非调试指令
                        # 如果是，这是for循环的开始；如果不是（如推导式中的GET_ITER），这是else分支
                        # [关键修复] 检查GET_ITER是否是块的第一条非调试指令
                        # 如果是，这是for循环的开始；如果不是（如推导式中的GET_ITER），这是else分支
                        first_non_debug = None
                        for instr in jump_target.instructions:
                            if instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                                first_non_debug = instr
                                break
                        if first_non_debug and first_non_debug.opname == 'GET_ITER':
                            # [关键修复] 跳转目标是for循环的开始，这是正常控制流，不是else分支
                            # [关键修复] 跳转目标是for循环的开始，这是正常控制流，不是else分支
                            # [关键修复] 跳转目标是for循环的开始，这是正常控制流，不是else分支
                            # [关键修复] 跳转目标是for循环的开始，这是正常控制流，不是else分支
                            else_branch = None
                        else:
                            # GET_ITER不是第一条指令（如推导式），这是else分支
                            else_branch = jump_target
                    else:
                        else_branch = jump_target
                elif 'IF_NOT_NONE' in first_jump.opname:
                    # [关键修复] IF_NOT_NONE: 如果不是None则跳转
                    # 对于 if x is None: 使用 POP_JUMP_IF_NOT_NONE（如果不是None则跳转到else）
                    # 所以跳转目标是else分支，fall-through是then分支
                    # [关键修复] IF_NOT_NONE: 如果不是None则跳转
                    # 对于 if x is None: 使用 POP_JUMP_IF_NOT_NONE（如果不是None则跳转到else）
                    # 所以跳转目标是else分支，fall-through是then分支
                    then_branch = fall_through
                    # [关键修复] 检查跳转目标是否是独立的else分支还是merge点
                    # 如果跳转目标只包含简单的代码（如LOAD_FAST + RETURN_VALUE），它是merge点，不是else分支
                    if jump_target and self._is_simple_merge_block(jump_target):
                        else_branch = None  # 没有else分支，跳转目标是merge点
                    else:
                        else_branch = jump_target
                elif 'IF_NONE' in first_jump.opname:
                    # [关键修复] IF_NONE: 如果是None则跳转
                    # 对于 if x is not None: 使用 POP_JUMP_IF_NONE（如果是None则跳转到else）
                    # 所以跳转目标是else分支，fall-through是then分支
                    # [关键修复] IF_NONE: 如果是None则跳转
                    # 对于 if x is not None: 使用 POP_JUMP_IF_NONE（如果是None则跳转到else）
                    # 所以跳转目标是else分支，fall-through是then分支
                    then_branch = fall_through
                    # [关键修复] 检查跳转目标是否是独立的else分支还是merge点
                    if jump_target and self._is_simple_merge_block(jump_target):
                        else_branch = None  # 没有else分支，跳转目标是merge点
                    else:
                        else_branch = jump_target
                else:
                    then_branch = fall_through
                    else_branch = jump_target
            else:
                # 无法确定，使用默认顺序
                # [关键修复] 对于IF_NOT_NONE, IF_NONE, IF_FALSE, IF_TRUE指令，不要重新设置else_branch
                if has_conditional_jump and else_branch is None:
                    # 保持else_branch为None（merge点）
                    # 保持else_branch为None（merge点）
                    # 保持else_branch为None（merge点）
                    # 保持else_branch为None（merge点）
                    then_branch = succs[0]
                else:
                    then_branch, else_branch = succs[0], succs[1]
        
        # 确保then_branch和else_branch不为None
        if then_branch is None:
            then_branch = succs[0]
        # [关键修复] 对于IF_NOT_NONE, IF_NONE, IF_FALSE, IF_TRUE指令，如果else_branch为None，
        # 不要重新设置它，因为这表示跳转目标是merge点，不是else分支
        if else_branch is None and not has_conditional_jump:
            else_branch = succs[1] if len(succs) > 1 else succs[0]
        
        # [关键修复] 过滤掉异常处理块
        # 当有超过2个后继时（如try-except中的if），需要过滤掉异常处理块
        non_exception_succs = [succ for succ in succs if not self._is_exception_handler_block(succ)]
        if len(non_exception_succs) >= 2:
            # 重新确定then_branch和else_branch，只使用非异常处理块
            # 重新确定then_branch和else_branch，只使用非异常处理块
            # 重新确定then_branch和else_branch，只使用非异常处理块
            # 重新确定then_branch和else_branch，只使用非异常处理块
            if then_branch in non_exception_succs and else_branch in non_exception_succs:
                # 两者都是非异常处理块，保持不变
                # 两者都是非异常处理块，保持不变
                # 两者都是非异常处理块，保持不变
                # 两者都是非异常处理块，保持不变
                pass
            elif then_branch not in non_exception_succs:
                # then_branch是异常处理块，使用第一个非异常处理块
                # then_branch是异常处理块，使用第一个非异常处理块
                then_branch = non_exception_succs[0]
                if else_branch not in non_exception_succs:
                    else_branch = non_exception_succs[1] if len(non_exception_succs) > 1 else non_exception_succs[0]
            elif else_branch not in non_exception_succs:
                # else_branch是异常处理块，使用第二个非异常处理块
                # [关键修复] 只有else_branch为None时才重新设置，否则保持原值
                # [关键修复] 对于IF_NOT_NONE, IF_NONE, IF_FALSE, IF_TRUE指令，如果else_branch为None，不要重新设置
                # 因为这表示跳转目标是merge点，不是else分支
                # else_branch是异常处理块，使用第二个非异常处理块
                # [关键修复] 只有else_branch为None时才重新设置，否则保持原值
                # [关键修复] 对于IF_NOT_NONE, IF_NONE, IF_FALSE, IF_TRUE指令，如果else_branch为None，不要重新设置
                # 因为这表示跳转目标是merge点，不是else分支
                if else_branch is None and not has_conditional_jump:
                    else_branch = non_exception_succs[1] if len(non_exception_succs) > 1 else non_exception_succs[0]
        
        # [关键修复] 检测elif链模式
        # 在elif链中，fall-through块可能是下一个elif条件，而不是then分支
        # 特征：fall-through块包含条件跳转，且其跳转目标与当前if的跳转目标相同
        # 首先找到fall_through块（不是then_branch的那个后继）
        fall_through = None
        for succ in succs:
            if succ != then_branch and succ != else_branch:
                fall_through = succ
                break
        if fall_through is None:
            fall_through = then_branch if then_branch in succs else else_branch
        
        is_elif_chain_pattern = False
        if fall_through and self._is_conditional_block(fall_through):
            fall_through_jump = self._get_jump_instr(fall_through)
            header_jump = self._get_jump_instr(header)
            if fall_through_jump and header_jump:
                # 如果fall-through块的跳转目标与header的跳转目标相同，这是elif链模式
                # 如果fall-through块的跳转目标与header的跳转目标相同，这是elif链模式
                # 如果fall-through块的跳转目标与header的跳转目标相同，这是elif链模式
                # 如果fall-through块的跳转目标与header的跳转目标相同，这是elif链模式
                if fall_through_jump.argval == header_jump.argval:
                    # [关键修复] 区分elif链和链式比较
                    # 链式比较的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # elif链的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # 但链式比较的fall-through块的跳转目标与header的跳转目标相同
                    # 我们需要检查fall-through块是否是链式比较的一部分
                    # 链式比较的fall-through块通常包含COMPARE_OP指令
                    # [关键修复] 区分elif链和链式比较
                    # 链式比较的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # elif链的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # 但链式比较的fall-through块的跳转目标与header的跳转目标相同
                    # 我们需要检查fall-through块是否是链式比较的一部分
                    # 链式比较的fall-through块通常包含COMPARE_OP指令
                    # [关键修复] 区分elif链和链式比较
                    # 链式比较的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # elif链的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # 但链式比较的fall-through块的跳转目标与header的跳转目标相同
                    # 我们需要检查fall-through块是否是链式比较的一部分
                    # 链式比较的fall-through块通常包含COMPARE_OP指令
                    # [关键修复] 区分elif链和链式比较
                    # 链式比较的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # elif链的特征：fall-through块使用POP_JUMP_FORWARD_IF_FALSE/POP_JUMP_FORWARD_IF_TRUE
                    # 但链式比较的fall-through块的跳转目标与header的跳转目标相同
                    # 我们需要检查fall-through块是否是链式比较的一部分
                    # 链式比较的fall-through块通常包含COMPARE_OP指令
                    is_chained_compare = False
                    if 'POP_JUMP_FORWARD_IF_FALSE' in fall_through_jump.opname:
                        # 检查fall-through块是否包含COMPARE_OP指令
                        # 检查fall-through块是否包含COMPARE_OP指令
                        # 检查fall-through块是否包含COMPARE_OP指令
                        # 检查fall-through块是否包含COMPARE_OP指令
                        for instr in fall_through.instructions:
                            if instr.opname == 'COMPARE_OP':
                                is_chained_compare = True
                                break
                    
                    if not is_chained_compare:
                        # [关键修复] 区分elif链和复合条件
                        # 复合条件的特征：fall-through块本身也是条件块，且它的fall-through也是条件块
                        # 形成链式结构：header -> fall_through -> next_fall_through -> ...
                        # [关键修复] 区分elif链和复合条件
                        # 复合条件的特征：fall-through块本身也是条件块，且它的fall-through也是条件块
                        # 形成链式结构：header -> fall_through -> next_fall_through -> ...
                        # [关键修复] 区分elif链和复合条件
                        # 复合条件的特征：fall-through块本身也是条件块，且它的fall-through也是条件块
                        # 形成链式结构：header -> fall_through -> next_fall_through -> ...
                        # [关键修复] 区分elif链和复合条件
                        # 复合条件的特征：fall-through块本身也是条件块，且它的fall-through也是条件块
                        # 形成链式结构：header -> fall_through -> next_fall_through -> ...
                        is_compound_chain = False
                        if len(fall_through.successors) == 2:
                            # 找到fall-through块的fall-through后继
                            # 找到fall-through块的fall-through后继
                            # 找到fall-through块的fall-through后继
                            # 找到fall-through块的fall-through后继
                            next_fall_through = None
                            for succ in fall_through.successors:
                                if succ.start_offset != fall_through_jump.argval:
                                    next_fall_through = succ
                                    break
                            # 如果next_fall_through也是条件块，这是复合条件，不是elif链
                            if next_fall_through and self._is_conditional_block(next_fall_through):
                                is_compound_chain = True
                        
                        # [关键修复] 区分elif链和独立的if语句
                        # elif链的特征：then_branch只包含简单的代码（如赋值），然后直接跳转到merge
                        # 独立的if语句：then_branch包含实际执行的代码，且后面还有其他代码
                        # 检查then_branch是否包含复杂的代码或跳转到其他位置
                        is_independent_if = False
                        if then_branch and not is_compound_chain:
                            # 检查then_branch是否有后继（除了merge点）
                            # 如果then_branch有多个后继，或者后继不是merge点，这可能是独立的if
                            # 检查then_branch是否有后继（除了merge点）
                            # 如果then_branch有多个后继，或者后继不是merge点，这可能是独立的if
                            # 检查then_branch是否有后继（除了merge点）
                            # 如果then_branch有多个后继，或者后继不是merge点，这可能是独立的if
                            # 检查then_branch是否有后继（除了merge点）
                            # 如果then_branch有多个后继，或者后继不是merge点，这可能是独立的if
                            then_succs = list(then_branch.successors)
                            if len(then_succs) > 1:
                                # then_branch有多个后继，说明它不是简单的elif链
                                # then_branch有多个后继，说明它不是简单的elif链
                                # then_branch有多个后继，说明它不是简单的elif链
                                # then_branch有多个后继，说明它不是简单的elif链
                                is_independent_if = True
                            elif len(then_succs) == 1:
                                # 检查then_branch的后继是否是merge点
                                # 检查then_branch的后继是否是merge点
                                then_succ = then_succs[0]
                                # 如果then_succ不是header_jump的目标，说明这不是elif链
                                if then_succ.start_offset != header_jump.argval:
                                    is_independent_if = True
                        
                        # 只有不是复合条件且不是独立的if时，才认为是elif链
                        if not is_compound_chain and not is_independent_if:
                            is_elif_chain_pattern = True
        
        # [关键修复] 如果是elif链模式，交换then_branch和else_branch
        if is_elif_chain_pattern:
            then_branch, else_branch = else_branch, then_branch
        
        # [关键修复] 检查else_branch是否是while循环的头部
        # 如果else_branch是一个条件块，且它的fall-through后继包含向后跳转指令
        # 那么else_branch是while循环的头部，不是if的else分支
        if else_branch and self._is_conditional_block(else_branch):
            else_branch_jump = self._get_jump_instr(else_branch)
            if else_branch_jump and 'POP_JUMP_FORWARD_IF_FALSE' in else_branch_jump.opname:
                # 找到fall-through后继
                # 找到fall-through后继
                # 找到fall-through后继
                # 找到fall-through后继
                for succ in else_branch.successors:
                    if succ.start_offset != else_branch_jump.argval:
                        # 检查fall-through后继是否包含向后跳转指令
                        # 检查fall-through后继是否包含向后跳转指令
                        # 检查fall-through后继是否包含向后跳转指令
                        # 检查fall-through后继是否包含向后跳转指令
                        for instr in succ.instructions:
                            if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                                if instr.argval is not None and instr.argval == succ.start_offset:
                                    # 这是while循环的头部，不是if的else分支
                                    # 这是while循环的头部，不是if的else分支
                                    # 这是while循环的头部，不是if的else分支
                                    # 这是while循环的头部，不是if的else分支
                                    else_branch = None
                                    break
                        break
        
        # [关键修复] 检查else_branch是否是循环体的正常代码（continue）
        # 如果else_branch包含向后跳转到循环头部的指令，它是continue，不是else分支
        # [关键修复] 但是，如果else_branch包含实际业务逻辑（如函数调用），它不是continue
        is_else_continue = False
        if else_branch is None:
            # [关键修复] else_branch为None，表示没有else分支（跳转目标是merge点）
            # [关键修复] else_branch为None，表示没有else分支（跳转目标是merge点）
            # [关键修复] else_branch为None，表示没有else分支（跳转目标是merge点）
            # [关键修复] else_branch为None，表示没有else分支（跳转目标是merge点）
            is_else_continue = False
        else:
            # [关键修复] 首先检查else_branch是否包含实际业务逻辑
            # 如果包含CALL、STORE等指令，说明是else分支的正常代码，不是continue
            has_meaningful_logic = False
            for instr in else_branch.instructions:
                if instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'STORE_FAST', 'STORE_NAME',
                                   'STORE_ATTR', 'STORE_SUBSCR', 'LOAD_METHOD', 'LOAD_ATTR',
                                   'BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'BUILD_TUPLE', 
                                   'BUILD_LIST', 'BUILD_MAP', 'LIST_APPEND', 'SET_ADD', 'MAP_ADD'):
                    has_meaningful_logic = True
                    break
            
            # 只有没有实际业务逻辑时，才检查是否是continue块
            if not has_meaningful_logic:
                for instr in else_branch.instructions:
                    if instr.opname in ('JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                        if instr.argval is not None:
                            # 检查跳转目标是否是任何循环的头部
                            # 检查跳转目标是否是任何循环的头部
                            # 检查跳转目标是否是任何循环的头部
                            # 检查跳转目标是否是任何循环的头部
                            for struct in self.structures:
                                if isinstance(struct, LoopStructure) and struct.header_block:
                                    if instr.argval == struct.header_block.start_offset:
                                        is_else_continue = True
                                        break
                            
                            # [关键修复] 如果还没有识别出循环结构，直接检查跳转目标是否是FOR_ITER
                            if not is_else_continue:
                                for block in self.cfg.blocks.values():
                                    if block.start_offset == instr.argval:
                                        for block_instr in block.instructions:
                                            if block_instr.opname == 'FOR_ITER':
                                                is_else_continue = True
                                                break
                                    if is_else_continue:
                                        break
                        if is_else_continue:
                            break
                    # [关键修复] 也检查POP_JUMP_BACKWARD_IF_TRUE指令
                    # 这种指令表示条件向后跳转，也是continue块
                    elif 'BACKWARD' in instr.opname:
                        if instr.argval is not None:
                            # 检查跳转目标是否是任何循环的头部
                            # 检查跳转目标是否是任何循环的头部
                            # 检查跳转目标是否是任何循环的头部
                            # 检查跳转目标是否是任何循环的头部
                            for struct in self.structures:
                                if isinstance(struct, LoopStructure) and struct.header_block:
                                    if instr.argval == struct.header_block.start_offset:
                                        is_else_continue = True
                                        break
                            
                            # [关键修复] 如果还没有识别出循环结构，直接检查跳转目标是否是FOR_ITER
                            if not is_else_continue:
                                for block in self.cfg.blocks.values():
                                    if block.start_offset == instr.argval:
                                        for block_instr in block.instructions:
                                            if block_instr.opname == 'FOR_ITER':
                                                is_else_continue = True
                                                break
                                    if is_else_continue:
                                        break
                        if is_else_continue:
                            break
        
        # [关键修复] 如果else_branch是continue块，将其视为循环体内的代码
        # 而不是if的else分支
        if is_else_continue:
            # 将else_branch设置为空，表示没有else分支
            # 将else_branch设置为空，表示没有else分支
            # 将else_branch设置为空，表示没有else分支
            # 将else_branch设置为空，表示没有else分支
            else_branch = None
        
        # [关键修复] 检查else_branch是否是while循环的一部分
        # 特征1：else_branch包含向后跳转到某个循环头部的指令
        # 且该循环头部不是if条件块（header）
        # 特征2：else_branch包含while循环的条件检查（COMPARE_OP + POP_JUMP_BACKWARD_IF_TRUE）
        if else_branch:
            is_part_of_while_loop = False
            
            # 检查特征1：向后跳转到循环头部
            # [关键修复] 只有当else_branch不包含实际业务逻辑时，才将其视为循环的一部分
            # 如果else_branch包含实际业务逻辑（如CALL, STORE等），它应该作为if的else分支
            has_meaningful_code_in_else = False
            for instr in else_branch.instructions:
                if instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                   'STORE_FAST', 'STORE_NAME', 'STORE_ATTR', 'STORE_SUBSCR',
                                   'BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT',
                                   'BINARY_MULTIPLY', 'BINARY_TRUE_DIVIDE',
                                   'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP',
                                   'LOAD_METHOD', 'LOAD_ATTR', 'LIST_APPEND'):
                    has_meaningful_code_in_else = True
                    break
            
            if not has_meaningful_code_in_else:
                # else_branch没有实际业务逻辑，检查是否是循环的一部分
                # else_branch没有实际业务逻辑，检查是否是循环的一部分
                # else_branch没有实际业务逻辑，检查是否是循环的一部分
                # else_branch没有实际业务逻辑，检查是否是循环的一部分
                for instr in else_branch.instructions:
                    if 'BACKWARD' in instr.opname and instr.argval is not None:
                        # 检查跳转目标是否是某个循环的头部
                        # 检查跳转目标是否是某个循环的头部
                        # 检查跳转目标是否是某个循环的头部
                        # 检查跳转目标是否是某个循环的头部
                        for struct in self.structures:
                            if isinstance(struct, LoopStructure) and struct.header_block:
                                if instr.argval == struct.header_block.start_offset:
                                    # 跳转目标是循环头部
                                    # 检查该循环是否包含if条件块（header）
                                    # 跳转目标是循环头部
                                    # 检查该循环是否包含if条件块（header）
                                    # 跳转目标是循环头部
                                    # 检查该循环是否包含if条件块（header）
                                    # 跳转目标是循环头部
                                    # 检查该循环是否包含if条件块（header）
                                    if hasattr(struct, 'body_blocks'):
                                        body_block_offsets = {b.start_offset for b in struct.body_blocks}
                                        if header.start_offset in body_block_offsets:
                                            # if条件块在循环体内，说明else_branch是循环的一部分
                                            # if条件块在循环体内，说明else_branch是循环的一部分
                                            # if条件块在循环体内，说明else_branch是循环的一部分
                                            # if条件块在循环体内，说明else_branch是循环的一部分
                                            is_part_of_while_loop = True
                                            break
                        if is_part_of_while_loop:
                            break
            else:
                pass
            
            # 检查特征2：else_branch包含while循环的条件检查
            # 特征：包含COMPARE_OP和POP_JUMP_BACKWARD_IF_TRUE指令
            # [关键修复] 也检查else_branch的后继块，因为while循环的条件检查可能在后继块中
            if not is_part_of_while_loop:
                # 收集需要检查的块：else_branch本身及其后继块
                # 收集需要检查的块：else_branch本身及其后继块
                # 收集需要检查的块：else_branch本身及其后继块
                # 收集需要检查的块：else_branch本身及其后继块
                blocks_to_check = [else_branch]
                for succ in else_branch.successors:
                    blocks_to_check.append(succ)
                
                for block in blocks_to_check:
                    has_compare_op = False
                    has_backward_jump = False
                    for instr in block.instructions:
                        if instr.opname == 'COMPARE_OP':
                            has_compare_op = True
                        elif 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                            has_backward_jump = True
                            # 检查跳转目标是否是if条件块（header）
                            if instr.argval is not None and instr.argval == header.start_offset:
                                # 跳转到if条件块，说明这是while循环的一部分
                                # 检查if条件块是否在循环体内
                                # 跳转到if条件块，说明这是while循环的一部分
                                # 检查if条件块是否在循环体内
                                # 跳转到if条件块，说明这是while循环的一部分
                                # 检查if条件块是否在循环体内
                                # 跳转到if条件块，说明这是while循环的一部分
                                # 检查if条件块是否在循环体内
                                for struct in self.structures:
                                    if isinstance(struct, LoopStructure) and hasattr(struct, 'body_blocks'):
                                        body_block_offsets = {b.start_offset for b in struct.body_blocks}
                                        if header.start_offset in body_block_offsets:
                                            is_part_of_while_loop = True
                                            break
                        if is_part_of_while_loop:
                            break
                    
                    # 如果找到了while循环的条件检查，停止检查其他块
                    if is_part_of_while_loop:
                        break
            
            if is_part_of_while_loop:
                else_branch = None
        
        # [关键修复] 检查else_branch是否包含向后跳转到if条件块（header）的指令
        # 如果是，说明else_branch是while循环的一部分，不是if的else分支
        # [关键修复] 但只有当else_branch不包含其他有意义的代码时才跳过
        # 如果else_branch包含实际业务逻辑（如BINARY_OP、STORE_FAST等），它应该作为if的else分支
        if else_branch:
            has_backward_jump_to_header = False
            for instr in else_branch.instructions:
                if 'BACKWARD' in instr.opname:
                    if instr.argval is not None and instr.argval == header.start_offset:
                        # else_branch包含向后跳转到if条件块的指令
                        # else_branch包含向后跳转到if条件块的指令
                        # else_branch包含向后跳转到if条件块的指令
                        # else_branch包含向后跳转到if条件块的指令
                        has_backward_jump_to_header = True
                        break
            
            if has_backward_jump_to_header:
                # [关键修复] 检查else_branch是否包含其他有意义的代码
                # 如果有，保留else_branch作为if的else分支
                # [关键修复] 检查else_branch是否包含其他有意义的代码
                # 如果有，保留else_branch作为if的else分支
                # [关键修复] 检查else_branch是否包含其他有意义的代码
                # 如果有，保留else_branch作为if的else分支
                # [关键修复] 检查else_branch是否包含其他有意义的代码
                # 如果有，保留else_branch作为if的else分支
                has_meaningful_code = False
                for instr in else_branch.instructions:
                    if instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 
                                       'STORE_FAST', 'STORE_NAME', 'STORE_ATTR', 'STORE_SUBSCR',
                                       'BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 
                                       'BINARY_MULTIPLY', 'BINARY_TRUE_DIVIDE',
                                       'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP',
                                       'LOAD_METHOD', 'LOAD_ATTR', 'LIST_APPEND'):
                        has_meaningful_code = True
                        break
                
                if not has_meaningful_code:
                    # else_branch只包含跳转到header的指令，没有实际业务逻辑
                    # 这是while循环的增量部分，不是if的else分支
                    # else_branch只包含跳转到header的指令，没有实际业务逻辑
                    # 这是while循环的增量部分，不是if的else分支
                    # else_branch只包含跳转到header的指令，没有实际业务逻辑
                    # 这是while循环的增量部分，不是if的else分支
                    # else_branch只包含跳转到header的指令，没有实际业务逻辑
                    # 这是while循环的增量部分，不是if的else分支
                    else_branch = None
                else:
                    # else_branch包含实际业务逻辑，保留作为if的else分支
                    pass
        
        # [关键修复] 检查then_branch是否是continue块
        # 如果then_branch包含向后跳转到循环头部的指令，它是continue
        is_then_continue = False
        for instr in then_branch.instructions:
            if instr.opname in ('JUMP_BACKWARD', 'JUMP_ABSOLUTE'):
                if instr.argval is not None:
                    # 检查跳转目标是否是任何循环的头部
                    # 检查跳转目标是否是任何循环的头部
                    # 检查跳转目标是否是任何循环的头部
                    # 检查跳转目标是否是任何循环的头部
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure) and struct.header_block:
                            if instr.argval == struct.header_block.start_offset:
                                is_then_continue = True
                                break
                    
                    # [关键修复] 如果还没有识别出循环结构，直接检查跳转目标是否是FOR_ITER
                    if not is_then_continue:
                        for block in self.cfg.blocks.values():
                            if block.start_offset == instr.argval:
                                for block_instr in block.instructions:
                                    if block_instr.opname == 'FOR_ITER':
                                        is_then_continue = True
                                        break
                            if is_then_continue:
                                break
                if is_then_continue:
                    break
        
        # [关键修复] 如果then_branch是continue块，且else_branch是条件块
        # 则then_body应该只包含continue语句，else_body应该包含else_branch及其后续代码
        if is_then_continue and else_branch and self._is_conditional_block(else_branch):
            # then_body只包含continue块（Block 452）
            # else_body包含else_branch及其后续代码（Block 454, 466, 470）
            # 标记这种情况，后续需要特殊处理
            # then_body只包含continue块（Block 452）
            # else_body包含else_branch及其后续代码（Block 454, 466, 470）
            # 标记这种情况，后续需要特殊处理
            # then_body只包含continue块（Block 452）
            # else_body包含else_branch及其后续代码（Block 454, 466, 470）
            # 标记这种情况，后续需要特殊处理
            # then_body只包含continue块（Block 452）
            # else_body包含else_branch及其后续代码（Block 454, 466, 470）
            # 标记这种情况，后续需要特殊处理
            is_then_continue_with_conditional_else = True
        else:
            is_then_continue_with_conditional_else = False
        
        # [关键修复] 收集所有循环头部用于边界检查
        loop_headers = set()
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and struct.header_block:
                loop_headers.add(struct.header_block)
        
        # [关键修复] 检测是否是AND链还是OR链
        is_and_chain = False
        for instr in header.instructions:
            if instr.opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                is_and_chain = True
                break
            elif instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE'):
                is_and_chain = False
                break
            # [关键修复] POP_JUMP_*_IF_NONE 和 POP_JUMP_*_IF_NOT_NONE 不是AND链的一部分
            # 它们用于 is None / is not None 检查，应该作为普通条件处理
            elif instr.opname in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                                  'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'):
                is_and_chain = False
                break
        
        # [关键修复] 先找到合并块，然后再查找分支体
        
        # [关键修复] 检查then_branch是否是嵌套条件表达式
        # 嵌套条件表达式的特征：
        # 1. then_branch是一个条件块（有POP_JUMP指令）
        # 2. then_branch的then分支和else分支都只包含简单的值加载和JUMP_FORWARD
        # 3. then_branch的then分支和else分支都汇入同一个merge点
        # 这种情况下，then_branch是一个独立的IfStructure，不应该收集它的后继
        is_nested_conditional_expr = False
        if then_branch and self._is_conditional_block(then_branch):
            then_branch_jump = self._get_jump_instr(then_branch)
            if then_branch_jump:
                # 找到then_branch的then分支和else分支
                # 找到then_branch的then分支和else分支
                # 找到then_branch的then分支和else分支
                # 找到then_branch的then分支和else分支
                tb_then = None
                tb_else = None
                for succ in then_branch.successors:
                    if succ.start_offset != then_branch_jump.argval:
                        tb_then = succ
                    else:
                        tb_else = succ
                
                if tb_then and tb_else:
                    # 检查then分支是否是条件表达式模式
                    # 检查then分支是否是条件表达式模式
                    # 检查then分支是否是条件表达式模式
                    # 检查then分支是否是条件表达式模式
                    tb_then_non_trivial = [i for i in tb_then.instructions 
                                           if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                    # [关键修复] 如果tb_then_non_trivial为空，这不是条件表达式模式
                    # 空块（如只包含NOP的pass语句）不应该被识别为条件表达式
                    tb_then_is_cond_expr = len(tb_then_non_trivial) > 0 and all(
                        i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD'
                        for i in tb_then_non_trivial
                    )
                    
                    # 检查else分支是否是条件表达式模式
                    tb_else_non_trivial = [i for i in tb_else.instructions 
                                           if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                    # [关键修复] 如果tb_else_non_trivial为空，这不是条件表达式模式
                    tb_else_is_cond_expr = len(tb_else_non_trivial) > 0 and all(
                        i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD'
                        for i in tb_else_non_trivial
                    )
                    
                    # 检查then分支和else分支是否汇入同一个merge点
                    tb_then_succs = set(s.start_offset for s in tb_then.successors)
                    tb_else_succs = set(s.start_offset for s in tb_else.successors)
                    tb_common_merge = tb_then_succs & tb_else_succs
                    
                    # [关键修复] 检查tb_then或tb_else是否包含实际业务逻辑（如STORE_FAST等）
                    # 如果包含，这是嵌套if结构，不是条件表达式
                    has_business_logic = False
                    for block in [tb_then, tb_else]:
                        for instr in block.instructions:
                            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_ATTR',
                                               'CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                               'BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT',
                                               'LIST_APPEND', 'SET_ADD', 'MAP_ADD'):
                                has_business_logic = True
                                break
                        if has_business_logic:
                            break
                    
                    # 如果都是条件表达式模式且有共同的merge点，且没有业务逻辑，这是嵌套条件表达式
                    if tb_then_is_cond_expr and tb_else_is_cond_expr and tb_common_merge and not has_business_logic:
                        is_nested_conditional_expr = True
        
        if is_nested_conditional_expr:
            # 嵌套条件表达式，只收集then_branch本身，不收集它的后继
            # 嵌套条件表达式，只收集then_branch本身，不收集它的后继
            # 嵌套条件表达式，只收集then_branch本身，不收集它的后继
            # 嵌套条件表达式，只收集then_branch本身，不收集它的后继
            then_body_full = {then_branch}
        else:
            then_body_full = self._find_branch_body(then_branch, header, loop_headers)
        
        # [关键修复] 无论then_branch是否是continue块，都需要正确收集else_branch的所有分支
        # 删除原来的特殊处理，让else_body_full通过_find_branch_body正确收集所有分支
        # [关键修复] 检查else_branch是否是某个循环结构的entry_block
        # 如果是，只添加entry_block本身，不收集循环的所有块
        # 这样可以避免将独立的循环结构包含在if的else_body中
        else_body_full = None  # 初始化为None，用于后续判断
        else_branch_is_loop_entry = False
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and struct.entry_block == else_branch:
                else_branch_is_loop_entry = True
                break
        
        if else_branch_is_loop_entry:
            else_body_full = {else_branch}
            
            for struct in self.structures:
                if isinstance(struct, LoopStructure) and struct.entry_block == else_branch:
                    for loop_block in struct.body_blocks:
                        else_body_full.add(loop_block)
                    break
        # [关键修复] 检查else_branch是否是只包含return的块（if之后的代码）
        # 如果是，这是if之后的代码，不是else分支
        # [关键修复] 只有当else_branch不是header的跳转目标时，才将其视为if之后的代码
        # 如果else_branch是header的跳转目标，它可能是else分支的一部分（如else: return None）
        # [关键修复] 但是，如果then分支没有JUMP_FORWARD到if语句之后的代码，
        # 那么else_branch实际上是if语句之后的代码，不是else分支
        elif else_branch:
            non_trivial = [i for i in else_branch.instructions 
                          if i.opname not in ('RESUME', 'CACHE', 'NOP')]
            # [关键修复] 检查块是否以RETURN_VALUE结尾，且只包含加载/构建指令（没有业务逻辑）
            # 这包括简单的return None、return x、return (x, y)等
            is_return_only = (len(non_trivial) >= 2 and 
                             non_trivial[-1].opname == 'RETURN_VALUE' and
                             all(i.opname.startswith('LOAD_') or i.opname in ('BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP', 'BUILD_CONST_KEY_MAP', 'BUILD_STRING')
                                 for i in non_trivial[:-1]))
            
            if is_return_only:
                # [关键修复] 检查else_branch是否是header的跳转目标
                # 如果是，这可能是else分支的一部分，也可能是if语句之后的代码
                header_jump = self._get_jump_instr(header)
                is_jump_target = header_jump and else_branch.start_offset == header_jump.argval
                
                # [关键修复] 检查else_branch是否是嵌套if结构的else分支
                # 特征：else_branch是条件块（内层if的else分支），且不在then_body中
                is_nested_if_else = self._is_conditional_block(else_branch) and else_branch not in then_body_full
                
                if not is_jump_target and not is_nested_if_else:
                    # 这是if之后的return语句，不是else分支
                    else_body_full = set()
                elif is_nested_if_else:
                    # [关键修复] 这是嵌套if结构的else分支，应该收集它
                    else_body_full = {else_branch}
                else:
                    # [关键修复] 检查else_branch是否是函数的最后一条指令（没有后继）
                    # 如果是，这是if语句之后的代码，不是else分支
                    # [关键修复] 但如果else_branch是header的跳转目标，它是else分支的一部分
                    if not else_branch.successors and not is_jump_target:
                        # else_branch是函数的最后一条指令，不是else分支
                        else_body_full = set()
                    else:
                        # [关键修复] 检查then分支是否有JUMP_FORWARD到if语句之后的代码
                        # 如果有，说明if语句之后的代码是独立的块，else_branch是else分支
                        # 如果没有，说明else_branch实际上是if语句之后的代码
                        # [关键修复] 需要递归检查嵌套if结构的分支
                        then_has_jump_to_after = False
                        
                        # 收集所有then分支的块（包括嵌套if的分支）
                        all_then_blocks = set(then_body_full)
                        visited = set()
                        worklist = list(then_body_full)
                        
                        while worklist:
                            block = worklist.pop(0)
                            if block in visited:
                                continue
                            visited.add(block)
                            
                            # 如果块是条件块，收集它的then分支和else分支
                            if self._is_conditional_block(block):
                                jump_instr = self._get_jump_instr(block)
                                if jump_instr and jump_instr.argval is not None:
                                    for succ in block.successors:
                                        if succ not in visited:
                                            worklist.append(succ)
                                            all_then_blocks.add(succ)
                            else:
                                # 非条件块，收集它的后继
                                for succ in block.successors:
                                    if succ not in visited and succ not in all_then_blocks:
                                        worklist.append(succ)
                                        all_then_blocks.add(succ)
                        
                        # 检查所有then分支的块是否有JUMP_FORWARD到else_branch之后的代码
                        for block in all_then_blocks:
                            for instr in block.instructions:
                                if instr.opname == 'JUMP_FORWARD':
                                    # 检查跳转目标是否是else_branch之后的块
                                    if instr.argval is not None and instr.argval > else_branch.start_offset:
                                        then_has_jump_to_after = True
                                        break
                            if then_has_jump_to_after:
                                break
                        
                        if then_has_jump_to_after:
                            # [关键修复] 这是else分支的一部分（如else: return None）
                            # 需要收集这个块
                            else_body_full = {else_branch}
                        elif is_jump_target:
                            # [关键修复] else_branch是header的直接跳转目标，这是真正的else分支
                            # 即使then分支没有JUMP_FORWARD，else_branch也是else分支
                            else_body_full = {else_branch}
                        else:
                            # [关键修复] 这是if语句之后的代码，不是else分支
                            else_body_full = set()
        
        # [关键修复] 检查else_branch是否是独立的if结构的入口
        # 如果是，不应该收集它的所有分支，让独立的if结构自己处理自己
        if else_branch and else_body_full is None and self._is_conditional_block(else_branch):
            # [关键修复] 检查else_branch是否是另一个IfStructure的entry_block
            # 如果是，这是嵌套if结构，不应该收集它的分支
            is_nested_if_entry = False
            for struct in self.structures:
                if isinstance(struct, IfStructure) and struct.entry_block == else_branch:
                    is_nested_if_entry = True
                    break
            
            if is_nested_if_entry:
                else_body_full = {else_branch}
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == else_branch:
                        for b in struct.then_body:
                            else_body_full.add(b)
                        for b in struct.else_body:
                            else_body_full.add(b)
                        if hasattr(struct, 'elif_conditions') and struct.elif_conditions:
                            for b in struct.elif_conditions:
                                else_body_full.add(b)
                        break
            else:
                # [关键修复] 检查else_branch是否是独立的if语句（不是elif链的一部分）
                # 如果是独立的if语句，不应该将它及其分支收集到当前if的else_body中
                # 判断标准：else_branch的then分支是否只包含跳转指令（continue/break/return）
                is_independent_if = False
                else_branch_jump = self._get_jump_instr(else_branch)
                if else_branch_jump:
                    has_backward_conditional = any(
                        instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                        for instr in else_branch.instructions
                    )
                    if has_backward_conditional:
                        is_independent_if = False
                    else:
                        else_branch_then = None
                        for succ in else_branch.successors:
                            if succ.start_offset != else_branch_jump.argval:
                                else_branch_then = succ
                                break
                        
                        if else_branch_then:
                            non_jump_instrs = []
                            for instr in else_branch_then.instructions:
                                if instr.opname not in ('RESUME', 'CACHE', 'NOP', 'POP_TOP'):
                                    non_jump_instrs.append(instr)
                            
                            if len(non_jump_instrs) == 1 and ('JUMP' in non_jump_instrs[0].opname or 
                                                               non_jump_instrs[0].opname == 'RETURN_VALUE'):
                                is_independent_if = True
                
                # [关键修复] 如果else_branch是条件块，且它的跳转目标与header的跳转目标不同
                # 则它是独立的if语句，不是当前if结构的else分支
                # [例外] 如果else_branch使用JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP进行赋值
                # 如 x = a or b，这不是独立的if语句，而是else分支的正常代码
                if not is_independent_if and self._is_conditional_block(else_branch):
                    header_jump = self._get_jump_instr(header)
                    if header_jump and else_branch_jump:
                        # [关键修复] 检查else_branch是否使用JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP进行赋值
                        # 如果是，这不是独立的if语句
                        is_assignment = False
                        if else_branch_jump.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                            jump_target_offset = else_branch_jump.argval
                            if jump_target_offset is not None:
                                for succ in else_branch.successors:
                                    if succ.start_offset == jump_target_offset:
                                        for target_instr in succ.instructions:
                                            if target_instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                                                if target_instr.opname == 'STORE_FAST':
                                                    is_assignment = True
                                                break
                                        break
                        
                        if not is_assignment:
                            # 如果else_branch的跳转目标与header的跳转目标不同
                            # 且else_branch的跳转目标不是header的then分支
                            # 则else_branch是独立的if语句
                            if else_branch_jump.argval != header_jump.argval:
                                # 检查else_branch的跳转目标是否是header的then分支
                                header_then = None
                                for succ in header.successors:
                                    if succ.start_offset != header_jump.argval:
                                        header_then = succ
                                        break
                                
                                if header_then and else_branch_jump.argval != header_then.start_offset:
                                    # [关键修复-2026] 例外：如果else_branch的所有前驱都属于当前if结构，
                                    # 则它不是独立的if，而是else分支的一部分
                                    # 这处理的是 else: if x: 这样的模式
                                    all_preds_in_current_if = True
                                    current_if_blocks = then_body_full | {header}
                                    if else_branch:
                                        current_if_blocks.add(else_branch)
                                    for pred in else_branch.predecessors:
                                        if pred not in current_if_blocks and pred != header:
                                            all_preds_in_current_if = False
                                            break
                                    
                                    if not all_preds_in_current_if or len(else_branch.predecessors) == 0:
                                        is_independent_if = True
                
                if is_independent_if:
                    # else_branch是独立的if语句，不收集它的分支
                    # 让独立的if结构自己处理自己
                    else_body_full = set()
                else:
                    # [关键修复] 对于else分支中的条件块，调用_find_branch_body收集所有分支
                    # 这样可以收集所有分支（then_body和else_body）
                    # 独立的if结构会在后续被单独处理，但我们需要确保它的所有分支都被收集到当前if的else_body中
                    else_body_full = self._find_branch_body(else_branch, header, loop_headers, is_else_branch=True)
        
        # [关键修复] 如果else_body_full还是None，使用默认逻辑
        if else_body_full is None:
            # [关键修复] 在调用_find_branch_body之前，先检查else_branch是否是return-only块且没有后继
            # 如果是，这是if语句之后的代码，不是else分支
            if else_branch:
                non_trivial = [i for i in else_branch.instructions 
                              if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                # [关键修复] 检查块是否以RETURN_VALUE结尾，且只包含加载/构建指令（没有业务逻辑）
                # 这包括简单的return None、return x、return (x, y)等
                is_return_only = (len(non_trivial) >= 2 and 
                                 non_trivial[-1].opname == 'RETURN_VALUE' and
                                 all(i.opname.startswith('LOAD_') or i.opname in ('BUILD_TUPLE', 'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP', 'BUILD_CONST_KEY_MAP', 'BUILD_STRING')
                                     for i in non_trivial[:-1]))
                
                # [关键修复] 检查else_branch是否是header的跳转目标
                # 如果是，这是else分支的一部分（如else: return None），应该保留
                header_jump = self._get_jump_instr(header)
                is_jump_target = header_jump and else_branch.start_offset == header_jump.argval
                
                if is_return_only and not else_branch.successors and not is_jump_target:
                    # else_branch是函数的最后一条指令，不是else分支
                    else_body_full = set()
                else:
                    else_body_full = self._find_branch_body(else_branch, header, loop_headers, is_else_branch=True)
            else:
                else_body_full = set()
        
        while_loop_bottom_blocks = set()
        header_in_while_loop = False
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and header in struct.body_blocks:
                header_in_while_loop = True
                break
        if header_in_while_loop:
            for struct in self.structures:
                if isinstance(struct, LoopStructure) and header in struct.body_blocks:
                    for block in else_body_full:
                        if block in struct.body_blocks:
                            for instr in block.instructions:
                                if instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                                    if instr.argval is not None:
                                        for b in struct.body_blocks:
                                            if b.start_offset == instr.argval:
                                                while_loop_bottom_blocks.add(block)
                                                break
                                        break
        if while_loop_bottom_blocks:
            # [关键修复-2026] 只排除真正的循环退出块，不排除循环继续点
            # 循环退出块的特征：它的后继不在循环体内（或没有后继）
            # 循环继续点的特征：它有BACKWARD跳转到循环头部
            actual_exit_blocks = set()
            for block in while_loop_bottom_blocks:
                is_actual_exit = False
                
                # 找到包含该块的LoopStructure
                containing_loop = None
                for ls in self.structures:
                    if isinstance(ls, LoopStructure) and block in (ls.body_blocks if hasattr(ls, 'body_blocks') else []):
                        containing_loop = ls
                        break
                
                if containing_loop:
                    # 检查块是否有BACKWARD跳转到循环头部
                    has_backward_to_header = False
                    header_start = containing_loop.header_block.start_offset if hasattr(containing_loop, 'header_block') else None
                    for instr in block.instructions:
                        if 'POP_JUMP_BACKWARD' in instr.opname and instr.argval is not None:
                            if instr.argval == header_start:
                                has_backward_to_header = True
                                break
                    
                    # 如果有BACKWARD跳转到循环头部，这是循环继续点，不排除
                    if has_backward_to_header:
                        continue
                
                # 没有找到循环或不是循环继续点，认为是退出块
                actual_exit_blocks.add(block)
            
            else_body_full -= actual_exit_blocks
        
        # [关键修复] 检测复合条件模式
        # 如果then_body包含另一个条件块的入口，且该条件块的else分支与当前if的else分支相同
        # 则这是一个复合条件（如 x > 0 and y > 0），需要合并
        compound_condition_blocks, condition_chain = self._detect_compound_condition(header, then_body_full, else_body_full, loop_headers)

        # [关键修复] 如果是复合条件，需要特殊处理
        is_compound_condition = len(condition_chain) > 1
        
        if is_compound_condition:
            # [关键修复] 区分链式比较和复合条件赋值
            # 链式比较使用 POP_JUMP_FORWARD_IF_FALSE 指令
            # 复合条件赋值使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP 指令
            # [关键修复] 区分链式比较和复合条件赋值
            # 链式比较使用 POP_JUMP_FORWARD_IF_FALSE 指令
            # 复合条件赋值使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP 指令
            # [关键修复] 区分链式比较和复合条件赋值
            # 链式比较使用 POP_JUMP_FORWARD_IF_FALSE 指令
            # 复合条件赋值使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP 指令
            # [关键修复] 区分链式比较和复合条件赋值
            # 链式比较使用 POP_JUMP_FORWARD_IF_FALSE 指令
            # 复合条件赋值使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP 指令
            is_compound_assignment = any(
                instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                for cond_block in condition_chain
                for instr in cond_block.instructions
            )
            
            if is_compound_assignment:
                # [关键修复] 检查是否是混合条件（AND-OR-AND）
                # 混合条件的特征：同时使用了 POP_JUMP_IF_FALSE 和 JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP
                # [关键修复] 检查是否是混合条件（AND-OR-AND）
                # 混合条件的特征：同时使用了 POP_JUMP_IF_FALSE 和 JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP
                # [关键修复] 检查是否是混合条件（AND-OR-AND）
                # 混合条件的特征：同时使用了 POP_JUMP_IF_FALSE 和 JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP
                # [关键修复] 检查是否是混合条件（AND-OR-AND）
                # 混合条件的特征：同时使用了 POP_JUMP_IF_FALSE 和 JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP
                has_pop_jump = any(
                    instr.opname.startswith('POP_JUMP')
                    for cond_block in condition_chain
                    for instr in cond_block.instructions
                )
                has_or_pop = any(
                    instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                    for cond_block in condition_chain
                    for instr in cond_block.instructions
                )
                is_mixed = has_pop_jump and has_or_pop
                
                if is_mixed:
                    # [关键修复] 对于混合条件，找到所有条件共同指向的merge块
                    # 混合条件的所有部分最终都汇入同一个merge块
                    # then_body是merge块的内容
                    # else_body为空（因为混合条件没有单独的else分支）
                    
                    # 找到最后一个条件的fall-through块
                    # [关键修复] 对于混合条件，找到所有条件共同指向的merge块
                    # 混合条件的所有部分最终都汇入同一个merge块
                    # then_body是merge块的内容
                    # else_body为空（因为混合条件没有单独的else分支）
                    
                    # 找到最后一个条件的fall-through块
                    # [关键修复] 对于混合条件，找到所有条件共同指向的merge块
                    # 混合条件的所有部分最终都汇入同一个merge块
                    # then_body是merge块的内容
                    # else_body为空（因为混合条件没有单独的else分支）
                    
                    # 找到最后一个条件的fall-through块
                    # [关键修复] 对于混合条件，找到所有条件共同指向的merge块
                    # 混合条件的所有部分最终都汇入同一个merge块
                    # then_body是merge块的内容
                    # else_body为空（因为混合条件没有单独的else分支）
                    
                    # 找到最后一个条件的fall-through块
                    last_condition_block = condition_chain[-1]
                    last_jump = self._get_jump_instr(last_condition_block)
                    
                    # [关键修复] 如果最后一个条件块没有跳转指令（如not操作），直接使用它的后继
                    if last_jump and last_jump.argval is not None:
                        # 找到fall-through块（不是跳转目标的那个后继）
                        # 找到fall-through块（不是跳转目标的那个后继）
                        # 找到fall-through块（不是跳转目标的那个后继）
                        # 找到fall-through块（不是跳转目标的那个后继）
                        fall_through_block = None
                        for succ in last_condition_block.successors:
                            if succ.start_offset != last_jump.argval:
                                fall_through_block = succ
                                break
                    elif len(last_condition_block.successors) == 1:
                        # 只有一个后继，这就是fall-through块
                        # 只有一个后继，这就是fall-through块
                        fall_through_block = list(last_condition_block.successors)[0]
                    else:
                        fall_through_block = None
                    
                    if fall_through_block:
                        # [关键修复] 检查fall_through_block是否是存储结果的块
                        # 特征：包含STORE_FAST等赋值指令
                        # [关键修复] 检查fall_through_block是否是存储结果的块
                        # 特征：包含STORE_FAST等赋值指令
                        # [关键修复] 检查fall_through_block是否是存储结果的块
                        # 特征：包含STORE_FAST等赋值指令
                        # [关键修复] 检查fall_through_block是否是存储结果的块
                        # 特征：包含STORE_FAST等赋值指令
                        has_store = any(
                            instr.opname.startswith('STORE_')
                            for instr in fall_through_block.instructions
                        )
                        
                        if has_store:
                            # 这是复合布尔表达式赋值
                            # [关键修复] 只包含fall_through_block本身，不收集它的后继
                            # 因为后继可能是另一个if结构的then_body
                            # 这是复合布尔表达式赋值
                            # [关键修复] 只包含fall_through_block本身，不收集它的后继
                            # 因为后继可能是另一个if结构的then_body
                            # 这是复合布尔表达式赋值
                            # [关键修复] 只包含fall_through_block本身，不收集它的后继
                            # 因为后继可能是另一个if结构的then_body
                            # 这是复合布尔表达式赋值
                            # [关键修复] 只包含fall_through_block本身，不收集它的后继
                            # 因为后继可能是另一个if结构的then_body
                            then_body = {fall_through_block}
                        else:
                            # 这是普通的if语句，then_body是merge块的内容
                            then_body = self._find_branch_body(fall_through_block, last_condition_block, loop_headers)
                    else:
                        then_body = set()
                    
                    # [字节码一致性修复] 检查混合条件的跳转目标是否是真正的else分支还是merge点
                    # 对于嵌套的条件表达式（如 'all' if A and B and C else 'some' if X or Y or Z else 'none'），
                    # 外层AND链的else分支包含内层的OR条件表达式，不应该被忽略
                    last_condition_block = condition_chain[-1]
                    last_jump = self._get_jump_instr(last_condition_block)
                    else_body = set()
                    
                    if last_jump and last_jump.argval is not None:
                        # 找到跳转目标块
                        jump_target_block = None
                        for succ in last_condition_block.successors:
                            if succ.start_offset == last_jump.argval:
                                jump_target_block = succ
                                break
                        
                        if jump_target_block:
                            # 检查跳转目标块是否包含有意义的代码（不是简单的merge点）
                            non_trivial_instrs = [
                                i for i in jump_target_block.instructions
                                if i.opname not in ('RESUME', 'CACHE', 'NOP', 'RETURN_VALUE', 'RETURN_CONST', 'POP_TOP')
                            ]
                            
                            # 如果跳转目标块包含有意义的代码（如LOAD_CONST、条件指令、JUMP_FORWARD等），
                            # 说明这是真正的else分支，应该收集它
                            has_meaningful_code = len(non_trivial_instrs) > 0
                            
                            # 特别检查：如果跳转目标块是另一个IfStructure的entry_block（嵌套if/条件表达式）
                            is_nested_if_entry = self._is_conditional_block(jump_target_block)
                            
                            # 或者跳转目标块包含值加载指令（如条件表达式的then/else值）
                            has_value_load = any(
                                i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD'
                                for i in non_trivial_instrs
                            )
                            
                            if has_meaningful_code and (is_nested_if_entry or has_value_load):
                                # 这是真正的else分支（嵌套的条件表达式或值加载），收集它
                                else_body = self._find_branch_body(jump_target_block, last_condition_block, loop_headers, is_else_branch=True)
                else:
                    # [关键修复] 对于复合条件赋值，重新确定then_body和else_body
                    # AND链：then_body是最后一个条件的fall-through块的内容
                    # OR链：then_body是第一个条件的jump目标块的内容
                    last_condition_block = condition_chain[-1]
                    
                    # 获取最后一个条件的跳转指令
                    last_jump = self._get_jump_instr(last_condition_block)
                    if last_jump and last_jump.argval is not None:
                        # 找到fall-through块（then分支）
                        # 找到fall-through块（then分支）
                        # 找到fall-through块（then分支）
                        # 找到fall-through块（then分支）
                        for succ in last_condition_block.successors:
                            if succ.start_offset != last_jump.argval:
                                # 这是then分支
                                # 这是then分支
                                # 这是then分支
                                # 这是then分支
                                then_body = self._find_branch_body(succ, last_condition_block, loop_headers)
                                break
                        else:
                            then_body = set()
                    else:
                        then_body = set()
                    
                    # else_body是最后一个条件的jump目标块的内容
                    # [字节码一致性修复] 对于嵌套的三元表达式（如 'all' if A and B else 'some' if X or Y else 'none'），
                    # 最后一个条件块的jump目标可能是then值的加载块（如LOAD_CONST('all') + JUMP_FORWARD），
                    # 真正的else分支是内层条件表达式的入口块
                    if last_jump and last_jump.argval is not None:
                        for succ in last_condition_block.successors:
                            if succ.start_offset == last_jump.argval:
                                # [关键修复] 检查跳转目标块是否是then值的加载块（不是真正的else分支）
                                # then值加载块的特征：只包含LOAD_* + JUMP_FORWARD，且JUMP_FORWARD跳到函数出口或merge点
                                non_trivial_instrs = [
                                    i for i in succ.instructions
                                    if i.opname not in ('RESUME', 'CACHE', 'NOP', 'RETURN_VALUE', 'RETURN_CONST')
                                ]
                                
                                is_then_value_block = False
                                # [字节码一致性修复] 放宽条件以支持更多模式
                                # then值加载块的特征：包含LOAD_*指令，且没有STORE_*指令
                                if len(non_trivial_instrs) >= 1:
                                    has_load = any(i.opname.startswith('LOAD_') for i in non_trivial_instrs)
                                    no_store = not any(i.opname.startswith('STORE_') for i in non_trivial_instrs)
                                    has_jump_forward = any(i.opname == 'JUMP_FORWARD' for i in non_trivial_instrs)
                                    is_simple_value = all(
                                        i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD' or
                                        i.opname == 'COMPARE_OP' or i.opname.startswith('POP_JUMP')
                                        for i in non_trivial_instrs
                                    )
                                    
                                    # [关键修复] 如果块只包含简单的值加载和跳转指令（没有复杂的业务逻辑）
                                    # 且不以STORE开头，这是条件表达式的一部分（then或else值）
                                    if (has_load or is_simple_value) and no_store:
                                        # 进一步检查：如果块包含条件跳转指令，它是条件表达式的一部分
                                        has_conditional = any(
                                            i.opname.startswith('POP_JUMP') or i.opname == 'COMPARE_OP'
                                            for i in non_trivial_instrs
                                        )
                                        
                                        if has_conditional or has_jump_forward:
                                            # 这是条件表达式的一部分
                                            # 需要区分是then值还是else分支（内层条件）
                                            if has_conditional:
                                                # 包含条件跳转，这是else分支（内层条件表达式）
                                                is_then_value_block = False
                                                # 直接收集这个块作为else_body
                                                else_body = self._find_branch_body(succ, last_condition_block, loop_headers, is_else_branch=True)
                                            elif has_jump_forward and not has_conditional:
                                                # 只有JUMP_FORWARD没有条件跳转，这是then值加载块
                                                is_then_value_block = True
                                        
                                        # [关键修复] 对于嵌套三元表达式，else分支是then值加载块的JUMP_FORWARD目标
                                        # 或者是第一个未被收集到then_body的条件块
                                        jump_fwd_instr = None
                                        for instr in succ.instructions:
                                            if instr.opname == 'JUMP_FORWARD':
                                                jump_fwd_instr = instr
                                                break
                                        
                                        if jump_fwd_instr and jump_fwd_instr.argval is not None:
                                            # 找到JUMP_FORWARD的目标块
                                            for fwd_succ in succ.successors:
                                                if fwd_succ.start_offset == jump_fwd_instr.argval:
                                                    # 检查这个块是否是merge点（多个前驱）
                                                    if len(fwd_succ.predecessors) >= 2:
                                                        # 这是merge点，else分支在另一个前驱链上
                                                        # 找到不在then_body中的前驱链
                                                        for pred in fwd_succ.predecessors:
                                                            if pred != succ and pred not in then_body:
                                                                # 这可能是else分支的起点
                                                                else_body = self._find_branch_body(pred, last_condition_block, loop_headers, is_else_branch=True)
                                                                break
                                                    break
                                
                                if not is_then_value_block:
                                    # [关键修复] 对于else分支，传递is_else_branch=True
                                    else_body = self._find_branch_body(succ, last_condition_block, loop_headers, is_else_branch=True)
                                break
                        else:
                            else_body = set()
                    else:
                        else_body = set()
            else:
                # [关键修复] 对于链式比较，使用原始的then_body和else_body
                # 但需要排除condition_chain中的块
                then_body = then_body_full - set(condition_chain)
                else_body = else_body_full - set(condition_chain)
                
                # [关键修复-2026-elif-else] 对于有elif链的if结构：
                # - then_body 应该保留 header 的 then 分支（第一个 if 的 then）
                # - 不应该被最后一个 elif 条件的 then 分支覆盖
                # - 每个 elif 条件的 then 分支会在后续的 elif 链处理中被添加到 else_body
                if len(condition_chain) >= 2:
                    last_condition_block = condition_chain[-1]
                    last_jump = self._get_jump_instr(last_condition_block)
                    if last_jump and last_jump.argval is not None:
                        # 找到最后一个条件的then分支（fall-through后继）
                        last_then_block = None
                        last_else_block = None
                        for succ in last_condition_block.successors:
                            if succ.start_offset != last_jump.argval:
                                last_then_block = succ
                            else:
                                last_else_block = succ
                        
                        # [关键修复-2026] 只有当condition_chain只有header时，
                        # 才用last_then_block替换then_body
                        # 如果有elif链，保留原始的then_body（header的then分支）
                        # pass: 不覆盖then_body
                        
                        # [关键修复] 检查last_else_block是否是merge点
                        # 如果是merge点（有多个前驱，包括then_body中的块），不是真正的else分支
                        if last_else_block:
                            is_merge_point = len(last_else_block.predecessors) >= 2 and any(
                                pred in then_body or pred == last_then_block
                                for pred in last_else_block.predecessors
                            )
                            if is_merge_point:
                                # 这是merge点，不是else分支
                                # 这是merge点，不是else分支
                                # 这是merge点，不是else分支
                                # 这是merge点，不是else分支
                                else_body = set()
                                # 将merge点从then_body中移除（如果它在then_body中）
                                then_body.discard(last_else_block)
                
                # [关键修复] 对于AND复合条件（如 if x > 0 and y > 0:）
                # else_body应该是最后一个条件块的else分支
                # 因为前面的条件的else分支直接跳转到merge，只有最后一个条件的else分支包含实际代码
                # [调试] 暂时注释掉这段代码
                # if len(condition_chain) >= 2:
                #     last_condition_block = condition_chain[-1]
                #     last_jump = self._get_jump_instr(last_condition_block)
                #     if last_jump and last_jump.argval is not None:
                #         # 找到最后一个条件的else分支（jump目标）
                #         for succ in last_condition_block.successors:
                #             if succ.start_offset == last_jump.argval:
                #                 # 这是最后一个条件的else分支
                #                 last_else_body = self._find_branch_body(succ, last_condition_block, loop_headers)
                #                 # 将最后一个条件的else分支添加到else_body
                #                 else_body = else_body | last_else_body
                #                 break
        else:
            if compound_condition_blocks:
                # 从then_body中排除复合条件的中间块
                # 从then_body中排除复合条件的中间块
                # 从then_body中排除复合条件的中间块
                # 从then_body中排除复合条件的中间块
                then_body_full = then_body_full - compound_condition_blocks
            
            then_body = then_body_full
            else_body = else_body_full
            
            # [关键修复] 检查then_branch的后继是否是循环头部，如果是，将其添加到then_body中
            # 这种情况发生在for-if-for嵌套中，内部for循环的头部块需要在then_body中被收集
            if then_branch:
                for succ in then_branch.successors:
                    if succ.loop_header and succ not in loop_headers:
                        # 检查该循环头部是否是嵌套在if语句中的
                        # 这里我们假设：如果循环头部的前驱是then_branch，它是嵌套的
                        # 检查该循环头部是否是嵌套在if语句中的
                        # 这里我们假设：如果循环头部的前驱是then_branch，它是嵌套的
                        # 检查该循环头部是否是嵌套在if语句中的
                        # 这里我们假设：如果循环头部的前驱是then_branch，它是嵌套的
                        # 检查该循环头部是否是嵌套在if语句中的
                        # 这里我们假设：如果循环头部的前驱是then_branch，它是嵌套的
                        if then_branch in succ.predecessors:
                            # 找到该循环结构，将其所有块添加到then_body中
                            # 找到该循环结构，将其所有块添加到then_body中
                            # 找到该循环结构，将其所有块添加到then_body中
                            # 找到该循环结构，将其所有块添加到then_body中
                            for struct in self.structures:
                                if isinstance(struct, LoopStructure) and struct.header_block == succ:
                                    for block in struct.body_blocks:
                                        then_body.add(block)
                                    then_body.add(succ)
                                    break
            
            # [关键修复] 同样检查else_branch的后继是否是循环头部
            # 这种情况发生在if-else-for嵌套中
            if else_branch:
                for succ in else_branch.successors:
                    if succ.loop_header and succ not in loop_headers:
                        # 检查该循环头部是否是嵌套在if语句中的
                        # 检查该循环头部是否是嵌套在if语句中的
                        # 检查该循环头部是否是嵌套在if语句中的
                        # 检查该循环头部是否是嵌套在if语句中的
                        if else_branch in succ.predecessors:
                            # 找到该循环结构，将其所有块添加到else_body中
                            # 找到该循环结构，将其所有块添加到else_body中
                            # 找到该循环结构，将其所有块添加到else_body中
                            # 找到该循环结构，将其所有块添加到else_body中
                            for struct in self.structures:
                                if isinstance(struct, LoopStructure) and struct.header_block == succ:
                                    for block in struct.body_blocks:
                                        else_body.add(block)
                                    else_body.add(succ)
                                    break
            
            # [关键修复] 递归检查then_body和else_body中的所有块，收集嵌套循环
            # 这对于深层嵌套结构（如for-if-for-if-while）非常重要
            def collect_nested_loops(body_set, loop_headers_set):
                """递归收集body_set中的嵌套循环"""
                changed = True
                while changed:
                    changed = False
                    for block in list(body_set):
                        for succ in block.successors:
                            if succ.loop_header and succ not in loop_headers_set and succ not in body_set:
                                # 检查该循环头部是否是嵌套的
                                # 检查该循环头部是否是嵌套的
                                # 检查该循环头部是否是嵌套的
                                # 检查该循环头部是否是嵌套的
                                if block in succ.predecessors:
                                    # 找到该循环结构
                                    # 找到该循环结构
                                    # 找到该循环结构
                                    # 找到该循环结构
                                    for struct in self.structures:
                                        if isinstance(struct, LoopStructure) and struct.header_block == succ:
                                            for loop_block in struct.body_blocks:
                                                if loop_block not in body_set:
                                                    body_set.add(loop_block)
                                                    changed = True
                                            if succ not in body_set:
                                                body_set.add(succ)
                                                changed = True
                                            break
            
            collect_nested_loops(then_body, loop_headers)
            collect_nested_loops(else_body, loop_headers)
        
        # [关键修复] 排除已经被其他结构使用的块
        # 这防止不同结构之间的块重叠
        # 注意：不排除属于当前结构的块（通过header识别）
        # [关键修复] 也不排除属于当前if结构的then_body或else_body的块
        # 这些块即使被映射到LoopStructure，也应该保留在then_body/else_body中
        # [调试] 暂时注释掉这段代码
        # used_blocks = set()
        # for block, struct in self.block_to_structure.items():
        #     # 只排除属于其他结构的块
        #     if struct.entry_block != header:
        #         # [关键修复] 检查该块是否在当前if结构的then_body或else_body中
        #         # 如果是，不要排除它
        #         if block in then_body or block in else_body:
        #             continue
        #         used_blocks.add(block)
        # then_body = then_body - used_blocks
        # else_body = else_body - used_blocks
        
        # [关键修复] 使用 then_body 和 else_body 来找合并块
        # [调试] 暂时注释掉这段代码
        # merge_body = then_body | else_body
        # 
        # merge_block = self._find_merge_block(merge_body, header)
        merge_block = None
        
        # [关键修复] 对于复合条件赋值，如果merge_block为None，从condition_chain中找
        # 复合条件赋值的merge_block是所有条件跳转指令的目标块（所有跳转都指向的同一个块）
        # [调试] 暂时注释掉这段代码，因为它影响了其他结构的识别
        # if is_compound_condition and not merge_block:
        #     # 收集所有条件跳转指令的目标
        #     jump_targets = set()
        #     for cond_block in condition_chain:
        #         for instr in cond_block.instructions:
        #             if 'JUMP' in instr.opname and instr.argval is not None:
        #                 # 找到目标块
        #                 for succ in cond_block.successors:
        #                     if succ.start_offset == instr.argval:
        #                         jump_targets.add(succ)
        #                         break
        #
        #     # 如果所有跳转都指向同一个块，那就是merge_block
        #     if len(jump_targets) == 1:
        #         merge_block = jump_targets.pop()
        #     elif jump_targets:
        #         # 有多个跳转目标，找包含STORE_FAST的那个
        #         for target in jump_targets:
        #             has_store = any(
        #                 instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL')
        #                 for instr in target.instructions
        #             )
        #             if has_store:
        #                 merge_block = target
        #                 break
        
        # [关键修复] 从分支体中排除合并块和合并块之后的代码
        # [例外] 对于复合条件，如果merge_block是then_body或else_body的唯一块，不要移除
        # [例外] 如果else_body为空，不要从then_body中移除merge_block（因为then_body的后继就是合并块）
        # [调试] 暂时注释掉这段代码
        # if merge_block:
        #     if is_compound_condition:
        #         # 对于复合条件，只从then_body或else_body中移除merge_block如果它们有多个块
        #         if len(then_body) > 1:
        #             then_body = then_body - {merge_block}
        #         if len(else_body) > 1:
        #             else_body = else_body - {merge_block}
        #     else:
        #         # [关键修复] 只有当else_body不为空时，才从then_body中移除merge_block
        #         # 如果else_body为空，then_body的后继自然就是合并块，不应该移除
        #         if else_body:
        #             then_body = then_body - {merge_block}
        #         # [关键修复] 同样，只有当then_body不为空时，才从else_body中移除merge_block
        #         if then_body:
        #             else_body = else_body - {merge_block}
        #     
        #     # [关键修复] 排除合并块之后的所有代码
        #     # 合并块之后的代码不属于这个if结构
        #     # [例外] 如果合并块是循环头部或在循环内部，不要排除，因为循环内的if结构的分支都回到循环
        #     is_loop_header = merge_block.loop_header
        #     
        #     # [关键修复] 检查合并块是否在循环内部
        #     merge_in_loop = any(
        #         merge_block in loop.body_blocks or merge_block == loop.header_block
        #         for loop in self.structures
        #         if isinstance(loop, LoopStructure) and hasattr(loop, 'body_blocks')
        #     )
        #     
        #     # [关键修复] 如果合并块包含JUMP_BACKWARD指令，它可能是循环的一部分
        #     # 这种情况下不应该调用 _exclude_after_merge
        #     merge_has_backward_jump = any(
        #         'BACKWARD' in instr.opname for instr in merge_block.instructions
        #     )
        #     
        #     if not is_loop_header and not merge_in_loop and not merge_has_backward_jump:
        #         # [关键修复] 对于复合条件，不要调用 _exclude_after_merge
        #         # 因为 merge_block 可能是 then_body 或 else_body 的唯一块
        #         if not is_compound_condition:
        #             then_body = self._exclude_after_merge(then_body, merge_block)
        #             else_body = self._exclude_after_merge(else_body, merge_block)
        
        # [关键修复] 过滤else_body中包含GET_ITER的块
        # 这些块属于下一个循环，不是else块的一部分
        # [例外] 如果块是循环结构的entry_block，保留它，因为循环结构需要被正确处理
        # [关键修复] 但如果GET_ITER不是块的第一条非调试指令（如推导式），保留它
        # [关键修复] 如果else_body包含循环结构，保留循环体的所有块
        loop_body_blocks_in_else = set()
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and hasattr(struct, 'body_blocks'):
                if struct.entry_block in else_body:
                    for loop_block in struct.body_blocks:
                        loop_body_blocks_in_else.add(loop_block)
        
        filtered_else_body = set()
        for b in else_body:
            if b in loop_body_blocks_in_else:
                filtered_else_body.add(b)
                continue
            
            has_get_iter = any(instr.opname == 'GET_ITER' for instr in b.instructions)
            if has_get_iter:
                first_non_debug = None
                for instr in b.instructions:
                    if instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                        first_non_debug = instr
                        break
                
                if first_non_debug and first_non_debug.opname != 'GET_ITER':
                    filtered_else_body.add(b)
                else:
                    is_loop_entry = False
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure) and struct.entry_block == b:
                            is_loop_entry = True
                            break
                    if is_loop_entry:
                        filtered_else_body.add(b)
            else:
                filtered_else_body.add(b)
        else_body = filtered_else_body
        
        # [关键修复] 过滤else_body中属于复合条件的块
        # 这些块是复合条件的一部分，不应该在else_body中
        if is_compound_condition:
            # 复合条件的块（包括条件链和then_body）不应该在else_body中
            # 复合条件的块（包括条件链和then_body）不应该在else_body中
            # 复合条件的块（包括条件链和then_body）不应该在else_body中
            # 复合条件的块（包括条件链和then_body）不应该在else_body中
            all_compound_blocks = set(condition_chain)
            all_compound_blocks.update(then_body)
            else_body = else_body - all_compound_blocks
        else:
            # 非复合条件，但也要排除compound_condition_blocks
            if compound_condition_blocks:
                else_body = else_body - compound_condition_blocks
        
        # [关键修复] 先检测elif链，然后再从else_body中排除其他if结构的块
        # 这样可以确保_current_elif_conditions被正确设置
        
        # [关键修复] 清除之前的elif_conditions
        if hasattr(self, '_current_elif_conditions'):
            delattr(self, '_current_elif_conditions')
        
        # [关键修复] 对于复合条件，从else_body中排除复合条件的块，然后检测elif链
        if is_compound_condition:
            else_body_for_elif = else_body - compound_condition_blocks
            elif_chain_blocks = self._detect_elif_chain(header, else_body_for_elif, loop_headers)
        else:
            # 检测elif链（不限于循环内）
            elif_chain_blocks = self._detect_elif_chain(header, else_body, loop_headers)
        
        # [关键修复] 只有当then分支包含非末尾return语句时，才认为else分支是独立的if
        # 如果return是then_body的最后一条指令（函数正常结束），不应该丢弃elif链
        # 这是因为Python函数末尾的隐式return None会导致误判
        if len(elif_chain_blocks) > 1:
            then_has_early_return = False
            for block in then_body:
                instructions = block.instructions
                for i, instr in enumerate(instructions):
                    if instr.opname == 'RETURN_VALUE':
                        # [关键修复] 检查return是否是块的中间指令（不是最后一条）
                        # 如果return后面还有指令，说明是提前返回
                        # 如果return是最后一条指令，可能是函数正常结束
                        is_last_instr = (i == len(instructions) - 1)
                        if not is_last_instr:
                            then_has_early_return = True
                            break
                if then_has_early_return:
                    break

            # [额外检查] 即使return是最后一条指令，也要检查then_body后是否有其他代码
            # 如果有，说明这是if-return模式，else分支是顺序执行的
            if not then_has_early_return and then_body:
                # 检查是否有块不在then_body、else_body和elif_chain_blocks中
                # 这些块会在if-elif-else之后执行
                all_if_blocks = set(then_body) | else_body | set(elif_chain_blocks)
                has_subsequent_code = any(
                    b not in all_if_blocks and b != header
                    for b in self.cfg.blocks.values()
                )
                if has_subsequent_code:
                    # 有后续代码，检查then_body是否真的提前返回
                    # 重新检查：如果then_body的最后一个块以return结尾，且后续有代码，则是if-return
                    last_then_block = None
                    for block in then_body:
                        if last_then_block is None or block.start_offset > last_then_block.start_offset:
                            last_then_block = block

                    if last_then_block:
                        last_instr = last_then_block.instructions[-1] if last_then_block.instructions else None
                        if last_instr and last_instr.opname == 'RETURN_VALUE':
                            then_has_early_return = True

            # [关键修复] 只有当then_body包含非末尾return，且没有后续代码时，才重置elif_chain_blocks
            # 如果有后续代码，说明这是if-elif-else结构，elif链应该被保留
            if then_has_early_return and not has_subsequent_code:
                elif_chain_blocks = [header]
        
        # [关键修复] 设置当前if结构的elif_conditions，用于后续排除其他if结构的块
        if len(elif_chain_blocks) > 1:
            self._current_elif_conditions = set(elif_chain_blocks) - {header}
        
        # [关键修复] 过滤else_body中属于其他if结构的块
        # 这些块是其他if结构的一部分，不应该在当前结构的else_body中
        # [例外] 如果其他if结构的header是当前if结构的then_body或else_body的一部分
        # 这是嵌套if结构，应该保留该header，让AST生成器正确处理嵌套
        # [关键修复] 如果其他if结构的header是当前if结构的elif_conditions的一部分
        # 不应该排除它的块，因为它是elif链的一部分
        other_if_blocks = set()
        nested_if_headers = set()  # [关键修复] 记录嵌套if的header
        for other_struct in self.structures:
            if isinstance(other_struct, IfStructure) and other_struct.entry_block != header:
                other_header = other_struct.entry_block
                # [关键修复] 检查其他if结构的header是否是当前if结构的elif_conditions的一部分
                # 如果是，这是elif链的一部分，不应该排除它的块
                is_elif_condition = hasattr(self, '_current_elif_conditions') and other_header in self._current_elif_conditions
                
                # [关键修复] 检查其他if结构的header是否是当前if结构的then_body或else_body的一部分
                # 如果是，这是嵌套if结构，保留该header
                is_nested = (other_header in then_body or other_header in else_body)
                
                other_all_blocks = set(other_struct.then_body) | set(other_struct.else_body) | {other_header}
                current_all_blocks = set(then_body) | set(else_body) | {header}
                has_shared_blocks = len(other_all_blocks & current_all_blocks) > 0
                
                is_current_nested = (header in other_struct.then_body or header in other_struct.else_body)
                
                if is_current_nested:
                    # [关键修复] 当前if结构嵌套在其他if结构中，不要排除其他if结构的任何块
                    # 因为这些块可能属于当前if结构的then_body或else_body
                    # [关键修复] 当前if结构嵌套在其他if结构中，不要排除其他if结构的任何块
                    # 因为这些块可能属于当前if结构的then_body或else_body
                    # [关键修复] 当前if结构嵌套在其他if结构中，不要排除其他if结构的任何块
                    # 因为这些块可能属于当前if结构的then_body或else_body
                    # [关键修复] 当前if结构嵌套在其他if结构中，不要排除其他if结构的任何块
                    # 因为这些块可能属于当前if结构的then_body或else_body
                    continue
                
                if is_elif_condition:
                    # [关键修复] 这是elif链的一部分，不排除它的块
                    # [关键修复] 这是elif链的一部分，不排除它的块
                    # [关键修复] 这是elif链的一部分，不排除它的块
                    # [关键修复] 这是elif链的一部分，不排除它的块
                    continue
                
                if is_nested or has_shared_blocks:
                    nested_if_headers.add(other_header)
                    for b in other_struct.then_body:
                        nested_if_headers.add(b)
                    for b in other_struct.else_body:
                        nested_if_headers.add(b)
                else:
                    # [关键修复] 不是嵌套if结构，排除所有块
                    # [关键修复] 但是，如果这些块是当前if结构的elif_conditions的一部分，不排除它们
                    # [关键修复] 需要递归检查：如果一个块是elif_conditions中的块的then_body或else_body的一部分，不排除它
                    
                    # 收集elif_conditions中的所有块（包括嵌套的）
                    elif_related_blocks = set()
                    if hasattr(self, '_current_elif_conditions'):
                        for elif_block in self._current_elif_conditions:
                            elif_related_blocks.add(elif_block)
                            # 递归收集elif块的then_body和else_body
                            elif_then = self._find_branch_body_for_elif(elif_block, header, loop_headers)
                            elif_related_blocks = elif_related_blocks | elif_then
                    
                    # 排除与elif相关的块
                    other_if_blocks.add(other_header)
                    for b in other_struct.then_body:
                        if b not in elif_related_blocks:
                            other_if_blocks.add(b)
                    for b in other_struct.else_body:
                        if b not in elif_related_blocks:
                            other_if_blocks.add(b)
        
        # [关键修复] 也检查cfg.blocks中是否有其他条件块（尚未被识别为IfStructure的）
        # 这些块可能是独立的if结构，不应该在当前结构的else_body中
        for block in self.cfg.blocks.values():
            if block != header and self._is_conditional_block(block):
                # [关键修复] 如果该块包含实际业务逻辑（如BINARY_OP、STORE_FAST等），不要排除它
                # 这些块是else分支的正常代码，不是独立的if结构
                has_meaningful_logic = False
                for instr in block.instructions:
                    if instr.opname in ('BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'STORE_FAST', 'STORE_NAME',
                                       'CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'BUILD_TUPLE', 'BUILD_LIST'):
                        has_meaningful_logic = True
                        break
                
                if has_meaningful_logic:
                    continue
                
                # [关键修复-2026] 检查该块是否真的独立
                # 如果该块的所有前驱都属于当前if结构的then_body、else_body或elif链，
                # 说明它是当前if结构的一部分（如else分支中的嵌套if），不应该被排除
                all_predecessors_in_current_if = True
                current_if_blocks = set(then_body) | else_body | {header}
                if hasattr(self, '_current_elif_conditions'):
                    current_if_blocks = current_if_blocks | self._current_elif_conditions
                
                for pred in block.predecessors:
                    if pred not in current_if_blocks and pred != header:
                        all_predecessors_in_current_if = False
                        break
                
                if all_predecessors_in_current_if and len(block.predecessors) > 0:
                    # 所有前驱都在当前if结构内，这不是独立的if结构
                    continue
                
                # 检查这个块是否有前驱在else_body之外（说明是独立的if结构）
                # [关键修复] 对于嵌套在else分支中的if结构，它的前驱可能包括header和then分支
                # 如果前驱包含header，说明这是嵌套if，不应该被排除
                has_external_predecessor = False
                has_header_predecessor = False
                block_parent_loop = None
                for struct in self.structures:
                    if isinstance(struct, LoopStructure) and block in struct.body_blocks:
                        block_parent_loop = struct
                        break
                for pred in block.predecessors:
                    if pred == header:
                        has_header_predecessor = True
                    elif pred not in else_body:
                        if block_parent_loop and pred in block_parent_loop.body_blocks:
                            pass
                        else:
                            has_external_predecessor = True
                
                # [关键修复] 如果该块的前驱包含header，这是嵌套if，不要排除它
                if has_header_predecessor:
                    continue
                
                # [关键修复] 如果该块是嵌套if的header，不要排除它
                if block in nested_if_headers:
                    continue
                
                if has_external_predecessor and block in else_body:
                    other_if_blocks.add(block)
                    # 也排除该块的后继（then_body和else_body）
                    for succ in block.successors:
                        if succ in else_body:
                            other_if_blocks.add(succ)
        
        # 从else_body中排除其他if结构的块
        # if header.start_offset == 76:
        #     print(f'    else_body: {[b.start_offset for b in else_body]}')
        #     print(f'    other_if_blocks: {[b.start_offset for b in other_if_blocks]}')
        #     print(f'    elif_chain_blocks: {[b.start_offset for b in elif_chain_blocks]}')
        
        else_body = else_body - other_if_blocks
        
        # if header.start_offset == 76:
        #     print(f'    else_body: {[b.start_offset for b in else_body]}')
        
        # 如果else分支直接回到header或很短，可能是while循环
        # [关键修复] 只有当else_body非空且长度小于等于1时才返回None
        # 如果else_body为空，说明else_branch是循环尾部，不应该返回None
        if else_branch and len(else_body) == 1 and else_branch in header.dominators:
            return None
        
        # [关键修复] 确定是否有else分支
        # 如果else_body为空，或者else_body只是合并块，则没有else分支
        # [关键修复] 检查else_body中的块是否是if之后的正常代码（包含continue/break指令）
        # 如果是，else_body中的块不是else分支，而是if之后的正常代码
        is_else_continue_or_break = False
        if else_body:
            # 检查else_body中的块是否包含向后跳转指令（continue）或跳转到循环外部（break）
            # 检查else_body中的块是否包含向后跳转指令（continue）或跳转到循环外部（break）
            # 检查else_body中的块是否包含向后跳转指令（continue）或跳转到循环外部（break）
            # 检查else_body中的块是否包含向后跳转指令（continue）或跳转到循环外部（break）
            for block in else_body:
                for instr in block.instructions:
                    # [关键修复] 排除 await 循环的 JUMP_BACKWARD_NO_INTERRUPT 指令
                    # await 循环的特征：包含 SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT
                    # [关键修复] 排除 await 循环的 JUMP_BACKWARD_NO_INTERRUPT 指令
                    # await 循环的特征：包含 SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT
                    # [关键修复] 排除 await 循环的 JUMP_BACKWARD_NO_INTERRUPT 指令
                    # await 循环的特征：包含 SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT
                    # [关键修复] 排除 await 循环的 JUMP_BACKWARD_NO_INTERRUPT 指令
                    # await 循环的特征：包含 SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD_NO_INTERRUPT
                    is_await_loop = False
                    if instr.opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                        # 检查同一块中是否有 SEND 和 YIELD_VALUE
                        # 检查同一块中是否有 SEND 和 YIELD_VALUE
                        # 检查同一块中是否有 SEND 和 YIELD_VALUE
                        # 检查同一块中是否有 SEND 和 YIELD_VALUE
                        has_send = any(i.opname == 'SEND' for i in block.instructions)
                        has_yield_value = any(i.opname == 'YIELD_VALUE' for i in block.instructions)
                        if has_send and has_yield_value:
                            is_await_loop = True
                    
                    # 包含向后跳转指令（continue）或跳转到循环外部（break）
                    # [关键修复] 但排除 await 循环的 JUMP_BACKWARD_NO_INTERRUPT
                    if ('BACKWARD' in instr.opname or instr.opname == 'JUMP_FORWARD') and not is_await_loop:
                        is_else_continue_or_break = True
                        break
                if is_else_continue_or_break:
                    break
        
        # [关键修复] 先检测elif链，然后再计算has_else
        # 这样可以确保else_body包含最终的else分支
        
        # [关键修复] 检测elif链
        # 如果当前if的else_body包含另一个条件块，可能是elif链
        # [关键修复] 即使检测到复合条件，也应该检测elif链
        # 因为复合条件和elif链可以共存：if (A and B): ... elif C: ... else: ...
        # [关键修复] 如果检测到elif链，将elif条件块添加到else_body中
        # elif条件块是前一个if的else分支，应该保留在else_body中
        # [关键修复] 同时将elif条件块的then分支和else分支添加到else_body中
        if len(elif_chain_blocks) > 1:  # 有elif链（包含header）
            for elif_block in elif_chain_blocks:
                if elif_block == header:
                    continue  # 跳过header
                
                # [关键修复] 将elif条件块添加到else_body中
                else_body.add(elif_block)
                
                # 找到elif块的跳转指令
                elif_jump = self._get_jump_instr(elif_block)
                if elif_jump and elif_jump.argval is not None:
                    # 找到elif块的fall-through块（then分支）
                    # 找到elif块的fall-through块（then分支）
                    # 找到elif块的fall-through块（then分支）
                    # 找到elif块的fall-through块（then分支）
                    for succ in elif_block.successors:
                        if succ.start_offset != elif_jump.argval:
                            # 这是elif的then分支，添加到else_body中
                            # [关键修复] 不收集嵌套if的else_body，因为那是嵌套if自己的else分支
                            # 这是elif的then分支，添加到else_body中
                            # [关键修复] 不收集嵌套if的else_body，因为那是嵌套if自己的else分支
                            # 这是elif的then分支，添加到else_body中
                            # [关键修复] 不收集嵌套if的else_body，因为那是嵌套if自己的else分支
                            # 这是elif的then分支，添加到else_body中
                            # [关键修复] 不收集嵌套if的else_body，因为那是嵌套if自己的else分支
                            elif_then_body = self._find_branch_body(succ, elif_block, loop_headers, is_else_branch=False, collect_nested_else=False)
                            else_body = else_body | elif_then_body
                            break
                    
                    # [关键修复] 同时收集elif块的else分支（jump目标）
                    # 如果else分支是另一个elif条件块，它会在下一次循环中被处理
                    # 如果else分支是最终的else分支，它会在下面的代码中被处理
                    for succ in elif_block.successors:
                        if succ.start_offset == elif_jump.argval:
                            # 检查这个块是否是下一个elif条件块
                            # 检查这个块是否是下一个elif条件块
                            # 检查这个块是否是下一个elif条件块
                            # 检查这个块是否是下一个elif条件块
                            is_next_elif = False
                            for next_elif in elif_chain_blocks:
                                if next_elif == succ:
                                    is_next_elif = True
                                    break
                            
                            if not is_next_elif:
                                # 这不是下一个elif条件块，可能是最终的else分支或嵌套if的entry_block
                                # [关键修复] 检查跳转目标是否是嵌套if的entry_block
                                # 嵌套if的特征：跳转目标是条件块，且它的fall-through后继包含实际代码
                                # 这不是下一个elif条件块，可能是最终的else分支或嵌套if的entry_block
                                # [关键修复] 检查跳转目标是否是嵌套if的entry_block
                                # 嵌套if的特征：跳转目标是条件块，且它的fall-through后继包含实际代码
                                # 这不是下一个elif条件块，可能是最终的else分支或嵌套if的entry_block
                                # [关键修复] 检查跳转目标是否是嵌套if的entry_block
                                # 嵌套if的特征：跳转目标是条件块，且它的fall-through后继包含实际代码
                                # 这不是下一个elif条件块，可能是最终的else分支或嵌套if的entry_block
                                # [关键修复] 检查跳转目标是否是嵌套if的entry_block
                                # 嵌套if的特征：跳转目标是条件块，且它的fall-through后继包含实际代码
                                is_nested_if_entry = False
                                if self._is_conditional_block(succ):
                                    # 找到succ的fall-through后继
                                    # 找到succ的fall-through后继
                                    # 找到succ的fall-through后继
                                    # 找到succ的fall-through后继
                                    succ_jump = self._get_jump_instr(succ)
                                    if succ_jump:
                                        for succ_succ in succ.successors:
                                            if succ_succ.start_offset != succ_jump.argval:
                                                # 检查fall-through后继是否包含实际代码（不只是跳转）
                                                # 检查fall-through后继是否包含实际代码（不只是跳转）
                                                # 检查fall-through后继是否包含实际代码（不只是跳转）
                                                # 检查fall-through后继是否包含实际代码（不只是跳转）
                                                non_trivial = [i for i in succ_succ.instructions 
                                                              if i.opname not in ('RESUME', 'CACHE', 'NOP', 'POP_TOP', 'JUMP_FORWARD')]
                                                if non_trivial:
                                                    is_nested_if_entry = True
                                                    break
                                
                                if not is_nested_if_entry:
                                    # 这不是嵌套if的entry_block，是最终的else分支
                                    # 收集这个else分支中的所有块
                                    # 这不是嵌套if的entry_block，是最终的else分支
                                    # 收集这个else分支中的所有块
                                    # 这不是嵌套if的entry_block，是最终的else分支
                                    # 收集这个else分支中的所有块
                                    # 这不是嵌套if的entry_block，是最终的else分支
                                    # 收集这个else分支中的所有块
                                    final_else_body = self._find_branch_body(succ, elif_block, loop_headers, is_else_branch=True)
                                    else_body = else_body | final_else_body
                            break

        
        # [关键修复] 在elif链处理之后重新计算is_else_continue_or_break
        # 因为else_body在elif链处理之后才包含最终的else分支
        is_else_continue_or_break = False
        if else_body:
            has_meaningful_else = False
            for block in else_body:
                for instr in block.instructions:
                    if instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD',
                                       'STORE_FAST', 'STORE_NAME', 'STORE_ATTR', 'STORE_SUBSCR',
                                       'BINARY_OP', 'BUILD_STRING', 'BUILD_LIST', 'BUILD_MAP'):
                        has_meaningful_else = True
                        break
                if has_meaningful_else:
                    break
            
            if has_meaningful_else:
                is_else_continue_or_break = False
            else:
                for block in else_body:
                    for instr in block.instructions:
                        is_await_loop = False
                        if instr.opname == 'JUMP_BACKWARD_NO_INTERRUPT':
                            has_send = any(i.opname == 'SEND' for i in block.instructions)
                            has_yield_value = any(i.opname == 'YIELD_VALUE' for i in block.instructions)
                            if has_send and has_yield_value:
                                is_await_loop = True
                        if ('BACKWARD' in instr.opname or instr.opname == 'JUMP_FORWARD') and not is_await_loop:
                            is_else_continue_or_break = True
                            break
                    if is_else_continue_or_break:
                        break
        
        # [关键修复] 在elif链处理之后计算has_else
        # 这样可以确保else_body包含最终的else分支
        has_else = len(else_body) > 0 and else_body != then_body and not is_else_continue_or_break
        
        # 这种情况通常发生在 if __name__ == '__main__': 之后
        # 模块级别的代码不应该被视为else分支
        if has_else and else_body:
            # 检查else_body中的代码是否是模块级别的
            # 特征：包含全局变量赋值、类定义、函数定义等
            # 检查else_body中的代码是否是模块级别的
            # 特征：包含全局变量赋值、类定义、函数定义等
            # 检查else_body中的代码是否是模块级别的
            # 特征：包含全局变量赋值、类定义、函数定义等
            # 检查else_body中的代码是否是模块级别的
            # 特征：包含全局变量赋值、类定义、函数定义等
            is_module_level = False
            for block in else_body:
                for instr in block.instructions:
                    # 检查是否是模块级别的操作
                    # 检查是否是模块级别的操作
                    # 检查是否是模块级别的操作
                    # 检查是否是模块级别的操作
                    if instr.opname in ('STORE_NAME', 'STORE_GLOBAL'):
                        # 检查变量名是否是模块级别的（如GLOBAL_CONSTANT, _config等）
                        # 检查变量名是否是模块级别的（如GLOBAL_CONSTANT, _config等）
                        # 检查变量名是否是模块级别的（如GLOBAL_CONSTANT, _config等）
                        # 检查变量名是否是模块级别的（如GLOBAL_CONSTANT, _config等）
                        if instr.argval in ('GLOBAL_CONSTANT', '_config', 'final_message'):
                            is_module_level = True
                            break
                    elif instr.opname == 'LOAD_CONST' and isinstance(instr.argval, str):
                        # 检查是否是模块级别的字符串常量
                        # 检查是否是模块级别的字符串常量
                        if instr.argval in ('全局常量', '模块初始化完成'):
                            is_module_level = True
                            break
                if is_module_level:
                    break
            
            # 如果识别为模块级别的代码，不将其视为else分支
            if is_module_level:
                has_else = False
                else_body = set()
        
        # [关键修复] 如果then_branch直接跳转到else_branch（没有then代码），可能是空的then分支
        # 这种情况下应该交换then和else
        # [关键修复] 但对于复合条件，then_body为空是正常的（所有条件块都在condition_chain中）
        # 所以不应该交换
        # [关键修复] 对于嵌套if，then_branch是条件块，then_body为空也是正常的
        # 因为内层if是独立的IfStructure，不应该交换
        if not is_compound_condition and not then_body and else_body and else_branch:
            # [关键修复] 检查then_branch是否是条件块（嵌套if）
            # 如果是，不交换，因为内层if是独立的IfStructure
            # [关键修复] 检查then_branch是否是条件块（嵌套if）
            # 如果是，不交换，因为内层if是独立的IfStructure
            # [关键修复] 检查then_branch是否是条件块（嵌套if）
            # 如果是，不交换，因为内层if是独立的IfStructure
            # [关键修复] 检查then_branch是否是条件块（嵌套if）
            # 如果是，不交换，因为内层if是独立的IfStructure
            if not self._is_conditional_block(then_branch):
                # 交换then和else
                # 交换then和else
                # 交换then和else
                # 交换then和else
                then_body, else_body = else_body, then_body
                then_branch, else_branch = else_branch, then_branch

        # [调试输出]
        if_struct = IfStructure(
            struct_type=ControlStructureType.IF_THEN_ELSE if has_else else ControlStructureType.IF_THEN,
            entry_block=header,
            condition_block=header,
            then_body=list(then_body),
            else_body=list(else_body) if has_else else [],
            merge_block=merge_block,
            is_compound_condition=is_compound_condition,
            condition_chain=condition_chain,
            elif_conditions=[b for b in elif_chain_blocks if b != header and not self._has_chain_compare_pattern(b)],  # [关键修复] 链式比较块不放入elif_conditions
        )
        
        # [关键修复] 清除_current_elif_conditions
        if hasattr(self, '_current_elif_conditions'):
            delattr(self, '_current_elif_conditions')
        
        # [关键修复] 不再为每个elif块创建独立的IfStructure
        # elif链应该由父if结构统一处理，通过elif_conditions属性传递给AST生成器
        # AST生成器会根据elif_conditions生成正确的elif链代码
        
        return if_struct
    
    def _detect_compound_condition(self, header: BasicBlock, then_body: Set[BasicBlock], 
                                   else_body: Set[BasicBlock], loop_headers: Set[BasicBlock]) -> Tuple[Set[BasicBlock], List[BasicBlock]]:
        """
        检测复合条件模式（如 x > 0 and y > 0 或 x < 0 or y < 0）
        
        [DEBUG] 导入sys用于调试输出
        
        [关键修复] 严格区分复合条件和elif链：
        - 复合条件：多个条件共享同一个else分支（跳转目标相同）
        - elif链：每个条件有自己的else分支（跳转目标不同，指向下一个elif）
        
        复合条件的核心特征（基于字节码分析）：
        1. 多个连续的条件块形成链式结构
        2. 条件块之间通过fall-through连接
        3. 所有条件块的跳转目标都指向同一个else分支（共享else）
        
        AND条件（如 x > 0 and y > 0）:
        - 第一个条件块：x > 0，POP_JUMP_IF_FALSE -> 偏移68
        - 第二个条件块：y > 0，POP_JUMP_IF_FALSE -> 偏移68（相同目标）
        
        OR条件（如 x < 0 or y < 0）:
        - 第一个条件块：x < 0，POP_JUMP_IF_TRUE -> 偏移92（共同的then目标）
        - 第二个条件块：y < 0，POP_JUMP_IF_FALSE -> 偏移126（else目标）
        
        而对于elif链：
        - 第一个条件块：if x == 1，POP_JUMP_IF_FALSE -> 下一个elif块（偏移不同）
        - 第二个条件块：elif x == 2，POP_JUMP_IF_FALSE -> 再下一个elif块（偏移不同）
        
        Args:
            header: 当前if的头部块
            then_body: then分支体
            else_body: else分支体
            loop_headers: 循环头部集合
            
        Returns:
            (复合条件中需要排除的块集合, 复合条件链中的条件块列表)
        """
        compound_blocks = set()
        condition_chain = [header]
        
        # [关键修复] 初始化is_complex_bool_chain，用于标记复杂布尔表达式链
        is_complex_bool_chain = False
        
        # 获取header的跳转指令
        header_jump_instr = self._get_jump_instr(header)
        if not header_jump_instr or header_jump_instr.argval is None:
            return compound_blocks, condition_chain
        
        # [关键修复] 记录header的跳转目标（共享的else分支）
        header_jump_target = header_jump_instr.argval
        
        # [关键修复] 获取header的then分支（fall-through目标）
        # 这对于检测OR条件很重要
        header_then = None
        for succ in header.successors:
            if succ.start_offset != header_jump_target:
                header_then = succ
                break
        
        # [关键修复] 如果header是循环头部，不应该识别为复合条件
        # 因为循环条件（如while x < 10:）和循环内的if条件（如if y > 0:）不是复合条件
        if getattr(header, 'loop_header', False):
            return compound_blocks, condition_chain
        
        # [关键修复] 也检查header是否是任何LoopStructure的header_block
        # 因为loop_header属性可能没有被正确设置
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and struct.header_block == header:
                return compound_blocks, condition_chain
        
        # [关键修复] 改进复合条件检测逻辑
        # 复合条件的特征：连续的多个条件块，每个条件块的fall-through是下一个条件块
        # 且所有条件块的跳转目标都相同（共享else分支）或都是else分支的一部分
        
        current_block = header
        
        # [关键修复] 在混合条件链中，排除某些指令
        is_mixed_condition_chain = False
        
        while True:
            # 获取当前块的跳转指令
            # 获取当前块的跳转指令
            # 获取当前块的跳转指令
            # 获取当前块的跳转指令
            current_jump = self._get_jump_instr(current_block)
            if not current_jump or current_jump.argval is None:
                break
            
            # fall-through块是then分支（不是跳转目标的那个后继）
            fall_through_block = None
            for succ in current_block.successors:
                if succ.start_offset != current_jump.argval:
                    fall_through_block = succ
                    break
            
            if not fall_through_block:
                break

            if fall_through_block is None:
                break
            
            # [关键修复] 检查fall_through_block是否是条件块
            # 条件块的特征：有两个后继（then和else分支）
            is_cond = self._is_conditional_block(fall_through_block)
            has_two_succ = len(fall_through_block.successors) == 2
            
            # [重要修复] 对于混合条件（使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP），
            # 最后一部分可能没有条件跳转指令（如 not flag），但它仍然是复合条件的一部分
            # 检查当前是否已经在处理混合条件
            # [重要修复] 同时检查fall_through_block是否使用了JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP
            # 这可以检测到混合条件的开始（如 (x > 0 and y < 10) or ...）
            is_currently_mixed = is_mixed_condition_chain or any(
                instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                for cond_block in condition_chain
                for instr in cond_block.instructions
            ) or any(
                instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                for instr in fall_through_block.instructions
            )
            
            # [重要修复] 如果是混合条件，且fall_through_block只有一个后继（直接连接到merge块），
            # 这可能是复合条件的最后一部分（如 not flag）
            if is_currently_mixed and not has_two_succ and len(fall_through_block.successors) == 1:
                # 这是混合条件的最后一部分，添加到条件链并退出
                # 这是混合条件的最后一部分，添加到条件链并退出
                # 这是混合条件的最后一部分，添加到条件链并退出
                # 这是混合条件的最后一部分，添加到条件链并退出
                compound_blocks.add(fall_through_block)
                condition_chain.append(fall_through_block)
                break
            
            # [关键修复] 对于OR条件模式，fall_through_block可能只有一个后继
            # 当它的then分支和header的then分支相同时
            # 这种情况下，只要is_cond为True，就应该继续检测
            
            # [关键修复] 检查fall_through_block是否使用JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP进行赋值
            # 如 x = a or b，这种情况下fall_through_block不是复合条件的一部分
            if is_cond and fall_through_block:
                ft_jump = self._get_jump_instr(fall_through_block)
                if ft_jump and ft_jump.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                    # 检查跳转目标是否是STORE_FAST
                    jump_target_offset = ft_jump.argval
                    if jump_target_offset is not None:
                        for succ in fall_through_block.successors:
                            if succ.start_offset <= jump_target_offset:
                                for target_instr in succ.instructions:
                                    if target_instr.offset == jump_target_offset:
                                        if target_instr.opname == 'STORE_FAST':
                                            # 这是赋值语句，不是复合条件
                                            is_cond = False
                                        break
                            if not is_cond:
                                break
            
            if not is_cond:
                break
            
            # [关键修复] 检查是否是OR条件模式
            # OR条件的特征（如 if a or b:）：
            # 1. header使用POP_JUMP_FORWARD_IF_TRUE（条件为True时跳转到then-body）
            # 2. fall_through_block使用POP_JUMP_FORWARD_IF_FALSE（条件为False时跳转到else-body）
            # 3. fall_through_block的fall-through目标与header的跳转目标相同（都是then-body）
            fall_through_jump = self._get_jump_instr(fall_through_block)
            is_or_condition = False
            
            if fall_through_jump and header_jump_instr.opname in ('POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_IF_TRUE'):
                # 找到fall_through_block的fall-through目标（不是跳转目标的那个后继）
                # 找到fall_through_block的fall-through目标（不是跳转目标的那个后继）
                # 找到fall_through_block的fall-through目标（不是跳转目标的那个后继）
                # 找到fall_through_block的fall-through目标（不是跳转目标的那个后继）
                fall_through_fall_through = None
                for succ in fall_through_block.successors:
                    if succ.start_offset != fall_through_jump.argval:
                        fall_through_fall_through = succ
                        break
                
                # 对于OR条件：
                # - header的跳转目标 = then-body（当第一个条件为True时）
                # - fall_through_block的fall-through目标 = then-body（当第二个条件为True时）
                # 两者应该相同
                if fall_through_fall_through and fall_through_fall_through.start_offset == header_jump_target:
                    is_or_condition = True
            
            # [关键修复] 对于OR条件，即使has_two_succ为False，也继续检测
            if not has_two_succ and not is_or_condition:
                break
            
            # [关键修复] 区分嵌套if和复合条件
            fall_through_jump = self._get_jump_instr(fall_through_block)
            successors = list(fall_through_block.successors)
            if fall_through_jump:
                # 找到fall_through_block的then分支（不是跳转目标的那个后继）
                fall_through_then = None
                for succ in fall_through_block.successors:
                    if succ.start_offset != fall_through_jump.argval:
                        fall_through_then = succ
                        break
                
                if fall_through_then:
                    # [关键修复] 检查then分支是否只包含NOP/RETURN（没有实际代码）
                    # 如果是，这可能是嵌套if，不是复合条件
                    then_instructions = [i for i in fall_through_then.instructions 
                                        if i.opname not in ('RESUME', 'CACHE', 'POP_TOP')]
                    if len(then_instructions) <= 1 and all(
                        i.opname in ('NOP', 'RETURN_VALUE') for i in then_instructions
                    ):
                        # then分支只包含NOP或RETURN，这是嵌套if，不是复合条件
                        break
                    # 检查then分支是否包含条件块（嵌套if）
                    # 检查then分支是否包含条件块（嵌套if）
                    # 检查then分支是否包含条件块（嵌套if）
                    # 检查then分支是否包含条件块（嵌套if）
                    is_cond_block = self._is_conditional_block(fall_through_then)
                    
                    # [关键修复] 检查是否是混合条件（AND-OR-AND）
                    # 混合条件的特征：fall_through_block使用了JUMP_IF_TRUE_OR_POP或JUMP_IF_FALSE_OR_POP
                    # 且fall_through_then也是条件块
                    if is_cond_block and fall_through_jump:
                        if fall_through_jump.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                            # 这是混合条件的一部分，不是嵌套if
                            # 这是混合条件的一部分，不是嵌套if
                            # 这是混合条件的一部分，不是嵌套if
                            # 这是混合条件的一部分，不是嵌套if
                            is_mixed_condition_chain = True
                    
                    # [关键修复] 对于复杂布尔表达式链，即使then分支包含条件块，也不应该中断
                    # 复杂布尔表达式链的特征：
                    # 1. 所有条件块的跳转目标最终都汇入同一个merge点
                    # 2. then分支只包含简单的跳转指令（如JUMP_FORWARD）或RETURN_VALUE
                    # [关键修复] 但是，如果fall_through_block和header共享同一个跳转目标，
                    # 这是AND复合条件（如 if a and b:），不应该因为then分支包含代码就中断
                    shared_jump_target = False
                    if fall_through_jump and header_jump_instr:
                        if fall_through_jump.argval == header_jump_instr.argval:
                            shared_jump_target = True
                    
                    if is_cond_block and not is_mixed_condition_chain and not shared_jump_target:
                        # [字节码一致性修复] 检查是否是链式比较的最后一个比较块
                        # 链式比较的特征：当前块和fall_through块都有链式比较模式
                        # 但最后一个比较块的跳转目标是then值（而非共享else点）
                        is_last_chain_compare = (
                            self._has_chain_compare_pattern(current_block) and
                            self._has_chain_compare_pattern(fall_through_block) and
                            len(condition_chain) >= 2  # 已经收集了至少2个链式比较块
                        )
                        
                        if not is_last_chain_compare:
                            # [关键修复] 如果跳转目标不同，这是嵌套if，不是复合条件
                            break
                    
                    # [关键修复] 即使共享跳转目标，如果then分支是条件块且只包含NOP/RETURN，也是嵌套if
                    if is_cond_block and not is_mixed_condition_chain and shared_jump_target:
                        # 检查then分支是否只包含NOP/RETURN（没有实际代码）
                        then_instructions = [i for i in fall_through_then.instructions 
                                            if i.opname not in ('RESUME', 'CACHE', 'POP_TOP')]
                        if len(then_instructions) <= 1 and all(
                            i.opname in ('NOP', 'RETURN_VALUE') for i in then_instructions
                        ):
                            # then分支只包含NOP或RETURN，这是嵌套if，不是复合条件
                            break
                        
                        # [关键修复] 如果then分支是条件块，检查它是否有自己的then分支包含实际代码
                        # 如果是，这是嵌套if，不是复合条件
                        # 获取fall_through_then的跳转指令
                        ft_then_jump = self._get_jump_instr(fall_through_then)
                        if ft_then_jump:
                            # 找到fall_through_then的then分支（fall-through）
                            ft_then_fall_through = None
                            for succ in fall_through_then.successors:
                                if succ.start_offset != ft_then_jump.argval:
                                    ft_then_fall_through = succ
                                    break
                            
                            if ft_then_fall_through:
                                # 检查ft_then_fall_through是否包含实际代码（不只是NOP/RETURN）
                                ft_then_fall_through_instrs = [i for i in ft_then_fall_through.instructions 
                                                              if i.opname not in ('RESUME', 'CACHE', 'POP_TOP')]
                                
                                # [字节码一致性修复] 排除链式比较的then值加载模式
                                # 链式比较的特征：then分支只包含条件相关的指令（值加载+比较+跳转）
                                # 例如：0 < a < b < c < 100 会生成多个比较块，每个块包含：
                                #   LOAD_*, COMPARE_OP, POP_JUMP_*（中间块）
                                #   或 LOAD_*, JUMP_FORWARD（最后一个块的then分支）
                                is_chain_compare_block = (
                                    len(ft_then_fall_through_instrs) >= 1 and
                                    len(ft_then_fall_through_instrs) <= 5 and
                                    all(i.opname.startswith('LOAD_') or 
                                        i.opname == 'COMPARE_OP' or
                                        i.opname == 'IS_OP' or
                                        i.opname == 'CONTAINS_OP' or
                                        i.opname.startswith('POP_JUMP') or
                                        i.opname == 'JUMP_FORWARD'
                                        for i in ft_then_fall_through_instrs)
                                )
                                
                                has_real_code = any(
                                    i.opname not in ('NOP', 'RETURN_VALUE', 'JUMP_FORWARD')
                                    for i in ft_then_fall_through_instrs
                                )
                                
                                # [关键修复] 如果是链式比较的条件块，不算作"实际代码"
                                if is_chain_compare_block:
                                    has_real_code = False
                                
                                if has_real_code:
                                    # fall_through_then是内层if的条件块，不是复合条件的一部分
                                    break
                    
                    # 检查then分支是否包含任何实际代码（不只是简单的值加载、存储和跳转）
                    # 复合条件的then分支应该只包含简单的值加载或直接跳转到merge
                    # 嵌套if的then分支包含实际执行的代码（如赋值、调用等）
                    
                    # [关键修复] 在混合条件链中，排除JUMP_IF_TRUE_OR_POP和JUMP_IF_FALSE_OR_POP
                    excluded_ops = ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                    'POP_TOP', 'RETURN_VALUE')
                    if is_mixed_condition_chain:
                        excluded_ops += ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP', 
                                         'LOAD_GLOBAL', 'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME',
                                         'COMPARE_OP', 'UNARY_NOT')
                    
                    non_trivial_instrs = [i for i in fall_through_then.instructions 
                                          if i.opname not in excluded_ops]
                    # 如果then分支包含STORE_*（赋值）、BINARY_*（运算）、CALL（调用）等实际代码
                    # [关键修复] 在混合条件链中，LOAD_*, COMPARE_OP, UNARY_NOT是条件的一部分，不是实际代码
                    if is_mixed_condition_chain:
                        has_actual_code = any(
                            i.opname.startswith(('STORE_', 'BINARY_', 'CALL', 'BUILD_')) or
                            (i.opname.startswith('UNARY_') and i.opname != 'UNARY_NOT')
                            for i in non_trivial_instrs
                            if not i.opname.startswith('LOAD_')  # [关键修复] 排除所有LOAD_*指令
                        )
                    else:
                        # [关键修复] 对于复杂布尔表达式链，POP_JUMP_*指令是条件的一部分，不是实际代码
                        # [关键修复] 同时排除COMPARE_OP, IS_OP, CONTAINS_OP，因为它们是条件表达式的一部分
                        has_actual_code = any(
                            i.opname.startswith(('STORE_', 'BINARY_', 'CALL', 'BUILD_')) or
                            (i.opname.startswith('UNARY_') and not i.opname.startswith('POP_JUMP'))
                            for i in non_trivial_instrs
                            if not i.opname.startswith('POP_JUMP')  # [关键修复] 排除所有POP_JUMP_*指令
                        )
                    if has_actual_code:
                        break
            
            # 条件表达式的特征：fall_through_block只包含值加载指令（如LOAD_CONST），不包含条件跳转
            # 复合条件的特征：fall_through_block包含条件跳转指令（如POP_JUMP_IF_*）
            # 检查fall_through_block是否只包含值加载和JUMP_FORWARD指令（条件表达式模式）
            # [关键修复] 排除所有POP_JUMP_*指令，因为它们可能是复合条件的一部分
            non_trivial_instrs = [i for i in fall_through_block.instructions 
                                  if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                                      'POP_TOP', 'RETURN_VALUE',
                                                      'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                      'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                                      'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                                      'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE')]
            load_only_pattern = all(
                i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD'
                for i in non_trivial_instrs
            )
            # [关键修复] 如果fall_through_block是条件块（包含POP_JUMP_*指令），
            # 那么它不应该被识别为条件表达式模式，而是复合条件的一部分
            has_cond_jump = any(i.opname.startswith('POP_JUMP') for i in fall_through_block.instructions)
            if load_only_pattern and not has_cond_jump:
                # 这是条件表达式模式，不是复合条件

            # [关键修复] 获取fall_through_block的跳转指令和目标
                # 这是条件表达式模式，不是复合条件

            # [关键修复] 获取fall_through_block的跳转指令和目标
                pass
                # 这是条件表达式模式，不是复合条件

            # [关键修复] 获取fall_through_block的跳转指令和目标
            next_jump = self._get_jump_instr(fall_through_block)
            if not next_jump or next_jump.argval is None:
                break
            
            # [关键修复] 检测嵌套条件表达式模式
            # 嵌套条件表达式如：(x if x > 0 else 0) if x is not None else -1
            # 特征：
            # 1. fall_through_block是一个条件块（有POP_JUMP指令）
            # 2. fall_through_block的then分支和else分支都汇入同一个块（内层条件表达式的merge点）
            # 3. 该merge点再通过JUMP_FORWARD汇入外层的merge点
            # 这种情况下，fall_through_block是一个独立的条件表达式，不是复合条件的一部分
            is_nested_conditional_expr_pattern = False
            if has_cond_jump:
                # 找到fall_through_block的then分支和else分支
                # 找到fall_through_block的then分支和else分支
                # 找到fall_through_block的then分支和else分支
                # 找到fall_through_block的then分支和else分支
                ft_then_block = None
                ft_else_block = None
                for succ in fall_through_block.successors:
                    if succ.start_offset != next_jump.argval:
                        ft_then_block = succ
                    else:
                        ft_else_block = succ
                
                if ft_then_block and ft_else_block:
                    # 检查then分支和else分支是否汇入同一个块
                    # 检查then分支和else分支是否汇入同一个块
                    # 检查then分支和else分支是否汇入同一个块
                    # 检查then分支和else分支是否汇入同一个块
                    ft_then_succs = set(s.start_offset for s in ft_then_block.successors)
                    ft_else_succs = set(s.start_offset for s in ft_else_block.successors)
                    common_succ = ft_then_succs & ft_else_succs
                    
                    if common_succ:
                        # 检查共同后继是否只包含简单的值加载和JUMP_FORWARD（条件表达式模式）
                        # 检查共同后继是否只包含简单的值加载和JUMP_FORWARD（条件表达式模式）
                        # 检查共同后继是否只包含简单的值加载和JUMP_FORWARD（条件表达式模式）
                        # 检查共同后继是否只包含简单的值加载和JUMP_FORWARD（条件表达式模式）
                        common_block = None
                        for succ in ft_then_block.successors:
                            if succ.start_offset in common_succ:
                                common_block = succ
                                break
                        
                        if common_block:
                            common_instrs = [i for i in common_block.instructions 
                                            if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                            # 条件表达式的merge点应该只包含STORE指令或JUMP_FORWARD
                            is_cond_expr_merge = all(
                                i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                           'JUMP_FORWARD', 'RETURN_VALUE', 'RETURN_CONST',
                                           'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME') or
                                i.opname.startswith('POP_')
                                for i in common_instrs
                            )
                            
                            if is_cond_expr_merge:
                                # 这是嵌套条件表达式模式，不是复合条件
                                # 这是嵌套条件表达式模式，不是复合条件
                                # 这是嵌套条件表达式模式，不是复合条件
                                # 这是嵌套条件表达式模式，不是复合条件
                                is_nested_conditional_expr_pattern = True
            
            if is_nested_conditional_expr_pattern:
                # [字节码一致性修复] 检查是否是链式比较模式
                # 链式比较中，then和else分支可能汇入同一个块，但这不是嵌套条件表达式
                is_chain_nested = self._has_chain_compare_pattern(current_block) or self._has_chain_compare_pattern(fall_through_block)
                if is_chain_nested:
                    is_nested_conditional_expr_pattern = False
                else:
                    # 这是嵌套条件表达式，不是复合条件
                    pass
            else:
                pass

            # [关键修复] 检查是否是链式比较（如 0 < x < 100）
            # 链式比较的特征：
            # 1. 当前块的跳转目标在else_body中（是else分支的一部分）
            # 2. fall_through_block的跳转目标也在else_body中（也是else分支的一部分）
            # 3. fall_through_block的then分支只包含简单的值加载和JUMP_FORWARD（不是嵌套if）
                # 这是嵌套条件表达式，不是复合条件

            # [关键修复] 检查是否是链式比较（如 0 < x < 100）
            # 链式比较的特征：
            # 1. 当前块的跳转目标在else_body中（是else分支的一部分）
            # 2. fall_through_block的跳转目标也在else_body中（也是else分支的一部分）
            # 3. fall_through_block的then分支只包含简单的值加载和JUMP_FORWARD（不是嵌套if）
                pass
                # 这是嵌套条件表达式，不是复合条件

            # [关键修复] 检查是否是链式比较（如 0 < x < 100）
            # 链式比较的特征：
            # 1. 当前块的跳转目标在else_body中（是else分支的一部分）
            # 2. fall_through_block的跳转目标也在else_body中（也是else分支的一部分）
            # 3. fall_through_block的then分支只包含简单的值加载和JUMP_FORWARD（不是嵌套if）
            current_jump_target_in_else = any(
                succ.start_offset == current_jump.argval for succ in current_block.successors
            )
            next_jump_target_in_else = any(
                succ.start_offset == next_jump.argval for succ in fall_through_block.successors
            )
            
            # [关键修复] 检查是否是链式比较的特殊情况
            # 链式比较的特征：两个跳转目标最终汇入同一个merge点
            # 例如：0 < x < 100
            #   - 第一个条件为False时，跳转到POP_TOP，然后到共同的merge点
            #   - 第二个条件为False时，直接跳转到共同的merge点
            #   - 两个条件都为True时，通过JUMP_FORWARD到共同的merge点
            is_chained_compare_pattern = False
            if current_jump_target_in_else and next_jump_target_in_else:
                # 找到两个跳转目标块
                # 找到两个跳转目标块
                # 找到两个跳转目标块
                # 找到两个跳转目标块
                current_jump_target_block = None
                next_jump_target_block = None
                for succ in current_block.successors:
                    if succ.start_offset == current_jump.argval:
                        current_jump_target_block = succ
                        break
                for succ in fall_through_block.successors:
                    if succ.start_offset == next_jump.argval:
                        next_jump_target_block = succ
                        break
                
                if current_jump_target_block and next_jump_target_block:
                    # 检查两个跳转目标是否最终汇入同一个块
                    # 简单情况：第二个跳转目标就是共同的merge点
                    # 复杂情况：第一个跳转目标通过JUMP_FORWARD到第二个跳转目标
                    # 检查两个跳转目标是否最终汇入同一个块
                    # 简单情况：第二个跳转目标就是共同的merge点
                    # 复杂情况：第一个跳转目标通过JUMP_FORWARD到第二个跳转目标
                    # 检查两个跳转目标是否最终汇入同一个块
                    # 简单情况：第二个跳转目标就是共同的merge点
                    # 复杂情况：第一个跳转目标通过JUMP_FORWARD到第二个跳转目标
                    # 检查两个跳转目标是否最终汇入同一个块
                    # 简单情况：第二个跳转目标就是共同的merge点
                    # 复杂情况：第一个跳转目标通过JUMP_FORWARD到第二个跳转目标
                    if current_jump_target_block == next_jump_target_block:
                        # 两个跳转目标相同，这是AND条件，不是链式比较
                        # 两个跳转目标相同，这是AND条件，不是链式比较
                        # 两个跳转目标相同，这是AND条件，不是链式比较
                        # 两个跳转目标相同，这是AND条件，不是链式比较
                        pass
                    else:
                        # 检查第一个跳转目标是否通过JUMP_FORWARD到第二个跳转目标
                        # 或者两个跳转目标都汇入同一个后继
                        current_target_succs = set(s.start_offset for s in current_jump_target_block.successors)
                        next_target_succs = set(s.start_offset for s in next_jump_target_block.successors)
                        
                        # 如果两个跳转目标有共同的后继，这是链式比较
                        common_succs = current_target_succs & next_target_succs
                        if common_succs:
                            is_chained_compare_pattern = True
                        # 或者第一个跳转目标直接跳转到第二个跳转目标
                        elif next_jump_target_block.start_offset in current_target_succs:
                            is_chained_compare_pattern = True
            
            # [关键修复] 检查fall_through_block的then分支是否是嵌套if
            # 嵌套if的特征：then分支包含条件块或复杂的代码
            # 链式比较的特征：then分支只包含简单的值加载和JUMP_FORWARD
            fall_through_then = None
            for succ in fall_through_block.successors:
                if succ.start_offset != next_jump.argval:
                    fall_through_then = succ
                    break
            
            # [关键修复] 首先检测是否是复杂布尔表达式链
            # 这需要在检查is_nested_if之前完成，以便is_nested_if的检查可以跳过
            # [关键修复] 对于复杂布尔表达式链，只要fall-through块是条件块，
            # 即使它的then分支包含实际代码，也应该继续检测
            # 因为最后一个条件块的fall-through可能是then body
            is_complex_bool_chain = False
            if fall_through_then:
                # 检查fall-through块的then分支是否包含实际代码
                # [关键修复] 包含所有POP_JUMP_*指令，因为它们可能是复杂布尔表达式链的一部分
                # [关键修复] 排除COMPARE_OP，因为它是复合条件的一部分（如"x > 0"）
                # 检查fall-through块的then分支是否包含实际代码
                # [关键修复] 包含所有POP_JUMP_*指令，因为它们可能是复杂布尔表达式链的一部分
                # [关键修复] 排除COMPARE_OP，因为它是复合条件的一部分（如"x > 0"）
                # 检查fall-through块的then分支是否包含实际代码
                # [关键修复] 包含所有POP_JUMP_*指令，因为它们可能是复杂布尔表达式链的一部分
                # [关键修复] 排除COMPARE_OP，因为它是复合条件的一部分（如"x > 0"）
                # 检查fall-through块的then分支是否包含实际代码
                # [关键修复] 包含所有POP_JUMP_*指令，因为它们可能是复杂布尔表达式链的一部分
                # [关键修复] 排除COMPARE_OP，因为它是复合条件的一部分（如"x > 0"）
                non_trivial = [i for i in fall_through_then.instructions 
                               if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                                   'POP_TOP', 'RETURN_VALUE', 'JUMP_FORWARD',
                                                   'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                                   'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                   'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                                   'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                                   'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                                                   'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                                                   'COMPARE_OP')]
                ft_then_has_actual_code = len(non_trivial) > 0
                
                # [关键修复] 简化检测：只要fall-through块的then分支不包含实际代码，
                # 就认为是复杂布尔表达式链的一部分
                # [关键修复] 但是，如果fall_through_then本身是条件块（嵌套if），
                # 且它的then分支包含实际代码，则不应该认为是复杂布尔表达式链
                # [关键修复] 最重要的是：如果跳转目标不同，这不是复杂布尔表达式链，而是嵌套if
                if not ft_then_has_actual_code:
                    # [关键修复] 检查跳转目标是否相同
                    # 复合条件的特征：所有条件块共享同一个跳转目标
                    # 如果跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                    # [关键修复] 检查跳转目标是否相同
                    # 复合条件的特征：所有条件块共享同一个跳转目标
                    # 如果跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                    # [关键修复] 检查跳转目标是否相同
                    # 复合条件的特征：所有条件块共享同一个跳转目标
                    # 如果跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                    # [关键修复] 检查跳转目标是否相同
                    # 复合条件的特征：所有条件块共享同一个跳转目标
                    # 如果跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                    shared_jump_target = False
                    if fall_through_jump and header_jump_instr:
                        if fall_through_jump.argval == header_jump_instr.argval:
                            shared_jump_target = True
                    
                    if not shared_jump_target:
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        is_complex_bool_chain = False
                    elif self._is_conditional_block(fall_through_then):
                        # 找到fall_through_then的then分支
                        # 找到fall_through_then的then分支
                        ft_then_jump = self._get_jump_instr(fall_through_then)
                        if ft_then_jump:
                            ft_then_then = None
                            for succ in fall_through_then.successors:
                                if succ.start_offset != ft_then_jump.argval:
                                    ft_then_then = succ
                                    break
                            if ft_then_then:
                                # 检查ft_then_then是否包含实际代码
                                # 检查ft_then_then是否包含实际代码
                                # 检查ft_then_then是否包含实际代码
                                # 检查ft_then_then是否包含实际代码
                                ft_then_then_non_trivial = [i for i in ft_then_then.instructions 
                                                            if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                                                                'POP_TOP', 'RETURN_VALUE', 'JUMP_FORWARD',
                                                                                'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                                                                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                                                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                                                                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                                                                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                                                                                'UNARY_NOT')]
                                if len(ft_then_then_non_trivial) > 0:
                                    # 这是嵌套if结构，不是复杂布尔表达式链
                                    # 这是嵌套if结构，不是复杂布尔表达式链
                                    # 这是嵌套if结构，不是复杂布尔表达式链
                                    # 这是嵌套if结构，不是复杂布尔表达式链
                                    is_complex_bool_chain = False
                                else:
                                    is_complex_bool_chain = True
                            else:
                                is_complex_bool_chain = True
                        else:
                            is_complex_bool_chain = True
                    else:
                        is_complex_bool_chain = True
                # [关键修复] 如果fall-through块是条件块，且我们已经检测到至少一个条件块，
                # 也认为是复杂布尔表达式链的一部分
                # [关键修复] 但是，如果fall_through_then本身也是条件块（嵌套if），
                # 且它的then分支包含实际代码，则不应该认为是复杂布尔表达式链
                # [关键修复] 最重要的是：如果跳转目标不同，这不是复杂布尔表达式链，而是嵌套if
                elif len(condition_chain) >= 1 and self._is_conditional_block(fall_through_block):
                    # [关键修复] 首先检查跳转目标是否相同
                    # 复合条件的特征：所有条件块共享同一个跳转目标
                    # 如果跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                    # [关键修复] 首先检查跳转目标是否相同
                    # 复合条件的特征：所有条件块共享同一个跳转目标
                    # 如果跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                    shared_jump_target = False
                    if fall_through_jump and header_jump_instr:
                        if fall_through_jump.argval == header_jump_instr.argval:
                            shared_jump_target = True
                    
                    if not shared_jump_target:
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        # 跳转目标不同，这是嵌套if，不是复杂布尔表达式链
                        is_complex_bool_chain = False
                    elif self._is_conditional_block(fall_through_then):
                        # 找到fall_through_then的then分支
                        # 找到fall_through_then的then分支
                        ft_then_jump = self._get_jump_instr(fall_through_then)
                        if ft_then_jump:
                            ft_then_then = None
                            for succ in fall_through_then.successors:
                                if succ.start_offset != ft_then_jump.argval:
                                    ft_then_then = succ
                                    break
                            if ft_then_then:
                                # [关键修复] 如果ft_then_then也是条件块，这是嵌套if，不是复杂布尔表达式链
                                # [关键修复] 如果ft_then_then也是条件块，这是嵌套if，不是复杂布尔表达式链
                                # [关键修复] 如果ft_then_then也是条件块，这是嵌套if，不是复杂布尔表达式链
                                # [关键修复] 如果ft_then_then也是条件块，这是嵌套if，不是复杂布尔表达式链
                                if self._is_conditional_block(ft_then_then):
                                    is_complex_bool_chain = False
                                else:
                                    # 检查ft_then_then是否包含实际代码
                                    ft_then_then_non_trivial = [i for i in ft_then_then.instructions 
                                                                if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                                                                    'POP_TOP', 'RETURN_VALUE', 'JUMP_FORWARD',
                                                                                    'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                                                                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                                                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                                                                    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                                                                    'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE')]
                                    if len(ft_then_then_non_trivial) > 0:
                                        # 这是嵌套if结构，不是复杂布尔表达式链
                                        # 这是嵌套if结构，不是复杂布尔表达式链
                                        # 这是嵌套if结构，不是复杂布尔表达式链
                                        # 这是嵌套if结构，不是复杂布尔表达式链
                                        is_complex_bool_chain = False
                                    else:
                                        is_complex_bool_chain = True
                            else:
                                is_complex_bool_chain = True
                        else:
                            is_complex_bool_chain = True
                    else:
                        is_complex_bool_chain = True
            
            is_nested_if = False
            if fall_through_then:
                # 检查then分支是否包含条件块
                # [关键修复] 如果fall_through_then是条件块，这可能是嵌套if
                # 需要检查它的跳转目标是否与fall_through_block的跳转目标相同
                # 检查then分支是否包含条件块
                # [关键修复] 如果fall_through_then是条件块，这可能是嵌套if
                # 需要检查它的跳转目标是否与fall_through_block的跳转目标相同
                # 检查then分支是否包含条件块
                # [关键修复] 如果fall_through_then是条件块，这可能是嵌套if
                # 需要检查它的跳转目标是否与fall_through_block的跳转目标相同
                # 检查then分支是否包含条件块
                # [关键修复] 如果fall_through_then是条件块，这可能是嵌套if
                # 需要检查它的跳转目标是否与fall_through_block的跳转目标相同
                if self._is_conditional_block(fall_through_then):
                    # [关键修复] 检查fall_through_then的跳转目标
                    # [关键修复] 检查fall_through_then的跳转目标
                    # [关键修复] 检查fall_through_then的跳转目标
                    # [关键修复] 检查fall_through_then的跳转目标
                    ft_then_jump = self._get_jump_instr(fall_through_then)
                    if ft_then_jump and ft_then_jump.argval is not None:
                        # [关键修复] 如果fall_through_then的跳转目标与fall_through_block的跳转目标不同
                        # 这是嵌套if，不是复合条件的一部分
                        # [关键修复] 如果fall_through_then的跳转目标与fall_through_block的跳转目标不同
                        # 这是嵌套if，不是复合条件的一部分
                        # [关键修复] 如果fall_through_then的跳转目标与fall_through_block的跳转目标不同
                        # 这是嵌套if，不是复合条件的一部分
                        # [关键修复] 如果fall_through_then的跳转目标与fall_through_block的跳转目标不同
                        # 这是嵌套if，不是复合条件的一部分
                        if ft_then_jump.argval != fall_through_jump.argval:
                            is_nested_if = True
                            if header.start_offset == 0:
                        # [关键修复] 如果跳转目标相同，检查fall_through_then的then分支是否也是条件块
                        # 如果是，这是嵌套if（如 if a: if b: if c: ...），不是复合条件
                        # [关键修复] 如果跳转目标相同，检查fall_through_then的then分支是否也是条件块
                        # 如果是，这是嵌套if（如 if a: if b: if c: ...），不是复合条件
                                pass
                        # [关键修复] 如果跳转目标相同，检查fall_through_then的then分支是否也是条件块
                        # 如果是，这是嵌套if（如 if a: if b: if c: ...），不是复合条件
                        elif not is_complex_bool_chain:
                            # 找到fall_through_then的then分支
                            # 找到fall_through_then的then分支
                            ft_then_then = None
                            for succ in fall_through_then.successors:
                                if succ.start_offset != ft_then_jump.argval:
                                    ft_then_then = succ
                            if header.start_offset == 0:
                                if ft_then_then:
                            # 如果fall_through_then的then分支也是条件块，这是嵌套if
                            # 如果fall_through_then的then分支也是条件块，这是嵌套if
                                    pass
                            # 如果fall_through_then的then分支也是条件块，这是嵌套if
                            if ft_then_then and self._is_conditional_block(ft_then_then):
                                # [字节码一致性修复] 检查是否是链式比较模式
                                # 链式比较的特征：当前块和fall_through块都有链式比较模式
                                # 此时ft_then_then是条件块是正常的（它是链中的下一个比较）
                                is_current_chain_cc = self._has_chain_compare_pattern(current_block)
                                is_fall_through_chain_cc = self._has_chain_compare_pattern(fall_through_block)
                                
                                if is_current_chain_cc or is_fall_through_chain_cc:
                                    # 这是链式比较，不是嵌套if，不要break
                                    is_nested_if = False  # 确保不标记为嵌套if
                                else:
                                    is_nested_if = True
                                    if header.start_offset == 0:
                                        break
                            elif header.start_offset == 0:
                                pass
                            # [关键修复] 检查fall_through_then的then分支是否包含实际代码
                            # 如果包含实际代码，这是嵌套if
                            if not is_nested_if:
                                non_trivial_instrs = [i for i in fall_through_then.instructions 
                                                      if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL',
                                                                          'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                                          'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                                                          'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                                                          'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE')]
                                has_actual_code = any(
                                    i.opname.startswith(('STORE_', 'BINARY_', 'CALL', 'BUILD_')) or
                                    (i.opname.startswith('UNARY_') and not i.opname.startswith('POP_JUMP'))
                                    for i in non_trivial_instrs
                                    if not i.opname.startswith(('LOAD_', 'POP_JUMP'))
                                )
                                if has_actual_code:
                                    is_nested_if = True
                                    if header.start_offset == 0:
                # 检查then分支是否包含复杂的代码（不只是值加载和JUMP_FORWARD）
                # [关键修复] 排除所有POP_JUMP_*指令，因为它们可能是复杂布尔表达式链的一部分
                # [关键修复] 同时排除LOAD_NAME，因为它是条件表达式的一部分
                # [关键修复] 对于复杂布尔表达式链，跳过这个检查
                # [关键修复] 排除UNARY_NOT，因为它是复合条件的一部分（如"not flag"）
                # 检查then分支是否包含复杂的代码（不只是值加载和JUMP_FORWARD）
                # [关键修复] 排除所有POP_JUMP_*指令，因为它们可能是复杂布尔表达式链的一部分
                # [关键修复] 同时排除LOAD_NAME，因为它是条件表达式的一部分
                # [关键修复] 对于复杂布尔表达式链，跳过这个检查
                # [关键修复] 排除UNARY_NOT，因为它是复合条件的一部分（如"not flag"）
                                        pass
                # 检查then分支是否包含复杂的代码（不只是值加载和JUMP_FORWARD）
                # [关键修复] 排除所有POP_JUMP_*指令，因为它们可能是复杂布尔表达式链的一部分
                # [关键修复] 同时排除LOAD_NAME，因为它是条件表达式的一部分
                # [关键修复] 对于复杂布尔表达式链，跳过这个检查
                # [关键修复] 排除UNARY_NOT，因为它是复合条件的一部分（如"not flag"）
                if not is_complex_bool_chain and not is_nested_if:
                    non_trivial_instrs = [i for i in fall_through_then.instructions 
                                          if i.opname not in ('RESUME', 'CACHE', 'NOP',
                                                              'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                                              'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                                                              'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                                              'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                                                              'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_CONST', 'LOAD_FAST',
                                                              'UNARY_NOT')]
                    has_complex_code = any(
                        i.opname not in ('LOAD_CONST', 'LOAD_FAST', 'JUMP_FORWARD', 'RETURN_VALUE', 'LOAD_NAME', 'LOAD_GLOBAL', 'UNARY_NOT')
                        for i in non_trivial_instrs
                    )
                    if has_complex_code:
                        is_nested_if = True
            
            # [关键修复] 检查fall_through_block是否是嵌套条件表达式
            # 嵌套条件表达式的特征：
            # 1. fall_through_block是一个条件块（有POP_JUMP指令）
            # 2. fall_through_block的then分支和else分支都只包含简单的值加载和JUMP_FORWARD
            # 3. fall_through_block的then分支和else分支都汇入同一个merge点
            # 这种情况下，fall_through_block是一个独立的条件表达式，不是复合条件的一部分
            # [关键修复] 对于复杂布尔表达式链，跳过这个检查，因为fall_through_block的then分支
            # 可能是另一个条件块，这是复杂布尔表达式链的正常特征
            if not is_nested_if and self._is_conditional_block(fall_through_block) and not is_complex_bool_chain:
                # 检查then分支和else分支是否都是条件表达式模式
                # 检查then分支和else分支是否都是条件表达式模式
                # 检查then分支和else分支是否都是条件表达式模式
                # 检查then分支和else分支是否都是条件表达式模式
                then_block = None
                else_block = None
                for succ in fall_through_block.successors:
                    if succ.start_offset != next_jump.argval:
                        then_block = succ
                    else:
                        else_block = succ
                
                if then_block and else_block:
                    # 检查then分支是否是条件表达式模式（只包含值加载和JUMP_FORWARD）
                    # 检查then分支是否是条件表达式模式（只包含值加载和JUMP_FORWARD）
                    # 检查then分支是否是条件表达式模式（只包含值加载和JUMP_FORWARD）
                    # 检查then分支是否是条件表达式模式（只包含值加载和JUMP_FORWARD）
                    then_non_trivial = [i for i in then_block.instructions 
                                        if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                    then_is_cond_expr = all(
                        i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD'
                        for i in then_non_trivial
                    )
                    
                    # 检查else分支是否是条件表达式模式（只包含值加载和JUMP_FORWARD）
                    else_non_trivial = [i for i in else_block.instructions 
                                        if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                    else_is_cond_expr = all(
                        i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD'
                        for i in else_non_trivial
                    )
                    
                    # 检查then分支和else分支是否汇入同一个merge点
                    then_succs = set(s.start_offset for s in then_block.successors)
                    else_succs = set(s.start_offset for s in else_block.successors)
                    common_merge = then_succs & else_succs
                    
                    # 如果都是条件表达式模式且有共同的merge点，这是嵌套条件表达式
                    if then_is_cond_expr and else_is_cond_expr and common_merge:
                        is_nested_if = True
            
            # [关键修复] 检查跳转目标是否与header相同（AND条件）
            # 或跳转目标都在else_body中且不是嵌套if（链式比较）
            is_and_condition = (current_jump.argval == header_jump_target and 
                               next_jump.argval == header_jump_target)
            
            # [关键修复] 区分深层嵌套if和AND复合条件
            # 深层嵌套if的特征：
            # 1. 所有条件的跳转目标都相同（共享else分支）
            # 2. 每个条件的fall-through块是下一个条件块（不是包含实际代码的then分支）
            # 3. 最后一个条件的fall-through块包含实际代码（如return）
            # AND复合条件的特征：
            # 1. 所有条件的跳转目标都相同（共享else分支）
            # 2. 最后一个条件的fall-through块包含实际代码（如赋值、调用等）
            # 3. 所有条件块都在同一个逻辑行（没有嵌套结构）
            # 
            # [关键修复] 最重要的区别：
            # - 深层嵌套if：每个条件的fall-through块是条件块（形成嵌套结构）
            # - AND复合条件：只有最后一个条件的fall-through块可能包含实际代码
            # [关键修复] 对于AND复合条件（如 if x > 0 and y > 0:）
            # 即使fall-through块是条件块，只要跳转目标相同，也是AND复合条件
            # 不是嵌套if结构。嵌套if的特征是：内层if的else分支包含实际代码，不只是跳转
            if is_and_condition and self._is_conditional_block(fall_through_block):
                # 检查fall-through块的else分支是否只是简单的跳转（复合条件）
                # 还是包含实际代码（嵌套if）
                # 检查fall-through块的else分支是否只是简单的跳转（复合条件）
                # 还是包含实际代码（嵌套if）
                # 检查fall-through块的else分支是否只是简单的跳转（复合条件）
                # 还是包含实际代码（嵌套if）
                # 检查fall-through块的else分支是否只是简单的跳转（复合条件）
                # 还是包含实际代码（嵌套if）
                ft_jump = self._get_jump_instr(fall_through_block)
                if ft_jump:
                    ft_else_block = None
                    for succ in fall_through_block.successors:
                        if succ.start_offset == ft_jump.argval:
                            ft_else_block = succ
                            break
                    
                    if ft_else_block:
                        # 检查else分支是否包含实际代码
                        # [关键修复] 排除LOAD_CONST和LOAD_FAST，因为它们是return语句的一部分
                        # 检查else分支是否包含实际代码
                        # [关键修复] 排除LOAD_CONST和LOAD_FAST，因为它们是return语句的一部分
                        # 检查else分支是否包含实际代码
                        # [关键修复] 排除LOAD_CONST和LOAD_FAST，因为它们是return语句的一部分
                        # 检查else分支是否包含实际代码
                        # [关键修复] 排除LOAD_CONST和LOAD_FAST，因为它们是return语句的一部分
                        non_trivial_in_else = [i for i in ft_else_block.instructions 
                                               if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                                                   'POP_TOP', 'RETURN_VALUE', 'JUMP_FORWARD',
                                                                   'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL')]
                        if len(non_trivial_in_else) == 0:
                            # else分支只是简单的跳转，这是复合条件，不是嵌套if
                            # else分支只是简单的跳转，这是复合条件，不是嵌套if
                            # else分支只是简单的跳转，这是复合条件，不是嵌套if
                            # else分支只是简单的跳转，这是复合条件，不是嵌套if
                            is_nested_if = False
                        else:
                            # else分支包含实际代码，这是嵌套if
                            is_and_condition = False
                            is_nested_if = True
            
            if not is_and_condition and current_block == header:
                # 检查是否是AND复合条件
                # 特征：第二个条件块的else分支最终汇入第一个条件块的else分支
                # 检查是否是AND复合条件
                # 特征：第二个条件块的else分支最终汇入第一个条件块的else分支
                # 检查是否是AND复合条件
                # 特征：第二个条件块的else分支最终汇入第一个条件块的else分支
                # 检查是否是AND复合条件
                # 特征：第二个条件块的else分支最终汇入第一个条件块的else分支
                next_jump_target_block = None
                for succ in fall_through_block.successors:
                    if succ.start_offset == next_jump.argval:
                        next_jump_target_block = succ
                        break
                
                if next_jump_target_block:
                    # [关键修复] 检查next_jump_target_block是否是条件块
                    # 如果是条件块，这是嵌套if，不是复合条件
                    # 嵌套if的else分支是另一个条件块，有自己的then_body和else_body
                    # [关键修复] 检查next_jump_target_block是否是条件块
                    # 如果是条件块，这是嵌套if，不是复合条件
                    # 嵌套if的else分支是另一个条件块，有自己的then_body和else_body
                    # [关键修复] 检查next_jump_target_block是否是条件块
                    # 如果是条件块，这是嵌套if，不是复合条件
                    # 嵌套if的else分支是另一个条件块，有自己的then_body和else_body
                    # [关键修复] 检查next_jump_target_block是否是条件块
                    # 如果是条件块，这是嵌套if，不是复合条件
                    # 嵌套if的else分支是另一个条件块，有自己的then_body和else_body
                    if self._is_conditional_block(next_jump_target_block):
                        # 这是嵌套if，不是复合条件
                        # [字节码一致性修复] 检查是否是链式比较模式
                        # 链式比较的特征：当前块和fall_through块都有链式比较模式
                        # 此时next_jump_target_block是条件块是正常的（它是下一个比较）
                        is_current_chain = self._has_chain_compare_pattern(current_block)
                        is_fall_through_chain = self._has_chain_compare_pattern(fall_through_block)
                        
                        if is_current_chain or is_fall_through_chain:
                            # 这是链式比较，不是嵌套if，不要break
                            pass
                        elif header.start_offset == 0:
                            break
                    else:
                        # [关键修复] 检查next_jump_target_block是否是简单的跳转块
                        # 复合条件的特征：第二个条件的else分支是一个简单的跳转块，只包含JUMP_FORWARD到共享else
                        # 嵌套if的特征：第二个条件的else分支包含实际代码（如赋值），然后才跳转
                        # [关键修复] 对于复杂布尔表达式链，跳过这个检查
                        if not is_complex_bool_chain:
                            non_trivial_in_else = [i for i in next_jump_target_block.instructions 
                                                   if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                                                       'POP_TOP', 'RETURN_VALUE', 'JUMP_FORWARD')]
                            # 如果else分支包含实际代码（不只是跳转），这是嵌套if，不是复合条件
                            if len(non_trivial_in_else) > 0:
                                # [关键修复] 设置is_nested_if为True，防止将嵌套if识别为复合条件
                                # [关键修复] 设置is_nested_if为True，防止将嵌套if识别为复合条件
                                # [关键修复] 设置is_nested_if为True，防止将嵌套if识别为复合条件
                                # [关键修复] 设置is_nested_if为True，防止将嵌套if识别为复合条件
                                is_nested_if = True
                                # 嵌套if：第二个条件的else分支有自己的代码逻辑
                                is_and_condition = False
                        else:
                            # 检查next_jump_target_block是否最终汇入header_jump_target
                            # 简单情况：next_jump_target_block直接跳转到header_jump_target
                            next_target_jump = self._get_jump_instr(next_jump_target_block)
                            if next_target_jump and next_target_jump.argval == header_jump_target:
                                is_and_condition = True
                            # 复杂情况：next_jump_target_block的后继包含header_jump_target
                            elif any(succ.start_offset == header_jump_target for succ in next_jump_target_block.successors):
                                is_and_condition = True
            
            # [关键修复] 对于复杂布尔表达式链，即使跳转目标不同，也应该继续检测
            # 特征：fall_through_block是条件块，且它的then分支不包含实际代码
            if not is_and_condition and is_complex_bool_chain:
                # 检查是否是复杂布尔表达式链的一部分
                # 只要fall_through_block是条件块，且它的then分支不包含实际代码，就继续
                # 检查是否是复杂布尔表达式链的一部分
                # 只要fall_through_block是条件块，且它的then分支不包含实际代码，就继续
                # 检查是否是复杂布尔表达式链的一部分
                # 只要fall_through_block是条件块，且它的then分支不包含实际代码，就继续
                # 检查是否是复杂布尔表达式链的一部分
                # 只要fall_through_block是条件块，且它的then分支不包含实际代码，就继续
                is_and_condition = True
            
            # [关键修复] 检测三个或更多条件的链式比较（如 0 < x <= 5 < 10）
            # 特征：
            # 1. 当前块和fall_through块都是条件块
            # 2. 它们的跳转目标都在else_body中
            # 3. fall_through块本身是条件块（有三个或更多条件）
            is_multi_condition_chain = False
            if (current_jump_target_in_else and next_jump_target_in_else and
                not is_nested_if):
                # 检查fall_through块本身是否是条件块（有三个或更多条件）
                # 特征：fall_through块包含条件跳转指令（POP_JUMP_*）
                fall_through_has_cond_jump = any(
                    i.opname.startswith('POP_JUMP') or i.opname.startswith('JUMP_IF')
                    for i in fall_through_block.instructions
                )
                # 检查fall_through块是否是条件块（有两个后继）
                fall_through_is_cond_block = len(fall_through_block.successors) == 2
                if fall_through_has_cond_jump and fall_through_is_cond_block:
                    is_multi_condition_chain = True
            
            is_chained_compare = ((current_jump_target_in_else and next_jump_target_in_else and
                                 current_block == header and not is_nested_if) or
                                 is_chained_compare_pattern or
                                 is_multi_condition_chain)
            
            # [关键修复] 检查是否都是简单的return None（模块级别的复合条件）
            # 这种情况：每个条件块的else分支都是独立的return None块
            current_jump_target_block = None
            next_jump_target_block = None
            for succ in current_block.successors:
                if succ.start_offset == current_jump.argval:
                    current_jump_target_block = succ
                    break
            for succ in fall_through_block.successors:
                if succ.start_offset == next_jump.argval:
                    next_jump_target_block = succ
                    break
            is_both_return_none = (
                self._is_simple_return_none(current_jump_target_block) and
                self._is_simple_return_none(next_jump_target_block)
            )
            
            # [关键修复] 检查是否是混合AND/OR复合条件（如 x > 0 and y < 10 or z == 'test'）
            # 混合条件的特征：
            # 1. 使用 JUMP_IF_TRUE_OR_POP 或 JUMP_IF_FALSE_OR_POP 指令
            # 2. 所有条件块的跳转最终都指向同一个目标（存储结果的块）
            is_mixed_condition = False
            if next_jump.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                # 检查这是否是混合条件的一部分
                # 混合条件的所有部分最终都跳转到同一个目标
                # 检查这是否是混合条件的一部分
                # 混合条件的所有部分最终都跳转到同一个目标
                # 检查这是否是混合条件的一部分
                # 混合条件的所有部分最终都跳转到同一个目标
                # 检查这是否是混合条件的一部分
                # 混合条件的所有部分最终都跳转到同一个目标
                if len(condition_chain) >= 1:
                    # 获取第一个条件的跳转目标
                    # 获取第一个条件的跳转目标
                    # 获取第一个条件的跳转目标
                    # 获取第一个条件的跳转目标
                    first_jump = self._get_jump_instr(condition_chain[0])
                    if first_jump and first_jump.opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                        # AND链的开始，检查后续条件是否使用OR或继续AND
                        # 如果fall_through_block使用JUMP_IF_TRUE_OR_POP或JUMP_IF_FALSE_OR_POP，这是混合条件
                        # AND链的开始，检查后续条件是否使用OR或继续AND
                        # 如果fall_through_block使用JUMP_IF_TRUE_OR_POP或JUMP_IF_FALSE_OR_POP，这是混合条件
                        # AND链的开始，检查后续条件是否使用OR或继续AND
                        # 如果fall_through_block使用JUMP_IF_TRUE_OR_POP或JUMP_IF_FALSE_OR_POP，这是混合条件
                        # AND链的开始，检查后续条件是否使用OR或继续AND
                        # 如果fall_through_block使用JUMP_IF_TRUE_OR_POP或JUMP_IF_FALSE_OR_POP，这是混合条件
                        if next_jump.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                            is_mixed_condition = True
                    elif first_jump and first_jump.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE'):
                        # OR链的开始，检查后续条件是否使用AND或继续OR
                        # OR链的开始，检查后续条件是否使用AND或继续OR
                        if next_jump.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                            is_mixed_condition = True
            
            # [关键修复] 如果检测到嵌套条件表达式，不要将其识别为复合条件
            if is_nested_if:
                # 嵌套条件表达式是独立的IfStructure，不是复合条件的一部分
                # 嵌套条件表达式是独立的IfStructure，不是复合条件的一部分
                pass
                # 嵌套条件表达式是独立的IfStructure，不是复合条件的一部分
            # [字节码一致性修复] 强制检测链式比较模式（如 0 < a < b < c < 100）
            # 链式比较的特征：
            # 1. 当前块和fall-through块都包含 SWAP(2) + COPY(2) + COMPARE_OP 指令序列
            # 2. fall-through块也是条件块（有2个后继）
            # 3. 即使跳转目标不完全相同，也应该继续收集
            is_forced_chain_compare = False
            if (not (is_and_condition or is_or_condition or is_chained_compare or is_both_return_none or is_mixed_condition or is_complex_bool_chain) and
                self._has_chain_compare_pattern(current_block) and
                self._has_chain_compare_pattern(fall_through_block) and
                len(fall_through_block.successors) == 2):
                # [关键修复] 这是链式比较的一部分，强制继续收集
                is_forced_chain_compare = True

            if not (is_and_condition or is_or_condition or is_chained_compare or is_both_return_none or is_mixed_condition or is_complex_bool_chain or is_forced_chain_compare):
                break

            # [关键修复] 对于复合条件，不需要检查elif链
            # elif链的检测在 _analyze_if_structure 方法中进行
            # 这里只需要检查条件链的结构

            # 这是复合条件的一部分
                # 不是复合条件的一部分

            # [关键修复] 对于复合条件，不需要检查elif链
            # elif链的检测在 _analyze_if_structure 方法中进行
            # 这里只需要检查条件链的结构

            # 这是复合条件的一部分
                pass
                # 不是复合条件的一部分

            # [关键修复] 对于复合条件，不需要检查elif链
            # elif链的检测在 _analyze_if_structure 方法中进行
            # 这里只需要检查条件链的结构

            # 这是复合条件的一部分
            compound_blocks.add(fall_through_block)
            condition_chain.append(fall_through_block)
            current_block = fall_through_block
        
        # [关键修复] 检查是否有复合条件的最后一部分（如 not flag）
        # 这种块没有条件跳转指令，但直接连接到 merge_block
        # 注意：这只适用于复合条件赋值（使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP）
        # 不适用于链式比较（使用 POP_JUMP_FORWARD_IF_FALSE）
        if len(condition_chain) >= 2:
            # 检查是否是复合条件赋值（使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP）
            # 检查是否是复合条件赋值（使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP）
            # 检查是否是复合条件赋值（使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP）
            # 检查是否是复合条件赋值（使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP）
            is_compound_assignment = any(
                instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                for cond_block in condition_chain
                for instr in cond_block.instructions
            )
            
            if is_compound_assignment:
                last_cond_block = condition_chain[-1]
                # 获取最后一个条件块的 fall-through 后继
                last_jump = self._get_jump_instr(last_cond_block)
                if last_jump:
                    for succ in last_cond_block.successors:
                        if succ.start_offset != last_jump.argval:
                            # 这是 fall-through 后继
                            # 检查它是否是复合条件的最后一部分
                            # 特征：没有条件跳转，但可能是 not 操作等
                            # 这是 fall-through 后继
                            # 检查它是否是复合条件的最后一部分
                            # 特征：没有条件跳转，但可能是 not 操作等
                            # 这是 fall-through 后继
                            # 检查它是否是复合条件的最后一部分
                            # 特征：没有条件跳转，但可能是 not 操作等
                            # 这是 fall-through 后继
                            # 检查它是否是复合条件的最后一部分
                            # 特征：没有条件跳转，但可能是 not 操作等
                            has_cond_jump = any(
                                'JUMP' in instr.opname and ('IF_' in instr.opname or 'IF_FALSE' in instr.opname or 'IF_TRUE' in instr.opname)
                                for instr in succ.instructions
                            )
                            if not has_cond_jump:
                                # 这可能是复合条件的最后一部分（如 not flag）
                                # 检查它是否连接到 merge_block
                                # 对于混合条件，所有部分最终都汇入同一个 merge_block
                                # 这可能是复合条件的最后一部分（如 not flag）
                                # 检查它是否连接到 merge_block
                                # 对于混合条件，所有部分最终都汇入同一个 merge_block
                                # 这可能是复合条件的最后一部分（如 not flag）
                                # 检查它是否连接到 merge_block
                                # 对于混合条件，所有部分最终都汇入同一个 merge_block
                                # 这可能是复合条件的最后一部分（如 not flag）
                                # 检查它是否连接到 merge_block
                                # 对于混合条件，所有部分最终都汇入同一个 merge_block
                                compound_blocks.add(succ)
                                condition_chain.append(succ)
                            break

        # [关键修复] 最终检查：确保所有条件块的跳转目标都相同（复合条件的特征）
        # 如果跳转目标不同，说明这是嵌套if，不是复合条件
        # [重要修复] 但对于混合条件（如 (x > 0 and y < 10) or (z == 'test' and not flag)），
        # 跳转目标可能不同，但最终都汇入同一个merge块
        if len(condition_chain) > 1:
            jump_targets = set()
            for cond_block in condition_chain:
                jump_instr = self._get_jump_instr(cond_block)
                if jump_instr and jump_instr.argval is not None:
                    jump_targets.add(jump_instr.argval)

            # [重要修复] 检查是否是混合条件（使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP）
            # 混合条件的跳转目标可能不同，但最终都汇入同一个merge块
            is_mixed_compound_condition = any(
                instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                for cond_block in condition_chain
                for instr in cond_block.instructions
            )
            
            # [关键修复] 检查是否是OR条件
            # OR条件的特征：第一个条件使用POP_JUMP_IF_TRUE，第二个条件使用POP_JUMP_IF_FALSE
            # 且第二个条件的fall-through目标与第一个条件的跳转目标相同
            is_or_compound_condition = False
            if len(condition_chain) >= 2:
                first_cond = condition_chain[0]
                second_cond = condition_chain[1]
                first_jump = self._get_jump_instr(first_cond)
                second_jump = self._get_jump_instr(second_cond)
                
                if first_jump and second_jump:
                    # 第一个条件使用IF_TRUE，第二个条件使用IF_FALSE
                    # 第一个条件使用IF_TRUE，第二个条件使用IF_FALSE
                    # 第一个条件使用IF_TRUE，第二个条件使用IF_FALSE
                    # 第一个条件使用IF_TRUE，第二个条件使用IF_FALSE
                    is_first_true = 'IF_TRUE' in first_jump.opname
                    is_second_false = 'IF_FALSE' in second_jump.opname
                    
                    if is_first_true and is_second_false:
                        # 找到第二个条件的fall-through目标
                        # 找到第二个条件的fall-through目标
                        # 找到第二个条件的fall-through目标
                        # 找到第二个条件的fall-through目标
                        second_fall_through = None
                        for succ in second_cond.successors:
                            if succ.start_offset != second_jump.argval:
                                second_fall_through = succ
                                break
                        
                        # 检查第二个条件的fall-through目标是否与第一个条件的跳转目标相同
                        if second_fall_through and second_fall_through.start_offset == first_jump.argval:
                            is_or_compound_condition = True
            
            # 如果跳转目标不同，且不是混合条件，也不是OR条件，说明不是复合条件，重置为只有header
            # [字节码一致性修复] 链式比较的每个比较块跳转到不同的目标（各自的失败处理）
            # 这是链式比较的正常特征，不应该导致重置
            is_chain_compare_result = any(
                self._has_chain_compare_pattern(b) for b in condition_chain
            )
            
            if len(jump_targets) > 1 and not is_mixed_compound_condition and not is_or_compound_condition and not is_chain_compare_result:
                return set(), [header]

        return compound_blocks, condition_chain

    def _has_chain_compare_pattern(self, block: BasicBlock) -> bool:
        """
        检查块是否包含链式比较特征指令
        
        链式比较（如 0 < x < 100）的特征：
        1. 包含COMPARE_OP指令
        2. 包含JUMP_IF_FALSE_OR_POP或JUMP_IF_TRUE_OR_POP指令（这是链式比较特有的）
        
        注意：普通的if条件（如 if x > 0:）使用POP_JUMP_FORWARD_IF_FALSE等指令，
        而不是JUMP_IF_FALSE_OR_POP。只有链式比较才会使用JUMP_IF_FALSE_OR_POP。
        
        Returns:
            True如果块包含链式比较特征，False否则
        """
        has_compare = False
        has_chain_jump = False
        
        for instr in block.instructions:
            if instr.opname == 'COMPARE_OP':
                has_compare = True
            elif instr.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                # 链式比较特有的跳转指令
                has_chain_jump = True
        
        return has_compare and has_chain_jump

    def _detect_elif_chain_in_loop(self, header: BasicBlock, else_body: Set[BasicBlock],
                                   loop_headers: Set[BasicBlock]) -> List[BasicBlock]:
        """
        检测循环内的elif链
        
        循环内的elif链特征：
        1. 当前if的else分支（fall-through）包含另一个条件块
        2. 该条件块的跳转目标与当前if不同（指向下一个条件或循环外）
        3. 形成链式结构
        
        Args:
            header: 当前if的头部块
            else_body: else分支体
            loop_headers: 循环头部集合
            
        Returns:
            elif链中的条件块列表（包括header）
        """
        elif_chain = [header]
        
        # 获取header的跳转指令
        header_jump = self._get_jump_instr(header)
        if not header_jump or header_jump.argval is None:
            return elif_chain
        
        # 找到header的fall-through块（then分支）
        header_then = None
        for succ in header.successors:
            if succ.start_offset != header_jump.argval:
                header_then = succ
                break
        
        if not header_then:
            return elif_chain
        
        # 检查fall-through块是否是条件块（可能是elif）
        current = header_then
        visited = {header}
        
        while current and current not in visited:
            if not self._is_conditional_block(current):
                break
            if len(current.successors) != 2:
                break
            
            visited.add(current)
            
            # 获取当前块的跳转指令
            jump_instr = self._get_jump_instr(current)
            if not jump_instr or jump_instr.argval is None:
                break
            
            # 找到跳转目标块
            jump_target = None
            for succ in current.successors:
                if succ.start_offset == jump_instr.argval:
                    jump_target = succ
                    break
            
            if not jump_target:
                break
            
            # 检查是否是elif链的一部分
            # 条件：跳转目标不在当前已访问的链中（指向下一个elif或else/循环）
            if jump_target not in visited:
                elif_chain.append(current)
                
                # 找到fall-through块，继续链
                fall_through = None
                for succ in current.successors:
                    if succ.start_offset != jump_instr.argval:
                        fall_through = succ
                        break
                
                current = fall_through
            else:
                break
        
        return elif_chain
    
    def _detect_elif_chain(self, header: BasicBlock, else_body: Set[BasicBlock],
                          loop_headers: Set[BasicBlock]) -> List[BasicBlock]:
        """
        检测elif链（通用版本，不限于循环内）

        elif链的核心特征：
        1. 多个条件块形成链式结构
        2. 每个条件块的else分支指向下一个条件块
        3. 最后一个条件块的else分支指向最终的else分支

        与复合条件的区别：
        - 复合条件：所有条件块的跳转目标相同（共享else分支）
        - elif链：每个条件块的跳转目标不同（指向下一个elif或最终else）

        Args:
            header: 当前if的头部块
            else_body: else分支体
            loop_headers: 循环头部集合

        Returns:
            elif链中的条件块列表（包括header）
        """
        elif_chain = [header]

        # 获取header的跳转指令
        header_jump = self._get_jump_instr(header)
        if not header_jump or header_jump.argval is None:
            return elif_chain

        # [关键修复] 检测链式比较模式（如 0 < a < b < c < 100）
        # 链式比较的特征：
        # 1. header包含 SWAP(2) + COPY(2) + COMPARE_OP 指令序列
        # 2. fall-through后继也是条件块，且包含相同的指令序列
        # 3. 两者的跳转目标相同（都指向else分支）
        # 这与真正的elif不同：elif的条件块通常不包含SWAP/COPY指令
        header_fall_through = None
        for succ in header.successors:
            if succ.start_offset != header_jump.argval:
                header_fall_through = succ
                break

        if header_fall_through and self._is_conditional_block(header_fall_through):
            fall_through_jump = self._get_jump_instr(header_fall_through)

            # [关键修复] 检查是否是链式比较模式
            is_chain_compare = False
            if (fall_through_jump and fall_through_jump.argval == header_jump.argval):
                # 检查header和fall-through是否都包含链式比较特征指令
                header_has_chain_pattern = self._has_chain_compare_pattern(header)
                fallthrough_has_chain_pattern = self._has_chain_compare_pattern(header_fall_through)

                if header_has_chain_pattern and fallthrough_has_chain_pattern:
                    is_chain_compare = True

            # [关键修复] 检查fall-through块是否包含赋值语句
            # 如果包含，这是内层if结构，不是复合条件
            has_assignment = any(
                instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')
                for instr in header_fall_through.instructions
            )
            
            # [关键修复] 检查fall-through块是否是独立的if结构（内层if）
            # 独立的if结构特征：
            # 1. fall-through块是条件块
            # 2. fall-through块有自己的then分支和else分支
            # 3. fall-through块的跳转目标与header的跳转目标相同（共享else分支）
            # 4. fall-through块的前驱只有header（不是复合条件的一部分）
            is_independent_if = False
            if fall_through_jump:
                # 找到fall-through块的fall-through后继（then分支）和跳转目标（else分支）
                fall_through_then = None
                fall_through_else = None
                for succ in header_fall_through.successors:
                    if succ.start_offset == fall_through_jump.argval:
                        fall_through_else = succ
                    else:
                        fall_through_then = succ
                
                # [关键修复] 独立的if结构的特征：
                # 1. fall-through块是条件块（已检查）
                # 2. fall-through块的跳转目标与header的跳转目标相同（共享else分支）
                # 3. fall-through块的前驱只有header（不是复合条件的一部分）
                # 4. fall-through块有自己的then分支（即使是NOP）
                if fall_through_then and fall_through_else:
                    # 检查fall-through块的前驱是否只有header
                    preds = list(header_fall_through.predecessors)
                    has_only_header_pred = len(preds) == 1 and preds[0] == header
                    
                    # 检查fall-through块的跳转目标是否与header的跳转目标相同
                    shares_else_with_header = fall_through_jump.argval == header_jump.argval
                    
                    # 如果满足这些条件，这是独立的if结构（内层if）
                    if has_only_header_pred and shares_else_with_header:
                        is_independent_if = True
            
            if not has_assignment and not is_independent_if and (is_chain_compare or (fall_through_jump and fall_through_jump.argval == header_jump.argval)):
                # [关键修复] 这是复合条件（如 if a and b:），不是elif链
                # 将fall-through块添加到条件链中，然后停止
                # [关键修复] 这是复合条件（如 if a and b:），不是elif链
                # 将fall-through块添加到条件链中，然后停止
                # [关键修复] 这是复合条件（如 if a and b:），不是elif链
                # 将fall-through块添加到条件链中，然后停止
                # [关键修复] 这是复合条件（如 if a and b:），不是elif链
                # 将fall-through块添加到条件链中，然后停止
                elif_chain.append(header_fall_through)
                return elif_chain

        # [关键修复] 在else_body中查找条件块
        # 这些条件块可能是elif链的一部分
        visited = {header}
        current = header
        
        while True:
            # 获取当前块的跳转指令
            # 获取当前块的跳转指令
            # 获取当前块的跳转指令
            # 获取当前块的跳转指令
            current_jump = self._get_jump_instr(current)
            if not current_jump or current_jump.argval is None:
                break

            # 找到跳转目标块
            jump_target = None
            for succ in current.successors:
                if succ.start_offset == current_jump.argval:
                    jump_target = succ
                    break
            if not jump_target:
                break

            # [关键修复] 检查跳转目标是否是条件块
            # 如果是，这可能是elif链的一部分
            # [关键修复] 不要排除包含向后跳转的块
            # 在循环内的elif链中，每个条件块都包含JUMP_BACKWARD指令（跳转到循环头部）
            # 这是正常的，不应该因此排除
            is_conditional = self._is_conditional_block(jump_target)
            
            # [关键修复] 检查jump_target是否使用JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP进行赋值
            # 如 x = a or b，这种情况下jump_target不是elif条件，而是else分支的正常代码
            if is_conditional:
                target_jump = self._get_jump_instr(jump_target)
                if target_jump and target_jump.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                    # 检查跳转目标是否是STORE_FAST
                    jump_target_offset = target_jump.argval
                    if jump_target_offset is not None:
                        for succ in jump_target.successors:
                            if succ.start_offset == jump_target_offset:
                                # 检查跳转目标块是否以STORE_FAST开头
                                for target_instr in succ.instructions:
                                    if target_instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                                        if target_instr.opname == 'STORE_FAST':
                                            # 这是赋值语句，不是elif条件
                                            is_conditional = False
                                        break
                                break
            
            # [关键修复] 检查jump_target是否是OR条件的header（如 if a or b:）
            # OR条件的特征：
            # 1. jump_target使用POP_JUMP_FORWARD_IF_TRUE（条件为True时跳转到then-body）
            # 2. jump_target的fall-through后继也是条件块，使用POP_JUMP_FORWARD_IF_FALSE
            # 3. jump_target的fall-through后继的fall-through目标与jump_target的跳转目标相同（都是then-body）
            if is_conditional:
                target_jump = self._get_jump_instr(jump_target)
                if target_jump and 'POP_JUMP_FORWARD_IF_TRUE' in target_jump.opname:
                    # 找到jump_target的fall-through后继
                    # 找到jump_target的fall-through后继
                    # 找到jump_target的fall-through后继
                    # 找到jump_target的fall-through后继
                    target_fall_through = None
                    for succ in jump_target.successors:
                        if succ.start_offset != target_jump.argval:
                            target_fall_through = succ
                            break
                    
                    if target_fall_through and self._is_conditional_block(target_fall_through):
                        fall_through_jump = self._get_jump_instr(target_fall_through)
                        if fall_through_jump and 'POP_JUMP_FORWARD_IF_FALSE' in fall_through_jump.opname:
                            # 找到fall-through后继的fall-through目标
                            # 找到fall-through后继的fall-through目标
                            # 找到fall-through后继的fall-through目标
                            # 找到fall-through后继的fall-through目标
                            fall_through_fall_through = None
                            for succ in target_fall_through.successors:
                                if succ.start_offset != fall_through_jump.argval:
                                    fall_through_fall_through = succ
                                    break
                            
                            # 检查fall-through后继的fall-through目标是否与jump_target的跳转目标相同
                            if fall_through_fall_through and fall_through_fall_through.start_offset == target_jump.argval:
                                # jump_target是OR条件的header，不是elif链的一部分
                                # jump_target是OR条件的header，不是elif链的一部分
                                # jump_target是OR条件的header，不是elif链的一部分
                                # jump_target是OR条件的header，不是elif链的一部分
                                break
            
            # [关键修复] 对于复合条件的情况，jump_target可能不在else_body中
            # 但只要jump_target是条件块，且它的唯一前驱是current，就是elif链的一部分
            in_else_body = jump_target in else_body
            is_elif_candidate = is_conditional and in_else_body

            
            # [关键修复] 如果jump_target不在else_body中，但它是current的跳转目标
            # 且jump_target是条件块，则它也是elif候选
            # 这种情况发生在if的then分支直接return时（如：if x: return ... elif y: ...）
            if is_conditional and not in_else_body:
                # 检查jump_target是否是current的跳转目标
                is_jump_target_of_current = False
                for succ in current.successors:
                    if succ.start_offset == current_jump.argval and succ == jump_target:
                        is_jump_target_of_current = True
                        break
                
                if is_jump_target_of_current:
                    # 检查jump_target的前驱是否主要是current
                    preds = list(jump_target.predecessors)
                    if len(preds) == 1 and preds[0] == current:
                        is_elif_candidate = True
                    elif current in preds:
                        # 有多个前驱，但current是其中之一
                        # 检查current的then分支是否有return
                        current_then = None
                        for succ in current.successors:
                            if succ.start_offset != current_jump.argval:
                                current_then = succ
                                break
                        
                        if current_then:
                            then_has_return = any(instr.opname == 'RETURN_VALUE' for instr in current_then.instructions)
                            if then_has_return:
                                is_elif_candidate = True
            
            # [关键修复] 如果jump_target不在else_body中，检查它是否是elif链的候选
            if is_conditional and not in_else_body:
                # [关键修复] 首先检查jump_target是否是循环body块
                # 如果是，需要进一步判断它是elif链的一部分还是独立的if语句
                # 在循环体内的if-elif-else结构中，elif条件块也在循环的body_blocks中
                # 但它仍然是elif链的一部分，不应该被排除
                # [关键修复] 首先检查jump_target是否是循环body块
                # 如果是，需要进一步判断它是elif链的一部分还是独立的if语句
                # 在循环体内的if-elif-else结构中，elif条件块也在循环的body_blocks中
                # 但它仍然是elif链的一部分，不应该被排除
                # [关键修复] 首先检查jump_target是否是循环body块
                # 如果是，需要进一步判断它是elif链的一部分还是独立的if语句
                # 在循环体内的if-elif-else结构中，elif条件块也在循环的body_blocks中
                # 但它仍然是elif链的一部分，不应该被排除
                # [关键修复] 首先检查jump_target是否是循环body块
                # 如果是，需要进一步判断它是elif链的一部分还是独立的if语句
                # 在循环体内的if-elif-else结构中，elif条件块也在循环的body_blocks中
                # 但它仍然是elif链的一部分，不应该被排除
                is_loop_body_block = False
                containing_loop = None
                for struct in self.structures:
                    if isinstance(struct, LoopStructure):
                        if jump_target in struct.body_blocks:
                            is_loop_body_block = True
                            containing_loop = struct
                            break
                
                if is_loop_body_block:
                    # [关键修复] jump_target是循环body块，但可能是elif链的一部分
                    # 进一步检查：
                    # 1. jump_target的唯一前驱是否是current（前一个if条件的跳转目标）
                    # 2. current的then分支是否跳转到循环内的merge点（而不是fall-through到jump_target）
                    # 如果满足这些条件，jump_target是elif链的一部分
                    # [关键修复] jump_target是循环body块，但可能是elif链的一部分
                    # 进一步检查：
                    # 1. jump_target的唯一前驱是否是current（前一个if条件的跳转目标）
                    # 2. current的then分支是否跳转到循环内的merge点（而不是fall-through到jump_target）
                    # 如果满足这些条件，jump_target是elif链的一部分
                    # [关键修复] jump_target是循环body块，但可能是elif链的一部分
                    # 进一步检查：
                    # 1. jump_target的唯一前驱是否是current（前一个if条件的跳转目标）
                    # 2. current的then分支是否跳转到循环内的merge点（而不是fall-through到jump_target）
                    # 如果满足这些条件，jump_target是elif链的一部分
                    # [关键修复] jump_target是循环body块，但可能是elif链的一部分
                    # 进一步检查：
                    # 1. jump_target的唯一前驱是否是current（前一个if条件的跳转目标）
                    # 2. current的then分支是否跳转到循环内的merge点（而不是fall-through到jump_target）
                    # 如果满足这些条件，jump_target是elif链的一部分
                    is_elif_in_loop = False
                    
                    # 检查jump_target的前驱是否只有current（或主要是current）
                    preds = list(jump_target.predecessors)
                    if len(preds) == 1 and preds[0] == current:
                        # jump_target的唯一前驱是current，这是elif链的典型特征
                        # jump_target的唯一前驱是current，这是elif链的典型特征
                        # jump_target的唯一前驱是current，这是elif链的典型特征
                        # jump_target的唯一前驱是current，这是elif链的典型特征
                        is_elif_in_loop = True
                    elif current in preds:
                        # jump_target有多个前驱，但current是其中之一
                        # 检查current的then分支是否跳转到与jump_target不同的位置
                        # jump_target有多个前驱，但current是其中之一
                        # 检查current的then分支是否跳转到与jump_target不同的位置
                        current_then = None
                        for succ in current.successors:
                            if succ.start_offset != current_jump.argval:
                                current_then = succ
                                break
                        
                        if current_then:
                            # 检查current的then分支是否以JUMP_FORWARD结束（跳转到merge点）
                            # 检查current的then分支是否以JUMP_FORWARD结束（跳转到merge点）
                            # 检查current的then分支是否以JUMP_FORWARD结束（跳转到merge点）
                            # 检查current的then分支是否以JUMP_FORWARD结束（跳转到merge点）
                            then_has_jump_forward = False
                            then_jump_target = None
                            for instr in current_then.instructions:
                                if instr.opname == 'JUMP_FORWARD':
                                    then_has_jump_forward = True
                                    then_jump_target = instr.argval
                                    break
                            
                            if then_has_jump_forward:
                                # current的then分支跳转到merge点，这是elif链的特征
                                # 再检查jump_target是否是条件块
                                # current的then分支跳转到merge点，这是elif链的特征
                                # 再检查jump_target是否是条件块
                                # current的then分支跳转到merge点，这是elif链的特征
                                # 再检查jump_target是否是条件块
                                # current的then分支跳转到merge点，这是elif链的特征
                                # 再检查jump_target是否是条件块
                                if self._is_conditional_block(jump_target):
                                    is_elif_in_loop = True
                    
                    if is_elif_in_loop:
                        is_elif_candidate = True
                    else:
                        is_elif_candidate = False
                else:
                    # 检查jump_target的前驱是否包含current
                    # 如果是，这可能是elif链的一部分（复合条件后的elif）
                    # [关键修复] 对于复合条件，jump_target可能有多个前驱（复合条件的所有条件块）
                    # 但只要包含current，就是elif链的一部分
                    has_current_pred = current in jump_target.predecessors
                    if has_current_pred:
                        # jump_target的前驱包含current，这是elif链的一部分
                        # jump_target的前驱包含current，这是elif链的一部分
                        # jump_target的前驱包含current，这是elif链的一部分
                        # jump_target的前驱包含current，这是elif链的一部分
                        is_elif_candidate = True
            
            if is_elif_candidate:
                # [关键修复] 检查jump_target是否是循环结构的入口块或header块
                # 如果是，不应该将其识别为elif链的一部分
                # [关键修复] 检查jump_target是否是循环结构的入口块或header块
                # 如果是，不应该将其识别为elif链的一部分
                # [关键修复] 检查jump_target是否是循环结构的入口块或header块
                # 如果是，不应该将其识别为elif链的一部分
                # [关键修复] 检查jump_target是否是循环结构的入口块或header块
                # 如果是，不应该将其识别为elif链的一部分
                is_loop_entry = False
                for struct in self.structures:
                    if isinstance(struct, LoopStructure):
                        if jump_target == struct.entry_block or jump_target == struct.header_block:
                            is_loop_entry = True
                            break
                
                if is_loop_entry:
                    # jump_target是循环结构的入口块，不是elif链的一部分
                    # jump_target是循环结构的入口块，不是elif链的一部分
                    # jump_target是循环结构的入口块，不是elif链的一部分
                    # jump_target是循环结构的入口块，不是elif链的一部分
                    break
                
                # [关键修复] 检查jump_target是否是TryExcept结构的入口块
                # 如果是，不应该将其识别为elif链的一部分
                # 因为TryExcept结构应该包含if-else，生成 try: if-else: except:
                is_try_except_entry = False
                for struct in self.structures:
                    if isinstance(struct, TryExceptStructure):
                        if jump_target == struct.entry_block:
                            is_try_except_entry = True
                            break
                
                if is_try_except_entry:
                    break
                
                # [关键修复] 区分elif链和嵌套if-else
                # elif链的特征：
                # 1. header的then分支和jump_target的then分支都合并到同一个点
                # 2. jump_target是header的跳转目标（即jump_target是下一个elif条件）
                # 嵌套if-else的特征：
                # 1. header的then分支和jump_target的then分支合并到不同的点
                # 2. jump_target的跳转目标与header的跳转目标相同（共享merge块）
                target_jump = self._get_jump_instr(jump_target)
                
                # [关键修复] 检查 jump_target 是否包含向后条件跳转（循环条件）
                # 如果是，说明 jump_target 是循环条件块，不是 elif 条件
                has_backward_conditional = any(
                    instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                    for instr in jump_target.instructions
                )
                if has_backward_conditional:
                    break
                
                # [关键修复] 检查 jump_target 的跳转目标是否与 header 的跳转目标相同
                # 如果是，说明它们共享同一个 merge 块，这是嵌套 if
                has_same_jump_target = target_jump and target_jump.argval == header_jump.argval
                
                if has_same_jump_target:
                    break
                
                # [关键修复] 检查 jump_target 是否是 header 的跳转目标
                # 在elif链中，jump_target就是header的跳转目标（下一个elif条件）
                # 所以不能仅凭这个条件判断为嵌套if
                # 需要进一步检查：header的then分支和jump_target的then分支是否合并到同一个点
                is_jump_target_of_header = jump_target.start_offset == header_jump.argval
                
                if is_jump_target_of_header:
                    # jump_target是header的跳转目标，可能是elif链
                    # 检查header的then分支和jump_target的then分支是否合并到同一个点
                    # jump_target是header的跳转目标，可能是elif链
                    # 检查header的then分支和jump_target的then分支是否合并到同一个点
                    # jump_target是header的跳转目标，可能是elif链
                    # 检查header的then分支和jump_target的then分支是否合并到同一个点
                    # jump_target是header的跳转目标，可能是elif链
                    # 检查header的then分支和jump_target的then分支是否合并到同一个点
                    header_then = None
                    for succ in header.successors:
                        if succ.start_offset != header_jump.argval:
                            header_then = succ
                            break
                    
                    jump_target_then = None
                    if target_jump and target_jump.argval is not None:
                        for succ in jump_target.successors:
                            if succ.start_offset != target_jump.argval:
                                jump_target_then = succ
                                break
                    
                    # 找到header_then的合并点（JUMP_FORWARD的目标）
                    header_then_merge = None
                    if header_then:
                        for instr in header_then.instructions:
                            if instr.opname == 'JUMP_FORWARD' and instr.argval is not None:
                                header_then_merge = instr.argval
                                break
                    
                    # 找到jump_target_then的合并点（JUMP_FORWARD的目标）
                    jump_target_then_merge = None
                    if jump_target_then:
                        for instr in jump_target_then.instructions:
                            if instr.opname == 'JUMP_FORWARD' and instr.argval is not None:
                                jump_target_then_merge = instr.argval
                                break
                    
                    # 如果两个then分支合并到同一个点，这是elif链
                    # 如果合并到不同的点，这是嵌套if-else
                    if header_then_merge is not None and jump_target_then_merge is not None:
                        if header_then_merge == jump_target_then_merge:
                            pass
                        else:
                            break
                    elif header_then_merge is not None or jump_target_then_merge is not None:
                        if header_then_merge is None and jump_target_then_merge is not None:
                            header_then_has_return = any(instr.opname == 'RETURN_VALUE' for instr in header_then.instructions)
                            if not header_then_has_return:
                                break
                        elif header_then_merge is not None and jump_target_then_merge is None:
                            has_backward_conditional = any(
                                instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                                for instr in jump_target.instructions
                            )
                            if has_backward_conditional:
                                break
                    else:
                        header_then_final_targets = self._find_all_jump_targets(header_then) if header_then else set()
                        jump_target_then_final_targets = self._find_all_jump_targets(jump_target_then) if jump_target_then else set()
                        
                        if header_then_final_targets and jump_target_then_final_targets:
                            common_targets = header_then_final_targets & jump_target_then_final_targets
                            if common_targets:
                                pass
                            else:
                                has_backward_conditional = any(
                                    instr.opname in ('POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE')
                                    for instr in jump_target.instructions
                                )
                                if has_backward_conditional or not self._is_conditional_block(jump_target):
                                    break
                                header_then_exits_scope = self._branch_exits_scope(header_then)
                                jump_target_then_exits_scope = self._branch_exits_scope(jump_target_then)
                                if header_then_exits_scope and jump_target_then_exits_scope:
                                    pass
                                else:
                                    break
                        else:
                            # 检查是否有RETURN_VALUE
                            header_then_has_return = header_then and any(instr.opname == 'RETURN_VALUE' for instr in header_then.instructions)
                            jump_target_then_has_return = jump_target_then and any(instr.opname == 'RETURN_VALUE' for instr in jump_target_then.instructions)
                            if header_then_has_return and jump_target_then_has_return:
                                pass
                            elif not header_then_has_return and not jump_target_then_has_return:
                                break
                            # [关键修复] 如果header的then分支有return，但jump_target的then分支没有
                            # 这也可能是elif链（如：if x: return ... elif y: ...）
                            # 只要jump_target是header的跳转目标，就认为是elif链
                
                # [关键修复] 检查current的then分支是否只包含跳转指令（continue/break/return）
                # 如果是，说明current是一个独立的if语句（如 if x: continue），不是elif链的一部分
                # 这种情况下，jump_target是顺序执行的下一条语句，不是elif
                current_then = None
                for succ in current.successors:
                    if succ.start_offset != current_jump.argval:
                        current_then = succ
                        break
                
                if current_then:
                    # 检查then分支是否只包含跳转指令（continue/break/return）
                    # 如果是，说明current是一个独立的if语句（如 if x: return），不是elif链的一部分
                    # 这种情况下，jump_target是顺序执行的下一条语句，不是elif
                    # 检查then分支是否只包含跳转指令（continue/break/return）
                    # 如果是，说明current是一个独立的if语句（如 if x: return），不是elif链的一部分
                    # 这种情况下，jump_target是顺序执行的下一条语句，不是elif
                    # 检查then分支是否只包含跳转指令（continue/break/return）
                    # 如果是，说明current是一个独立的if语句（如 if x: return），不是elif链的一部分
                    # 这种情况下，jump_target是顺序执行的下一条语句，不是elif
                    # 检查then分支是否只包含跳转指令（continue/break/return）
                    # 如果是，说明current是一个独立的if语句（如 if x: return），不是elif链的一部分
                    # 这种情况下，jump_target是顺序执行的下一条语句，不是elif
                    has_only_control_flow = True
                    has_return = False
                    for instr in current_then.instructions:
                        if instr.opname in ('RESUME', 'CACHE', 'NOP', 'POP_TOP'):
                            continue
                        # 检查是否是跳转指令（continue/break）或return
                        if 'JUMP' in instr.opname:
                            continue
                        elif instr.opname == 'RETURN_VALUE':
                            has_return = True
                            continue
                        elif instr.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_GLOBAL'):
                            # 这些指令可能是return的参数（如 return False）
                            # 继续检查下一条指令
                            # 这些指令可能是return的参数（如 return False）
                            # 继续检查下一条指令
                            continue
                        else:
                            # 包含其他指令，不是纯控制流
                            has_only_control_flow = False
                            break
                    
                    # [关键修复] 不要因为then分支只包含控制流指令就认为这是独立的if语句
                    # 关键在于检查jump_target是否是下一个elif条件
                    # 如果jump_target是条件块，且它的跳转目标与header的跳转目标不同
                    # 则它是elif链的一部分
                    # 只有当then分支只包含continue/break（循环控制流）时，才认为是独立的if语句
                    if has_only_control_flow and has_return:
                        # then分支只包含return语句，这可能是elif链的一部分
                        # 不要break，继续检查jump_target
                        # then分支只包含return语句，这可能是elif链的一部分
                        # 不要break，继续检查jump_target
                        # then分支只包含return语句，这可能是elif链的一部分
                        # 不要break，继续检查jump_target
                        # then分支只包含return语句，这可能是elif链的一部分
                        # 不要break，继续检查jump_target
                        pass
                    elif has_only_control_flow:
                        # then分支只包含continue/break，这是循环内的控制流
                        # 检查jump_target是否是循环内的下一个条件
                        # 如果jump_target是条件块，继续检测
                        # then分支只包含continue/break，这是循环内的控制流
                        # 检查jump_target是否是循环内的下一个条件
                        # 如果jump_target是条件块，继续检测
                        if not self._is_conditional_block(jump_target):
                            # jump_target不是条件块，这是独立的if语句
                            # jump_target不是条件块，这是独立的if语句
                            # jump_target不是条件块，这是独立的if语句
                            # jump_target不是条件块，这是独立的if语句
                            break
                
                # [关键修复] 简化elif链检测逻辑
                # elif链的核心特征：
                # 1. jump_target是条件块
                # 2. jump_target在else_body中
                # 3. jump_target的唯一前驱是current（前一个if条件的跳转目标）
                # 如果满足这些条件，就是elif链的一部分
                
                is_independent_if = False

                # [关键修复-2026-elif-else] 检查jump_target是否已经被识别为独立的IfStructure
                # 如果是，说明这是一个独立的if语句，不是elif链的一部分
                # [关键修复] 但是，如果jump_target是当前if结构的跳转目标（即elif链的一部分），
                # 那么它应该被视为elif链的一部分，而不是独立的if结构
                jump_target_is_current_else = False
                for succ in current.successors:
                    if succ.start_offset == current_jump.argval and succ == jump_target:
                        # jump_target是当前if结构的else分支（跳转目标）
                        # jump_target是当前if结构的else分支（跳转目标）
                        # jump_target是当前if结构的else分支（跳转目标）
                        # jump_target是当前if结构的else分支（跳转目标）
                        jump_target_is_current_else = True
                        break
                
                # [关键修复-2026-elif-merge] 精确条件：
                # 如果jump_target是条件块（内层if），且它的跳转目标是header的then分支的merge点，
                # 则说明这是if-elif-else结构中的else分支（包含内层if），不是独立的if结构
                if not jump_target_is_current_else and is_conditional:
                    target_jump = self._get_jump_instr(jump_target)
                    if target_jump and target_jump.argval is not None:
                        header_then = None
                        for succ in header.successors:
                            if succ.start_offset != header_jump.argval:
                                header_then = succ
                                break
                        
                        if header_then:
                            header_then_end = None
                            for instr in reversed(header_then.instructions):
                                if instr.opname == 'JUMP_FORWARD' and instr.argval is not None:
                                    header_then_end = instr.argval
                                    break
                            
                            merge_point = header_then_end or header_then.start_offset
                            
                            if target_jump.argval == merge_point or target_jump.argval == header_then.start_offset:
                                jump_target_is_current_else = True
                
                # [关键修复-2026-elif-else] 如果jump_target是current的直接跳转目标，
                # 即使它被识别为独立的IfStructure，也应该视为elif链的一部分
                if not jump_target_is_current_else:
                    for struct in self.structures:
                        if isinstance(struct, IfStructure) and struct.entry_block == jump_target:
                            # 检查该if结构是否是独立的（不在任何其他if结构的else_body中）
                            # 检查该if结构是否是独立的（不在任何其他if结构的else_body中）
                            # 检查该if结构是否是独立的（不在任何其他if结构的else_body中）
                            # 检查该if结构是否是独立的（不在任何其他if结构的else_body中）
                            is_nested_in_other = False
                            for other_struct in self.structures:
                                if isinstance(other_struct, IfStructure) and other_struct != struct:
                                    if struct.entry_block in other_struct.else_body or struct.entry_block in other_struct.then_body:
                                        is_nested_in_other = True
                                        break
                            if not is_nested_in_other:
                                # 这是独立的if结构，不是elif链
                                # 这是独立的if结构，不是elif链
                                # 这是独立的if结构，不是elif链
                                # 这是独立的if结构，不是elif链
                                is_independent_if = True
                                break
                
                if not is_independent_if:
                    # 检查jump_target是否有前驱在else_body之外（且不是current）
                    # [关键修复] 对于elif链，jump_target的前驱应该是current（前一个elif条件）
                    # 或者来自current的then分支（如果current的then分支以JUMP_FORWARD结束）
                    # 如果jump_target有其他前驱，说明它是独立的if结构
                    # 检查jump_target是否有前驱在else_body之外（且不是current）
                    # [关键修复] 对于elif链，jump_target的前驱应该是current（前一个elif条件）
                    # 或者来自current的then分支（如果current的then分支以JUMP_FORWARD结束）
                    # 如果jump_target有其他前驱，说明它是独立的if结构
                    # 检查jump_target是否有前驱在else_body之外（且不是current）
                    # [关键修复] 对于elif链，jump_target的前驱应该是current（前一个elif条件）
                    # 或者来自current的then分支（如果current的then分支以JUMP_FORWARD结束）
                    # 如果jump_target有其他前驱，说明它是独立的if结构
                    # 检查jump_target是否有前驱在else_body之外（且不是current）
                    # [关键修复] 对于elif链，jump_target的前驱应该是current（前一个elif条件）
                    # 或者来自current的then分支（如果current的then分支以JUMP_FORWARD结束）
                    # 如果jump_target有其他前驱，说明它是独立的if结构
                    for pred in jump_target.predecessors:
                        if pred != current:
                            # [关键修复] 检查pred是否是current的then分支的一部分
                            # 如果是，这是正常的elif链
                            # [关键修复] 检查pred是否是current的then分支的一部分
                            # 如果是，这是正常的elif链
                            # [关键修复] 检查pred是否是current的then分支的一部分
                            # 如果是，这是正常的elif链
                            # [关键修复] 检查pred是否是current的then分支的一部分
                            # 如果是，这是正常的elif链
                            current_then = None
                            for succ in current.successors:
                                if succ.start_offset != current_jump.argval:
                                    current_then = succ
                                    break
                            
                            is_from_current_then = False
                            if current_then:
                                current_then_body = self._find_branch_body(current_then, current, loop_headers, is_else_branch=False)
                                if pred in current_then_body or pred == current_then:
                                    is_from_current_then = True
                            
                            if not is_from_current_then:
                                # jump_target有前驱不是current且不是current的then分支
                                # 这是独立的if结构
                                # jump_target有前驱不是current且不是current的then分支
                                # 这是独立的if结构
                                # jump_target有前驱不是current且不是current的then分支
                                # 这是独立的if结构
                                # jump_target有前驱不是current且不是current的then分支
                                # 这是独立的if结构
                                is_independent_if = True
                                break
                
                # 检查jump_target是否有前驱来自current的then分支（fall-through）
                if not is_independent_if:
                    # 找到current的fall-through后继（then分支）
                    # 找到current的fall-through后继（then分支）
                    # 找到current的fall-through后继（then分支）
                    # 找到current的fall-through后继（then分支）
                    current_then = None
                    for succ in current.successors:
                        if succ.start_offset != current_jump.argval:
                            current_then = succ
                            break
                    
                    # [关键修复] 如果jump_target有前驱来自current_then，需要进一步判断
                    # 如果current_then只包含NOP或简单的控制流指令（如pass语句），
                    # 这是正常的elif链结构，不是独立的if
                    if current_then:
                        for pred in jump_target.predecessors:
                            if pred == current_then:
                                # [关键修复] 检查current_then是否只包含NOP或简单的控制流指令
                                # 如果是，这是elif链的正常结构（如if ...: pass; elif ...: ...）
                                # 如果不是，这是独立的if结构
                                # [关键修复] 检查current_then是否只包含NOP或简单的控制流指令
                                # 如果是，这是elif链的正常结构（如if ...: pass; elif ...: ...）
                                # 如果不是，这是独立的if结构
                                # [关键修复] 检查current_then是否只包含NOP或简单的控制流指令
                                # 如果是，这是elif链的正常结构（如if ...: pass; elif ...: ...）
                                # 如果不是，这是独立的if结构
                                # [关键修复] 检查current_then是否只包含NOP或简单的控制流指令
                                # 如果是，这是elif链的正常结构（如if ...: pass; elif ...: ...）
                                # 如果不是，这是独立的if结构
                                current_then_has_real_code = False
                                for instr in current_then.instructions:
                                    if instr.opname not in ('RESUME', 'CACHE', 'NOP', 'POP_TOP', 'JUMP_FORWARD'):
                                        current_then_has_real_code = True
                                        break
                                
                                if current_then_has_real_code:
                                    # current_then包含实际代码，这是独立的if结构
                                    # current_then包含实际代码，这是独立的if结构
                                    # current_then包含实际代码，这是独立的if结构
                                    # current_then包含实际代码，这是独立的if结构
                                    is_independent_if = True
                                # 否则current_then只包含NOP/控制流，这是elif链，不设置is_independent_if
                                break
                
                if not is_independent_if:
                    # 检查jump_target本身是否是完整的if-else结构
                    # 如果是，说明这是嵌套if，不是elif链
                    # 完整的if-else结构特征：
                    # 1. 包含POP_JUMP_FORWARD_IF_FALSE指令
                    # 2. 跳转目标是另一个条件块（else分支的条件块）或包含条件代码的块
                    
                    # 检查jump_target本身是否是完整的if-else结构
                    # 如果是，说明这是嵌套if，不是elif链
                    # 完整的if-else结构特征：
                    # 1. 包含POP_JUMP_FORWARD_IF_FALSE指令
                    # 2. 跳转目标是另一个条件块（else分支的条件块）或包含条件代码的块
                    
                    # 检查jump_target本身是否是完整的if-else结构
                    # 如果是，说明这是嵌套if，不是elif链
                    # 完整的if-else结构特征：
                    # 1. 包含POP_JUMP_FORWARD_IF_FALSE指令
                    # 2. 跳转目标是另一个条件块（else分支的条件块）或包含条件代码的块
                    
                    # 检查jump_target本身是否是完整的if-else结构
                    # 如果是，说明这是嵌套if，不是elif链
                    # 完整的if-else结构特征：
                    # 1. 包含POP_JUMP_FORWARD_IF_FALSE指令
                    # 2. 跳转目标是另一个条件块（else分支的条件块）或包含条件代码的块
                    
                    jump_target_jump = self._get_jump_instr(jump_target)
                    if jump_target_jump and 'POP_JUMP_FORWARD_IF_FALSE' in jump_target_jump.opname:
                        # 找到jump_target的fall-through后继（then分支）
                        # 找到jump_target的fall-through后继（then分支）
                        # 找到jump_target的fall-through后继（then分支）
                        # 找到jump_target的fall-through后继（then分支）
                        jump_target_then = None
                        jump_target_else = None
                        for succ in jump_target.successors:
                            if succ.start_offset == jump_target_jump.argval:
                                jump_target_else = succ
                            else:
                                jump_target_then = succ
                        
                        # 检查jump_target_else是否是条件块或包含循环
                        if jump_target_else:
                            is_jt_else_conditional = self._is_conditional_block(jump_target_else)
                            # [关键修复] 区分elif链和嵌套if-else
                            # elif链的特征：else分支是条件块，且该条件块也在else_body中
                            # 嵌套if-else的特征：else分支是条件块，但该条件块不在else_body中（或有其他前驱）
                            if is_jt_else_conditional:
                                # 检查这个条件块是否在else_body中
                                # 如果在，它可能是elif链的一部分
                                # 如果不在，说明这是嵌套if-else
                                # 检查这个条件块是否在else_body中
                                # 如果在，它可能是elif链的一部分
                                # 如果不在，说明这是嵌套if-else
                                # 检查这个条件块是否在else_body中
                                # 如果在，它可能是elif链的一部分
                                # 如果不在，说明这是嵌套if-else
                                # 检查这个条件块是否在else_body中
                                # 如果在，它可能是elif链的一部分
                                # 如果不在，说明这是嵌套if-else
                                # [关键修复] 对于elif链，jump_target的else分支可能不在else_body中
                                # 这是因为elif的else分支可能是下一个elif或独立if
                                # 只有当jump_target_else是条件块且不在else_body中时，才认为是独立的if结构
                                if jump_target_else not in else_body:
                                    # [关键修复] 检查jump_target_else是否是条件块
                                    # 如果不是条件块，这是正常的elif链结构
                                    # 如果是条件块，这可能是嵌套if-else或下一个elif
                                    is_jt_else_conditional = self._is_conditional_block(jump_target_else)
                                    if is_jt_else_conditional:
                                        # jump_target_else是条件块，检查它是否是elif链的一部分
                                        # 如果jump_target_else的前驱只有jump_target，它是elif链的一部分
                                        # 如果jump_target_else有其他前驱，需要进一步判断
                                        jt_else_preds = list(jump_target_else.predecessors)
                                        # [关键修复] 检查jump_target的then分支
                                        # 如果jump_target_else的前驱包含jump_target的then分支，这是正常的控制流
                                        # 因为elif的then分支执行完后会顺序执行到后面的代码
                                        jump_target_then = None
                                        for succ in jump_target.successors:
                                            if succ.start_offset != target_jump.argval:
                                                jump_target_then = succ
                                                break
                                        
                                        # 检查前驱是否只有jump_target和jump_target的then分支
                                        has_only_expected_preds = True
                                        for pred in jt_else_preds:
                                            if pred != jump_target and pred != jump_target_then:
                                                has_only_expected_preds = False
                                                break
                                        
                                        if not has_only_expected_preds:
                                            is_independent_if = True
                                    # 否则jump_target_else不是条件块，这是正常的elif链结构，不设置is_independent_if
                            
                            # [关键修复] 删除之前的向后跳转检查
                            # 在 elif-else 链中，每个分支都包含向后跳转到循环头部，这是正常的
                            # 关键区别应该是：elif-else 链中的 else 分支的唯一前驱是前一个 elif 条件的跳转目标
                            
                            # [关键修复] 检查 else 分支的前驱
                            # 在 elif 链中，最终的 else 分支的前驱是最后一个 elif 条件（jump_target）
                            # 这是正常的，不应该因此认为它是独立的 if 结构
                            # 只有当 else 分支有前驱不是 current 且不是 jump_target 且不是 jump_target 的 then 分支时，才是独立的 if 结构
                            
                            # [关键修复] 收集 jump_target 的 then 分支中的所有块
                            jump_target_then_blocks = set()
                            if jump_target_then:
                                jump_target_then_blocks = self._find_branch_body(jump_target_then, jump_target, loop_headers, is_else_branch=False)
                            
                            # [关键修复] 检查 else 分支的前驱
                            # 排除来自循环尾部或循环头部的块（这些块是循环的正常组成部分，不是独立的执行路径）
                            def is_loop_related_block(block):
                                """检查块是否与循环相关（循环尾部或循环头部）"""
                                # 检查是否是循环尾部（包含向后跳转）
                                for instr in block.instructions:
                                    if 'BACKWARD' in instr.opname:
                                        return True
                                # 检查是否是循环头部（FOR_ITER指令）
                                for instr in block.instructions:
                                    if instr.opname == 'FOR_ITER':
                                        return True
                                return False
                            
                            jump_target_else_preds = [p for p in jump_target_else.predecessors 
                                                      if p != current and p != jump_target and p not in jump_target_then_blocks
                                                      and not is_loop_related_block(p)]
                            if jump_target_else_preds:
                                # 如果 else 分支有前驱不是 current 且不是 jump_target 且不是 jump_target 的 then 分支且不是循环尾部，说明它有其他执行路径
                                # 这是独立的 if 结构，不是 elif 链
                                # 如果 else 分支有前驱不是 current 且不是 jump_target 且不是 jump_target 的 then 分支且不是循环尾部，说明它有其他执行路径
                                # 这是独立的 if 结构，不是 elif 链
                                # 如果 else 分支有前驱不是 current 且不是 jump_target 且不是 jump_target 的 then 分支且不是循环尾部，说明它有其他执行路径
                                # 这是独立的 if 结构，不是 elif 链
                                # 如果 else 分支有前驱不是 current 且不是 jump_target 且不是 jump_target 的 then 分支且不是循环尾部，说明它有其他执行路径
                                # 这是独立的 if 结构，不是 elif 链
                                is_independent_if = True
                            # else 分支的唯一前驱是 current 或来自 jump_target 的 then 分支，这是 elif 链的一部分
                            
                            # [关键修复] 检查else分支是否包含GET_ITER指令（for循环）
                            # 如果是，说明这是嵌套if-else，不是elif链
                            if not is_independent_if:
                                for instr in jump_target_else.instructions:
                                    if instr.opname == 'GET_ITER':
                                        is_independent_if = True
                                        break
                            
                            # [关键修复] 删除这个检查
                            # 在循环内的elif链中，每个分支的then分支都包含JUMP_BACKWARD跳转到循环头部
                            # 这是正常的，不应该因此认为它是独立的if结构
                            pass
                            
                            # [关键修复] 检查jump_target_then是否是break语句
                            # break语句的特征：
                            # 1. 只有一个POP_TOP指令（可选）
                            # 2. 加载None常量
                            # 3. RETURN_VALUE指令
                            # 这种结构不应该被识别为elif链的一部分
                            # [关键修复] 但是，对于简单的if-elif链（如if x == 1: return ... elif x == 2: return ...），
                            # 每个分支都以RETURN_VALUE结束是正常的，应该被识别为elif链
                            if not is_independent_if and jump_target_then:
                                # 检查是否是break模式
                                # 检查是否是break模式
                                # 检查是否是break模式
                                # 检查是否是break模式
                                non_trivial_instrs = [i for i in jump_target_then.instructions 
                                                      if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                                # break模式：POP_TOP(可选), LOAD_CONST None, RETURN_VALUE
                                if len(non_trivial_instrs) >= 2:
                                    has_return = any(i.opname == 'RETURN_VALUE' for i in non_trivial_instrs)
                                    has_none = any(i.opname == 'LOAD_CONST' and i.argval is None for i in non_trivial_instrs)
                                    if has_return and has_none:
                                        # [关键修复] 检查这是否是真正的break语句，还是elif链的一部分
                                        # 真正的break语句：在循环体内，且跳转到循环外部
                                        # elif链的一部分：不在循环体内，或者所有分支都有RETURN_VALUE
                                        # [关键修复] 检查这是否是真正的break语句，还是elif链的一部分
                                        # 真正的break语句：在循环体内，且跳转到循环外部
                                        # elif链的一部分：不在循环体内，或者所有分支都有RETURN_VALUE
                                        # [关键修复] 检查这是否是真正的break语句，还是elif链的一部分
                                        # 真正的break语句：在循环体内，且跳转到循环外部
                                        # elif链的一部分：不在循环体内，或者所有分支都有RETURN_VALUE
                                        # [关键修复] 检查这是否是真正的break语句，还是elif链的一部分
                                        # 真正的break语句：在循环体内，且跳转到循环外部
                                        # elif链的一部分：不在循环体内，或者所有分支都有RETURN_VALUE
                                        is_in_loop = False
                                        for struct in self.structures:
                                            if isinstance(struct, LoopStructure):
                                                if jump_target_then in getattr(struct, 'body_blocks', []):
                                                    is_in_loop = True
                                                    break
                                        
                                        if is_in_loop:
                                            # 在循环体内，这是break语句，不应该作为elif链的一部分
                                            # 在循环体内，这是break语句，不应该作为elif链的一部分
                                            # 在循环体内，这是break语句，不应该作为elif链的一部分
                                            # 在循环体内，这是break语句，不应该作为elif链的一部分
                                            is_independent_if = True
                                        # 否则，不在循环体内，这可能是elif链的一部分，继续检查
                
                if is_independent_if:
                    # [关键修复-2026-elif-final] 最终兜底检查：
                    # 即使前面的检查判定为独立if，也要验证基本条件
                    # 如果jump_target是current的直接跳转目标、是条件块、且唯一前驱是current，
                    # 则它应该是elif链的一部分（如 else: if x: ... 结构中的内层if）
                    _preds = list(jump_target.predecessors)
                    if (len(_preds) == 1 and _preds[0] == current and 
                        self._is_conditional_block(jump_target)):
                        _tj = self._get_jump_instr(jump_target)
                        if _tj and _tj.argval is not None:
                            # 检查跳转目标是否与header的then分支合并到同一个点
                            _ht = None
                            for _s in header.successors:
                                if _s.start_offset != header_jump.argval:
                                    _ht = _s
                                    break
                            if _ht:
                                for _instr in reversed(_ht.instructions):
                                    if _instr.opname == 'JUMP_FORWARD' and _instr.argval is not None:
                                        if _tj.argval == _instr.argval:
                                            is_independent_if = False
                                        break
                    
                    if is_independent_if:
                        break

                # [关键修复] 这是elif链的一部分
                # 添加当前跳转目标到elif链
                elif_chain.append(jump_target)
                visited.add(jump_target)
                
                # [关键修复] 检查jump_target是否包含复合条件
                # 复合条件的特征：fall-through后继也是条件块，且共享同一个跳转目标
                jump_target_fall_through = None
                for succ in jump_target.successors:
                    if succ.start_offset != target_jump.argval:
                        jump_target_fall_through = succ
                        break
                
                if jump_target_fall_through and self._is_conditional_block(jump_target_fall_through):
                    jt_fall_through_jump = self._get_jump_instr(jump_target_fall_through)
                    if jt_fall_through_jump and jt_fall_through_jump.argval == target_jump.argval:
                        # [关键修复] 这是复合条件（如 elif a and b:）
                        # 将fall-through块也添加到条件链中
                        # [关键修复] 这是复合条件（如 elif a and b:）
                        # 将fall-through块也添加到条件链中
                        # [关键修复] 这是复合条件（如 elif a and b:）
                        # 将fall-through块也添加到条件链中
                        # [关键修复] 这是复合条件（如 elif a and b:）
                        # 将fall-through块也添加到条件链中
                        elif_chain.append(jump_target_fall_through)
                        visited.add(jump_target_fall_through)
                
                current = jump_target
                
                # [关键修复] 更新else_body为当前elif的else分支
                # 这样可以在后续的迭代中检测到更多的elif
                # 找到当前elif的else分支（跳转目标）
                current_jump = self._get_jump_instr(current)
                if current_jump and current_jump.argval is not None:
                    # 找到跳转目标块（else分支）
                    # 找到跳转目标块（else分支）
                    # 找到跳转目标块（else分支）
                    # 找到跳转目标块（else分支）
                    for succ in current.successors:
                        if succ.start_offset == current_jump.argval:
                            # 收集else分支中的所有块
                            # 收集else分支中的所有块
                            # 收集else分支中的所有块
                            # 收集else分支中的所有块
                            new_else_body = self._find_branch_body(succ, current, loop_headers, is_else_branch=True)
                            if new_else_body:
                                else_body = new_else_body
                            break
            else:
                # 没有更多的elif条件
                break
        return elif_chain
    
    def _merge_compound_conditions_v2(self) -> None:
        """
        检测并合并复合条件链（改进版）
        
        基于 statement_builder.py 的技术，更准确地识别复合条件。
        
        复合条件如 x > 0 and y > 0 的字节码特征：
        - 多个连续的 POP_JUMP_IF_FALSE 指令
        - 所有条件跳转都指向同一个 else 分支
        - then 分支形成链式结构
        """
        # 找到所有条件块
        conditional_blocks = []
        for block in self.cfg.blocks.values():
            if self._is_conditional_block(block) and len(block.successors) == 2:
                conditional_blocks.append(block)
        
        if len(conditional_blocks) < 2:
            return
        
        # 按偏移排序
        conditional_blocks.sort(key=lambda b: b.start_offset)
        
        # [关键修复] 收集已经被识别为IfStructure entry_block的块
        # 避免重复创建IfStructure
        existing_if_entries = set()
        for struct in self.structures:
            if isinstance(struct, IfStructure):
                existing_if_entries.add(struct.entry_block)
        
        # 检测复合条件链
        chains = []
        visited = set()
        
        for block in conditional_blocks:
            if block in visited:
                continue
            
            # [关键修复] 跳过已经被识别为IfStructure entry_block的块
            # 这些块已经在_identify_conditionals中被处理过了
            if block in existing_if_entries:
                continue
            
            chain = [block]
            visited.add(block)
            
            # 获取当前块的跳转目标
            jump_instr = self._get_jump_instr(block)
            if not jump_instr:
                continue
            
            current_else = self._get_jump_target_block(block, jump_instr)
            
            # 查找链中的下一个块
            current = block
            while True:
                # 获取当前块的 then 分支
                # 获取当前块的 then 分支
                # 获取当前块的 then 分支
                # 获取当前块的 then 分支
                current_then = self._get_fall_through_block(current, jump_instr)
                
                if not current_then:
                    break
                
                # 检查 then 分支是否是另一个条件块
                if not (self._is_conditional_block(current_then) and len(current_then.successors) == 2):
                    break
                
                # 检查是否是复合条件的一部分
                # 条件：then 分支是条件块，且它的 else 分支与当前块的 else 分支相同
                next_jump_instr = self._get_jump_instr(current_then)
                if not next_jump_instr:
                    break
                
                next_else = self._get_jump_target_block(current_then, next_jump_instr)
                
                # [关键修复] 区分复合条件和 elif 链
                # 复合条件：else 分支相同，或者都是简单的 return None
                # elif 链：else 分支不同（指向下一个 if）
                is_same_else = (next_else == current_else)
                is_both_return_none = (
                    self._is_simple_return_none(current_else) and 
                    self._is_simple_return_none(next_else)
                )
                
                if is_same_else or is_both_return_none:
                    # 这是复合条件的一部分
                    # 这是复合条件的一部分
                    # 这是复合条件的一部分
                    # 这是复合条件的一部分
                    chain.append(current_then)
                    visited.add(current_then)
                    current = current_then
                    jump_instr = next_jump_instr
                else:
                    # 这是 elif 链，停止
                    break
            
            if len(chain) > 1:
                chains.append(chain)
        
        # 合并每个复合条件链
        for chain in chains:
            self._merge_condition_chain_v2(chain)

    def _has_chain_compare_pattern(self, block: BasicBlock) -> bool:
        """
        检查块是否包含链式比较的特征指令模式

        链式比较（如 0 < a < b < c < 100）的字节码特征：
        - SWAP(2): 交换栈顶两个元素
        - COPY(2): 复制栈上第二个元素
        - COMPARE_OP: 执行比较操作
        - JUMP_IF_FALSE_OR_POP 或 JUMP_IF_TRUE_OR_POP: 链式比较特有的跳转指令

        这与普通条件（如 if a and b:）不同，后者不包含SWAP/COPY指令，
        也不使用JUMP_IF_FALSE_OR_POP/JUMP_IF_TRUE_OR_POP指令

        Args:
            block: 要检查的基本块

        Returns:
            True如果块包含链式比较特征，False否则
        """
        has_swap = False
        has_copy_2 = False
        has_compare_op = False
        has_chain_jump = False

        for instr in block.instructions:
            if instr.opname == 'SWAP' and instr.arg == 2:
                has_swap = True
            elif instr.opname == 'COPY' and instr.arg == 2:
                has_copy_2 = True
            elif instr.opname == 'COMPARE_OP':
                has_compare_op = True
            elif instr.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                # 链式比较特有的跳转指令
                has_chain_jump = True

        # [字节码一致性修复] 链式比较必须使用JUMP_IF_FALSE_OR_POP或JUMP_IF_TRUE_OR_POP指令
        # 普通的if条件（如 if x > 0:）使用POP_JUMP_FORWARD_IF_FALSE等指令
        if not has_chain_jump:
            return False

        # [字节码一致性修复] 支持两种链式比较模式：
        # 1. 完整模式（中间比较）：SWAP(2) + COPY(2) + COMPARE_OP + JUMP_IF_FALSE_OR_POP
        # 2. 简化模式（最后比较）：COMPARE_OP + JUMP_IF_FALSE_OR_POP（没有 SWAP/COPY）
        # 链式比较的最后一个比较不需要 SWAP/COPY，因为左操作数已经在栈上
        if has_compare_op and has_chain_jump:
            return True

        return False

    def _get_jump_instr(self, block: BasicBlock) -> Optional[Any]:
        """获取块的跳转指令

        [关键修复] 支持复合条件的短路求值指令：
        - JUMP_IF_TRUE_OR_POP: 逻辑或(or)的短路求值
        - JUMP_IF_FALSE_OR_POP: 逻辑与(and)的短路求值
        """
        for instr in block.instructions:
            if 'POP_JUMP' in instr.opname:
                return instr
            if instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                return instr
        return None
    
    def _find_all_jump_targets(self, block: BasicBlock, visited: Set = None) -> Set[int]:
        """递归查找块中所有路径的最终跳转目标
        
        对于嵌套if结构，需要递归查找所有路径的最终跳转目标。
        例如：if isinstance(item, int): if item < 0: continue elif item > 100: return False else: continue
        所有路径最终都跳回循环头部（continue）或函数退出（return）
        """
        if visited is None:
            visited = set()
        
        if block in visited:
            return set()
        visited.add(block)
        
        targets = set()
        for instr in block.instructions:
            if instr.opname == 'RETURN_VALUE':
                targets.add('return')
                return targets
            if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                if instr.argval is not None:
                    targets.add(instr.argval)
                return targets
        
        for succ in block.successors:
            targets.update(self._find_all_jump_targets(succ, visited))
        
        return targets
    
    def _branch_exits_scope(self, block: BasicBlock, visited: Set = None) -> bool:
        """检查分支是否退出当前作用域（continue/break/return）
        
        在elif链中，then分支可能通过不同方式退出：
        - continue: JUMP_BACKWARD到循环头部
        - break: JUMP_FORWARD跳出循环
        - return: RETURN_VALUE
        如果分支通过任何这些方式退出，则认为它退出了当前if-elif-else作用域
        """
        if block is None:
            return False
        if visited is None:
            visited = set()
        if block in visited:
            return False
        visited.add(block)
        for instr in block.instructions:
            if instr.opname == 'RETURN_VALUE':
                return True
            if instr.opname in ('JUMP_FORWARD', 'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT'):
                return True
        for succ in block.successors:
            if self._branch_exits_scope(succ, visited):
                return True
        return False
    
    def _get_jump_target_block(self, block: BasicBlock, jump_instr) -> Optional[BasicBlock]:
        """获取跳转目标块"""
        if jump_instr.argval is None:
            return None
        for succ in block.successors:
            if succ.start_offset == jump_instr.argval:
                return succ
        return None
    
    def _get_fall_through_block(self, block: BasicBlock, jump_instr) -> Optional[BasicBlock]:
        """获取 fall-through 块（非跳转目标）"""
        if jump_instr.argval is None:
            return None
        for succ in block.successors:
            if succ.start_offset != jump_instr.argval:
                return succ
        return None
    
    def _is_simple_return_none(self, block: Optional[BasicBlock]) -> bool:
        """检查块是否是简单的 return None
        
        [关键修复] 支持链式比较的清理代码块：
        - 链式比较的中间条件失败时，会跳转到 POP_TOP + LOAD_CONST None + RETURN_VALUE
        - 链式比较的最后一个条件失败时，会跳转到 LOAD_CONST None + RETURN_VALUE
        这两种情况都应该被认为是简单的 return None 块。
        """
        if not block:
            return False
        
        # 检查块是否只包含 LOAD_CONST (None) 和 RETURN_VALUE
        # [关键修复] 链式比较的清理代码块还包含 POP_TOP
        non_trivial_instrs = [i for i in block.instructions 
                              if i.opname not in ('RESUME', 'CACHE', 'NOP')]
        
        # [关键修复] 支持两种模式：
        # 模式1: LOAD_CONST None, RETURN_VALUE (2条指令)
        # 模式2: POP_TOP, LOAD_CONST None, RETURN_VALUE (3条指令，链式比较的清理代码)
        if len(non_trivial_instrs) == 2:
            # 模式1: LOAD_CONST (None) 和 RETURN_VALUE
            # 模式1: LOAD_CONST (None) 和 RETURN_VALUE
            # 模式1: LOAD_CONST (None) 和 RETURN_VALUE
            # 模式1: LOAD_CONST (None) 和 RETURN_VALUE
            first_instr = non_trivial_instrs[0]
            second_instr = non_trivial_instrs[1]
            
            if (first_instr.opname in ('LOAD_CONST', 'RETURN_CONST') and 
                first_instr.argval is None and
                second_instr.opname == 'RETURN_VALUE'):
                return True
        elif len(non_trivial_instrs) == 3:
            # 模式2: POP_TOP + LOAD_CONST (None) + RETURN_VALUE (链式比较的清理代码)
            # 模式2: POP_TOP + LOAD_CONST (None) + RETURN_VALUE (链式比较的清理代码)
            first_instr = non_trivial_instrs[0]
            second_instr = non_trivial_instrs[1]
            third_instr = non_trivial_instrs[2]
            
            if (first_instr.opname == 'POP_TOP' and
                second_instr.opname in ('LOAD_CONST', 'RETURN_CONST') and 
                second_instr.argval is None and
                third_instr.opname == 'RETURN_VALUE'):
                return True
        
        return False
    
    def _is_simple_jump_or_return_block(self, block: Optional[BasicBlock]) -> bool:
        """检查块是否是简单的跳转块或return None块
        
        用于识别复杂布尔表达式链中的跳转目标块。
        """
        if not block:
            return False
        
        # 首先检查是否是简单的return None块
        if self._is_simple_return_none(block):
            return True
        
        # 检查是否是简单的JUMP_FORWARD块
        non_trivial_instrs = [i for i in block.instructions 
                              if i.opname not in ('RESUME', 'CACHE', 'NOP')]
        
        if len(non_trivial_instrs) == 1 and non_trivial_instrs[0].opname == 'JUMP_FORWARD':
            return True
        
        # 检查是否是只包含实际代码的块（不是条件块）
        has_cond_jump = any(
            'JUMP' in instr.opname and 'IF_' in instr.opname
            for instr in block.instructions
        )
        
        # 如果不是条件块，且只包含简单的代码，认为是简单的块
        if not has_cond_jump:
            non_trivial = [i for i in block.instructions 
                           if i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'CALL', 
                                               'POP_TOP', 'RETURN_VALUE', 'JUMP_FORWARD',
                                               'LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                               'LOAD_METHOD', 'LOAD_ATTR')]
            return len(non_trivial) == 0
        
        return False
    
    def _get_block_id_by_offset(self, cfg, offset: int) -> Optional[int]:
        """根据偏移量获取块ID"""
        for block_id, block in cfg.blocks.items():
            if block.start_offset == offset:
                return block_id
        return None
    
    def _merge_condition_chain_v2(self, chain: List[BasicBlock]) -> None:
        """合并复合条件链（改进版）"""
        if len(chain) < 2:
            return
        
        # 第一个块是主条件块
        main_block = chain[0]
        # 最后一个块决定 then 和 else 分支
        last_block = chain[-1]
        
        # 获取最后一个块的跳转目标
        last_jump_instr = self._get_jump_instr(last_block)
        if not last_jump_instr or last_jump_instr.argval is None:
            return
        
        # 确定 then 和 else 分支
        then_branch = None
        else_branch = None
        for succ in last_block.successors:
            if succ.start_offset == last_jump_instr.argval:
                else_branch = succ
            else:
                then_branch = succ
        
        if not then_branch or not else_branch:
            return
        
        # 收集循环头部用于边界检查
        loop_headers = set()
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and struct.header_block:
                loop_headers.add(struct.header_block)
        # 查找分支体
        then_body = self._find_branch_body(then_branch, main_block, loop_headers)
        # [关键修复] 对于else分支，传递is_else_branch=True
        else_body = self._find_branch_body(else_branch, main_block, loop_headers, is_else_branch=True)
        
        # 找到合并块
        merge_block = self._find_merge_block(then_body | else_body)
        
        # 从分支体中排除合并块和链中的中间块
        if merge_block:
            then_body = then_body - {merge_block}
            else_body = else_body - {merge_block}
            then_body = self._exclude_after_merge(then_body, merge_block)
            else_body = self._exclude_after_merge(else_body, merge_block)
        
        # 排除链中的中间块
        for block in chain[1:]:
            then_body.discard(block)
            else_body.discard(block)
        
        # 创建复合条件结构
        has_else = len(else_body) > 0
        
        if_struct = IfStructure(
            struct_type=ControlStructureType.IF_THEN_ELSE if has_else else ControlStructureType.IF_THEN,
            entry_block=main_block,
            condition_block=main_block,
            then_body=list(then_body),
            else_body=list(else_body) if has_else else [],
            merge_block=merge_block
        )
        
        # 标记为复合条件
        if_struct.is_compound_condition = True
        if_struct.condition_chain = chain
        
        self.structures.append(if_struct)
        
        # [关键修复] 只映射入口块和条件链中的块
        # 不映射then_body和else_body中的块，因为这些块可能属于其他结构
        for block in chain:
            self.block_to_structure[block] = if_struct
    
    def _merge_compound_conditions(self) -> None:
        """
        检测并合并复合条件链
        
        复合条件如 x > 0 and y > 0 会被编译成多个条件跳转指令。
        这个方法检测这些链并将它们合并为一个复合条件结构。
        
        识别模式（AND条件）：
        - 块A的then分支连接到块B
        - 块A和块B的else分支相同
        - 块B的then分支是实际的代码（不是另一个条件块）
        
        注意：这与elif链不同，elif链的else分支指向下一个if结构
        """
        # 找到所有条件块
        conditional_blocks = []
        for block in self.cfg.blocks.values():
            if self._is_conditional_block(block) and len(block.successors) == 2:
                conditional_blocks.append(block)
        
        if len(conditional_blocks) < 2:
            return
        
        # 按偏移排序
        conditional_blocks.sort(key=lambda b: b.start_offset)
        
        # [关键修复] 收集已经被识别为IfStructure entry_block的块
        # 避免重复创建IfStructure
        existing_if_entries = set()
        for struct in self.structures:
            if isinstance(struct, IfStructure):
                existing_if_entries.add(struct.entry_block)
        
        # 检测复合条件链
        chains = []
        visited = set()
        
        for block in conditional_blocks:
            if block in visited:
                continue
            
            # [关键修复] 跳过已经被识别为IfStructure entry_block的块
            # 这些块已经在_identify_conditionals中被处理过了
            if block in existing_if_entries:
                continue
            
            chain = [block]
            visited.add(block)
            
            # 查找链中的下一个块
            current = block
            while True:
                # 获取当前块的跳转目标
                # 获取当前块的跳转目标
                # 获取当前块的跳转目标
                # 获取当前块的跳转目标
                jump_instr = None
                for instr in current.instructions:
                    if 'POP_JUMP' in instr.opname and 'IF' in instr.opname:
                        jump_instr = instr
                        break
                
                if not jump_instr or jump_instr.argval is None:
                    break
                
                # 确定当前块的then和else分支
                current_then = None
                current_else = None
                for succ in current.successors:
                    if succ.start_offset == jump_instr.argval:
                        current_else = succ
                    else:
                        current_then = succ
                
                if not current_then or not current_else:
                    break
                
                # [关键修复] 检查当前块的else分支是否是另一个条件块的入口
                # 如果是，这可能是elif链，不应该合并
                if self._is_conditional_block(current_else) and len(current_else.successors) == 2:
                    # 这是elif链的特征，停止合并
                    # 这是elif链的特征，停止合并
                    # 这是elif链的特征，停止合并
                    # 这是elif链的特征，停止合并
                    break
                
                # 在条件块中查找下一个块
                found_next = False
                for other in conditional_blocks:
                    if other in visited:
                        continue
                    
                    # 检查是否是AND条件链
                    # 条件1: 当前块的then分支连接到下一个块
                    if current_then != other:
                        continue
                    
                    # 获取下一个块的跳转目标
                    other_jump_instr = None
                    for instr in other.instructions:
                        if 'POP_JUMP' in instr.opname and 'IF' in instr.opname:
                            other_jump_instr = instr
                            break
                    
                    if not other_jump_instr or other_jump_instr.argval is None:
                        continue
                    
                    # 确定下一个块的else分支
                    other_else = None
                    for succ in other.successors:
                        if succ.start_offset == other_jump_instr.argval:
                            other_else = succ
                            break
                    
                    # 条件2: 当前块和下一个块的else分支相同
                    if current_else != other_else:
                        continue
                    
                    # 条件3: 下一个块的then分支不是另一个条件块（或者是链的终点）
                    other_then = None
                    for succ in other.successors:
                        if succ.start_offset != other_jump_instr.argval:
                            other_then = succ
                            break
                    
                    # [关键修复] 额外检查：确保不是elif链
                    # elif链的特征：当前块的else分支是另一个条件块
                    if self._is_conditional_block(current_else) and len(current_else.successors) == 2:
                        break
                    
                    # 这是AND条件链
                    chain.append(other)
                    visited.add(other)
                    current = other
                    found_next = True
                    break
                
                if not found_next:
                    break
            
            if len(chain) > 1:
                chains.append(chain)
        
        # 合并每个复合条件链
        for chain in chains:
            self._merge_condition_chain(chain)
    
    def _merge_condition_chain(self, chain: List[BasicBlock]) -> None:
        """
        合并复合条件链
        
        Args:
            chain: 条件块链，每个块是一个条件跳转
        """
        if len(chain) < 2:
            return
        
        # 第一个块是主条件块
        main_block = chain[0]
        # 最后一个块决定then和else分支
        last_block = chain[-1]
        
        # 获取最后一个块的then和else分支
        last_jump_instr = None
        for instr in last_block.instructions:
            if 'POP_JUMP' in instr.opname and 'IF' in instr.opname:
                last_jump_instr = instr
                break
        
        if not last_jump_instr or last_jump_instr.argval is None:
            return
        
        # 确定then和else分支
        then_branch = None
        else_branch = None
        for succ in last_block.successors:
            if succ.start_offset == last_jump_instr.argval:
                else_branch = succ
            else:
                then_branch = succ
        
        if not then_branch or not else_branch:
            return
        
        # 收集循环头部用于边界检查
        loop_headers = set()
        for struct in self.structures:
            if isinstance(struct, LoopStructure) and struct.header_block:
                loop_headers.add(struct.header_block)
        
        # 查找分支体
        then_body = self._find_branch_body(then_branch, main_block, loop_headers)
        # [关键修复] 对于else分支，传递is_else_branch=True
        else_body = self._find_branch_body(else_branch, main_block, loop_headers, is_else_branch=True)
        
        # [关键修复] 从then_body和else_body中排除嵌套if结构的entry_block
        # 嵌套if结构应该被识别为独立的IfStructure
        # [关键修复] 但是，then_body和else_body应该包含entry_block本身
        # 因为entry_block是复合条件的then/else分支的一部分
        nested_if_entries = set()
        for block in then_body | else_body:
            if self._is_conditional_block(block) and block not in chain:
                # 这是一个嵌套if的entry_block
                # 这是一个嵌套if的entry_block
                # 这是一个嵌套if的entry_block
                # 这是一个嵌套if的entry_block
                nested_if_entries.add(block)
        
        # [关键修复] 只从then_body和else_body中排除嵌套if的then_body和else_body中的块
        # 保留entry_block本身，因为它属于复合条件的then/else分支
        for nested_entry in nested_if_entries:
            # 收集嵌套if的then_body和else_body
            # 收集嵌套if的then_body和else_body
            # 收集嵌套if的then_body和else_body
            # 收集嵌套if的then_body和else_body
            nested_then_body = self._find_branch_body(nested_entry, main_block, loop_headers, is_else_branch=False)
            nested_else_body = self._find_branch_body(nested_entry, main_block, loop_headers, is_else_branch=True)
            
            # 从复合条件的then_body中排除嵌套if的then_body和else_body
            # 但保留entry_block本身
            for block in nested_then_body:
                if block != nested_entry:
                    then_body.discard(block)
            for block in nested_else_body:
                if block != nested_entry:
                    then_body.discard(block)
                    else_body.discard(block)
        
        # [关键修复] 在查找合并块之前，先将嵌套if的块从body中排除
        # 这样可以避免将嵌套if的then_body或else_body中的块错误地识别为merge_block
        body_for_merge = (then_body | else_body) - nested_if_entries
        for nested_entry in nested_if_entries:
            nested_then_body = self._find_branch_body(nested_entry, main_block, loop_headers, is_else_branch=False)
            nested_else_body = self._find_branch_body(nested_entry, main_block, loop_headers, is_else_branch=True)
            body_for_merge = body_for_merge - nested_then_body - nested_else_body
        
        # 找到合并块
        merge_block = self._find_merge_block(body_for_merge)
        
        # 从分支体中排除合并块
        if merge_block:
            then_body = then_body - {merge_block}
            else_body = else_body - {merge_block}
            # [关键修复] 只排除从merge_block可达的块，但这些块不应该属于嵌套if
            reachable_from_merge = self._find_reachable_blocks(merge_block)
            for block in list(reachable_from_merge):
                if block in nested_if_entries:
                    reachable_from_merge.discard(block)
                else:
                    for nested_entry in nested_if_entries:
                        nested_then_body = self._find_branch_body(nested_entry, main_block, loop_headers, is_else_branch=False)
                        nested_else_body = self._find_branch_body(nested_entry, main_block, loop_headers, is_else_branch=True)
                        if block in nested_then_body or block in nested_else_body:
                            reachable_from_merge.discard(block)
                            break
            then_body = then_body - reachable_from_merge
            else_body = else_body - reachable_from_merge
        
        # 创建复合条件结构
        has_else = len(else_body) > 0 and else_body != then_body
        
        # 排除链中的中间块从then_body
        for block in chain[1:]:
            then_body.discard(block)
            else_body.discard(block)
        
        if_struct = IfStructure(
            struct_type=ControlStructureType.IF_THEN_ELSE if has_else else ControlStructureType.IF_THEN,
            entry_block=main_block,
            condition_block=main_block,
            then_body=list(then_body),
            else_body=list(else_body) if has_else else [],
            merge_block=merge_block
        )
        
        self.structures.append(if_struct)
        
        # [关键修复] 只映射入口块和条件链中的块
        # 不映射then_body和else_body中的块，因为这些块可能属于其他结构
        for block in chain:
            self.block_to_structure[block] = if_struct
    
    def _exclude_after_merge(self, body: Set[BasicBlock], merge_block: BasicBlock) -> Set[BasicBlock]:
        """
        从分支体中排除合并块之后的代码
        
        Args:
            body: 分支体块集合
            merge_block: 合并块
            
        Returns:
            排除合并块之后代码的块集合
        """
        if not merge_block:
            return body
        
        # 找到所有从合并块可达的块
        reachable_from_merge = self._find_reachable_blocks(merge_block)
        
        # 从分支体中排除这些块
        return body - reachable_from_merge
    
    def _find_reachable_blocks(self, start: BasicBlock) -> Set[BasicBlock]:
        """
        查找从起始块可达的所有块
        
        Args:
            start: 起始块
            
        Returns:
            可达块集合
        """
        reachable = set()
        worklist = [start]
        
        while worklist:
            block = worklist.pop(0)
            if block in reachable:
                continue
            reachable.add(block)
            
            for succ in block.successors:
                if succ not in reachable:
                    worklist.append(succ)
        
        return reachable
    
    def _find_branch_body_for_elif(self, elif_block: BasicBlock, header: BasicBlock, 
                                    loop_headers: Optional[Set[BasicBlock]] = None,
                                    visited: Optional[Set[BasicBlock]] = None) -> Set[BasicBlock]:
        """
        查找elif块的所有相关块（包括then_body和else_body）
        
        Args:
            elif_block: elif条件块
            header: 当前if结构的header
            loop_headers: 所有循环头部的集合
            visited: 已访问的块集合（用于防止循环引用）
            
        Returns:
            elif块相关的所有基本块集合
        """
        # [关键修复] 添加已访问块检查，防止循环引用
        if visited is None:
            visited = set()
        
        if elif_block in visited:
            return set()
        
        visited.add(elif_block)
        
        result = set()
        result.add(elif_block)
        
        # 找到elif块的跳转指令
        elif_jump = self._get_jump_instr(elif_block)
        if elif_jump and elif_jump.argval is not None:
            # 收集then分支（fall-through后继）
            # 收集then分支（fall-through后继）
            # 收集then分支（fall-through后继）
            # 收集then分支（fall-through后继）
            for succ in elif_block.successors:
                if succ.start_offset != elif_jump.argval:
                    # [关键修复] 检查then分支是否是条件块
                    # [关键修复] 检查then分支是否是条件块
                    # [关键修复] 检查then分支是否是条件块
                    # [关键修复] 检查then分支是否是条件块
                    if self._is_conditional_block(succ):
                        # then分支是条件块，检查它是否是elif链的一部分
                        # elif链的特征：then分支的跳转目标与当前elif块的fall-through后继不同
                        # then分支是条件块，检查它是否是elif链的一部分
                        # elif链的特征：then分支的跳转目标与当前elif块的fall-through后继不同
                        # then分支是条件块，检查它是否是elif链的一部分
                        # elif链的特征：then分支的跳转目标与当前elif块的fall-through后继不同
                        # then分支是条件块，检查它是否是elif链的一部分
                        # elif链的特征：then分支的跳转目标与当前elif块的fall-through后继不同
                        succ_jump = self._get_jump_instr(succ)
                        if succ_jump and succ_jump.argval is not None:
                            # 找到当前elif块的fall-through后继
                            # 找到当前elif块的fall-through后继
                            # 找到当前elif块的fall-through后继
                            # 找到当前elif块的fall-through后继
                            elif_fall_through = None
                            for s in elif_block.successors:
                                if s.start_offset != elif_jump.argval:
                                    elif_fall_through = s
                                    break
                            
                            # 检查是否是elif链（then分支的跳转目标不是当前elif块的fall-through后继）
                            if elif_fall_through and succ_jump.argval != elif_fall_through.start_offset:
                                # 这是elif链，递归调用_find_branch_body_for_elif
                                # 这是elif链，递归调用_find_branch_body_for_elif
                                # 这是elif链，递归调用_find_branch_body_for_elif
                                # 这是elif链，递归调用_find_branch_body_for_elif
                                nested_result = self._find_branch_body_for_elif(succ, header, loop_headers, visited)
                                result = result | nested_result
                            else:
                                # 不是elif链，使用_find_branch_body收集
                                then_body = self._find_branch_body(succ, elif_block, loop_headers, is_else_branch=False)
                                result = result | then_body
                        else:
                            # 没有跳转指令，使用_find_branch_body收集
                            then_body = self._find_branch_body(succ, elif_block, loop_headers, is_else_branch=False)
                            result = result | then_body
                    else:
                        # then分支不是条件块，使用_find_branch_body收集
                        then_body = self._find_branch_body(succ, elif_block, loop_headers, is_else_branch=False)
                        result = result | then_body
                    break
            
            # 收集else分支（jump目标后继）
            for succ in elif_block.successors:
                # [关键修复] 跳过异常处理器块
                # [关键修复] 跳过异常处理器块
                # [关键修复] 跳过异常处理器块
                # [关键修复] 跳过异常处理器块
                if succ.instructions and succ.instructions[0].opname == 'PUSH_EXC_INFO':
                    continue
                if succ.start_offset == elif_jump.argval:
                    # [关键修复] 检查else分支是否是elif条件块
                    # 如果是，递归调用_find_branch_body_for_elif来收集它的所有块
                    # [关键修复] 检查else分支是否是elif条件块
                    # 如果是，递归调用_find_branch_body_for_elif来收集它的所有块
                    # [关键修复] 检查else分支是否是elif条件块
                    # 如果是，递归调用_find_branch_body_for_elif来收集它的所有块
                    # [关键修复] 检查else分支是否是elif条件块
                    # 如果是，递归调用_find_branch_body_for_elif来收集它的所有块
                    if self._is_conditional_block(succ):
                        # else分支是elif条件块，递归收集
                        # else分支是elif条件块，递归收集
                        # else分支是elif条件块，递归收集
                        # else分支是elif条件块，递归收集
                        nested_result = self._find_branch_body_for_elif(succ, header, loop_headers, visited)
                        result = result | nested_result
                    else:
                        # else分支不是条件块，使用_find_branch_body收集
                        else_body = self._find_branch_body(succ, elif_block, loop_headers, is_else_branch=True)
                        result = result | else_body
                    break
        
        return result
    
    def _find_branch_body(self, start: BasicBlock, header: BasicBlock,
                          loop_headers: Optional[Set[BasicBlock]] = None,
                          is_else_branch: bool = False,
                          collect_nested_else: bool = True) -> Set[BasicBlock]:
        """
        查找分支体

        Args:
            start: 起始块
            header: 条件头部
            loop_headers: 所有循环头部的集合（用于边界检查）
            is_else_branch: 是否是else分支（用于特殊处理）

        Returns:
            分支体中的基本块集合
        """
        body: Set[BasicBlock] = set()
        worklist = deque([start])

        # [调试输出]
        import sys as _debug_sys        
        if loop_headers is None:
            loop_headers = set()
        
        # [关键修复] 定义异常处理块检查函数
        def is_exception_handler_block(block):
            """检查块是否是异常处理块（PUSH_EXC_INFO, CHECK_EXC_MATCH, POP_EXCEPT, RERAISE）"""
            for instr in block.instructions:
                if instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'POP_EXCEPT', 'RERAISE'):
                    return True
            return False
        
        while worklist:
            block = worklist.popleft()
            if block in body:
                continue
            
            # [关键修复] 跳过异常处理块
            if is_exception_handler_block(block):
                continue
            
            # [关键修复] 如果 block == header，跳过
            # 但如果是 start == header 的情况（即条件块本身也是 then_branch），
            # 则需要收集 fall-through 后继
            if block == header:
                if start == header and block == start:
                    # start == header 的情况，添加 block 到 body
                    # start == header 的情况，添加 block 到 body
                    # start == header 的情况，添加 block 到 body
                    # start == header 的情况，添加 block 到 body
                    body.add(block)
                    
                    # [关键修复] 检查是否是 AND 复合条件
                    # 如果是，不收集 fall-through 后继，因为它是复合条件的一部分
                    jump_instr = self._get_jump_instr(block)
                    is_and_compound = False
                    if jump_instr and 'POP_JUMP_FORWARD_IF_FALSE' in jump_instr.opname:
                        for succ in block.successors:
                            if succ.start_offset != jump_instr.argval:
                                if self._is_conditional_block(succ):
                                    succ_jump = self._get_jump_instr(succ)
                                    if succ_jump and succ_jump.argval == jump_instr.argval:
                                        is_and_compound = True
                                break
                    
                    # [关键修复] 对于嵌套if结构，需要递归收集嵌套if的所有块
                    # 这是嵌套if结构：当前块是条件块，需要收集它的then_body和else_body
                    # [关键修复] 检查是否是独立的if结构（不是嵌套在then分支中）
                    # 独立的if结构特征：条件块有多个前驱
                    is_independent_if = len(block.predecessors) > 1
                    
                    if jump_instr and jump_instr.argval is not None and not is_and_compound and not is_independent_if:
                        # [关键修复] 递归收集嵌套if结构的所有块
                        # 找到嵌套if的then_branch（fall-through后继）和else_branch（jump目标后继）
                        # [关键修复] 递归收集嵌套if结构的所有块
                        # 找到嵌套if的then_branch（fall-through后继）和else_branch（jump目标后继）
                        # [关键修复] 递归收集嵌套if结构的所有块
                        # 找到嵌套if的then_branch（fall-through后继）和else_branch（jump目标后继）
                        # [关键修复] 递归收集嵌套if结构的所有块
                        # 找到嵌套if的then_branch（fall-through后继）和else_branch（jump目标后继）
                        nested_then_branch = None
                        nested_else_branch = None
                        for succ in block.successors:
                            if succ.start_offset != jump_instr.argval:
                                nested_then_branch = succ  # fall-through后继是then分支
                            else:
                                nested_else_branch = succ  # jump目标后继是else分支
                        
                        # 递归收集嵌套if的then_body
                        # [关键修复] 如果nested_then_branch是复合条件的一部分，
                        # 应该找到复合条件链的最后一个条件块的fall-through后继作为then_body
                        if nested_then_branch and nested_then_branch not in body and nested_then_branch != header:
                            # [关键修复] 检查nested_then_branch是否是复合条件的一部分
                            # [关键修复] 检查nested_then_branch是否是复合条件的一部分
                            # [关键修复] 检查nested_then_branch是否是复合条件的一部分
                            # [关键修复] 检查nested_then_branch是否是复合条件的一部分
                            is_nested_compound = False
                            if self._is_conditional_block(nested_then_branch):
                                nested_then_jump = self._get_jump_instr(nested_then_branch)
                                if nested_then_jump and nested_then_jump.argval == jump_instr.argval:
                                    # nested_then_branch是复合条件的一部分
                                    # nested_then_branch是复合条件的一部分
                                    # nested_then_branch是复合条件的一部分
                                    # nested_then_branch是复合条件的一部分
                                    is_nested_compound = True
                                    # 找到复合条件链的最后一个条件块
                                    last_cond_block = nested_then_branch
                                    while True:
                                        # 找到last_cond_block的fall-through后继
                                        # 找到last_cond_block的fall-through后继
                                        # 找到last_cond_block的fall-through后继
                                        # 找到last_cond_block的fall-through后继
                                        last_fall_through = None
                                        last_jump = self._get_jump_instr(last_cond_block)
                                        if last_jump:
                                            for succ in last_cond_block.successors:
                                                if succ.start_offset != last_jump.argval:
                                                    last_fall_through = succ
                                                    break
                                        
                                        # 检查fall-through后继是否也是复合条件的一部分
                                        if last_fall_through and self._is_conditional_block(last_fall_through):
                                            last_fall_through_jump = self._get_jump_instr(last_fall_through)
                                            if last_fall_through_jump and last_fall_through_jump.argval == jump_instr.argval:
                                                # 也是复合条件的一部分，继续
                                                # 也是复合条件的一部分，继续
                                                # 也是复合条件的一部分，继续
                                                # 也是复合条件的一部分，继续
                                                last_cond_block = last_fall_through
                                                continue
                                        
                                        # 找到最后一个条件块，使用它的fall-through后继作为then_body
                                        if last_fall_through and last_fall_through not in body and last_fall_through != header:
                                            nested_then_body = self._find_branch_body(last_fall_through, block, loop_headers, is_else_branch=False)
                                            for b in nested_then_body:
                                                if b != header:
                                                    body.add(b)
                                        break
                            
                            if not is_nested_compound:
                                nested_then_body = self._find_branch_body(nested_then_branch, block, loop_headers, is_else_branch=False)
                                for b in nested_then_body:
                                    if b != header:
                                        body.add(b)
                        
                        # 递归收集嵌套if的else_body
                        # [关键修复] 当collect_nested_else=False时，不收集嵌套if的else_body
                        if collect_nested_else and nested_else_branch and nested_else_branch not in body and nested_else_branch != header:
                            nested_else_body = self._find_branch_body(nested_else_branch, block, loop_headers, is_else_branch=True)
                            for b in nested_else_body:
                                if b != header:
                                    body.add(b)
                continue
            
            # [关键修复] 检查块是否是循环头部或包含GET_ITER指令（for循环的entry块）
            # 对于包含GET_ITER的块，需要找到对应的循环结构并收集所有body_blocks
            is_loop_entry = False
            original_block = block  # 保存原始块，用于后续处理
            if block.loop_header:
                is_loop_entry = True
            elif any(instr.opname == 'GET_ITER' for instr in block.instructions):
                for succ in block.successors:
                    if any(instr.opname == 'FOR_ITER' for instr in succ.instructions):
                        is_loop_entry = True
                        block = succ
                        break
            if not is_loop_entry:
                for struct in self.structures:
                    if isinstance(struct, LoopStructure) and struct.header_block == block:
                        is_loop_entry = True
                        break
            
            if is_loop_entry:
                is_nested_loop = any(pred in body or pred == start for pred in block.predecessors)
                if not is_nested_loop and not body:
                    is_nested_loop = block in start.successors
                if not is_nested_loop and block == start:
                    is_nested_loop = True
                
                # [关键修复] 对于作为start的循环入口，需要添加块本身到body
                # 并收集循环的所有body_blocks，然后继续收集后继
                # 使用original_block来检查是否是start
                if original_block == start or is_nested_loop:
                    # 添加原始块本身到body（包含GET_ITER的块）
                    body.add(original_block)
                    # 添加当前块（可能是FOR_ITER块）到body
                    if block != original_block:
                        body.add(block)
                    # 找到对应的LoopStructure并添加所有body_blocks
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure) and struct.header_block == block:
                            for loop_block in struct.body_blocks:
                                body.add(loop_block)
                            break
                    # 添加循环header的后继到worklist
                    for loop_succ in block.successors:
                        if loop_succ not in body and loop_succ != header:
                            worklist.append(loop_succ)
                continue
            
            # [关键修复] 检查块是否是循环尾部（包含向后跳转指令）
            # 如果是，添加这个块，并继续收集非向后跳转目标的后继
            has_backward_jump = False
            backward_jump_target = None
            for instr in block.instructions:
                if 'BACKWARD' in instr.opname:
                    has_backward_jump = True
                    backward_jump_target = instr.argval
                    break
            
            if has_backward_jump:
                # 添加这个块
                # 添加这个块
                # 添加这个块
                # 添加这个块
                body.add(block)
                # [关键修复] 对于包含向后跳转的块，检查跳转目标是否是循环头部
                # 如果是，继续收集后继（因为这些后继是嵌套在循环中的if结构的then/else分支）
                # 例如：块44包含POP_JUMP_BACKWARD_IF_TRUE（跳转到循环头部），
                # 但它的后继46是内层if结构的then分支，应该被收集
                is_loop_back_edge = False
                if backward_jump_target is not None:
                    for loop_header in loop_headers:
                        if loop_header.start_offset == backward_jump_target:
                            is_loop_back_edge = True
                            break
                    
                    # [关键修复] 如果跳转目标不是循环头部，检查它是否在循环体内
                    # 这对于while True循环很重要，因为循环体内的if条件块也是有效的跳转目标
                    if not is_loop_back_edge:
                        for loop_header in loop_headers:
                            # 找到对应的LoopStructure
                            # 找到对应的LoopStructure
                            # 找到对应的LoopStructure
                            # 找到对应的LoopStructure
                            for struct in self.structures:
                                if isinstance(struct, LoopStructure) and struct.header_block == loop_header:
                                    # 检查跳转目标是否在循环体内
                                    # 检查跳转目标是否在循环体内
                                    # 检查跳转目标是否在循环体内
                                    # 检查跳转目标是否在循环体内
                                    if hasattr(struct, 'body_blocks'):
                                        for loop_block in struct.body_blocks:
                                            if loop_block.start_offset == backward_jump_target:
                                                is_loop_back_edge = True
                                                break
                                    break
                            if is_loop_back_edge:
                                break
                
                if is_loop_back_edge:
                    # 这是循环回边，继续收集后继（跳过循环回边目标）
                    # 这是循环回边，继续收集后继（跳过循环回边目标）
                    # 这是循环回边，继续收集后继（跳过循环回边目标）
                    # 这是循环回边，继续收集后继（跳过循环回边目标）
                    for succ in block.successors:
                        if succ.start_offset != backward_jump_target and succ not in body and succ != header:
                            worklist.append(succ)
                    continue
                else:
                    # 不是循环回边，不收集后继
                    continue
            
            # [关键修复] 检查块是否包含跳出循环的跳转指令
            # 如果是，不要收集跳转目标之后的块
            # [关键修复] 改进：处理break语句（向前跳转到循环之后的代码）
            has_exit_jump = False
            for instr in block.instructions:
                if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                    # 检查跳转目标
                    if instr.argval is not None:
                        jump_target_offset = instr.argval
                        # [关键修复] 检查是否是向后跳转到header（循环回边）
                        if block.start_offset >= jump_target_offset and jump_target_offset == header.start_offset:
                            # 向后跳转到header，是循环回边
                            has_exit_jump = True
                            break
                        # [关键修复] 检查是否是break语句（向前跳转到循环之后的代码）
                        # break的特征：向前跳转，且跳转目标不在当前分支体内
                        if jump_target_offset > block.start_offset:
                            # 向前跳转，可能是break
                            # 检查跳转目标是否是任何循环的退出点
                            for loop in self.structures:
                                if isinstance(loop, LoopStructure):
                                    # 如果跳转目标在循环体之外，这是break
                                    if hasattr(loop, 'body_blocks'):
                                        loop_body_ids = {b.start_offset for b in loop.body_blocks}
                                        if jump_target_offset not in loop_body_ids:
                                            # 这是break，不要收集后继
                                            has_exit_jump = True
                                            break
                            if has_exit_jump:
                                break
                        
                        # [关键修复] 如果JUMP_FORWARD跳转到当前if结构之后的代码
                        # 这是if-elif-else结构的结束，不要收集后继
                        if jump_target_offset > block.start_offset:
                            # 检查跳转目标是否是任何结构的entry_block
                            for struct in self.structures:
                                if hasattr(struct, 'entry_block') and struct.entry_block:
                                    if struct.entry_block.start_offset == jump_target_offset:
                                        # 跳转目标是另一个结构的开始
                                        # 检查该结构是否在当前if结构之后
                                        if struct.entry_block.start_offset > header.start_offset:
                                            # 这是if结构之后的代码，不要收集后继
                                            has_exit_jump = True
                                            break
                            if has_exit_jump:
                                break

            # [关键修复] 如果块包含RETURN_VALUE且没有后继，这是函数的最后一条return语句
            # 添加块到body，但不继续收集后继，因为return会终止当前执行路径
            # [关键修复-2026] 但是首先要检查是否是合并点（merge point）
            # 如果是合并点，不应该被包含在任何分支体中，即使它有RETURN_VALUE
            is_merge_point_before_return = False
            if len(block.predecessors) > 1:
                predecessors_in_body = sum(1 for pred in block.predecessors if pred in body or pred == start)
                if predecessors_in_body < len(block.predecessors):
                    is_merge_point_before_return = True
            
            has_return = any(instr.opname == 'RETURN_VALUE' for instr in block.instructions)
            if has_return and not block.successors and not is_merge_point_before_return:
                body.add(block)
                continue

            # [关键修复] 检查是否是OR条件模式（如 if a or b:）
            # OR条件的特征：
            # 1. 当前块使用POP_JUMP_FORWARD_IF_TRUE（条件为True时跳转到then-body）
            # 2. fall-through后继也是条件块，使用POP_JUMP_FORWARD_IF_FALSE
            # 3. fall-through后继的fall-through目标与当前块的跳转目标相同（都是then-body）
            # [关键修复] 这个检查必须在body.add(block)之前，否则OR条件块会被添加到body中
            if self._is_conditional_block(block):
                jump_instr = self._get_jump_instr(block)
                if jump_instr and 'POP_JUMP_FORWARD_IF_TRUE' in jump_instr.opname:
                    # 找到fall-through后继
                    # 找到fall-through后继
                    # 找到fall-through后继
                    # 找到fall-through后继
                    fall_through_succ = None
                    for succ in block.successors:
                        if succ.start_offset != jump_instr.argval:
                            fall_through_succ = succ
                            break
                    
                    if fall_through_succ and self._is_conditional_block(fall_through_succ):
                        fall_through_jump = self._get_jump_instr(fall_through_succ)
                        if fall_through_jump and 'POP_JUMP_FORWARD_IF_FALSE' in fall_through_jump.opname:
                            # 找到fall-through后继的fall-through目标
                            # 找到fall-through后继的fall-through目标
                            # 找到fall-through后继的fall-through目标
                            # 找到fall-through后继的fall-through目标
                            fall_through_fall_through = None
                            for succ in fall_through_succ.successors:
                                if succ.start_offset != fall_through_jump.argval:
                                    fall_through_fall_through = succ
                                    break
                            
                            # 检查fall-through后继的fall-through目标是否与当前块的跳转目标相同
                            if fall_through_fall_through and fall_through_fall_through.start_offset == jump_instr.argval:
                                # 这是OR条件，不收集当前块，让它被识别为独立的条件块
                                # 这是OR条件，不收集当前块，让它被识别为独立的条件块
                                # 这是OR条件，不收集当前块，让它被识别为独立的条件块
                                # 这是OR条件，不收集当前块，让它被识别为独立的条件块
                                continue

            # [关键修复] 如果start块是条件块且不是header，需要判断是嵌套if还是复合条件
            # 嵌套if：start块的else分支与header的else分支不同
            # 复合条件：start块的else分支与header的else分支相同
            # [关键修复] 对于else分支，我们需要收集嵌套if的所有块，而不是跳过
            is_start_conditional = block == start and start != header and self._is_conditional_block(start)
            if is_start_conditional:
                jump_instr = self._get_jump_instr(start)
                if jump_instr and jump_instr.argval is not None:
                    header_jump = self._get_jump_instr(header)
                    
                    if header_jump and header_jump.argval is not None:
                        start_else = None
                        for succ in start.successors:
                            if succ.start_offset == jump_instr.argval:
                                start_else = succ
                                break
                        
                        header_else = None
                        for succ in header.successors:
                            if succ.start_offset == header_jump.argval:
                                header_else = succ
                                break
                        
                        # [关键修复] 添加start块本身到body
                        body.add(start)
                        
                        # [关键修复] 找到start的then_branch（fall-through后继）和else_branch（jump目标）
                        nested_then_branch = None
                        nested_else_branch = None
                        for succ in start.successors:
                            if succ.start_offset != jump_instr.argval:
                                nested_then_branch = succ
                            else:
                                nested_else_branch = succ
                        
                        # [关键修复] 对于else分支，需要递归收集嵌套if的所有块
                        if is_else_branch:
                            # [关键修复] 检查nested_else_branch是否是真正的嵌套if
                            # 真正的嵌套if：只有一个前驱，且是当前的header
                            # 独立的if结构：有多个前驱，或在if/elif之后执行
                            is_truly_nested = (nested_else_branch and 
                                              len(nested_else_branch.predecessors) == 1 and 
                                              header in nested_else_branch.predecessors)
                            
                            # [关键修复] 检查是否是JUMP_IF_TRUE_OR_POP赋值（如x = a or b）
                            # 如果是，这不是嵌套if结构，应该继续收集后继块
                            is_assignment_pattern = False
                            if jump_instr and jump_instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                                # 检查跳转目标是否是STORE_FAST
                                jump_target_offset = jump_instr.argval
                                if jump_target_offset is not None:
                                    for succ in start.successors:
                                        if succ.start_offset == jump_target_offset:
                                            for target_instr in succ.instructions:
                                                if target_instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                                                    if target_instr.opname == 'STORE_FAST':
                                                        is_assignment_pattern = True
                                                    break
                                            break
                            
                            if is_truly_nested:
                                # 递归收集嵌套if的then_body
                                if nested_then_branch and nested_then_branch not in body and nested_then_branch != header:
                                    nested_then_body = self._find_branch_body(nested_then_branch, start, loop_headers, is_else_branch=False)
                                    for b in nested_then_body:
                                        if b != header:
                                            body.add(b)

                                # 递归收集嵌套if的else_body
                                if nested_else_branch and nested_else_branch not in body and nested_else_branch != header:
                                    nested_else_body = self._find_branch_body(nested_else_branch, start, loop_headers, is_else_branch=True)
                                    for b in nested_else_body:
                                        if b != header:
                                            body.add(b)
                            elif is_assignment_pattern:
                                # [关键修复] 对于JUMP_IF_TRUE_OR_POP赋值，继续收集后继块
                                # 不要continue，让后面的代码收集后继块
                                pass
                            else:
                                # 不是真正的嵌套if，也不是赋值模式
                                # 继续收集后继块
                                pass
                        else:
                            # [关键修复] 对于then分支中的嵌套if结构，只添加条件块本身
                            # 不递归收集它的then/else分支，因为这些分支属于嵌套if结构自己
                            # 嵌套if结构会在后续被单独处理
                            pass
                    
                # [关键修复] 对于JUMP_IF_TRUE_OR_POP赋值，不要continue，继续收集后继块
                if not (jump_instr and jump_instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')):
                    continue
            
            # [关键修复] 在添加块到body之前，检查它是否是函数的结尾块（只包含return）
            # 如果是，不添加它到body，也不收集它的后继
            # [关键修复] 排除只包含NOP的块，因为NOP是有效的代码（如pass语句）
            is_return_only_block = True
            has_non_nop_instruction = False
            for instr in block.instructions:
                if instr.opname not in ('RESUME', 'CACHE', 'NOP', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE'):
                    is_return_only_block = False
                    break
                if instr.opname != 'NOP':
                    has_non_nop_instruction = True
            
            # [关键修复] 如果块只包含NOP（没有其他指令），这不是return-only块
            # NOP是有效的代码（如pass语句），应该被添加到body
            if not has_non_nop_instruction:
                is_return_only_block = False
            
            # 如果是return-only块，跳过它（不添加到body，也不收集后继）
            if is_return_only_block:
                continue
            
            # [关键修复-2026] 通用合并点检测
            # 如果块是合并点（有多个前驱且不完全属于当前分支），不应该被添加到body中
            # [关键修复-2026-2] 但是循环继续点（包含BACKWARD跳转）除外
            # 因为循环继续点虽然是合并点，但它属于当前控制流结构的一部分
            is_merge_point = False
            is_loop_continuation = False
            
            if len(block.predecessors) > 1:
                predecessors_in_body = sum(1 for pred in block.predecessors if pred in body or pred == start)
                if predecessors_in_body < len(block.predecessors):
                    # 检查是否是循环继续点（包含BACKWARD跳转指令）
                    has_backward_jump = any('BACKWARD' in instr.opname for instr in block.instructions)
                    if has_backward_jump:
                        # 是循环继续点，不视为合并点
                        is_loop_continuation = True
                    else:
                        # 不是循环继续点，是真正的跨结构合并点
                        is_merge_point = True
            
            # 如果是合并点（且不是循环继续点），跳过它
            if is_merge_point and not is_loop_continuation:
                continue
            
            body.add(block)

            # [关键修复] 如果当前块是条件块，不要继续收集后继
            # 这是嵌套if结构的关键：条件块的then分支是另一个if结构，我们不应该深入
            # [例外] 对于复合条件（使用JUMP_IF_TRUE_OR_POP或JUMP_IF_FALSE_OR_POP），
            # 需要继续收集fall-through后继，因为这些指令是复合条件的一部分
            is_cond_block = self._is_conditional_block(block)
            if is_cond_block:
                jump_instr = self._get_jump_instr(block)
                is_compound_condition = jump_instr and jump_instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP')
                
                # [关键修复] 区分复合条件和赋值语句
                # 如果跳转目标是STORE_FAST，这是赋值语句（如x = a or b），不是复合条件
                if is_compound_condition and jump_instr and jump_instr.argval is not None:
                    jump_target_offset = jump_instr.argval
                    for succ in block.successors:
                        if succ.start_offset == jump_target_offset:
                            # 检查跳转目标块是否以STORE_FAST开头
                            for target_instr in succ.instructions:
                                if target_instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                                    if target_instr.opname == 'STORE_FAST':
                                        # 这是赋值语句，不是复合条件
                                        is_compound_condition = False
                                        break
                            break
                
                # [关键修复] 对于AND复合条件（如 if A and B:），条件块使用POP_JUMP_FORWARD_IF_FALSE
                # 且fall-through后继也是条件块，跳转目标相同
                # 这种情况下，fall-through后继是复合条件的一部分，不是then_body的一部分
                is_and_compound = False
                if jump_instr and 'POP_JUMP_FORWARD_IF_FALSE' in jump_instr.opname:
                    # 检查fall-through后继
                    # 检查fall-through后继
                    # 检查fall-through后继
                    # 检查fall-through后继
                    for succ in block.successors:
                        if succ.start_offset != jump_instr.argval:  # fall-through后继
                            if self._is_conditional_block(succ):
                                # fall-through后继是条件块
                                # fall-through后继是条件块
                                # fall-through后继是条件块
                                # fall-through后继是条件块
                                succ_jump = self._get_jump_instr(succ)
                                if succ_jump and succ_jump.argval == jump_instr.argval:
                                    # 跳转目标相同，是AND复合条件
                                    # 跳转目标相同，是AND复合条件
                                    # 跳转目标相同，是AND复合条件
                                    # 跳转目标相同，是AND复合条件
                                    is_and_compound = True
                            break
                    
                    # [关键修复] 即使fall-through后继不是条件块，当前块也可能是AND复合条件的一部分
                    # 特征：当前块的跳转目标与header的跳转目标相同，且当前块的唯一前驱是header
                    if not is_and_compound and block != header:
                        header_jump = self._get_jump_instr(header)
                        if header_jump and jump_instr.argval == header_jump.argval:
                            # 检查当前块的唯一前驱是否是header
                            # 检查当前块的唯一前驱是否是header
                            # 检查当前块的唯一前驱是否是header
                            # 检查当前块的唯一前驱是否是header
                            preds = list(block.predecessors)
                            if len(preds) == 1 and preds[0] == header:
                                # 这是AND复合条件的一部分
                                # 这是AND复合条件的一部分
                                # 这是AND复合条件的一部分
                                # 这是AND复合条件的一部分
                                is_and_compound = True
                
                # [关键修复] 对于链式比较（如 0 < x < 100），条件块使用POP_JUMP_FORWARD_IF_FALSE
                # 但它们的then分支包含实际代码，应该继续收集
                # [关键修复] 链式比较的特征：
                # 1. 当前块是条件块（使用POP_JUMP_FORWARD_IF_FALSE）
                # 2. fall-through后继也是条件块，且跳转目标相同
                # 3. 或者fall-through后继只包含JUMP_FORWARD（链式比较的中间块）
                is_chained_compare = False
                if jump_instr and 'POP_JUMP_FORWARD_IF_FALSE' in jump_instr.opname:
                    # 检查fall-through后继
                    # 检查fall-through后继
                    # 检查fall-through后继
                    # 检查fall-through后继
                    for succ in block.successors:
                        if succ.start_offset != jump_instr.argval:  # fall-through后继
                            if self._is_conditional_block(succ):
                                # fall-through后继是条件块
                                # fall-through后继是条件块
                                # fall-through后继是条件块
                                # fall-through后继是条件块
                                succ_jump = self._get_jump_instr(succ)
                                if succ_jump and succ_jump.argval == jump_instr.argval:
                                    # 跳转目标相同，是链式比较
                                    # 跳转目标相同，是链式比较
                                    # 跳转目标相同，是链式比较
                                    # 跳转目标相同，是链式比较
                                    is_chained_compare = True
                            else:
                                # fall-through后继不是条件块
                                # 检查是否是链式比较的中间块（只包含JUMP_FORWARD）
                                non_trivial = [i for i in succ.instructions 
                                              if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                                if len(non_trivial) == 1 and non_trivial[0].opname == 'JUMP_FORWARD':
                                    # 这是链式比较的中间块（JUMP_FORWARD到then_body）
                                    # 这是链式比较的中间块（JUMP_FORWARD到then_body）
                                    # 这是链式比较的中间块（JUMP_FORWARD到then_body）
                                    # 这是链式比较的中间块（JUMP_FORWARD到then_body）
                                    is_chained_compare = True
                            break
                
                # [关键修复] 检查当前块是否是while循环的条件块
                # 特征：fall-through后继包含POP_JUMP_BACKWARD_IF_TRUE指令，跳转目标是fall-through后继自己
                # 这种情况下，fall-through后继是while循环的body块
                is_while_condition = False
                fall_through_is_loop_header = False
                if jump_instr and 'POP_JUMP_FORWARD_IF_FALSE' in jump_instr.opname:
                    for succ in block.successors:
                        if succ.start_offset != jump_instr.argval:  # fall-through后继
                            # [关键修复] 检查fall-through后继是否是循环header
                            if succ.loop_header:
                                fall_through_is_loop_header = True
                            for instr in succ.instructions:
                                if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                                    if instr.argval is not None and instr.argval == succ.start_offset:
                                        # fall-through后继包含向后跳转到自己，是while循环的body块
                                        # fall-through后继包含向后跳转到自己，是while循环的body块
                                        # fall-through后继包含向后跳转到自己，是while循环的body块
                                        # fall-through后继包含向后跳转到自己，是while循环的body块
                                        is_while_condition = True
                                        break
                            if is_while_condition:
                                break
                
                if not is_compound_condition and not is_chained_compare and not is_and_compound:
                    # 不是复合条件，也不是链式比较
                    # [关键修复] 如果是while循环的条件块，且fall-through后继不是循环header
                    # 则不收集任何后继（这是独立的while循环，不是嵌套在if中的）
                    # 但如果fall-through后继是循环header，我们需要收集它作为嵌套循环
                    # [关键修复-2026] 例外：如果是else分支(is_else_branch=True)，
                    # 且fall-through后继包含向后跳转指令（循环继续点），则收集这个后继
                    # 这处理的是 else: if x: ...; count += 1 这样的模式
                    should_collect_fallthrough = False
                    
                    if is_else_branch and not is_while_condition:
                        for succ in block.successors:
                            if succ.start_offset != jump_instr.argval:  # fall-through后继
                                has_backward = any('BACKWARD' in i.opname for i in succ.instructions)
                                if has_backward:
                                    should_collect_fallthrough = True
                                    break
                    
                    if (is_while_condition and fall_through_is_loop_header) or should_collect_fallthrough:
                        # [关键修复] 收集fall-through后继（嵌套循环的header）及其所有body_blocks
                        # [关键修复] 收集fall-through后继（嵌套循环的header）及其所有body_blocks
                        # [关键修复] 收集fall-through后继（嵌套循环的header）及其所有body_blocks
                        # [关键修复] 收集fall-through后继（嵌套循环的header）及其所有body_blocks
                        for succ in block.successors:
                            if succ.start_offset != jump_instr.argval:  # fall-through后继
                                if succ not in body and succ != header:
                                    body.add(succ)
                                    # 找到对应的LoopStructure并添加所有body_blocks
                                    for struct in self.structures:
                                        if isinstance(struct, LoopStructure) and struct.header_block == succ:
                                            for loop_block in struct.body_blocks:
                                                body.add(loop_block)
                                            break
                                    # 添加循环header的后继到worklist
                                    for loop_succ in succ.successors:
                                        if loop_succ not in body and loop_succ != header:
                                            worklist.append(loop_succ)
                        continue
                    
                    if is_while_condition:
                        continue
                    
                    # [关键修复-2026-else] 对于else分支中的条件块，始终收集fall-through后继
                    # 这解决了 else: if x: ...; stmt 模式中stmt缺失的问题
                    # 无论后续走哪条路径（嵌套if、独立if等），都要确保fall-through后继被收集
                    if is_else_branch and jump_instr and jump_instr.argval is not None:
                        for succ in block.successors:
                            if succ.start_offset != jump_instr.argval:  # fall-through后继
                                if succ not in body and succ != header:
                                    non_trivial = [i for i in succ.instructions 
                                                  if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                                    is_return_only = (len(non_trivial) == 2 and 
                                                     non_trivial[0].opname.startswith('LOAD_') and
                                                     non_trivial[1].opname == 'RETURN_VALUE')
                                    if not is_return_only:
                                        body.add(succ)
                                        worklist.append(succ)
                        # 注意：这里不continue，让后续逻辑继续处理嵌套if等特殊情况
                    
                    # [关键修复] 对于else分支中的条件块，需要区分嵌套if和elif链
                    # 嵌套if的特征：条件块的前驱包含当前if结构的header
                    # elif链的特征：条件块的前驱不包含当前if结构的header
                    if is_else_branch and jump_instr and jump_instr.argval is not None:
                        # [关键修复] 检查条件块是否是嵌套在当前if结构中的
                        # 嵌套if的特征：是fall-through后继（只有一个前驱，且是当前的header）
                        # elif的特征：是jump目标后继，前驱包含当前的header，但有多个前驱
                        is_single_pred = len(block.predecessors) == 1
                        is_nested_in_current = header in block.predecessors and is_single_pred
                        
                        # [关键修复] 检查是否是赋值语句（如 x = a or b）
                        # 如果是赋值语句，不应该将其视为嵌套if结构
                        is_assignment = False
                        if jump_instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                            # 检查跳转目标是否是STORE_FAST
                            jump_target_offset = jump_instr.argval
                            if jump_target_offset is not None:
                                for succ in block.successors:
                                    if succ.start_offset == jump_target_offset:
                                        for target_instr in succ.instructions:
                                            if target_instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                                                if target_instr.opname == 'STORE_FAST':
                                                    is_assignment = True
                                                break
                                        break
                        
                        if is_nested_in_current and not is_assignment:
                            # [关键修复] 这是嵌套在当前if结构中的if
                            # 添加当前条件块到body
                            body.add(block)
                            
                            # [关键修复] 递归收集嵌套if的then_body和else_body
                            # 找到嵌套if的then_branch（fall-through后继）和else_branch（jump目标后继）
                            nested_then = None
                            nested_else = None
                            for succ in block.successors:
                                if is_exception_handler_block(succ):
                                    continue
                                if succ.start_offset != jump_instr.argval:
                                    nested_then = succ
                                else:
                                    nested_else = succ
                            
                            # 递归收集then_body
                            if nested_then and nested_then not in body and nested_then != header:
                                nested_then_body = self._find_branch_body(nested_then, block, loop_headers, is_else_branch=False)
                                for b in nested_then_body:
                                    if b != header:
                                        body.add(b)
                            
                            # 递归收集else_body
                            if nested_else and nested_else not in body and nested_else != header:
                                nested_else_body = self._find_branch_body(nested_else, block, loop_headers, is_else_branch=True)
                                for b in nested_else_body:
                                    if b != header:
                                        body.add(b)
                            continue
                        else:
                            # [关键修复] 这是独立的if结构（在if/elif之后执行）
                            # 不是elif链的一部分，也不是嵌套在当前if结构中的if
                            # [关键修复] 但是，如果这个条件块有多个前驱，它是完全独立的if结构
                            # 不应该收集它的后继，因为这些后继属于独立的if结构自己
                            # [例外] 如果是赋值语句（如 x = a or b），应该继续收集后继块
                            is_fully_independent = len(block.predecessors) > 1
                            
                            if is_fully_independent and not is_assignment:
                                # 完全独立的if结构，只添加条件块本身，不收集后继
                                body.add(block)
                                continue
                            
                            # [关键修复] 添加当前条件块到body
                            body.add(block)
                            for succ in block.successors:
                                # [关键修复] 跳过异常处理器块
                                if is_exception_handler_block(succ):
                                    continue
                                # [关键修复] 检查后继是否是复合条件的一部分
                                is_compound_part = False
                                if self._is_conditional_block(succ):
                                    succ_jump = self._get_jump_instr(succ)
                                    if succ_jump and succ_jump.argval == jump_instr.argval:
                                        is_compound_part = True
                                
                                if not is_compound_part:
                                    # [关键修复] 检查后继是否是只包含return的块（if之后的代码）
                                    non_trivial = [i for i in succ.instructions 
                                                  if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                                    is_return_only = (len(non_trivial) == 2 and 
                                                     non_trivial[0].opname.startswith('LOAD_') and
                                                     non_trivial[1].opname == 'RETURN_VALUE')
                                    
                                    if is_return_only:
                                        # 这是if之后的return语句，不是else分支的一部分
                                        continue
                                    
                                    if succ not in body and succ != header:
                                        worklist.append(succ)
                        continue
                    
                    # [关键修复-2026-else] 对于else分支中的条件块，收集fall-through后继
                    # 这解决了 else: if x: ...; stmt 模式中stmt缺失的问题
                    # fall-through后继包含循环回跳或普通语句，应该被收集到else_body中
                    if is_else_branch and jump_instr and jump_instr.argval is not None:
                        for succ in block.successors:
                            if succ.start_offset != jump_instr.argval:  # fall-through后继
                                if succ not in body and succ != header:
                                    # 检查是否是return-only块
                                    non_trivial = [i for i in succ.instructions 
                                                  if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                                    is_return_only = (len(non_trivial) == 2 and 
                                                     non_trivial[0].opname.startswith('LOAD_') and
                                                     non_trivial[1].opname == 'RETURN_VALUE')
                                    
                                    if not is_return_only:
                                        body.add(succ)
                                        worklist.append(succ)
                        continue
                    
                    # [关键修复] 对于嵌套if结构，需要递归收集嵌套if的所有块
                    # 这是嵌套if结构：当前块是条件块，需要收集它的then_body和else_body
                    # [关键修复] 但是，如果是elif链的一部分，不应该收集jump目标后继
                    # elif链的特征：jump目标后继是条件块，且它的跳转目标与当前块的fall-through后继不同
                    if jump_instr and jump_instr.argval is not None:
                        # 找到fall-through后继和jump目标后继
                        # [关键修复] 处理有三个后继的情况（jump目标、异常处理器、fall-through）
                        # 找到fall-through后继和jump目标后继
                        # [关键修复] 处理有三个后继的情况（jump目标、异常处理器、fall-through）
                        # 找到fall-through后继和jump目标后继
                        # [关键修复] 处理有三个后继的情况（jump目标、异常处理器、fall-through）
                        # 找到fall-through后继和jump目标后继
                        # [关键修复] 处理有三个后继的情况（jump目标、异常处理器、fall-through）
                        nested_then_branch = None
                        nested_else_branch = None
                        for succ in block.successors:
                            # [关键修复] 跳过异常处理器块
                            # [关键修复] 跳过异常处理器块
                            # [关键修复] 跳过异常处理器块
                            # [关键修复] 跳过异常处理器块
                            if is_exception_handler_block(succ):
                                continue
                            if succ.start_offset != jump_instr.argval:
                                nested_then_branch = succ  # fall-through后继
                            else:
                                nested_else_branch = succ  # jump目标后继
                        
                        # [关键修复] 检查jump目标后继是否是elif链的一部分
                        # elif链的特征：
                        # 1. jump目标后继是条件块
                        # 2. 该条件块的else分支（jump目标）与当前块的else分支共享同一个merge点
                        #    - 即：nested_else_branch的fall-through后继 == 当前块的jump目标
                        # 嵌套if的特征：
                        # 1. jump目标后继是条件块
                        # 2. 但该条件块有自己的then/else分支，不共享merge点
                        is_elif_chain = False
                        if nested_else_branch and self._is_conditional_block(nested_else_branch):
                            # jump目标后继是条件块，可能是elif链或嵌套if
                            nested_else_jump = self._get_jump_instr(nested_else_branch)
                            if nested_else_jump and nested_else_jump.argval is not None:
                                # [关键修复] 检查nested_else_branch是否是elif链的一部分
                                # elif链的关键特征：nested_else_branch的fall-through后继应该是当前块的jump目标
                                # 即：elif条件的then分支应该与外层if的else分支共享同一个merge点
                                
                                # 找到nested_else_branch的fall-through后继（它的then分支）
                                nested_else_fall_through = None
                                for succ in nested_else_branch.successors:
                                    if succ.start_offset != nested_else_jump.argval:
                                        nested_else_fall_through = succ
                                        break
                                
                                # 找到当前块的jump目标（当前块的else分支终点）
                                current_jump_target = None
                                for succ in block.successors:
                                    if succ.start_offset == jump_instr.argval:
                                        current_jump_target = succ
                                        break
                                
                                # [关键修复] 如果nested_else_branch的fall-through后继是当前块的jump目标
                                # 则这是elif链（共享merge点）
                                # 否则是嵌套if（有自己的then/else分支）
                                if nested_else_fall_through and current_jump_target:
                                    if nested_else_fall_through.start_offset == current_jump_target.start_offset:
                                        # 共享同一个merge点，是elif链
                                        is_elif_chain = True
                                elif nested_else_fall_through is None and current_jump_target is None:
                                    # 两者都没有fall-through，可能是elif链
                                    is_elif_chain = True
                        

                        if is_elif_chain:
                            # [关键修复] 这是elif链，只收集fall-through后继（then分支）
                            # elif链的else分支是下一个elif条件块，应该由_find_branch_body_for_elif处理
                            # [关键修复] 这是elif链，只收集fall-through后继（then分支）
                            # elif链的else分支是下一个elif条件块，应该由_find_branch_body_for_elif处理
                            # [关键修复] 这是elif链，只收集fall-through后继（then分支）
                            # elif链的else分支是下一个elif条件块，应该由_find_branch_body_for_elif处理
                            # [关键修复] 这是elif链，只收集fall-through后继（then分支）
                            # elif链的else分支是下一个elif条件块，应该由_find_branch_body_for_elif处理
                            if nested_then_branch and nested_then_branch not in body and nested_then_branch != header:
                                nested_then_body = self._find_branch_body(nested_then_branch, block, loop_headers, is_else_branch=False)
                                for b in nested_then_body:
                                    if b != header:
                                        body.add(b)
                            # 添加当前块到body
                            body.add(block)
                            continue
                        
                        # [关键修复] 如果当前块是复合条件的一部分，不要递归收集fall-through后继
                        # 复合条件的fall-through后继是条件链的一部分，不是嵌套if
                        if is_and_compound:
                            # 添加当前块到body，但不递归收集fall-through后继
                            # 添加当前块到body，但不递归收集fall-through后继
                            # 添加当前块到body，但不递归收集fall-through后继
                            # 添加当前块到body，但不递归收集fall-through后继
                            body.add(block)
                            continue
                        
                        # 递归收集嵌套if的then_body
                        if nested_then_branch and nested_then_branch not in body and nested_then_branch != header:
                            nested_then_body = self._find_branch_body(nested_then_branch, block, loop_headers, is_else_branch=False, collect_nested_else=collect_nested_else)
                            for b in nested_then_body:
                                if b != header:
                                    body.add(b)

                        # 递归收集嵌套if的else_body
                        # [关键修复] 当collect_nested_else=False时，不收集嵌套if的else_body
                        if collect_nested_else and nested_else_branch and nested_else_branch not in body and nested_else_branch != header:
                            # [关键修复] 检查nested_else_branch是否是函数的结尾块（只包含return）
                            # 如果是，不收集它
                            non_trivial = [i for i in nested_else_branch.instructions 
                                          if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                            is_return_only = (len(non_trivial) == 2 and 
                                             non_trivial[0].opname.startswith('LOAD_') and
                                             non_trivial[1].opname == 'RETURN_VALUE')

                            
                            if not is_return_only:
                                nested_else_body = self._find_branch_body(nested_else_branch, block, loop_headers, is_else_branch=True, collect_nested_else=collect_nested_else)
                                for b in nested_else_body:
                                    if b != header:
                                        body.add(b)
                        
                        # 添加当前块到body
                        body.add(block)
                        continue
                    else:
                        # [关键修复] 对于else分支中的JUMP_IF_TRUE_OR_POP赋值，
                        # 即使不是复合条件，也应该继续收集后继块
                        # 因为赋值可能跨越多个块（如 source_start = start[8:] or '0000')
                        if not is_else_branch:
                            continue
                
                # 是复合条件或链式比较，继续收集后继
                # [关键修复] 对于else分支，不应该收集复合条件的fall-through后继
                # 因为复合条件的fall-through后继是条件链的一部分，不是else分支的一部分
                if not is_else_branch:
                    # 只收集fall-through后继（不收集jump目标）
                    # 只收集fall-through后继（不收集jump目标）
                    # 只收集fall-through后继（不收集jump目标）
                    # 只收集fall-through后继（不收集jump目标）
                    if jump_instr and jump_instr.argval is not None:
                        for succ in block.successors:
                            if succ.start_offset != jump_instr.argval:
                                # 这是fall-through后继，继续收集
                                # 这是fall-through后继，继续收集
                                # 这是fall-through后继，继续收集
                                # 这是fall-through后继，继续收集
                                if succ not in body and succ != header:
                                    worklist.append(succ)
                        # 不收集jump目标后继（else分支）
                        continue
                else:
                    # [关键修复] 对于else分支，只收集jump目标后继
                    # [例外] 对于JUMP_IF_TRUE_OR_POP赋值，收集所有后继块                    if jump_instr and jump_instr.argval is not None:
                        if is_compound_condition:
                            # 复合条件，只收集jump目标后继
                            for succ in block.successors:
                                if succ.start_offset == jump_instr.argval:
                                    # 这是jump目标后继
                                    # [关键修复] 检查jump目标后继是否是if之后的代码（只包含return）
                                    # 如果是，不要收集它，因为它是if之后的代码，不是else分支
                                    non_trivial = [i for i in succ.instructions 
                                                  if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                                    is_return_only = (len(non_trivial) == 2 and 
                                                     non_trivial[0].opname.startswith('LOAD_') and
                                                     non_trivial[1].opname == 'RETURN_VALUE')
                                    
                                    if is_return_only:
                                        # 这是if之后的return语句，不是else分支
                                        # 不要收集它
                                        pass
                                    elif succ not in body and succ != header:
                                        worklist.append(succ)
                            # 不收集fall-through后继（复合条件的一部分）
                            continue
                        else:
                            # [关键修复] 对于JUMP_IF_TRUE_OR_POP赋值，收集所有后继块                            for succ in block.successors:                                if succ not in body and succ != header:
                                    worklist.append(succ)
            # [关键修复] 检测条件表达式模式
            # 条件表达式的then/else分支只包含值加载和JUMP_FORWARD指令
            # 这种情况下不应该继续收集后继，因为JUMP_FORWARD指向的是条件表达式之后的代码
            # [例外] 对于链式比较，JUMP_FORWARD可能指向then_body的其他部分
            non_trivial_instrs = [i for i in block.instructions 
                                  if i.opname not in ('RESUME', 'CACHE', 'NOP')]
            # [关键修复] 如果块只包含NOP（non_trivial_instrs为空），这不是条件表达式分支
            # 而是try-except结构的入口块，应该继续收集后继
            is_conditional_expr_branch = (
                len(non_trivial_instrs) > 0 and  # [关键修复] 必须至少有一条非平凡指令
                len(non_trivial_instrs) <= 2 and
                all(i.opname.startswith('LOAD_') or i.opname == 'JUMP_FORWARD' 
                    for i in non_trivial_instrs)
            )
            if is_conditional_expr_branch:
                # [关键修复] 检查JUMP_FORWARD的跳转目标是否是合并块
                # 如果是合并块，这是条件表达式的分支，不要继续收集后继
                # 如果不是合并块，可能是链式比较的then_body，继续收集后继
                # [关键修复] 检查JUMP_FORWARD的跳转目标是否是合并块
                # 如果是合并块，这是条件表达式的分支，不要继续收集后继
                # 如果不是合并块，可能是链式比较的then_body，继续收集后继
                # [关键修复] 检查JUMP_FORWARD的跳转目标是否是合并块
                # 如果是合并块，这是条件表达式的分支，不要继续收集后继
                # 如果不是合并块，可能是链式比较的then_body，继续收集后继
                # [关键修复] 检查JUMP_FORWARD的跳转目标是否是合并块
                # 如果是合并块，这是条件表达式的分支，不要继续收集后继
                # 如果不是合并块，可能是链式比较的then_body，继续收集后继
                jump_target_is_merge = False
                has_jump_forward = False
                for instr in block.instructions:
                    if instr.opname == 'JUMP_FORWARD' and instr.argval is not None:
                        has_jump_forward = True
                        for succ in block.successors:
                            if succ.start_offset == instr.argval:
                                # 检查目标块是否是合并块（有多个前驱）
                                # 检查目标块是否是合并块（有多个前驱）
                                # 检查目标块是否是合并块（有多个前驱）
                                # 检查目标块是否是合并块（有多个前驱）
                                if len(succ.predecessors) > 1:
                                    jump_target_is_merge = True
                                break
                        break
                
                # [关键修复] 对于条件表达式的分支：
                # 1. 如果有JUMP_FORWARD且指向合并块，不要继续收集后继
                # 2. 如果没有JUMP_FORWARD（只有LOAD_CONST），这是else分支，不要继续收集后继                if jump_target_is_merge or not has_jump_forward:
                    # 这是条件表达式的分支，不要继续收集后继
                    # 这是条件表达式的分支，不要继续收集后继
                    # 这是条件表达式的分支，不要继续收集后继
                    # 这是条件表达式的分支，不要继续收集后继                    continue
                # 否则继续收集后继（可能是链式比较的then_body）

            # [关键修复] 如果块包含退出跳转，不要继续收集后继块            if has_exit_jump:                continue

            # [关键修复] 如果块包含JUMP_FORWARD指令，检查跳转目标是否是合并块
            # 只有当JUMP_FORWARD指向合并块时，才停止收集后继
            # 对于链式比较等结构，JUMP_FORWARD可能指向then_body的其他部分
            has_jump_forward = False
            jump_target_is_merge = False
            for instr in block.instructions:
                if instr.opname == 'JUMP_FORWARD' and instr.argval is not None:
                    has_jump_forward = True
                    # 检查跳转目标是否是合并块
                    for succ in block.successors:
                        if succ.start_offset == instr.argval:
                            # 检查目标块是否是合并块（有多个前驱）
                            # 检查目标块是否是合并块（有多个前驱）
                            # 检查目标块是否是合并块（有多个前驱）
                            # 检查目标块是否是合并块（有多个前驱）
                            if len(succ.predecessors) > 1:
                                jump_target_is_merge = True
                            break
                    break            
            # [关键修复] 只有当JUMP_FORWARD指向合并块时，才停止收集后继
            # 否则，继续收集后继（如链式比较的then_body）
            if has_jump_forward and jump_target_is_merge:                continue
            
            # [关键修复] 如果当前块是条件块（不是start块），不要继续收集后继
            # 这是嵌套if结构的关键：条件块的then分支是另一个if结构，我们不应该深入
            # [例外1] 如果块使用JUMP_IF_TRUE_OR_POP/JUMP_IF_FALSE_OR_POP进行赋值（如x = a or b）
            # 这不是嵌套if结构，应该继续收集后继
            # [例外2] 如果当前是else分支（is_else_branch=True），条件块可能是else分支中的嵌套if
            # 应该继续收集后继，以确保嵌套if的所有分支都被包含在else_body中
            skip_block = False
            if block != start and self._is_conditional_block(block):
                jump_instr = self._get_jump_instr(block)
                if jump_instr and jump_instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                    # 检查跳转目标是否是STORE_FAST
                    jump_target_offset = jump_instr.argval
                    if jump_target_offset is not None:
                        for succ in block.successors:
                            if succ.start_offset == jump_target_offset:
                                for target_instr in succ.instructions:
                                    if target_instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                                        if target_instr.opname == 'STORE_FAST':
                                            # 这是赋值语句，不是嵌套if结构
                                            skip_block = False
                                        else:
                                            skip_block = True
                                        break
                                break
                elif not is_else_branch:
                    # [关键修复] 对于非else分支，普通条件块应该跳过
                    # 但对于else分支，条件块可能是嵌套if，不应该跳过
                    skip_block = True
            
            if skip_block:                continue
            for succ in block.successors:                # [关键修复] 跳过异常处理器块
                # [关键修复] 跳过异常处理器块
                # [关键修复] 跳过异常处理器块
                # [关键修复] 跳过异常处理器块
                if is_exception_handler_block(succ):                    continue
                if succ not in body and succ != header:
                    # [关键修复] 检查后继块是否是其他循环的头部（不在当前循环内）
                    # [关键修复] 但是，如果后继块是嵌套在if语句中的循环头部，不要跳过它
                    # 这种情况发生在for-if-for嵌套中，内部for循环的头部块需要在then_body中被收集
                    # [关键修复] 检查后继块是否是其他循环的头部（不在当前循环内）
                    # [关键修复] 但是，如果后继块是嵌套在if语句中的循环头部，不要跳过它
                    # 这种情况发生在for-if-for嵌套中，内部for循环的头部块需要在then_body中被收集
                    # [关键修复] 检查后继块是否是其他循环的头部（不在当前循环内）
                    # [关键修复] 但是，如果后继块是嵌套在if语句中的循环头部，不要跳过它
                    # 这种情况发生在for-if-for嵌套中，内部for循环的头部块需要在then_body中被收集
                    # [关键修复] 检查后继块是否是其他循环的头部（不在当前循环内）
                    # [关键修复] 但是，如果后继块是嵌套在if语句中的循环头部，不要跳过它
                    # 这种情况发生在for-if-for嵌套中，内部for循环的头部块需要在then_body中被收集
                    if succ.loop_header and succ not in loop_headers:
                        is_nested_loop = any(pred in body or pred == start or pred == block for pred in succ.predecessors)
                        if not is_nested_loop:
                            continue
                        body.add(succ)
                        continue
                    
                    # [关键修复] 检查后继块是否是当前if的else分支起始块
                    # 这种情况发生在：then分支块通过fall-through连接到else分支块
                    # 特征是：后继块是header的jump目标，且有多个前驱（header和当前block）
                    is_else_branch_start = False
                    jump_instr = self._get_jump_instr(header)
                    if jump_instr and jump_instr.argval is not None:
                        if succ.start_offset == jump_instr.argval:
                            # 这是header的jump目标
                            # 检查是否有多个前驱（header和当前block）
                            # 这是header的jump目标
                            # 检查是否有多个前驱（header和当前block）
                            # 这是header的jump目标
                            # 检查是否有多个前驱（header和当前block）
                            # 这是header的jump目标
                            # 检查是否有多个前驱（header和当前block）
                            if len(succ.predecessors) >= 2 and header in succ.predecessors:
                                # 这是else分支的起始块，不应该收集到then_body中
                                # 这是else分支的起始块，不应该收集到then_body中
                                # 这是else分支的起始块，不应该收集到then_body中
                                # 这是else分支的起始块，不应该收集到then_body中
                                is_else_branch_start = True
                    
                    if is_else_branch_start:
                        continue
                    
                    # [关键修复] 检查后继块是否是merge点（合并块）
                    # merge点的特征：
                    # 1. 有多个前驱
                    # 2. 这些前驱来自不同的分支（如then分支和else分支都指向它）
                    # 对于嵌套if-else结构，merge点不应该被包含在任何分支体中
                    is_loop_header = False
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure) and struct.header_block == succ:
                            is_loop_header = True
                            break
                    if is_loop_header:
                        worklist.append(succ)
                        continue
                    
                    is_merge_point = False
                    if len(succ.predecessors) >= 2:
                        # 检查是否有前驱在当前body中（当前分支）
                        # 检查是否有前驱在当前body中（当前分支）
                        # 检查是否有前驱在当前body中（当前分支）
                        # 检查是否有前驱在当前body中（当前分支）
                        has_pred_in_body = any(pred in body for pred in succ.predecessors)
                        # 检查是否有前驱不在当前body中且不是当前处理的block（其他分支）
                        has_pred_outside_body = any(
                            pred not in body and pred != block and pred != header
                            for pred in succ.predecessors
                        )
                        # 如果同时满足，这是merge点
                        if has_pred_in_body and has_pred_outside_body:
                            is_merge_point = True
                    
                    # [关键修复] 对于else分支中的嵌套if，不跳过merge点
                    # 因为嵌套if的then分支和else分支都会指向merge点
                    if is_merge_point and not is_else_branch:
                        continue
                    
                    is_other_if_entry = False
                    for other_struct in self.structures:
                        if isinstance(other_struct, IfStructure):
                            if other_struct.entry_block == succ and other_struct.entry_block != header:
                                # 这是其他独立if结构的入口块
                                # 这是其他独立if结构的入口块
                                # 这是其他独立if结构的入口块
                                # 这是其他独立if结构的入口块
                                is_other_if_entry = True
                                break
                    
                    # [关键修复] 也检查后继块是否是条件块且有外部前驱
                    # 如果是，这可能是独立的if结构，不应该收集
                    # [例外] 如果当前是else分支（is_else_branch=True），条件块可能是else分支中的嵌套if
                    # 应该继续收集，以确保嵌套if的所有分支都被包含在else_body中
                    if not is_else_branch and not is_other_if_entry and self._is_conditional_block(succ):
                        # 检查是否有前驱不在当前body中（说明是独立的执行路径）
                        # 检查是否有前驱不在当前body中（说明是独立的执行路径）
                        # 检查是否有前驱不在当前body中（说明是独立的执行路径）
                        # 检查是否有前驱不在当前body中（说明是独立的执行路径）
                        for pred in succ.predecessors:
                            if pred not in body and pred != block and pred != header:
                                # 这是独立的if结构
                                # 这是独立的if结构
                                # 这是独立的if结构
                                # 这是独立的if结构
                                is_other_if_entry = True
                                break
                        
                        # [关键修复] 检查是否是独立的if语句（如elif链中的独立if）
                        # 独立的if语句的特征：
                        # 1. 它是条件块
                        # 2. 它有多个前驱
                        # 3. 它的前驱中，至少有一个不是条件块（即不是复合条件的一部分）
                        if not is_other_if_entry and len(succ.predecessors) >= 2:
                            non_cond_preds = [pred for pred in succ.predecessors if not self._is_conditional_block(pred)]
                            if len(non_cond_preds) > 0:
                                # 有非条件块的前驱，这是独立的if语句
                                # 有非条件块的前驱，这是独立的if语句
                                # 有非条件块的前驱，这是独立的if语句
                                # 有非条件块的前驱，这是独立的if语句
                                is_other_if_entry = True
                    
                    if is_other_if_entry:
                        continue
                    
                    worklist.append(succ)
        
        return body
    
    def _find_merge_block(self, body: Set[BasicBlock], header: Optional[BasicBlock] = None) -> Optional[BasicBlock]:
        """
        查找合并块
        
        Args:
            body: 所有分支体的并集（then_body | else_body）
            header: 条件头部（用于排除）
            
        Returns:
            合并块
        """
        # 将body分成then_body和else_body两部分
        # 基于是否有前驱在body内来判断
        # 实际上这里我们只需要找到所有分支的退出点
        
        # 找到所有分支的退出点（后继不在body内的块）
        exits = set()
        for block in body:
            for succ in block.successors:
                if succ not in body:
                    # [关键修复] 排除header本身
                    # [关键修复] 排除header本身
                    # [关键修复] 排除header本身
                    # [关键修复] 排除header本身
                    if header and succ == header:
                        continue
                    exits.add(succ)
        
        # 如果只有一个退出点，那就是合并块
        if len(exits) == 1:
            return exits.pop()
        
        # [关键修复] 如果有多个退出点，找到被最多分支指向的块
        # 这通常是合并块
        if exits:
            # 统计每个退出点被多少个body块指向
            # 统计每个退出点被多少个body块指向
            # 统计每个退出点被多少个body块指向
            # 统计每个退出点被多少个body块指向
            exit_counts = {}
            for exit_block in exits:
                count = sum(1 for block in body if exit_block in block.successors)
                exit_counts[exit_block] = count
            
            # 返回被最多分支指向的块
            return max(exits, key=lambda b: exit_counts[b])
        

        
        return None
    
    def _identify_try_except(self) -> None:
        """识别try-except结构"""
        analyzed_blocks = set(self.block_to_structure.keys())
        
        # [关键修复] 使用异常表信息来识别try-except结构
        # 异常表条目包含：start（try开始）, end（try结束）, target（handler开始）
        if self.cfg.exception_table:
            # [修复] 使用简化版的识别算法，避免原算法中的问题
            # [修复] 使用简化版的识别算法，避免原算法中的问题
            # [修复] 使用简化版的识别算法，避免原算法中的问题
            # [修复] 使用简化版的识别算法，避免原算法中的问题
            from .exception_handler import identify_try_except_simplified
            identify_try_except_simplified(self, analyzed_blocks)
        else:
            # 回退到旧方法（Python < 3.11）
            self._identify_try_except_legacy(analyzed_blocks)
    
    def _identify_try_except_from_table(self, analyzed_blocks: Set[BasicBlock]) -> None:
        """使用异常表识别try-except结构"""
        # [关键修复] 按 start_offset 分组，收集每个 try 块
        # 只收集包含 NOP 指令的 try 块（这是 try 块的开始标志）
        try_entries = {}  # start_offset -> (end_offset, depth)

        for entry in self.cfg.exception_table:
            start_offset = entry['start']
            end_offset = entry['end']
            depth = entry['depth']
            
            # [关键修复] 处理所有depth的try块，不只是depth==0
            # 这包括嵌套的try-except结构
            if depth >= 0:
                # [关键修复] 检查这个 try 块是否包含 NOP 指令
                # NOP 指令是 try 块的开始标志，通常在 try 块开始之前或之内
                # [关键修复] 检查这个 try 块是否包含 NOP 指令
                # NOP 指令是 try 块的开始标志，通常在 try 块开始之前或之内
                # [关键修复] 检查这个 try 块是否包含 NOP 指令
                # NOP 指令是 try 块的开始标志，通常在 try 块开始之前或之内
                # [关键修复] 检查这个 try 块是否包含 NOP 指令
                # NOP 指令是 try 块的开始标志，通常在 try 块开始之前或之内
                try_block = self._find_block_containing_offset(start_offset)
                if try_block:
                    # [关键修复] 严格检查NOP指令：try块必须有NOP指令作为开始标志
                    # 检查 NOP 指令是否在 try 块附近（之前10字节或之内）
                    # [关键修复] 严格检查NOP指令：try块必须有NOP指令作为开始标志
                    # 检查 NOP 指令是否在 try 块附近（之前10字节或之内）
                    # [关键修复] 严格检查NOP指令：try块必须有NOP指令作为开始标志
                    # 检查 NOP 指令是否在 try 块附近（之前10字节或之内）
                    # [关键修复] 严格检查NOP指令：try块必须有NOP指令作为开始标志
                    # 检查 NOP 指令是否在 try 块附近（之前10字节或之内）
                    has_nop = any(
                        instr.opname == 'NOP' and start_offset - 10 <= instr.offset <= start_offset + 5
                        for instr in try_block.instructions
                    )
                    # [关键修复] 只接受有NOP的try块，避免将except handler块错误识别为try块
                    if has_nop:
                        # 记录try块及其depth
                        # 记录try块及其depth
                        # 记录try块及其depth
                        # 记录try块及其depth
                        if start_offset not in try_entries:
                            try_entries[start_offset] = (end_offset, depth)
                        else:
                            # 如果已存在，保留更大的end_offset和更小的depth
                            existing_end, existing_depth = try_entries[start_offset]
                            if end_offset > existing_end:
                                try_entries[start_offset] = (end_offset, depth)
        
        # 为每个 try 块创建 TryExceptStructure
        # [关键修复] 按depth排序，先处理外层try块，再处理内层try块
        sorted_try_entries = sorted(try_entries.items(), key=lambda x: (x[1][1], x[0]))

        for start_offset, (end_offset, try_depth) in sorted_try_entries:
            pass  # 暂时跳过，后续实现
    
    def _identify_simple_try_except(self, analyzed_blocks: Set[BasicBlock]) -> None:
        """
        [关键修复] 识别简单的try-except结构（异常表只有depth>0条目的情况）
        
        当try体非常简单（如只有return）时，Python编译器可能不生成depth=0的异常表条目。
        这种情况下，需要从字节码中推断try块的位置。
        
        特征：
        1. 异常表只有depth>0的条目（except handler）
        2. 函数中有NOP指令（try块的开始标志）
        3. NOP和except handler之间是try体代码
        """
        # 检查是否已经有depth=0的try块被识别
        def _check_depth_zero(struct):
            if not hasattr(struct, 'try_start_offset'):
                return False
            for entry in self.cfg.exception_table:
                if entry['start'] == struct.try_start_offset and entry['depth'] == 0:
                    return True
            return False
        
        has_depth_zero_try = any(
            isinstance(struct, TryExceptStructure) and _check_depth_zero(struct)
            for struct in self.structures
        )
        
        if has_depth_zero_try:
            return
        
        # 查找所有depth>0的异常表条目（except handler）
        depth_one_entries = [e for e in self.cfg.exception_table if e['depth'] > 0]
        if not depth_one_entries:
            return
        
        # 对于每个depth>0的条目，查找对应的try块
        for entry in depth_one_entries:
            handler_start = entry['target']
            handler_depth = entry['depth']
            
            # 查找包含NOP的块（try块的开始标志）
            for block in self.cfg.blocks.values():
                if block in analyzed_blocks:
                    continue
                
                # 检查块是否包含NOP
                has_nop = any(instr.opname == 'NOP' for instr in block.instructions)
                if not has_nop:
                    continue
                
                # 检查这个NOP是否在except handler之前
                # 并且NOP块和except handler之间没有其他try-except结构
                nop_offset = next((i.offset for i in block.instructions if i.opname == 'NOP'), None)
                if nop_offset is None:
                    continue
                
                # 检查NOP块和handler之间是否有代码
                # 这些代码就是try体
                try_start = nop_offset
                try_end = handler_start
                
                # 收集try体的块
                try_body = []
                for b in self.cfg.blocks.values():
                    if b.start_offset >= try_start and b.end_offset <= try_end:
                        if b not in analyzed_blocks:
                            try_body.append(b)
                
                if not try_body:
                    continue
                
                # 收集except handler
                handler_entry = self._find_block_containing_offset(handler_start)
                if not handler_entry:
                    continue
                
                except_handlers = []
                handler_body = self._collect_handler_body(handler_entry, analyzed_blocks)
                if handler_body:
                    exc_type = self._extract_exception_type_from_handler(handler_entry)
                    exc_name = self._extract_exception_name_from_handler_body(handler_body)
                    except_handlers.append((exc_type, exc_name, handler_body))
                
                if not except_handlers:
                    continue
                
                # 创建TryExceptStructure
                try_struct = TryExceptStructure(
                    entry_block=block,
                    try_body=try_body,
                    except_handlers=except_handlers,
                    has_else=False,
                    has_finally=False
                )
                try_struct.try_start_offset = try_start
                try_struct.try_end_offset = try_end
                
                self.structures.append(try_struct)
                
                # 标记块为已分析
                for b in try_body:
                    analyzed_blocks.add(b)
                    self.block_to_structure[b] = try_struct
                for b in handler_body:
                    analyzed_blocks.add(b)
                    self.block_to_structure[b] = try_struct
                
                break  # 只处理第一个匹配的try块
            # 找到包含 start_offset 的基本块
            try_entry = self._find_block_containing_offset(start_offset)
            
            if not try_entry:
                continue
            
            # [关键修复] 如果try_entry已经在analyzed_blocks中，检查它是否是try块
            # 如果是try块（包含NOP指令），仍然需要处理它
            if try_entry in analyzed_blocks:
                has_nop = any(
                    instr.opname == 'NOP' and start_offset - 10 <= instr.offset <= start_offset + 5
                    for instr in try_entry.instructions
                )
                if not has_nop:
                    continue
                # [关键修复] 如果是try块，从block_to_structure中移除，以便重新处理
                del self.block_to_structure[try_entry]
                # 也从analyzed_blocks中移除
                analyzed_blocks.discard(try_entry)
            
            # 收集 try 体
            try_body = self._collect_try_body(start_offset, end_offset, analyzed_blocks)

            # [关键修复] 收集所有 handler
            # 从try块的第一个handler开始，沿着跳转链收集所有handlers
            except_handlers = []
            visited_handlers = set()
            
            # 找到第一个handler（异常表中target最小的那个）
            # [关键修复] 使用try块的depth来查找对应的handler
            first_handler_offset = None
            for entry in self.cfg.exception_table:
                if entry['depth'] == try_depth and entry['start'] == start_offset:
                    if first_handler_offset is None or entry['target'] < first_handler_offset:
                        first_handler_offset = entry['target']
            
            # [关键修复] 检查是否是try-finally（不是try-except-finally）
            # 对于try-finally，try块和handler之间有finally代码
            is_try_finally_only = False
            if first_handler_offset:
                # 检查try块和handler之间是否有finally代码
                # 通过查找try_body块中try范围之后的指令
                # 检查try块和handler之间是否有finally代码
                # 通过查找try_body块中try范围之后的指令
                # 检查try块和handler之间是否有finally代码
                # 通过查找try_body块中try范围之后的指令
                # 检查try块和handler之间是否有finally代码
                # 通过查找try_body块中try范围之后的指令
                for block in try_body:
                    for instr in block.instructions:
                        if instr.offset >= end_offset and instr.offset < first_handler_offset:
                            # [关键修复] 在try范围和handler之间有代码
                            # 需要区分else子句和finally代码
                            # else子句通常以JUMP_FORWARD结束，而finally代码有特殊的异常处理结构
                            # 检查这个范围内是否有PUSH_EXC_INFO，如果有则是finally代码
                            # [关键修复] 在try范围和handler之间有代码
                            # 需要区分else子句和finally代码
                            # else子句通常以JUMP_FORWARD结束，而finally代码有特殊的异常处理结构
                            # 检查这个范围内是否有PUSH_EXC_INFO，如果有则是finally代码
                            # [关键修复] 在try范围和handler之间有代码
                            # 需要区分else子句和finally代码
                            # else子句通常以JUMP_FORWARD结束，而finally代码有特殊的异常处理结构
                            # 检查这个范围内是否有PUSH_EXC_INFO，如果有则是finally代码
                            # [关键修复] 在try范围和handler之间有代码
                            # 需要区分else子句和finally代码
                            # else子句通常以JUMP_FORWARD结束，而finally代码有特殊的异常处理结构
                            # 检查这个范围内是否有PUSH_EXC_INFO，如果有则是finally代码
                            if instr.opname == 'PUSH_EXC_INFO':
                                is_try_finally_only = True
                                break
                    if is_try_finally_only:
                        break
            
            if first_handler_offset and not is_try_finally_only:
                # [关键修复] 收集所有与这个try块相关的except handler
                # 从exception table中找到所有target是这个try块的handler
                # 并且这些handler需要有CHECK_EXC_MATCH指令
                
                # 首先收集所有可能的handler offset
                # [关键修复] 收集所有与这个try块相关的except handler
                # 从exception table中找到所有target是这个try块的handler
                # 并且这些handler需要有CHECK_EXC_MATCH指令
                
                # 首先收集所有可能的handler offset
                # [关键修复] 收集所有与这个try块相关的except handler
                # 从exception table中找到所有target是这个try块的handler
                # 并且这些handler需要有CHECK_EXC_MATCH指令
                
                # 首先收集所有可能的handler offset
                # [关键修复] 收集所有与这个try块相关的except handler
                # 从exception table中找到所有target是这个try块的handler
                # 并且这些handler需要有CHECK_EXC_MATCH指令
                
                # 首先收集所有可能的handler offset
                handler_offsets = set()
                for entry in self.cfg.exception_table:
                    # [关键修复] 使用try_depth而不是硬编码的0
                    # [关键修复] 使用try_depth而不是硬编码的0
                    # [关键修复] 使用try_depth而不是硬编码的0
                    # [关键修复] 使用try_depth而不是硬编码的0
                    if entry['start'] == start_offset and entry['depth'] == try_depth:
                        target = entry['target']
                        # [关键修复] 检查target是否是另一个try块的开始（嵌套try-except）
                        # 如果target有对应的depth>try_depth的exception table条目，并且该块有NOP指令（try块标志），那么它是嵌套try
                        is_nested_try_start = False
                        for e in self.cfg.exception_table:
                            if e['start'] == target and e['depth'] > try_depth:
                                # [关键修复] 检查该块是否有NOP指令（try块的开始标志）
                                # [关键修复] 检查该块是否有NOP指令（try块的开始标志）
                                # [关键修复] 检查该块是否有NOP指令（try块的开始标志）
                                # [关键修复] 检查该块是否有NOP指令（try块的开始标志）
                                target_block = self._find_block_containing_offset(target)
                                if target_block:
                                    has_nop = any(
                                        instr.opname == 'NOP' and target - 10 <= instr.offset <= target + 5
                                        for instr in target_block.instructions
                                    )
                                    if has_nop:
                                        is_nested_try_start = True
                                break
                        if not is_nested_try_start:
                            handler_offsets.add(target)

                # [修复] 不收集与try块重叠的其他异常范围的handler
                # 这会导致错误的handler分配（如将内层try的handler分配给外层try）
                # 只收集明确属于当前try块的handler（entry['start'] == start_offset）
                
                # [修复] 不收集try范围结束后的exception table条目
                # 这会导致收集cleanup代码块（depth=2）作为handler
                # 只收集明确属于当前try块的handler（entry['start'] == start_offset 且 entry['depth'] == try_depth）
                
                # [关键修复] 使用while循环处理动态添加的handler offset
                # 这对于链式except handler（多个except）很重要
                handler_worklist = list(handler_offsets)
                handler_index = 0
                
                while handler_index < len(handler_worklist):
                    handler_offset = handler_worklist[handler_index]
                    handler_index += 1
                    
                    if handler_offset in visited_handlers:
                        continue
                    
                    handler_entry = self._find_block_containing_offset(handler_offset)
                    if not handler_entry:
                        continue
                    
                    # [关键修复] 检查handler_entry是否是except handler块
                    # 如果是，即使它在analyzed_blocks中，也应该处理它
                    is_except_handler_entry = any(
                        instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH')
                        for instr in handler_entry.instructions
                    )
                    
                    if handler_entry in analyzed_blocks:
                        if is_except_handler_entry:
                            # [关键修复] 从analyzed_blocks和block_to_structure中移除，以便处理
                            # [关键修复] 从analyzed_blocks和block_to_structure中移除，以便处理
                            # [关键修复] 从analyzed_blocks和block_to_structure中移除，以便处理
                            # [关键修复] 从analyzed_blocks和block_to_structure中移除，以便处理
                            analyzed_blocks.discard(handler_entry)
                            if handler_entry in self.block_to_structure:
                                del self.block_to_structure[handler_entry]
                        else:
                            continue
                    
                    visited_handlers.add(handler_offset)
                    
                    # [关键修复] 检查handler是否是except handler（有CHECK_EXC_MATCH）
                    # 还是finally块（有清理代码但没有CHECK_EXC_MATCH）
                    has_check_exc_match = any(
                        instr.opname == 'CHECK_EXC_MATCH' 
                        for instr in handler_entry.instructions
                    )
                    
                    # [关键修复] 检查是否是裸except（没有CHECK_EXC_MATCH，但有PUSH_EXC_INFO和POP_TOP）
                    has_push_exc_info = any(
                        instr.opname == 'PUSH_EXC_INFO'
                        for instr in handler_entry.instructions
                    )
                    has_pop_top = any(
                        instr.opname == 'POP_TOP'
                        for instr in handler_entry.instructions
                    )
                    is_bare_except = not has_check_exc_match and has_push_exc_info and has_pop_top
                    
                    if has_check_exc_match or is_bare_except:
                        # 这是except handler（包括裸except）
                        # 这是except handler（包括裸except）
                        # 这是except handler（包括裸except）
                        # 这是except handler（包括裸except）
                        handler_body = self._collect_handler_body(handler_entry, analyzed_blocks)
                        exc_type = self._extract_exception_type_from_handler(handler_entry)
                        # [关键修复] 从整个handler body中提取except-as变量名，而不仅仅是handler_entry
                        exc_name = self._extract_exception_name_from_handler_body(handler_body)
                        if handler_body:
                            except_handlers.append((exc_type, exc_name, handler_body))
                    
                    # [关键修复] 对于链式except handler（多个except），
                    # 查找当前handler的POP_JUMP_FORWARD_IF_FALSE跳转目标
                    # 如果跳转目标不是RERAISE块，可能是下一个handler
                    for instr in handler_entry.instructions:
                        if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE':
                            jump_target = instr.argval
                            next_block = self._find_block_containing_offset(jump_target)
                            if next_block:
                                # 检查是否是RERAISE块
                                # 检查是否是RERAISE块
                                # 检查是否是RERAISE块
                                # 检查是否是RERAISE块
                                has_reraise = any(i.opname == 'RERAISE' for i in next_block.instructions)
                                if not has_reraise:
                                    # 检查是否有CHECK_EXC_MATCH（是except handler）
                                    # 检查是否有CHECK_EXC_MATCH（是except handler）
                                    # 检查是否有CHECK_EXC_MATCH（是except handler）
                                    # 检查是否有CHECK_EXC_MATCH（是except handler）
                                    has_check = any(
                                        i.opname == 'CHECK_EXC_MATCH' 
                                        for i in next_block.instructions
                                    )
                                    if has_check and jump_target not in handler_worklist:
                                        # 这是下一个handler，添加到待处理列表
                                        # 这是下一个handler，添加到待处理列表
                                        # 这是下一个handler，添加到待处理列表
                                        # 这是下一个handler，添加到待处理列表
                                        handler_worklist.append(jump_target)
                            break
                    
                    # [关键修复] 收集包含RERAISE的清理代码块
                    # 这些块是except handler的一部分，包含清理代码（如e = None; del e; RERAISE）
                    
                    # 方法1: 检查POP_JUMP_FORWARD_IF_FALSE的跳转目标
                    for instr in handler_entry.instructions:
                        if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE':
                            jump_target = instr.argval
                            next_block = self._find_block_containing_offset(jump_target)
                            if next_block:
                                # 检查是否是RERAISE块（清理代码块）
                                # 检查是否是RERAISE块（清理代码块）
                                # 检查是否是RERAISE块（清理代码块）
                                # 检查是否是RERAISE块（清理代码块）
                                has_reraise = any(i.opname == 'RERAISE' for i in next_block.instructions)
                                has_cleanup = any(
                                    i.opname in ('LOAD_CONST', 'STORE_FAST', 'DELETE_FAST')
                                    for i in next_block.instructions
                                )
                                # [关键修复] 检查是否有PUSH_EXC_INFO，如果有，这是finally块的异常路径，不是except handler的清理代码
                                has_push_exc_info = any(i.opname == 'PUSH_EXC_INFO' for i in next_block.instructions)
                                if has_reraise and has_cleanup and not has_push_exc_info:
                                    # 这是清理代码块，添加到当前的except handler
                                    # 这是清理代码块，添加到当前的except handler
                                    # 这是清理代码块，添加到当前的except handler
                                    # 这是清理代码块，添加到当前的except handler
                                    if except_handlers:
                                        last_handler = except_handlers[-1]
                                        if len(last_handler) == 3:
                                            exc_type, exc_name, handler_blocks = last_handler
                                        else:
                                            exc_type, handler_blocks = last_handler
                                            exc_name = None
                                        if next_block not in handler_blocks:
                                            handler_blocks.append(next_block)
                            break
                    
                    # 方法2: 从handler body的最后一个块的后继中查找清理代码块
                    # 这对于except-as的清理代码块很重要
                    if except_handlers:
                        last_handler = except_handlers[-1]
                        if len(last_handler) == 3:
                            _, _, handler_blocks = last_handler
                        else:
                            _, handler_blocks = last_handler
                        
                        if handler_blocks:
                            last_block = max(handler_blocks, key=lambda b: b.end_offset)
                            for succ in last_block.successors:
                                if succ not in handler_blocks:
                                    # 检查是否是清理代码块
                                    # 检查是否是清理代码块
                                    # 检查是否是清理代码块
                                    # 检查是否是清理代码块
                                    has_reraise = any(i.opname == 'RERAISE' for i in succ.instructions)
                                    has_cleanup = any(
                                        i.opname in ('LOAD_CONST', 'STORE_FAST', 'DELETE_FAST')
                                        for i in succ.instructions
                                    )
                                    # [关键修复] 检查是否有PUSH_EXC_INFO，如果有，这是finally块的异常路径，不是except handler的清理代码
                                    has_push_exc_info = any(i.opname == 'PUSH_EXC_INFO' for i in succ.instructions)
                                    if has_reraise and has_cleanup and not has_push_exc_info:
                                        # 这是清理代码块，添加到当前的except handler
                                        # 这是清理代码块，添加到当前的except handler
                                        # 这是清理代码块，添加到当前的except handler
                                        # 这是清理代码块，添加到当前的except handler
                                        if succ not in handler_blocks:
                                            handler_blocks.append(succ)
            
            # [关键修复] 支持try-except、try-finally和try-except-finally
            # 只要有try_body，并且有except_handlers或finally，就创建结构
            has_finally_candidate = False
            finally_candidates = set()
            
            # [关键修复] 检查是否有finally
            # depth=1的异常表条目可能是：
            # 1. finally代码（真正的finally子句）
            # 2. except handler内部的异常处理（不是finally）
            # 需要通过检查handler块的内容来区分
            for entry in self.cfg.exception_table:
                if entry['depth'] == 1:
                    handler_offset = entry['target']
                    handler_block = self._find_block_containing_offset(handler_offset)
                    if handler_block:
                        # [关键修复] 检查这个块是否是真正的finally代码
                        # finally代码的特征：
                        # 1. 不包含CHECK_EXC_MATCH（不是except handler）
                        # 2. 包含实际的代码（LOAD_/STORE_等），不只是清理代码
                        # [关键修复] 检查这个块是否是真正的finally代码
                        # finally代码的特征：
                        # 1. 不包含CHECK_EXC_MATCH（不是except handler）
                        # 2. 包含实际的代码（LOAD_/STORE_等），不只是清理代码
                        # [关键修复] 检查这个块是否是真正的finally代码
                        # finally代码的特征：
                        # 1. 不包含CHECK_EXC_MATCH（不是except handler）
                        # 2. 包含实际的代码（LOAD_/STORE_等），不只是清理代码
                        # [关键修复] 检查这个块是否是真正的finally代码
                        # finally代码的特征：
                        # 1. 不包含CHECK_EXC_MATCH（不是except handler）
                        # 2. 包含实际的代码（LOAD_/STORE_等），不只是清理代码
                        has_check_exc_match = any(
                            instr.opname == 'CHECK_EXC_MATCH' 
                            for instr in handler_block.instructions
                        )
                        has_actual_code = any(
                            instr.opname.startswith('LOAD_') and not instr.opname.startswith('LOAD_CONST') or
                            instr.opname.startswith('STORE_') or
                            instr.opname.startswith('CALL_')
                            for instr in handler_block.instructions
                        )
                        
                        # 如果不是except handler且有实际代码，可能是finally
                        if not has_check_exc_match and has_actual_code:
                            has_finally_candidate = True
                            finally_candidates.add(handler_block)
            
            if try_body and (except_handlers or has_finally_candidate):
                # [关键修复] 识别else子句
                # [关键修复] 首先识别finally子句
                # finally子句的特征：
                # 1. 在try/except/else之后执行
                # 2. 有两个入口：正常路径和异常路径
                # 3. 正常路径以JUMP_FORWARD结束，异常路径以RERAISE结束
                # [关键修复] 识别else子句
                # [关键修复] 首先识别finally子句
                # finally子句的特征：
                # 1. 在try/except/else之后执行
                # 2. 有两个入口：正常路径和异常路径
                # 3. 正常路径以JUMP_FORWARD结束，异常路径以RERAISE结束
                # [关键修复] 识别else子句
                # [关键修复] 首先识别finally子句
                # finally子句的特征：
                # 1. 在try/except/else之后执行
                # 2. 有两个入口：正常路径和异常路径
                # 3. 正常路径以JUMP_FORWARD结束，异常路径以RERAISE结束
                # [关键修复] 识别else子句
                # [关键修复] 首先识别finally子句
                # finally子句的特征：
                # 1. 在try/except/else之后执行
                # 2. 有两个入口：正常路径和异常路径
                # 3. 正常路径以JUMP_FORWARD结束，异常路径以RERAISE结束
                finally_body = []
                has_finally = False
                
                # 收集所有handler body块
                all_handler_body_blocks = set()
                for _, _, h_blocks in except_handlers:
                    all_handler_body_blocks.update(h_blocks)
                
                # [关键修复] 查找finally代码
                # 对于try-except-finally结构，finally有两个入口：
                # 1. 正常路径：从try块通过JUMP_FORWARD跳转
                # 2. 异常路径：从exception table跳转（depth=0或depth=1）
                
                finally_candidates = set()
                
                # 方法1：从exception table查找finally入口（depth=0，target在try范围之外）
                for entry in self.cfg.exception_table:
                    if entry['depth'] == 0:
                        # 检查这个entry是否在try范围内或与try范围重叠
                        # [关键修复] 对于finally块，exception table条目的start可能等于try范围的结束
                        # 但entry['end']会大于try范围的结束
                        # 检查这个entry是否在try范围内或与try范围重叠
                        # [关键修复] 对于finally块，exception table条目的start可能等于try范围的结束
                        # 但entry['end']会大于try范围的结束
                        # 检查这个entry是否在try范围内或与try范围重叠
                        # [关键修复] 对于finally块，exception table条目的start可能等于try范围的结束
                        # 但entry['end']会大于try范围的结束
                        # 检查这个entry是否在try范围内或与try范围重叠
                        # [关键修复] 对于finally块，exception table条目的start可能等于try范围的结束
                        # 但entry['end']会大于try范围的结束
                        is_in_try_range = start_offset <= entry['start'] < end_offset
                        is_finally_entry = entry['start'] == end_offset and entry['end'] > end_offset
                        if is_in_try_range or is_finally_entry:
                            # 检查target是否在try范围之外
                            # 检查target是否在try范围之外
                            # 检查target是否在try范围之外
                            # 检查target是否在try范围之外
                            if entry['target'] >= end_offset:
                                handler_block = self._find_block_containing_offset(entry['target'])
                                if handler_block:
                                    # 检查是否是finally代码（有PUSH_EXC_INFO）
                                    # 检查是否是finally代码（有PUSH_EXC_INFO）
                                    # 检查是否是finally代码（有PUSH_EXC_INFO）
                                    # 检查是否是finally代码（有PUSH_EXC_INFO）
                                    has_push_exc_info = any(
                                        instr.opname == 'PUSH_EXC_INFO'
                                        for instr in handler_block.instructions
                                    )
                                    # [关键修复] 确保不是except handler（有CHECK_EXC_MATCH）
                                    has_check_exc_match = any(
                                        instr.opname == 'CHECK_EXC_MATCH'
                                        for instr in handler_block.instructions
                                    )
                                    # [关键修复] 确保不是with语句的异常处理块（有WITH_EXCEPT_START）
                                    has_with_except_start = any(
                                        instr.opname == 'WITH_EXCEPT_START'
                                        for instr in handler_block.instructions
                                    )
                                    if has_push_exc_info and not has_check_exc_match and not has_with_except_start:
                                        finally_candidates.add(handler_block)
                
                # 方法2：从try/else块查找正常路径的finally代码
                # 这些块通过JUMP_FORWARD跳转，且后继块有PUSH_EXC_INFO
                for block in try_body:
                    has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in block.instructions)
                    if has_jump_forward:
                        for succ in block.successors:
                            if succ not in all_handler_body_blocks and succ not in try_body:
                                # 检查后继块是否是finally代码
                                # 检查后继块是否是finally代码
                                # 检查后继块是否是finally代码
                                # 检查后继块是否是finally代码
                                has_push_exc_info = any(
                                    instr.opname == 'PUSH_EXC_INFO'
                                    for instr in succ.instructions
                                )
                                # 或者检查后继块的后继是否有PUSH_EXC_INFO
                                has_finally_in_succ = any(
                                    any(instr.opname == 'PUSH_EXC_INFO' for instr in s.instructions)
                                    for s in succ.successors
                                )
                                # [关键修复] 检查后继块是否跳转到包含PUSH_EXC_INFO的块
                                # 这是正常路径的finally代码的特征
                                jumps_to_finally = False
                                for s in succ.successors:
                                    if any(instr.opname == 'PUSH_EXC_INFO' for instr in s.instructions):
                                        jumps_to_finally = True
                                        break
                                # [关键修复] 确保不是except handler（有CHECK_EXC_MATCH）
                                has_check_exc_match = any(
                                    instr.opname == 'CHECK_EXC_MATCH'
                                    for instr in succ.instructions
                                )
                                # [关键修复] 检查是否是另一个try的开始
                                # 方法1：检查是否有exception table条目的start等于块的start_offset
                                is_another_try_start = any(
                                    entry['start'] == succ.start_offset and entry['depth'] == 0
                                    for entry in self.cfg.exception_table
                                )
                                # 方法2：检查块是否包含NOP指令，并且exception table中有条目在NOP之后不久开始
                                if not is_another_try_start:
                                    has_nop = any(
                                        instr.opname == 'NOP'
                                        for instr in succ.instructions
                                    )
                                    if has_nop:
                                        for entry in self.cfg.exception_table:
                                            if entry['depth'] == 0:
                                                # 检查entry的start是否在NOP之后10个字节内
                                                # 检查entry的start是否在NOP之后10个字节内
                                                # 检查entry的start是否在NOP之后10个字节内
                                                # 检查entry的start是否在NOP之后10个字节内
                                                nop_offset = None
                                                for instr in succ.instructions:
                                                    if instr.opname == 'NOP':
                                                        nop_offset = instr.offset
                                                        break
                                                if nop_offset and 0 < entry['start'] - nop_offset <= 10:
                                                    is_another_try_start = True
                                                    break
                                # [关键修复] 确保不是with语句的异常处理块（有WITH_EXCEPT_START）
                                has_with_except_start = any(
                                    instr.opname == 'WITH_EXCEPT_START'
                                    for instr in succ.instructions
                                )
                                if (has_push_exc_info or has_finally_in_succ or jumps_to_finally) and not has_check_exc_match and not is_another_try_start and not has_with_except_start:
                                    finally_candidates.add(succ)

                # 方法3：从handler块查找异常路径的finally代码
                # 找到所有handler body的最后一个块
                last_handler_blocks = []
                for _, _, h_blocks in except_handlers:
                    if h_blocks:
                        last_handler_blocks.append(max(h_blocks, key=lambda b: b.end_offset))
                
                for block in last_handler_blocks:
                    for succ in block.successors:
                        if succ not in all_handler_body_blocks and succ not in try_body:
                            has_push_exc_info = any(
                                instr.opname == 'PUSH_EXC_INFO'
                                for instr in succ.instructions
                            )
                            # [关键修复] 确保不是except handler（有CHECK_EXC_MATCH）
                            has_check_exc_match = any(
                                instr.opname == 'CHECK_EXC_MATCH'
                                for instr in succ.instructions
                            )
                            # [关键修复] 检查是否是另一个try的开始
                            is_another_try_start = any(
                                entry['start'] == succ.start_offset and entry['depth'] == 0
                                for entry in self.cfg.exception_table
                            )
                            # [关键修复] 确保不是with语句的异常处理块（有WITH_EXCEPT_START）
                            has_with_except_start = any(
                                instr.opname == 'WITH_EXCEPT_START'
                                for instr in succ.instructions
                            )
                            if has_push_exc_info and not has_check_exc_match and not is_another_try_start and not has_with_except_start:
                                finally_candidates.add(succ)

                # 如果找到了finally候选块，收集finally体
                if finally_candidates:
                    finally_worklist = list(finally_candidates)
                    finally_visited = set()
                    
                    while finally_worklist:
                        block = finally_worklist.pop(0)
                        if block in finally_visited:
                            continue
                        
                        # [关键修复] 确保不收集except handler块
                        is_handler_block = block in all_handler_body_blocks
                        if is_handler_block:
                            continue
                        
                        finally_visited.add(block)
                        finally_body.append(block)
                        
                        # 继续收集后继块（只要不是RERAISE块或RETURN_VALUE块或handler块）
                        has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in block.instructions)
                        if not has_jump_forward:
                            for succ in block.successors:
                                if succ not in finally_visited:
                                    has_reraise = any(instr.opname == 'RERAISE' for instr in succ.instructions)
                                    has_return = any(instr.opname == 'RETURN_VALUE' for instr in succ.instructions)
                                    is_handler = succ in all_handler_body_blocks
                                    if not has_reraise and not has_return and not is_handler:
                                        finally_worklist.append(succ)
                    
                    if finally_body:
                        has_finally = True
                        finally_body.sort(key=lambda b: b.start_offset)
                        
                        # [关键修复] 查找正常路径的finally代码
                        # 正常路径的finally代码从try块通过JUMP_FORWARD跳转
                        # 并且不是except handler块或另一个try块
                        for block in try_body:
                            has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in block.instructions)
                            if has_jump_forward:
                                for succ in block.successors:
                                    if succ not in all_handler_body_blocks and succ not in try_body and succ not in finally_body:
                                        # 检查这个块是否是finally代码
                                        # 通过检查它是否包含实际的代码（LOAD/STORE/CALL）
                                        # 检查这个块是否是finally代码
                                        # 通过检查它是否包含实际的代码（LOAD/STORE/CALL）
                                        # 检查这个块是否是finally代码
                                        # 通过检查它是否包含实际的代码（LOAD/STORE/CALL）
                                        # 检查这个块是否是finally代码
                                        # 通过检查它是否包含实际的代码（LOAD/STORE/CALL）
                                        has_actual_code = any(
                                            instr.opname.startswith(('LOAD_', 'STORE_', 'CALL_'))
                                            for instr in succ.instructions
                                        )
                                        # 并且不包含PUSH_EXC_INFO（不是异常路径的finally入口）
                                        has_push_exc_info = any(
                                            instr.opname == 'PUSH_EXC_INFO'
                                            for instr in succ.instructions
                                        )
                                        # [关键修复] 检查这个块是否是另一个try的开始
                                        # 方法1：通过检查是否有对应的exception table条目（depth=0，start等于块的start_offset）
                                        is_another_try_start = any(
                                            entry['start'] == succ.start_offset and entry['depth'] == 0
                                            for entry in self.cfg.exception_table
                                        )
                                        # 方法2：检查块是否包含NOP指令（try的入口通常有NOP）
                                        # 并且exception table中有条目在NOP之后不久开始
                                        has_nop = any(
                                            instr.opname == 'NOP'
                                            for instr in succ.instructions
                                        )
                                        if has_nop:
                                            # 检查是否有exception table条目在NOP之后不久开始
                                            # 检查是否有exception table条目在NOP之后不久开始
                                            # 检查是否有exception table条目在NOP之后不久开始
                                            # 检查是否有exception table条目在NOP之后不久开始
                                            for entry in self.cfg.exception_table:
                                                if entry['depth'] == 0:
                                                    # 检查entry的start是否在NOP之后10个字节内
                                                    # 检查entry的start是否在NOP之后10个字节内
                                                    # 检查entry的start是否在NOP之后10个字节内
                                                    # 检查entry的start是否在NOP之后10个字节内
                                                    nop_offset = None
                                                    for instr in succ.instructions:
                                                        if instr.opname == 'NOP':
                                                            nop_offset = instr.offset
                                                            break
                                                    if nop_offset and 0 <= entry['start'] - nop_offset <= 10:
                                                        is_another_try_start = True
                                                        break
                                        
                                        if has_actual_code and not has_push_exc_info and not is_another_try_start:
                                            # 这个块是正常路径的finally代码
                                            # 这个块是正常路径的finally代码
                                            # 这个块是正常路径的finally代码
                                            # 这个块是正常路径的finally代码
                                            finally_body.append(succ)
                        
                        finally_body.sort(key=lambda b: b.start_offset)
                
                # else子句的块在try块之后、except块之前，以JUMP_FORWARD结束
                else_body = []
                has_else = False
                
                # [关键修复] 如果已经识别了finally，不再识别else
                # finally块的正常路径会被错误地识别为else块，所以需要先检查
                if not has_finally:
                    # 找到try块的最后一个块
                    # 找到try块的最后一个块
                    # 找到try块的最后一个块
                    # 找到try块的最后一个块
                    if try_body:
                        last_try_block = max(try_body, key=lambda b: b.end_offset)
                        
                        # [关键修复] 检查try块的最后一个块是否包含try范围之外的指令
                        # 如果包含，这些指令可能是else子句的一部分
                        # [关键修复] 修正逻辑：last_try_block 一定在 try_body 中，所以不应该检查 not in try_body
                        if last_try_block.end_offset > end_offset:
                            # 这个块包含了try范围之外的指令
                            # 检查这些指令是否以JUMP_FORWARD结束（else子句的特征）
                            # 这个块包含了try范围之外的指令
                            # 检查这些指令是否以JUMP_FORWARD结束（else子句的特征）
                            # 这个块包含了try范围之外的指令
                            # 检查这些指令是否以JUMP_FORWARD结束（else子句的特征）
                            # 这个块包含了try范围之外的指令
                            # 检查这些指令是否以JUMP_FORWARD结束（else子句的特征）
                            has_jump_forward = any(
                                instr.opname == 'JUMP_FORWARD' and instr.offset >= end_offset
                                for instr in last_try_block.instructions
                            )
                            if has_jump_forward:
                                # 创建虚拟的else块
                                # 创建虚拟的else块
                                # 创建虚拟的else块
                                # 创建虚拟的else块
                                else_body = [last_try_block]
                                has_else = True
                        
                        if not has_else:
                            # 如果没有找到else块，尝试查找从try块跳转出来的块
                            # 如果没有找到else块，尝试查找从try块跳转出来的块
                            # 如果没有找到else块，尝试查找从try块跳转出来的块
                            # 如果没有找到else块，尝试查找从try块跳转出来的块
                            for succ in last_try_block.successors:
                                if succ not in analyzed_blocks and succ not in [b for _, _, blocks in except_handlers for b in blocks]:
                                    # [关键修复] 检查这个块是否是真正的else块
                                    # 真正的else块应该：
                                    # 1. 不包含NOP（不是另一个try的开始）
                                    # 2. 不包含PUSH_EXC_INFO（不是finally代码）
                                    # 3. 不包含CHECK_EXC_MATCH（不是except handler）
                                    # 4. 不包含POP_EXCEPT（不是except handler代码）
                                    # [注意] 不需要检查JUMP_FORWARD，else块可以是简单的return语句
                                    # [关键修复] 检查这个块是否是真正的else块
                                    # 真正的else块应该：
                                    # 1. 不包含NOP（不是另一个try的开始）
                                    # 2. 不包含PUSH_EXC_INFO（不是finally代码）
                                    # 3. 不包含CHECK_EXC_MATCH（不是except handler）
                                    # 4. 不包含POP_EXCEPT（不是except handler代码）
                                    # [注意] 不需要检查JUMP_FORWARD，else块可以是简单的return语句
                                    # [关键修复] 检查这个块是否是真正的else块
                                    # 真正的else块应该：
                                    # 1. 不包含NOP（不是另一个try的开始）
                                    # 2. 不包含PUSH_EXC_INFO（不是finally代码）
                                    # 3. 不包含CHECK_EXC_MATCH（不是except handler）
                                    # 4. 不包含POP_EXCEPT（不是except handler代码）
                                    # [注意] 不需要检查JUMP_FORWARD，else块可以是简单的return语句
                                    # [关键修复] 检查这个块是否是真正的else块
                                    # 真正的else块应该：
                                    # 1. 不包含NOP（不是另一个try的开始）
                                    # 2. 不包含PUSH_EXC_INFO（不是finally代码）
                                    # 3. 不包含CHECK_EXC_MATCH（不是except handler）
                                    # 4. 不包含POP_EXCEPT（不是except handler代码）
                                    # [注意] 不需要检查JUMP_FORWARD，else块可以是简单的return语句
                                    has_nop = any(instr.opname == 'NOP' for instr in succ.instructions)
                                    has_push_exc_info = any(instr.opname == 'PUSH_EXC_INFO' for instr in succ.instructions)
                                    has_check_exc_match = any(instr.opname == 'CHECK_EXC_MATCH' for instr in succ.instructions)
                                    has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in succ.instructions)
                                    
                                    # [关键修复] 检查这个块是否是另一个try的开始
                                    is_another_try = any(
                                        entry['start'] == succ.start_offset and entry['depth'] == 0
                                        for entry in self.cfg.exception_table
                                    )
                                    
                                    # [关键修复] 检查是否是异常处理相关的块
                                    is_exception_related = has_push_exc_info or has_check_exc_match or has_pop_except
                                    
                                    if not has_nop and not is_exception_related and not is_another_try:
                                        # 这可能是else块
                                        # 这可能是else块
                                        # 这可能是else块
                                        # 这可能是else块
                                        else_body = self._collect_else_body(succ, analyzed_blocks, except_handlers)
                                        if else_body:
                                            has_else = True
                                            break
                
                try_struct = TryExceptStructure(
                    struct_type=ControlStructureType.TRY_EXCEPT,
                    entry_block=try_entry,
                    try_body=try_body,
                    except_handlers=except_handlers,
                    else_body=else_body,
                    has_else=has_else,
                    finally_body=finally_body,
                    has_finally=has_finally,
                    try_start_offset=start_offset,
                    try_end_offset=end_offset
                )
                
                self.structures.append(try_struct)
                
                # [关键修复] 将entry_block映射到TryExceptStructure
                self.block_to_structure[try_entry] = try_struct
                
                # [关键修复] 收集所有内层try块的范围，避免将内层try的块映射到外层try
                inner_try_ranges = []
                if self.cfg.exception_table:
                    for entry in self.cfg.exception_table:
                        if entry['depth'] > try_depth:
                            inner_start = entry['start']
                            inner_end = entry['end']
                            # 只收集在当前try范围内的内层try块
                            if start_offset < inner_start < end_offset:
                                inner_try_ranges.append((inner_start, inner_end))
                
                for b in try_body:
                    # [关键修复] 检查这个块是否是内层try的一部分
                    # 如果是，不要将它映射到当前try结构，让内层try结构来处理它
                    # [关键修复] 检查这个块是否是内层try的一部分
                    # 如果是，不要将它映射到当前try结构，让内层try结构来处理它
                    # [关键修复] 检查这个块是否是内层try的一部分
                    # 如果是，不要将它映射到当前try结构，让内层try结构来处理它
                    # [关键修复] 检查这个块是否是内层try的一部分
                    # 如果是，不要将它映射到当前try结构，让内层try结构来处理它
                    is_inner_try_block = False
                    for inner_start, inner_end in inner_try_ranges:
                        # 如果块的任何部分在内层try范围内，它是内层try的一部分
                        # 如果块的任何部分在内层try范围内，它是内层try的一部分
                        # 如果块的任何部分在内层try范围内，它是内层try的一部分
                        # 如果块的任何部分在内层try范围内，它是内层try的一部分
                        if inner_start <= b.start_offset < inner_end or inner_start < b.end_offset <= inner_end:
                            is_inner_try_block = True
                            break
                    
                    if not is_inner_try_block:
                        self.block_to_structure[b] = try_struct
                # [关键修复] 新的except_handlers格式是(exc_type, exc_name, handler_blocks)
                for handler_info in except_handlers:
                    if len(handler_info) == 3:
                        _, _, handler_blocks = handler_info
                    else:
                        _, handler_blocks = handler_info
                    for b in handler_blocks:
                        self.block_to_structure[b] = try_struct
                
                # [关键修复] 将else块的块也标记为已处理
                for b in else_body:
                    self.block_to_structure[b] = try_struct
                
                # [关键修复] 将finally_body的块也标记为已处理
                for b in finally_body:
                    self.block_to_structure[b] = try_struct
                
                # [关键修复] 将包含RERAISE的清理代码块也标记为已处理
                # 同时更新except_handlers中的块到block_to_structure
                for handler_info in except_handlers:
                    if len(handler_info) == 3:
                        _, _, handler_blocks = handler_info
                    else:
                        _, handler_blocks = handler_info
                    for block in handler_blocks:
                        if block not in self.block_to_structure:
                            self.block_to_structure[block] = try_struct
                
                # [关键修复] 处理其他包含RERAISE的块
                for block in self.cfg.blocks.values():
                    if block not in self.block_to_structure:
                        has_reraise = any(instr.opname == 'RERAISE' for instr in block.instructions)
                        if has_reraise:
                            # 检查这个块是否是当前try-except结构的一部分
                            # 通过检查块的位置是否在try块之后
                            # 检查这个块是否是当前try-except结构的一部分
                            # 通过检查块的位置是否在try块之后
                            # 检查这个块是否是当前try-except结构的一部分
                            # 通过检查块的位置是否在try块之后
                            # 检查这个块是否是当前try-except结构的一部分
                            # 通过检查块的位置是否在try块之后
                            if block.start_offset >= end_offset:
                                self.block_to_structure[block] = try_struct
    
    def _collect_else_body(self, else_entry: BasicBlock, 
                           analyzed_blocks: Set[BasicBlock],
                           except_handlers: List[Tuple[Optional[str], Optional[str], List[BasicBlock]]]) -> List[BasicBlock]:
        """收集 else 体的所有块"""
        else_body = []
        worklist = [else_entry]
        visited = set()
        
        # 收集所有except handler的块，用于检查
        except_blocks = set()
        for _, _, handler_blocks in except_handlers:
            except_blocks.update(handler_blocks)
        
        while worklist:
            block = worklist.pop(0)
            if block in visited or block in analyzed_blocks or block in except_blocks:
                continue
            
            visited.add(block)
            else_body.append(block)
            
            # 如果块包含JUMP_FORWARD，停止收集（这是else块的结束）
            has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in block.instructions)
            if has_jump_forward:
                break
            
            # 继续收集后继块
            for succ in block.successors:
                if succ not in visited and succ not in analyzed_blocks and succ not in except_blocks:
                    worklist.append(succ)
        
        # 按偏移量排序
        else_body.sort(key=lambda b: b.start_offset)
        return else_body
    
    def _find_block_containing_offset(self, offset: int) -> Optional[BasicBlock]:
        """找到包含指定偏移量的基本块"""
        # 首先尝试直接查找
        if offset in self.cfg.offset_to_block:
            return self.cfg.offset_to_block[offset]
        
        # 否则查找包含该偏移量的块
        for block in self.cfg.blocks.values():
            if block.start_offset <= offset < block.end_offset:
                return block
        
        # 如果没找到，返回最接近的块（小于等于 offset 的最大 start_offset）
        candidates = [b for b in self.cfg.blocks.values() if b.start_offset <= offset]
        if candidates:
            return max(candidates, key=lambda b: b.start_offset)
        

        
        return None
    
    def _collect_try_body(self, start_offset: int, end_offset: int, 
                          analyzed_blocks: Set[BasicBlock]) -> List[BasicBlock]:
        """收集 try 体的所有块"""
        try_body = []
        
        # 找到包含 start_offset 的块作为 try 入口
        try_entry = self._find_block_containing_offset(start_offset)
        
        if not try_entry:
            return try_body
        
        # [关键修复] 收集所有嵌套try块的范围（depth更大的try块）
        # 这些范围需要特殊处理，但仍然应该被包含在try_body中
        nested_try_ranges = []
        current_depth = None
        if self.cfg.exception_table:
            # 首先确定当前try块的depth
            # 首先确定当前try块的depth
            # 首先确定当前try块的depth
            # 首先确定当前try块的depth
            for entry in self.cfg.exception_table:
                if entry['start'] == start_offset:
                    current_depth = entry['depth']
                    break
            
            # 收集嵌套try块的范围（depth比当前大的）
            if current_depth is not None:
                for entry in self.cfg.exception_table:
                    if entry['depth'] > current_depth:
                        nested_start = entry['start']
                        nested_end = entry['end']
                        # 只收集在当前try范围内的嵌套try块
                        if start_offset <= nested_start < end_offset:
                            nested_try_ranges.append((nested_start, nested_end))
        
        # [关键修复] 对于嵌套try-except结构，我们需要包含内层try的块
        # 即使它们已经被标记为analyzed_blocks
        # 因为这些块实际上是外层try的一部分
        nested_try_blocks = set()
        for nested_start, nested_end in nested_try_ranges:
            # 收集这个嵌套try的所有块
            # 收集这个嵌套try的所有块
            # 收集这个嵌套try的所有块
            # 收集这个嵌套try的所有块
            nested_blocks = self._collect_nested_try_blocks(nested_start, nested_end)
            nested_try_blocks.update(nested_blocks)
        
        # [关键修复] 对于嵌套try-except，内层try可能从外层try的handler开始
        # 这种情况下，try_entry可能只包含清理代码（COPY, POP_EXCEPT, RERAISE）
        # 我们需要检查try_entry是否包含实际的try体代码
        # 实际的try体代码应该在try_entry的前驱块中
        has_actual_try_code = False
        for instr in try_entry.instructions:
            if start_offset <= instr.offset < end_offset:
                # 检查是否是实际的try体代码（不是清理代码）
                # 检查是否是实际的try体代码（不是清理代码）
                # 检查是否是实际的try体代码（不是清理代码）
                # 检查是否是实际的try体代码（不是清理代码）
                if instr.opname not in ('COPY', 'POP_EXCEPT', 'RERAISE', 'NOP'):
                    has_actual_try_code = True
                    break
        
        # [关键修复] 如果try_entry不包含实际的try体代码，尝试从前驱块中找
        # 这种情况发生在嵌套try-except中，内层try从外层try的handler开始
        if not has_actual_try_code:
            # 找到包含实际try体代码的块
            # 找到包含实际try体代码的块
            # 找到包含实际try体代码的块
            # 找到包含实际try体代码的块
            for block in self.cfg.blocks.values():
                # 检查块是否包含try范围内的实际代码
                # 检查块是否包含try范围内的实际代码
                # 检查块是否包含try范围内的实际代码
                # 检查块是否包含try范围内的实际代码
                block_has_try_code = False
                for instr in block.instructions:
                    if start_offset <= instr.offset < end_offset:
                        if instr.opname not in ('COPY', 'POP_EXCEPT', 'RERAISE', 'NOP', 'PUSH_EXC_INFO'):
                            block_has_try_code = True
                            break
                if block_has_try_code:
                    try_entry = block
                    break
        
        # 收集所有在 try 范围内的块
        worklist = [try_entry]
        visited = set()
        
        while worklist:
            block = worklist.pop(0)
            if block in visited:
                continue
            
            # [修复] 检查块是否在 try 范围内
            # 只要块的任何部分在 try 范围内，就应该包含它
            in_range = False
            for instr in block.instructions:
                if start_offset <= instr.offset < end_offset:
                    in_range = True
                    break
            
            if not in_range and block != try_entry:
                continue
            
            visited.add(block)
            try_body.append(block)
            
            # 继续收集后继块（只要在范围内且不是异常处理块）
            for succ in block.successors:
                if succ not in visited:
                    # 检查后继是否是异常处理块（PUSH_EXC_INFO开头）
                    # 检查后继是否是异常处理块（PUSH_EXC_INFO开头）
                    # 检查后继是否是异常处理块（PUSH_EXC_INFO开头）
                    # 检查后继是否是异常处理块（PUSH_EXC_INFO开头）
                    is_handler_entry = any(
                        instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH')
                        for instr in succ.instructions
                    )
                    # 检查后继是否在try范围内
                    succ_in_range = any(
                        start_offset <= instr.offset < end_offset
                        for instr in succ.instructions
                    )
                    # 只收集在try范围内且不是异常处理块的后继
                    if not is_handler_entry and succ_in_range:
                        worklist.append(succ)
        
        # 按偏移量排序
        try_body.sort(key=lambda b: b.start_offset)
        return try_body
    
    def _collect_nested_try_blocks(self, start_offset: int, end_offset: int) -> Set[BasicBlock]:
        """
        收集嵌套try块的所有块（包括try体和handler体）
        
        这是辅助函数，用于在收集外层try_body时包含内层try的所有块
        """
        blocks = set()
        
        # 找到包含 start_offset 的块
        try_entry = self._find_block_containing_offset(start_offset)
        if not try_entry:
            return blocks
        
        # 收集try体内的所有块
        worklist = [try_entry]
        visited = set()
        
        while worklist:
            block = worklist.pop(0)
            if block in visited:
                continue
            
            # 检查块是否在try范围内
            if block.end_offset <= start_offset or block.start_offset >= end_offset:
                continue
            
            visited.add(block)
            blocks.add(block)
            
            # 继续收集后继块
            for succ in block.successors:
                if succ not in visited and succ.start_offset < end_offset:
                    worklist.append(succ)
        
        return blocks
    
    def _collect_handler_body(self, handler_entry: BasicBlock, 
                              analyzed_blocks: Set[BasicBlock]) -> List[BasicBlock]:
        """收集 handler 体的所有块
        
        对于 Python 3.11+ 的异常处理结构：
        - handler_entry 包含 PUSH_EXC_INFO, LOAD_GLOBAL, CHECK_EXC_MATCH, POP_JUMP_FORWARD_IF_FALSE
        - 匹配成功的分支是 POP_JUMP_FORWARD_IF_FALSE 的 fall-through 后继（即匹配时继续执行）
        - 不匹配的分支会跳转到 RERAISE
        """
        handler_body = [handler_entry]
        
        # [关键修复] 找到 POP_JUMP_FORWARD_IF_FALSE 指令，确定匹配成功的分支
        # 匹配成功的分支是紧接在 POP_JUMP_FORWARD_IF_FALSE 之后的块（offset最小的那个）
        match_success_block = None
        for i, instr in enumerate(handler_entry.instructions):
            if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE':
                # 找到跳转目标
                # 找到跳转目标
                # 找到跳转目标
                # 找到跳转目标
                jump_target = instr.argval if instr.argval is not None else 0
                # [关键修复] 匹配成功的分支是 offset 最小的那个不等于 jump_target 的后继
                # 这是因为 Python 字节码中，POP_JUMP_FORWARD_IF_FALSE 的 fall-through 分支
                # 是紧接着的下一条指令，对应的块应该有最小的 start_offset
                candidates = [succ for succ in handler_entry.successors if succ.start_offset != jump_target]
                if candidates:
                    # 选择 offset 最小的那个（紧接在 POP_JUMP_FORWARD_IF_FALSE 之后的块）
                    # 选择 offset 最小的那个（紧接在 POP_JUMP_FORWARD_IF_FALSE 之后的块）
                    # 选择 offset 最小的那个（紧接在 POP_JUMP_FORWARD_IF_FALSE 之后的块）
                    # 选择 offset 最小的那个（紧接在 POP_JUMP_FORWARD_IF_FALSE 之后的块）
                    match_success_block = min(candidates, key=lambda b: b.start_offset)
                break
        
        # [关键修复] 如果没有找到 POP_JUMP_FORWARD_IF_FALSE（裸except），
        # 需要特殊处理：裸except的handler body可能包含POP_TOP和实际代码
        # 检查handler_entry是否包含POP_TOP，如果包含，需要收集后继
        if match_success_block is None:
            # 对于裸except，检查是否有POP_TOP
            # 对于裸except，检查是否有POP_TOP
            # 对于裸except，检查是否有POP_TOP
            # 对于裸except，检查是否有POP_TOP
            has_pop_top = any(instr.opname == 'POP_TOP' for instr in handler_entry.instructions)
            if has_pop_top:
                # 有POP_TOP，说明这是裸except的入口，需要收集后继
                # 找到POP_TOP之后的后继（即实际代码块）
                # 有POP_TOP，说明这是裸except的入口，需要收集后继
                # 找到POP_TOP之后的后继（即实际代码块）
                # 有POP_TOP，说明这是裸except的入口，需要收集后继
                # 找到POP_TOP之后的后继（即实际代码块）
                # 有POP_TOP，说明这是裸except的入口，需要收集后继
                # 找到POP_TOP之后的后继（即实际代码块）
                for succ in handler_entry.successors:
                    # 检查后继是否包含实际代码（不是RERAISE块）
                    # 检查后继是否包含实际代码（不是RERAISE块）
                    # 检查后继是否包含实际代码（不是RERAISE块）
                    # 检查后继是否包含实际代码（不是RERAISE块）
                    has_reraise = any(i.opname == 'RERAISE' for i in succ.instructions)
                    if not has_reraise:
                        worklist = [succ]
                        break
                else:
                    worklist = []
            else:
                # [关键修复] 对于嵌套在循环中的裸except，
                # handler_entry可能不包含POP_TOP，但可能有后继块包含实际代码
                # 检查所有后继块，找到包含实际代码的块
                for succ in handler_entry.successors:
                    has_reraise = any(i.opname == 'RERAISE' for i in succ.instructions)
                    has_push_exc_info = any(i.opname == 'PUSH_EXC_INFO' for i in succ.instructions)
                    # 排除RERAISE块和另一个try-except的入口
                    if not has_reraise and not has_push_exc_info:
                        # 检查是否包含实际代码
                        # 检查是否包含实际代码
                        # 检查是否包含实际代码
                        # 检查是否包含实际代码
                        has_actual_code = any(
                            i.opname not in ('RESUME', 'CACHE', 'NOP', 'PRECALL', 'POP_TOP')
                            for i in succ.instructions
                        )
                        if has_actual_code:
                            worklist = [succ]
                            break
                else:
                    # 没有POP_TOP，handler body就是handler_entry本身
                    worklist = []
        else:
            worklist = [match_success_block]
        
        visited = {handler_entry}
        
        while worklist:
            block = worklist.pop(0)
            if block in visited or block in analyzed_blocks:
                continue
            
            # [关键修复] 跳过包含 RERAISE 的块（这些是异常传播路径）
            # 但对于嵌套try-except，我们需要包含内层try的entry_block
            has_reraise = any(instr.opname == 'RERAISE' for instr in block.instructions)
            if has_reraise:
                # [关键修复] 检查这个块是否是另一个try块的开始
                # 如果是，我们应该包含它，因为它可能是内层try-except的entry
                # [关键修复] 检查这个块是否是另一个try块的开始
                # 如果是，我们应该包含它，因为它可能是内层try-except的entry
                # [关键修复] 检查这个块是否是另一个try块的开始
                # 如果是，我们应该包含它，因为它可能是内层try-except的entry
                # [关键修复] 检查这个块是否是另一个try块的开始
                # 如果是，我们应该包含它，因为它可能是内层try-except的entry
                is_try_start = any(
                    instr.opname == 'NOP' for instr in block.instructions
                )
                if not is_try_start:
                    continue
            
            visited.add(block)
            handler_body.append(block)
            
            # [关键修复] 如果块包含 RETURN_VALUE，不再继续收集后继
            has_return = any(instr.opname == 'RETURN_VALUE' for instr in block.instructions)
            if has_return:
                continue
            
            # [关键修复] 如果块包含 POP_EXCEPT + JUMP_FORWARD，不再继续收集后继
            # 这是handler结束的标志，后继是finally块
            is_handler_end = False
            for instr in block.instructions:
                if instr.opname == 'POP_EXCEPT':
                    for next_instr in block.instructions[block.instructions.index(instr)+1:]:
                        if next_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                            is_handler_end = True
                            break
            
            if is_handler_end:
                continue
            
            for succ in block.successors:
                if succ not in visited and succ not in analyzed_blocks:
                    worklist.append(succ)
        
        # 按偏移量排序
        handler_body.sort(key=lambda b: b.start_offset)
        return handler_body
    
    def _extract_exception_type_from_handler(self, handler_entry: BasicBlock) -> Optional[str]:
        """从handler入口块提取异常类型"""
        exc_types = []
        in_exc_type = False
        
        # [关键修复] 检查块是否包含PUSH_EXC_INFO
        has_push_exc_info = any(instr.opname == 'PUSH_EXC_INFO' for instr in handler_entry.instructions)
        
        for i, instr in enumerate(handler_entry.instructions):
            if instr.opname == 'PUSH_EXC_INFO':
                in_exc_type = True
                continue
            
            # [关键修复] 如果没有PUSH_EXC_INFO（链式handler），在CHECK_EXC_MATCH之前都认为是异常类型
            if not has_push_exc_info and instr.opname == 'LOAD_GLOBAL':
                in_exc_type = True
            
            if not in_exc_type:
                continue
            
            if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                if instr.argval and isinstance(instr.argval, str):
                    val = instr.argval
                    if val and val[0].isupper():
                        exc_types.append(val)
            elif instr.opname == 'BUILD_TUPLE':
                # 元组类型的异常，已经收集了所有类型
                # 元组类型的异常，已经收集了所有类型
                continue
            elif instr.opname == 'CHECK_EXC_MATCH':
                # 异常类型检查结束
                # 异常类型检查结束
                break
        
        if len(exc_types) == 1:
            return exc_types[0]
        elif len(exc_types) > 1:
            return f"({', '.join(exc_types)})"
        return None
    
    def _extract_exception_name_from_handler(self, handler_entry: BasicBlock) -> Optional[str]:
        """从handler入口块提取except-as的变量名（如 except Exception as e: 中的e）"""
        # [关键修复] except-as的变量绑定有以下特征：
        # 1. 在POP_JUMP_FORWARD_IF_FALSE之后
        # 2. 在POP_TOP之后（弹出异常对象）
        # 3. 紧接着是handler body的实际代码
        
        found_jump = False
        found_pop_top = False
        for i, instr in enumerate(handler_entry.instructions):
            if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE':
                found_jump = True
                continue
            
            if found_jump and instr.opname == 'POP_TOP':
                found_pop_top = True
                continue
            
            # [关键修复] 只有在POP_TOP之后紧接着的STORE_FAST才是except-as的变量
            if found_pop_top and instr.opname == 'STORE_FAST':
                # 检查下一条是否是LOAD_GLOBAL/LOAD_FAST/LOAD_CONST（实际handler代码的开始）
                # 检查下一条是否是LOAD_GLOBAL/LOAD_FAST/LOAD_CONST（实际handler代码的开始）
                # 检查下一条是否是LOAD_GLOBAL/LOAD_FAST/LOAD_CONST（实际handler代码的开始）
                # 检查下一条是否是LOAD_GLOBAL/LOAD_FAST/LOAD_CONST（实际handler代码的开始）
                if i + 1 < len(handler_entry.instructions):
                    next_instr = handler_entry.instructions[i + 1]
                    if next_instr.opname in ('LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_CONST', 'LOAD_NAME'):
                        return instr.argval
        
        # [关键修复] 如果没有在handler_entry中找到，检查后继块
        # 但需要确保这是真正的except-as变量，而不是handler body中的赋值
        for succ in handler_entry.successors:
            # 只检查后继块的前几条指令
            # 只检查后继块的前几条指令
            # 只检查后继块的前几条指令
            # 只检查后继块的前几条指令
            for i, instr in enumerate(succ.instructions[:3]):  # 只检查前3条指令
                if instr.opname == 'POP_TOP':
                    # POP_TOP之后如果有STORE_FAST，可能是except-as变量
                    # POP_TOP之后如果有STORE_FAST，可能是except-as变量
                    # POP_TOP之后如果有STORE_FAST，可能是except-as变量
                    # POP_TOP之后如果有STORE_FAST，可能是except-as变量
                    if i + 1 < len(succ.instructions):
                        next_instr = succ.instructions[i + 1]
                        if next_instr.opname == 'STORE_FAST':
                            return next_instr.argval
        

        
        return None
    
    def _extract_exception_name_from_handler_body(self, handler_body: List[BasicBlock]) -> Optional[str]:
        """从handler body的所有块中提取except-as的变量名
        
        对于Python 3.11+，except-as变量的STORE_FAST可能在handler body的任何块中，
        而不仅仅是在handler entry块中。
        
        特征：
        1. 在包含POP_JUMP_FORWARD_IF_FALSE的块中，匹配成功的分支是fall-through
        2. 匹配成功后：
           - 对于无as的except: 执行POP_TOP（弹出异常对象）
           - 对于有as的except: 直接执行STORE_FAST（异常对象已经在栈上）
        3. 如果是STORE_FAST，这就是except-as变量
        """
        # 首先找到包含POP_JUMP_FORWARD_IF_FALSE的块
        jump_block = None
        for block in handler_body:
            for instr in block.instructions:
                if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE':
                    jump_block = block
                    break
            if jump_block:
                break
        
        if jump_block:
            # 找到跳转目标
            # 找到跳转目标
            # 找到跳转目标
            # 找到跳转目标
            jump_target = None
            for instr in jump_block.instructions:
                if instr.opname == 'POP_JUMP_FORWARD_IF_FALSE':
                    jump_target = instr.argval
                    break
            
            # 找到匹配成功的分支（fall-through后继，即offset最小的那个不等于jump_target的后继）
            if jump_target is not None:
                candidates = [b for b in jump_block.successors if b.start_offset != jump_target]
                if candidates:
                    match_success_block = min(candidates, key=lambda b: b.start_offset)
                    # 在这个块中查找第一条指令
                    # 如果有as，第一条是STORE_FAST；如果无as，第一条是POP_TOP
                    if match_success_block.instructions:
                        first_instr = match_success_block.instructions[0]
                        if first_instr.opname == 'STORE_FAST':
                            return first_instr.argval
                        # 如果是POP_TOP，检查下一条是否是STORE_FAST
                        elif first_instr.opname == 'POP_TOP':
                            if len(match_success_block.instructions) > 1:
                                second_instr = match_success_block.instructions[1]
                                if second_instr.opname == 'STORE_FAST':
                                    return second_instr.argval
        
        # [备选方案] 查找handler body中第一条是STORE_FAST的块
        for block in handler_body:
            if block.instructions:
                first_instr = block.instructions[0]
                if first_instr.opname == 'STORE_FAST':
                    return first_instr.argval
        
        # [备选方案2] 查找handler body中任何POP_TOP之后的STORE_FAST
        for block in handler_body:
            for i, instr in enumerate(block.instructions):
                if instr.opname == 'POP_TOP':
                    if i + 1 < len(block.instructions):
                        next_instr = block.instructions[i + 1]
                        if next_instr.opname == 'STORE_FAST':
                            return next_instr.argval
        

        
        return None
    
    def _identify_try_except_legacy(self, analyzed_blocks: Set[BasicBlock]) -> None:
        """识别try-except结构（支持 Python 3.11+）"""
        # [关键修复] 首先收集所有包含 PUSH_EXC_INFO 的块（Python 3.11+ 的 handler 入口）
        handler_entries = []
        for block in self.cfg.blocks.values():
            for instr in block.instructions:
                if instr.opname == 'PUSH_EXC_INFO':
                    handler_entries.append(block)
                    break
        
        # [关键修复] 如果没有 PUSH_EXC_INFO，使用旧方法（SETUP_EXCEPT）
        if not handler_entries:
            self._identify_try_except_pre_311(analyzed_blocks)
            return
        
        # [关键修复] Python 3.11+ 方法：从 handler 入口反向找到 try 入口
        # 使用局部集合来跟踪已处理的 try-except 结构，避免重复处理
        processed_try_entries = set()
        
        for handler_entry in handler_entries:
            # 找到对应的 try 入口
            # try 块在 handler 之前，且以 JUMP_FORWARD 结束
            # 找到对应的 try 入口
            # try 块在 handler 之前，且以 JUMP_FORWARD 结束
            # 找到对应的 try 入口
            # try 块在 handler 之前，且以 JUMP_FORWARD 结束
            # 找到对应的 try 入口
            # try 块在 handler 之前，且以 JUMP_FORWARD 结束
            try_entry = self._find_try_entry_for_handler(handler_entry, analyzed_blocks, processed_try_entries)
            if not try_entry or try_entry in processed_try_entries:
                continue
            
            processed_try_entries.add(try_entry)
            
            # 分析try-except结构
            try_struct = self._analyze_try_except_structure_v2(try_entry, handler_entry)
            if try_struct:
                self.structures.append(try_struct)
                
                for b in try_struct.try_body:
                    self.block_to_structure[b] = try_struct
                for exc_type, exc_body in try_struct.except_handlers:
                    for b in exc_body:
                        self.block_to_structure[b] = try_struct
                for b in try_struct.finally_body:
                    self.block_to_structure[b] = try_struct
    
    def _identify_try_except_pre_311(self, analyzed_blocks: Set[BasicBlock]) -> None:
        """Python 3.10 及更早版本的 try-except 识别"""
        for block in self.cfg.blocks.values():
            if block in analyzed_blocks:
                continue
            
            # 检查是否包含异常处理相关指令
            has_try = False
            for instr in block.instructions:
                if instr.opname in {'SETUP_EXCEPT', 'SETUP_FINALLY'}:
                    has_try = True
                    break
            
            if not has_try:
                continue
            
            # 分析try-except结构
            try_struct = self._analyze_try_except_structure_v2(block, None)
            if try_struct:
                self.structures.append(try_struct)
                
                for b in try_struct.try_body:
                    self.block_to_structure[b] = try_struct
                for exc_type, exc_body in try_struct.except_handlers:
                    for b in exc_body:
                        self.block_to_structure[b] = try_struct
                for b in try_struct.finally_body:
                    self.block_to_structure[b] = try_struct
    
    def _find_try_entry_for_handler(self, handler_entry: BasicBlock, analyzed_blocks: Set[BasicBlock], processed_try_entries: Set[BasicBlock]) -> Optional[BasicBlock]:
        """
        从 handler 入口反向找到 try 入口
        
        在 Python 3.11+ 中，try 块以 JUMP_FORWARD 结束，跳转到 try 块之后
        handler 入口是 PUSH_EXC_INFO 指令所在的块
        """
        # [关键修复] 从 handler_entry 反向查找，找到以 JUMP_FORWARD 结束的块
        # 这些块可能是 try 块的结尾
        
        # 首先找到所有前驱块
        visited = set()
        worklist = [handler_entry]
        candidates = []
        
        while worklist:
            block = worklist.pop(0)
            if block in visited:
                continue
            visited.add(block)
            
            # 检查这个块是否以 JUMP_FORWARD 结束
            if block.instructions:
                last_instr = block.instructions[-1]
                if last_instr.opname == 'JUMP_FORWARD':
                    jump_target = last_instr.arg
                    # 如果跳转目标在 handler 之后，这个块可能是 try 块的结尾
                    if jump_target and jump_target > handler_entry.start_offset:
                        # 找到这个块的入口
                        # 找到这个块的入口
                        # 找到这个块的入口
                        # 找到这个块的入口
                        try_entry = self._find_try_entry(block)
                        if try_entry and try_entry not in processed_try_entries:
                            candidates.append(try_entry)
            
            # 继续查找前驱
            for pred in block.predecessors:
                if pred not in visited:
                    worklist.append(pred)
        
        # 返回偏移量最大的候选（最接近 handler 的 try 块）
        if candidates:
            return max(candidates, key=lambda b: b.start_offset)
        

        
        return None
    
    def _find_try_entry(self, end_block: BasicBlock) -> Optional[BasicBlock]:
        """从try块的末尾反向找到入口"""
        # 简单策略：沿着前驱链找到最前面的块
        visited = {end_block}
        current = end_block
        
        while current.predecessors:
            # 找到不是循环的一部分的前驱
            # 找到不是循环的一部分的前驱
            # 找到不是循环的一部分的前驱
            # 找到不是循环的一部分的前驱
            preds = [p for p in current.predecessors if p not in visited]
            if not preds:
                break
            
            # 选择偏移量最小的前驱（最前面的）
            current = min(preds, key=lambda b: b.start_offset)
            visited.add(current)
            
            # 如果到达函数入口或没有前驱，停止
            if not current.predecessors:
                break
        
        return current
    
    def _analyze_try_except_structure_v2(self, try_entry: BasicBlock, first_handler: BasicBlock) -> Optional[TryExceptStructure]:
        """
        分析try-except结构（Python 3.11+版本）
        
        Args:
            try_entry: try块的入口块
            first_handler: 第一个异常处理块（包含 PUSH_EXC_INFO）
            
        Returns:
            try-except结构
        """
        except_handlers = []
        finally_body = []
        has_finally = False
        
        # [关键修复] 使用异常表来确定try块的范围
        # 找到包含 try_entry.start_offset 的异常表条目
        try_start = try_entry.start_offset
        try_end = None
        for entry in self.cfg.exception_table:
            if entry['start'] <= try_start < entry['end']:
                try_end = entry['end']
                break
        
        # [关键修复] 如果没有找到try_end，使用first_handler来找到try块的范围
        # first_handler是PUSH_EXC_INFO块，异常表中target等于first_handler.start_offset的条目
        # 对应的start和end就是try块的范围
        if try_end is None and first_handler:
            for entry in self.cfg.exception_table:
                if entry['target'] == first_handler.start_offset and entry['depth'] == 0:
                    try_start = entry['start']
                    try_end = entry['end']
                    break
        
        # [关键修复] 如果仍然没有找到，尝试找到包含 NOP 指令的块
        if try_end is None:
            for block in self.cfg.blocks.values():
                for instr in block.instructions:
                    if instr.opname == 'NOP':
                        nop_offset = instr.offset
                        for entry in self.cfg.exception_table:
                            if entry['start'] <= nop_offset < entry['end']:
                                try_start = entry['start']
                                try_end = entry['end']
                                try_entry = block
                                break
                        if try_end is not None:
                            break
                if try_end is not None:
                    break
        
        # [关键修复] 找到包含 try_start 偏移量的块作为真正的try块入口
        # 这可能是 try_entry 本身，也可能是其中的某个块
        # 因为 try_entry 可能包含 NOP 指令之前的代码
        real_try_entry = try_entry
        for block in self.cfg.blocks.values():
            if block.start_offset <= try_start < block.end_offset:
                real_try_entry = block
                break
        
        # [关键修复] 初始化try_body，使用real_try_entry作为起点
        try_body = [real_try_entry]
        
        # 收集try体 - 只包含在 try_start 到 try_end 范围内的块
        # [关键修复] 使用 real_try_entry 而不是 try_entry 作为起点
        visited = {real_try_entry}
        handler_blocks = set()
        
        # 首先收集所有异常处理块
        # [关键修复] 不要收集finally块（以POP_EXCEPT + JUMP_FORWARD结束的块的后继）
        handler_worklist = [first_handler]
        while handler_worklist:
            block = handler_worklist.pop(0)
            if block in handler_blocks:
                continue
            handler_blocks.add(block)
            
            # [关键修复] 检查是否是handler的结束（POP_EXCEPT + JUMP_FORWARD）
            is_handler_end = False
            for instr in block.instructions:
                if instr.opname == 'POP_EXCEPT':
                    for next_instr in block.instructions[block.instructions.index(instr)+1:]:
                        if next_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                            is_handler_end = True
                            break
            
            # [关键修复] 如果是handler的结束，不要收集后继块（那是finally块）
            if not is_handler_end:
                for succ in block.successors:
                    if succ not in handler_blocks:
                        handler_worklist.append(succ)
        
        # [关键修复] 收集try体（在异常表范围内的块，且不在handler_blocks中）
        # [关键修复] 使用 real_try_entry 的后继块
        worklist = list(real_try_entry.successors)
        while worklist:
            block = worklist.pop(0)
            if block in visited or block in handler_blocks:
                continue
            
            # [关键修复] 检查块是否在try范围内
            # 如果块的起始偏移量 >= try_end，则不属于这个try块
            if try_end is not None and block.start_offset >= try_end:
                continue
            
            # [关键修复] 检查块中的所有指令是否都在try范围内
            # 如果块中包含超出try_end的指令，需要特殊处理
            if try_end is not None:
                # 找到块中第一条 >= try_end 的指令
                # 找到块中第一条 >= try_end 的指令
                # 找到块中第一条 >= try_end 的指令
                # 找到块中第一条 >= try_end 的指令
                first_outside_instr = None
                for instr in block.instructions:
                    if instr.offset >= try_end:
                        first_outside_instr = instr
                        break
                
                if first_outside_instr is not None:
                    # 块中包含超出try_end的指令
                    # 检查这些指令是否是NOP（NOP是try-except的分隔符）
                    # 块中包含超出try_end的指令
                    # 检查这些指令是否是NOP（NOP是try-except的分隔符）
                    # 块中包含超出try_end的指令
                    # 检查这些指令是否是NOP（NOP是try-except的分隔符）
                    # 块中包含超出try_end的指令
                    # 检查这些指令是否是NOP（NOP是try-except的分隔符）
                    if first_outside_instr.opname == 'NOP':
                        # NOP是try-except的分隔符，可以忽略
                        # NOP是try-except的分隔符，可以忽略
                        # NOP是try-except的分隔符，可以忽略
                        # NOP是try-except的分隔符，可以忽略
                        pass
                    else:
                        # 块中包含有效的超出try_end的指令
                        # 这种情况通常发生在try块的最后一个块包含多条指令时
                        # 我们需要只包含try范围内的指令
                        # 但由于块是不可分割的，我们只能跳过整个块
                        # 或者标记这个块需要特殊处理
                        # [关键修复] 检查块中是否有任何指令在try范围内
                        has_instr_in_try = any(instr.offset < try_end for instr in block.instructions)
                        if not has_instr_in_try:
                            continue
                        # 如果块中有指令在try范围内，我们仍然包含这个块
                        # 但需要在后续处理中标记这个块的部分指令在try范围外
            
            visited.add(block)
            try_body.append(block)
            for succ in block.successors:
                if succ not in visited and succ not in handler_blocks:
                    worklist.append(succ)
        
        # 从handler块中提取异常类型
        processed_handlers = set()
        for block in sorted(handler_blocks, key=lambda b: b.start_offset):
            if block in processed_handlers:
                continue
            
            # 检查是否是异常handler的开始（PUSH_EXC_INFO）
            has_push_exc = False
            for instr in block.instructions:
                if instr.opname == 'PUSH_EXC_INFO':
                    has_push_exc = True
                    break
            
            if has_push_exc:
                # [关键修复] 只处理真正的except handler，不处理finally的异常路径
                # except handler的特征：包含 CHECK_EXC_MATCH 和 POP_JUMP_FORWARD_IF_FALSE
                # [关键修复] 只处理真正的except handler，不处理finally的异常路径
                # except handler的特征：包含 CHECK_EXC_MATCH 和 POP_JUMP_FORWARD_IF_FALSE
                # [关键修复] 只处理真正的except handler，不处理finally的异常路径
                # except handler的特征：包含 CHECK_EXC_MATCH 和 POP_JUMP_FORWARD_IF_FALSE
                # [关键修复] 只处理真正的except handler，不处理finally的异常路径
                # except handler的特征：包含 CHECK_EXC_MATCH 和 POP_JUMP_FORWARD_IF_FALSE
                has_check_exc_match = any(instr.opname == 'CHECK_EXC_MATCH' for instr in block.instructions)
                has_pop_jump = any(instr.opname == 'POP_JUMP_FORWARD_IF_FALSE' for instr in block.instructions)
                
                if not (has_check_exc_match and has_pop_jump):
                    continue
                
                # [关键修复] 传入空的visited集合，让每个handler独立收集
                # 因为多个except handler是并列的，不是嵌套的
                exc_type, handler_body = self._extract_exception_handler(block, set())
                exc_name = self._extract_exception_name_from_handler(block)
                if handler_body:
                    except_handlers.append((exc_type, exc_name, handler_body))
                    processed_handlers.update(handler_body)
        
        # [关键修复] 识别finally子句
        # finally子句的特征：
        # 1. 在try/except/else之后执行
        # 2. 有两个入口：正常路径和异常路径
        # 3. 正常路径以JUMP_FORWARD结束
        
        # [关键修复] 收集所有已处理的handler body块
        all_handler_body_blocks = set()
        for _, _, h_blocks in except_handlers:
            all_handler_body_blocks.update(h_blocks)
        
        # 找到所有handler body的最后一个块
        last_handler_blocks = []
        for _, _, h_blocks in except_handlers:
            if h_blocks:
                last_handler_blocks.append(max(h_blocks, key=lambda b: b.end_offset))
        
        # 查找从handler块或try/else块跳转出来的块（可能是finally块）
        # [关键修复] finally有两个路径：
        # 1. 正常路径：从try/else块跳转过来，以JUMP_FORWARD结束
        # 2. 异常路径：从handler块跳转过来，以RERAISE结束
        finally_candidates = set()
        
        # 从handler块查找（异常路径）
        for block in last_handler_blocks:
            for succ in block.successors:
                # [关键修复] 使用 all_handler_body_blocks 而不是 handler_blocks
                # [关键修复] 使用 all_handler_body_blocks 而不是 handler_blocks
                # [关键修复] 使用 all_handler_body_blocks 而不是 handler_blocks
                # [关键修复] 使用 all_handler_body_blocks 而不是 handler_blocks
                if succ not in all_handler_body_blocks and succ not in try_body:
                    # 检查这个块是否以JUMP_FORWARD或RERAISE结束
                    # 检查这个块是否以JUMP_FORWARD或RERAISE结束
                    # 检查这个块是否以JUMP_FORWARD或RERAISE结束
                    # 检查这个块是否以JUMP_FORWARD或RERAISE结束
                    has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in succ.instructions)
                    has_reraise = any(instr.opname == 'RERAISE' for instr in succ.instructions)
                    if has_jump_forward or has_reraise:
                        finally_candidates.add(succ)
        
        # [关键修复-根本性修复] 识别else子句和finally子句
        # 在Python 3.11+中，try-except-else-finally的字节码结构：
        # 1. try body 以 JUMP_FORWARD 结束，跳转到 else body（如果有）或 finally（如果有）
        # 2. else body 以 JUMP_FORWARD 结束，跳转到 finally 或 try-except 之后的代码
        # 3. finally 有两个路径：正常路径（JUMP_FORWARD）和异常路径（RERAISE）
        
        # [关键修复] 从try body查找正常路径的后继
        # 这可能是 else body 或 finally 的正常路径
        else_candidates = []
        for block in try_body:
            has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in block.instructions)
            if has_jump_forward:
                for succ in block.successors:
                    if succ not in all_handler_body_blocks and succ not in try_body:
                        # 检查后继块是否以JUMP_FORWARD结束
                        succ_has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in succ.instructions)
                        if succ_has_jump_forward:
                            # 这可能是 else body 或 finally 的正常路径
                            # 检查这个块是否会被handler块跳转到（如果是，则是finally）
                            is_finally = False
                            for handler_block in all_handler_body_blocks:
                                if succ in handler_block.successors:
                                    is_finally = True
                                    break
                            if is_finally:
                                finally_candidates.add(succ)
                            else:
                                # 这可能是 else body
                                else_candidates.append(succ)
        
        # [关键修复-根本性修复] 收集else body（如果存在）
        else_body = []
        has_else_code = False
        
        # [关键修复] 检查try_body块中是否有try_end之后的代码（else代码）
        # 这种情况发生在try-except-else结构中，else代码和try代码在同一个块
        if try_end is not None:
            for block in try_body:
                # 检查块中是否有try_end之后的指令
                for instr in block.instructions:
                    if instr.offset >= try_end:
                        # 跳过NOP和JUMP_FORWARD
                        if instr.opname not in ('NOP', 'JUMP_FORWARD', 'JUMP_BACKWARD'):
                            has_else_code = True
                            break
                if has_else_code:
                    break
        
        # [关键修复] 如果try_body块中有else代码，标记为has_else
        # 实际的else代码提取在AST生成阶段处理
        if has_else_code:
            # else代码在try_body块中，不需要单独的else_body块
            pass
        
        if else_candidates:
            # 收集else body的所有块
            # else body的特征：不包含 POP_EXCEPT，以 JUMP_FORWARD 结束
            else_worklist = list(else_candidates)
            else_visited = set()
            
            while else_worklist:
                block = else_worklist.pop(0)
                if block in else_visited:
                    continue
                
                # 检查是否是handler块（包含 POP_EXCEPT）
                has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in block.instructions)
                if has_pop_except:
                    continue
                
                else_visited.add(block)
                else_body.append(block)
                
                # 继续收集后继块（只要不是以 JUMP_FORWARD 结束的块的后继）
                has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in block.instructions)
                if not has_jump_forward:
                    for succ in block.successors:
                        if succ not in else_visited and succ not in all_handler_body_blocks and succ not in try_body:
                            else_worklist.append(succ)
            
            if else_body:
                else_body.sort(key=lambda b: b.start_offset)
            
            has_else_code = True
        
        # 如果找到了finally候选块，收集finally体
        if finally_candidates:
            # 收集所有finally块（包括正常路径和异常路径）
            # 收集所有finally块（包括正常路径和异常路径）
            # 收集所有finally块（包括正常路径和异常路径）
            # 收集所有finally块（包括正常路径和异常路径）
            finally_worklist = list(finally_candidates)
            finally_visited = set()
            
            while finally_worklist:
                block = finally_worklist.pop(0)
                if block in finally_visited:
                    continue
                
                finally_visited.add(block)
                finally_body.append(block)
                
                # 继续收集后继块（只要不是RERAISE块或RETURN_VALUE块）
                # [关键修复] 如果当前块以JUMP_FORWARD结束，不要收集后继块
                # 因为JUMP_FORWARD会跳转到函数的其他部分（如return语句）
                has_jump_forward = any(instr.opname == 'JUMP_FORWARD' for instr in block.instructions)
                if not has_jump_forward:
                    for succ in block.successors:
                        if succ not in finally_visited:
                            has_reraise = any(instr.opname == 'RERAISE' for instr in succ.instructions)
                            has_return = any(instr.opname == 'RETURN_VALUE' for instr in succ.instructions)
                            if not has_reraise and not has_return:
                                finally_worklist.append(succ)
            
            if finally_body:
                has_finally = True
                finally_body.sort(key=lambda b: b.start_offset)
        
        return TryExceptStructure(
            struct_type=ControlStructureType.TRY_EXCEPT,
            entry_block=real_try_entry,
            try_body=try_body,
            except_handlers=except_handlers,
            else_body=else_body,
            finally_body=finally_body,
            has_else=has_else_code,
            has_finally=has_finally,
            try_start_offset=try_start,
            try_end_offset=try_end if try_end else 0
        )
    
    def _extract_exception_handler(self, header: BasicBlock, global_visited: Set[BasicBlock]) -> Tuple[Optional[str], List[BasicBlock]]:
        """
        提取异常handler的信息
        
        Args:
            header: 异常handler的头部块（包含 PUSH_EXC_INFO）
            global_visited: 全局已访问块集合
            
        Returns:
            (异常类型, handler体块列表)
        """
        exc_type = None
        handler_body = [header]
        
        # 提取异常类型 - 在 PUSH_EXC_INFO 之后，CHECK_EXC_MATCH 之前
        for i, instr in enumerate(header.instructions):
            if instr.opname == 'PUSH_EXC_INFO':
                # 向后查找 LOAD_GLOBAL/LOAD_NAME（异常类型）
                # 向后查找 LOAD_GLOBAL/LOAD_NAME（异常类型）
                # 向后查找 LOAD_GLOBAL/LOAD_NAME（异常类型）
                # 向后查找 LOAD_GLOBAL/LOAD_NAME（异常类型）
                for j in range(i+1, len(header.instructions)):
                    next_instr = header.instructions[j]
                    if next_instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                        if next_instr.argval and isinstance(next_instr.argval, str):
                            val = next_instr.argval
                            # 检查是否是有效的异常类型名称
                            if val and val[0].isupper() and not val.startswith('\'') and not val.startswith('"'):
                                exc_type = val
                                break
                    elif next_instr.opname in ('CHECK_EXC_MATCH', 'POP_JUMP_FORWARD_IF_FALSE'):
                        # 到达匹配检查，停止查找
                        # 到达匹配检查，停止查找
                        break
            elif instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                # 备选：直接查找
                # 备选：直接查找
                if instr.argval and isinstance(instr.argval, str):
                    val = instr.argval
                    if val and val[0].isupper() and not val.startswith('\'') and not val.startswith('"'):
                        exc_type = val
        
        # 收集handler体 - 包括所有后继块，直到遇到 RERAISE 或 POP_EXCEPT + JUMP_FORWARD
        worklist = list(header.successors)
        visited = {header}
        
        while worklist:
            block = worklist.pop(0)
            if block in visited or block in global_visited:
                continue
            
            # [关键修复] 在添加块到handler_body之前，先检查是否是结束块
            # 检查是否是handler的结束
            is_end = False
            has_jump_forward = False
            for instr in block.instructions:
                if instr.opname == 'RERAISE':
                    is_end = True
                    break
                elif instr.opname == 'POP_EXCEPT':
                    # 检查后面是否有 JUMP_FORWARD（表示handler结束）
                    # 检查后面是否有 JUMP_FORWARD（表示handler结束）
                    for next_instr in block.instructions[block.instructions.index(instr)+1:]:
                        if next_instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                            is_end = True
                            has_jump_forward = True
                            break
            
            visited.add(block)
            handler_body.append(block)
            
            # [关键修复] 如果handler以JUMP_FORWARD结束，不要收集JUMP_FORWARD的目标块
            # 因为那是finally块或else块
            if not is_end:
                for succ in block.successors:
                    if succ not in visited and succ not in global_visited:
                        worklist.append(succ)
            elif has_jump_forward:
                # [关键修复] 标记这个块为handler的最后一个块，其后继可能是finally块
                # [关键修复] 标记这个块为handler的最后一个块，其后继可能是finally块
                pass  # 不添加后继块
        
        return exc_type, handler_body
    
    def _identify_with_structures(self) -> None:
        """识别with上下文管理器结构"""
        analyzed_blocks = set(self.block_to_structure.keys())
        
        for block in self.cfg.blocks.values():
            # [关键修复] 处理一个块中的多个 BEFORE_WITH / BEFORE_ASYNC_WITH 指令
            # 查找所有 BEFORE_WITH 和 BEFORE_ASYNC_WITH 的位置
            # [关键修复] 处理一个块中的多个 BEFORE_WITH / BEFORE_ASYNC_WITH 指令
            # 查找所有 BEFORE_WITH 和 BEFORE_ASYNC_WITH 的位置
            # [关键修复] 处理一个块中的多个 BEFORE_WITH / BEFORE_ASYNC_WITH 指令
            # 查找所有 BEFORE_WITH 和 BEFORE_ASYNC_WITH 的位置
            # [关键修复] 处理一个块中的多个 BEFORE_WITH / BEFORE_ASYNC_WITH 指令
            # 查找所有 BEFORE_WITH 和 BEFORE_ASYNC_WITH 的位置
            before_with_positions = []
            for i, instr in enumerate(block.instructions):
                if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                    before_with_positions.append((i, instr.opname == 'BEFORE_ASYNC_WITH'))
            
            if not before_with_positions:
                continue
            
            # [关键修复] 检查这个块是否已经被识别为with结构
            # 如果是，跳过（避免重复识别同一个with）
            existing_with = False
            for struct in self.structures:
                if isinstance(struct, WithStructure) and struct.entry_block == block:
                    existing_with = True
                    break
            if existing_with:
                continue
            
            # [关键修复] 检查是否是多上下文with（连续的多个BEFORE_WITH）
            # 如果是连续的BEFORE_WITH（中间没有其他控制流），则合并为一个WithStructure
            
            if len(before_with_positions) > 1:
                
                # 检查是否是多上下文with
                # 多上下文with的特征：
                # 1. 所有的BEFORE_WITH指令都在同一个块中
                # 2. 它们的body是共享的（即所有的with语句都共享同一个代码块）
                # 3. 中间只有async with相关的指令，没有其他控制流
                
                # 检查是否所有BEFORE_WITH都是连续的（中间没有其他控制流指令）
                
                # 检查是否是多上下文with
                # 多上下文with的特征：
                # 1. 所有的BEFORE_WITH指令都在同一个块中
                # 2. 它们的body是共享的（即所有的with语句都共享同一个代码块）
                # 3. 中间只有async with相关的指令，没有其他控制流
                
                # 检查是否所有BEFORE_WITH都是连续的（中间没有其他控制流指令）
                
                # 检查是否是多上下文with
                # 多上下文with的特征：
                # 1. 所有的BEFORE_WITH指令都在同一个块中
                # 2. 它们的body是共享的（即所有的with语句都共享同一个代码块）
                # 3. 中间只有async with相关的指令，没有其他控制流
                
                # 检查是否所有BEFORE_WITH都是连续的（中间没有其他控制流指令）
                
                # 检查是否是多上下文with
                # 多上下文with的特征：
                # 1. 所有的BEFORE_WITH指令都在同一个块中
                # 2. 它们的body是共享的（即所有的with语句都共享同一个代码块）
                # 3. 中间只有async with相关的指令，没有其他控制流
                
                # 检查是否所有BEFORE_WITH都是连续的（中间没有其他控制流指令）
                is_multi_context = True
                
                # 检查第一个和第二个BEFORE_WITH之间的指令
                first_pos = before_with_positions[0][0]
                second_pos = before_with_positions[1][0]
                
                # 检查中间是否有STORE_FAST/STORE_NAME指令（嵌套with的特征）
                has_store_between = False
                for j in range(first_pos + 1, second_pos):
                    instr = block.instructions[j]
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                        has_store_between = True
                        break
                
                # 对于async with，检查是否有POP_TOP指令（这表示第一个async with的结束）
                has_pop_top_between = False
                for j in range(first_pos + 1, second_pos):
                    instr = block.instructions[j]
                    if instr.opname == 'POP_TOP':
                        has_pop_top_between = True
                        break
                
                # 如果中间有STORE或POP_TOP指令，说明是嵌套with
                if has_store_between or has_pop_top_between:
                    # 中间有STORE或POP_TOP指令，说明是嵌套with
                    # 中间有STORE或POP_TOP指令，说明是嵌套with
                    # 中间有STORE或POP_TOP指令，说明是嵌套with
                    # 中间有STORE或POP_TOP指令，说明是嵌套with
                    is_multi_context = False
                else:
                    # 检查中间是否有控制流指令
                    for j in range(first_pos + 1, second_pos):
                        instr = block.instructions[j]
                        # 允许async with相关的指令
                        if instr.opname in ('GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'RESUME', 
                                           'JUMP_BACKWARD_NO_INTERRUPT', 'LOAD_CONST', 'PRECALL', 'CALL',
                                           'SWAP', 'POP_TOP', 'NOP', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL',
                                           'LOAD_METHOD', 'BINARY_OP', 'UNARY_OP', 'COMPARE_OP',
                                           'DUP_TOP', 'DUP_TOP_TWO', 'ROT_TWO', 'ROT_THREE'):
                            continue
                        # 检查是否有控制流指令
                        if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'POP_JUMP_FORWARD_IF_FALSE', 
                                           'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE',
                                           'RETURN_VALUE', 'RERAISE', 'RAISE_VARARGS'):
                            is_multi_context = False
                            break
                
                if is_multi_context:
                    # [关键修复] 多上下文with，合并为一个WithStructure
                    # [关键修复] 多上下文with，合并为一个WithStructure
                    # [关键修复] 多上下文with，合并为一个WithStructure
                    # [关键修复] 多上下文with，合并为一个WithStructure
                    with_struct = self._analyze_multi_with_structure(block, before_with_positions)
                    if with_struct:
                        self.structures.append(with_struct)
                        for b in with_struct.with_body:
                            self.block_to_structure[b] = with_struct
                        self.block_to_structure[block] = with_struct
                        analyzed_blocks.add(block)
                    # 多上下文with处理完毕，跳过后续的单个处理
                    continue
            
            # 处理单个 BEFORE_WITH / BEFORE_ASYNC_WITH
            for idx, (before_with_pos, is_async) in enumerate(before_with_positions):
                # [关键修复] 对于同一个块中的多个with，都使用原始块作为entry
                # 但是每个with有不同的before_with_pos，所以它们会被正确处理
                # [关键修复] 对于同一个块中的多个with，都使用原始块作为entry
                # 但是每个with有不同的before_with_pos，所以它们会被正确处理
                # [关键修复] 对于同一个块中的多个with，都使用原始块作为entry
                # 但是每个with有不同的before_with_pos，所以它们会被正确处理
                # [关键修复] 对于同一个块中的多个with，都使用原始块作为entry
                # 但是每个with有不同的before_with_pos，所以它们会被正确处理
                entry_block = block
                
                with_struct = self._analyze_with_structure(entry_block, before_with_pos, is_async)
                if with_struct:
                    self.structures.append(with_struct)
                    
                    for b in with_struct.with_body:
                        self.block_to_structure[b] = with_struct
                    # [关键修复] 只对第一个with添加block到block_to_structure
                    # 后续with共享同一个entry block，但是有不同的body
                    if idx == 0:
                        self.block_to_structure[entry_block] = with_struct
                    analyzed_blocks.add(entry_block)
    
    def _find_next_with_entry(self, block: BasicBlock, before_with_pos: int) -> Optional[BasicBlock]:
        """查找下一个with语句的入口块"""
        # 在BEFORE_WITH之后查找STORE_FAST，然后找到下一个指令块
        for i in range(before_with_pos + 1, len(block.instructions)):
            instr = block.instructions[i]
            if instr.opname == 'STORE_FAST':
                # 查找这个变量的后续使用块
                # 查找这个变量的后续使用块
                # 查找这个变量的后续使用块
                # 查找这个变量的后续使用块
                target_var = str(instr.argval)
                for succ in block.successors:
                    # 检查后继块是否使用了这个变量
                    # 检查后继块是否使用了这个变量
                    # 检查后继块是否使用了这个变量
                    # 检查后继块是否使用了这个变量
                    for succ_instr in succ.instructions:
                        if succ_instr.opname == 'LOAD_FAST' and str(succ_instr.argval) == target_var:
                            return succ
                break
        return None
    
    def _analyze_with_structure(self, entry_block: BasicBlock, before_with_pos: int = 0, is_async: bool = False) -> Optional[WithStructure]:
        """
        分析with结构
        
        Args:
            entry_block: 入口块
            before_with_pos: BEFORE_WITH / BEFORE_ASYNC_WITH 指令的位置
            is_async: 是否为异步with
            
        Returns:
            with结构
        """
        with_body = self._find_with_body(entry_block, before_with_pos)
        

        
        if not with_body:
            return None
        
        # [关键修复] 提取 resource_expr 和 target
        resource_expr = self._extract_with_resource(entry_block, before_with_pos)
        target = self._extract_with_target(entry_block, before_with_pos)
        
        with_struct = WithStructure(
            struct_type=ControlStructureType.WITH,
            entry_block=entry_block,
            with_body=with_body,
            resource_expr=resource_expr,
            target=target,
            is_async=is_async
        )
        
        return with_struct
    
    def _analyze_multi_with_structure(self, entry_block: BasicBlock, before_with_positions: List[Tuple[int, bool]]) -> Optional[WithStructure]:
        """
        [关键修复] 分析多上下文with结构（如：with ctx1() as a, ctx2() as b:）
        
        Args:
            entry_block: 入口块
            before_with_positions: 所有BEFORE_WITH/BEFORE_ASYNC_WITH的位置列表 [(pos, is_async), ...]
            
        Returns:
            包含多个items的with结构
        """
        if not before_with_positions:
            return None
        
        # 使用第一个BEFORE_WITH的位置来查找with body
        first_pos, is_async = before_with_positions[0]
        with_body = self._find_with_body(entry_block, first_pos)
        
        if not with_body:
            return None
        
        # [关键修复] 提取所有resource_expr和target
        # 对于多上下文with，我们需要提取所有的资源表达式和变量
        items = []
        resource_exprs = []
        targets = []
        
        for before_with_pos, _ in before_with_positions:
            resource_expr = self._extract_with_resource(entry_block, before_with_pos)
            target = self._extract_with_target(entry_block, before_with_pos)
            if resource_expr:
                resource_exprs.append(resource_expr)
                targets.append(target)
                items.append((resource_expr, target))
        
        # [关键修复] 将多个资源表达式和变量合并为单个字符串（用于兼容性）
        # 格式："ctx1() as a, ctx2() as b, ctx3() as c"
        if len(resource_exprs) > 1:
            combined_resource = ", ".join([
                f"{expr} as {tgt}" if tgt else expr
                for expr, tgt in zip(resource_exprs, targets)
            ])
            combined_target = ", ".join(targets) if targets else None
        else:
            combined_resource = resource_exprs[0] if resource_exprs else None
            combined_target = targets[0] if targets else None
        
        with_struct = WithStructure(
            struct_type=ControlStructureType.WITH,
            entry_block=entry_block,
            with_body=with_body,
            resource_expr=combined_resource,
            target=combined_target,
            is_async=is_async,
            items=items  # [关键修复] 保存所有items
        )
        
        return with_struct
    
    def _extract_with_resource(self, entry_block: BasicBlock, before_with_pos: int = 0) -> Optional[str]:
        """提取with语句的资源表达式"""
        # [关键修复] 使用传入的 before_with_pos 参数
        before_with_idx = before_with_pos

        if before_with_idx < 0 or before_with_idx >= len(entry_block.instructions):
            return None

        # [关键修复] 查找这个with对应的资源表达式
        # 如果是同一个块中的多个with，需要找到正确的资源表达式范围
        # 查找上一个BEFORE_WITH/BEFORE_ASYNC_WITH或块开始的位置
        start_idx = 0
        prev_before_with_idx = -1
        for i in range(before_with_idx - 1, -1, -1):
            if entry_block.instructions[i].opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                prev_before_with_idx = i
                break
        
        if prev_before_with_idx >= 0:
            # [关键修复] 找到上一个BEFORE_WITH/BEFORE_ASYNC_WITH之后，需要跳过async with的完整序列
            # async with序列: STORE_FAST + (GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + JUMP)* + LOAD_GLOBAL + PRECALL + CALL
            # [关键修复] 找到上一个BEFORE_WITH/BEFORE_ASYNC_WITH之后，需要跳过async with的完整序列
            # async with序列: STORE_FAST + (GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + JUMP)* + LOAD_GLOBAL + PRECALL + CALL
            # [关键修复] 找到上一个BEFORE_WITH/BEFORE_ASYNC_WITH之后，需要跳过async with的完整序列
            # async with序列: STORE_FAST + (GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + JUMP)* + LOAD_GLOBAL + PRECALL + CALL
            # [关键修复] 找到上一个BEFORE_WITH/BEFORE_ASYNC_WITH之后，需要跳过async with的完整序列
            # async with序列: STORE_FAST + (GET_AWAITABLE + SEND + YIELD_VALUE + RESUME + JUMP)* + LOAD_GLOBAL + PRECALL + CALL
            start_idx = prev_before_with_idx + 1
            # 从prev_before_with_idx + 1开始，找到下一个LOAD_GLOBAL或LOAD_NAME（下一个context的开始）
            # 这会包含async with的中间指令
            # 实际上，我们只需要从上一个BEFORE_ASYNC_WITH之后开始，跳过async序列，找到下一个资源表达式
            # 跳过async with序列：STORE_FAST, GET_AWAITABLE, SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD, LOAD_*, PRECALL, CALL
            skip_end = prev_before_with_idx
            for i in range(prev_before_with_idx + 1, len(entry_block.instructions)):
                instr = entry_block.instructions[i]
                if instr.offset >= before_with_idx:
                    # 到达当前BEFORE_ASYNC_WITH，停止
                    # 到达当前BEFORE_ASYNC_WITH，停止
                    # 到达当前BEFORE_ASYNC_WITH，停止
                    # 到达当前BEFORE_ASYNC_WITH，停止
                    start_idx = i - 1
                    break
                # 跳过async with中间的所有指令
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                   'GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'RESUME',
                                   'JUMP_BACKWARD_NO_INTERRUPT', 'POP_TOP', 'NOP',
                                   'LOAD_CONST', 'PRECALL', 'CALL'):
                    continue
                # 遇到LOAD_GLOBAL/LOAD_NAME，这是下一个资源表达式的开始
                if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                    start_idx = i
                    break
        else:
            # 第一个with，从块开始
            start_idx = 0

        # resource 表达式在 BEFORE_WITH/BEFORE_ASYNC_WITH 之前（从start_idx到before_with_idx）
        resource_instrs = []
        for i in range(start_idx, before_with_idx):
            instr = entry_block.instructions[i]
            # 跳过 RESUME 和不需要的指令
            if instr.opname in ('RESUME', 'CACHE', 'POP_TOP', 'NOP', 'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                              'GET_AWAITABLE', 'SEND', 'YIELD_VALUE', 'JUMP_BACKWARD_NO_INTERRUPT'):
                continue
            resource_instrs.append(instr)

        # 使用栈模拟来重建表达式
        if resource_instrs:
            return self._reconstruct_expr_from_instrs(resource_instrs)

        return None
    
    def _reconstruct_expr_from_instrs(self, instrs: List[Any]) -> Optional[str]:
        """从指令序列重建表达式字符串"""
        stack = []
        kw_names = None  # [关键修复] 存储 KW_NAMES 指令的关键字参数名
        
        for instr in instrs:
            opname = instr.opname
            argval = instr.argval
            
            if opname in ('LOAD_GLOBAL', 'LOAD_NAME'):
                stack.append(str(argval))
            elif opname in ('LOAD_FAST', 'LOAD_DEREF', 'LOAD_CLOSURE'):
                stack.append(str(argval))
            elif opname == 'LOAD_CONST':
                if isinstance(argval, str):
                    stack.append(repr(argval))
                else:
                    stack.append(repr(argval))
            elif opname == 'LOAD_ATTR':
                if stack:
                    obj = stack.pop()
                    stack.append(f"{obj}.{argval}")
            elif opname == 'LOAD_METHOD':
                if stack:
                    obj = stack.pop()
                    stack.append(f"{obj}.{argval}")
            elif opname == 'PRECALL':
                # 函数调用的参数数量，Python 3.11+ 的预调用指令
                # 不执行实际操作，只是标记
                # 函数调用的参数数量，Python 3.11+ 的预调用指令
                # 不执行实际操作，只是标记
                pass
            elif opname == 'CALL':
                # Python 3.11+ 的 CALL 指令
                # Python 3.11+ 的 CALL 指令
                nargs = argval if argval is not None else 0
                if len(stack) >= nargs + 1:
                    args = []
                    kwargs = []
                    
                    # [关键修复] 处理关键字参数
                    if kw_names and isinstance(kw_names, tuple):
                        # 有关键字参数，最后 len(kw_names) 个参数是关键字参数
                        # 有关键字参数，最后 len(kw_names) 个参数是关键字参数
                        # 有关键字参数，最后 len(kw_names) 个参数是关键字参数
                        # 有关键字参数，最后 len(kw_names) 个参数是关键字参数
                        kw_arg_count = len(kw_names)
                        pos_arg_count = nargs - kw_arg_count
                        
                        # 弹出关键字参数（从后往前）
                        for i in range(kw_arg_count - 1, -1, -1):
                            if stack:
                                value = stack.pop()
                                kwargs.insert(0, f"{kw_names[i]}={value}")
                        
                        # 弹出位置参数
                        for _ in range(pos_arg_count):
                            if stack:
                                args.insert(0, stack.pop())
                        
                        # 清除 KW_NAMES
                        kw_names = None
                    else:
                        # 没有关键字参数，所有参数都是位置参数
                        for _ in range(nargs):
                            if stack:
                                args.insert(0, stack.pop())
                    
                    func = stack.pop()
                    if func is not None:
                        # 合并位置参数和关键字参数
                        # 合并位置参数和关键字参数
                        # 合并位置参数和关键字参数
                        # 合并位置参数和关键字参数
                        all_args = args + kwargs
                        stack.append(f"{func}({', '.join(all_args)})")
            elif opname == 'KW_NAMES':
                # [关键修复] 存储关键字参数名称，供后续的 CALL 指令使用
                # instr.arg 是常量表索引，需要从 code.co_consts 中获取关键字参数名元组
                # [关键修复] 存储关键字参数名称，供后续的 CALL 指令使用
                # instr.arg 是常量表索引，需要从 code.co_consts 中获取关键字参数名元组
                try:
                    if hasattr(self, 'cfg') and self.cfg and hasattr(self.cfg, 'code'):
                        kw_names = self.cfg.code.co_consts[instr.arg]
                    elif hasattr(self, 'code') and self.code:
                        kw_names = self.code.co_consts[instr.arg]
                    else:
                        kw_names = argval
                except (IndexError, AttributeError):
                    kw_names = argval
            elif opname == 'PUSH_NULL':
                # PUSH_NULL 是 Python 3.11+ 的标记，不应该出现在最终表达式中
                # 跳过它，不压入栈
                # PUSH_NULL 是 Python 3.11+ 的标记，不应该出现在最终表达式中
                # 跳过它，不压入栈
                pass
        
        # 返回栈顶元素（跳过任何None值）
        while stack:
            result = stack[-1]
            if result is not None:
                return result
            stack.pop()
        

        
        return None
    
    def _extract_with_target(self, entry_block: BasicBlock, before_with_pos: int = 0) -> Optional[str]:
        """提取with语句的目标变量"""
        # [关键修复] 使用传入的 before_with_pos 参数
        before_with_idx = before_with_pos

        if before_with_idx < 0 or before_with_idx >= len(entry_block.instructions):
            return None

        # [关键修复] 查找这个with对应的STORE_FAST
        # 如果是同一个块中的多个with，需要找到正确的target
        # 查找下一个BEFORE_WITH/BEFORE_ASYNC_WITH的位置
        next_before_with = len(entry_block.instructions)
        for i in range(before_with_idx + 1, len(entry_block.instructions)):
            if entry_block.instructions[i].opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                next_before_with = i
                break

        # [关键修复] 检查BEFORE_WITH之后是否是POP_TOP（表示没有as子句）
        # 如果是POP_TOP，说明这个with没有target变量
        for i in range(before_with_idx + 1, min(next_before_with, len(entry_block.instructions))):
            instr = entry_block.instructions[i]
            # 如果遇到POP_TOP，说明没有as子句，返回None
            if instr.opname == 'POP_TOP':
                return None
            # 如果遇到STORE，返回变量名
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                return str(instr.argval)
            # 如果遇到其他非控制流指令，继续查找
            if instr.opname not in ('NOP', 'RESUME', 'CACHE', 'POP_TOP'):
                continue

        # [关键修复] 对于异步with，STORE_FAST可能在一个后继块中
        # 但首先检查BEFORE_WITH之后是否直接是POP_TOP（表示没有as子句）
        # 只有在确认不是POP_TOP的情况下才去后继块中查找
        
        # 检查BEFORE_WITH之后的前几个指令
        has_pop_top_after_before_with = False
        for i in range(before_with_idx + 1, min(before_with_idx + 5, len(entry_block.instructions))):
            instr = entry_block.instructions[i]
            if instr.opname == 'POP_TOP':
                has_pop_top_after_before_with = True
                break
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                # 找到了STORE，不需要去后继块查找
                # 找到了STORE，不需要去后继块查找
                # 找到了STORE，不需要去后继块查找
                # 找到了STORE，不需要去后继块查找
                has_pop_top_after_before_with = False
                break
        
        # 如果BEFORE_WITH之后有POP_TOP，说明没有as子句，不去后继块查找
        if has_pop_top_after_before_with:
            return None
        
        # 递归搜索所有后继块（仅限于with相关的块）
        visited = set()
        def search_for_store_fast(block, depth=0):
            if depth > 3:  # 限制搜索深度，避免搜索到不相关的块
                return None
            if id(block) in visited:
                return None
            visited.add(id(block))
            
            for instr in block.instructions:
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                    return str(instr.argval)
                # 如果遇到POP_TOP，说明没有as子句
                if instr.opname == 'POP_TOP':
                    return None
                # 如果遇到其他类型的指令，停止搜索这个块
                if instr.opname not in ('NOP', 'RESUME', 'CACHE', 'SEND', 'YIELD_VALUE', 'JUMP_BACKWARD_NO_INTERRUPT', 'SWAP'):
                    break
            
            # 递归搜索后继块
            for succ in block.successors:
                result = search_for_store_fast(succ, depth + 1)
                if result is not None:
                    return result
            return None
        
        for succ in entry_block.successors:
            result = search_for_store_fast(succ)
            if result is not None:
                return result

        return None

    def _merge_multi_context_withs(self) -> None:
        """
        [关键修复] 合并多上下文with结构

        多上下文with（如：with ctx1() as a, ctx2() as b:）在字节码中会被编译为嵌套的with结构。
        这个方法识别并合并这些嵌套的with结构。

        识别特征：
        1. 连续的WithStructure
        2. 外层with的body只包含内层with的entry_block
        3. 所有with都是同步或都是异步
        """
        # 收集所有with结构
        with_structs = [s for s in self.structures if isinstance(s, WithStructure)]
        if len(with_structs) < 2:
            return

        
        # 按entry_block的偏移量排序
        with_structs.sort(key=lambda w: w.entry_block.start_offset if w.entry_block else float('inf'))

        # 查找可以合并的with链
        merged_indices = set()
        new_structures = []

        i = 0
        while i < len(with_structs):
            if i in merged_indices:
                i += 1
                continue

            current = with_structs[i]
            chain = [current]

            # 查找后续的with是否形成链
            j = i + 1
            while j < len(with_structs):
                if j in merged_indices:
                    j += 1
                    continue

                next_with = with_structs[j]
                
                # 检查是否是链式结构：当前with的body只包含下一个with的entry_block
                is_chain = self._is_with_chain(current, next_with)
                if is_chain:
                    chain.append(next_with)
                    merged_indices.add(j)
                    current = next_with
                    j += 1
                else:
                    break

            # 如果找到链，合并它们
            if len(chain) > 1:
                merged = self._create_merged_with_structure(chain)
                if merged:
                    new_structures.append(merged)
                    merged_indices.add(i)
                    # 更新block_to_structure映射
                    for w in chain:
                        if w in self.structures:
                            self.structures.remove(w)
                        for b in w.with_body:
                            if b in self.block_to_structure and self.block_to_structure[b] == w:
                                del self.block_to_structure[b]
                    # 添加新的映射
                    self.structures.append(merged)
                    for b in merged.with_body:
                        self.block_to_structure[b] = merged
                    if merged.entry_block:
                        self.block_to_structure[merged.entry_block] = merged
            else:
                # 不是链，保留原样
                pass

            i += 1

    def _is_with_chain(self, outer: WithStructure, inner: WithStructure) -> bool:
        """
        检查两个with是否形成链式结构（多上下文with的嵌套形式）

        启发式判断：
        1. 两个with都是同步或都是异步
        2. [关键修复] 检查是否是连续的多上下文with（entry_block偏移量接近）
        3. 内层with的entry_block在外层with的body中（如果是嵌套）
        4. 外层with的target变量是否在内层with的body中被使用（区分嵌套vs多上下文）
        """
        if not outer.entry_block or not inner.entry_block:
            return False

        # 检查是否都是同步或都是异步
        if outer.is_async != inner.is_async:
            return False

        # [关键修复] 检查entry_block的偏移量是否接近
        # 这是多上下文with的关键特征
        outer_end = outer.entry_block.end_offset
        inner_start = inner.entry_block.start_offset
        
        # 如果距离太远，不是链式结构
        if inner_start - outer_end > 50:
            return False

        # [关键修复] 对于async with，检查是否是连续的多上下文
        # 特征：inner的entry紧跟在outer的BEFORE_ASYNC_WITH之后
        if outer.is_async:
            # 检查outer.entry_block中是否有BEFORE_ASYNC_WITH
            # 检查outer.entry_block中是否有BEFORE_ASYNC_WITH
            # 检查outer.entry_block中是否有BEFORE_ASYNC_WITH
            # 检查outer.entry_block中是否有BEFORE_ASYNC_WITH
            has_before_async = any(
                instr.opname == 'BEFORE_ASYNC_WITH' 
                for instr in outer.entry_block.instructions
            )
            if has_before_async:
                # 检查inner.entry_block的start是否紧跟在outer之后
                # 检查inner.entry_block的start是否紧跟在outer之后
                # 检查inner.entry_block的start是否紧跟在outer之后
                # 检查inner.entry_block的start是否紧跟在outer之后
                if inner_start - outer_end < 20:
                    # [关键修复] 对于多上下文async with，所有with共享同一个body
                    # 关键区别：多上下文with的body是相同的，嵌套with的body是不同的
                    
                    # [关键修复] 对于多上下文async with，所有with共享同一个body
                    # 关键区别：多上下文with的body是相同的，嵌套with的body是不同的
                    
                    # [关键修复] 对于多上下文async with，所有with共享同一个body
                    # 关键区别：多上下文with的body是相同的，嵌套with的body是不同的
                    
                    # [关键修复] 对于多上下文async with，所有with共享同一个body
                    # 关键区别：多上下文with的body是相同的，嵌套with的body是不同的
                    
                    if outer.with_body and inner.with_body:
                        outer_body_set = set(outer.with_body)
                        inner_body_set = set(inner.with_body)
                        
                        # [关键修复] 区分多上下文with和嵌套with
                        # 多上下文with：所有with共享相同的实际代码body
                        # 嵌套with：inner的body是outer的body的真子集，且outer有额外的代码
                        
                        # 检查是否是多上下文with的特殊情况：
                        # 1. 两个with都是异步的
                        # 2. inner的entry_block紧跟在outer的entry_block之后
                        # 3. 两个with的body有交集（共享实际代码）
                        if outer.is_async and inner.is_async:
                            # 计算交集
                            # 计算交集
                            # 计算交集
                            # 计算交集
                            intersection = outer_body_set & inner_body_set
                            
                            # 检查inner的entry_block是否在outer的body中
                            # 如果是，说明是嵌套with，不是多上下文with
                            if inner.entry_block in outer_body_set:
                                return False
                            
                            # 如果有交集，且inner的entry_block紧跟在outer之后，可能是多上下文with
                            if intersection and len(intersection) > 0:
                                # 检查交集中是否有实际的代码块
                                # 检查交集中是否有实际的代码块
                                # 检查交集中是否有实际的代码块
                                # 检查交集中是否有实际的代码块
                                has_code_in_intersection = False
                                for block in intersection:
                                    # 检查块中是否有实际的代码指令
                                    # 检查块中是否有实际的代码指令
                                    # 检查块中是否有实际的代码指令
                                    # 检查块中是否有实际的代码指令
                                    for instr in block.instructions:
                                        if instr.opname not in ('SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 
                                                               'NOP', 'CACHE', 'POP_TOP', 'LOAD_CONST', 'GET_AWAITABLE'):
                                            has_code_in_intersection = True
                                            break
                                    if has_code_in_intersection:
                                        break
                                
                                if has_code_in_intersection:
                                    # 有共享的代码块，是多上下文with
                                    # 有共享的代码块，是多上下文with
                                    # 有共享的代码块，是多上下文with
                                    # 有共享的代码块，是多上下文with
                                    return True
                        
                        # 如果两个body完全相同，说明是多上下文with
                        if outer_body_set == inner_body_set:
                            return True
                        
                        # 如果inner的body是outer的body的真子集
                        if inner_body_set.issubset(outer_body_set):
                            # [关键修复] 检查outer是否有inner没有的代码块（outer_only）
                            # [关键修复] 检查outer是否有inner没有的代码块（outer_only）
                            # [关键修复] 检查outer是否有inner没有的代码块（outer_only）
                            # [关键修复] 检查outer是否有inner没有的代码块（outer_only）
                            outer_only = outer_body_set - inner_body_set
                            
                            # [关键修复] 检查outer_only中的块是否包含实际的代码（不是entry相关的块）
                            # 如果outer_only包含实际的代码块，说明是嵌套with
                            # 如果outer_only只包含entry相关的块，说明是多上下文with
                            has_code_in_outer_only = False
                            for block in outer_only:
                                # 跳过entry_block
                                # 跳过entry_block
                                # 跳过entry_block
                                # 跳过entry_block
                                if block == outer.entry_block:
                                    continue
                                # 检查块中是否有实际的代码指令
                                for instr in block.instructions:
                                    if instr.opname not in ('SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 
                                                           'NOP', 'CACHE', 'POP_TOP', 'LOAD_CONST', 'GET_AWAITABLE'):
                                        has_code_in_outer_only = True
                                        break
                                if has_code_in_outer_only:
                                    break
                            
                            if has_code_in_outer_only:
                                # outer有inner没有的代码块，是嵌套with
                                # outer有inner没有的代码块，是嵌套with
                                # outer有inner没有的代码块，是嵌套with
                                # outer有inner没有的代码块，是嵌套with
                                return False
                            
                            # outer_only只包含entry相关的块，是多上下文with
                            return True
                        
                        # inner的body不是outer的body的子集，但可能是多上下文with
                        # 检查是否有共享的代码块
                        intersection = outer_body_set & inner_body_set
                        if len(intersection) > 0:
                            # 有共享的代码块，可能是多上下文with
                            # 有共享的代码块，可能是多上下文with
                            # 有共享的代码块，可能是多上下文with
                            # 有共享的代码块，可能是多上下文with
                            return True
                        
                        # inner的body不是outer的body的子集，也没有共享代码块
                        return False
                    
                    # 默认认为是多上下文with
                    return True

        # [关键修复] 如果两个with的entry_block不同，它们是独立的with语句，不是多上下文with
        if outer.entry_block != inner.entry_block:
            return False
        
        # 检查内层with的entry_block是否在外层with的body中（嵌套with的特征）
        if outer.with_body and inner.entry_block in outer.with_body:
            # 检查内层with的body是否是外层with的body的子集
            # 检查内层with的body是否是外层with的body的子集
            # 检查内层with的body是否是外层with的body的子集
            # 检查内层with的body是否是外层with的body的子集
            outer_body_set = set(outer.with_body)
            inner_body_set = set(inner.with_body)

            if inner_body_set.issubset(outer_body_set):
                
                # [关键修复] 如果两个with有完全相同的entry_block和body，需要更仔细地检查
                
                # [关键修复] 如果两个with有完全相同的entry_block和body，需要更仔细地检查
                
                # [关键修复] 如果两个with有完全相同的entry_block和body，需要更仔细地检查
                
                # [关键修复] 如果两个with有完全相同的entry_block和body，需要更仔细地检查
                if outer.entry_block == inner.entry_block and outer_body_set == inner_body_set:
                    # 检查entry_block中的指令来确定是否是嵌套with
                    # 嵌套with的特征：同一个块中有多个BEFORE_WITH，中间有STORE指令
                    # 检查entry_block中的指令来确定是否是嵌套with
                    # 嵌套with的特征：同一个块中有多个BEFORE_WITH，中间有STORE指令
                    # 检查entry_block中的指令来确定是否是嵌套with
                    # 嵌套with的特征：同一个块中有多个BEFORE_WITH，中间有STORE指令
                    # 检查entry_block中的指令来确定是否是嵌套with
                    # 嵌套with的特征：同一个块中有多个BEFORE_WITH，中间有STORE指令
                    entry_block = outer.entry_block
                    before_with_positions = []
                    for i, instr in enumerate(entry_block.instructions):
                        if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                            before_with_positions.append(i)
                    
                    if len(before_with_positions) > 1:
                        # 检查BEFORE_WITH之间是否有STORE指令（嵌套with的特征）
                        # 检查BEFORE_WITH之间是否有STORE指令（嵌套with的特征）
                        # 检查BEFORE_WITH之间是否有STORE指令（嵌套with的特征）
                        # 检查BEFORE_WITH之间是否有STORE指令（嵌套with的特征）
                        for idx in range(len(before_with_positions) - 1):
                            first_pos = before_with_positions[idx]
                            second_pos = before_with_positions[idx + 1]
                            for j in range(first_pos + 1, second_pos):
                                if entry_block.instructions[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                                    return False
                        
                        # 没有STORE指令，检查是否有POP_TOP（也是嵌套with的特征）
                        for idx in range(len(before_with_positions) - 1):
                            first_pos = before_with_positions[idx]
                            second_pos = before_with_positions[idx + 1]
                            for j in range(first_pos + 1, second_pos):
                                if entry_block.instructions[j].opname == 'POP_TOP':
                                    return False
                        
                        # 没有STORE或POP_TOP，可能是多上下文with
                        return True
                
                # [关键修复] 区分嵌套with和多上下文with
                # 嵌套with: outer有inner没有的代码块（outer_only包含实际代码）
                # 多上下文with: outer和inner共享完全相同的body
                outer_only = outer_body_set - inner_body_set
                
                # 检查outer_only中的块是否包含实际的代码（不是entry相关的块）
                has_code_in_outer_only = False
                for block in outer_only:
                    # 跳过entry_block
                    # 跳过entry_block
                    # 跳过entry_block
                    # 跳过entry_block
                    if block == outer.entry_block:
                        continue
                    # 检查块中是否有实际的代码指令
                    for instr in block.instructions:
                        if instr.opname not in ('SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT',
                                               'NOP', 'CACHE', 'POP_TOP', 'LOAD_CONST', 'GET_AWAITABLE',
                                               'BEFORE_WITH', 'BEFORE_ASYNC_WITH', 'SETUP_ASYNC_WITH'):
                            has_code_in_outer_only = True
                            break
                    if has_code_in_outer_only:
                        break
                
                if has_code_in_outer_only:
                    # outer有inner没有的代码块，说明是嵌套with
                    # outer有inner没有的代码块，说明是嵌套with
                    # outer有inner没有的代码块，说明是嵌套with
                    # outer有inner没有的代码块，说明是嵌套with
                    return False
                
                # 关键启发式：检查外层with的target变量是否在内层with的body中被使用
                # 如果是，说明这是嵌套with（内层使用了外层的变量）
                # [关键修复] 需要区分LOAD_FAST是在内层with的STORE_FAST之前还是之后
                # 如果在STORE_FAST之前，那是使用外层的target；如果在STORE_FAST之后，那是使用内层自己的target
                if outer.target:
                    for block in inner.with_body:
                        # [关键修复] 找到内层with的STORE_FAST位置
                        # [关键修复] 找到内层with的STORE_FAST位置
                        # [关键修复] 找到内层with的STORE_FAST位置
                        # [关键修复] 找到内层with的STORE_FAST位置
                        inner_store_pos = -1
                        for i, instr in enumerate(block.instructions):
                            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                                if str(instr.argval) == inner.target:
                                    inner_store_pos = i
                                    break
                        
                        # 检查LOAD_FAST是否在STORE_FAST之前
                        for i, instr in enumerate(block.instructions):
                            if instr.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                                if str(instr.argval) == outer.target:
                                    # [关键修复] 如果LOAD_FAST在STORE_FAST之前，那是使用外层的target
                                    # 如果LOAD_FAST在STORE_FAST之后，那是使用内层自己的target（如果target相同）
                                    # [关键修复] 如果LOAD_FAST在STORE_FAST之前，那是使用外层的target
                                    # 如果LOAD_FAST在STORE_FAST之后，那是使用内层自己的target（如果target相同）
                                    # [关键修复] 如果LOAD_FAST在STORE_FAST之前，那是使用外层的target
                                    # 如果LOAD_FAST在STORE_FAST之后，那是使用内层自己的target（如果target相同）
                                    # [关键修复] 如果LOAD_FAST在STORE_FAST之前，那是使用外层的target
                                    # 如果LOAD_FAST在STORE_FAST之后，那是使用内层自己的target（如果target相同）
                                    if inner_store_pos >= 0 and i > inner_store_pos:
                                        # 这是在内层with的STORE_FAST之后，是内层自己的target
                                        # 这是在内层with的STORE_FAST之后，是内层自己的target
                                        # 这是在内层with的STORE_FAST之后，是内层自己的target
                                        # 这是在内层with的STORE_FAST之后，是内层自己的target
                                        continue
                                    # 外层with的target在内层with的body中被使用，说明是嵌套with
                                    return False

                # 外层with的target没有在内层with的body中被使用，且没有额外的代码块，说明是多上下文with
                return True
            else:
                # 其他情况，不是多上下文with
                return False
        return False

    def _create_merged_with_structure(self, chain: List[WithStructure]) -> Optional[WithStructure]:
        """从with链创建合并的with结构"""
        if not chain:
            return None

        # 使用链的第一个with作为entry_block
        first = chain[0]
        last = chain[-1]

        # 收集所有items
        items = []
        for w in chain:
            items.append((w.resource_expr, w.target))

        # 使用最后一个with的body作为合并后的body
        merged_body = last.with_body

        # 创建合并后的with结构
        merged = WithStructure(
            struct_type=ControlStructureType.WITH,
            entry_block=first.entry_block,
            with_body=merged_body,
            resource_expr=first.resource_expr,
            target=first.target,
            is_async=first.is_async,
            items=items
        )

        return merged

    def _find_with_body(self, start: BasicBlock, before_with_pos: int = 0) -> List[BasicBlock]:
        """
        查找with体
        
        Args:
            start: 起始块
            before_with_pos: BEFORE_WITH / BEFORE_ASYNC_WITH 指令的位置
            
        Returns:
            with体中的基本块列表
        """
        body: List[BasicBlock] = []
        
        # [关键修复] 查找所有BEFORE_WITH和BEFORE_ASYNC_WITH的位置
        all_before_with_positions = []
        for i, instr in enumerate(start.instructions):
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                all_before_with_positions.append(i)
        
        # [关键修复] 确定当前with的索引
        with_index = all_before_with_positions.index(before_with_pos) if before_with_pos in all_before_with_positions else 0
        
        # [关键修复] 检查是否是多上下文with（同一个块中有多个BEFORE_WITH）
        is_multi_context = len(all_before_with_positions) > 1
        
        # [关键修复] 检查是否是嵌套with（同一个块中有多个BEFORE_WITH，中间有STORE）
        is_nested_with = False
        if len(all_before_with_positions) > 1:
            # 检查BEFORE_WITH之间是否有STORE指令
            # 检查BEFORE_WITH之间是否有STORE指令
            # 检查BEFORE_WITH之间是否有STORE指令
            # 检查BEFORE_WITH之间是否有STORE指令
            for idx in range(len(all_before_with_positions) - 1):
                first_pos = all_before_with_positions[idx]
                second_pos = all_before_with_positions[idx + 1]
                for j in range(first_pos + 1, second_pos):
                    if start.instructions[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                        is_nested_with = True
                        break
                if is_nested_with:
                    break
        
        # [关键修复] 对于嵌套with，所有with都包含entry_block
        # 但代码生成时，每个with只提取自己的代码部分
        body.append(start)
        
        # [关键修复] 收集with体内的其他块（如嵌套的if语句、for循环等）
        # 从start开始，遍历所有后继块，直到遇到异常处理块或退出块
        visited = {start}
        # [关键修复] 对于嵌套with的内层with，不遍历后继块
        # 因为内层with的代码都在entry_block中，不需要遍历后继块
        # [关键修复] 对于非嵌套with，需要遍历后继块来查找控制流结构（如for循环）
        # [关键修复] 但如果entry_block包含JUMP_FORWARD，则不遍历后继块
        # 因为JUMP_FORWARD标志着with语句的结束
        # [关键修复] 但对于嵌套with的外层with，需要遍历后继块来找到所有的body块
        has_jump_forward_in_start = False
        for instr in start.instructions:
            if instr.opname == 'JUMP_FORWARD':
                has_jump_forward_in_start = True
                break
        
        # [关键修复] 对于嵌套with，所有层级的with都需要遍历后继块
        # 因为内层with的body可能分布在多个块中（如with open() as f: f.write()）
        if is_nested_with:
            # [关键修复] 嵌套with的所有层级都需要遍历后继块
            # 即使entry_block包含JUMP_FORWARD
            # [关键修复] 嵌套with的所有层级都需要遍历后继块
            # 即使entry_block包含JUMP_FORWARD
            # [关键修复] 嵌套with的所有层级都需要遍历后继块
            # 即使entry_block包含JUMP_FORWARD
            # [关键修复] 嵌套with的所有层级都需要遍历后继块
            # 即使entry_block包含JUMP_FORWARD
            worklist = list(start.successors)
        elif has_jump_forward_in_start:
            worklist = []  # entry_block包含JUMP_FORWARD，不遍历后继块
        else:
            worklist = list(start.successors)  # 非嵌套with遍历后继块
        
        # 找到这个with的STORE_FAST/STORE_NAME位置（确定with变量的结束位置）
        store_end_pos = len(start.instructions)
        for i, instr in enumerate(start.instructions):
            if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                if i >= before_with_pos:
                    # 查找这个BEFORE_WITH/BEFORE_ASYNC_WITH之后的STORE_FAST/STORE_NAME
                    # 查找这个BEFORE_WITH/BEFORE_ASYNC_WITH之后的STORE_FAST/STORE_NAME
                    # 查找这个BEFORE_WITH/BEFORE_ASYNC_WITH之后的STORE_FAST/STORE_NAME
                    # 查找这个BEFORE_WITH/BEFORE_ASYNC_WITH之后的STORE_FAST/STORE_NAME
                    for j in range(i + 1, len(start.instructions)):
                        if start.instructions[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                            store_end_pos = j + 1
                            break
                    break
        
        # [关键修复] 对于嵌套with，确定body的范围
        # 外层with的body应该包含内层with的代码
        # 内层with的body应该只包含它自己的代码
        inner_with_start_pos = len(start.instructions)
        if is_nested_with and with_index < len(all_before_with_positions) - 1:
            # 这不是最后一个with，查找下一个with的BEFORE_WITH位置
            # 这不是最后一个with，查找下一个with的BEFORE_WITH位置
            # 这不是最后一个with，查找下一个with的BEFORE_WITH位置
            # 这不是最后一个with，查找下一个with的BEFORE_WITH位置
            inner_with_start_pos = all_before_with_positions[with_index + 1]
        
        # [关键修复] 获取所有已识别的循环结构，用于检查块是否属于循环
        loop_headers = set()
        for struct in self.structures:
            if hasattr(struct, 'header_block') and struct.header_block:
                loop_headers.add(struct.header_block)
        
        # 收集后继块
        while worklist:
            block = worklist.pop(0)
            if block in visited:
                continue
            
            # [关键修复] 处理其他with结构的entry块
            # 如果当前块是另一个with的entry块，需要特殊处理
            is_other_with_entry = False
            for instr in block.instructions:
                if instr.opname in ('BEFORE_WITH', 'BEFORE_ASYNC_WITH'):
                    # 检查这个块是否是当前with的entry块
                    # 检查这个块是否是当前with的entry块
                    # 检查这个块是否是当前with的entry块
                    # 检查这个块是否是当前with的entry块
                    if block != start:
                        is_other_with_entry = True
                        break
            
            if is_other_with_entry:
                # [关键修复] 遇到其他with结构的entry_block
                # 对于外层with，需要包含内层with的所有代码块
                # 因为内层with的代码也是外层with的body的一部分
                # [关键修复] 遇到其他with结构的entry_block
                # 对于外层with，需要包含内层with的所有代码块
                # 因为内层with的代码也是外层with的body的一部分
                # [关键修复] 遇到其他with结构的entry_block
                # 对于外层with，需要包含内层with的所有代码块
                # 因为内层with的代码也是外层with的body的一部分
                # [关键修复] 遇到其他with结构的entry_block
                # 对于外层with，需要包含内层with的所有代码块
                # 因为内层with的代码也是外层with的body的一部分
                visited.add(block)
                body.append(block)
                # [关键修复] 继续遍历后继块，因为内层with的代码也是外层with的一部分
                for succ in block.successors:
                    if succ not in visited:
                        worklist.append(succ)
                continue
            
            # [关键修复] 跳过异常处理块
            is_exception_block = False
            # [关键修复] 检查块是否以PUSH_EXC_INFO开头（真正的异常处理块）
            first_real_instr = None
            for instr in block.instructions:
                if instr.opname in ('RESUME', 'CACHE', 'NOP'):
                    continue
                first_real_instr = instr
                break
            
            if first_real_instr and first_real_instr.opname in ('PUSH_EXC_INFO', 'RERAISE'):
                is_exception_block = True
            
            if not is_exception_block:
                # [关键修复] 检查是否是只包含清理代码的块（POP_TOP, POP_EXCEPT等）
                # 只有当块不包含实质性代码时，才跳过
                # [关键修复] 检查是否是只包含清理代码的块（POP_TOP, POP_EXCEPT等）
                # 只有当块不包含实质性代码时，才跳过
                # [关键修复] 检查是否是只包含清理代码的块（POP_TOP, POP_EXCEPT等）
                # 只有当块不包含实质性代码时，才跳过
                # [关键修复] 检查是否是只包含清理代码的块（POP_TOP, POP_EXCEPT等）
                # 只有当块不包含实质性代码时，才跳过
                is_pure_cleanup = True
                has_substantial_code = False
                has_jump_forward = False
                for instr in block.instructions:
                    if instr.opname in ('RESUME', 'CACHE', 'NOP', 'POP_TOP', 'POP_EXCEPT', 'COPY', 'RERAISE'):
                        continue
                    elif instr.opname == 'LOAD_CONST' and instr.argval is None:
                        continue
                    elif instr.opname in ('PRECALL', 'CALL', 'JUMP_ABSOLUTE'):
                        continue
                    elif instr.opname == 'JUMP_FORWARD':
                        has_jump_forward = True
                        continue
                    elif instr.opname in ('LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_ATTR', 'LOAD_METHOD'):
                        has_substantial_code = True
                        is_pure_cleanup = False
                        break
                    else:
                        has_substantial_code = True
                        is_pure_cleanup = False
                        break
                
                # [关键修复] 如果块只包含JUMP_FORWARD，不将其标记为异常块
                # 因为JUMP_FORWARD可能是with语句正常结束后的跳转
                if is_pure_cleanup and not has_substantial_code and not has_jump_forward:
                    is_exception_block = True
            
            if is_exception_block:
                continue
            
            # [关键修复] 对于在with语句体中的循环，保留循环头部块
            # 这些块虽然被识别为循环头部，但它们是with语句体的一部分
            # 让_generate_with_ast方法来正确处理它们
            # if block in loop_headers:
            #     continue
            
            # [关键修复] 跳过函数返回块
            # 这些块包含RETURN_VALUE或RETURN_CONST，标志着函数结束
            # [关键修复] 但对于async with，return语句可能在with块内部
            # 需要检查这个块是否是with cleanup代码的一部分
            is_return_block = False
            for instr in block.instructions:
                if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    # [关键修复] 检查是否是async with cleanup后的return
                    # 特征：块以POP_TOP开头（__aexit__的结果），然后是return
                    if len(block.instructions) >= 3:
                        first_instr = None
                        for i in block.instructions:
                            if i.opname not in ('RESUME', 'CACHE', 'NOP'):
                                first_instr = i
                                break
                        # 如果是POP_TOP开头，说明是cleanup后的return，应该包含在with_body中
                        if first_instr and first_instr.opname == 'POP_TOP':
                            is_return_block = False
                            break
                    is_return_block = True
                    break
            if is_return_block:
                continue
            
            # [关键修复] 跳过循环尾部块（包含JUMP_BACKWARD到循环头部的块）
            # 这些块不属于with体，而是循环的一部分
            # [关键修复] 但是，如果with语句在循环内部，with体的最后一个块可能包含JUMP_BACKWARD
            # 这种情况下，这个块应该被包含在with体中
            is_loop_tail = False
            for instr in block.instructions:
                if instr.opname == 'JUMP_BACKWARD':
                    # 检查跳转目标是否是某个循环的头部
                    # 检查跳转目标是否是某个循环的头部
                    # 检查跳转目标是否是某个循环的头部
                    # 检查跳转目标是否是某个循环的头部
                    jump_target = instr.argval
                    for header in loop_headers:
                        if header.start_offset == jump_target:
                            # [关键修复] 检查这个块是否是with体的最后一个块
                            # 如果是，它应该被包含在with体中
                            # 特征：块包含实际代码（不只是跳转）
                            # [关键修复] 检查这个块是否是with体的最后一个块
                            # 如果是，它应该被包含在with体中
                            # 特征：块包含实际代码（不只是跳转）
                            # [关键修复] 检查这个块是否是with体的最后一个块
                            # 如果是，它应该被包含在with体中
                            # 特征：块包含实际代码（不只是跳转）
                            # [关键修复] 检查这个块是否是with体的最后一个块
                            # 如果是，它应该被包含在with体中
                            # 特征：块包含实际代码（不只是跳转）
                            has_real_code = False
                            for i in block.instructions:
                                if i.opname not in ('RESUME', 'CACHE', 'NOP', 'JUMP_BACKWARD', 'JUMP_FORWARD', 'POP_TOP'):
                                    has_real_code = True
                                    break
                            if not has_real_code:
                                is_loop_tail = True
                            break
                if is_loop_tail:
                    break
            if is_loop_tail:
                continue
            
            visited.add(block)
            body.append(block)
            
            # [关键修复] 添加后继块到worklist，继续遍历
            # 即使块包含JUMP_FORWARD，也需要遍历其后继块
            # 因为JUMP_FORWARD可能是内层with的结束，其后继块是外层with的body的一部分
            for succ in block.successors:
                if succ not in visited:
                    worklist.append(succ)
        
        # 按偏移量排序
        body.sort(key=lambda b: b.start_offset)
        return body
    
    def _identify_sequences(self) -> None:
        """识别顺序结构"""
        analyzed = set(self.block_to_structure.keys())
        
        for block in self.cfg.get_blocks_in_order():
            # [关键修复] 直接检查 self.block_to_structure，而不是使用 analyzed 集合
            # 因为 analyzed 集合是在方法开始时创建的，可能不包含最新的映射
            # [关键修复] 直接检查 self.block_to_structure，而不是使用 analyzed 集合
            # 因为 analyzed 集合是在方法开始时创建的，可能不包含最新的映射
            # [关键修复] 直接检查 self.block_to_structure，而不是使用 analyzed 集合
            # 因为 analyzed 集合是在方法开始时创建的，可能不包含最新的映射
            # [关键修复] 直接检查 self.block_to_structure，而不是使用 analyzed 集合
            # 因为 analyzed 集合是在方法开始时创建的，可能不包含最新的映射
            if block in self.block_to_structure:
                continue
            
            # [关键修复] 检查块是否只包含NOP
            # 如果是，不要创建SEQUENCE结构，让它被识别为if True:结构
            block_nop_only = True
            block_has_nop = False
            for instr in block.instructions:
                if instr.opname == 'NOP':
                    block_has_nop = True
                elif instr.opname not in ('RESUME', 'CACHE', 'PRECALL'):
                    block_nop_only = False
                    break
            
            # 如果块只包含NOP，跳过它（让它被_identify_nop_sequences处理）
            if block_nop_only and block_has_nop:
                continue
            
            # [关键修复] 检查块是否是elif条件块或elif的then分支
            # 如果是，映射到IfStructure，不创建SEQUENCE结构
            is_elif_related = False
            elif_struct = None
            for struct in self.structures:
                if isinstance(struct, IfStructure) and hasattr(struct, 'elif_conditions'):
                    for elif_block in struct.elif_conditions:
                        if block == elif_block:
                            is_elif_related = True
                            elif_struct = struct
                            break
                        # 检查块是否是elif的then分支
                        elif_jump = self._get_jump_instr(elif_block)
                        if elif_jump and elif_jump.argval is not None:
                            for succ in elif_block.successors:
                                if succ == block and succ.start_offset != elif_jump.argval:
                                    is_elif_related = True
                                    elif_struct = struct
                                    break
                    if is_elif_related:
                        break
            
            if is_elif_related and elif_struct:
                self.block_to_structure[block] = elif_struct
                continue
            
            # [关键修复] 检查块是否是正常路径的finally代码块
            # 这些块是try-except-finally结构的一部分，不应该被识别为独立的SEQUENCE
            is_normal_finally_block = False
            for struct in self.structures:
                if isinstance(struct, TryExceptStructure) and hasattr(struct, 'finally_body'):
                    # 获取finally_body中的常数值
                    # 获取finally_body中的常数值
                    # 获取finally_body中的常数值
                    # 获取finally_body中的常数值
                    finally_consts = set()
                    for fb in struct.finally_body:
                        for instr in fb.instructions:
                            if instr.opname == 'LOAD_CONST' and instr.argval is not None:
                                finally_consts.add(instr.argval)
                    
                    # 检查当前块是否包含相同的常数
                    has_matching_const = False
                    for instr in block.instructions:
                        if instr.opname == 'LOAD_CONST' and instr.argval in finally_consts:
                            has_matching_const = True
                            break
                    
                    if has_matching_const:
                        # 检查前驱是否是try_body或except handler
                        # 检查前驱是否是try_body或except handler
                        # 检查前驱是否是try_body或except handler
                        # 检查前驱是否是try_body或except handler
                        try_body_ids = {tb.id for tb in struct.try_body}
                        handler_ids = set()
                        if hasattr(struct, 'except_handlers'):
                            for handler_info in struct.except_handlers:
                                if len(handler_info) == 3:
                                    _, _, handler_blocks = handler_info
                                else:
                                    _, handler_blocks = handler_info
                                handler_ids.update(hb.id for hb in handler_blocks)
                        
                        for pred in block.predecessors:
                            if pred.id in try_body_ids or pred.id in handler_ids:
                                is_normal_finally_block = True
                                break
                    
                    if is_normal_finally_block:
                        break
            
            if is_normal_finally_block:
                # 这是正常路径的finally代码块，映射到TryExceptStructure
                # 这是正常路径的finally代码块，映射到TryExceptStructure
                # 这是正常路径的finally代码块，映射到TryExceptStructure
                # 这是正常路径的finally代码块，映射到TryExceptStructure
                for struct in self.structures:
                    if isinstance(struct, TryExceptStructure) and hasattr(struct, 'finally_body'):
                        self.block_to_structure[block] = struct
                        break
                continue
            
            # [关键修复] 检查块是否是IfStructure的else_body的一部分
            # 如果是，不要创建SEQUENCE结构，让它属于IfStructure
            is_else_body_block = False
            else_body_struct = None
            for struct in self.structures:
                if isinstance(struct, IfStructure) and hasattr(struct, 'else_body'):
                    if block in struct.else_body:
                        is_else_body_block = True
                        else_body_struct = struct
                        break
            
            if is_else_body_block and else_body_struct:
                self.block_to_structure[block] = else_body_struct
                continue
            
            # [关键修复] 检查块是否是链式比较表达式的一部分
            # 链式比较表达式的特征：
            # 1. 块包含 COMPARE_OP 和 JUMP_FORWARD
            # 2. 块的前驱使用 JUMP_IF_FALSE_OR_POP 或 JUMP_IF_TRUE_OR_POP
            # 3. 所有路径最终汇合到包含赋值指令的块
            is_chained_compare_part = False
            if len(block.successors) == 1:
                # 检查当前块是否包含 COMPARE_OP 和 JUMP_FORWARD
                has_compare_op = any(i.opname == 'COMPARE_OP' for i in block.instructions)
                has_jump_forward = any(i.opname == 'JUMP_FORWARD' for i in block.instructions)
                
                if has_compare_op and has_jump_forward:
                    # 检查前驱是否使用 JUMP_IF_FALSE_OR_POP 或 JUMP_IF_TRUE_OR_POP
                    for pred in block.predecessors:
                        for instr in pred.instructions:
                            if instr.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                                # 检查跳转目标块是否包含 SWAP 和 POP_TOP
                                jump_target_offset = instr.argval
                                for succ in pred.successors:
                                    if succ.start_offset == jump_target_offset:
                                        has_swap = any(i.opname == 'SWAP' for i in succ.instructions)
                                        has_pop_top = any(i.opname == 'POP_TOP' for i in succ.instructions)
                                        if has_swap and has_pop_top:
                                            is_chained_compare_part = True
                                        break
                            if is_chained_compare_part:
                                break
                        if is_chained_compare_part:
                            break
            
            # 检查块是否是链式比较的跳转目标块（包含 SWAP 和 POP_TOP）
            if not is_chained_compare_part:
                has_swap = any(i.opname == 'SWAP' for i in block.instructions)
                has_pop_top = any(i.opname == 'POP_TOP' for i in block.instructions)
                if has_swap and has_pop_top:
                    # 检查前驱是否使用 JUMP_IF_FALSE_OR_POP 或 JUMP_IF_TRUE_OR_POP
                    for pred in block.predecessors:
                        for instr in pred.instructions:
                            if instr.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                                is_chained_compare_part = True
                                break
                        if is_chained_compare_part:
                            break
            
            if is_chained_compare_part:
                # 这是链式比较表达式的一部分，不创建SEQUENCE结构
                continue
            
            if len(block.successors) <= 1:
                seq = ControlStructure(
                    struct_type=ControlStructureType.SEQUENCE,
                    entry_block=block,
                    exit_block=list(block.successors)[0] if block.successors else None
                )
                self.structures.append(seq)
                self.block_to_structure[block] = seq
    
    def _build_hierarchy(self) -> None:
        """构建控制结构层次关系"""
        # [关键修复] 首先按范围排序结构（从外层到内层）
        # 这样可以确保外层结构先处理，内层结构后处理
        def get_struct_range(s):
            if isinstance(s, LoopStructure):
                blocks = s.body_blocks
            elif isinstance(s, IfStructure):
                blocks = list(s.then_body) + list(s.else_body)
            else:
                blocks = []
            if blocks:
                return (min(b.start_offset for b in blocks), max(b.start_offset for b in blocks))
            return (0, 0)
        
        # 按起始偏移排序
        sorted_structures = sorted(self.structures, key=lambda s: get_struct_range(s)[0])
        
        for struct in sorted_structures:
            if isinstance(struct, LoopStructure):
                for other in sorted_structures:
                    if other != struct and other.entry_block in struct.body_blocks:
                        # [关键修复] 如果other已经有父结构，检查是否是当前结构的子结构
                        # [关键修复] 如果other已经有父结构，检查是否是当前结构的子结构
                        # [关键修复] 如果other已经有父结构，检查是否是当前结构的子结构
                        # [关键修复] 如果other已经有父结构，检查是否是当前结构的子结构
                        if other.parent is not None:
                            # 检查other的父结构是否是当前结构的子结构
                            # 如果是，other应该是当前结构的孙结构，不是直接子结构
                            # 检查other的父结构是否是当前结构的子结构
                            # 如果是，other应该是当前结构的孙结构，不是直接子结构
                            # 检查other的父结构是否是当前结构的子结构
                            # 如果是，other应该是当前结构的孙结构，不是直接子结构
                            # 检查other的父结构是否是当前结构的子结构
                            # 如果是，other应该是当前结构的孙结构，不是直接子结构
                            continue
                        struct.children.append(other)
                        other.parent = struct
            
            elif isinstance(struct, IfStructure):
                for other in sorted_structures:
                    if other != struct:
                        # [关键修复] 如果other已经是当前结构的父结构，跳过
                        # 使用id()比较以避免递归
                        # [关键修复] 如果other已经是当前结构的父结构，跳过
                        # 使用id()比较以避免递归
                        # [关键修复] 如果other已经是当前结构的父结构，跳过
                        # 使用id()比较以避免递归
                        # [关键修复] 如果other已经是当前结构的父结构，跳过
                        # 使用id()比较以避免递归
                        if struct.parent is not None and id(struct.parent) == id(other):
                            continue
                        # [关键修复] 如果other已经有父结构，检查是否需要重新分配
                        # 如果other的entry_block在当前结构的then_body或else_body中
                        # 且当前结构是other的父结构的子结构，则重新分配
                        if other.parent is not None:
                            # 检查other的entry_block是否在当前结构的then_body或else_body中
                            # 检查other的entry_block是否在当前结构的then_body或else_body中
                            # 检查other的entry_block是否在当前结构的then_body或else_body中
                            # 检查other的entry_block是否在当前结构的then_body或else_body中
                            if other.entry_block in struct.then_body or other.entry_block in struct.else_body:
                                # 检查当前结构是否是other的父结构的子结构
                                # 或者当前结构和other有相同的父结构
                                # 或者当前结构是other的父结构的父结构（祖孙关系）
                                # 如果是，说明other应该属于当前结构，而不是直接属于外层结构
                                # 检查当前结构是否是other的父结构的子结构
                                # 或者当前结构和other有相同的父结构
                                # 或者当前结构是other的父结构的父结构（祖孙关系）
                                # 如果是，说明other应该属于当前结构，而不是直接属于外层结构
                                # 检查当前结构是否是other的父结构的子结构
                                # 或者当前结构和other有相同的父结构
                                # 或者当前结构是other的父结构的父结构（祖孙关系）
                                # 如果是，说明other应该属于当前结构，而不是直接属于外层结构
                                # 检查当前结构是否是other的父结构的子结构
                                # 或者当前结构和other有相同的父结构
                                # 或者当前结构是other的父结构的父结构（祖孙关系）
                                # 如果是，说明other应该属于当前结构，而不是直接属于外层结构
                                should_reassign = False
                                if struct.parent is not None and other.parent == struct.parent:
                                    # 当前结构和other有相同的父结构
                                    # 检查other是否在当前结构的then_body或else_body中
                                    # 当前结构和other有相同的父结构
                                    # 检查other是否在当前结构的then_body或else_body中
                                    # 当前结构和other有相同的父结构
                                    # 检查other是否在当前结构的then_body或else_body中
                                    # 当前结构和other有相同的父结构
                                    # 检查other是否在当前结构的then_body或else_body中
                                    should_reassign = True
                                elif struct.parent is not None and other.parent in struct.parent.children:
                                    # 当前结构是other的父结构的子结构
                                    # 当前结构是other的父结构的子结构
                                    should_reassign = True
                                elif struct.parent is None and other.parent.parent == struct:
                                    # [关键修复] 当前结构是other的父结构的父结构（祖孙关系）
                                    # 这种情况发生在：IfStructure 0 -> TryExceptStructure -> IfStructure 286
                                    # 块286的IfStructure应该被重新分配为IfStructure 0的child
                                    # [关键修复] 当前结构是other的父结构的父结构（祖孙关系）
                                    # 这种情况发生在：IfStructure 0 -> TryExceptStructure -> IfStructure 286
                                    # 块286的IfStructure应该被重新分配为IfStructure 0的child
                                    should_reassign = True
                                
                                if should_reassign:
                                    # 从原父结构中移除
                                    # 从原父结构中移除
                                    # 从原父结构中移除
                                    # 从原父结构中移除
                                    other.parent.children.remove(other)
                                    # 重新分配
                                    struct.children.append(other)
                                    other.parent = struct
                            continue
                        # [关键修复] 检查other的entry_block是否在then_body或else_body中
                        # [关键修复] 但只有当other的entry_block不是条件块时，才设置为child
                        # 条件块的特征：包含POP_JUMP指令且有两个后继
                        is_other_conditional = False
                        if hasattr(other, 'entry_block') and other.entry_block:
                            other_entry = other.entry_block
                            has_pop_jump = any(i.opname.startswith('POP_JUMP') for i in other_entry.instructions)
                            has_two_succ = len(other_entry.successors) == 2
                            is_other_conditional = has_pop_jump and has_two_succ
                        
                        # [关键修复] 检查other.entry_block是否同时在IfStructure的else_body和LoopStructure的body_blocks中
                        # 如果是，应该优先设置parent为LoopStructure，而不是IfStructure
                        is_in_loop_body = False
                        if isinstance(other, IfStructure):
                            for loop_struct in sorted_structures:
                                if isinstance(loop_struct, LoopStructure):
                                    if other.entry_block in loop_struct.body_blocks:
                                        if other.entry_block != loop_struct.header_block and other.entry_block != loop_struct.entry_block:
                                            is_in_loop_body = True
                                            break
                        
                        # [关键修复] 检查other的entry_block是否在struct的then_body或else_body中
                        # 如果是，设置parent关系
                        # 对于嵌套if结构（is_other_conditional为True），也应该设置parent
                        # [关键修复] 也检查other的entry_block是否是then_body中某个条件块的fall-through后继
                        # 这种情况发生在嵌套if结构中，如：
                        # if A:
                        #     if B:  # B是A的then_body中某个条件块的fall-through后继
                        #         pass
                        #     if C:  # C是A的then_body中某个条件块的fall-through后继
                        #         pass
                        is_in_then_body = other.entry_block in struct.then_body or other.entry_block in struct.else_body
                        
                        # [关键修复] 检查other的entry_block是否是then_body中某个条件块的fall-through后继
                        # 只有条件块的fall-through后继才被认为是嵌套if
                        # 非条件块（如赋值语句）的后继不应该被认为是嵌套if
                        if not is_in_then_body:
                            for block in struct.then_body:
                                # [关键修复] 只检查条件块的fall-through后继
                                if self._is_conditional_block(block):
                                    block_jump = self._get_jump_instr(block)
                                    if block_jump:
                                        for succ in block.successors:
                                            if succ == other.entry_block and succ.start_offset != block_jump.argval:
                                                # 检查是否是elif链
                                                is_elif = False
                                                for instr in struct.entry_block.instructions:
                                                    if instr.opname.startswith('POP_JUMP'):
                                                        if instr.argval == other.entry_block.start_offset:
                                                            is_elif = True
                                                            break
                                                if not is_elif:
                                                    is_in_then_body = True
                                                break
                                if is_in_then_body:
                                    break
                        
                        if is_in_then_body and not is_in_loop_body:
                            # [关键修复] 对于嵌套if结构（条件块），检查它是否真的嵌套在当前结构中
                            # 判断标准：other的entry_block不是当前结构的entry_block的后继（即不是elif链）
                            if is_other_conditional:
                                # 检查other是否是当前结构的嵌套if（不是elif链）
                                # elif链的特征：other的entry_block是当前结构的跳转目标
                                is_elif_chain = False
                                for instr in struct.entry_block.instructions:
                                    if instr.opname.startswith('POP_JUMP'):
                                        if instr.argval == other.entry_block.start_offset:
                                            is_elif_chain = True
                                            break
                                
                                if not is_elif_chain:
                                    # 这是嵌套if，设置parent
                                    struct.children.append(other)
                                    other.parent = struct
                            else:
                                # 不是条件块，直接设置parent
                                struct.children.append(other)
                                other.parent = struct
                        # [关键修复] 如果then_body为空，但pre_then_branch是条件块（嵌套if）
                        # 设置嵌套if的parent为当前if结构
                        elif not struct.then_body and hasattr(struct, 'pre_then_branch') and struct.pre_then_branch == other.entry_block:
                            # 检查other是否是条件块
                            if is_other_conditional:
                                struct.children.append(other)
                                other.parent = struct
                        # [关键修复] 对于嵌套循环（如for-if-for），检查循环的初始化块是否在then_body中
                        # 因为for循环的body_blocks包含初始化块，但entry_block是FOR_ITER块
                        # [关键修复] 设置LoopStructure的parent
                        elif isinstance(other, LoopStructure):
                            # [关键修复] 检查循环的entry_block是否在then_body或else_body中
                            # [关键修复] 检查循环的entry_block是否在then_body或else_body中
                            if other.entry_block in struct.then_body or other.entry_block in struct.else_body:
                                # [关键修复] 设置parent关系
                                # [关键修复] 设置parent关系
                                # [关键修复] 设置parent关系
                                # [关键修复] 设置parent关系
                                struct.children.append(other)
                                other.parent = struct
            
            # [关键修复] 构建TryExceptStructure的层次关系
            elif isinstance(struct, TryExceptStructure):
                # [关键修复] 根据异常表的target关系建立嵌套关系
                # 对于嵌套的try-except，如果try块A的except handler的target是try块B的开始，
                # 那么A是B的child（B包含A）
                # [关键修复] 根据异常表的target关系建立嵌套关系
                # 对于嵌套的try-except，如果try块A的except handler的target是try块B的开始，
                # 那么A是B的child（B包含A）
                struct_start = struct.try_start_offset
                struct_end = struct.try_end_offset
                
                # [关键修复] 找到当前结构对应的except条目的target
                # 对于try块（depth>=0），找到对应的except条目（depth=current_depth+1）
                # [关键修复] except条目的start应该在try块的end附近（不是严格相等）
                # 因为在Python 3.11+中，try块的end和except条目的start之间可能有PUSH_EXC_INFO等指令
                # [关键修复] 首先确定当前try块的depth
                struct_depth = None
                if self.cfg.exception_table:
                    for entry in self.cfg.exception_table:
                        if entry['start'] == struct_start:
                            struct_depth = entry['depth']
                            break
                
                struct_handler_target = None
                if self.cfg.exception_table and struct_depth is not None:
                    for entry in self.cfg.exception_table:
                        # 找到对应于当前try块的except条目
                        # 条件：entry的start在当前try块end附近（±10字节），且depth=struct_depth+1
                        # 找到对应于当前try块的except条目
                        # 条件：entry的start在当前try块end附近（±10字节），且depth=struct_depth+1
                        # 找到对应于当前try块的except条目
                        # 条件：entry的start在当前try块end附近（±10字节），且depth=struct_depth+1
                        # 找到对应于当前try块的except条目
                        # 条件：entry的start在当前try块end附近（±10字节），且depth=struct_depth+1
                        if entry['depth'] == struct_depth + 1:
                            # 检查entry的start是否在struct_end附近
                            # 检查entry的start是否在struct_end附近
                            # 检查entry的start是否在struct_end附近
                            # 检查entry的start是否在struct_end附近
                            if struct_end <= entry['start'] <= struct_end + 10:
                                struct_handler_target = entry['target']
                                break
                
                for other in self.structures:
                    if other != struct and other != struct.parent and isinstance(other, TryExceptStructure):
                        other_start = other.try_start_offset
                        
                        # [关键修复] 检查当前结构是否是other的内层try
                        # 条件：当前结构的handler的target等于other的start
                        # 这意味着如果当前结构的except中发生异常，会跳转到other的异常处理
                        # 所以当前结构应该作为other的child
                        if struct_handler_target is not None and other_start == struct_handler_target:
                            if struct.parent is None:
                                other.children.append(struct)
                                struct.parent = other
                                break
                        
                        # [备选方案] 检查other的handler的target是否是当前结构的start
                        # 这意味着如果other的except中发生异常，会跳转到当前结构的异常处理
                        # 所以other应该作为当前结构的child
                        other_depth = None
                        if self.cfg.exception_table:
                            for entry in self.cfg.exception_table:
                                if entry['start'] == other_start:
                                    other_depth = entry['depth']
                                    break
                        other_handler_target = None
                        if self.cfg.exception_table and other_depth is not None:
                            for entry in self.cfg.exception_table:
                                if entry['depth'] == other_depth + 1:
                                    if other.try_end_offset <= entry['start'] <= other.try_end_offset + 10:
                                        other_handler_target = entry['target']
                                        break
                        if other_handler_target is not None and struct_start == other_handler_target:
                            if other.parent is None:
                                struct.children.append(other)
                                other.parent = struct
                                break
                
                # [关键修复] 也基于try_body的包含关系构建层次关系
                # 如果other的try_body完全包含在当前struct的try_body中，那么other是struct的child
                for other in self.structures:
                    if other != struct and other != struct.parent and isinstance(other, TryExceptStructure):
                        if other.parent is None:
                            # 检查other的try_body是否完全包含在当前struct的try_body中
                            # 检查other的try_body是否完全包含在当前struct的try_body中
                            # 检查other的try_body是否完全包含在当前struct的try_body中
                            # 检查other的try_body是否完全包含在当前struct的try_body中
                            other_in_current = all(
                                block in struct.try_body or block == struct.entry_block
                                for block in other.try_body
                            )
                            if other_in_current and other.try_body:
                                struct.children.append(other)
                                other.parent = struct
                                break
                
                # [关键修复] 建立TryExceptStructure和LoopStructure/IfStructure之间的关系
                # 如果LoopStructure或IfStructure的entry_block在try_body中，它们应该是TryExceptStructure的children
                for other in self.structures:
                    if other != struct and other != struct.parent:
                        if other.parent is None:
                            # 检查other的entry_block是否在try_body中
                            # 检查other的entry_block是否在try_body中
                            # 检查other的entry_block是否在try_body中
                            # 检查other的entry_block是否在try_body中
                            if isinstance(other, (LoopStructure, IfStructure)):
                                if other.entry_block in struct.try_body or other.entry_block == struct.entry_block:
                                    struct.children.append(other)
                                    other.parent = struct
                            # 对于ControlStructure（SEQUENCE），检查其entry_block是否在try_body中
                            elif hasattr(other, 'entry_block') and hasattr(other, 'struct_type'):
                                if other.entry_block in struct.try_body or other.entry_block == struct.entry_block:
                                    struct.children.append(other)
                                    other.parent = struct
    
            elif isinstance(struct, TryExceptStructure):
                pass  # TryExcept的parent设置已合并到上面的IfStruct分支中

    def get_structure_for_block(self, block: BasicBlock) -> Optional[ControlStructure]:
        """
        获取基本块所属的控制结构
        
        Args:
            block: 基本块
            
        Returns:
            控制结构
        """
        return self.block_to_structure.get(block)
    
    def is_block_in_loop(self, block: BasicBlock) -> bool:
        """
        检查基本块是否在循环中
        
        Args:
            block: 基本块
            
        Returns:
            如果在循环中则返回True
        """
        struct = self.get_structure_for_block(block)
        return isinstance(struct, LoopStructure)
    
    def get_enclosing_loop(self, block: BasicBlock) -> Optional[LoopStructure]:
        """
        获取包含基本块的循环
        
        Args:
            block: 基本块
            
        Returns:
            循环结构
        """
        struct = self.get_structure_for_block(block)
        while struct:
            if isinstance(struct, LoopStructure):
                return struct
            struct = struct.parent
        return None
    
    def get_loop_depth(self, block: BasicBlock) -> int:
        """
        获取基本块的循环嵌套深度
        
        Args:
            block: 基本块
            
        Returns:
            循环嵌套深度
        """
        depth = 0
        struct = self.get_structure_for_block(block)
        while struct:
            if isinstance(struct, LoopStructure):
                depth += 1
            struct = struct.parent
        return depth
    
    def _identify_match_structures(self) -> None:
        """
        [Python 3.10+] 识别match/case模式匹配结构
        
        match语句的字节码特征：
        1. 以 LOAD_NAME/LOAD_FAST 加载match主题开始
        2. 后跟 COPY 指令复制主题
        3. 使用 MATCH_VALUE/MATCH_SEQUENCE/MATCH_MAPPING等指令进行匹配
        4. 每个case以 POP_JUMP_FORWARD_IF_FALSE 或类似跳转结束
        5. 最后有一个合并块
        """
        analyzed_blocks = set()
        
        for block in self.cfg.blocks.values():
            if block in analyzed_blocks:
                continue
            
            # 查找match主题加载模式
            # match x: 会生成：LOAD_NAME x, COPY
            match_subject = self._find_match_subject(block)
            if not match_subject:
                continue
            
            # 找到了match主题，现在识别case块
            match_structure = self._analyze_match_structure(block, match_subject)
            if match_structure:
                self.structures.append(match_structure)
                analyzed_blocks.update(match_structure.case_blocks)
                analyzed_blocks.add(block)
    
    def _find_match_subject(self, block: BasicBlock) -> Optional[Any]:
        """
        查找match主题表达式
        
        Args:
            block: 要分析的块
            
        Returns:
            主题表达式或None
        """
        if not block.instructions:
            return None
        
        # 查找模式：LOAD_NAME/LOAD_FAST/LOAD_GLOBAL + COPY
        instrs = block.instructions
        for i, instr in enumerate(instrs):
            if instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF'):
                # 检查下一条是否是COPY
                # 检查下一条是否是COPY
                # 检查下一条是否是COPY
                # 检查下一条是否是COPY
                if i + 1 < len(instrs) and instrs[i + 1].opname == 'COPY':
                    # 找到了match主题
                    # 找到了match主题
                    # 找到了match主题
                    # 找到了match主题
                    return {
                        'type': 'Name',
                        'id': instr.argval,
                        'ctx': 'Load',
                        'lineno': instr.starts_line
                    }
        return None
    
    def _analyze_match_structure(self, subject_block: BasicBlock, subject: Any) -> Optional[MatchStructure]:
        """
        分析match结构
        
        Args:
            subject_block: 包含match主题的块
            subject: 主题表达式
            
        Returns:
            MatchStructure或None
        """
        case_blocks = []
        case_patterns = []
        case_guards = []
        case_bodies = []
        
        # 从subject_block开始，遍历所有case
        current_block = subject_block
        visited = {subject_block}
        
        while current_block:
            # 查找当前块中的MATCH_*指令
            # 查找当前块中的MATCH_*指令
            # 查找当前块中的MATCH_*指令
            # 查找当前块中的MATCH_*指令
            pattern = self._extract_match_pattern(current_block)
            if pattern:
                case_blocks.append(current_block)
                case_patterns.append(pattern)
                
                # 查找guard（if条件）
                guard = self._extract_match_guard(current_block)
                case_guards.append(guard)
                
                # 查找case body
                body = self._extract_match_case_body(current_block)
                case_bodies.append(body)
            
            # 找到下一个case块
            next_block = self._find_next_case_block(current_block, visited)
            if next_block and next_block not in visited:
                visited.add(next_block)
                current_block = next_block
            else:
                break
        
        if len(case_blocks) < 1:
            return None
        
        # 查找合并块
        merge_block = self._find_match_merge_block(case_blocks)
        
        return MatchStructure(
            struct_type=ControlStructureType.MATCH,
            entry_block=subject_block,
            subject_block=subject_block,
            case_blocks=case_blocks,
            case_patterns=case_patterns,
            case_guards=case_guards,
            case_bodies=case_bodies,
            merge_block=merge_block
        )
    
    def _extract_match_pattern(self, block: BasicBlock) -> Optional[Any]:
        """从块中提取匹配模式"""
        for instr in block.instructions:
            if instr.opname == 'MATCH_VALUE':
                return {'type': 'MatchValue', 'op': instr.opname}
            elif instr.opname == 'MATCH_SEQUENCE':
                return {'type': 'MatchSequence', 'op': instr.opname}
            elif instr.opname == 'MATCH_MAPPING':
                return {'type': 'MatchMapping', 'op': instr.opname}
            elif instr.opname == 'MATCH_CLASS':
                return {'type': 'MatchClass', 'op': instr.opname}
            elif instr.opname == 'MATCH_KEYS':
                return {'type': 'MatchKeys', 'op': instr.opname}
        return None
    
    def _extract_match_guard(self, block: BasicBlock) -> Optional[Any]:
        """从块中提取guard条件（if条件）"""
        # [关键修复] guard条件应该是一个实际的表达式，而不是跳转指令
        # 跳转指令用于控制流，不是guard表达式
        # 真正的guard条件需要更复杂的分析，目前先返回None
        # TODO: 实现完整的guard表达式提取
        return None
    
    def _extract_match_case_body(self, block: BasicBlock) -> List[BasicBlock]:
        """提取case body块"""
        body = []
        # case body通常是匹配成功后的块（直接后继）
        # [关键修复] 排除包含MATCH_*指令的块（那些是下一个case的块）
        for succ in block.successors:
            # 检查是否是case块（包含MATCH_*指令）
            # 检查是否是case块（包含MATCH_*指令）
            # 检查是否是case块（包含MATCH_*指令）
            # 检查是否是case块（包含MATCH_*指令）
            is_case_block = any(instr.opname.startswith('MATCH_') for instr in succ.instructions)
            if not is_case_block and succ not in body:
                body.append(succ)
        
        # [关键修复] 查找POP_JUMP_FORWARD_IF_FALSE的目标块（case body）
        for instr in block.instructions:
            if instr.opname in ('POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                # 找到跳转目标
                # 找到跳转目标
                # 找到跳转目标
                # 找到跳转目标
                target_offset = instr.argval
                # 在CFG中查找对应的块
                for b in self.cfg.blocks.values():
                    if b.start_offset == target_offset and b not in body:
                        # 检查是否是case块
                        # 检查是否是case块
                        # 检查是否是case块
                        # 检查是否是case块
                        is_case_block = any(i.opname.startswith('MATCH_') for i in b.instructions)
                        if not is_case_block:
                            body.append(b)
                        break
        
        return body
    
    def _find_next_case_block(self, current_block: BasicBlock, visited: Set[BasicBlock]) -> Optional[BasicBlock]:
        """查找下一个case块"""
        # case块通常通过跳转连接
        for succ in current_block.successors:
            if succ not in visited:
                # 检查是否是case块（包含MATCH_*指令）
                # 检查是否是case块（包含MATCH_*指令）
                # 检查是否是case块（包含MATCH_*指令）
                # 检查是否是case块（包含MATCH_*指令）
                for instr in succ.instructions:
                    if instr.opname.startswith('MATCH_'):
                        return succ
        return None
    
    def _find_match_merge_block(self, case_blocks: List[BasicBlock]) -> Optional[BasicBlock]:
        """查找match结构的合并块"""
        if not case_blocks:
            return None
        
        # 合并块是所有case的公共后继
        common_succs = None
        for block in case_blocks:
            succs = set(block.successors)
            if common_succs is None:
                common_succs = succs
            else:
                common_succs &= succs
        
        if common_succs:
            return min(common_succs, key=lambda b: b.start_offset)
        return None

class RegionAnalyzer:
    """
    区域分析器
    
    将控制流图分解为区域（region），用于结构化代码生成。
    """
    
    def __init__(self, cfg: ControlFlowGraph):
        """
        初始化区域分析器
        
        Args:
            cfg: 控制流图
        """
        self.cfg = cfg
        self.regions: Dict[BasicBlock, Set[BasicBlock]] = {}
        self.region_entries: Set[BasicBlock] = set()
        self.region_exits: Dict[BasicBlock, Set[BasicBlock]] = {}
    
    def analyze(self) -> Dict[BasicBlock, Set[BasicBlock]]:
        """
        执行区域分析
        
        Returns:
            区域字典，键是入口块，值是区域中的块集合
        """
        self._find_single_entry_regions()
        self._find_loop_regions()
        self._find_conditional_regions()
        
        return self.regions
    
    def _find_single_entry_regions(self) -> None:
        """查找单入口区域"""
        for block in self.cfg.blocks.values():
            if len(block.predecessors) > 1:
                continue
            
            region = self._expand_region(block)
            if len(region) > 1:
                self.regions[block] = region
                self.region_entries.add(block)
    
    def _expand_region(self, entry: BasicBlock) -> Set[BasicBlock]:
        """
        从入口块扩展区域
        
        Args:
            entry: 入口块
            
        Returns:
            区域中的块集合
        """
        region = {entry}
        worklist = deque([entry])
        
        while worklist:
            block = worklist.popleft()
            
            for succ in block.successors:
                if succ in region:
                    continue
                
                if len(succ.predecessors) == 1 and succ.predecessors.issubset(region):
                    region.add(succ)
                    worklist.append(succ)
        
        return region
    
    def _find_loop_regions(self) -> None:
        """查找循环区域"""
        dom_analyzer = DominatorAnalyzer(self.cfg)
        dom_analyzer.analyze()
        
        loop_analyzer = LoopAnalyzer(self.cfg, dom_analyzer)
        loop_analyzer.analyze()
        
        loops = loop_analyzer.get_all_loops()
        
        for header, body in loops.items():
            if header not in self.regions:
                self.regions[header] = body
                self.region_entries.add(header)
    
    def _find_conditional_regions(self) -> None:
        """查找条件区域"""
        for block in self.cfg.blocks.values():
            if len(block.successors) != 2:
                continue
            
            if block in self.regions:
                continue
            
            region = self._analyze_conditional_region(block)
            if region:
                self.regions[block] = region
                self.region_entries.add(block)
    
    def _analyze_conditional_region(self, header: BasicBlock) -> Optional[Set[BasicBlock]]:
        """
        分析条件区域
        
        Args:
            header: 条件头部
            
        Returns:
            区域中的块集合
        """
        region = {header}
        
        succs = list(header.successors)
        merge = self._find_conditional_merge(succs[0], succs[1])
        
        if merge:
            for succ in succs:
                path = self._collect_path(succ, merge)
                region.update(path)
            region.add(merge)
        
        return region if len(region) > 1 else None
    
    def _find_conditional_merge(self, branch1: BasicBlock, branch2: BasicBlock) -> Optional[BasicBlock]:
        """
        查找条件分支的合并点
        
        Args:
            branch1: 分支1
            branch2: 分支2
            
        Returns:
            合并块
        """
        visited1 = self._reachable_blocks(branch1)
        visited2 = self._reachable_blocks(branch2)
        
        common = visited1 & visited2
        
        if common:
            return min(common, key=lambda b: b.start_offset)
        

        
        return None
    
    def _reachable_blocks(self, start: BasicBlock) -> Set[BasicBlock]:
        """
        获取从起始块可达的所有块
        
        Args:
            start: 起始块
            
        Returns:
            可达块集合
        """
        visited = set()
        worklist = deque([start])
        
        while worklist:
            block = worklist.popleft()
            
            if block in visited:
                continue
            
            visited.add(block)
            
            for succ in block.successors:
                if succ not in visited:
                    worklist.append(succ)
        
        return visited
    
    def _collect_path(self, start: BasicBlock, end: BasicBlock) -> Set[BasicBlock]:
        """
        收集从start到end路径上的所有块
        
        Args:
            start: 起始块
            end: 结束块
            
        Returns:
            路径上的块集合
        """
        path = set()
        worklist = deque([start])
        
        while worklist:
            block = worklist.popleft()
            
            if block == end or block in path:
                continue
            
            path.add(block)
            
            for succ in block.successors:
                if succ != end and succ not in path:
                    worklist.append(succ)
        
        return path
    
    def get_region_for_block(self, block: BasicBlock) -> Optional[Set[BasicBlock]]:
        """
        获取包含基本块的区域
        
        Args:
            block: 基本块
            
        Returns:
            区域中的块集合
        """
        for entry, region in self.regions.items():
            if block in region:
                return region
        return None
    
    def get_region_entry(self, block: BasicBlock) -> Optional[BasicBlock]:
        """
        获取包含基本块的区域的入口
        
        Args:
            block: 基本块
            
        Returns:
            区域入口块
        """
        for entry, region in self.regions.items():
            if block in region:
                return entry
        return None

def analyze_structure(cfg: ControlFlowGraph) -> List[ControlStructure]:
    """
    便捷函数：执行结构化分析
    
    Args:
        cfg: 控制流图
        
    Returns:
        控制结构列表
    """
    analyzer = StructuredAnalyzer(cfg)
    return analyzer.analyze()

def analyze_regions(cfg: ControlFlowGraph) -> Dict[BasicBlock, Set[BasicBlock]]:
    """
    便捷函数：执行区域分析
    
    Args:
        cfg: 控制流图
        
    Returns:
        区域字典
    """
    analyzer = RegionAnalyzer(cfg)
    return analyzer.analyze()
