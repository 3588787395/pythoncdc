#!/usr/bin/env python3
"""
控制流分析模块
基于C++版本的ASTree.cpp实现，提供完整的Python字节码控制流分析功能
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict


class BlockType(Enum):
    """基本块类型，对应C++版本的ASTBlock::BlkType"""
    BLK_MAIN = "main"           # 主块
    BLK_IF = "if"              # if语句块
    BLK_ELSE = "else"          # else语句块
    BLK_ELIF = "elif"          # elif语句块
    BLK_TRY = "try"            # try语句块
    BLK_CONTAINER = "container" # 容器块
    BLK_EXCEPT = "except"      # except语句块
    BLK_FINALLY = "finally"    # finally语句块
    BLK_WHILE = "while"        # while循环块
    BLK_FOR = "for"            # for循环块
    BLK_WITH = "with"          # with语句块
    BLK_ASYNCFOR = "asyncfor"  # async for循环块


@dataclass
class Instruction:
    """
    指令类，对应C++版本的指令结构
    """
    offset: int              # 指令偏移量
    opcode: int              # 操作码
    opname: str              # 操作码名称
    arg: int = 0             # 参数值
    argval: Any = None       # 参数值对象
    target: Optional[int] = None  # 跳转目标（如果有）
    
    def __repr__(self) -> str:
        return f"<Instruction {self.opname} at offset {self.offset}>"
    
    def is_jump_instruction(self) -> bool:
        """判断是否为跳转指令"""
        jump_opcodes = {
            'JUMP_FORWARD_A', 'JUMP_BACKWARD_A', 'JUMP_BACKWARD_NO_INTERRUPT_A',
            'POP_JUMP_FORWARD_IF_TRUE_A', 'POP_JUMP_FORWARD_IF_FALSE_A',
            'POP_JUMP_BACKWARD_IF_TRUE_A', 'POP_JUMP_BACKWARD_IF_FALSE_A',
            'JUMP_IF_TRUE_A', 'JUMP_IF_FALSE_A',
            'POP_JUMP_IF_TRUE_A', 'POP_JUMP_IF_FALSE_A',
            'JUMP_IF_NOT_EXC_MATCH_A', 'POP_JUMP_FORWARD_IF_NOT_NONE_A',
            'POP_JUMP_FORWARD_IF_NONE_A', 'POP_JUMP_BACKWARD_IF_NOT_NONE_A',
            'POP_JUMP_BACKWARD_IF_NONE_A',
        }
        return self.opname in jump_opcodes
    
    def is_terminator(self) -> bool:
        """判断是否为终止指令"""
        terminator_opcodes = {
            'RETURN_VALUE', 'RETURN_GENERATOR', 'RAISE_VARARGS_A',
            'YIELD_VALUE', 'YIELD_FROM', 'POP_BLOCK', 'POP_EXCEPT',
        }
        return self.opname in terminator_opcodes


class BasicBlock:
    """
    基本块类，对应C++版本的ASTBlock
    """
    
    def __init__(self, start_offset: int, block_type: BlockType = BlockType.BLK_MAIN, name: str = ""):
        self.start_offset: int = start_offset
        self.end_offset: int = start_offset
        self.block_type: BlockType = block_type
        self.name: str = name or f"block_{start_offset}"
        self.instructions: List[Instruction] = []
        self.predecessors: List['BasicBlock'] = []
        self.successors: List['BasicBlock'] = []
        self.is_entry: bool = False
        self.is_exit: bool = False
        self.inited: bool = False  # 对应C++版本的m_inited
    
    def add_instruction(self, instruction: Instruction) -> None:
        """添加指令到基本块"""
        self.instructions.append(instruction)
        self.end_offset = instruction.offset
    
    def add_successor(self, block: 'BasicBlock') -> None:
        """添加后继基本块"""
        if block not in self.successors:
            self.successors.append(block)
            block.predecessors.append(self)
    
    def add_predecessor(self, block: 'BasicBlock') -> None:
        """添加前驱基本块"""
        if block not in self.predecessors:
            self.predecessors.append(block)
            block.successors.append(self)
    
    def __repr__(self) -> str:
        return f"<BasicBlock {self.name} [{self.start_offset}-{self.end_offset}] {self.block_type.value}>"
    
    def __str__(self) -> str:
        return self.__repr__()


class ControlFlowAnalyzer:
    """
    控制流分析器，基于C++版本ASTree.cpp的控制流分析算法实现
    """
    
    def __init__(self, instructions: Optional[List[Instruction]] = None):
        """
        初始化控制流分析器
        
        Args:
            instructions: 字节码指令列表（可选）
        """
        self.instructions: List[Instruction] = instructions if instructions else []
        self.blocks: List[BasicBlock] = []
        self.block_map: Dict[int, BasicBlock] = {}  # 偏移量到基本块的映射
        self.analysis_completed: bool = False
        
    def analyze(self) -> List[BasicBlock]:
        """
        执行控制流分析
        基于C++版本的控制流分析算法
        
        Returns:
            分析得到的基本块列表
        """
        if not self.instructions:
            # 空指令列表，创建空的主块
            self.blocks = [BasicBlock(0, BlockType.BLK_MAIN, "entry")]
            self.blocks[0].is_entry = True
            self.analysis_completed = True
            return self.blocks
        
        # 第一步：找到所有基本块的起始位置
        block_starts = self._find_block_starts()
        
        # 第二步：创建基本块
        self._create_blocks(block_starts)
        
        # 第三步：分配指令到基本块
        self._assign_instructions_to_blocks()
        
        # 第四步：连接基本块
        self._connect_blocks()
        
        self.analysis_completed = True
        return self.blocks
    
    def _find_block_starts(self) -> Set[int]:
        """
        找到所有基本块的起始位置
        对应C++版本的块起始分析
        """
        block_starts = {0}  # 总是从偏移量0开始
        
        for instr in self.instructions:
            # 跳转目标总是新块的开始
            if instr.is_jump_instruction() and instr.target is not None:
                block_starts.add(instr.target)
            
            # 跳转到当前指令的下一条指令（fall-through）
            if instr.is_jump_instruction():
                next_offset = instr.offset + self._get_instruction_size(instr)
                block_starts.add(next_offset)
            
            # 🎯 新增：识别MAKE_FUNCTION指令作为函数边界
            if instr.opname == 'MAKE_FUNCTION':
                # MAKE_FUNCTION指令后开始新的基本块（函数定义）
                next_offset = instr.offset + self._get_instruction_size(instr)
                block_starts.add(next_offset)
                print(f'🔍 发现函数边界：MAKE_FUNCTION at {instr.offset}, 新块起始于 {next_offset}')
        
        return block_starts
    
    def _get_instruction_size(self, instruction: Instruction) -> int:
        """
        获取指令大小（字节数）
        简化实现，假设大部分指令占2字节
        """
        if instruction.arg is not None and instruction.arg != 0:
            return 3  # opcode + operand
        return 1  # just opcode
    
    def _create_blocks(self, block_starts: Set[int]) -> None:
        """创建基本块"""
        self.blocks = []
        self.block_map = {}
        
        # 按偏移量排序
        sorted_starts = sorted(block_starts)
        
        for start in sorted_starts:
            # 根据起始位置推断块类型（简化实现）
            block_type = self._infer_block_type(start)
            block = BasicBlock(start, block_type)
            
            # 标记入口块
            if start == 0:
                block.is_entry = True
            elif start == max(sorted_starts):
                block.is_exit = True
            
            self.blocks.append(block)
            self.block_map[start] = block
    
    def _infer_block_type(self, offset: int) -> BlockType:
        """
        根据偏移量推断块类型（简化实现）
        在实际实现中需要更复杂的分析
        """
        # 查找包含此偏移量的指令
        for instr in self.instructions:
            if instr.offset == offset:
                # 改进：根据指令类型推断
                if 'JUMP' in instr.opname:
                    return BlockType.BLK_IF
                elif 'MAKE_FUNCTION' in instr.opname:
                    print(f'🔍 推断函数定义块：offset {offset}, MAKE_FUNCTION')
                    return BlockType.BLK_MAIN  # 函数定义仍然归类为主块
                elif 'RETURN' in instr.opname:
                    return BlockType.BLK_MAIN
                break
        
        return BlockType.BLK_MAIN
    
    def _assign_instructions_to_blocks(self) -> None:
        """将指令分配到对应的基本块"""
        current_block = None
        
        for instr in self.instructions:
            # 找到包含此指令的基本块
            block = self._find_block_containing_offset(instr.offset)
            if block != current_block:
                current_block = block
            
            if current_block:
                current_block.add_instruction(instr)
    
    def _find_block_containing_offset(self, offset: int) -> Optional[BasicBlock]:
        """找到包含指定偏移量的基本块"""
        for block in self.blocks:
            if block.start_offset <= offset <= block.end_offset:
                return block
        return None
    
    def _connect_blocks(self) -> None:
        """连接基本块，建立前驱和后继关系"""
        # 按起始偏移量排序
        sorted_blocks = sorted(self.blocks, key=lambda b: b.start_offset)
        
        for i, block in enumerate(sorted_blocks):
            # 连接非终止块到下一个块
            if not self._is_terminator_block(block):
                next_block = self._find_next_block(block)
                if next_block:
                    block.add_successor(next_block)
            
            # 处理跳转指令
            self._handle_jump_instructions(block)
    
    def _is_terminator_block(self, block: BasicBlock) -> bool:
        """判断是否为终止块（没有后继）"""
        if not block.instructions:
            return False
        
        # 检查最后一条指令是否为终止指令
        last_instr = block.instructions[-1]
        return last_instr.is_terminator()
    
    def detect_function_calls_returns(self) -> Dict[str, Any]:
        """
        检测函数调用和返回控制流
        基于C++版本的CALL_FUNCTION和RETURN_VALUE处理逻辑
        
        Returns:
            检测到的函数调用和返回信息字典
        """
        function_control_flow = {
            'function_calls': [],
            'return_statements': [],
            'function_entries': [],
            'function_exits': [],
            'parameter_passing': []
        }
        
        # 遍历所有基本块，寻找函数调用和返回
        for block in self.blocks:
            self._analyze_function_calls(block, function_control_flow)
            self._analyze_return_statements(block, function_control_flow)
        
        # 分析函数入口和出口
        self._analyze_function_entries_exits(function_control_flow)
        
        # 分析参数传递
        self._analyze_parameter_passing(function_control_flow)
        
        return function_control_flow
    
    def _analyze_function_calls(self, block: BasicBlock, function_control_flow: Dict[str, Any]) -> None:
        """分析函数调用"""
        for instr in block.instructions:
            if self._is_function_call_instruction(instr):
                call_info = {
                    'call_block': block,
                    'call_instruction': instr,
                    'function_target': None,
                    'arguments': [],
                    'return_handling': None
                }
                
                # 分析调用目标
                target = self._analyze_call_target(block, instr, call_info)
                call_info['function_target'] = target
                
                # 分析参数
                arguments = self._analyze_call_arguments(block, instr)
                call_info['arguments'] = arguments
                
                function_control_flow['function_calls'].append(call_info)
    
    def _is_function_call_instruction(self, instruction: Instruction) -> bool:
        """判断是否为函数调用指令"""
        call_opcodes = {
            'CALL_A', 'CALL_KW', 'CALL', 'CALL_FUNCTION', 'CALL_FUNCTION_EX',
            'CALL_METHOD', 'PRECALL_FUNCTION', 'PRECALL_FUNCTION_EX',
            'PRECALL_METHOD', 'PRECALL', 'CALL_A_1', 'CALL_A_2', 'CALL_A_3',
            'CALL_A_4', 'CALL_A_5', 'CALL_A_6', 'CALL_A_7', 'CALL_A_8',
            'CALL_A_9', 'CALL_A_10', 'CALL_A_11', 'CALL_A_12',
            'CALL_A_13', 'CALL_A_14', 'CALL_A_15', 'CALL_A_16',
            'CALL_A_17', 'CALL_A_18', 'CALL_A_19', 'CALL_A_20',
            'CALL_A_21', 'CALL_A_22', 'CALL_A_23', 'CALL_A_24',
            'CALL_A_25', 'CALL_A_26', 'CALL_A_27', 'CALL_A_28',
            'CALL_A_29', 'CALL_A_30', 'CALL_A_31', 'CALL_A_32'
        }
        return instruction.opname in call_opcodes
    
    def _analyze_call_target(self, block: BasicBlock, call_instr: Instruction, call_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """分析函数调用目标"""
        # 寻找调用目标（在调用指令之前的指令）
        call_offset = call_instr.offset
        
        # 在当前块中寻找调用目标
        target_instr = None
        for instr in block.instructions:
            if instr.offset < call_offset and self._is_call_target_instruction(instr):
                target_instr = instr
                break
        
        if not target_instr:
            # 寻找在前驱块中的调用目标
            for predecessor in block.predecessors:
                for instr in predecessor.instructions:
                    if instr.offset < call_offset and self._is_call_target_instruction(instr):
                        target_instr = instr
                        break
                if target_instr:
                    break
        
        if target_instr:
            return {
                'target_block': block,
                'target_instruction': target_instr,
                'target_type': self._determine_target_type(target_instr)
            }
        
        return None
    
    def _is_call_target_instruction(self, instruction: Instruction) -> bool:
        """判断是否为调用目标指令"""
        target_opcodes = {
            'LOAD_GLOBAL_A', 'LOAD_NAME_A', 'LOAD_ATTR_A', 'LOAD_FAST_A',
            'LOAD_CONST_A', 'LOAD_METHOD_A', 'LOAD_DEREF_A', 'LOAD_CLASSDEREF_A',
            'LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_ATTR', 'LOAD_FAST',
            'LOAD_CONST', 'LOAD_METHOD', 'LOAD_DEREF', 'LOAD_CLASSDEREF',
            'BUILD_TUPLE_A', 'BUILD_LIST_A', 'BUILD_SET_A', 'BUILD_MAP_A',
            'BUILD_SLICE_A', 'BUILD_STRING_A'
        }
        return instruction.opname in target_opcodes
    
    def _determine_target_type(self, target_instr: Instruction) -> str:
        """确定调用目标的类型"""
        if target_instr.opname in ['LOAD_GLOBAL_A', 'LOAD_GLOBAL']:
            return 'global_function'
        elif target_instr.opname in ['LOAD_ATTR_A', 'LOAD_ATTR']:
            return 'method_call'
        elif target_instr.opname in ['LOAD_FAST_A', 'LOAD_FAST']:
            return 'parameter_function'
        elif target_instr.opname in ['LOAD_CONST_A', 'LOAD_CONST']:
            return 'lambda_function'
        else:
            return 'unknown'
    
    def _analyze_call_arguments(self, block: BasicBlock, call_instr: Instruction) -> List[Dict[str, Any]]:
        """分析函数调用参数"""
        arguments = []
        
        # 简化的参数分析：基于调用指令的参数数量
        arg_count = call_instr.arg if call_instr.arg else 0
        
        for i in range(arg_count):
            arg_info = {
                'arg_index': i,
                'arg_type': 'positional',  # 默认类型
                'arg_source': None
            }
            arguments.append(arg_info)
        
        return arguments
    
    def _analyze_return_statements(self, block: BasicBlock, function_control_flow: Dict[str, Any]) -> None:
        """分析返回语句"""
        for instr in block.instructions:
            if self._is_return_instruction(instr):
                return_info = {
                    'return_block': block,
                    'return_instruction': instr,
                    'return_value': None,
                    'function_exit': None
                }
                
                # 分析返回值
                return_value = self._analyze_return_value(block, instr)
                return_info['return_value'] = return_value
                
                function_control_flow['return_statements'].append(return_info)
    
    def _is_return_instruction(self, instruction: Instruction) -> bool:
        """判断是否为返回指令"""
        return_opcodes = {
            'RETURN_VALUE', 'RETURN_GENERATOR', 'INSTRUMENTED_RETURN_VALUE_A'
        }
        return instruction.opname in return_opcodes
    
    def _analyze_return_value(self, block: BasicBlock, return_instr: Instruction) -> Optional[Dict[str, Any]]:
        """分析返回值"""
        # 寻找返回值的源（返回指令之前的指令）
        return_offset = return_instr.offset
        
        # 在当前块中寻找返回值
        value_instr = None
        for instr in block.instructions:
            if instr.offset < return_offset and self._is_value_instruction(instr):
                value_instr = instr
                break
        
        if value_instr:
            return {
                'value_block': block,
                'value_instruction': value_instr,
                'value_type': self._determine_value_type(value_instr)
            }
        
        return None
    
    def _is_value_instruction(self, instruction: Instruction) -> bool:
        """判断是否为值指令"""
        value_opcodes = {
            'LOAD_CONST_A', 'LOAD_CONST', 'LOAD_FAST_A', 'LOAD_FAST',
            'LOAD_GLOBAL_A', 'LOAD_GLOBAL', 'LOAD_NAME_A', 'LOAD_NAME',
            'LOAD_DEREF_A', 'LOAD_DEREF', 'LOAD_CLASSDEREF_A', 'LOAD_CLASSDEREF'
        }
        return instruction.opname in value_opcodes
    
    def _determine_value_type(self, value_instr: Instruction) -> str:
        """确定值类型"""
        if value_instr.opname in ['LOAD_CONST_A', 'LOAD_CONST']:
            return 'constant'
        elif value_instr.opname in ['LOAD_FAST_A', 'LOAD_FAST']:
            return 'parameter'
        elif value_instr.opname in ['LOAD_GLOBAL_A', 'LOAD_GLOBAL']:
            return 'global_variable'
        elif value_instr.opname in ['LOAD_DEREF_A', 'LOAD_DEREF']:
            return 'closure_variable'
        else:
            return 'unknown'
    
    def detect_for_while_loops(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        检测for和while循环
        基于C++版本的ASTIterBlock和ASTCondBlock分析逻辑
        
        Returns:
            检测到的循环结构信息字典
        """
        loops = {
            'for_loops': [],
            'while_loops': [],
            'nested_loops': []
        }
        
        # 检测for循环
        self._detect_for_loops(loops)
        
        # 检测while循环
        self._detect_while_loops(loops)
        
        # 检测嵌套循环
        self._detect_nested_loops(loops)
        
        return loops
    
    def _detect_for_loops(self, loops: Dict[str, List[Dict[str, Any]]]) -> None:
        """检测for循环"""
        for block in self.blocks:
            if self._is_for_loop_block(block):
                for_loop = {
                    'loop_block': block,
                    'loop_entry': block,
                    'loop_exit': None,
                    'iterator': None,
                    'body': [],
                    'nesting_level': self._calculate_loop_nesting_level(block)
                }
                loops['for_loops'].append(for_loop)
    
    def _is_for_loop_block(self, block: BasicBlock) -> bool:
        """判断是否为for循环块"""
        # 简化实现：检查是否包含循环相关指令
        for instr in block.instructions:
            if 'GET_ITER' in instr.opname or 'FOR_ITER' in instr.opname:
                return True
        return False
    
    def _detect_while_loops(self, loops: Dict[str, List[Dict[str, Any]]]) -> None:
        """检测while循环"""
        for block in self.blocks:
            if self._is_while_loop_block(block):
                while_loop = {
                    'loop_block': block,
                    'condition': None,
                    'loop_body': [],
                    'loop_exit': None,
                    'nesting_level': self._calculate_loop_nesting_level(block)
                }
                loops['while_loops'].append(while_loop)
    
    def _is_while_loop_block(self, block: BasicBlock) -> bool:
        """判断是否为while循环块"""
        # 检查是否包含条件跳转指令（while循环的特征）
        for instr in block.instructions:
            if instr.is_jump_instruction():
                return True
        return False
    
    def _detect_nested_loops(self, loops: Dict[str, List[Dict[str, Any]]]) -> None:
        """检测嵌套循环"""
        # 简化实现：检测循环的嵌套关系
        for for_loop in loops['for_loops']:
            nested_level = 1
            for other_loop in loops['for_loops'] + loops['while_loops']:
                if (other_loop != for_loop and 
                    self._is_block_contained_in_block(other_loop['loop_block'], for_loop['loop_block'])):
                    nested_level += 1
                    loops['nested_loops'].append({
                        'outer_loop': for_loop,
                        'inner_loop': other_loop,
                        'nesting_level': nested_level
                    })
    
    def _is_block_contained_in_block(self, inner_block: BasicBlock, outer_block: BasicBlock) -> bool:
        """判断内层块是否被外层块包含"""
        return (outer_block.start_offset <= inner_block.start_offset and
                inner_block.end_offset <= outer_block.end_offset)
    
    def _calculate_loop_nesting_level(self, block: BasicBlock) -> int:
        """计算循环嵌套深度"""
        nesting_level = 0
        for other_block in self.blocks:
            if (other_block != block and
                self._is_block_contained_in_block(block, other_block) and
                self._is_loop_block(other_block)):
                nesting_level += 1
        return nesting_level
    
    def _is_loop_block(self, block: BasicBlock) -> bool:
        """判断是否为循环块"""
        return self._is_for_loop_block(block) or self._is_while_loop_block(block)
    
    def _analyze_function_entries_exits(self, function_control_flow: Dict[str, Any]) -> None:
        """分析函数入口和出口"""
        # 分析函数入口
        for call in function_control_flow['function_calls']:
            if call['function_target']:
                target = call['function_target']['target_block']
                if target not in function_control_flow['function_entries']:
                    function_control_flow['function_entries'].append(target)
        
        # 分析函数出口
        for return_stmt in function_control_flow['return_statements']:
            return_block = return_stmt['return_block']
            if return_block not in function_control_flow['function_exits']:
                function_control_flow['function_exits'].append(return_block)
    
    def _analyze_parameter_passing(self, function_control_flow: Dict[str, Any]) -> None:
        """分析参数传递"""
        for call in function_control_flow['function_calls']:
            if call['function_target']:
                param_info = {
                    'call': call,
                    'parameters': [],
                    'return_handling': None
                }
                
                # 分析参数传递
                for arg in call['arguments']:
                    param_info['parameters'].append({
                        'parameter_index': arg['arg_index'],
                        'parameter_type': arg['arg_type'],
                        'parameter_source': arg['arg_source']
                    })
                
                function_control_flow['parameter_passing'].append(param_info)
    
    def analyze_complete_control_flow(self) -> Dict[str, Any]:
        """
        完整控制流分析
        整合所有控制流分析功能
        
        Returns:
            完整的控制流分析结果
        """
        complete_analysis = {
            'basic_blocks': len(self.blocks),
            'entry_block': self.blocks[0] if self.blocks else None,
            'exit_blocks': [block for block in self.blocks if block.is_exit],
            'control_flow_graph': self.get_control_flow_graph(),
            'conditions': self.detect_conditions(),
            'if_elif_else': self.detect_if_elif_else_structure(),
            'loops': self.detect_for_while_loops(),
            'loop_control_flow': self.analyze_loop_control_flow(),
            'exceptions': self.detect_exception_handling(),
            'exception_control_flow': self.analyze_exception_control_flow(),
            'break_continue_jumps': self.detect_break_continue_jumps(),
            'function_calls_returns': self.detect_function_calls_returns(),
            'complexity_metrics': self._calculate_complexity_metrics()
        }
        
        return complete_analysis
    
    def _calculate_complexity_metrics(self) -> Dict[str, int]:
        """计算控制流复杂度指标"""
        metrics = {
            'cyclomatic_complexity': 1,  # 基础复杂度
            'max_loop_nesting': 0,
            'max_condition_nesting': 0,
            'function_call_count': 0,
            'exception_handling_count': 0
        }
        
        # 计算条件复杂度
        conditions = self.detect_conditions()
        metrics['cyclomatic_complexity'] += len(conditions)
        
        # 计算循环嵌套深度
        loops = self.detect_for_while_loops()
        if loops['nested_loops']:
            metrics['max_loop_nesting'] = max(len(nested['nested_loops']) for nested in loops['nested_loops'])
        
        # 计算函数调用数量
        function_calls = self.detect_function_calls_returns()
        metrics['function_call_count'] = len(function_calls['function_calls'])
        
        # 计算异常处理数量
        exceptions = self.detect_exception_handling()
        metrics['exception_handling_count'] = len(exceptions['try_blocks'])
        
        return metrics
    
    def optimize_control_flow_analysis(self) -> Dict[str, Any]:
        """
        优化控制流分析性能
        基于C++版本的高效分析算法
        
        Returns:
            优化后的分析结果和性能指标
        """
        optimization = {
            'optimized_blocks': [],
            'merged_blocks': [],
            'removed_redundancy': [],
            'performance_gain': {},
            'analysis_time': 0.0
        }
        
        import time
        start_time = time.time()
        
        # 优化基本块
        self._optimize_basic_blocks(optimization)
        
        # 合并冗余块
        self._merge_redundant_blocks(optimization)
        
        # 移除冗余跳转
        self._remove_redundant_jumps(optimization)
        
        # 计算性能指标
        optimization['analysis_time'] = time.time() - start_time
        optimization['performance_gain'] = {
            'original_block_count': len(self.blocks),
            'optimized_block_count': len(optimization['optimized_blocks']),
            'reduction_ratio': len(optimization['merged_blocks']) / max(len(self.blocks), 1)
        }
        
        return optimization
    
    def _optimize_basic_blocks(self, optimization: Dict[str, Any]) -> None:
        """优化基本块"""
        # 移除空块
        for block in self.blocks:
            if block.instructions:
                optimization['optimized_blocks'].append(block)
    
    def _merge_redundant_blocks(self, optimization: Dict[str, Any]) -> None:
        """合并冗余块"""
        # 简化实现：合并只有一个后继且内容简单的块
        for i, block in enumerate(self.blocks):
            if (len(block.successors) == 1 and 
                len(block.instructions) <= 2 and
                block.instructions and
                not block.instructions[-1].is_terminator()):
                
                successor = block.successors[0]
                if successor.instructions:
                    # 合并块
                    merged_block = BasicBlock(block.start_offset, block.block_type)
                    merged_block.instructions = block.instructions + successor.instructions
                    optimization['optimized_blocks'].append(merged_block)
                    optimization['merged_blocks'].append((block, successor))
    
    def _remove_redundant_jumps(self, optimization: Dict[str, Any]) -> None:
        """移除冗余跳转"""
        # 简化实现：移除跳转到下一条指令的跳转
        for block in self.blocks:
            for instr in block.instructions:
                if instr.is_jump_instruction() and instr.target:
                    # 检查是否为跳转到下一条指令
                    next_offset = instr.offset + 3  # 假设指令占3字节
                    if instr.target == next_offset:
                        optimization['removed_redundancy'].append(instr)
                        # 移除跳转（简化实现）
                        block.instructions.remove(instr)
        
        last_instr = block.instructions[-1]
        return last_instr.is_terminator()
    
    def _find_next_block(self, current_block: BasicBlock) -> Optional[BasicBlock]:
        """找到当前块的后继块（fall-through路径）"""
        if not current_block.instructions:
            # 如果当前块没有指令，直接返回下一个按偏移量排序的块
            sorted_blocks = sorted(self.blocks, key=lambda b: b.start_offset)
            current_index = sorted_blocks.index(current_block)
            if current_index + 1 < len(sorted_blocks):
                return sorted_blocks[current_index + 1]
            return None
        
        next_offset = current_block.end_offset + self._get_instruction_size(current_block.instructions[-1])
        
        for block in self.blocks:
            if block.start_offset == next_offset:
                return block
        return None
    
    def _handle_jump_instructions(self, block: BasicBlock) -> None:
        """处理跳转指令，添加跳转边"""
        for instr in block.instructions:
            if instr.is_jump_instruction() and instr.target is not None:
                target_block = self._find_block_containing_offset(instr.target)
                if target_block:
                    block.add_successor(target_block)
    
    def get_block_at_offset(self, offset: int) -> Optional[BasicBlock]:
        """获取包含指定偏移量的基本块"""
        return self._find_block_containing_offset(offset)
    
    def detect_conditions(self) -> List[Tuple[BasicBlock, BasicBlock, str]]:
        """
        检测条件分支
        基于C++版本的复杂条件分支分析
        
        Returns:
            (条件块, 跳转目标块, 条件类型) 的列表
        """
        conditions = []
        
        for block in self.blocks:
            for instr in block.instructions:
                if instr.is_jump_instruction():
                    target_block = self._find_block_containing_offset(instr.target)
                    if target_block:
                        conditions.append((block, target_block, instr.opname))
        
        return conditions
    
    def detect_if_elif_else_structure(self) -> Dict[str, Any]:
        """
        检测if/elif/else结构
        基于C++版本的ASTree.cpp条件分支分析逻辑
        
        Returns:
            检测到的结构信息字典
        """
        structure = {
            'if_blocks': [],
            'elif_blocks': [],
            'else_blocks': [],
            'nested_structures': []
        }
        
        # 遍历所有基本块，寻找if/elif/else模式
        for block in self.blocks:
            if_block_info = self._analyze_if_block(block)
            if if_block_info:
                structure['if_blocks'].append(if_block_info)
        
        # 寻找elif链
        self._detect_elif_chains(structure)
        
        # 寻找else块
        self._detect_else_blocks(structure)
        
        return structure
    
    def _analyze_if_block(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """
        分析单个if块
        基于C++版本的ASTBlock分析逻辑
        """
        if not block.instructions:
            return None
        
        # 寻找条件跳转指令
        condition_instr = None
        for instr in block.instructions:
            if instr.is_jump_instruction():
                condition_instr = instr
                break
        
        if not condition_instr:
            return None
        
        if_block_info = {
            'condition_block': block,
            'condition_instruction': condition_instr,
            'jump_target': condition_instr.target,
            'false_branch': None,
            'true_branch': None,
            'condition_type': condition_instr.opname,
            'nested_conditions': []
        }
        
        # 分析true和false分支
        self._analyze_condition_branches(if_block_info)
        
        return if_block_info
    
    def _is_conditional_jump(self, instruction: Instruction) -> bool:
        """判断是否为条件跳转指令"""
        conditional_jumps = {
            'POP_JUMP_FORWARD_IF_TRUE_A', 'POP_JUMP_FORWARD_IF_FALSE_A',
            'POP_JUMP_BACKWARD_IF_TRUE_A', 'POP_JUMP_BACKWARD_IF_FALSE_A',
            'JUMP_IF_TRUE_A', 'JUMP_IF_FALSE_A',
            'POP_JUMP_IF_TRUE_A', 'POP_JUMP_IF_FALSE_A',
            'JUMP_IF_NOT_EXC_MATCH_A',
            'POP_JUMP_FORWARD_IF_NOT_NONE_A', 'POP_JUMP_FORWARD_IF_NONE_A',
            'POP_JUMP_BACKWARD_IF_NOT_NONE_A', 'POP_JUMP_BACKWARD_IF_NONE_A',
        }
        return instruction.opname in conditional_jumps
    
    def _analyze_condition_branches(self, if_block_info: Dict[str, Any]) -> None:
        """分析条件分支的true和false路径"""
        condition_instr = if_block_info['condition_instruction']
        jump_target = if_block_info['jump_target']
        
        # 获取false分支（fall-through路径）
        false_branch = self._find_next_block(if_block_info['condition_block'])
        if_block_info['false_branch'] = false_branch
        
        # 获取true分支（jump target）
        true_branch = self._find_block_containing_offset(jump_target)
        if_block_info['true_branch'] = true_branch
    
    def _detect_elif_chains(self, structure: Dict[str, Any]) -> None:
        """检测elif链"""
        # 基于C++版本的elif检测逻辑
        for if_block in structure['if_blocks']:
            elif_chain = self._build_elif_chain(if_block)
            if elif_chain:
                structure['elif_blocks'].append(elif_chain)
    
    def _build_elif_chain(self, if_block: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """构建elif链"""
        # 简化的elif链构建逻辑
        # 在实际实现中需要更复杂的分析
        
        current_block = if_block['false_branch']
        elif_chain = []
        
        while current_block and current_block != if_block['true_branch']:
            elif_info = self._analyze_elif_block(current_block)
            if elif_info:
                elif_chain.append(elif_info)
                current_block = elif_info['false_branch']
            else:
                break
        
        return elif_chain if elif_chain else None
    
    def _analyze_elif_block(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """分析elif块"""
        # 检查是否是条件跳转
        condition_instr = None
        for instr in block.instructions:
            if instr.is_jump_instruction():
                condition_instr = instr
                break
        
        if not condition_instr:
            return None
        
        return {
            'condition_block': block,
            'condition_instruction': condition_instr,
            'jump_target': condition_instr.target,
            'false_branch': self._find_next_block(block),
            'true_branch': self._find_block_containing_offset(condition_instr.target),
            'condition_type': condition_instr.opname
        }
    
    def _detect_else_blocks(self, structure: Dict[str, Any]) -> None:
        """检测else块"""
        for if_block in structure['if_blocks']:
            false_branch = if_block['false_branch']
            if false_branch:
                # 检查false分支是否以返回或跳转结束
                if not self._ends_with_terminator(false_branch):
                    structure['else_blocks'].append({
                        'else_block': false_branch,
                        'parent_if': if_block
                    })
    
    def _ends_with_terminator(self, block: BasicBlock) -> bool:
        """检查块是否以终止指令结束"""
        if not block.instructions:
            return False
        
        return block.instructions[-1].is_terminator()
    
    def _find_next_block(self, current_block: BasicBlock) -> Optional[BasicBlock]:
        """找到当前块的后继块（fall-through路径）"""
        if not current_block.instructions:
            # 如果当前块没有指令，直接返回下一个按偏移量排序的块
            sorted_blocks = sorted(self.blocks, key=lambda b: b.start_offset)
            current_index = sorted_blocks.index(current_block)
            if current_index + 1 < len(sorted_blocks):
                return sorted_blocks[current_index + 1]
            return None
        
        next_offset = current_block.end_offset + self._get_instruction_size(current_block.instructions[-1])
        
        for block in self.blocks:
            if block.start_offset == next_offset:
                return block
        return None
    
    def detect_loops(self) -> List[Tuple[BasicBlock, BasicBlock]]:
        """
        检测循环
        基于C++版本的循环检测算法
        
        Returns:
            (循环头块, 循环尾块) 的列表
        """
        loops = []
        
        for block in self.blocks:
            for successor in block.successors:
                # 如果后继块在当前块之前，可能是循环
                if successor.start_offset < block.start_offset:
                    loops.append((successor, block))
        
        return loops
    
    def detect_for_while_loops(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        检测for和while循环
        基于C++版本的ASTIterBlock和ASTCondBlock分析逻辑
        
        Returns:
            检测到的循环结构信息字典
        """
        loops = {
            'for_loops': [],
            'while_loops': [],
            'nested_loops': []
        }
        
        # 检测for循环
        self._detect_for_loops(loops)
        
        # 检测while循环
        self._detect_while_loops(loops)
        
        # 检测嵌套循环
        self._detect_nested_loops(loops)
        
        return loops
    
    def _detect_for_loops(self, loops: Dict[str, List[Dict[str, Any]]]) -> None:
        """检测for循环"""
        for block in self.blocks:
            for_loop_info = self._analyze_for_loop(block)
            if for_loop_info:
                loops['for_loops'].append(for_loop_info)
    
    def _detect_while_loops(self, loops: Dict[str, List[Dict[str, Any]]]) -> None:
        """检测while循环"""
        for block in self.blocks:
            while_loop_info = self._analyze_while_loop(block)
            if while_loop_info:
                loops['while_loops'].append(while_loop_info)
    
    def _analyze_for_loop(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """
        分析for循环
        基于C++版本的FOR_ITER_A分析逻辑
        """
        # 寻找FOR_ITER指令
        for_iter_instr = None
        for instr in block.instructions:
            if instr.opname in ['FOR_ITER_A', 'FOR_ITER']:
                for_iter_instr = instr
                break
        
        if not for_iter_instr:
            return None
        
        for_loop_info = {
            'loop_header': block,
            'iterator_instruction': for_iter_instr,
            'loop_body': [],
            'loop_exit': None,
            'break_blocks': [],
            'continue_blocks': []
        }
        
        # 分析循环体和退出点
        self._analyze_for_loop_structure(for_loop_info)
        
        return for_loop_info
    
    def _analyze_for_loop_structure(self, for_loop_info: Dict[str, Any]) -> None:
        """分析for循环结构"""
        iterator_instr = for_loop_info['iterator_instruction']
        jump_target = iterator_instr.target
        
        # 获取循环体（从当前块开始到跳转目标之前）
        current_block = for_loop_info['loop_header']
        while current_block:
            for_loop_info['loop_body'].append(current_block)
            
            # 检查是否应该停止
            if current_block == for_loop_info['loop_header']:
                break
            
            # 获取下一个块
            current_block = self._find_next_block(current_block)
            
            # 如果遇到跳转目标，停止
            if current_block and current_block.start_offset >= jump_target:
                break
    
    def _analyze_while_loop(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """
        分析while循环
        基于C++版本的SETUP_LOOP_A分析逻辑
        """
        # 寻找SETUP_LOOP指令
        setup_loop_instr = None
        for instr in block.instructions:
            if instr.opname == 'SETUP_LOOP_A':
                setup_loop_instr = instr
                break
        
        if not setup_loop_instr:
            return None
        
        while_loop_info = {
            'loop_header': block,
            'setup_instruction': setup_loop_instr,
            'condition_block': None,
            'loop_body': [],
            'loop_exit': None,
            'break_blocks': [],
            'continue_blocks': []
        }
        
        # 分析while循环结构
        self._analyze_while_loop_structure(while_loop_info)
        
        return while_loop_info
    
    def _analyze_while_loop_structure(self, while_loop_info: Dict[str, Any]) -> None:
        """分析while循环结构"""
        setup_instr = while_loop_info['setup_instruction']
        loop_end_offset = setup_instr.target
        
        # 寻找条件块
        condition_block = self._find_condition_block(while_loop_info['loop_header'])
        while_loop_info['condition_block'] = condition_block
        
        # 分析循环体
        if condition_block:
            self._analyze_while_loop_body(while_loop_info, loop_end_offset)
    
    def _find_condition_block(self, loop_header: BasicBlock) -> Optional[BasicBlock]:
        """找到while循环的条件块"""
        # 简化实现：在实际中需要更复杂的分析
        return self._find_next_block(loop_header)
    
    def _analyze_while_loop_body(self, while_loop_info: Dict[str, Any], loop_end_offset: int) -> None:
        """分析while循环体"""
        condition_block = while_loop_info['condition_block']
        if not condition_block:
            return
        
        current_block = self._find_next_block(condition_block)
        while current_block and current_block.start_offset < loop_end_offset:
            while_loop_info['loop_body'].append(current_block)
            
            # 检查break指令
            self._check_for_break_continue(current_block, while_loop_info)
            
            current_block = self._find_next_block(current_block)
    
    def _check_for_break_continue(self, block: BasicBlock, loop_info: Dict[str, Any]) -> None:
        """检查break和continue指令"""
        for instr in block.instructions:
            if instr.opname == 'BREAK_LOOP':
                loop_info['break_blocks'].append(block)
            elif instr.opname == 'CONTINUE_LOOP':
                loop_info['continue_blocks'].append(block)
    
    def _detect_nested_loops(self, loops: Dict[str, List[Dict[str, Any]]]) -> None:
        """检测嵌套循环"""
        all_loops = loops['for_loops'] + loops['while_loops']
        
        for i, outer_loop in enumerate(all_loops):
            nested_loops = []
            for j, inner_loop in enumerate(all_loops):
                if i != j and self._is_nested_loop(outer_loop, inner_loop):
                    nested_loops.append(inner_loop)
            
            if nested_loops:
                loops['nested_loops'].append({
                    'outer_loop': outer_loop,
                    'nested_loops': nested_loops
                })
    
    def _is_nested_loop(self, outer_loop: Dict[str, Any], inner_loop: Dict[str, Any]) -> bool:
        """判断是否是嵌套循环"""
        outer_blocks = set()
        if 'loop_body' in outer_loop:
            outer_blocks.update(outer_loop['loop_body'])
        if 'loop_header' in outer_loop:
            outer_blocks.add(outer_loop['loop_header'])
        
        inner_blocks = set()
        if 'loop_body' in inner_loop:
            inner_blocks.update(inner_loop['loop_body'])
        if 'loop_header' in inner_loop:
            inner_blocks.add(inner_loop['loop_header'])
        
        return outer_blocks.intersection(inner_blocks)
    
    def analyze_loop_control_flow(self) -> Dict[str, Any]:
        """
        分析循环控制流
        基于C++版本的控制流分析
        
        Returns:
            循环控制流分析结果
        """
        control_flow = {
            'loop_headers': [],
            'loop_exits': [],
            'break_statements': [],
            'continue_statements': [],
            'loop_dependence': []
        }
        
        # 分析所有循环
        loops = self.detect_for_while_loops()
        
        for for_loop in loops['for_loops']:
            self._analyze_loop_control_flow(for_loop, control_flow)
        
        for while_loop in loops['while_loops']:
            self._analyze_loop_control_flow(while_loop, control_flow)
        
        return control_flow
    
    def _analyze_loop_control_flow(self, loop_info: Dict[str, Any], control_flow: Dict[str, Any]) -> None:
        """分析单个循环的控制流"""
        if 'loop_header' in loop_info:
            control_flow['loop_headers'].append(loop_info['loop_header'])
        
        if 'break_blocks' in loop_info:
            control_flow['break_statements'].extend(loop_info['break_blocks'])
        
        if 'continue_blocks' in loop_info:
            control_flow['continue_statements'].extend(loop_info['continue_blocks'])
        
        # 分析循环依赖
        if 'loop_body' in loop_info:
            self._analyze_loop_dependence(loop_info, control_flow)
    
    def _analyze_loop_dependence(self, loop_info: Dict[str, Any], control_flow: Dict[str, Any]) -> None:
        """分析循环依赖关系"""
        loop_body = loop_info.get('loop_body', [])
        if not loop_body:
            return
        
        # 简化的依赖分析
        for i, block1 in enumerate(loop_body):
            for j, block2 in enumerate(loop_body[i+1:], i+1):
                if self._has_control_dependency(block1, block2):
                    control_flow['loop_dependence'].append((block1, block2))
    
    def _has_control_dependency(self, block1: BasicBlock, block2: BasicBlock) -> bool:
        """判断是否存在控制依赖"""
        # 简化实现：检查是否有边连接
        return block2 in block1.successors or block1 in block2.successors
    
    def detect_exception_handling(self) -> Dict[str, Any]:
        """
        检测异常处理结构
        基于C++版本的SETUP_FINALLY_A和SETUP_EXCEPT处理逻辑
        
        Returns:
            检测到的异常处理结构信息字典
        """
        exception_handling = {
            'try_blocks': [],
            'except_blocks': [],
            'finally_blocks': [],
            'nested_exceptions': []
        }
        
        # 遍历所有基本块，寻找异常处理模式
        for block in self.blocks:
            try_block_info = self._analyze_try_block(block)
            if try_block_info:
                exception_handling['try_blocks'].append(try_block_info)
        
        # 寻找except块
        self._detect_except_blocks(exception_handling)
        
        # 寻找finally块
        self._detect_finally_blocks(exception_handling)
        
        # 检测嵌套异常
        self._detect_nested_exceptions(exception_handling)
        
        return exception_handling
    
    def _analyze_try_block(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """
        分析try块
        基于C++版本的SETUP_FINALLY_A和SETUP_EXCEPT分析逻辑
        """
        # 寻找SETUP_FINALLY或SETUP_EXCEPT指令
        setup_instr = None
        for instr in block.instructions:
            if instr.opname in ['SETUP_FINALLY_A', 'SETUP_EXCEPT_A']:
                setup_instr = instr
                break
        
        if not setup_instr:
            return None
        
        try_block_info = {
            'try_block': block,
            'setup_instruction': setup_instr,
            'handler_blocks': [],
            'finally_blocks': [],
            'exception_handlers': []
        }
        
        # 分析异常处理结构
        self._analyze_exception_structure(try_block_info)
        
        return try_block_info
    
    def _analyze_exception_structure(self, try_block_info: Dict[str, Any]) -> None:
        """分析异常处理结构"""
        setup_instr = try_block_info['setup_instruction']
        
        if setup_instr.opname == 'SETUP_FINALLY_A':
            self._analyze_finally_block(try_block_info)
        elif setup_instr.opname == 'SETUP_EXCEPT_A':
            self._analyze_except_handlers(try_block_info)
    
    def _analyze_finally_block(self, try_block_info: Dict[str, Any]) -> None:
        """分析finally块"""
        setup_instr = try_block_info['setup_instruction']
        finally_offset = setup_instr.target
        
        # 寻找finally块
        finally_block = self._find_block_containing_offset(finally_offset)
        if finally_block:
            try_block_info['finally_blocks'].append({
                'finally_block': finally_block,
                'finally_offset': finally_offset
            })
    
    def _analyze_except_handlers(self, try_block_info: Dict[str, Any]) -> None:
        """分析except处理器"""
        setup_instr = try_block_info['setup_instruction']
        handler_offset = setup_instr.target
        
        # 寻找第一个except处理器
        current_block = self._find_block_containing_offset(handler_offset)
        
        while current_block and current_block != try_block_info['try_block']:
            except_handler = self._analyze_single_except_handler(current_block)
            if except_handler:
                try_block_info['exception_handlers'].append(except_handler)
            
            # 寻找下一个except处理器
            current_block = self._find_next_except_handler(current_block)
            
            # 如果遇到跳出try块的范围，停止
            if not current_block or self._is_out_of_try_block(current_block, try_block_info):
                break
    
    def _analyze_single_except_handler(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """分析单个except处理器"""
        # 寻找异常处理开始指令
        except_instr = None
        for instr in block.instructions:
            if instr.opname in ['POP_EXCEPT', 'DUP_TOP']:
                except_instr = instr
                break
        
        if not except_instr:
            return None
        
        # 分析except块内容
        except_handler = {
            'handler_block': block,
            'handler_instruction': except_instr,
            'exception_types': [],
            'handler_body': [],
            'handler_exit': None
        }
        
        # 收集异常类型（简化实现）
        exception_types = self._extract_exception_types(block)
        except_handler['exception_types'] = exception_types
        
        return except_handler
    
    def _extract_exception_types(self, block: BasicBlock) -> List[str]:
        """提取异常类型（简化实现）"""
        # 简化的异常类型提取
        # 在实际实现中需要更复杂的分析
        exception_types = []
        
        for instr in block.instructions:
            if instr.opname == 'LOAD_GLOBAL_A' and instr.arg == 'Exception':
                exception_types.append('Exception')
            elif instr.opname == 'LOAD_GLOBAL_A' and instr.arg == 'ValueError':
                exception_types.append('ValueError')
        
        return exception_types if exception_types else ['Exception']  # 默认Exception
    
    def _find_next_except_handler(self, current_block: BasicBlock) -> Optional[BasicBlock]:
        """寻找下一个except处理器"""
        # 简化实现：查找包含异常处理指令的块
        for block in self.blocks:
            for instr in block.instructions:
                if instr.opname in ['POP_EXCEPT', 'DUP_TOP'] and block != current_block:
                    return block
        return None
    
    def _is_out_of_try_block(self, block: BasicBlock, try_block_info: Dict[str, Any]) -> bool:
        """判断是否超出了try块的范围"""
        # 简化实现：检查块是否在try块之前
        try_block = try_block_info['try_block']
        return block.start_offset < try_block.start_offset
    
    def _detect_except_blocks(self, exception_handling: Dict[str, Any]) -> None:
        """检测except块"""
        for try_block in exception_handling['try_blocks']:
            for handler in try_block.get('exception_handlers', []):
                exception_handling['except_blocks'].append(handler)
    
    def _detect_finally_blocks(self, exception_handling: Dict[str, Any]) -> None:
        """检测finally块"""
        for try_block in exception_handling['try_blocks']:
            for finally_info in try_block.get('finally_blocks', []):
                exception_handling['finally_blocks'].append(finally_info)
    
    def _detect_nested_exceptions(self, exception_handling: Dict[str, Any]) -> None:
        """检测嵌套异常"""
        try_blocks = exception_handling['try_blocks']
        
        for i, outer_try in enumerate(try_blocks):
            nested_exceptions = []
            for j, inner_try in enumerate(try_blocks):
                if i != j and self._is_nested_exception(outer_try, inner_try):
                    nested_exceptions.append(inner_try)
            
            if nested_exceptions:
                exception_handling['nested_exceptions'].append({
                    'outer_try': outer_try,
                    'nested_exceptions': nested_exceptions
                })
    
    def _is_nested_exception(self, outer_try: Dict[str, Any], inner_try: Dict[str, Any]) -> bool:
        """判断是否是嵌套异常"""
        outer_block = outer_try['try_block']
        inner_block = inner_try['try_block']
        
        # 简化判断：内层异常块的偏移量在外层异常块范围内
        return (inner_block.start_offset >= outer_block.start_offset and 
                inner_block.start_offset <= outer_block.end_offset)
    
    def analyze_exception_control_flow(self) -> Dict[str, Any]:
        """
        分析异常控制流
        基于C++版本的控制流分析
        
        Returns:
            异常控制流分析结果
        """
        control_flow = {
            'try_entries': [],
            'exception_handlers': [],
            'finally_entries': [],
            'exception_propagation': []
        }
        
        # 分析所有异常处理
        exceptions = self.detect_exception_handling()
        
        # 分析try块入口
        for try_block in exceptions['try_blocks']:
            control_flow['try_entries'].append(try_block['try_block'])
        
        # 分析异常处理器
        for try_block in exceptions['try_blocks']:
            for handler in try_block.get('exception_handlers', []):
                control_flow['exception_handlers'].append(handler)
        
        # 分析finally块入口
        for try_block in exceptions['try_blocks']:
            for finally_info in try_block.get('finally_blocks', []):
                control_flow['finally_entries'].append(finally_info['finally_block'])
        
        # 分析异常传播
        self._analyze_exception_propagation(exceptions, control_flow)
        
        return control_flow
    
    def _analyze_exception_propagation(self, exceptions: Dict[str, Any], control_flow: Dict[str, Any]) -> None:
        """分析异常传播路径"""
        # 简化实现：分析异常传播路径
        for try_block in exceptions['try_blocks']:
            for handler in try_block.get('exception_handlers', []):
                propagation = {
                    'from_try': try_block['try_block'],
                    'to_handler': handler['handler_block'],
                    'exception_types': handler['exception_types']
                }
                control_flow['exception_propagation'].append(propagation)
    
    def detect_break_continue_jumps(self) -> Dict[str, Any]:
        """
        检测break和continue跳转逻辑
        基于C++版本的控制流分析
        
        Returns:
            检测到的break/continue跳转信息字典
        """
        jumps = {
            'break_statements': [],
            'continue_statements': [],
            'jump_targets': {},
            'loop_dependencies': []
        }
        
        # 遍历所有基本块，寻找break和continue指令
        for block in self.blocks:
            self._analyze_break_continue_statements(block, jumps)
        
        # 分析跳转目标
        self._analyze_jump_targets(jumps)
        
        # 分析循环依赖
        self._analyze_loop_dependencies(jumps)
        
        return jumps
    
    def _analyze_break_continue_statements(self, block: BasicBlock, jumps: Dict[str, Any]) -> None:
        """分析break和continue语句"""
        for instr in block.instructions:
            if instr.opname == 'BREAK_LOOP':
                jumps['break_statements'].append({
                    'block': block,
                    'instruction': instr,
                    'jump_target': instr.target
                })
            elif instr.opname == 'CONTINUE_LOOP':
                jumps['continue_statements'].append({
                    'block': block,
                    'instruction': instr,
                    'jump_target': instr.target
                })
    
    def _analyze_jump_targets(self, jumps: Dict[str, Any]) -> None:
        """分析跳转目标"""
        all_jumps = jumps['break_statements'] + jumps['continue_statements']
        
        for jump in all_jumps:
            target_offset = jump['jump_target']
            target_block = self._find_block_containing_offset(target_offset)
            
            if target_block:
                if target_offset not in jumps['jump_targets']:
                    jumps['jump_targets'][target_offset] = []
                jumps['jump_targets'][target_offset].append({
                    'from_block': jump['block'],
                    'jump_type': 'break' if jump in jumps['break_statements'] else 'continue'
                })
    
    def _analyze_loop_dependencies(self, jumps: Dict[str, Any]) -> None:
        """分析循环依赖"""
        all_loops = self.detect_for_while_loops()
        all_jumps = jumps['break_statements'] + jumps['continue_statements']
        
        for jump in all_jumps:
            jump_block = jump['block']
            jump_target = self._find_block_containing_offset(jump['jump_target'])
            
            if jump_target:
                # 寻找包含跳转目标的循环
                for loop_type in ['for_loops', 'while_loops']:
                    for loop in all_loops.get(loop_type, []):
                        if self._is_jump_dependent_on_loop(jump_block, jump_target, loop):
                            jumps['loop_dependencies'].append({
                                'jump_block': jump_block,
                                'jump_type': 'break' if jump in jumps['break_statements'] else 'continue',
                                'loop': loop,
                                'dependency_type': 'loop_exit' if jump in jumps['break_statements'] else 'loop_continue'
                            })
    
    def _is_jump_dependent_on_loop(self, jump_block: BasicBlock, jump_target: BasicBlock, loop: Dict[str, Any]) -> bool:
        """判断跳转是否依赖于循环"""
        loop_body = loop.get('loop_body', [])
        loop_header = loop.get('loop_header')
        
        # break跳转到循环外部
        if jump_target not in loop_body and jump_target != loop_header:
            return True
        
        # continue跳转到循环头部
        if jump_target == loop_header:
            return True
        
        return False
    
    def get_control_flow_graph(self) -> Dict[int, List[int]]:
        """
        获取控制流图的邻接表表示
        Returns:
            {块索引: [后继块索引列表]}
        """
        cfg = {}
        
        for i, block in enumerate(self.blocks):
            cfg[i] = [self.blocks.index(succ) for succ in block.successors]
        
        return cfg
    
    def print_analysis(self) -> None:
        """打印分析结果"""
        print("控制流分析结果:")
        print("=" * 50)
        
        for i, block in enumerate(self.blocks):
            print(f"块 {i}: {block}")
            print(f"  前驱: {[p.name for p in block.predecessors]}")
            print(f"  后继: {[s.name for s in block.successors]}")
            print(f"  指令数: {len(block.instructions)}")
            if block.instructions:
                print(f"  指令: {[instr.opname for instr in block.instructions[:3]]}{'...' if len(block.instructions) > 3 else ''}")
            print()


def create_simple_if_analysis() -> ControlFlowAnalyzer:
    """
    创建简单的if语句分析示例
    对应测试中的if语句字节码
    """
    instructions = [
        Instruction(0, 151, 'RESUME_A'),
        Instruction(2, 124, 'LOAD_FAST_A', arg=0),
        Instruction(42, 115, 'POP_JUMP_FORWARD_IF_TRUE_A', arg=100, target=100),
        Instruction(46, 100, 'LOAD_CONST_A', arg=0),
        Instruction(50, 1, 'RETURN_VALUE'),
        Instruction(100, 100, 'LOAD_CONST_A', arg=1),
        Instruction(110, 1, 'RETURN_VALUE'),
    ]
    
    return ControlFlowAnalyzer(instructions)


def create_simple_loop_analysis() -> ControlFlowAnalyzer:
    """
    创建简单的循环分析示例
    """
    instructions = [
        Instruction(0, 151, 'RESUME_A'),
        Instruction(2, 100, 'LOAD_CONST_A', arg=0),  # 循环计数
        Instruction(10, 124, 'LOAD_FAST_A', arg=1),  # 循环范围
        Instruction(42, 93, 'FOR_ITER_A', arg=50, target=50),  # 循环迭代
        Instruction(46, 100, 'LOAD_CONST_A', arg=1),  # 循环体
        Instruction(50, 110, 'JUMP_BACKWARD_A', arg=30, target=10),  # 跳转回循环头
        Instruction(60, 1, 'RETURN_VALUE'),
    ]
    
    return ControlFlowAnalyzer(instructions)


if __name__ == "__main__":
    # 示例用法
    print("控制流分析示例")
    print("=" * 40)
    
    # 测试if语句分析
    print("\n1. If语句控制流分析:")
    if_analyzer = create_simple_if_analysis()
    if_blocks = if_analyzer.analyze()
    if_analyzer.print_analysis()
    
    # 测试循环分析
    print("\n2. 循环控制流分析:")
    loop_analyzer = create_simple_loop_analysis()
    loop_blocks = loop_analyzer.analyze()
    loop_analyzer.print_analysis()
    
    # 检测条件分支
    print("\n3. 条件分支检测:")
    conditions = if_analyzer.detect_conditions()
    for block1, block2, cond_type in conditions:
        print(f"  {block1.name} --{cond_type}--> {block2.name}")
    
    # 检测循环
    print("\n4. 循环检测:")
    loops = loop_analyzer.detect_loops()
    for head, tail in loops:
        print(f"  循环: {head.name} -> {tail.name}")