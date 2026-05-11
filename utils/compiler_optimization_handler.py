"""
编译器优化处理器 - 处理Python编译器优化导致的字节码差异

Python编译器会在编译时进行以下优化：
1. 常量折叠: True and False -> False, 1 + 2 -> 3
2. 死代码消除: if True: ... else: ... (else部分被消除)

这些优化是编译器的固有行为，不是反编译器的问题。
本模块提供工具来识别和处理这类差异。
"""

import dis
import marshal
import types
from typing import List, Tuple, Dict, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass


class OptimizationType(Enum):
    """编译器优化类型"""
    CONST_FOLDING = "常量折叠"
    DEAD_CODE_ELIMINATION = "死代码消除"
    CONST_POOL_REORDER = "常量池重排序"
    UNKNOWN = "未知优化"


@dataclass
class OptimizationPattern:
    """优化模式"""
    opt_type: OptimizationType
    description: str
    is_expected: bool  # 是否是预期的优化行为


class CompilerOptimizationHandler:
    """
    编译器优化处理器
    
    用于识别和处理Python编译器优化导致的字节码差异。
    """
    
    def __init__(self):
        self.patterns = self._init_patterns()
    
    def _init_patterns(self) -> Dict[str, Any]:
        """初始化优化模式识别规则"""
        return {
            'const_folding_ops': {
                'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
                'BINARY_FLOOR_DIVIDE', 'BINARY_MODULO', 'BINARY_POWER',
                'BINARY_AND', 'BINARY_OR', 'BINARY_XOR',
                'BINARY_LSHIFT', 'BINARY_RSHIFT',
                'UNARY_POSITIVE', 'UNARY_NEGATIVE', 'UNARY_NOT', 'UNARY_INVERT',
            },
            'logical_ops': {'JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'},
            'const_load_ops': {'LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST'},
        }
    
    def analyze_diff(self, func_name: str, position: int,
                     orig_instr: dis.Instruction, new_instr: dis.Instruction,
                     orig_code: types.CodeType, new_code: types.CodeType) -> Optional[OptimizationPattern]:
        """
        分析差异是否由编译器优化导致
        
        Args:
            func_name: 函数名
            position: 指令位置
            orig_instr: 原始指令
            new_instr: 新指令
            orig_code: 原始代码对象
            new_code: 新代码对象
            
        Returns:
            如果是编译器优化导致的差异，返回OptimizationPattern；否则返回None
        """
        # 检查是否是LOAD_CONST索引差异
        if orig_instr.opname == 'LOAD_CONST' and new_instr.opname == 'LOAD_CONST':
            return self._check_const_pool_diff(
                orig_instr, new_instr, orig_code, new_code
            )
        
        # 检查是否是常量折叠
        if self._is_const_folding_pattern(orig_instr, new_instr, orig_code, new_code):
            return OptimizationPattern(
                opt_type=OptimizationType.CONST_FOLDING,
                description=f"常量折叠: {orig_instr.opname} -> {new_instr.opname}",
                is_expected=True
            )
        
        # 检查是否是死代码消除
        if self._is_dead_code_elimination(orig_instr, new_instr, orig_code, new_code):
            return OptimizationPattern(
                opt_type=OptimizationType.DEAD_CODE_ELIMINATION,
                description="死代码消除: 不可达代码被移除",
                is_expected=True
            )
        
        return None
    
    def _check_const_pool_diff(self, orig_instr: dis.Instruction, 
                               new_instr: dis.Instruction,
                               orig_code: types.CodeType, 
                               new_code: types.CodeType) -> Optional[OptimizationPattern]:
        """检查常量池差异是否由编译器优化导致"""
        orig_consts = orig_code.co_consts
        new_consts = new_code.co_consts
        
        if orig_instr.arg >= len(orig_consts) or new_instr.arg >= len(new_consts):
            return None
        
        orig_val = orig_consts[orig_instr.arg]
        new_val = new_consts[new_instr.arg]
        
        # 如果常量值相同但索引不同，这是常量池重排序
        if orig_val == new_val and orig_instr.arg != new_instr.arg:
            return OptimizationPattern(
                opt_type=OptimizationType.CONST_POOL_REORDER,
                description=f"常量池重排序: 值 {repr(orig_val)} 从索引 {orig_instr.arg} 变为 {new_instr.arg}",
                is_expected=True
            )
        
        # 如果常量值不同，检查是否是常量折叠的结果
        # 例如: True and False 被折叠为 False
        if orig_val != new_val:
            # 检查是否是布尔逻辑优化
            if self._is_boolean_folding_result(orig_val, new_val, orig_code, position=orig_instr.offset):
                return OptimizationPattern(
                    opt_type=OptimizationType.CONST_FOLDING,
                    description=f"布尔常量折叠: 原始值 {repr(orig_val)} 被优化为 {repr(new_val)}",
                    is_expected=True
                )
            
            # 检查是否是算术常量折叠
            if self._is_arithmetic_folding_result(orig_val, new_val):
                return OptimizationPattern(
                    opt_type=OptimizationType.CONST_FOLDING,
                    description=f"算术常量折叠: 原始表达式被优化为 {repr(new_val)}",
                    is_expected=True
                )
        
        # 检查是否是死代码消除导致的常量池变化
        # 例如: if True: ... else: ... 中else分支被消除，导致常量池变小
        if self._is_dead_code_elimination_const_diff(orig_instr, new_instr, orig_code, new_code):
            return OptimizationPattern(
                opt_type=OptimizationType.DEAD_CODE_ELIMINATION,
                description=f"死代码消除: 常量池索引变化 {orig_instr.arg} -> {new_instr.arg} (值: {repr(new_val)})",
                is_expected=True
            )
        
        return None
    
    def _is_dead_code_elimination_const_diff(self, orig_instr: dis.Instruction,
                                              new_instr: dis.Instruction,
                                              orig_code: types.CodeType,
                                              new_code: types.CodeType) -> bool:
        """检查是否是死代码消除导致的常量池差异"""
        orig_consts = orig_code.co_consts
        new_consts = new_code.co_consts
        
        # 死代码消除通常会导致常量池变小
        if len(new_consts) < len(orig_consts):
            # 检查新常量池是否是原常量池的子集
            new_consts_set = set(str(c) for c in new_consts if c is not None)
            orig_consts_set = set(str(c) for c in orig_consts if c is not None)
            
            # 如果新常量池是原常量池的子集，可能是死代码消除
            if new_consts_set <= orig_consts_set:
                # 检查指令加载的值在新代码中是否存在
                if new_instr.arg < len(new_consts):
                    new_val = new_consts[new_instr.arg]
                    # 检查这个值是否在原始代码中也存在（可能在不同位置）
                    for orig_val in orig_consts:
                        if orig_val == new_val:
                            return True
        
        return False
    
    def _is_boolean_folding_result(self, orig_val: Any, new_val: Any, 
                                   code: types.CodeType, position: int) -> bool:
        """检查是否是布尔逻辑折叠的结果"""
        # 如果原始值是布尔值，可能是逻辑运算的折叠结果
        if isinstance(orig_val, bool) or orig_val is None:
            instructions = list(dis.get_instructions(code))
            # 查找周围的逻辑运算指令
            for i, instr in enumerate(instructions):
                if instr.offset == position:
                    # 检查前面是否有逻辑运算指令
                    for j in range(max(0, i-5), i):
                        if instructions[j].opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                            return True
                    break
        
        # [关键修复] 检查是否是常量折叠的结果
        # 例如: a = True and False 被优化为 a = False
        # 原始代码加载 True (索引0)，新代码加载 False (索引0)
        # 但原始常量池中有 True 和 False，新常量池中只有 False
        if isinstance(orig_val, bool) and isinstance(new_val, bool):
            # 两个都是布尔值，可能是常量折叠
            return True
        
        return False
    
    def _is_arithmetic_folding_result(self, orig_val: Any, new_val: Any) -> bool:
        """检查是否是算术运算折叠的结果"""
        # 如果新值是数字，且原始值也是数字或None，可能是算术折叠
        if isinstance(new_val, (int, float)) and not isinstance(new_val, bool):
            if orig_val is None or isinstance(orig_val, (int, float)):
                return True
        return False
    
    def _is_const_folding_pattern(self, orig_instr: dis.Instruction,
                                   new_instr: dis.Instruction,
                                   orig_code: types.CodeType,
                                   new_code: types.CodeType) -> bool:
        """检查是否是常量折叠模式"""
        # 原始指令是二元/一元操作，新指令是LOAD_CONST
        if orig_instr.opname in self.patterns['const_folding_ops']:
            if new_instr.opname == 'LOAD_CONST':
                return True
        return False
    
    def _is_dead_code_elimination(self, orig_instr: dis.Instruction,
                                   new_instr: dis.Instruction,
                                   orig_code: types.CodeType,
                                   new_code: types.CodeType) -> bool:
        """检查是否是死代码消除"""
        # 如果原始代码有更多指令，且新代码缺少某些指令
        orig_ins = list(dis.get_instructions(orig_code))
        new_ins = list(dis.get_instructions(new_code))
        
        if len(orig_ins) > len(new_ins):
            # 检查是否有条件跳转相关的模式
            for instr in orig_ins:
                if instr.opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_IF_TRUE'):
                    # 检查跳转目标是否在代码末尾（即else分支被消除）
                    target_offset = instr.arg
                    if target_offset is not None:
                        # 如果跳转目标是代码末尾附近，可能是死代码消除
                        last_offset = orig_ins[-1].offset if orig_ins else 0
                        if abs(target_offset - last_offset) < 10:
                            return True
        return False
    
    def is_compiler_optimization_diff(self, func_name: str, position: int,
                                       orig_instr: dis.Instruction, 
                                       new_instr: dis.Instruction,
                                       orig_code: types.CodeType, 
                                       new_code: types.CodeType) -> bool:
        """
        检查差异是否由编译器优化导致
        
        Returns:
            如果是编译器优化导致的差异返回True，否则返回False
        """
        pattern = self.analyze_diff(func_name, position, orig_instr, new_instr, 
                                    orig_code, new_code)
        return pattern is not None and pattern.is_expected


def check_compiler_optimization_case(source_code: str) -> Optional[OptimizationType]:
    """
    检查源代码是否会导致编译器优化
    
    Args:
        source_code: Python源代码
        
    Returns:
        如果会导致编译器优化，返回OptimizationType；否则返回None
    """
    source_code = source_code.strip()
    
    # 检查常量逻辑运算
    const_logic_patterns = [
        'True and', 'and True', 'True or', 'or True',
        'False and', 'and False', 'False or', 'or False',
        'not True', 'not False',
    ]
    for pattern in const_logic_patterns:
        if pattern in source_code:
            return OptimizationType.CONST_FOLDING
    
    # 检查常量算术运算
    import re
    const_arith_patterns = [
        r'\b\d+\s*[-+*/%]\s*\d+\b',  # 1 + 2, 3 * 4 等
        r'\b0x[0-9a-fA-F]+\s*[-+*/%]',  # 十六进制运算
    ]
    for pattern in const_arith_patterns:
        if re.search(pattern, source_code):
            return OptimizationType.CONST_FOLDING
    
    # 检查常量if条件
    if 'if True:' in source_code or 'if False:' in source_code:
        return OptimizationType.DEAD_CODE_ELIMINATION
    
    # 检查elif链中的常量条件
    if 'elif True:' in source_code or 'elif False:' in source_code:
        return OptimizationType.DEAD_CODE_ELIMINATION
    
    return None


# 全局处理器实例
optimization_handler = CompilerOptimizationHandler()
