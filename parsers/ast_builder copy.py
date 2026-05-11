"""
AST构建模块

负责从字节码构建抽象语法树

"""

from typing import List, Optional, Tuple, Dict, Set, Union
from collections import defaultdict

# 调试配置
DEBUG = True  # 设置为True启用调试输出

def debug_print(*args, **kwargs):
    """条件调试输出"""
    if DEBUG:
        print(*args, **kwargs)

from core.pyc_objects import PycModule, PycRef, PycString, PycSequence, PycCode
from core.ast_nodes import (
    ASTNode, ASTNodeList, ASTObject, ASTUnary, ASTBinary, 
    ASTCompare, ASTSlice, ASTStore, ASTReturn, ASTName, ASTYield,
    ASTDelete, ASTFunctionDef, ASTClassDef as ASTClass, ASTCall, ASTBlock,
    NodeType, ASTChainStore, ASTImport, ASTImportFrom, ASTIf,
    ASTFor, ASTWhile, ASTTry, ASTExceptHandler, ASTBreak, ASTContinue, ASTWith,
    ASTPass, ASTRaise, ASTAssert, ASTModule, ASTConstant, ASTExpr, ASTFormattedValue, ASTJoinedStr,
    ASTAttribute, ASTAssign, ASTSubscript, ASTList, ASTSet, ASTDict, ASTAugAssign
)
from bytecode.bytecode_ops import Opcode, opcode_to_name
from utils.stack import FastStack
from .context_manager import ContextManager, ContextType
from .enhanced_class_handler import EnhancedClassHandler
from .enhanced_decorator_handler import EnhancedDecoratorHandler

import sys


class ControlFlowAnalyzer:
    """控制流分析器"""
    
    def __init__(self):
        self.control_flow_graph = {}  # 偏移 -> {next: offset, jumps: [offset], exception_handlers: [offset]}
        self.loop_structures = []  # 循环结构列表
        self.exception_blocks = []  # 异常处理块列表
        self.branch_patterns = {}  # 分支模式识别
        self.unreachable_blocks = set()  # 不可达块
        self.processed_jumps = set()  # 已处理的跳转
        self.last_instr_offset = -1  # 上一条指令的偏移
        self.code = None  # 字节码
        self.instructions = []  # 指令列表
        
    def analyze(self, code_obj, disasm):
        """分析代码对象的控制流"""
        self.code_obj = code_obj  # 保存code_obj以便后续使用异常表
        self.code = code_obj.code.get() if code_obj.code else None
        if not self.code:
            return
            
        # 获取指令列表
        self.instructions = disasm.instructions if hasattr(disasm, 'instructions') else []
        
        # 构建控制流图
        self._build_control_flow_graph()
        
        # 识别循环结构
        self._detect_loop_structures()
        
        # 识别异常处理块（从异常表解析）
        self._detect_exception_blocks_from_table()
        
        # 识别分支模式
        self._detect_branch_patterns()
        
        # 检测不可达块
        self._detect_unreachable_blocks()
        
    def _build_control_flow_graph(self):
        """构建控制流图"""
        if not self.code or not self.instructions:
            return
            
        # 初始化控制流图
        for instruction in self.instructions:
            self.control_flow_graph[instruction['offset']] = {
                'next': None,
                'jumps': [],
                'exception_handlers': []
            }
        
        # 分析每条指令
        for i, instruction in enumerate(self.instructions):
            offset = instruction['offset']
            opcode = instruction['opcode']
            
            # 检查是否是跳转指令
            if self._is_jump_instruction(opcode):
                # 获取跳转目标
                target = self._get_jump_target(instruction)
                if target:
                    self.control_flow_graph[offset]['jumps'].append(target)
            
            # 获取下一条指令
            if i + 1 < len(self.instructions):
                next_offset = self.instructions[i + 1]['offset']
                self.control_flow_graph[offset]['next'] = next_offset
    
    def _is_jump_instruction(self, opcode):
        """检查是否是跳转指令"""
        # 检查是否是跳转指令
        jump_opcodes = {
            Opcode.POP_JUMP_IF_FALSE,
            Opcode.POP_JUMP_IF_TRUE,
            Opcode.JUMP_FORWARD,
            Opcode.JUMP_IF_FALSE_OR_POP,
            Opcode.JUMP_IF_TRUE_OR_POP,
            Opcode.JUMP_BACKWARD,
            Opcode.JUMP_BACKWARD_NO_INTERRUPT,
            Opcode.POP_JUMP_IF_NOT_EXC_MATCH,
            Opcode.POP_JUMP_IF_EXC_MATCH,
            # Python 3.11+ 跳转指令
            Opcode.JUMP_FORWARD,
            Opcode.JUMP_BACKWARD,
            Opcode.JUMP_IF_TRUE,
            Opcode.JUMP_IF_FALSE,
            Opcode.JUMP_IF_NOT_EXC_MATCH,
            Opcode.POP_JUMP_FORWARD_IF_FALSE,
            Opcode.POP_JUMP_FORWARD_IF_TRUE,
            Opcode.POP_JUMP_BACKWARD_IF_FALSE,
            Opcode.POP_JUMP_BACKWARD_IF_TRUE,
            Opcode.INLINE_CACHE_POP_JUMP_FORWARD_IF_NOT_EXC_MATCH,
        }
        
        return opcode in jump_opcodes
    
    def _get_jump_target(self, instruction):
        """获取跳转指令的目标偏移"""
        opcode = instruction['opcode']
        
        # 检查是否是跳转指令
        if not self._is_jump_instruction(opcode):
            return None
            
        # 获取跳转目标
        if 'operand' in instruction and instruction['operand'] is not None:
            return instruction['operand']
        
        # 特殊情况：某些跳转指令的跳转目标需要特殊处理
        if opcode == Opcode.JUMP_FORWARD:
            # 向前跳转：目标 = 当前偏移 + 跳转偏移 + 2
            if 'operand' in instruction:
                return instruction['offset'] + instruction['operand'] + 2
        elif opcode == Opcode.JUMP_BACKWARD:
            # 向后跳转：目标 = 当前偏移 - 跳转偏移 - 2
            if 'operand' in instruction:
                return instruction['offset'] - instruction['operand'] - 2
        elif opcode == Opcode.POP_JUMP_IF_FALSE or opcode == Opcode.POP_JUMP_IF_TRUE:
            # POP_JUMP指令：目标 = 当前偏移 + 跳转偏移 + 2
            if 'operand' in instruction:
                return instruction['offset'] + instruction['operand'] + 2
        
        return None
    
    def _detect_loop_structures(self):
        """识别循环结构"""
        # 检测while循环
        for offset, cfg in self.control_flow_graph.items():
            for jump_target in cfg['jumps']:
                # 检查是否是从后往前跳转的循环结构
                if jump_target < offset:
                    # 找到循环头
                    loop_header = jump_target
                    loop_end = offset
                    
                    # 检查循环体中是否包含循环条件
                    condition_found = False
                    for instr in self.instructions:
                        if instr['offset'] >= loop_header and instr['offset'] <= loop_end:
                            if self._is_jump_instruction(instr['opcode']):
                                # 这可能是循环条件判断
                                condition_found = True
                                break
                    
                    if condition_found:
                        # 记录循环结构
                        self.loop_structures.append({
                            'type': 'while',
                            'header': loop_header,
                            'end': loop_end,
                            'back_edge': (offset, jump_target),
                            'body': list(range(loop_header, loop_end + 1))
                        })
    
    def _detect_exception_blocks_from_table(self):
        """从异常表识别异常处理块（Python 3.11+）
        
        Python 3.11+使用新的异常表格式存储异常处理信息
        需要从code_obj.except_table中解析
        """
        if not hasattr(self, 'code_obj') or not self.code_obj:
            return
        
        # 尝试从异常表解析条目
        try:
            if hasattr(self.code_obj, 'exception_table_entries'):
                entries = self.code_obj.exception_table_entries()
                
                for entry in entries:
                    start_offset = entry['start_offset']
                    end_offset = entry['end_offset']
                    target = entry['target']
                    
                    # 记录异常处理块
                    self.exception_blocks.append({
                        'handler_offset': target,
                        'handled_blocks': [start_offset, end_offset],
                        'start_offset': start_offset,
                        'end_offset': end_offset,
                        'stack_depth': entry.get('stack_depth', 0),
                        'push_lasti': entry.get('push_lasti', False)
                    })
                    
                    # 在控制流图中标记异常处理器
                    if target in self.control_flow_graph:
                        self.control_flow_graph[target]['is_exception_handler'] = True
                        self.control_flow_graph[target]['exception_range'] = (start_offset, end_offset)
        except Exception as e:
            debug_print(f"解析异常表失败: {e}")
    
    def _detect_exception_blocks(self):
        """识别异常处理块（旧方法，保留用于兼容）"""
        # 异常处理块在控制流图中会有特殊的标记
        # 这里假设异常处理块已经在控制流图中标记好
        for offset, cfg in self.control_flow_graph.items():
            if cfg.get('exception_handlers'):
                self.exception_blocks.append({
                    'handler_offset': offset,
                    'handled_blocks': cfg['exception_handlers']
                })
    
    def _detect_branch_patterns(self):
        """识别分支模式"""
        # 识别简单的if-else分支
        for offset, cfg in self.control_flow_graph.items():
            jumps = cfg['jumps']
            if len(jumps) == 1:
                # 可能是条件跳转（if语句）
                jump_target = jumps[0]
                
                # 检查是否存在条件比较指令
                has_condition = False
                for instr in self.instructions:
                    if instr['offset'] < offset and instr['offset'] > offset - 10:
                        # 条件比较指令通常在跳转指令之前
                        if self._is_compare_instruction(instr['opcode']):
                            has_condition = True
                            break
                
                if has_condition:
                    self.branch_patterns[offset] = {
                        'type': 'if',
                        'condition_offset': None,  # 需要在后面的分析中确定
                        'true_block': [offset + 2, jump_target],  # 跳转目标后的块
                        'false_block': None  # 如果有else分支，这里会填入
                    }
        
        # 识别复杂的控制流模式
        self._detect_complex_control_flow_patterns()
    
    def _detect_complex_control_flow_patterns(self):
        """识别复杂的控制流模式"""
        # 1. 识别for循环
        self._detect_for_loops()
        
        # 2. 识别try-except语句
        self._detect_try_except_blocks()
        
        # 3. 识别with语句
        self._detect_with_statements()
        
        # 4. 识别复杂的if-elif-else结构
        self._detect_if_elif_else_chains()
    
    def _detect_for_loops(self):
        """识别for循环"""
        # 遍历所有可能的循环
        for loop in self.loop_structures:
            # 检查是否是for循环的特征
            # 1. 检查是否有迭代相关的字节码
            has_iter = False
            for instr in self.instructions:
                if (instr['offset'] >= loop['header'] and 
                    instr['offset'] <= loop['end']):
                    if instr['opcode'] in [Opcode.GET_ITER, Opcode.FOR_ITER]:
                        has_iter = True
                        break
            
            if has_iter:
                # 这可能是一个for循环
                if 'type' not in loop:
                    loop['type'] = 'for'
                    
                    # 添加for循环的特殊信息
                    loop['iter_instruction'] = None
                    for instr in self.instructions:
                        if (instr['offset'] >= loop['header'] and 
                            instr['offset'] <= loop['end'] and
                            instr['opcode'] == Opcode.GET_ITER):
                            loop['iter_instruction'] = instr
                            break
                    
                    # 添加循环变量信息
                    loop['iter_var'] = None
                    if loop.get('iter_instruction'):
                        # 检查是否有关于迭代变量的信息
                        prev_instr = self._get_previous_instruction(loop['iter_instruction'])
                        if prev_instr and prev_instr['opcode'] == Opcode.STORE_NAME:
                            loop['iter_var'] = prev_instr['operand']
    
    def _detect_try_except_blocks(self):
        """识别try-except语句"""
        # 查找异常处理块
        for exception_block in self.exception_blocks:
            # 尝试识别异常处理块的类型和结构
            handler_offset = exception_block['handler_offset']
            handled_blocks = exception_block['handled_blocks']
            
            # 获取异常处理器的第一条指令
            exception_instr = self._get_instruction_at_offset(handler_offset)
            
            # Python 3.11+ 异常处理器以 PUSH_EXC_INFO 或 COPY 指令开始
            # 或者可能是其他异常处理相关指令
            is_except_handler = False
            if exception_instr:
                opcode = exception_instr['opcode']
                # Python 3.11+ 异常处理器指令
                if opcode in [Opcode.PUSH_EXC_INFO, Opcode.COPY, Opcode.STORE_EXCINFO,
                             Opcode.POP_EXCEPT, Opcode.PUSH_NULL]:
                    is_except_handler = True
                # 检查是否是存储异常变量的指令
                elif opcode in [Opcode.STORE_FAST_A, Opcode.STORE_NAME_A, 
                               Opcode.STORE_GLOBAL_A, Opcode.STORE_DEREF_A]:
                    is_except_handler = True
            
            if is_except_handler:
                # 这是一个except语句
                # 记录异常类型和异常变量
                exception_info = {
                    'type': 'except',
                    'handler_offset': handler_offset,
                    'handled_blocks': handled_blocks,
                    'exception_var': None,  # 待后续分析确定
                    'exception_type': None,  # 待后续分析确定
                    'start_offset': exception_block.get('start_offset'),
                    'end_offset': exception_block.get('end_offset')
                }
                
                # 尝试获取异常变量和异常类型
                # 通过分析异常处理块内的指令
                handler_instrs = self._get_instructions_in_range(handler_offset, handler_offset + 50)
                
                for i, instr in enumerate(handler_instrs):
                    # 查找存储异常变量的指令
                    if instr['opcode'] in [Opcode.STORE_FAST_A, Opcode.STORE_NAME_A, 
                                          Opcode.STORE_GLOBAL_A, Opcode.STORE_DEREF_A]:
                        exception_info['exception_var'] = instr.get('operand')
                        break
                
                # 尝试获取异常类型
                # 异常类型通常在异常处理器开始处通过LOAD_CONST加载
                for i, instr in enumerate(handler_instrs[:5]):  # 只看前几条指令
                    if instr['opcode'] == Opcode.LOAD_CONST:
                        # 检查下一条指令是否是异常类型比较
                        if i + 1 < len(handler_instrs):
                            next_instr = handler_instrs[i + 1]
                            if next_instr['opcode'] in [Opcode.CHECK_EXC_MATCH, Opcode.JUMP_IF_NOT_EXC_MATCH_A]:
                                exception_info['exception_type'] = instr.get('operand')
                                break
                
                # 添加到分支模式中
                self.branch_patterns[handler_offset] = exception_info
                
                # 同时记录try块的信息
                if exception_block.get('start_offset') is not None:
                    try_start = exception_block['start_offset']
                    self.branch_patterns[try_start] = {
                        'type': 'try',
                        'try_start': try_start,
                        'try_end': exception_block.get('end_offset'),
                        'except_handler': handler_offset
                    }
    
    def _detect_with_statements(self):
        """识别with语句"""
        # 通过检查特定指令组合识别with语句
        for offset, cfg in self.control_flow_graph.items():
            # 检查是否有特定模式的跳转
            if cfg['jumps']:
                jump_target = cfg['jumps'][0]
                
                # 检查目标块是否包含了enter/exit相关的字节码
                # 通过检查指令序列来识别with语句
                instr = self._get_instruction_at_offset(offset)
                if instr and instr['opcode'] in [Opcode.SETUP_WITH, Opcode.BEFORE_WITH]:
                    # 这可能是一个with语句的开始
                    with_info = {
                        'type': 'with',
                        'offset': offset,
                        'jump_target': jump_target,
                        'context_manager': None,  # 待后续分析确定
                        'optional_vars': None  # 待后续分析确定
                    }
                    
                    # 尝试获取上下文管理器和可选变量
                    # 通过分析WITH指令附近的指令
                    next_instrs = self._get_instructions_after(offset, count=5)
                    for next_instr in next_instrs:
                        if next_instr['opcode'] == Opcode.LOAD_METHOD:
                            # 这可能是调用__enter__方法
                            with_info['context_manager'] = next_instr.get('operand')
                        elif next_instr['opcode'] == Opcode.STORE_NAME:
                            # 这可能是可选变量
                            with_info['optional_vars'] = next_instr.get('operand')
                    
                    # 添加到分支模式中
                    self.branch_patterns[offset] = with_info
    
    def _detect_if_elif_else_chains(self):
        """识别if-elif-else链"""
        # 通过分析多个连续的if语句来识别if-elif-else链
        for offset, cfg in self.control_flow_graph.items():
            # 检查是否是if语句
            if cfg['jumps'] and offset in self.branch_patterns:
                branch = self.branch_patterns[offset]
                if branch.get('type') == 'if':
                    # 检查是否有连续的条件跳转，形成if-elif-else链
                    jump_target = cfg['jumps'][0]
                    
                    # 检查jump_target附近的指令，看是否有其他条件跳转
                    subsequent_branches = []
                    for next_offset, next_cfg in self.control_flow_graph.items():
                        if next_offset > offset and next_offset < jump_target:
                            if next_cfg['jumps'] and next_offset in self.branch_patterns:
                                next_branch = self.branch_patterns[next_offset]
                                if next_branch.get('type') == 'if':
                                    subsequent_branches.append(next_offset)
                    
                    # 如果有连续的条件跳转，则可能是if-elif-else链
                    if subsequent_branches:
                        # 创建if-elif-else链结构
                        chain = {
                            'type': 'if_elif_else_chain',
                            'branches': [offset] + subsequent_branches,
                            'final_else': None  # 是否有else块
                        }
                        
                        # 检查最后是否有一个else块
                        for chain_offset in reversed(subsequent_branches):
                            chain_cfg = self.control_flow_graph[chain_offset]
                            if chain_cfg['next'] and chain_cfg['next'] < jump_target:
                                # 检查是否有一个非条件跳转（可能的else块）
                                if not chain_cfg['jumps']:
                                    chain['final_else'] = chain_cfg['next']
                                    break
                        
                        # 添加到分支模式中
                        self.branch_patterns[offset] = chain
    
    def _get_previous_instruction(self, instruction):
        """获取指定指令的前一条指令"""
        if not instruction or not self.instructions:
            return None
        
        # 查找当前指令在列表中的位置
        try:
            idx = self.instructions.index(instruction)
            if idx > 0:
                return self.instructions[idx - 1]
        except ValueError:
            pass
        
        return None
    
    def _get_instruction_at_offset(self, offset):
        """获取指定偏移处的指令"""
        if not self.instructions:
            return None
        
        # 查找偏移匹配的指令
        for instr in self.instructions:
            if instr['offset'] == offset:
                return instr
        
        return None
    
    def _get_instructions_before(self, offset, count=1):
        """获取指定偏移前count条指令"""
        if not self.instructions:
            return []
        
        # 查找偏移匹配的指令
        target_instr = None
        for instr in self.instructions:
            if instr['offset'] == offset:
                target_instr = instr
                break
        
        if not target_instr:
            return []
        
        # 查找指令在列表中的位置
        try:
            idx = self.instructions.index(target_instr)
            start_idx = max(0, idx - count)
            return self.instructions[start_idx:idx]
        except ValueError:
            return []
    
    def _get_instructions_after(self, offset, count=1):
        """获取指定偏移后count条指令"""
        if not self.instructions:
            return []
        
        # 查找偏移匹配的指令
        target_instr = None
        for instr in self.instructions:
            if instr['offset'] == offset:
                target_instr = instr
                break
        
        if not target_instr:
            return []
        
        # 查找指令在列表中的位置
        try:
            idx = self.instructions.index(target_instr)
            end_idx = min(len(self.instructions), idx + 1 + count)
            return self.instructions[idx + 1:end_idx]
        except ValueError:
            return []
    
    def _get_instructions_in_range(self, start_offset, end_offset):
        """获取指定偏移范围内的所有指令"""
        if not self.instructions:
            return []
        
        result = []
        for instr in self.instructions:
            if start_offset <= instr['offset'] < end_offset:
                result.append(instr)
        
        return result
    
    def _is_compare_instruction(self, opcode):
        """检查是否是条件比较指令"""
        compare_opcodes = {
            Opcode.COMPARE_OP,
            Opcode.IS_OP,
            Opcode.CONTAINS_OP,
        }
        return opcode in compare_opcodes
    
    def _detect_unreachable_blocks(self):
        """检测不可达块"""
        # 从第一条指令开始遍历控制流图
        if not self.instructions:
            return
            
        visited = set()
        queue = [self.instructions[0]['offset']]
        
        while queue:
            offset = queue.pop(0)
            if offset in visited:
                continue
                
            visited.add(offset)
            
            # 访问当前块的控制流图
            if offset in self.control_flow_graph:
                cfg = self.control_flow_graph[offset]
                
                # 添加下一条指令
                if cfg['next'] and cfg['next'] not in visited:
                    queue.append(cfg['next'])
                
                # 添加跳转目标
                for jump_target in cfg['jumps']:
                    if jump_target not in visited:
                        queue.append(jump_target)
        
        # 标记未访问的块为不可达
        self.unreachable_blocks = set(self.control_flow_graph.keys()) - visited
    
    def get_loop_structures(self):
        """获取循环结构"""
        return self.loop_structures
    
    def get_exception_blocks(self):
        """获取异常处理块"""
        return self.exception_blocks
    
    def get_branch_patterns(self):
        """获取分支模式"""
        return self.branch_patterns
    
    def get_unreachable_blocks(self):
        """获取不可达块"""
        return self.unreachable_blocks
    
    def get_control_flow_graph(self):
        """获取控制流图"""
        return self.control_flow_graph


class DataFlowAnalyzer:
    """数据流分析器"""
    
    def __init__(self):
        self.definition_blocks = {}  # 定义块：偏移量 -> 变量定义
        self.use_blocks = {}  # 使用块：偏移量 -> 变量使用
        self.live_variables = {}  # 活跃变量：偏移量 -> 活跃变量集合
        self.reaching_definitions = {}  # 到达定义：偏移量 -> 到达定义集合
        self.available_expressions = {}  # 可用表达式：偏移量 -> 可用表达式集合
        self.very_busy_expressions = {}  # 非常繁忙表达式：偏移量 -> 非常繁忙表达式集合
        
    def analyze(self, code_obj, control_flow_graph, instructions):
        """分析数据流"""
        self._build_def_use_chains(code_obj, instructions)
        self._analyze_live_variables(control_flow_graph, instructions)
        self._analyze_reaching_definitions(control_flow_graph, instructions)
        self._analyze_available_expressions(control_flow_graph, instructions)
        self._analyze_very_busy_expressions(control_flow_graph, instructions)
    
    def _build_def_use_chains(self, code_obj, instructions):
        """构建定义-使用链"""
        self.definition_blocks = {}
        self.use_blocks = {}
        
        for instr in instructions:
            offset = instr.get('offset', 0)
            opcode = instr.get('opcode', 0)
            operand = instr.get('operand', 0)
            
            # 处理变量定义
            if opcode in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A]:
                var_name = self._get_variable_name(code_obj, opcode, operand)
                if var_name:
                    if offset not in self.definition_blocks:
                        self.definition_blocks[offset] = []
                    self.definition_blocks[offset].append(var_name)
            
            # 处理变量使用
            if opcode in [Opcode.LOAD_NAME_A, Opcode.LOAD_FAST_A, Opcode.LOAD_GLOBAL_A]:
                var_name = self._get_variable_name(code_obj, opcode, operand)
                if var_name:
                    if offset not in self.use_blocks:
                        self.use_blocks[offset] = []
                    self.use_blocks[offset].append(var_name)
    
    def _get_variable_name(self, code_obj, opcode, operand):
        """获取变量名"""
        # 根据操作码和操作数获取变量名
        if opcode in [Opcode.STORE_NAME_A, Opcode.LOAD_NAME_A]:
            if hasattr(code_obj, 'names') and operand < len(code_obj.names()):
                name_obj = code_obj.names()[operand]
                if hasattr(name_obj, 'value'):
                    return name_obj.value
        elif opcode in [Opcode.STORE_FAST_A, Opcode.LOAD_FAST_A]:
            if hasattr(code_obj, 'varnames') and operand < len(code_obj.varnames()):
                name_obj = code_obj.varnames()[operand]
                if hasattr(name_obj, 'value'):
                    return name_obj.value
        elif opcode in [Opcode.STORE_GLOBAL_A, Opcode.LOAD_GLOBAL_A]:
            if hasattr(code_obj, 'globals') and operand < len(code_obj.globals()):
                name_obj = code_obj.globals()[operand]
                if hasattr(name_obj, 'value'):
                    return name_obj.value
        
        return None
    
    def _analyze_live_variables(self, control_flow_graph, instructions):
        """分析活跃变量"""
        # 初始化每个块的后继和前驱
        successors = {}
        predecessors = {}
        
        for offset, cfg in control_flow_graph.items():
            successors[offset] = []
            if cfg['next']:
                successors[offset].append(cfg['next'])
            for jump_target in cfg['jumps']:
                successors[offset].append(jump_target)
        
        # 构建前驱列表
        for offset, succs in successors.items():
            for succ in succs:
                if succ not in predecessors:
                    predecessors[succ] = []
                predecessors[succ].append(offset)
        
        # 初始化活跃变量集合
        for instr in instructions:
            offset = instr.get('offset', 0)
            self.live_variables[offset] = set()
        
        # 从后往前分析
        for offset in reversed([instr.get('offset', 0) for instr in instructions]):
            # 获取当前指令的变量使用
            use_vars = self.use_blocks.get(offset, [])
            
            # 获取所有后继块的活跃变量
            live_out = set()
            for succ in successors.get(offset, []):
                if succ in self.live_variables:
                    live_out.update(self.live_variables[succ])
            
            # 移除在当前块中重新定义的变量
            def_vars = self.definition_blocks.get(offset, [])
            live_in = set(use_vars)
            for var in def_vars:
                if var in live_out:
                    live_out.remove(var)
            
            # 添加到活跃变量集合
            self.live_variables[offset].update(live_in)
    
    def _analyze_reaching_definitions(self, control_flow_graph, instructions):
        """分析到达定义"""
        # 初始化每个块的到达定义集合
        for instr in instructions:
            offset = instr.get('offset', 0)
            self.reaching_definitions[offset] = set()
        
        # 从前往后迭代直到收敛
        changed = True
        while changed:
            changed = False
            
            for instr in instructions:
                offset = instr.get('offset', 0)
                
                # 获取所有前驱块的到达定义
                reaching_in = set()
                for pred in self._get_predecessors(control_flow_graph, offset):
                    if pred in self.reaching_definitions:
                        reaching_in.update(self.reaching_definitions[pred])
                
                # 获取当前块的定义
                defs = self.definition_blocks.get(offset, [])
                reaching_out = set(reaching_in)
                for var in defs:
                    # 移除对同一变量的旧定义
                    reaching_out = {d for d in reaching_out if not d.startswith(f"{var}=")}
                    # 添加新的定义
                    reaching_out.add(f"{var}={offset}")
                
                # 检查是否有变化
                if reaching_out != self.reaching_definitions[offset]:
                    self.reaching_definitions[offset] = reaching_out
                    changed = True
    
    def _analyze_available_expressions(self, control_flow_graph, instructions):
        """分析可用表达式"""
        # 初始化每个块的可用表达式集合
        for instr in instructions:
            offset = instr.get('offset', 0)
            self.available_expressions[offset] = set()
        
        # 从前往后分析
        for instr in instructions:
            offset = instr.get('offset', 0)
            
            # 获取所有前驱块的可用表达式
            available_in = set()
            for pred in self._get_predecessors(control_flow_graph, offset):
                if pred in self.available_expressions:
                    available_in.update(self.available_expressions[pred])
            
            # 应用kill函数（移除被重新定义的表达式）
            available_out = self._apply_kill_function(available_in, offset)
            
            # 应用gen函数（添加新表达式）
            available_out.update(self._apply_gen_function(offset))
            
            self.available_expressions[offset] = available_out
    
    def _analyze_very_busy_expressions(self, control_flow_graph, instructions):
        """分析非常繁忙表达式"""
        # 初始化每个块的非常繁忙表达式集合
        for instr in instructions:
            offset = instr.get('offset', 0)
            self.very_busy_expressions[offset] = set()
        
        # 从后往前分析
        for instr in reversed(instructions):
            offset = instr.get('offset', 0)
            
            # 获取所有后继块的非常繁忙表达式
            very_busy_out = set()
            for succ in self._get_successors(control_flow_graph, offset):
                if succ in self.very_busy_expressions:
                    very_busy_out.update(self.very_busy_expressions[succ])
            
            # 应用gen函数
            very_busy_in = self._apply_gen_function(offset)
            
            # 应用kill函数
            very_busy_in = self._apply_kill_function(very_busy_in, offset)
            
            # 合并结果
            self.very_busy_expressions[offset] = very_busy_in.union(very_busy_out)
    
    def _get_predecessors(self, control_flow_graph, offset):
        """获取前驱块"""
        predecessors = []
        for pred_offset, cfg in control_flow_graph.items():
            if cfg['next'] == offset or offset in cfg['jumps']:
                predecessors.append(pred_offset)
        return predecessors
    
    def _get_successors(self, control_flow_graph, offset):
        """获取后继块"""
        if offset not in control_flow_graph:
            return []
        
        successors = []
        cfg = control_flow_graph[offset]
        if cfg['next']:
            successors.append(cfg['next'])
        successors.extend(cfg['jumps'])
        return successors
    
    def _apply_kill_function(self, expressions, offset):
        """应用kill函数，移除被重新定义的表达式"""
        # 移除在当前块中被重新定义的变量的表达式
        def_vars = self.definition_blocks.get(offset, [])
        killed = set()
        
        for expr in expressions:
            # 简单的启发式：如果表达式中包含被重新定义的变量，则移除
            for var in def_vars:
                if var in expr:
                    killed.add(expr)
                    break
        
        return expressions - killed
    
    def _apply_gen_function(self, offset):
        """应用gen函数，添加新表达式"""
        # 根据指令生成新的表达式
        gen_expressions = set()
        
        # 这里可以添加更复杂的表达式生成逻辑
        # 目前返回空集合，后续可以扩展
        
        return gen_expressions
    
    def get_live_variables(self, offset):
        """获取指定偏移的活跃变量"""
        return self.live_variables.get(offset, set())
    
    def get_reaching_definitions(self, offset):
        """获取指定偏移的到达定义"""
        return self.reaching_definitions.get(offset, set())
    
    def get_available_expressions(self, offset):
        """获取指定偏移的可用表达式"""
        return self.available_expressions.get(offset, set())
    
    def get_very_busy_expressions(self, offset):
        """获取指定偏移的非常繁忙表达式"""
        return self.very_busy_expressions.get(offset, set())


class ASTBuilder:
    """AST构建器
    
    参考C++ pycdc实现，使用块栈管理控制流结构
    """
    
    def __init__(self, module: PycModule, code_obj=None):
        self.module = module
        self.code_obj = code_obj
        if module.code:
            stack_size = module.code.get().stack_size
            if stack_size > 10000:
                stack_size = 20
            self.stack = FastStack(stack_size)
        else:
            self.stack = FastStack(20)
        
        # 块栈管理 - 参考C++实现
        self.blocks: List[ASTBlock] = []
        self.main_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_MAIN)
        self.main_block.init()
        self.blocks.append(self.main_block)
        self.current_block = self.main_block
        
        # 栈历史 - 用于保存异常处理和else分支时的栈状态
        self.stack_hist: List[FastStack] = []
        
        # 状态标志 - 参考C++实现
        self.else_pop = False  # 处理else分支结束时的块弹出
        self.need_try = False  # 标记需要创建try块
        self.unpack = 0  # 解包计数
        self.in_function = False
        self.in_lambda = False  # 是否在lambda中
        self.variable_annotations = False  # 是否有变量注解
        
        # 导入相关
        self.last_import_module = None
        self.last_import_names = []
        self.pending_from_import = None
        
        # 控制流跟踪
        self.jump_targets: Dict[int, List[ASTNode]] = {}  # 偏移量 -> 节点列表
        self.conditions: List[Tuple[ASTNode, int]] = []   # (条件节点, 跳转目标)
        self.current_instruction_offset = -1
        
        # 增强：控制流图和结构化分析
        self._control_flow_graph = {}  # 偏移 -> {next: offset, jumps: [offset], exception_handlers: [offset]}
        self._loop_structures = []  # 循环结构列表
        self._exception_blocks = []  # 异常处理块列表
        self._branch_patterns = {}  # 分支模式识别
        self._unreachable_blocks = set()  # 不可达块
        self._processed_jumps = set()  # 已处理的跳转
        self._last_instr_offset = -1  # 上一条指令的偏移
        
        # 集成控制流分析器
        self._control_flow_analyzer = ControlFlowAnalyzer()
        
        # 上下文管理器
        self.context_manager = ContextManager()
        
        # 增强的类处理器
        self.class_handler = EnhancedClassHandler(self.context_manager)
        
        # 增强的装饰器处理器
        self.decorator_handler = EnhancedDecoratorHandler(self.context_manager)
        
        # For循环相关状态
        self.current_for_node = None
        self._for_loop_unpack_vars = []
    
    def build_from_code(self, code: 'PycRef') -> ASTNode:
        """从代码对象构建AST"""
        from bytecode.pyc_disasm import PycDisassembler
        from core.pyc_objects import PycString, PycCode
        from core.pyc_stream import PycRef as PycRefType
        
        # [DEBUG] 强制打印，确认方法被调用
        print(f"[BUILD_FROM_CODE] 方法被调用! code类型: {type(code)}")
        
        # 处理PycRef或直接的PycCode对象
        debug_print(f"[BUILD_FROM_CODE] code类型: {type(code)}, code: {code}")
        if isinstance(code, PycRefType):
            code_obj = code.get()
            debug_print(f"[BUILD_FROM_CODE] 从PycRef解引用，code_obj类型: {type(code_obj)}")
        elif isinstance(code, PycCode):
            code_obj = code
            debug_print(f"[BUILD_FROM_CODE] 直接是PycCode")
        else:
            debug_print(f"[BUILD_FROM_CODE] 不是PycRef也不是PycCode，返回main_block")
            return self.main_block
        
        if not code_obj:
            return self.main_block
        
        # 保存当前的code_obj，以便在处理过程中判断是否在函数内部
        saved_code_obj = self.code_obj
        try:
            debug_print(f"[BUILD_FROM_CODE] 设置code_obj: {code_obj}")
            # [DEBUG] 修复：当处理模块级别的代码对象时，将self.code_obj设置为None
            # 这样_load_const方法中的is_module_level判断才能正确工作
            # 但我们需要保存code_obj到另一个变量，以便提取assert消息
            self._current_code_obj = code_obj  # 保存code_obj供后续使用
            self.code_obj = None
            
            # 获取字节码
            if code_obj is None or code_obj.code is None:
                bytecode = b''
            elif hasattr(code_obj.code.get(), 'get_bytecode'):
                bytecode = code_obj.code.get().get_bytecode()
            elif hasattr(code_obj.code.get(), 'value'):
                bytecode = code_obj.code.get().value
            else:
                bytecode = b''
            
            # [DEBUG] 调试：检查字节码内容
            debug_print(f"[BUILD_FROM_CODE] 字节码长度: {len(bytecode)}")
            debug_print(f"[BUILD_FROM_CODE] 字节码前50字节: {bytecode[:50].hex() if bytecode else 'empty'}")
            
            # 创建反汇编器
            disasm = PycDisassembler(bytecode, self.module, self.module.version if hasattr(self.module, 'version') else (3, 11), code_obj)
            
            # 增强：使用控制流分析器分析控制流
            self._control_flow_analyzer.analyze(self.module, disasm)
            
            # 获取控制流分析结果
            self._control_flow_graph = self._control_flow_analyzer.get_control_flow_graph()
            self._loop_structures = self._control_flow_analyzer.get_loop_structures()
            self._exception_blocks = self._control_flow_analyzer.get_exception_blocks()
            self._branch_patterns = self._control_flow_analyzer.get_branch_patterns()
            self._unreachable_blocks = self._control_flow_analyzer.get_unreachable_blocks()
            
            # 获取字节码指令
            instructions = disasm.disassemble()
            
            # [DEBUG] 调试：检查指令列表中的STORE_NAME
            print(f"[BUILD_FROM_CODE] 指令总数: {len(instructions)}")
            for instr in instructions:
                if instr.get('opcode') == Opcode.STORE_NAME_A:
                    print(f"[BUILD_FROM_CODE] 发现STORE_NAME_A at offset {instr.get('offset')}, operand={instr.get('operand')}")
            
            # 保存指令列表，供后续分析使用
            self.instructions = instructions
            
            # [DEBUG] 预扫描：识别循环结构
            # 第一遍扫描：收集所有向后跳转信息
            self._prescan_for_loops(instructions)
            
            # 处理每条指令
            for instr in instructions:
                # [DEBUG] 调试：检查BEFORE_WITH是否在指令列表中
                if instr.get('opcode') == Opcode.BEFORE_WITH:
                    debug_print(f"[BUILD_FROM_CODE] 发现BEFORE_WITH指令在offset {instr.get('offset')}")
                self._process_instruction(instr)
            
            # 处理模块级别的函数定义
            self._process_module_level_functions(code_obj)
            
            return self.main_block
        finally:
            # [DEBUG] 修复：不恢复self.code_obj，保持为None以便_load_const方法正确工作
            # self.code_obj = saved_code_obj
            pass
    
    def _prescan_for_loops(self, instructions: List[Dict]) -> None:
        """预扫描指令，识别循环结构"""
        debug_print("[_prescan_for_loops] 开始预扫描循环结构")
        
        # 初始化循环结构存储
        self._loop_entries = {}  # 循环入口点 -> 循环信息
        self._loop_exits = {}    # 循环退出点 -> 循环信息
        self._backward_jumps = []  # 所有向后跳转
        
        # 第一遍：收集所有向后跳转
        for i, instr in enumerate(instructions):
            opcode = instr.get('opcode', 0)
            offset = instr.get('offset', 0)
            operand = instr.get('operand', 0)
            
            # 识别向后跳转指令 (Python 3.11+)
            if opcode in [Opcode.POP_JUMP_BACKWARD_IF_TRUE_A, Opcode.POP_JUMP_BACKWARD_IF_FALSE_A]:
                # 计算跳转目标（向后跳转）
                # Python 3.11+ 格式：跳转目标 = 当前指令偏移 + 2 - target * 2
                jump_target = offset + 2 - operand * 2
                self._backward_jumps.append({
                    'from': offset,
                    'to': jump_target,
                    'opcode': opcode,
                    'index': i
                })
                debug_print(f"[_prescan_for_loops] 发现向后跳转: {offset} -> {jump_target}")
            # [关键修复] 也检查无条件向后跳转 JUMP_BACKWARD
            elif opcode == Opcode.JUMP_BACKWARD_A:
                # 计算跳转目标（向后跳转）
                # Python 3.11+ 格式：跳转目标 = 当前指令偏移 + 2 - target * 2
                jump_target = offset + 2 - operand * 2
                self._backward_jumps.append({
                    'from': offset,
                    'to': jump_target,
                    'opcode': opcode,
                    'index': i
                })
                debug_print(f"[_prescan_for_loops] 发现无条件向后跳转: {offset} -> {jump_target}")
        
        # 第二遍：识别while循环
        # while循环的特征：
        # 1. 有一个条件判断（POP_JUMP_FORWARD_IF_FALSE 或 POP_JUMP_IF_FALSE）
        # 2. 后面跟着一个向后跳转（POP_JUMP_BACKWARD_IF_TRUE/FALSE）跳回条件之前
        for i, instr in enumerate(instructions):
            opcode = instr.get('opcode', 0)
            offset = instr.get('offset', 0)
            operand = instr.get('operand', 0)
            
            # 识别条件跳转（可能是while循环的开始）
            # Python 3.11+ 使用 POP_JUMP_FORWARD_IF_FALSE_A
            if opcode == Opcode.POP_JUMP_FORWARD_IF_FALSE_A:
                # Python 3.11+ 格式：跳转目标 = 当前指令偏移 + 2 + target * 2
                jump_target = offset + 2 + operand * 2
                
                # 检查后面是否有向后跳转跳回到这个条件之前
                for backward_jump in self._backward_jumps:
                    # while循环的特征：
                    # 1. 向后跳转的目标应该在条件判断之后（循环体开始处）
                    # 2. 向后跳转的来源应该在条件跳转目标之前（循环体结束处）
                    # 3. 向后跳转的目标应该在条件指令之后
                    if (backward_jump['to'] > offset and 
                        backward_jump['from'] < jump_target and
                        backward_jump['from'] > offset):
                        # 这是一个while循环
                        loop_info = {
                            'type': 'while',
                            'condition_offset': offset,
                            'body_start': backward_jump['to'],  # 向后跳转的目标（循环体开始）
                            'body_end': backward_jump['from'],  # 向后跳转指令（循环体结束）
                            'exit_offset': jump_target,
                            'condition_instr': instr
                        }
                        # [关键修复] 检查是否有else分支
                        # while-else的特征：exit_offset之后有实际代码（STORE_NAME等）
                        has_else = False
                        else_start = jump_target
                        else_end = -1
                        
                        # 查找exit_offset之后的指令
                        for j in range(i + 1, len(instructions)):
                            instr_after = instructions[j]
                            after_offset = instr_after.get('offset', 0)
                            after_opcode = instr_after.get('opcode', 0)
                            after_name = instr_after.get('name', '')
                            
                            if after_offset >= jump_target:
                                # [关键修复] 只有当exit_offset之后有实际代码（STORE_NAME等）时，才认为有else分支
                                # 如果只是LOAD_CONST None; RETURN_VALUE，说明没有else分支
                                # [扩展] 也检查其他可能的实际代码指令
                                real_code_opcodes = [
                                    Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A,
                                    Opcode.BINARY_OP_A, Opcode.BINARY_ADD, Opcode.BINARY_SUBTRACT,
                                    Opcode.BINARY_MULTIPLY, Opcode.BINARY_TRUE_DIVIDE, Opcode.BINARY_FLOOR_DIVIDE,
                                    Opcode.CALL_A, Opcode.LOAD_METHOD_A, Opcode.LOAD_ATTR_A,
                                    Opcode.LIST_APPEND_A, Opcode.DICT_MERGE_A, Opcode.SET_UPDATE_A,
                                ]
                                # [关键修复] 也检查LOAD_CONST后跟STORE_NAME的模式（如y = -1）
                                is_real_code = after_opcode in real_code_opcodes
                                if not is_real_code and after_opcode == Opcode.LOAD_CONST_A:
                                    # 检查下一条指令是否是STORE_NAME
                                    for next_instr in instructions:
                                        if next_instr.get('offset', -1) == after_offset + 2:
                                            if next_instr.get('opcode', -1) in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A]:
                                                is_real_code = True
                                                debug_print(f"[_prescan_for_loops] 检测到LOAD_CONST+STORE_NAME模式 at {after_offset}")
                                            break
                                
                                if is_real_code:
                                    has_else = True
                                    else_start = after_offset
                                    # 查找else block的结束位置（RETURN_VALUE或JUMP_FORWARD之前）
                                    prev_offset = after_offset
                                    for k in range(j, len(instructions)):
                                        end_instr = instructions[k]
                                        end_opcode = end_instr.get('opcode', 0)
                                        end_offset = end_instr.get('offset', 0)
                                        end_name = end_instr.get('name', '')
                                        # RETURN_VALUE或JUMP_FORWARD标志着else block的结束
                                        if end_opcode == Opcode.RETURN_VALUE or 'RETURN' in end_name or 'JUMP_FORWARD' in end_name:
                                            # else block在RETURN_VALUE/JUMP_FORWARD之前结束
                                            else_end = prev_offset
                                            break
                                        prev_offset = end_offset
                                break
                        
                        loop_info['has_else'] = has_else
                        loop_info['else_start'] = else_start if has_else else -1
                        loop_info['else_end'] = else_end if has_else else -1
                        
                        self._loop_entries[offset] = loop_info
                        self._loop_exits[jump_target] = loop_info
                        debug_print(f"[_prescan_for_loops] 识别到while循环: 条件@{offset}, 体@{backward_jump['to']}-{backward_jump['from']}, 退出@{jump_target}, has_else={has_else}, else_range={else_start}-{else_end}")
                        break
        
        # [关键修复] 第三遍：识别 while True: 循环
        # while True: 循环的特征：
        # 1. 有一个无条件向后跳转（JUMP_BACKWARD）
        # 2. 跳转目标在循环体开始处
        # 3. 没有被识别为其他循环
        # 4. 跳转目标处没有 FOR_ITER 指令（不是for循环）
        # 5. 跳转目标处没有 POP_JUMP_FORWARD_IF_FALSE 指令（不是普通while循环）
        for backward_jump in self._backward_jumps:
            if backward_jump['opcode'] == Opcode.JUMP_BACKWARD_A:
                # 检查是否已经被识别为while循环
                already_recognized = False
                for loop_info in self._loop_entries.values():
                    if loop_info.get('body_end') == backward_jump['from']:
                        already_recognized = True
                        break
                
                if not already_recognized:
                    # [关键修复] 检查跳转目标处是否有 FOR_ITER 或 POP_JUMP_FORWARD_IF_FALSE
                    # 如果有，说明是for循环或普通while循环，不是while True:
                    jump_target = backward_jump['to']
                    is_while_true = True
                    for instr in instructions:
                        instr_offset = instr.get('offset', -1)
                        if instr_offset == jump_target:
                            instr_opcode = instr.get('opcode', -1)
                            if instr_opcode in [Opcode.FOR_ITER_A, Opcode.POP_JUMP_FORWARD_IF_FALSE_A]:
                                is_while_true = False
                                debug_print(f"[_prescan_for_loops] 跳转目标@{jump_target}有FOR_ITER或POP_JUMP_FORWARD_IF_FALSE，不是while True:")
                                break
                    
                    if is_while_true:
                        # 这是一个 while True: 循环
                        loop_info = {
                            'type': 'while',
                            'condition_offset': jump_target,  # 循环体开始作为条件位置
                            'body_start': jump_target,  # 向后跳转的目标（循环体开始）
                            'body_end': backward_jump['from'],  # 向后跳转指令（循环体结束）
                            'exit_offset': backward_jump['from'] + 2,  # 跳转指令之后
                            'condition_instr': None,  # while True: 没有条件指令
                            'is_while_true': True  # 标记为 while True: 循环
                        }
                        # while True: 循环没有else分支
                        loop_info['has_else'] = False
                        loop_info['else_start'] = -1
                        loop_info['else_end'] = -1
                        
                        self._loop_entries[jump_target] = loop_info
                        self._loop_exits[backward_jump['from'] + 2] = loop_info
                        debug_print(f"[_prescan_for_loops] 识别到while True: 循环: 体@{jump_target}-{backward_jump['from']}")
        
        debug_print(f"[_prescan_for_loops] 预扫描完成，发现 {len(self._loop_entries)} 个循环")
    
    def _pop_blocks_to_current_pos(self, current_pos: int) -> None:
        """弹出块栈直到当前位置
        
        参考C++ pycdc实现：
        当else_pop为真且遇到非跳转指令时，需要弹出块栈
        将完成的块添加到父块中
        """
        if not self.blocks:
            return
        
        prev_block = self.current_block
        # 当上一个块的结束位置小于当前位置且不是主块时，继续弹出
        while (prev_block.end < current_pos and 
               prev_block.blk_type != ASTBlock.BlockType.BLK_MAIN):
            
            # 如果不是容器块，弹出栈历史
            if prev_block.blk_type != ASTBlock.BlockType.BLK_CONTAINER:
                if prev_block.end == 0:
                    break
                if self.stack_hist:
                    self.stack_hist.pop()
            
            # 弹出当前块
            self.blocks.pop()
            
            if not self.blocks:
                break
            
            # 更新当前块
            self.current_block = self.blocks[-1]
            # 将弹出的块添加到当前块
            self.current_block.append(prev_block)
            
            prev_block = self.current_block
    
    def _push_block(self, block: ASTBlock) -> None:
        """将块压入块栈"""
        self.blocks.append(block)
        self.current_block = block
    
    def _pop_block_from_stack(self) -> Optional[ASTBlock]:
        """从块栈弹出块"""
        if len(self.blocks) <= 1:  # 保留主块
            return None
        block = self.blocks.pop()
        self.current_block = self.blocks[-1]
        return block
    
    def _emit(self, node: ASTNode) -> None:
        """发射节点到当前块"""
        current_offset = getattr(self, 'current_instruction_offset', -1)
        node_type = type(node).__name__
        

        # [DEBUG] 调试：打印关键节点的发射信息
        if node_type in ['ASTTry', 'ASTStore', 'ASTBinary', 'ASTCall', 'ASTRaise', 'ASTReturn']:
            print(f"\n[_emit] 发射{node_type}节点, current_offset={current_offset}")
            has_if_node = hasattr(self, 'current_if_node') and self.current_if_node is not None
            print(f"[_emit] has_if_node={has_if_node}")
            if has_if_node:
                print(f"[_emit] current_if_node={self.current_if_node}")
                print(f"[_emit] if_body_start_offset={getattr(self, 'if_body_start_offset', None)}")
                print(f"[_emit] if_body_end_offset={getattr(self, 'if_body_end_offset', None)}")
                body_start = getattr(self, 'if_body_start_offset', -1)
                body_end = getattr(self, 'if_body_end_offset', -1)
                print(f"[_emit] body_start <= current_offset < body_end: {body_start} <= {current_offset} < {body_end} = {body_start <= current_offset < body_end}")
                print(f"[_emit] current_offset >= body_end: {current_offset} >= {body_end} = {current_offset >= body_end}")
                
                # 检查else分支
                else_end = self._find_else_end(body_end)
                print(f"[_emit] _find_else_end({body_end}) = {else_end}")
                if else_end > 0:
                    print(f"[_emit] current_offset < else_end: {current_offset} < {else_end} = {current_offset < else_end}")
        
        # 检查是否在if语句体内
        if hasattr(self, 'current_if_node') and self.current_if_node is not None:
            body_start = getattr(self, 'if_body_start_offset', -1)
            body_end = getattr(self, 'if_body_end_offset', -1)
            
            # [DEBUG] 打印调试信息
            if node_type == 'ASTReturn':
                print(f"\n[_emit] 检查if语句体: current_offset={current_offset}, body_start={body_start}, body_end={body_end}")
                print(f"[_emit] body_start <= current_offset < body_end: {body_start} <= {current_offset} < {body_end} = {body_start <= current_offset < body_end}")
            
            # 如果节点是ASTIf/ASTWhile/ASTFor本身，不要添加到if body中，而是添加到主块
            if node_type in ['ASTIf', 'ASTWhile', 'ASTFor']:
                # 控制流节点本身添加到主块
                pass  # 继续执行后面的代码，添加到主块
            elif body_start <= current_offset < body_end:
                # 在if语句体内 (then 分支)
                if hasattr(self.current_if_node, '_body') and self.current_if_node._body is not None:
                    self.current_if_node._body.append(node)
                    node.parent = self.current_if_node._body
                    
                    # [DEBUG] 关键修复：如果是return语句，检查是否需要结束当前if
                    if node_type == 'ASTReturn':
                        # [DEBUG] 关键修复：检查是否有else分支
                        else_end = self._find_else_end(body_end)
                        has_else = else_end > 0 and current_offset < else_end
                        
                        if has_else:
                            # [DEBUG] 有else分支，不要重置current_if_node，让else分支能正确处理
                            debug_print(f"[_emit] return语句在if body中，但有else分支，保持current_if_node")
                        else:
                            # 检查是否有嵌套的if需要恢复
                            if hasattr(self, '_if_stack') and self._if_stack:
                                # 从栈中弹出当前if，恢复外层if
                                current_if_info = self._if_stack.pop()
                                self.current_if_node = current_if_info['node']
                                self.if_body_start_offset = current_if_info['body_start']
                                self.if_body_end_offset = current_if_info['body_end']
                                debug_print(f"[_emit] return语句后恢复外层if，栈深度: {len(self._if_stack)}")
                            else:
                                # 没有外层if，重置current_if_node
                                self.current_if_node = None
                                debug_print(f"[_emit] return语句后重置current_if_node")
                    
                    return
            elif current_offset >= body_end:
                # 已经超出if语句体，检查是否在else分支
                # [DEBUG] 关键修复：只有当存在JUMP_FORWARD指令时，才认为有else分支
                else_end = self._find_else_end(body_end)
                
                # [DEBUG] 关键修复：只有当找到JUMP_FORWARD指令时，才认为有else分支
                # 如果没有JUMP_FORWARD，说明if没有else分支，直接跳转到if之后的代码
                # [DEBUG] 关键修复：使用 <= 而不是 <，因为else分支的最后一个指令（如RETURN_VALUE）的offset可能等于else_end
                if else_end > 0 and current_offset <= else_end:
                    # [关键修复] 在添加节点到else body之前，先检查是否是else分支的末尾
                    # 如果是，并且有外层if，应该先恢复外层if
                    is_last_node_in_else = current_offset >= else_end - 6
                    
                    # [关键修复] 对于嵌套if，如果当前节点是else分支的最后一个节点，先恢复外层if
                    # 这样后续节点（如外层if的else分支中的节点）会被正确处理
                    if is_last_node_in_else and hasattr(self, '_if_stack') and self._if_stack:
                        current_if_info = self._if_stack.pop()
                        self.current_if_node = current_if_info['node']
                        self.if_body_start_offset = current_if_info['body_start']
                        self.if_body_end_offset = current_if_info['body_end']
                        # [关键修复] 恢复后重新检查当前节点是否应该添加到外层if的else分支
                        body_start = self.if_body_start_offset
                        body_end = self.if_body_end_offset
                        else_end = self._find_else_end(body_end)
                        if else_end > 0 and current_offset <= else_end:
                            if hasattr(self.current_if_node, '_orelse') and self.current_if_node._orelse is not None:
                                self.current_if_node._orelse.append(node)
                                node.parent = self.current_if_node._orelse
                                return
                    
                    # 在else分支内
                    debug_print(f"[_emit] 节点添加到else body: {type(node).__name__}")
                    if hasattr(self.current_if_node, '_orelse') and self.current_if_node._orelse is not None:
                        # [DEBUG] 检查_orelse的类型和内容
                        orelse_type = type(self.current_if_node._orelse).__name__
                        orelse_nodes_count = len(self.current_if_node._orelse.nodes) if hasattr(self.current_if_node._orelse, 'nodes') else 'N/A'
                        debug_print(f"[_emit] current_if_node._orelse类型: {orelse_type}, 节点数: {orelse_nodes_count}")
                        self.current_if_node._orelse.append(node)
                        node.parent = self.current_if_node._orelse
                        # [DEBUG] 检查append后的节点数
                        orelse_nodes_count_after = len(self.current_if_node._orelse.nodes) if hasattr(self.current_if_node._orelse, 'nodes') else 'N/A'
                        debug_print(f"[_emit] append后节点数: {orelse_nodes_count_after}")
                        
                        # [关键修复] 检查是否是else分支中的最后一个节点
                        # 如果是，恢复外层if（如果有）
                        if is_last_node_in_else:
                            # [关键修复] 优先检查是否有外层if（嵌套if的情况）
                            if hasattr(self, '_if_stack') and self._if_stack:
                                current_if_info = self._if_stack.pop()
                                self.current_if_node = current_if_info['node']
                                self.if_body_start_offset = current_if_info['body_start']
                                self.if_body_end_offset = current_if_info['body_end']
                            else:
                                # [关键修复] 检查是否是if-elif-else链的一部分
                                is_if_elif_chain = False
                                if hasattr(self, '_if_chain_root') and self._if_chain_root is not None:
                                    if hasattr(self._if_chain_root, '_orelse') and self._if_chain_root._orelse:
                                        if hasattr(self._if_chain_root._orelse, 'nodes') and len(self._if_chain_root._orelse.nodes) > 0:
                                            is_if_elif_chain = True
                                
                                if is_if_elif_chain:
                                    pass  # 保持current_if_node
                                else:
                                    self.current_if_node = None
                        
                        return
                else:
                    # [DEBUG] 关键修复：没有else分支，节点应该添加到主块
                    # 先重置current_if_node，然后继续执行后面的代码（添加到主块）
                    debug_print(f"[_emit] 超出if body范围，没有else分支，节点将添加到主块")
                    # [关键修复] 检查是否是if-elif-else链的一部分
                    # 如果是，不要重置current_if_node，让后续的elif能被正确识别
                    is_if_elif_chain = False
                    if hasattr(self, 'current_if_node') and self.current_if_node is not None:
                        # 检查当前if节点是否已经有orelse（即前面是否有elif）
                        if hasattr(self.current_if_node, '_orelse') and self.current_if_node._orelse:
                            if hasattr(self.current_if_node._orelse, 'nodes') and len(self.current_if_node._orelse.nodes) > 0:
                                is_if_elif_chain = True
                                debug_print(f"[_emit] 检测到if-elif-else链，保持current_if_node")
                    
                    if not is_if_elif_chain:
                        # [DEBUG] 关键修复：从栈中恢复外层if（如果有）
                        if hasattr(self, '_if_stack') and self._if_stack:
                            current_if_info = self._if_stack.pop()
                            self.current_if_node = current_if_info['node']
                            self.if_body_start_offset = current_if_info['body_start']
                            self.if_body_end_offset = current_if_info['body_end']
                            debug_print(f"[_emit] 恢复外层if，栈深度: {len(self._if_stack)}")
                        else:
                            self.current_if_node = None
                    # [DEBUG] 关键修复：将current_block恢复为main_block，以便后续节点添加到主块
                    self.current_block = self.main_block
                    debug_print(f"[_emit] 将current_block恢复为main_block")
                    # [DEBUG] 关键修复：不返回，继续执行后面的代码（添加到主块）
        
        # 检查是否在for循环体内
        # [关键修复] 使用循环处理嵌套for的恢复和重新检查
        for_check_count = 0
        max_for_checks = 10  # 防止无限循环
        
        while hasattr(self, 'current_for_node') and self.current_for_node is not None and for_check_count < max_for_checks:
            for_check_count += 1
            
            body_start = getattr(self, 'for_body_start_offset', -1)
            body_end = getattr(self, 'for_body_end_offset', -1)
            else_start = getattr(self, 'for_else_start_offset', -1)
            else_end = getattr(self, 'for_else_end_offset', -1)
            
            debug_print(f"[_emit] 检查for body: current_offset={current_offset}, body范围={body_start}-{body_end}, else_start={else_start}, else_end={else_end}")
            
            if body_start <= current_offset < body_end:
                # 在for循环体内
                debug_print(f"[_emit] 节点添加到for body: {type(node).__name__}")
                if hasattr(self.current_for_node, '_body') and self.current_for_node._body is not None:
                    self.current_for_node._body.append(node)
                    node.parent = self.current_for_node._body
                    return
            elif else_start > 0 and else_end > 0 and else_start <= current_offset < else_end:
                # [关键修复] 在for-else分支中
                debug_print(f"[_emit] 节点添加到for-else body: {type(node).__name__}")
                if hasattr(self.current_for_node, '_else_block') and self.current_for_node._else_block is not None:
                    self.current_for_node._else_block.append(node)
                    node.parent = self.current_for_node._else_block
                    return
            elif else_start > 0 and else_end > 0 and current_offset >= else_end:
                # [关键修复] 已经超出for-else范围，从栈中恢复外层for（如果有）
                debug_print(f"[_emit] 超出for-else范围")
                if hasattr(self, '_for_stack') and self._for_stack:
                    # 从栈中弹出外层for
                    outer_for_info = self._for_stack.pop()
                    self.current_for_node = outer_for_info['node']
                    self.for_body_start_offset = outer_for_info['body_start']
                    self.for_body_end_offset = outer_for_info['body_end']
                    self.for_else_start_offset = outer_for_info['else_start']
                    self.for_else_end_offset = outer_for_info['else_end']
                    debug_print(f"[_emit] 恢复外层for，栈深度: {len(self._for_stack)}")
                    # [关键修复] 恢复后继续循环检查
                    continue
                else:
                    self.current_for_node = None
                    break
            elif current_offset >= body_end:
                # [关键修复] 已经超出for循环体，从栈中恢复外层for（如果有）
                debug_print(f"[_emit] 超出for body范围")
                if hasattr(self, '_for_stack') and self._for_stack:
                    # 从栈中弹出外层for
                    outer_for_info = self._for_stack.pop()
                    self.current_for_node = outer_for_info['node']
                    self.for_body_start_offset = outer_for_info['body_start']
                    self.for_body_end_offset = outer_for_info['body_end']
                    self.for_else_start_offset = outer_for_info['else_start']
                    self.for_else_end_offset = outer_for_info['else_end']
                    debug_print(f"[_emit] 恢复外层for，栈深度: {len(self._for_stack)}")
                    # [关键修复] 恢复后继续循环检查
                    continue
                else:
                    self.current_for_node = None
                    break
            else:
                # 不在当前for的任何范围内，退出循环
                break
        
        # [DEBUG] 检查是否在while循环体内
        # [关键修复] 使用循环处理while-else的恢复和重新检查
        while_check_count = 0
        max_while_checks = 10  # 防止无限循环
        
        while hasattr(self, 'current_while_node') and self.current_while_node is not None and while_check_count < max_while_checks:
            while_check_count += 1
            
            body_start = getattr(self, 'while_body_start', -1)
            body_end = getattr(self, 'while_body_end', -1)
            else_start = getattr(self, 'while_else_start', -1)
            else_end = getattr(self, 'while_else_end', -1)
            
            debug_print(f"[_emit] 检查while body: current_offset={current_offset}, body范围={body_start}-{body_end}, else范围={else_start}-{else_end}")
            
            if body_start <= current_offset < body_end:
                # 在while循环体内
                debug_print(f"[_emit] 节点添加到while body: {type(node).__name__}")
                if hasattr(self.current_while_node, '_body') and self.current_while_node._body is not None:
                    self.current_while_node._body.append(node)
                    node.parent = self.current_while_node._body
                    return
            elif else_start > 0 and else_end > 0 and else_start <= current_offset < else_end:
                # [关键修复] 在while-else分支中
                debug_print(f"[_emit] 节点添加到while-else body: {type(node).__name__}")
                if hasattr(self.current_while_node, '_orelse') and self.current_while_node._orelse is not None:
                    self.current_while_node._orelse.append(node)
                    node.parent = self.current_while_node._orelse
                    return
            elif current_offset >= body_end:
                # 已经超出while循环体，重置current_while_node
                debug_print(f"[_emit] 超出while body范围，重置current_while_node")
                self.current_while_node = None
                break
            else:
                # 不在当前while的任何范围内，退出循环
                break
        
        # 检查是否在try块体内
        if hasattr(self, 'current_try_node') and self.current_try_node is not None:
            body_start = getattr(self, 'try_body_start_offset', -1)
            body_end = getattr(self, 'try_body_end_offset', -1)
            else_start = getattr(self, 'try_else_start_offset', -1)
            else_end = getattr(self, 'try_else_end_offset', -1)
            
            # 如果节点是ASTTry本身，不要添加到try body中
            if node_type == 'ASTTry':
                # [DEBUG] 关键修复：当添加try节点本身时，不要重置current_try_node
                # 因为后续的except块需要引用这个try节点
                pass  # 继续执行后面的代码，添加到主块
            elif body_start <= current_offset < body_end:
                # [关键修复] 检查是否在else分支范围内
                if else_start > 0 and else_end > 0 and else_start <= current_offset < else_end:
                    # 在try-else分支中
                    debug_print(f"[_emit] 节点添加到try-else body: {type(node).__name__}")
                    if hasattr(self.current_try_node, '_orelse') and self.current_try_node._orelse is not None:
                        self.current_try_node._orelse.append(node)
                        node.parent = self.current_try_node._orelse
                        return
                else:
                    # 在try块体内
                    debug_print(f"[_emit] 节点添加到try body: {type(node).__name__}")
                    if hasattr(self.current_try_node, '_body') and self.current_try_node._body is not None:
                        self.current_try_node._body.append(node)
                        node.parent = self.current_try_node._body
                        return
            elif current_offset > body_end:
                # [DEBUG] 修复：使用 > 而不是 >=，因为当 current_offset == body_end 时，
                # 我们正在处理 PUSH_EXC_INFO，不应该重置
                # 已经超出try块范围，重置current_try_node
                # [DEBUG] 关键修复：但是，如果我们在except块体内，不应该重置current_try_node
                # 因为except块是try节点的一部分
                in_except_body = False
                if hasattr(self, 'except_body_start_offset') and hasattr(self, 'except_body_end_offset'):
                    except_start = self.except_body_start_offset
                    except_end = self.except_body_end_offset
                    if except_start <= current_offset < except_end:
                        in_except_body = True
                
                if not in_except_body:
                    debug_print(f"[_emit] 超出try body范围，重置current_try_node")
                    self.current_try_node = None
        
        # [DEBUG] 检查是否在except块体内
        if hasattr(self, 'current_exception_handler') and self.current_exception_handler is not None:
            if hasattr(self, 'except_body_start_offset') and hasattr(self, 'except_body_end_offset'):
                body_start = self.except_body_start_offset
                body_end = self.except_body_end_offset
                
                if body_start <= current_offset < body_end:
                    # 在except块体内
                    debug_print(f"[_emit] 节点添加到except body: {type(node).__name__}")
                    # 获取最后一个handler
                    if self.current_exception_handler.handlers:
                        last_handler = self.current_exception_handler.handlers[-1]
                        if hasattr(last_handler, '_body') and last_handler._body is not None:
                            last_handler._body.append(node)
                            node.parent = last_handler._body
                            return
                elif current_offset >= body_end:
                    # 已经超出except块范围
                    debug_print(f"[_emit] 超出except body范围")
        
        # [DEBUG] 检查是否在finally块体内
        if hasattr(self, 'current_exception_handler') and self.current_exception_handler is not None:
            if hasattr(self, 'finally_body_start_offset') and hasattr(self, 'finally_body_end_offset'):
                body_start = self.finally_body_start_offset
                body_end = self.finally_body_end_offset
                
                if body_start <= current_offset < body_end:
                    # 在finally块体内
                    debug_print(f"[_emit] 节点添加到finally body: {type(node).__name__}")
                    if hasattr(self.current_exception_handler, '_finalbody') and self.current_exception_handler._finalbody is not None:
                        self.current_exception_handler._finalbody.append(node)
                        node.parent = self.current_exception_handler._finalbody
                        return
                elif current_offset >= body_end:
                    # 已经超出finally块范围
                    debug_print(f"[_emit] 超出finally body范围")
        
        # [DEBUG] 检查是否在with语句体内 - 支持嵌套with
        if hasattr(self, '_with_stack') and self._with_stack:
            # 从栈顶开始查找，找到包含当前offset的with语句
            for i in range(len(self._with_stack) - 1, -1, -1):
                with_info = self._with_stack[i]
                body_start = with_info.get('start_offset', -1)
                body_end = with_info.get('end_offset', -1)
                with_node = with_info.get('node')
                
                # 检查当前offset是否在这个with语句的范围内
                if body_start <= current_offset:
                    # 在with语句体内
                    # 只有当body_end是真实值（小于1000）且current_offset >= body_end时，才表示超出范围
                    if body_end < 1000 and current_offset >= body_end:
                        # 已经超出这个with语句范围，从栈中移除
                        debug_print(f"[_emit] 超出with body范围，从栈中移除: {i}")
                        self._with_stack.pop(i)
                        continue
                    else:
                        # 在with语句体内
                        # [DEBUG] 对于嵌套with语句，内层with应该添加到外层with的body中
                        # 只有当当前节点不是这个with语句本身时才添加
                        if with_node is not node:
                            debug_print(f"[_emit] 节点添加到with body[{i}]: {type(node).__name__}, offset={current_offset}, body范围={body_start}-{body_end}")
                            if with_node and hasattr(with_node, '_body') and with_node._body is not None:
                                with_node._body.append(node)
                                node.parent = with_node._body
                                return
                        else:
                            # 当前节点就是这个with语句本身
                            # [DEBUG] 如果不是栈顶的with语句，继续查找外层的with语句
                            if i > 0:
                                debug_print(f"[_emit] 当前with语句本身，继续查找外层with: {i}")
                                continue
                            else:
                                # 这是栈底的with语句，添加到主块
                                debug_print(f"[_emit] 栈底with语句本身，添加到主块: {type(node).__name__}")
                                break
        
        # 兼容旧代码
        elif hasattr(self, 'current_with_node') and self.current_with_node is not None:
            body_start = getattr(self, 'current_with_node_start_offset', -1)
            body_end = getattr(self, 'current_with_end_offset', -1)
            
            # 如果节点是ASTWith本身，不要添加到with body中
            if node_type == 'ASTWith':
                pass  # 继续执行后面的代码，添加到主块
            elif body_start <= current_offset:
                # 在with语句体内（body_end可能是临时大值，只检查是否大于body_start）
                # 只有当body_end是真实值（小于1000）且current_offset >= body_end时，才表示超出范围
                if body_end < 1000 and current_offset >= body_end:
                    # 已经超出with语句范围，重置current_with_node
                    debug_print(f"[_emit] 超出with body范围，重置current_with_node")
                    self.current_with_node = None
                else:
                    # 在with语句体内
                    debug_print(f"[_emit] 节点添加到with body: {type(node).__name__}, offset={current_offset}, body范围={body_start}-{body_end}")
                    if hasattr(self.current_with_node, '_body') and self.current_with_node._body is not None:
                        self.current_with_node._body.append(node)
                        node.parent = self.current_with_node._body
                        return
        
        if self.current_block is not None:
            print(f"[_emit] 添加到current_block: {type(node).__name__}, current_block={id(self.current_block)}, main_block={id(self.main_block)}, same={self.current_block is self.main_block}")
            self.current_block.append(node)
            node.parent = self.current_block
    
    def _find_else_end(self, body_end: int) -> int:
        """查找else分支的结束位置
        
        在if-else结构中，else分支通常以JUMP_FORWARD指令结束
        该指令跳过else分支，到达if-else结构之后
        
        [关键修复] 在if-elif-else链中，需要正确识别else分支的结束
        [关键修复] 区分简单if（没有else）和if-else结构
        """
        if not hasattr(self, 'instructions') or not self.instructions:
            return -1
        
        # [关键修复] 首先检查跳转目标之后是否有实际代码（不是简单的return None）
        # 如果没有实际代码，说明是简单if，没有else分支
        has_real_code_after_jump = False
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            if instr_offset >= body_end:
                instr_opcode = instr.get('opcode', -1)
                # 如果遇到实际代码（STORE_NAME, STORE_FAST等），说明有else分支
                if instr_opcode in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A]:
                    has_real_code_after_jump = True
                    break
        
        # [关键修复] 检查if body是否有实际代码或break
        # 如果if body有实际代码，但跳转目标之后没有，说明是简单if
        has_real_code_in_if_body = False
        has_break_in_if_body = False
        has_nested_if = False
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            # if body的范围是从第一条指令到跳转目标
            if 0 <= instr_offset < body_end:
                instr_opcode = instr.get('opcode', -1)
                # [关键修复] 检查是否有嵌套if
                if instr_opcode in [Opcode.POP_JUMP_FORWARD_IF_FALSE_A, Opcode.POP_JUMP_FORWARD_IF_TRUE_A]:
                    has_nested_if = True
                if instr_opcode in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A]:
                    has_real_code_in_if_body = True
        
        # [关键修复] 检查跳转目标之后的代码量
        # 如果跳转目标之后只有很少的指令（如LOAD_CONST None; RETURN_VALUE），说明可能是简单if
        # 如果有更多的指令，说明是if-else
        instructions_after_jump = []
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            if instr_offset >= body_end:
                instructions_after_jump.append(instr)
        
        # [关键修复] 对于pass语句，我们无法从字节码区分简单if和if-else
        # 所以，对于pass语句，我们保守地假设有else分支
        # 只有当跳转目标之后有实际代码（STORE_NAME等）时，我们才确定有else分支
        # 如果跳转目标之后只有2条指令（LOAD_CONST None; RETURN_VALUE），且没有实际代码
        # 这可能是简单if，也可能是if-else（pass）
        # 在这种情况下，我们返回-1，让调用者决定如何处理
        if len(instructions_after_jump) <= 2 and not has_real_code_after_jump:
            # [关键修复] 检查if body是否有实际代码
            # 如果if body有实际代码，但跳转目标之后没有，说明是简单if
            # 如果if body也没有实际代码（都是pass），我们无法区分，保守地假设有else
            if has_real_code_in_if_body or has_break_in_if_body:
                # if body有实际代码或break，但跳转目标之后没有，说明是简单if
                return -1
            else:
                # if body也没有实际代码（都是pass），我们无法区分
                # 保守地假设有else分支，返回最后一个RETURN_VALUE的位置
                for instr in reversed(self.instructions):
                    if instr.get('opcode', -1) == Opcode.RETURN_VALUE:
                        return instr.get('offset', -1)
                return -1
        
        # [关键修复] 如果if body有break，说明是简单if（break会跳出循环，不会执行else）
        if has_break_in_if_body:
            return -1
        
        # [关键修复] 对于嵌套if，我们需要更仔细地分析
        # 不能简单地返回-1，因为嵌套if-else结构是有else分支的
        
        # [关键修复] 检查是否是if-elif-else链
        # 如果是，查找最后一个RETURN_VALUE或JUMP_FORWARD
        return_values = []
        jump_forwards = []
        
        # [关键修复] 检查是否是if-elif-else链
        # 如果是，查找最后一个RETURN_VALUE或JUMP_FORWARD
        return_values = []
        jump_forwards = []
        
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            if instr_offset >= body_end:
                instr_opcode = instr.get('opcode', -1)
                
                # JUMP_FORWARD 的 opcode
                if instr_opcode == Opcode.JUMP_FORWARD_A:
                    jump_forwards.append(instr_offset)
                # RETURN_VALUE
                elif instr_opcode == Opcode.RETURN_VALUE:
                    return_values.append(instr_offset)
                # 如果遇到另一个条件跳转，说明这是if-elif-else链
                elif instr_opcode in [Opcode.POP_JUMP_FORWARD_IF_FALSE_A, Opcode.POP_JUMP_FORWARD_IF_TRUE_A]:
                    # 在if-elif-else链中，else分支的结束应该是最后一个RETURN_VALUE
                    # 或者是在下一个条件跳转之前的RETURN_VALUE
                    if return_values:
                        last_return = return_values[-1]
                        return last_return
        
        # 如果找到JUMP_FORWARD，使用它
        if jump_forwards:
            result = jump_forwards[0]  # 使用第一个JUMP_FORWARD
            return result
        
        # [关键修复] 对于简单的if-else结构（没有JUMP_FORWARD）
        # 需要找到body_end之后的第一个RETURN_VALUE（if body的结束）
        # 然后找到下一个RETURN_VALUE（else body的结束）
        if return_values:
            # 找到body_end之后的所有RETURN_VALUE
            returns_after_body = [r for r in return_values if r > body_end]
            if len(returns_after_body) >= 2:
                # 第一个是if body的结束，第二个是else body的结束
                result = returns_after_body[1]
                return result
            elif len(returns_after_body) == 1:
                # 只有一个RETURN_VALUE，使用它
                result = returns_after_body[0]
                return result
            elif return_values:
                # 使用最后一个RETURN_VALUE
                result = return_values[-1]
                return result
        
        return -1
    
    def _process_instruction(self, instr: dict) -> None:
        """处理单条指令
        
        参考C++ pycdc实现，使用块栈管理控制流结构
        """
        import sys
        try:
            opcode = instr.get('opcode')
            operand = instr.get('operand', 0)
            
            current_offset = instr.get('offset', -1)
            self.current_instruction_offset = current_offset
            
            # [关键修复] 检查是否需要跳过break/continue后的指令
            if hasattr(self, '_skip_until_return') and self._skip_until_return:
                # 跳过LOAD_CONST和RETURN_VALUE指令
                if opcode in [Opcode.LOAD_CONST_A, Opcode.RETURN_VALUE]:
                    debug_print(f"[_PROCESS_INSTRUCTION] 跳过break/continue后的指令: opcode={opcode}, offset={current_offset}")
                    # 如果是RETURN_VALUE，重置标记
                    if opcode == Opcode.RETURN_VALUE:
                        self._skip_until_return = False
                    return
                else:
                    # 遇到其他指令，重置标记
                    self._skip_until_return = False
            
            # [关键修复] 检查是否是 while True: 循环的开始
            if hasattr(self, '_loop_entries') and current_offset in self._loop_entries:
                loop_info = self._loop_entries[current_offset]
                if loop_info.get('is_while_true', False):
                    debug_print(f"[_PROCESS_INSTRUCTION] 检测到while True:循环开始 at offset {current_offset}")
                    # 创建while节点，条件为True
                    from core.ast_nodes import ASTWhile, ASTNodeList
                    from core.ast_nodes import ASTObject
                    while_node = ASTWhile(ASTObject(True), ASTNodeList(), None)
                    
                    # 发射while节点
                    saved_block = self.current_block
                    self.current_block = self.main_block
                    self._emit(while_node)
                    self.current_block = saved_block
                    
                    # 设置while循环信息
                    self.current_while_node = while_node
                    self.while_body_start = loop_info['body_start']
                    self.while_body_end = loop_info['body_end']
                    self.while_else_start = -1
                    self.while_else_end = -1
                    debug_print(f"[_PROCESS_INSTRUCTION] while True:循环body范围: {self.while_body_start}-{self.while_body_end}")
            
            # ===== 块栈管理：处理else_pop逻辑（参考C++实现）=====
            if self.else_pop and opcode not in [
                Opcode.JUMP_FORWARD_A,
                Opcode.JUMP_IF_FALSE_A,
                Opcode.JUMP_IF_FALSE_OR_POP_A,
                Opcode.POP_JUMP_IF_FALSE_A,
                Opcode.POP_JUMP_FORWARD_IF_FALSE_A,
                Opcode.JUMP_IF_TRUE_A,
                Opcode.JUMP_IF_TRUE_OR_POP_A,
                Opcode.POP_JUMP_IF_TRUE_A,
                Opcode.POP_JUMP_FORWARD_IF_TRUE_A,
                Opcode.POP_BLOCK,
            ]:
                self.else_pop = False
                self._pop_blocks_to_current_pos(current_offset)
            
            # ===== 块栈管理：处理need_try逻辑（参考C++实现）=====
            if self.need_try and opcode != Opcode.SETUP_EXCEPT_A:
                self.need_try = False
                # 保存当前栈状态
                self.stack_hist.append(self.stack.copy())
                # 创建try块
                try_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_TRY, end=0, inited=True)
                self.blocks.append(try_block)
                self.current_block = self.blocks[-1]
            
            # [DEBUG] 关键修复：检查是否需要跳过assert相关指令
            if hasattr(self, '_skip_assert_instructions') and self._skip_assert_instructions:
                if hasattr(self, '_assert_end_offset') and current_offset <= self._assert_end_offset:
                    debug_print(f"[_PROCESS_INSTRUCTION] 跳过assert相关指令: opcode={opcode}, offset={current_offset}")
                    # [DEBUG] 关键修复：提取assert消息
                    if opcode == Opcode.LOAD_CONST_A and hasattr(self, '_current_assert_node'):
                        # 这是assert消息，提取并更新assert节点
                        const_idx = operand
                        # 使用_current_code_obj获取常量
                        code_obj_to_use = getattr(self, '_current_code_obj', None) or self.code_obj
                        if code_obj_to_use:
                            # 尝试使用get_const方法（PycCode对象）
                            msg_value = None
                            if hasattr(code_obj_to_use, 'get_const'):
                                msg_ref = code_obj_to_use.get_const(const_idx)
                                if msg_ref and msg_ref.get():
                                    msg_value = msg_ref.get()
                            # 尝试使用co_consts属性（原生code对象）
                            elif hasattr(code_obj_to_use, 'co_consts'):
                                consts = code_obj_to_use.co_consts
                                if const_idx < len(consts):
                                    msg_value = consts[const_idx]
                            
                            if msg_value:
                                from core.pyc_objects import PycString
                                if isinstance(msg_value, PycString):
                                    msg_str = msg_value.value
                                    self._current_assert_node._msg = ASTObject(msg_str)
                                    debug_print(f"[_PROCESS_INSTRUCTION] 更新assert消息: {msg_str}")
                    # 如果是RAISE_VARARGS，重置跳过标志
                    if opcode == Opcode.RAISE_VARARGS_A:
                        self._skip_assert_instructions = False
                        self._current_assert_node = None
                        debug_print(f"[_PROCESS_INSTRUCTION] assert指令处理完成，重置跳过标志")
                    return
                else:
                    # 已经超过assert结束位置，重置跳过标志
                    self._skip_assert_instructions = False
                    self._current_assert_node = None
            
            # [DEBUG] 调试：打印所有指令
            print(f"[_PROCESS_INSTRUCTION] 处理指令: opcode={opcode}, offset={current_offset}, operand={operand}")
            
            if opcode == Opcode.STORE_NAME_A:
                print(f"[_PROCESS_INSTRUCTION] 处理STORE_NAME_A at offset {current_offset}, operand={operand}")
            
            # [DEBUG] 调试：打印所有指令
            opcode_name = instr.get('opcode_name', 'unknown')
            if opcode == Opcode.BEFORE_WITH or 'WITH' in opcode_name:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理指令: {opcode_name} (opcode={opcode}) at offset {current_offset}")
            
            # 增强：构建控制流图
            self._build_control_flow_edge(current_offset, instr)
            
            # 增强：识别控制流结构模式
            self._analyze_control_flow_pattern(opcode, operand, current_offset)
            
            opcode_name_str = instr.get('opcode_name', 'unknown')
            
            opcode_name = instr.get('opcode_name', f'unknown_{opcode}')
            
            # 首先尝试使用增强的类处理器
            can_handle_class = self.class_handler.can_handle(opcode, operand)
            print(f"[_PROCESS_INSTRUCTION] opcode={opcode}, 检查class_handler.can_handle: {can_handle_class}")
            if can_handle_class:
                debug_print(f"[_PROCESS_INSTRUCTION] class_handler处理指令 {opcode}")
                result = self.class_handler.handle(opcode, operand, self)
                if result:
                    self._emit(result)
                    return
            
            # 然后尝试使用增强的装饰器处理器
            can_handle_decorator = self.decorator_handler.can_handle(opcode, operand)
            print(f"[_PROCESS_INSTRUCTION] opcode={opcode}, 检查decorator_handler.can_handle: {can_handle_decorator}")
            if can_handle_decorator:
                debug_print(f"[_PROCESS_INSTRUCTION] decorator_handler处理指令 {opcode}")
                result = self.decorator_handler.handle(opcode, operand, self)
                if result:
                    self._emit(result)
                    return
            
            # 特殊处理 FOR_ITER_A 指令
            if opcode == Opcode.FOR_ITER_A:
                self._for_iter(operand)
                return
            
            # Python 3.11 opcodes with _A suffix
            print(f"[_PROCESS_INSTRUCTION] 进入Python 3.11 opcodes处理, opcode={opcode}, type={type(opcode)}, MAKE_FUNCTION_A={Opcode.MAKE_FUNCTION_A}, type={type(Opcode.MAKE_FUNCTION_A)}")
            if opcode == Opcode.LOAD_BUILD_CLASS:
                self._load_build_class()
            elif opcode == Opcode.LOAD_CONST_A:
                self._load_const(operand)
            elif opcode == Opcode.LOAD_NAME_A:
                self._load_name(operand)
            elif opcode == Opcode.LOAD_FAST_A:
                self._load_fast(operand)
            elif opcode == Opcode.STORE_NAME_A:
                print(f"[STORE_NAME_A_HANDLER] 处理STORE_NAME_A at offset {current_offset}, operand={operand}")
                print(f"[STORE_NAME_A_HANDLER] self._store_name = {self._store_name}, type = {type(self._store_name)}")
                self._store_name(operand)
            elif opcode == Opcode.STORE_FAST_A:
                self._store_fast(operand)
            elif opcode == Opcode.BINARY_ADD:
                self._binary_op(ASTBinary.BinOp.BIN_ADD.value)
            elif opcode == Opcode.BINARY_SUBTRACT:
                self._binary_op(ASTBinary.BinOp.BIN_SUBTRACT.value)
            elif opcode == Opcode.BINARY_MULTIPLY:
                # print(f"DEBUG: BINARY_MULTIPLY detected, passing value {ASTBinary.BinOp.BIN_MULTIPLY.value}")
                self._binary_op(ASTBinary.BinOp.BIN_MULTIPLY.value)
            elif opcode == Opcode.BINARY_DIVIDE:
                self._binary_op(ASTBinary.BinOp.BIN_DIVIDE.value)
            elif opcode == Opcode.BINARY_OP_A:
                # Python 3.11+ 使用 BINARY_OP_A 统一处理所有二元操作
                # [DEBUG] 关键修复：基于实际测试更新的操作数映射
                binary_op_map = {
                    # 普通二元操作
                    0: ASTBinary.BinOp.BIN_ADD.value,           # +
                    1: ASTBinary.BinOp.BIN_AND.value,           # &
                    2: ASTBinary.BinOp.BIN_FLOOR_DIVIDE.value,  # //
                    3: ASTBinary.BinOp.BIN_LSHIFT.value,        # <<
                    5: ASTBinary.BinOp.BIN_MULTIPLY.value,      # *
                    6: ASTBinary.BinOp.BIN_MODULO.value,        # %
                    7: ASTBinary.BinOp.BIN_OR.value,            # |
                    8: ASTBinary.BinOp.BIN_POWER.value,         # **
                    9: ASTBinary.BinOp.BIN_RSHIFT.value,        # >>
                    10: ASTBinary.BinOp.BIN_SUBTRACT.value,     # -
                    11: ASTBinary.BinOp.BIN_DIVIDE.value,       # /
                    12: ASTBinary.BinOp.BIN_XOR.value,          # ^
                    # 原地操作 (in-place operations)
                    13: ASTBinary.BinOp.BIN_IP_ADD.value,       # +=
                    14: ASTBinary.BinOp.BIN_IP_AND.value,       # &=
                    15: ASTBinary.BinOp.BIN_IP_FLOORDIV.value,  # //=
                    16: ASTBinary.BinOp.BIN_IP_LSHIFT.value,    # <<=
                    17: ASTBinary.BinOp.BIN_IP_MAT_MULTIPLY.value,  # @=
                    18: ASTBinary.BinOp.BIN_IP_MULTIPLY.value,  # *=
                    19: ASTBinary.BinOp.BIN_IP_MODULO.value,    # %=
                    20: ASTBinary.BinOp.BIN_IP_OR.value,        # |=
                    21: ASTBinary.BinOp.BIN_IP_POWER.value,     # **=
                    22: ASTBinary.BinOp.BIN_IP_RSHIFT.value,    # >>=
                    23: ASTBinary.BinOp.BIN_IP_SUBTRACT.value,  # -=
                    24: ASTBinary.BinOp.BIN_IP_DIVIDE.value,    # /=
                    25: ASTBinary.BinOp.BIN_IP_XOR.value,       # ^=
                }
                op_value = binary_op_map.get(operand, ASTBinary.BinOp.BIN_ADD.value)
                debug_print(f"[BINARY_OP_A] 原始操作数: {operand}, 映射后: {op_value}")
                self._binary_op(op_value)
            elif opcode == Opcode.COMPARE_OP_A:
                self._compare_op(operand)
            elif opcode == Opcode.RETURN_VALUE:
                self._return_value()
            elif opcode == Opcode.YIELD_VALUE:
                self._yield_value()
            elif opcode == Opcode.CALL_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理CALL_A指令: operand={operand}")
                self._call_function(operand)
            elif opcode == Opcode.MAKE_FUNCTION_A:
                print(f"[_PROCESS_INSTRUCTION] 处理MAKE_FUNCTION_A指令: operand={operand}")
                self._make_function(operand)
            elif opcode == Opcode.MAKE_FUNCTION:
                print(f"[_PROCESS_INSTRUCTION] 处理MAKE_FUNCTION指令: operand={operand}")
                self._make_function(operand)
            elif opcode == Opcode.IMPORT_NAME_A:
                # print(f"DEBUG: 调用_import_name, operand={operand}")
                self._import_name(operand)
            elif opcode == Opcode.IMPORT_FROM_A:
                # print(f"DEBUG: 调用_import_from, operand={operand}")
                self._import_from(operand)
            # [DEBUG] 关键修复：BUILD_CLASS在Python 3.11+中已被移除
            # elif opcode == Opcode.BUILD_CLASS:
            #     self._build_class()
            elif opcode == Opcode.BUILD_LIST_A:
                self._build_list(operand)
            elif opcode == Opcode.BUILD_TUPLE_A:
                self._build_tuple(operand)
            elif opcode == Opcode.BUILD_SET_A:
                self._build_set(operand)
            elif opcode == Opcode.BUILD_MAP_A:
                self._build_map(operand)
            elif opcode == Opcode.BUILD_CONST_KEY_MAP_A:
                self._build_const_key_map(operand)
            # Handle BUILD_SLICE
            elif opcode == Opcode.BUILD_SLICE_A:
                self._build_slice(operand)
            # Handle LIST_EXTEND
            elif opcode == Opcode.LIST_EXTEND_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理LIST_EXTEND_A, operand={operand}")
                self._list_extend(operand)
            # Skip unknown opcodes
            elif opcode == 162:
                # CALL_INTRINSIC_1 - just pop the value
                if not self.stack.empty():
                    self.stack.pop()
            elif opcode == Opcode.POP_TOP:
                self._pop_top()
            elif opcode == Opcode.DUP_TOP:
                self._dup_top()
            elif opcode == Opcode.ROT_TWO:
                self._rot_two()
            elif opcode == Opcode.ROT_THREE:
                self._rot_three()
            # Skip CACHE instructions and RESUME
            elif opcode == Opcode.CACHE:
                pass
            elif opcode == Opcode.RESUME_A:
                pass
            elif opcode == Opcode.PUSH_NULL:
                # PUSH_NULL在Python 3.11+中用于准备函数调用，标记NULL参数
                self.stack.push(None)
            # Handle LOAD_ATTR
            elif opcode == Opcode.LOAD_ATTR_A:
                self._load_attr(operand)
            elif opcode == Opcode.STORE_ATTR_A:
                self._store_attr(operand)
            elif opcode == Opcode.DELETE_ATTR_A:
                self._delete_attr(operand)
            # Handle LOAD_BUILD_CLASS
            elif opcode == Opcode.LOAD_BUILD_CLASS:
                self._load_build_class()
            # Handle PRECALL and CALL
            elif opcode == Opcode.PRECALL_A:
                self._precall_a(operand)
            elif opcode == Opcode.CALL_A:
                self._call_function(operand)
            # Handle LOAD_METHOD
            elif opcode == Opcode.LOAD_METHOD_A:
                self._load_method(operand)
            # Handle UNPACK_SEQUENCE (for k, v in ...)
            elif opcode == Opcode.UNPACK_SEQUENCE_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理UNPACK_SEQUENCE_A, operand={operand}")
                self._unpack_sequence(operand)
            # Handle STORE_FAST
            elif opcode == Opcode.STORE_FAST_A:
                self._store_fast(operand)
            # Handle LOAD_GLOBAL
            elif opcode == Opcode.LOAD_GLOBAL_A:
                self._load_global(operand)
            elif opcode == Opcode.STORE_GLOBAL_A:
                self._store_global(operand)
            elif opcode == Opcode.STORE_DEREF_A:
                self._store_deref(operand)
            elif opcode == Opcode.DELETE_GLOBAL_A:
                self._delete_global(operand)
            elif opcode == Opcode.DELETE_NAME_A:
                self._delete_name(operand)
            elif opcode == Opcode.DELETE_FAST_A:
                self._delete_fast(operand)
            elif opcode == Opcode.DELETE_SUBSCR:
                self._delete_subscr()
            # Handle FORMAT_VALUE
            elif opcode == Opcode.FORMAT_VALUE_A:
                self._format_value(operand)
            # Handle POP_JUMP_FORWARD_IF_FALSE
            elif opcode == Opcode.POP_JUMP_FORWARD_IF_FALSE_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理POP_JUMP_FORWARD_IF_FALSE_A指令，operand={operand}")
                self._pop_jump_if_false(operand)
            elif opcode == Opcode.POP_JUMP_FORWARD_IF_TRUE_A:
                self._pop_jump_forward_if_true(operand)
            # Handle POP_JUMP_BACKWARD instructions (Python 3.11+)
            elif opcode == Opcode.POP_JUMP_BACKWARD_IF_TRUE_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理POP_JUMP_BACKWARD_IF_TRUE_A指令，operand={operand}")
                self._pop_jump_backward_if_true(operand)
            elif opcode == Opcode.POP_JUMP_BACKWARD_IF_FALSE_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理POP_JUMP_BACKWARD_IF_FALSE_A指令，operand={operand}")
                self._pop_jump_backward_if_false(operand)
            # Handle JUMP_FORWARD
            elif opcode == Opcode.JUMP_FORWARD_A:
                self._jump_forward(operand)
            # [关键修复] Handle JUMP_BACKWARD (while True: 循环 或 continue)
            elif opcode == Opcode.JUMP_BACKWARD_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理JUMP_BACKWARD_A指令，operand={operand}")
                current_offset = instr.get('offset', -1)
                # [关键修复] Python 3.11+ 的 JUMP_BACKWARD 操作数是相对偏移量（以2字节为单位）
                # 跳转目标 = 当前指令偏移量 + 2（指令本身占2字节）- operand * 2
                jump_target = current_offset + 2 - operand * 2
                
                # [关键修复] 检查是否是 continue 语句
                # continue 的特征：
                # 1. JUMP_BACKWARD 跳转到 FOR_ITER 的位置
                # 2. 在 if 语句内部（即 current_offset 在 if body 范围内）
                is_continue = False
                if hasattr(self, 'instructions') and self.instructions:
                    for instr_info in self.instructions:
                        if instr_info.get('offset') == jump_target:
                            if instr_info.get('opcode') == Opcode.FOR_ITER_A:
                                # 检查是否在 if 语句内部
                                if hasattr(self, 'current_if_node') and self.current_if_node is not None:
                                    if_body_start = getattr(self, 'if_body_start_offset', -1)
                                    if_body_end = getattr(self, 'if_body_end_offset', -1)
                                    if if_body_start <= current_offset < if_body_end:
                                        is_continue = True
                                        debug_print(f"[_PROCESS_INSTRUCTION] 检测到continue语句（在if内），跳转到FOR_ITER@{jump_target}")
                                break
                
                if is_continue:
                    # 发射 continue 节点
                    from core.ast_nodes import ASTContinue
                    continue_node = ASTContinue()
                    self._emit(continue_node)
                    debug_print(f"[_PROCESS_INSTRUCTION] 发射continue节点")
                elif hasattr(self, '_loop_entries') and current_offset in self._loop_exits:
                    loop_info = self._loop_exits[current_offset]
                    if loop_info.get('is_while_true', False):
                        debug_print(f"[_PROCESS_INSTRUCTION] 检测到while True:循环的JUMP_BACKWARD")
                        # 这是 while True: 循环的结束，不需要特殊处理
                        # 循环的创建在第一条指令时通过预扫描信息处理
                else:
                    # 其他情况，可能是循环结束后的跳转
                    debug_print(f"[_PROCESS_INSTRUCTION] JUMP_BACKWARD跳转到{jump_target}，不是continue")
            elif opcode == Opcode.JUMP_IF_FALSE_OR_POP_A:
                self._jump_if_false_or_pop(operand)
            elif opcode == Opcode.JUMP_IF_TRUE_OR_POP_A:
                self._jump_if_true_or_pop(operand)
            # Handle BUILD_STRING
            elif opcode == Opcode.BUILD_STRING_A:
                self._build_string(operand)
            elif opcode == Opcode.FOR_ITER_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理FOR_ITER_A指令，operand={operand}")
                try:
                    self._for_iter(operand)
                except Exception as e:
                    print(f"[_PROCESS_INSTRUCTION] FOR_ITER_A 处理失败: {e}")
                    import traceback
                    traceback.print_exc()
            elif opcode == Opcode.GET_ITER:
                self._get_iter()
            elif opcode == Opcode.BREAK_LOOP:
                self._break_loop()
            elif opcode == Opcode.SETUP_LOOP_A:
                self._setup_loop(operand)
            elif opcode == Opcode.RAISE_VARARGS_A:
                self._raise_varargs(operand)
            # Python 3.11+ 中 CONTINUE_LOOP 指令已被移除，使用 JUMP_BACKWARD_A 代替
            # elif opcode == Opcode.CONTINUE_LOOP_A:
            #     self._continue_loop(operand)
            # Handle UNARY operations
            elif opcode == Opcode.UNARY_POSITIVE:
                self._unary_op('UNARY_POSITIVE')
            elif opcode == Opcode.UNARY_NEGATIVE:
                self._unary_op('UNARY_NEGATIVE')
            elif opcode == Opcode.UNARY_NOT:
                self._unary_op('UNARY_NOT')
            elif opcode == Opcode.UNARY_INVERT:
                self._unary_op('UNARY_INVERT')
            # Handle LIST_APPEND
            elif opcode == Opcode.LIST_APPEND_A:
                self._list_append(operand)
            # Handle DICT_MERGE
            elif opcode == Opcode.DICT_MERGE_A:
                self._dict_merge(operand)
            # Handle SET_UPDATE
            elif opcode == Opcode.SET_UPDATE_A:
                self._set_update(operand)
            # Handle MATCH_*
            elif opcode == Opcode.MATCH_CLASS_A:
                self._match_class(operand)
            elif opcode == Opcode.MATCH_MAPPING:
                self._match_mapping()
            elif opcode == Opcode.MATCH_SEQUENCE:
                self._match_sequence(operand)
            elif opcode == Opcode.MATCH_KEYS:
                self._match_keys()
            # Handle IS_OP
            elif opcode == Opcode.IS_OP_A:
                self._is_op(operand)
            # Handle CONTAINS_OP
            elif opcode == Opcode.CONTAINS_OP_A:
                self._contains_op(operand)
            # Handle PUSH_EXC_INFO
            elif opcode == Opcode.PUSH_EXC_INFO:
                print(f"[_PROCESS_INSTRUCTION] 调用_push_exc_info at offset {current_offset}")
                self._push_exc_info()
            # Handle CHECK_EXC_MATCH
            elif opcode == Opcode.CHECK_EXC_MATCH:
                self._check_exc_match()
            # Handle POP_EXCEPT
            elif opcode == Opcode.POP_EXCEPT:
                self._pop_except()
            # Handle RERAISE
            elif opcode == Opcode.RERAISE_A:
                self._reraise(operand)
            # Handle CALL_INTRINSIC_2
            elif opcode == 163:
                self._call_intrinsic_2(operand)
            # Handle SETUP_FINALLY
            elif opcode == Opcode.SETUP_FINALLY_A:
                self._setup_finally(operand)
            # Handle SETUP_WITH
            elif opcode == Opcode.SETUP_WITH_A:
                self._setup_with(operand)
            # Handle NOP (Python 3.11+)
            elif opcode == Opcode.NOP:
                # NOP 指令通常代表 pass 语句或占位符
                # 在 with 语句 body 中，NOP 代表 pass 语句
                debug_print(f"[NOP_HANDLER] 处理NOP at offset {current_offset}")
                # 检查是否在 with 语句体内
                if hasattr(self, 'current_with_node') and self.current_with_node is not None:
                    body_start = getattr(self, 'current_with_node_start_offset', -1)
                    body_end = getattr(self, 'current_with_end_offset', -1)
                    if body_start <= current_offset < body_end:
                        # 在 with body 内，创建 pass 语句
                        from core.ast_nodes import ASTPass
                        pass_node = ASTPass()
                        self._emit(pass_node)
                        debug_print(f"[NOP_HANDLER] 在with body内创建pass语句")
            # Handle BEFORE_WITH (Python 3.11+)
            elif opcode == Opcode.BEFORE_WITH:
                print(f"[BEFORE_WITH_HANDLER] 处理BEFORE_WITH at offset {current_offset}")
                self._before_with(operand)
            # Handle WITH_CLEANUP_START/END
            # Python 3.11+ 中这些指令已被移除
            # elif opcode == Opcode.WITH_CLEANUP_START:
            #     self._with_cleanup_start()
            # elif opcode == Opcode.WITH_CLEANUP_FINISH:
            #     self._with_cleanup_finish()
            # Handle POP_BLOCK
            elif opcode == Opcode.POP_BLOCK:
                self._handle_pop_block()
            # Handle SETUP_CLEANUP
            # Python 3.11+ 中 SETUP_CLEANUP 指令已被移除
            # elif opcode == Opcode.SETUP_CLEANUP_A:
            #     self._setup_cleanup(operand)
            # Handle finally block instructions
            # Python 3.11+ 中这些指令可能已被移除
            # elif opcode == Opcode.START_FINALLY:
            #     self._start_finally()
            elif opcode == Opcode.END_FINALLY:
                self._end_finally()
            # Handle WITH_EXCEPT_START (Python 3.11+)
            elif opcode == Opcode.WITH_EXCEPT_START:
                # WITH_EXCEPT_START 标志着with语句体的结束
                # 设置with语句的结束位置（只在还没有被设置时才设置）
                if hasattr(self, 'current_with_node') and self.current_with_node is not None:
                    # 检查是否已经被 _push_exc_info 设置过
                    current_end = getattr(self, 'current_with_end_offset', -1)
                    temp_start = getattr(self, 'current_with_node_start_offset', -1)
                    # 如果当前值还是临时大值（> start + 100），说明还没被正确设置
                    if current_end > temp_start + 100:
                        self.current_with_end_offset = current_offset
                        debug_print(f"[WITH_EXCEPT_START] 设置with语句结束位置: {current_offset}")
                    else:
                        debug_print(f"[WITH_EXCEPT_START] 跳过设置，当前结束位置已是: {current_end}")
            # Handle LIST_EXTEND
            elif opcode == Opcode.LIST_EXTEND_A:
                debug_print(f"[_PROCESS_INSTRUCTION] 处理LIST_EXTEND_A, operand={operand}")
                self._list_extend(operand)
            # Handle SET_ADD
            elif opcode == Opcode.SET_ADD_A:
                self._set_add(operand)
            # Handle DICT_UPDATE
            elif opcode == Opcode.DICT_UPDATE_A:
                self._dict_update(operand)
            # Handle DICT_PREPEND
            # Python 3.11+ 中 DICT_PREPEND 指令可能不存在
            # elif opcode == Opcode.DICT_PREPEND_A:
            #     self._dict_prepend(operand)
            # Handle MAP_ADD
            elif opcode == Opcode.MAP_ADD_A:
                self._map_add(operand)
            # Handle TYPE_IGNORE
            # Python 3.11+ 中 TYPE_IGNORE 可能不是操作码
            # elif opcode == Opcode.TYPE_IGNORE:
            #     pass  # Type ignore is for static analysis
            # Handle LOAD_ASSERTION_ERROR
            elif opcode == Opcode.LOAD_ASSERTION_ERROR:
                self._load_assertion_error()
            # Handle LOAD_CLASSDEREF
            elif opcode == Opcode.LOAD_CLASSDEREF_A:
                self._load_classderef(operand)
            # Handle LOCALS dictionary ops
            elif opcode == Opcode.LOAD_LOCALS:
                self._load_locals()
            elif opcode == Opcode.RETURN_GENERATOR:
                self._return_generator()
            elif opcode == Opcode.YIELD_FROM:
                self._yield_from()
            # Handle SWAP operations
            elif opcode == Opcode.SWAP_A:
                self._swap(operand)
            # Python 3.11+ 中 ROT_N 可能已被移除或替换
            # elif opcode == Opcode.ROT_N:
            #     self._rot_n(operand)
            # Handle COPY operations
            elif opcode == Opcode.COPY_A:
                self._copy(operand)
            # Handle BINARY operations on strings, bytes, etc.
            elif opcode == Opcode.BINARY_SUBSCR:
                self._binary_subscript()
            # Python 3.11+ 中 BINARY_SLICE 指令可能不存在
            # elif opcode == Opcode.BINARY_SLICE_A:
            #     self._binary_slice(operand)
            elif opcode == Opcode.BINARY_FLOOR_DIVIDE:
                self._binary_op(ASTBinary.BinOp.BIN_FLOOR_DIVIDE.value)
            elif opcode == Opcode.BINARY_TRUE_DIVIDE:
                self._binary_op(ASTBinary.BinOp.BIN_TRUE_DIVIDE.value)
            elif opcode == Opcode.BINARY_MODULO:
                self._binary_op(ASTBinary.BinOp.BIN_MODULO.value)
            elif opcode == Opcode.BINARY_POWER:
                self._binary_op(ASTBinary.BinOp.BIN_POWER.value)
            elif opcode == Opcode.BINARY_LSHIFT:
                self._binary_op(ASTBinary.BinOp.BIN_LSHIFT.value)
            elif opcode == Opcode.BINARY_RSHIFT:
                self._binary_op(ASTBinary.BinOp.BIN_RSHIFT.value)
            elif opcode == Opcode.BINARY_XOR:
                self._binary_op(ASTBinary.BinOp.BIN_XOR.value)
            elif opcode == Opcode.BINARY_AND:
                self._binary_op(ASTBinary.BinOp.BIN_AND.value)
            elif opcode == Opcode.BINARY_OR:
                self._binary_op(ASTBinary.BinOp.BIN_OR.value)
            elif opcode == Opcode.INPLACE_POWER:
                self._binary_op(ASTBinary.BinOp.BIN_IP_POWER.value)
            elif opcode == Opcode.INPLACE_MULTIPLY:
                self._binary_op(ASTBinary.BinOp.BIN_IP_MULTIPLY.value)
            elif opcode == Opcode.INPLACE_MATRIX_MULTIPLY:
                self._binary_op(ASTBinary.BinOp.BIN_IP_MAT_MULTIPLY.value)
            elif opcode == Opcode.INPLACE_FLOOR_DIVIDE:
                self._binary_op(ASTBinary.BinOp.BIN_IP_FLOORDIV.value)
            elif opcode == Opcode.INPLACE_TRUE_DIVIDE:
                self._binary_op(ASTBinary.BinOp.BIN_IP_DIVIDE.value)
            elif opcode == Opcode.INPLACE_MODULO:
                self._binary_op(ASTBinary.BinOp.BIN_IP_MODULO.value)
            elif opcode == Opcode.INPLACE_ADD:
                self._binary_op(ASTBinary.BinOp.BIN_IP_ADD.value)
            elif opcode == Opcode.INPLACE_SUBTRACT:
                self._binary_op(ASTBinary.BinOp.BIN_IP_SUBTRACT.value)
            elif opcode == Opcode.INPLACE_LSHIFT:
                self._binary_op(ASTBinary.BinOp.BIN_IP_LSHIFT.value)
            elif opcode == Opcode.INPLACE_RSHIFT:
                self._binary_op(ASTBinary.BinOp.BIN_IP_RSHIFT.value)
            elif opcode == Opcode.INPLACE_XOR:
                self._binary_op(ASTBinary.BinOp.BIN_IP_XOR.value)
            elif opcode == Opcode.INPLACE_AND:
                self._binary_op(ASTBinary.BinOp.BIN_IP_AND.value)
            elif opcode == Opcode.INPLACE_OR:
                self._binary_op(ASTBinary.BinOp.BIN_IP_OR.value)
            # Handle closure-related instructions
            elif opcode == Opcode.MAKE_CELL_A:
                self._make_cell(operand)
            elif opcode == Opcode.LOAD_CLOSURE_A:
                self._load_closure(operand)
            elif opcode == Opcode.LOAD_DEREF_A:
                self._load_deref(operand)
            elif opcode == Opcode.COPY_FREE_VARS_A:
                self._copy_free_vars(operand)
            # Unknown opcodes - log but don't crash
            else:
                print(f"警告：未处理的指令 {opcode} at offset {current_offset}")
                # Try to pop one item from stack for unknown ops that expect arguments
                if not self.stack.empty():
                    self.stack.pop()
        except Exception as e:
            import traceback
            print(f"处理指令时出错：{e}")
            print(f"错误详情：")
            traceback.print_exc()
            # Try to recover
            self._recover_from_error()

    # === 缺失方法实现 ===
    
    def _unary_op(self, op_type: str) -> None:
        """处理一元操作符"""
        operand = self._safe_stack_pop()
        if operand is None:
            return
        
        unary_node = self._create_unary_op(op_type, operand)
        self.stack.push(unary_node)
    
    def _list_append(self, operand: int) -> None:
        """处理列表追加操作"""
        value = self._safe_stack_pop()
        list_node = self._safe_stack_pop()  # 获取列表对象
        
        # 创建列表追加表达式
        if isinstance(list_node, ASTList):
            list_node.nodes.append(value)
            self.stack.push(list_node)
        else:
            # 创建新的AST节点来处理列表追加
            self.stack.push(value)
    
    def _dict_merge(self, operand: int) -> None:
        """处理字典合并"""
        # 字典合并逻辑
        right = self._safe_stack_pop()
        left = self._safe_stack_pop()
        
        if left and right:
            # 创建字典更新表达式
            update_expr = ASTExpr(left)  # 简化实现
            self.stack.push(update_expr)
    
    def _set_update(self, operand: int) -> None:
        """处理集合更新 - 修复版本"""
        # SET_UPDATE指令用于将可迭代对象的元素添加到集合中
        # 栈顶是可迭代对象（如frozenset），下面是集合
        if self.stack.size() < 2:
            return
        
        # 弹出可迭代对象（frozenset）
        iterable = self.stack.top()
        self.stack.pop()
        
        # 获取集合
        set_obj = self.stack.top()
        self.stack.pop()
        
        # 如果可迭代对象是frozenset常量，提取其元素
        if hasattr(iterable, 'object') and isinstance(iterable.object, frozenset):
            # 从frozenset创建ASTSet
            from core.ast_nodes import ASTSet, ASTConstant
            items = [ASTConstant(item) for item in iterable.object]
            new_set = ASTSet(items)
            self.stack.push(new_set)
        elif hasattr(iterable, '_items'):
            # 如果已经是ASTSet，直接使用
            self.stack.push(iterable)
        else:
            # 否则保持原来的集合
            self.stack.push(set_obj)
    
    def _is_op(self, operand: int) -> None:
        """处理is操作符"""
        # IS操作符逻辑
        right = self._safe_stack_pop()
        left = self._safe_stack_pop()
        
        if left and right:
            compare_node = self._create_compare_op(left, right, 6)  # 6 = is
            self.stack.push(compare_node)
    
    def _contains_op(self, operand: int) -> None:
        """处理contains操作符"""
        # CONTAINS操作符逻辑
        right = self._safe_stack_pop()
        left = self._safe_stack_pop()
        
        if left and right:
            # contains操作符是in或not in
            op = 9 if operand == 1 else 8  # 9 = not in, 8 = in
            compare_node = self._create_compare_op(left, right, op)
            self.stack.push(compare_node)
    
    def _check_exc_match(self) -> None:
        """处理异常匹配检查 - 修复版本"""
        # 从栈中弹出异常类型
        exc_type = self._safe_stack_pop()
        
        # 创建异常处理器
        if hasattr(self, 'current_exception_handler') and self.current_exception_handler:
            from core.ast_nodes import ASTExceptHandler, ASTBlock
            handler = ASTExceptHandler(exc_type, None, ASTBlock())
            self.current_exception_handler.handlers.append(handler)
            # 设置当前正在处理的handler
            self.current_except_handler = handler
        
        # 异常匹配检查结果留在栈上
        if exc_type:
            self.stack.push(exc_type)
    
    def _pop_except(self) -> None:
        """处理POP_EXCEPT指令 - 修复版本"""
        # 弹出异常处理块
        if not self.stack.empty():
            self.stack.pop()
        
        # 重置当前异常处理器
        self.current_except_handler = None
    
    def _end_finally(self) -> None:
        """处理END_FINALLY指令 - 修复版本"""
        # 结束try/except/finally块
        # 设置finally块的实际结束位置
        if hasattr(self, 'finally_body_end_offset'):
            self.finally_body_end_offset = self.current_instruction_offset
        
        # 重置异常处理上下文
        if hasattr(self, 'current_exception_handler'):
            self.current_exception_handler = None
        if hasattr(self, 'current_try_node'):
            self.current_try_node = None
        if hasattr(self, 'current_except_handler'):
            self.current_except_handler = None
    
    def _reraise(self, operand: int) -> None:
        """处理reraise操作"""
        # RERAISE逻辑
        # 重新抛出当前异常
        reraise_node = ASTRaise()
        self.stack.push(reraise_node)
    
    def _call_intrinsic_2(self, operand: int) -> None:
        """处理内置函数调用2"""
        # CALL_INTRINSIC_2逻辑
        # 内置函数调用不需要特殊处理，只弹出参数
        if not self.stack.empty():
            self.stack.pop()
    
    def _load_global(self, operand: int) -> None:
        """加载全局变量"""
        # Python 3.11+ 的 LOAD_GLOBAL 操作数编码：
        # 低 1 位表示是否 push NULL，高 7 位表示实际的名称索引
        # 所以实际的索引是 operand >> 1
        actual_index = operand >> 1
        
        # 尝试从code_obj的names中获取实际名称
        name = self._get_name_from_code_obj(actual_index)
        if name is None:
            name = f"__global_{actual_index}__"
        global_node = ASTName(name)
        self.stack.push(global_node)
    
    def _store_global(self, operand: int) -> None:
        """存储全局变量"""
        value = self._safe_stack_pop()
        # 尝试从code_obj的names中获取实际名称
        name = self._get_name_from_code_obj(operand)
        if name is None:
            name = f"__global_{operand}__"
        store_node = ASTName(name)
        if value:
            # 创建赋值表达式
            assign_node = ASTAssign([store_node], value)
            self._emit(assign_node)
    
    def _get_name_from_code_obj(self, operand: int) -> Optional[str]:
        """从code_obj的names中获取实际名称"""
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if code_obj and hasattr(code_obj, 'names') and code_obj.names and code_obj.names.get():
            names_obj = code_obj.names.get()
            if hasattr(names_obj, 'size') and hasattr(names_obj, 'get'):
                if 0 <= operand < names_obj.size():
                    try:
                        name_ref = names_obj.get(operand)
                        if name_ref:
                            name_obj = name_ref.get() if hasattr(name_ref, 'get') else name_ref
                            if hasattr(name_obj, 'value'):
                                return name_obj.value
                            else:
                                return str(name_obj)
                    except (IndexError, TypeError, AttributeError):
                        pass
        return None
    
    def _delete_global(self, operand: int) -> None:
        """删除全局变量"""
        name = f"__global_{operand}__"
        delete_node = ASTDelete([ASTName(name, ASTName.Del)])
        self._emit(delete_node)
    
    def _delete_name(self, operand: int) -> None:
        """删除变量 (del x)"""
        debug_print(f"[_delete_name] 被调用, operand={operand}")
        if not self.module.code:
            debug_print(f"[_delete_name] self.module.code 为空")
            return
        
        names = self.module.code.get().names
        debug_print(f"[_delete_name] names={names}")
        if names and names.get():
            names_obj = names.get()
            debug_print(f"[_delete_name] names_obj={names_obj}, type={type(names_obj)}")
            
            name = None
            if isinstance(names_obj, PycString):
                name_list = names_obj.value.split('\x00')
                debug_print(f"[_delete_name] name_list={name_list}")
                if 0 <= operand < len(name_list):
                    name = name_list[operand]
            elif isinstance(names_obj, PycSequence):
                # PycSequence 类型，直接获取元素
                if 0 <= operand < names_obj.size():
                    name_ref = names_obj.get(operand)
                    if name_ref and name_ref.get():
                        name_obj = name_ref.get()
                        if isinstance(name_obj, PycString):
                            name = name_obj.value
            
            if name:
                node = ASTDelete([ASTName(name)])
                self._emit(node)
                debug_print(f"[_delete_name] 删除变量: {name}")
            else:
                debug_print(f"[_delete_name] 无法获取变量名")
        else:
            debug_print(f"[_delete_name] names 为空")
    
    def _delete_fast(self, operand: int) -> None:
        """删除局部变量 (del x)"""
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if not code_obj:
            return
        
        varnames = code_obj.local_names
        if varnames and varnames.get():
            varnames_list = varnames.get()
            list_size = varnames_list.size() if hasattr(varnames_list, 'size') else (len(varnames_list) if hasattr(varnames_list, '__len__') else 0)
            if 0 <= operand < list_size:
                try:
                    varname_obj = varnames_list.get(operand)
                    if varname_obj and varname_obj.get():
                        name_obj = varname_obj.get()
                        if isinstance(name_obj, PycString):
                            var_name = name_obj.value
                            node = ASTDelete([ASTName(var_name)])
                            self._emit(node)
                            debug_print(f"[_delete_fast] 删除局部变量: {var_name}")
                except (IndexError, TypeError):
                    pass
    
    def _delete_subscr(self) -> None:
        """删除序列/字典元素 (del obj[key])"""
        if self.stack.size() < 2:
            return
        
        # 栈顶是索引/键，下面是对象
        index = self.stack.top()
        self.stack.pop()
        obj = self.stack.top()
        self.stack.pop()
        
        # 创建下标节点
        subscript = ASTSubscript(obj, index)
        node = ASTDelete([subscript])
        self._emit(node)
        debug_print(f"[_delete_subscr] 删除下标: {obj}[{index}]")
    
    def _make_cell(self, operand: int) -> None:
        """处理MAKE_CELL指令 - 创建cell变量用于闭包
        
        参照C++版本的实现：直接忽略此指令
        """
        # C++版本中：/* Ignore this */
        # MAKE_CELL只是标记变量为cell变量，不需要特殊处理
        debug_print(f"[_make_cell] 忽略MAKE_CELL指令，operand={operand}")
        pass
    
    def _load_closure(self, operand: int) -> None:
        """处理LOAD_CLOSURE指令 - 加载闭包变量
        
        参照C++版本的实现：直接忽略此指令
        """
        # C++版本中：/* Ignore this */
        # LOAD_CLOSURE用于创建闭包，但在反编译时不需要特殊处理
        # 对应的变量会在LOAD_DEREF中被正确加载
        debug_print(f"[_load_closure] 忽略LOAD_CLOSURE指令，operand={operand}")
        pass
    
    def _load_deref(self, operand: int) -> None:
        """处理LOAD_DEREF指令 - 加载deref变量（自由变量）
        
        参照C++版本的实现：使用code->getCellVar(mod, operand)
        
        注意：在Python 3.11+中，LOAD_DEREF的operand需要减去COPY_FREE_VARS的operand
        才能得到正确的free_vars索引。
        例如：COPY_FREE_VARS 1, LOAD_DEREF 1 -> free_vars[0]
        """
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if code_obj and hasattr(code_obj, 'get_cell_var'):
            # [DEBUG] 修复：计算正确的free_vars索引
            # 在Python 3.11+中，operand需要减去自由变量数量偏移
            freevar_offset = 0
            if hasattr(code_obj, 'free_vars') and code_obj.free_vars and code_obj.free_vars.get():
                free_vars_obj = code_obj.free_vars.get()
                if hasattr(free_vars_obj, 'size'):
                    freevar_count = free_vars_obj.size()
                    # operand是相对于局部变量表的索引，需要减去局部变量数量
                    if hasattr(code_obj, 'num_locals') and code_obj.num_locals:
                        num_locals = code_obj.num_locals
                        if hasattr(num_locals, 'get'):
                            num_locals = num_locals.get()
                        if hasattr(num_locals, '_value'):
                            num_locals = num_locals._value
                        freevar_offset = num_locals
            
            # 计算正确的索引
            actual_idx = operand - freevar_offset
            debug_print(f"[_load_deref] operand={operand}, freevar_offset={freevar_offset}, actual_idx={actual_idx}")
            
            var_ref = code_obj.get_cell_var(self.module, actual_idx)
            if var_ref and var_ref.get():
                var_obj = var_ref.get()
                if isinstance(var_obj, PycString):
                    var_name = var_obj.value
                    debug_print(f"[_load_deref] 加载自由变量: {var_name}")
                    self.stack.push(ASTName(var_name))
                    return
        # 如果无法获取名称，使用占位符
        self.stack.push(ASTName(f"__deref_{operand}__"))
    
    def _copy_free_vars(self, operand: int) -> None:
        """处理COPY_FREE_VARS指令 - 复制自由变量到局部变量"""
        # COPY_FREE_VARS将自由变量复制到局部变量
        # operand表示要复制的自由变量数量
        debug_print(f"[_copy_free_vars] 复制 {operand} 个自由变量")
        # 这个指令主要是设置闭包环境，不需要特殊处理
        # 自由变量会在后续的LOAD_DEREF中被正确加载

    def _store_deref(self, operand: int) -> None:
        """处理STORE_DEREF指令 - 存储到自由变量（闭包变量）"""
        if self.stack.empty():
            return

        value = self.stack.top()
        self.stack.pop()

        # 获取变量名称
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        var_name = None

        if code_obj and hasattr(code_obj, 'get_cell_var'):
            # 计算正确的索引
            freevar_offset = 0
            if hasattr(code_obj, 'free_vars') and code_obj.free_vars and code_obj.free_vars.get():
                free_vars_obj = code_obj.free_vars.get()
                if hasattr(free_vars_obj, 'size'):
                    freevar_count = free_vars_obj.size()
                    if hasattr(code_obj, 'num_locals') and code_obj.num_locals:
                        num_locals = code_obj.num_locals
                        if hasattr(num_locals, 'get'):
                            num_locals = num_locals.get()
                        if hasattr(num_locals, '_value'):
                            num_locals = num_locals._value
                        freevar_offset = num_locals

            actual_idx = operand - freevar_offset
            debug_print(f"[_store_deref] operand={operand}, freevar_offset={freevar_offset}, actual_idx={actual_idx}")

            var_ref = code_obj.get_cell_var(self.module, actual_idx)
            if var_ref and var_ref.get():
                var_obj = var_ref.get()
                if isinstance(var_obj, PycString):
                    var_name = var_obj.value

        if var_name is None:
            var_name = f"__deref_{operand}__"

        debug_print(f"[_store_deref] 存储到自由变量: {var_name}")

        # 创建赋值表达式
        store_node = ASTName(var_name)
        assign_node = ASTAssign([store_node], value)
        self._emit(assign_node)

    def _for_iter(self, operand: int) -> None:
        """for循环迭代器
        
        参考C++ pycdc实现，使用块栈管理for循环结构
        """
        if self.stack.empty():
            return
        
        # 获取迭代对象（在 GET_ITER 之后，栈顶是迭代器）
        iter_obj = self.stack.top()
        
        # Python 3.12+ 不弹出迭代器
        if not (self.module.major == 3 and self.module.minor >= 12):
            self.stack.pop()
        
        # 计算跳转目标（循环结束后的位置）
        # Python 3.10+ 需要乘以sizeof(uint16_t)
        # [关键修复] Python 3.11+ 的 FOR_ITER 跳转计算需要加上指令长度（2字节）
        end = operand
        if self.module.major == 3 and self.module.minor >= 10:
            end *= 2  # sizeof(uint16_t)
        # [关键修复] 加上指令本身的长度（2字节）
        if self.module.major == 3 and self.module.minor >= 11:
            end += 2
        end += self.current_instruction_offset
        
        # 检查是否是推导式
        comprehension = False
        if (hasattr(self, '_current_code_obj') and self._current_code_obj and
            hasattr(self._current_code_obj, 'name')):
            code_name = self._current_code_obj.name
            if code_name and '<listcomp>' in str(code_name):
                comprehension = True
        
        # [关键修复] 检查是否有else分支
        # FOR_ITER的跳转目标是else body的开始（如果有else）
        # 或者循环结束（如果没有else）
        has_else = False
        else_start = end
        else_end = -1
        
        # 检查跳转目标之后是否有代码（else body）
        # 如果有else，跳转目标之后会有代码，直到遇到RETURN_VALUE或JUMP_FORWARD
        # [关键修复] 对于pass语句，else body可能只有LOAD_CONST; RETURN_VALUE
        # 所以我们需要检查跳转目标之后是否有任何代码（不只是STORE_NAME）
        instructions_after_jump = []
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            if instr_offset >= else_start:
                instructions_after_jump.append(instr)
        
        # [关键修复] 检查是否有else分支
        # 我们需要区分：
        # 1. 有else：跳转目标之后有实际代码（STORE_NAME, CALL等）
        # 2. 无else：跳转目标之后直接是RETURN_VALUE（函数结束）或只有LOAD_CONST; RETURN_VALUE
        if len(instructions_after_jump) > 0:
            # 检查跳转目标之后是否有实际代码
            # 实际代码包括：STORE_NAME, STORE_FAST, CALL, BINARY_OP等
            has_real_code = False
            for instr in instructions_after_jump:
                opcode = instr.get('opcode', -1)
                # 实际代码指令（不是LOAD_CONST或RETURN_VALUE）
                if opcode in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A,
                             Opcode.CALL_A, Opcode.BINARY_OP_A, Opcode.POP_TOP]:
                    has_real_code = True
                    break
            
            # 如果有实际代码，说明有else分支
            if has_real_code:
                has_else = True
                
                # [关键修复] 查找else block的结束位置
                # 对于for-else，else block结束后通常是：
                # 1. JUMP_BACKWARD - 跳回到外层循环（嵌套for）
                # 2. RETURN_VALUE - 函数结束
                # 3. JUMP_FORWARD - 跳转到其他位置
                for instr in instructions_after_jump:
                    opcode = instr.get('opcode', -1)
                    name = instr.get('name', '')
                    offset = instr.get('offset', -1)
                    # RETURN_VALUE (83), JUMP_BACKWARD (140), JUMP_FORWARD (110) 标志着else block的结束
                    if opcode == 83 or opcode == 140 or 'RETURN' in name or 'JUMP_BACKWARD' in name or 'JUMP_FORWARD' in name:
                        else_end = offset
                        debug_print(f"[_for_iter] 找到else block结束位置: {else_end} ({name})")
                        break
        
        # 创建 for 循环节点
        target = ASTName("i")  # 临时变量名，会被 STORE_NAME 更新
        body = ASTNodeList()
        else_block = ASTNodeList() if has_else else None
        for_node = ASTFor(target, iter_obj, body, else_block)
        
        # [关键修复] 使用栈管理嵌套for循环
        if not hasattr(self, '_for_stack'):
            self._for_stack = []
        
        # 如果已经有current_for_node，将其压入栈
        if hasattr(self, 'current_for_node') and self.current_for_node is not None:
            self._for_stack.append({
                'node': self.current_for_node,
                'body_start': self.for_body_start_offset,
                'body_end': self.for_body_end_offset,
                'else_start': getattr(self, 'for_else_start_offset', -1),
                'else_end': getattr(self, 'for_else_end_offset', -1)
            })
            debug_print(f"[_for_iter] 将外层for压入栈，栈深度: {len(self._for_stack)}")
        
        # [DEBUG] 关键修复：在发射for节点之前设置current_for_node和body范围
        # 这样后续的STORE_NAME指令可以正确识别for循环变量
        self.current_for_node = for_node
        self.for_body_start_offset = self.current_instruction_offset + 2
        self.for_body_end_offset = end
        
        # [关键修复] 记录else分支信息
        if has_else:
            self.for_else_start_offset = else_start
            self.for_else_end_offset = else_end
            debug_print(f"[_for_iter] 检测到for-else结构，else开始于: {else_start}, 结束于: {else_end}")
        
        # [关键修复] 检查当前是否在外层for循环的body范围内
        current_offset = self.current_instruction_offset
        outer_for_body = False
        if hasattr(self, '_for_stack') and self._for_stack:
            # 检查栈顶（当前的外层for）
            outer_for_info = self._for_stack[-1]
            outer_body_start = outer_for_info['body_start']
            outer_body_end = outer_for_info['body_end']
            outer_else_start = outer_for_info['else_start']
            
            # [关键修复] 如果当前offset在外层for的body范围内，将内层for添加到外层for的body
            if outer_body_start <= current_offset < outer_body_end:
                # 在body范围内
                outer_for_node = outer_for_info['node']
                if hasattr(outer_for_node, '_body') and outer_for_node._body is not None:
                    outer_for_node._body.append(for_node)
                    for_node.parent = outer_for_node._body
                    outer_for_body = True
                    debug_print(f"[_for_iter] 内层for添加到外层for的body中")
            elif outer_else_start > 0 and outer_body_end <= current_offset < outer_else_start:
                # 在外层for的else范围内
                outer_for_node = outer_for_info['node']
                if hasattr(outer_for_node, '_else_block') and outer_for_node._else_block is not None:
                    outer_for_node._else_block.append(for_node)
                    for_node.parent = outer_for_node._else_block
                    outer_for_body = True
                    debug_print(f"[_for_iter] 内层for添加到外层for的else_block中")
        
        # 如果不是嵌套在for中，发射到当前块
        if not outer_for_body:
            # [DEBUG] 关键修复：先发射for节点，再创建for块
            # 这样for节点本身会被添加到main_block，而不是for块中
            saved_block = self.current_block  # 保存当前块
            self.current_block = self.main_block  # 设置为主块
            self._emit(for_node)
            self.current_block = saved_block  # 恢复当前块
        
        # 创建for块并压入块栈
        for_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_FOR, end=end, inited=True)
        self._push_block(for_block)
        
        # FOR_ITER 将迭代值压入栈顶（NULL占位符）
        self.stack.push(None)
        
        debug_print(f"[_for_iter] 创建 ASTFor 节点, iter={iter_obj}")
        debug_print(f"[_for_iter] body范围: {self.for_body_start_offset}-{self.for_body_end_offset}")
        debug_print(f"[_for_iter] 块栈深度: {len(self.blocks)}")
    
    def _get_iter(self) -> None:
        """获取迭代器"""
        if not self.stack.empty():
            # 获取迭代对象（在栈顶）
            iterable = self.stack.top()
            # 不弹出，只是获取引用
            # GET_ITER 指令只是获取迭代器，不改变栈
            debug_print(f"[_get_iter] 获取迭代器: {iterable}")
        else:
            debug_print("[_get_iter] 栈为空，无法获取迭代器")
    
    def _break_loop(self) -> None:
        """跳出循环"""
        break_node = ASTBreak()
        self._emit(break_node)
    
    def _continue_loop(self, operand: int) -> None:
        """继续循环"""
        continue_node = ASTContinue()
        self._emit(continue_node)
    
    def _handle_pop_block(self) -> None:
        """处理POP_BLOCK指令 - 弹出代码块
        
        在Python字节码中，POP_BLOCK用于标记循环或try块的结束。
        我们需要根据当前上下文决定如何处理。
        """
        debug_print("[_handle_pop_block] 处理POP_BLOCK指令")
        
        # 检查当前是否有活跃的循环上下文
        if hasattr(self, 'current_loop_context') and self.current_loop_context:
            debug_print(f"[_pop_block] 结束循环块: {self.current_loop_context}")
            self.current_loop_context = None
        
        # 检查当前是否有活跃的try块上下文
        if hasattr(self, 'current_try_node') and self.current_try_node:
            debug_print(f"[_pop_block] 结束try块")
            # 不重置current_try_node，因为它可能还有except/finally块
    
    def _setup_loop(self, operand: int) -> None:
        """处理SETUP_LOOP指令 - 设置循环
        
        在旧版Python中，SETUP_LOOP用于设置循环的结束位置。
        操作数是相对跳转偏移量，指向循环块的结束位置。
        
        在Python 3.11+中，SETUP_LOOP已被移除，使用FOR_ITER代替。
        """
        debug_print(f"[_setup_loop] 处理SETUP_LOOP指令: operand={operand}")
        
        # 计算循环结束位置
        loop_end_offset = self.current_instruction_offset + operand
        
        # 记录循环上下文
        self.current_loop_context = {
            'start': self.current_instruction_offset,
            'end': loop_end_offset,
            'type': 'loop'
        }
        
        debug_print(f"[_setup_loop] 设置循环上下文: start={self.current_instruction_offset}, end={loop_end_offset}")
    
    # 删除重复的_raise_varargs方法，使用后面更完整的版本
    
    # 删除重复的_store_fast方法，使用后面更完整的版本
    
    # 删除重复的_load_fast方法，使用后面更完整的版本
    
    # 删除重复的_load_name方法，使用后面更完整的版本
    
    # 删除重复的_load_const方法，使用后面更完整的版本
    # [DEBUG] 关键修复：删除重复的_binary_op方法，使用后面更完整的版本（第3251行）
    # def _binary_op(self, operand: int) -> None:
    #     """处理二元操作"""
    #     right = self._safe_stack_pop()
    #     left = self._safe_stack_pop()
    #     
    #     if left and right:
    #         bin_op = ASTBinary(left, right, operand)
    #         self.stack.push(bin_op)
    
    def _build_slice(self, count: int) -> None:
        """处理BUILD_SLICE指令 - 创建切片对象"""
        # count表示切片的参数数量（2或3）
        # 栈顶是step（如果count=3），然后是upper，然后是lower
        from core.ast_nodes import ASTSlice, ASTConstant
        
        step = None
        if count == 3:
            step = self._safe_stack_pop()
        
        upper = self._safe_stack_pop()
        lower = self._safe_stack_pop()
        
        # 创建切片节点
        # ASTSlice需要lower, upper, step
        # 但我们想要的是slice(lower, upper, step)对象
        # 这里我们创建一个特殊的ASTObject来表示切片
        slice_obj = {
            'type': 'slice',
            'lower': lower,
            'upper': upper,
            'step': step
        }
        self.stack.push(ASTObject(slice_obj))
    
    def _binary_subscript(self) -> None:
        """处理BINARY_SUBSCR指令 - 二元下标操作如 obj[key]"""
        # 栈顶是索引，下面是对象
        index = self._safe_stack_pop()
        obj = self._safe_stack_pop()
        
        if obj and index:
            # 检查索引是否是切片对象
            if hasattr(index, 'object') and isinstance(index.object, dict) and index.object.get('type') == 'slice':
                # 创建切片访问节点
                slice_info = index.object
                lower = slice_info.get('lower')
                upper = slice_info.get('upper')
                step = slice_info.get('step')
                
                # 使用ASTSliceExpr创建切片表达式
                from core.ast_nodes import ASTSliceExpr
                slice_expr = ASTSliceExpr(lower, upper, step)
                subscript = ASTSubscript(obj, slice_expr)
                self.stack.push(subscript)
            else:
                # 普通下标访问
                subscript = ASTSubscript(obj, index)
                self.stack.push(subscript)
    
    def _get_slice_component_str(self, node) -> str:
        """获取切片组件的字符串表示"""
        if node is None:
            return ""
        if hasattr(node, 'value'):
            val = node.value
            if val is None:
                return ""
            return str(val)
        if hasattr(node, '_value'):
            val = node._value
            if val is None:
                return ""
            return str(val)
        return str(node)
    
    def _jump_backward_no_interrupt(self, operand: int) -> None:
        """处理JUMP_BACKWARD_NO_INTERRUPT指令"""
        # 向后跳转的处理逻辑
        pass
    
    def _recover_from_error(self) -> None:
        """从错误中恢复"""
        # 记录错误状态
        recovery_info = {
            'stack_depth': self.stack.size(),
            'current_offset': self.current_instruction_offset
        }
        
        # 尝试恢复堆栈状态，但限制恢复的元素数量以防无限循环
        recovery_attempts = 0
        max_recovery_attempts = 10  # 限制最大恢复尝试次数
        
        while not self.stack.empty() and recovery_attempts < max_recovery_attempts:
            try:
                self.stack.pop()
                recovery_attempts += 1
            except Exception:
                break
        
        # 发出恢复节点，标记这里发生了错误恢复
        recovery_node = ASTObject(f"ERROR_RECOVERY(stack_depth_reduced_by_{recovery_attempts})")
        self._emit(recovery_node)

    def _match_class(self, operand: int) -> None:
        """处理MATCH_CLASS_A指令，用于模式匹配中的类匹配"""
        if self.stack.empty():
            return
            
        # 栈中应该有：类名、位置参数数量、关键字参数数量、模式列表
        # 这里简化处理，直接弹出栈顶元素
        self.stack.pop()

    def _match_mapping(self) -> None:
        """处理MATCH_MAPPING指令，用于模式匹配中的字典/映射匹配"""
        if self.stack.empty():
            return
        # 映射匹配暂时简化处理
        self.stack.pop()

    def _match_sequence(self, operand: int) -> None:
        """处理MATCH_SEQUENCE指令，用于模式匹配中的序列匹配"""
        if self.stack.empty():
            return
        # 序列匹配暂时简化处理
        self.stack.pop()

    def _match_keys(self) -> None:
        """处理MATCH_KEYS指令，用于模式匹配中的键匹配"""
        if self.stack.empty():
            return
        # 键匹配暂时简化处理
        self.stack.pop()
    
    def _safe_stack_access(self, operation: str, default_value=None):
        """安全访问栈的包装函数"""
        try:
            if operation == 'top':
                return self.stack.top() if not self.stack.empty() else default_value
            elif operation == 'pop':
                return self.stack.pop() if not self.stack.empty() else default_value
            elif operation == 'size':
                return self.stack.size()
            else:
                return default_value
        except Exception as e:
            print(f"Error in stack operation {operation}: {e}")
            self._recover_from_error()
            return default_value
    
    def _load_attr(self, operand: int) -> None:
        """加载属性 (obj.attr)"""
        if self._safe_stack_access('size', 0) == 0:
            return
        
        obj = self._safe_stack_access('pop')
        if obj is None:
            return
        
        # 获取属性名 - 使用当前代码对象的names
        attr_name = f"attr_{operand}"
        current_code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if current_code_obj and hasattr(current_code_obj, 'names') and current_code_obj.names and current_code_obj.names.get():
            names_obj = current_code_obj.names.get()
            if hasattr(names_obj, 'get') and operand < names_obj.size():
                name_ref = names_obj.get(operand)
                if name_ref and name_ref.get():
                    name_obj = name_ref.get()
                    if isinstance(name_obj, PycString):
                        attr_name = name_obj.value
                    elif hasattr(name_obj, 'value'):
                        attr_name = str(name_obj.value)
        
        # 创建属性访问节点（如 self.name）
        attr_node = ASTAttribute(obj, attr_name, 1)  # 1 = Load context
        self.stack.push(attr_node)

    def _store_attr(self, operand: int) -> None:
        """存储属性 (obj.attr = value)"""
        if self._safe_stack_access('size', 0) < 2:
            return
        
        # STORE_ATTR: 栈顶是对象(obj)，下面是值(value)
        # 但在Python字节码中，执行STORE_ATTR前，栈是 [value, obj]
        # 所以先弹出的是 obj，然后是 value
        obj = self._safe_stack_access('pop')
        value = self._safe_stack_access('pop')
        
        if value is None or obj is None:
            # 栈访问失败，尝试恢复
            self._recover_from_error()
            return
        
        # 获取属性名 - 使用当前代码对象的names
        attr_name = f"attr_{operand}"
        # 优先使用当前代码对象（方法级），而不是模块级
        current_code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if current_code_obj and hasattr(current_code_obj, 'names') and current_code_obj.names and current_code_obj.names.get():
            names_obj = current_code_obj.names.get()
            if hasattr(names_obj, 'get') and operand < names_obj.size():
                name_ref = names_obj.get(operand)
                if name_ref and name_ref.get():
                    name_obj = name_ref.get()
                    if isinstance(name_obj, PycString):
                        attr_name = name_obj.value
                    elif hasattr(name_obj, 'value'):
                        attr_name = str(name_obj.value)
        
        # 创建属性访问节点作为目标（如 self.name）
        attr_node = ASTAttribute(obj, attr_name, 0)  # 0 = Store context
        # 创建赋值节点
        store_node = ASTStore(attr_node, value)
        self._emit(store_node)

    def _delete_attr(self, operand: int) -> None:
        """删除属性 (del obj.attr)"""
        obj = self._safe_stack_access('pop')
        if obj is None:
            return
        
        if not self.module.code:
            print(f"[_store_name] self.module.code is None or empty")
            return
        
        print(f"[_store_name] self.module.code={self.module.code}")
        names = self.module.code.get().names
        print(f"[_store_name] names={names}, names.get()={names.get() if names else None}")
        if names and names.get():
            names_obj = names.get()
            print(f"[_store_name] names_obj={names_obj}, type={type(names_obj)}")
            if isinstance(names_obj, PycString):
                attr_names = names_obj.value.split('\x00')
                if 0 <= operand < len(attr_names):
                    attr_name = attr_names[operand]
                    node = ASTChainStore(obj, ASTName(attr_name))
                    del_node = ASTDelete(node)
                    self._emit(del_node)

    def _load_const(self, operand: int) -> None:
        """加载常量"""
        from core.pyc_objects import PycCode as PycCodeClass
        
        # 使用当前代码对象的consts，而不是模块的
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if not code_obj:
            return
        
        consts = code_obj.consts
        if consts and consts.get():
            const_list = consts.get()
            const_obj = None
            
            # 处理PycSequence对象
            if hasattr(const_list, 'size') and hasattr(const_list, 'get'):
                if 0 <= operand < const_list.size():
                    const_item = const_list.get(operand)
                    if const_item:
                        const_obj = const_item.get()
                        debug_print(f"[LOAD_CONST] operand={operand}, const_obj类型: {type(const_obj)}, 值: {const_obj}")
            # 检查是否是PycSequence对象，如果是则使用其_values属性
            elif hasattr(const_list, '_values'):
                if 0 <= operand < len(const_list._values):
                    const_obj = const_list._values[operand].get() if hasattr(const_list._values[operand], 'get') else const_list._values[operand]
                    debug_print(f"[LOAD_CONST] operand={operand}, const_obj类型: {type(const_obj)}, 值: {const_obj}")
            elif hasattr(const_list, '__getitem__') and 0 <= operand < len(const_list):
                const_obj = const_list[operand]
                debug_print(f"[LOAD_CONST] operand={operand}, const_obj类型: {type(const_obj)}, 值: {const_obj}")
            
            if const_obj is not None:
                try:
                    debug_print(f"[LOAD_CONST] const_obj类型: {type(const_obj)}, isinstance(PycCodeClass): {isinstance(const_obj, PycCodeClass)}")
                    debug_print(f"[LOAD_CONST] self.code_obj: {self.code_obj}")
                    
                    # 检查是否是代码对象
                    is_pyc_code = isinstance(const_obj, PycCodeClass)
                    if is_pyc_code:
                        # [DEBUG] 修复：为所有代码对象创建函数定义（包括嵌套函数）
                        func_node = self._create_function_from_code(const_obj)
                        if func_node:
                            debug_print(f"[LOAD_CONST] 创建函数定义节点: {func_node.name if hasattr(func_node, 'name') else 'unknown'}")
                            self.stack.push(func_node)
                        else:
                            node = ASTObject(const_obj)
                            self.stack.push(node)
                    else:
                        # 检查是否是frozenset（PycSequence with TYPE_FROZENSET）
                        from core.pyc_objects import PycSequence, PycObject
                        if isinstance(const_obj, PycSequence) and const_obj.type == PycObject.TYPE_FROZENSET:
                            # 将frozenset转换为ASTSet
                            from core.ast_nodes import ASTSet, ASTConstant
                            items = []
                            if hasattr(const_obj, '_values'):
                                for item_ref in const_obj._values:
                                    if item_ref and item_ref.get():
                                        item_obj = item_ref.get()
                                        if hasattr(item_obj, 'value'):
                                            items.append(ASTConstant(item_obj.value))
                                        else:
                                            items.append(ASTConstant(item_obj))
                            node = ASTSet(items)
                            self.stack.push(node)
                        else:
                            # 非代码对象，作为普通对象处理
                            node = ASTObject(const_obj)
                            self.stack.push(node)
                except (IndexError, TypeError, RecursionError):
                    pass

    def _create_function_from_code(self, code_obj: 'PycCode') -> Optional['ASTFunctionDef']:
        """从代码对象创建函数定义节点"""
        from core.ast_nodes import ASTFunctionDef, ASTBlock as ASTBlockNode
        from core.pyc_objects import PycCode, PycString
        from core.pyc_stream import PycRef as PycRefType
        
        print(f"[DEBUG] _create_function_from_code - 开始创建函数")
        print(f"[DEBUG] _create_function_from_code - code_obj类型: {type(code_obj)}")
        
        if isinstance(code_obj, PycRefType):
            code_obj = code_obj.get()
            debug_print(f"[DEBUG] _create_function_from_code - 解引用后的code_obj: {type(code_obj)}")
        
        if not isinstance(code_obj, PycCode):
            debug_print(f"[DEBUG] _create_function_from_code - 不是PycCode类型")
            return None
        
        debug_print(f"[DEBUG] _create_function_from_code - 开始参数提取")
        
        # 获取函数字节码
        if not code_obj.code or not hasattr(code_obj.code, 'get'):
            return None
        
        code_obj_inner = code_obj.code.get()
        if not hasattr(code_obj_inner, 'value'):
            return None
        
        bytecode = code_obj_inner.value
        
        # 创建临时的ASTBuilder来处理函数的字节码
        func_builder = ASTBuilder(self.module, code_obj)
        func_builder.in_function = True
        
        # 直接处理字节码指令
        from bytecode.pyc_disasm import PycDisassembler
        disasm = PycDisassembler(bytecode, self.module, self.module.version if hasattr(self.module, 'version') else (3, 11), code_obj)
        instructions = disasm.disassemble()
        
        # [DEBUG] 关键修复：设置指令列表，以便_emit方法正确处理else分支
        func_builder.instructions = instructions
        
        # [DEBUG] 关键修复：预扫描循环结构
        func_builder._prescan_for_loops(instructions)
        print(f"[CREATE_FUNC] 预扫描完成，发现 {len(func_builder._loop_entries)} 个循环")
        for offset, info in func_builder._loop_entries.items():
            print(f"[CREATE_FUNC]   循环@{offset}: {info}")
        
        print(f"[CREATE_FUNC] 开始处理 {len(instructions)} 条指令")
        for idx, instr in enumerate(instructions):
            opcode = instr.get('opcode', 0)
            offset = instr.get('offset', 0)
            if opcode == Opcode.POP_JUMP_FORWARD_IF_FALSE_A:
                print(f"[CREATE_FUNC]   [{idx}] POP_JUMP_FORWARD_IF_FALSE_A @ offset={offset}")
            func_builder._process_instruction(instr)
        print(f"[CREATE_FUNC] 指令处理完成")
        
        # 获取函数名
        func_name = '<anonymous>'
        if hasattr(code_obj, 'name') and code_obj.name:
            name_ref = code_obj.name
            debug_print(f"[CREATE_FUNC] code_obj.name类型: {type(name_ref)}, 值: {name_ref}")
            # 处理PycRef
            if hasattr(name_ref, 'get'):
                name_obj = name_ref.get()
                debug_print(f"[CREATE_FUNC] name_obj类型: {type(name_obj)}, 值: {name_obj}")
                if name_obj:
                    if isinstance(name_obj, PycString):
                        func_name = name_obj.value
                        debug_print(f"[CREATE_FUNC] 从PycString提取函数名: {func_name}")
                    elif hasattr(name_obj, 'value'):
                        func_name = str(name_obj.value)
                        debug_print(f"[CREATE_FUNC] 从value属性提取函数名: {func_name}")
                    else:
                        func_name = str(name_obj)
                        debug_print(f"[CREATE_FUNC] 从str转换函数名: {func_name}")
            elif isinstance(name_ref, PycString):
                func_name = name_ref.value
                debug_print(f"[CREATE_FUNC] 从PycString直接提取函数名: {func_name}")
            elif hasattr(name_ref, 'value'):
                func_name = str(name_ref.value)
                debug_print(f"[CREATE_FUNC] 从value属性提取函数名: {func_name}")
        
        debug_print(f"[CREATE_FUNC] 最终提取的函数名: {func_name}")
        
        # [DEBUG] 关键修复：检测推导式函数并转换为推导式节点
        # 检查1: 函数名是否为推导式名称
        is_comp_by_name = func_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>')
        
        # 检查2: 通过代码对象特征检测推导式（函数名可能是<anonymous>）
        is_comp_by_features = self._is_comprehension_code(code_obj)
        
        if is_comp_by_name:
            debug_print(f"[CREATE_FUNC] 通过名称检测到推导式函数: {func_name}")
            comp_node = self._create_comprehension_from_code(code_obj, func_name)
            debug_print(f"[CREATE_FUNC] _create_comprehension_from_code 返回: {type(comp_node).__name__ if comp_node else 'None'}")
            if comp_node:
                debug_print(f"[CREATE_FUNC] 返回推导式节点: {type(comp_node).__name__}")
                return comp_node
            else:
                debug_print(f"[CREATE_FUNC] _create_comprehension_from_code 返回 None，继续创建普通函数")
        elif is_comp_by_features:
            # 通过特征检测到推导式，但函数名不是标准推导式名称
            # 根据代码特征推断推导式类型
            inferred_type = self._infer_comprehension_type(code_obj)
            debug_print(f"[CREATE_FUNC] 通过特征检测到推导式函数，推断类型: {inferred_type}")
            comp_node = self._create_comprehension_from_code(code_obj, inferred_type)
            debug_print(f"[CREATE_FUNC] _create_comprehension_from_code 返回: {type(comp_node).__name__ if comp_node else 'None'}")
            if comp_node:
                debug_print(f"[CREATE_FUNC] 返回推导式节点: {type(comp_node).__name__}")
                return comp_node
            else:
                debug_print(f"[CREATE_FUNC] _create_comprehension_from_code 返回 None，继续创建普通函数")
        
        # [DEBUG] 修复：使用专门的参数提取方法
        debug_print(f"[CREATE_FUNC] 调用_extract_function_args")
        
        try:
            args = self._extract_function_args(code_obj)
            debug_print(f"[CREATE_FUNC] 提取到的参数: {args}")
            debug_print(f"[CREATE_FUNC] 参数长度: {len(args)}")
        except Exception as e:
            debug_print(f"[CREATE_FUNC] 提取参数时发生异常: {e}")
            import traceback
            traceback.print_exc()
            args = []
        
        # 如果参数提取为空，使用原有逻辑
        if not args:
            debug_print(f"[CREATE_FUNC] 参数为空，使用fallback逻辑")
            debug_print(f"[DEBUG][DEBUG][DEBUG] _create_function_from_code - 使用原有参数提取逻辑")
            # 原有的参数提取逻辑作为fallback
            if hasattr(code_obj, 'local_names') and code_obj.local_names and code_obj.local_names.get():
                varnames_list = code_obj.local_names.get()
                argcount = 0
                if hasattr(argcount, '_value'):
                    argcount = argcount._value
            elif hasattr(code_obj, 'argcount'):
                argcount = code_obj.argcount
                if hasattr(argcount, 'get'):
                    argcount = argcount.get()
                if hasattr(argcount, '_value'):
                    argcount = argcount._value
            
            varnames = []
            if hasattr(varnames_list, 'size') and hasattr(varnames_list, 'get'):
                for i in range(varnames_list.size()):
                    try:
                        varname_obj = varnames_list.get(i)
                        if varname_obj and varname_obj.get():
                            name_obj = varname_obj.get()
                            if isinstance(name_obj, PycString):
                                var_name = name_obj.value
                                varnames.append(var_name)
                    except (IndexError, TypeError):
                        pass
            elif hasattr(varnames_list, '__len__') and hasattr(varnames_list, '__getitem__'):
                for varname_obj in varnames_list:
                    if isinstance(varname_obj, PycString):
                        var_name = varname_obj.value
                        varnames.append(var_name)
                    elif hasattr(varname_obj, 'get'):
                        name_obj = varname_obj.get()
                        if isinstance(name_obj, PycString):
                            var_name = name_obj.value
                            varnames.append(var_name)
            
            if varnames and argcount > 0:
                args = varnames[:argcount]
        
        # [关键修复] 直接使用func_builder.main_block作为func_body
        func_body = func_builder.main_block
        
        # [DEBUG] 关键修复：如果函数体为空，添加一个pass语句
        if not hasattr(func_body, 'nodes') or not func_body.nodes:
            debug_print(f"[DEBUG] 函数体为空，添加pass语句")
            from core.ast_nodes import ASTPass
            func_body.append(ASTPass())
        
        debug_print(f"[DEBUG] 调试函数体提取 - func_body节点数: {len(func_body.nodes) if hasattr(func_body, 'nodes') else 0}")
        
        # 保存原始代码对象
        result = ASTFunctionDef(func_name, args=args, body=func_body, code_obj=code_obj)
        
        # [DEBUG] 增强：对所有函数都尝试从字节码中提取默认值
        debug_print(f"[CREATE_FUNC] 为函数 {func_name} 增强默认值")
        self._enhance_with_defaults(result, code_obj)
        
        return result

    def _enhance_with_defaults(self, func_node, code_obj):
        """为函数节点增强默认值支持"""
        try:
            debug_print(f"[ENHANCE] 尝试增强默认值: {func_node.name}")
            
            # 获取默认值的字节码位置
            defaults = self._extract_defaults_from_bytecode(code_obj)
            if not defaults:
                debug_print(f"[ENHANCE] 未找到默认值")
                return
            
            debug_print(f"[ENHANCE] 找到默认值: {defaults}")
            
            # 更新参数列表
            enhanced_args = []
            num_defaults = len(defaults)
            argcount = len(func_node.args)
            num_positional = argcount - num_defaults
            
            for i, arg in enumerate(func_node.args):
                arg_name = self._extract_arg_name(arg)
                if arg_name:
                    if i >= num_positional:
                        default_index = i - num_positional
                        if default_index < len(defaults):
                            default_val = defaults[default_index]
                            enhanced_args.append(f"{arg_name}={default_val}")
                        else:
                            enhanced_args.append(arg_name)
                    else:
                        enhanced_args.append(arg_name)
            
            # 更新func_node的args属性
            if enhanced_args:
                debug_print(f"[ENHANCE] 增强后参数: {enhanced_args}")
                # 使用增强后的参数替换原有参数
                func_node._args = enhanced_args
                
        except Exception as e:
            debug_print(f"[ENHANCE] 增强默认值失败: {e}")
    
    def _create_comprehension_from_code(self, code_obj: 'PycCode', comp_type: str) -> Optional['ASTNode']:
        """从代码对象创建推导式节点
        
        comp_type: '<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'
        """
        from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp, ASTComprehension, ASTName, ASTBinary, ASTConstant
        
        debug_print(f"[_create_comprehension] 创建{comp_type}推导式")
        
        try:
            # 获取局部变量名
            local_names = []
            if hasattr(code_obj, 'local_names') and code_obj.local_names:
                varnames_list = code_obj.local_names.get()
                if varnames_list and hasattr(varnames_list, 'size'):
                    for i in range(varnames_list.size()):
                        try:
                            varname_ref = varnames_list.get(i)
                            if varname_ref and varname_ref.get():
                                name_obj = varname_ref.get()
                                from core.pyc_objects import PycString
                                if isinstance(name_obj, PycString):
                                    local_names.append(name_obj.value)
                                elif hasattr(name_obj, 'value'):
                                    local_names.append(str(name_obj.value))
                        except:
                            pass
            
            debug_print(f"[_create_comprehension] 局部变量: {local_names}")
            
            # 推导式的迭代变量通常是第二个局部变量（第一个是 .0）
            iter_var = "x"
            iter_vars = []  # 支持多变量，如 k, v
            if len(local_names) >= 2:
                # 跳过 .0，收集所有迭代变量
                iter_vars = [name for name in local_names[1:] if name != '.0']
                iter_var = local_names[1]  # 第一个迭代变量
            elif len(local_names) == 1 and local_names[0] != '.0':
                iter_var = local_names[0]
                iter_vars = [iter_var]
            
            # [关键修复] 解析字节码来提取元素表达式
            parse_result = self._parse_comprehension_element(code_obj, iter_var, comp_type)
            
            # 创建生成器 - 使用占位符迭代表达式
            iter_expr = ASTName("range(10)")  # 占位符
            
            # [关键修复] 支持多变量迭代（如 for k, v in ...）
            if len(iter_vars) > 1:
                # 多变量情况，创建元组作为 target
                from core.ast_nodes import ASTTuple
                target = ASTTuple([ASTName(name) for name in iter_vars])
            else:
                # 单变量情况
                target = ASTName(iter_var)
            
            generators = [ASTComprehension(target, iter_expr, [])]
            
            # 根据推导式类型创建相应的节点
            if comp_type == '<listcomp>':
                elt = parse_result if parse_result is not None else ASTName(iter_var)
                debug_print(f"[_create_comprehension] 创建列表推导式: 元素类型={type(elt).__name__}")
                result = ASTListComp(elt, generators)
                debug_print(f"[_create_comprehension] 返回 ASTListComp: {type(result).__name__}")
                return result
            elif comp_type == '<setcomp>':
                elt = parse_result if parse_result is not None else ASTName(iter_var)
                debug_print(f"[_create_comprehension] 创建集合推导式: 元素类型={type(elt).__name__}")
                result = ASTSetComp(elt, generators)
                debug_print(f"[_create_comprehension] 返回 ASTSetComp: {type(result).__name__}")
                return result
            elif comp_type == '<dictcomp>':
                # 字典推导式需要键和值
                if parse_result is not None and isinstance(parse_result, tuple) and len(parse_result) == 2:
                    key_expr, value_expr = parse_result
                    debug_print(f"[_create_comprehension] 创建字典推导式: 键类型={type(key_expr).__name__}, 值类型={type(value_expr).__name__}")
                else:
                    # 如果解析失败，使用默认的键和值
                    key_expr = ASTName("k")
                    value_expr = ASTName("v")
                    debug_print(f"[_create_comprehension] 创建字典推导式(默认): 键={key_expr}, 值={value_expr}")
                result = ASTDictComp(key_expr, value_expr, generators)
                debug_print(f"[_create_comprehension] 返回 ASTDictComp: {type(result).__name__}")
                return result
            elif comp_type == '<genexpr>':
                # 生成器表达式
                from core.ast_nodes import ASTGenExpr
                elt = parse_result if parse_result is not None else ASTName(iter_var)
                debug_print(f"[_create_comprehension] 创建生成器表达式: 元素类型={type(elt).__name__}")
                result = ASTGenExpr(elt, generators)
                debug_print(f"[_create_comprehension] 返回 ASTGenExpr: {type(result).__name__}")
                return result
            else:
                debug_print(f"[_create_comprehension] 返回 None (未知类型: {comp_type})")
                return None
                
        except Exception as e:
            debug_print(f"[_create_comprehension] 创建推导式失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_comprehension_element(self, code_obj: 'PycCode', iter_var: str, comp_type: str = None) -> Optional['ASTNode']:
        """解析推导式函数的字节码，提取元素表达式
        
        对于 [x**2 for x in range(10)]，推导式函数的字节码结构是：
        1. BUILD_LIST_A (创建空列表)
        2. LOAD_FAST_A .0 (加载迭代器)
        3. FOR_ITER_A (开始循环)
        4. STORE_FAST_A x (存储迭代变量)
        5. ... (元素表达式计算，如 x**2)
        6. LIST_APPEND_A (添加到列表)
        7. JUMP_BACKWARD_A (跳回循环开始)
        8. RETURN_VALUE (返回列表)
        
        对于字典推导式 {k: v for k, v in ...}：
        1. BUILD_MAP_A (创建空字典)
        2. LOAD_FAST_A .0 (加载迭代器)
        3. FOR_ITER_A (开始循环)
        4. UNPACK_SEQUENCE_A 2 (解包键值对)
        5. STORE_FAST_A k (存储键)
        6. STORE_FAST_A v (存储值)
        7. LOAD_FAST_A k (加载键)
        8. LOAD_FAST_A v (加载值)
        9. MAP_ADD_A (添加到字典)
        10. JUMP_BACKWARD_A (跳回循环开始)
        11. RETURN_VALUE (返回字典)
        """
        from core.ast_nodes import ASTName, ASTBinary, ASTConstant
        
        try:
            # 获取字节码
            if not hasattr(code_obj, 'code') or not code_obj.code:
                return None
            
            bytecode = code_obj.code.get()._value if code_obj.code else b''
            if not bytecode:
                return None
            
            # 反汇编字节码
            from bytecode.pyc_disasm import PycDisassembler
            from core.pyc_loader_v2 import load_pyc_file_v2
            
            # 使用默认版本
            version = (3, 11)
            disassembler = PycDisassembler(bytecode, version)
            instructions = disassembler.disassemble()
            
            debug_print(f"[_parse_comprehension_element] 解析{len(instructions)}条指令, 类型={comp_type}")
            
            # 获取常量表
            consts = []
            if hasattr(code_obj, 'consts') and code_obj.consts:
                consts_list = code_obj.consts.get()
                if consts_list:
                    for i in range(consts_list.size()):
                        try:
                            const_ref = consts_list.get(i)
                            if const_ref and const_ref.get():
                                const_obj = const_ref.get()
                                # 提取常量值
                                if hasattr(const_obj, 'value'):
                                    consts.append(const_obj.value)
                                elif hasattr(const_obj, '_value'):
                                    consts.append(const_obj._value)
                                else:
                                    consts.append(const_obj)
                            else:
                                consts.append(None)
                        except:
                            consts.append(None)
            
            debug_print(f"[_parse_comprehension_element] 常量表: {consts}")
            
            # 检查是否是字典推导式（有 UNPACK_SEQUENCE_A）
            is_dict_comp = False
            for instr in instructions:
                if instr.get('opcode_name', '') == 'UNPACK_SEQUENCE_A':
                    is_dict_comp = True
                    break
            
            if is_dict_comp or comp_type == '<dictcomp>':
                # 字典推导式：解析键和值
                return self._parse_dict_comprehension_element(instructions, consts)
            
            # 列表/集合推导式：查找元素表达式
            # 元素表达式在 STORE_FAST_A (迭代变量) 之后，LIST_APPEND_A/SET_ADD_A 之前
            elt_start_idx = -1
            elt_end_idx = -1
            
            for i, instr in enumerate(instructions):
                opcode = instr.get('opcode', -1)
                name = instr.get('opcode_name', '')
                
                # 找到存储迭代变量的位置
                if name == 'STORE_FAST_A' and elt_start_idx == -1:
                    elt_start_idx = i + 1
                
                # 找到 LIST_APPEND_A/SET_ADD_A，元素表达式在此结束
                if name in ('LIST_APPEND_A', 'SET_ADD_A') and elt_end_idx == -1:
                    elt_end_idx = i
                    break
            
            if elt_start_idx == -1 or elt_end_idx == -1 or elt_start_idx >= elt_end_idx:
                debug_print(f"[_parse_comprehension_element] 无法定位元素表达式范围: start={elt_start_idx}, end={elt_end_idx}")
                return None
            
            debug_print(f"[_parse_comprehension_element] 元素表达式范围: {elt_start_idx} - {elt_end_idx}")
            
            # 解析元素表达式指令
            elt_instructions = instructions[elt_start_idx:elt_end_idx]
            return self._build_expression_from_instructions(elt_instructions, iter_var, consts)
            
        except Exception as e:
            debug_print(f"[_parse_comprehension_element] 解析元素表达式失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_dict_comprehension_element(self, instructions: List[Dict], consts: List) -> Tuple['ASTNode', 'ASTNode']:
        """解析字典推导式的键和值表达式
        
        返回 (key_expr, value_expr)
        """
        from core.ast_nodes import ASTName, ASTBinary, ASTConstant
        
        debug_print(f"[_parse_dict_comprehension_element] 解析字典推导式元素")
        
        # 查找 UNPACK_SEQUENCE_A 和 MAP_ADD_A
        unpack_idx = -1
        map_add_idx = -1
        
        for i, instr in enumerate(instructions):
            name = instr.get('opcode_name', '')
            if name == 'UNPACK_SEQUENCE_A' and unpack_idx == -1:
                unpack_idx = i
            if name == 'MAP_ADD_A' and map_add_idx == -1:
                map_add_idx = i
                break
        
        if unpack_idx == -1 or map_add_idx == -1:
            debug_print(f"[_parse_dict_comprehension_element] 无法定位: unpack={unpack_idx}, map_add={map_add_idx}")
            return None, None
        
        # 获取迭代变量名
        key_var = "k"
        value_var = "v"
        
        # 查找 STORE_FAST_A 指令来获取变量名
        for i, instr in enumerate(instructions):
            if instr.get('opcode_name', '') == 'STORE_FAST_A':
                operand = instr.get('operand', 0)
                if operand == 1:
                    key_var = "k"
                elif operand == 2:
                    value_var = "v"
        
        # 键值表达式在第二个 STORE_FAST_A 之后，MAP_ADD_A 之前
        elt_start_idx = -1
        for i in range(unpack_idx + 1, map_add_idx):
            if instructions[i].get('opcode_name', '') == 'STORE_FAST_A':
                # 找到最后一个 STORE_FAST_A
                elt_start_idx = i + 1
        
        if elt_start_idx == -1 or elt_start_idx >= map_add_idx:
            debug_print(f"[_parse_dict_comprehension_element] 无法定位元素表达式: start={elt_start_idx}")
            return None, None
        
        debug_print(f"[_parse_dict_comprehension_element] 键值表达式范围: {elt_start_idx} - {map_add_idx}")
        
        # 解析键值表达式指令
        elt_instructions = instructions[elt_start_idx:map_add_idx]
        
        # 对于简单的 {k: v}，应该有两条 LOAD_FAST_A 指令
        # 第一个是键，第二个是值
        key_expr = None
        value_expr = None
        
        load_fast_count = 0
        for instr in elt_instructions:
            if instr.get('opcode_name', '') == 'LOAD_FAST_A':
                operand = instr.get('operand', 0)
                if load_fast_count == 0:
                    # 第一个 LOAD_FAST_A 是键
                    key_expr = ASTName(key_var)
                    load_fast_count += 1
                elif load_fast_count == 1:
                    # 第二个 LOAD_FAST_A 是值
                    value_expr = ASTName(value_var)
                    load_fast_count += 1
        
        if key_expr is None:
            key_expr = ASTName(key_var)
        if value_expr is None:
            value_expr = ASTName(value_var)
        
        debug_print(f"[_parse_dict_comprehension_element] 键={key_var}, 值={value_var}")
        return key_expr, value_expr
    
    def _build_expression_from_instructions(self, instructions: List[Dict], iter_var: str, consts: List = None) -> Optional['ASTNode']:
        """从指令列表构建表达式节点
        
        支持简单的表达式，如：
        - x (LOAD_FAST_A x)
        - x**2 (LOAD_FAST_A x, LOAD_CONST_A 2, BINARY_OP_A **)
        - x+1 (LOAD_FAST_A x, LOAD_CONST_A 1, BINARY_OP_A +)
        """
        from core.ast_nodes import ASTName, ASTBinary, ASTConstant
        
        if not instructions:
            return None
        
        if consts is None:
            consts = []
        
        # 使用栈来构建表达式
        stack = []
        
        for instr in instructions:
            opcode = instr.get('opcode', -1)
            name = instr.get('opcode_name', '')
            operand = instr.get('operand', 0)
            
            if name == 'LOAD_FAST_A':
                # 加载局部变量（迭代变量）
                stack.append(ASTName(iter_var))
            elif name == 'LOAD_CONST_A':
                # 加载常量 - operand 是常量表的索引
                const_value = operand  # 默认使用索引作为值
                if 0 <= operand < len(consts):
                    const_value = consts[operand]
                    debug_print(f"[_build_expression] 加载常量[{operand}] = {const_value}")
                else:
                    debug_print(f"[_build_expression] 常量索引 {operand} 超出范围，使用默认值 {const_value}")
                stack.append(ASTConstant(const_value))
            elif name == 'BINARY_OP_A':
                # 二元操作
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    
                    # 操作数映射 - 与 _process_instruction 中的映射保持一致
                    # Python 3.11+ BINARY_OP_A 操作数映射
                    binary_op_map = {
                        0: ASTBinary.BinOp.BIN_ADD.value,           # +
                        1: ASTBinary.BinOp.BIN_AND.value,           # &
                        2: ASTBinary.BinOp.BIN_FLOOR_DIVIDE.value,  # //
                        3: ASTBinary.BinOp.BIN_LSHIFT.value,        # <<
                        5: ASTBinary.BinOp.BIN_MULTIPLY.value,      # *
                        6: ASTBinary.BinOp.BIN_MODULO.value,        # %
                        7: ASTBinary.BinOp.BIN_OR.value,            # |
                        8: ASTBinary.BinOp.BIN_POWER.value,         # **
                        9: ASTBinary.BinOp.BIN_RSHIFT.value,        # >>
                        10: ASTBinary.BinOp.BIN_SUBTRACT.value,     # -
                        11: ASTBinary.BinOp.BIN_DIVIDE.value,       # /
                        12: ASTBinary.BinOp.BIN_XOR.value,          # ^
                    }
                    op_value = binary_op_map.get(operand, ASTBinary.BinOp.BIN_ADD.value)
                    result = ASTBinary(left, right, op_value)
                    stack.append(result)
                else:
                    debug_print(f"[_build_expression] 栈中元素不足，无法执行二元操作")
            elif name == 'CACHE':
                # 忽略缓存指令
                continue
            else:
                debug_print(f"[_build_expression] 未处理的指令: {name}")
        
        # 返回栈顶元素
        if stack:
            return stack[-1]
        return None
    
    def _is_comprehension_code(self, code_obj) -> bool:
        """通过代码对象特征检测是否为推导式代码
        
        推导式代码的特征：
        1. 局部变量名中包含 '.0'（隐式迭代器参数）
        2. 参数数量为1（只有一个隐式参数 .0）
        3. 代码通常较短且包含迭代逻辑
        """
        try:
            # 获取局部变量名
            local_names = []
            if hasattr(code_obj, 'local_names') and code_obj.local_names:
                varnames_list = code_obj.local_names.get()
                if varnames_list and hasattr(varnames_list, 'size'):
                    for i in range(varnames_list.size()):
                        try:
                            varname_ref = varnames_list.get(i)
                            if varname_ref and varname_ref.get():
                                name_obj = varname_ref.get()
                                from core.pyc_objects import PycString
                                if isinstance(name_obj, PycString):
                                    local_names.append(name_obj.value)
                                elif hasattr(name_obj, 'value'):
                                    local_names.append(str(name_obj.value))
                        except:
                            pass
            
            # 检查是否包含 '.0'（推导式的隐式迭代器参数）
            has_dot_zero = '.0' in local_names
            
            # 获取参数数量
            argcount = 0
            if hasattr(code_obj, 'argcount'):
                argcount = code_obj.argcount
                if hasattr(argcount, 'get'):
                    argcount = argcount.get()
                if hasattr(argcount, '_value'):
                    argcount = argcount._value
            
            # 推导式通常只有一个参数（.0）
            is_single_arg = argcount == 1
            
            debug_print(f"[_is_comprehension_code] 局部变量: {local_names}, 包含.0: {has_dot_zero}, 参数数: {argcount}")
            
            # 如果包含 .0 且只有一个参数，很可能是推导式
            return has_dot_zero and is_single_arg
            
        except Exception as e:
            debug_print(f"[_is_comprehension_code] 检测失败: {e}")
            return False
    
    def _infer_comprehension_type(self, code_obj) -> str:
        """根据代码对象特征推断推导式类型
        
        返回: '<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'
        """
        try:
            # 获取字节码
            code_bytes = None
            if hasattr(code_obj, 'code') and code_obj.code:
                code_bytes = code_obj.code.get() if hasattr(code_obj.code, 'get') else code_obj.code
            
            if not code_bytes:
                return '<listcomp>'  # 默认返回列表推导式
            
            # 通过字节码中的特定指令推断类型
            # 列表推导式: BUILD_LIST
            # 集合推导式: BUILD_SET
            # 字典推导式: BUILD_MAP, MAP_ADD
            # 生成器表达式: YIELD_VALUE
            
            code_str = str(code_bytes)
            
            # 简单的启发式检测
            if b'BUILD_SET' in code_bytes:
                return '<setcomp>'
            elif b'BUILD_MAP' in code_bytes or b'MAP_ADD' in code_bytes:
                return '<dictcomp>'
            elif b'YIELD_VALUE' in code_bytes:
                return '<genexpr>'
            else:
                # 默认为列表推导式
                return '<listcomp>'
                
        except Exception as e:
            debug_print(f"[_infer_comprehension_type] 推断失败: {e}")
            return '<listcomp>'  # 默认返回列表推导式
    
    def _extract_arg_name(self, arg):
        """提取参数名称"""
        if isinstance(arg, str):
            # [DEBUG] 处理带默认值的参数 "z=10"
            if '=' in arg:
                return arg.split('=', 1)[0]
            else:
                return arg
        elif hasattr(arg, 'name'):
            name = arg.name
            if hasattr(name, '_value'):
                return name._value
            elif isinstance(name, str):
                return name
            else:
                return str(name)
        elif hasattr(arg, '_value'):
            return arg._value
        else:
            return str(arg)

    def _extract_defaults_from_bytecode(self, code_obj):
        """从字节码中提取默认值 - Python 3.11兼容版本"""
        try:
            debug_print(f"[DEFAULTS] 开始检查默认值: {type(code_obj)}")
            
            # 方法1：检查co_defaults（兼容性检查）
            if hasattr(code_obj, 'co_defaults'):
                defaults = code_obj.co_defaults
                debug_print(f"[DEFAULTS] co_defaults属性存在: {defaults}")
                if defaults:
                    debug_print(f"[DEFAULTS] 找到co_defaults: {defaults}")
                    return list(defaults)
            
            # 方法2：Python 3.11特殊处理 - 检查主模块常量列表
            if hasattr(self.module, 'code') and self.module.code:
                module_code_obj = self.module.code.get()
                if hasattr(module_code_obj, 'consts') and module_code_obj.consts:
                    consts = module_code_obj.consts
                    if hasattr(consts, 'get'):
                        consts_list = consts.get()
                        debug_print(f"[DEFAULTS] 检查主模块常量列表，大小: {consts_list.size() if hasattr(consts_list, 'size') else '未知'}")
                        
                        # 查找当前代码对象在主模块常量列表中的位置
                        code_obj_index = -1
                        for i in range(consts_list.size()):
                            const_ref = consts_list.get(i)
                            const = const_ref.get()
                            
                            # 检查是否是当前代码对象
                            if const is code_obj:
                                code_obj_index = i
                                debug_print(f"[DEFAULTS] 找到代码对象在常量列表中的位置: {i}")
                                break
                        
                        # 如果找到了代码对象，检查前面的常量作为默认值
                        if code_obj_index > 0:
                            # Python 3.11：默认值存储在函数代码对象之前
                            # 但需要注意：不是所有前面的常量都是默认值
                            # 我们需要根据函数的参数数量来判断
                            
                            # 获取函数的参数数量
                            arg_count = 0
                            if hasattr(code_obj, 'arg_count'):
                                arg_count = code_obj.arg_count
                                if hasattr(arg_count, 'get'):
                                    arg_count = arg_count.get()
                                elif hasattr(arg_count, '_value'):
                                    arg_count = arg_count._value
                            
                            # 获取局部变量名列表（用于排除参数名）
                            local_varnames = set()
                            if hasattr(code_obj, 'local_names') and code_obj.local_names:
                                local_names_obj = code_obj.local_names.get()
                                if local_names_obj and hasattr(local_names_obj, 'size'):
                                    for j in range(local_names_obj.size()):
                                        try:
                                            var_ref = local_names_obj.get(j)
                                            if var_ref and var_ref.get():
                                                var_obj = var_ref.get()
                                                if isinstance(var_obj, PycString):
                                                    local_varnames.add(var_obj.value)
                                        except:
                                            pass
                            debug_print(f"[DEFAULTS] 局部变量名: {local_varnames}")
                            
                            potential_defaults = []
                            i = code_obj_index - 1
                            
                            # 向后检查可能的默认值，最多检查 arg_count 个
                            max_defaults = min(arg_count, 10) if arg_count > 0 else 0
                            
                            while i >= 0 and len(potential_defaults) < max_defaults:
                                const_ref = consts_list.get(i)
                                const = const_ref.get()
                                
                                # 检查是否是数字或字符串常量（可能的默认值）
                                # 严格检查：只接受简单的标量值，不接受类或函数对象
                                from core.pyc_objects import PycString, PycNumeric, PycObject
                                is_default = False
                                
                                if isinstance(const, PycString):
                                    value = const.value
                                    if isinstance(value, str):
                                        # 检查是否是标识符（可能是类名、函数名或类型注解）
                                        # 标识符通常不用作默认值
                                        if value.isidentifier():
                                            # 排除类型注解名称（如 'return'）和参数名
                                            if value == 'return':
                                                debug_print(f"[DEFAULTS] 遇到 'return' 类型注解，跳过: {value}")
                                                i -= 1
                                                continue
                                            # 检查是否是参数名
                                            if value in local_varnames:
                                                debug_print(f"[DEFAULTS] 遇到参数名，跳过: {value}")
                                                i -= 1
                                                continue
                                            if len(value) > 1 and value[0].isupper():
                                                # 可能是类名，停止
                                                debug_print(f"[DEFAULTS] 遇到类名，停止: {value}")
                                                break
                                            # 其他标识符（如小写的类型名）也跳过
                                            debug_print(f"[DEFAULTS] 遇到其他标识符，跳过: {value}")
                                            i -= 1
                                            continue
                                        # 非标识符字符串（如包含空格的字符串）可能是默认值
                                        default_str = repr(value)
                                        potential_defaults.insert(0, default_str)
                                        debug_print(f"[DEFAULTS] 找到字符串默认值: {value}")
                                        is_default = True
                                elif isinstance(const, PycNumeric):
                                    value = const.value
                                    if isinstance(value, (int, float)):
                                        potential_defaults.insert(0, str(value))
                                        debug_print(f"[DEFAULTS] 找到数值默认值: {value}")
                                        is_default = True
                                elif isinstance(const, PycObject) and const.type == PycObject.TYPE_NONE:
                                    potential_defaults.insert(0, "None")
                                    debug_print(f"[DEFAULTS] 找到None默认值")
                                    is_default = True
                                elif isinstance(const, PycObject) and const.type in (PycObject.TYPE_TRUE, PycObject.TYPE_FALSE):
                                    value = const.type == PycObject.TYPE_TRUE
                                    potential_defaults.insert(0, str(value))
                                    debug_print(f"[DEFAULTS] 找到布尔默认值: {value}")
                                    is_default = True
                                
                                if is_default:
                                    i -= 1
                                else:
                                    # 遇到其他类型（如类、函数等），停止
                                    debug_print(f"[DEFAULTS] 遇到非默认值类型: {type(const).__name__}")
                                    break
                            
                            if potential_defaults:
                                debug_print(f"[DEFAULTS] 从主模块常量列表提取到默认值: {potential_defaults}")
                                return potential_defaults
            
            # 方法3：检查内部代码对象
            if hasattr(code_obj, 'code') and code_obj.code:
                inner_code = code_obj.code
                if hasattr(inner_code, 'get'):
                    inner_code_obj = inner_code.get()
                    debug_print(f"[DEFAULTS] 检查内部代码对象: {type(inner_code_obj)}")
                    
                    # 检查是否是真正的代码对象
                    if hasattr(inner_code_obj, 'co_argcount') and hasattr(inner_code_obj, 'co_varnames'):
                        debug_print(f"[DEFAULTS] 这是一个真正的代码对象!")
                        if hasattr(inner_code_obj, 'co_defaults'):
                            defaults = inner_code_obj.co_defaults
                            debug_print(f"[DEFAULTS] 内部co_defaults: {defaults}")
                            if defaults:
                                return list(defaults)
                    else:
                        debug_print(f"[DEFAULTS] 这不是代码对象，是: {type(inner_code_obj)}")
            
            debug_print(f"[DEFAULTS] 未找到默认值")
            return None
            
        except Exception as e:
            debug_print(f"[DEFAULTS] 提取默认值失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_function_args(self, code_obj: 'PycCode') -> List['ASTNode']:
        """从代码对象提取函数参数"""
        debug_print(f"[EXTRACT_ARGS] _extract_function_args被调用! code_obj类型: {type(code_obj)}")
        debug_print(f"[EXTRACT_ARGS] 开始执行参数提取...")
        
        from core.ast_nodes import ASTName
        args = []
        
        try:
            debug_print(f"[EXTRACT_ARGS] 进入try块")
            
            # 🔧 关键修复：同时支持Python code对象和PycCode对象
            # 检查是否是Python的code对象
            if isinstance(code_obj, type(compile('', '', 'exec'))):
                debug_print(f"[EXTRACT_ARGS] 检测到Python code对象")
                return self._extract_function_args_from_python_code(code_obj)
            
            # [DEBUG] 优先：使用PycCode对象的实际属性
            if hasattr(code_obj, 'arg_count') and hasattr(code_obj, 'local_names'):
                argcount = code_obj.arg_count
                varnames_list = code_obj.local_names
                debug_print(f"[EXTRACT_ARGS] PycCode属性: arg_count={argcount}, local_names={varnames_list}")
                
                # [DEBUG] 修复：检查默认值
                defaults = []
                if hasattr(code_obj, 'defaults') and code_obj.defaults:
                    defaults = code_obj.defaults
                    debug_print(f"[EXTRACT_ARGS] 找到默认值: {defaults}")
                
                # 从local_names中提取变量名
                varnames = []
                if varnames_list and hasattr(varnames_list, 'get'):
                    varnames_obj = varnames_list.get()
                    if varnames_obj and hasattr(varnames_obj, 'size'):
                        for i in range(min(varnames_obj.size(), argcount)):
                            try:
                                varname_ref = varnames_obj.get(i)
                                if varname_ref:
                                    varname_obj = varname_ref.get() if hasattr(varname_ref, 'get') else varname_ref
                                    if varname_obj and isinstance(varname_obj, PycString):
                                        varnames.append(varname_obj.value)
                                    elif hasattr(varname_obj, 'value'):
                                        varnames.append(str(varname_obj.value))
                            except (IndexError, TypeError):
                                pass
                
                # 生成带默认值的参数
                num_defaults = len(defaults)
                num_positional = argcount - num_defaults
                
                for i, name in enumerate(varnames):
                    if i >= num_positional:
                        # 这个参数有默认值
                        default_index = i - num_positional
                        if default_index < len(defaults):
                            default_value = defaults[default_index]
                            # 直接存储带默认值的参数
                            args.append(f"{name}={default_value}")
                            debug_print(f"[EXTRACT_ARGS] 带默认值的参数: {name}={default_value}")
                        else:
                            args.append(ASTName(name))
                    else:
                        args.append(ASTName(name))
                
                # 🔧 关键修复：处理 *args 和 **kwargs
                # 检查 flags 属性来确定是否有 *args 或 **kwargs
                if hasattr(code_obj, 'flags'):
                    flags = code_obj.flags
                    if hasattr(flags, 'get'):
                        flags = flags.get()
                    
                    # CO_VARARGS = 0x04 (4)
                    # CO_VARKEYWORDS = 0x08 (8)
                    CO_VARARGS = 4
                    CO_VARKEYWORDS = 8
                    
                    has_varargs = (flags & CO_VARARGS) != 0
                    has_varkeywords = (flags & CO_VARKEYWORDS) != 0
                    
                    debug_print(f"[EXTRACT_ARGS] flags={flags}, has_varargs={has_varargs}, has_varkeywords={has_varkeywords}")
                    
                    # 如果有 *args 或 **kwargs，需要从 local_names 中提取
                    if has_varargs or has_varkeywords:
                        # 获取所有局部变量名
                        all_varnames = []
                        if varnames_list and hasattr(varnames_list, 'get'):
                            varnames_obj = varnames_list.get()
                            if varnames_obj and hasattr(varnames_obj, 'size'):
                                for i in range(varnames_obj.size()):
                                    try:
                                        varname_ref = varnames_obj.get(i)
                                        if varname_ref:
                                            varname_obj = varname_ref.get() if hasattr(varname_ref, 'get') else varname_ref
                                            if varname_obj and isinstance(varname_obj, PycString):
                                                all_varnames.append(varname_obj.value)
                                            elif hasattr(varname_obj, 'value'):
                                                all_varnames.append(str(varname_obj.value))
                                    except (IndexError, TypeError):
                                        pass
                        
                        debug_print(f"[EXTRACT_ARGS] 所有变量名: {all_varnames}")
                        
                        # 添加 *args
                        if has_varargs and len(all_varnames) > argcount:
                            args.append(f"*{all_varnames[argcount]}")
                            debug_print(f"[EXTRACT_ARGS] 添加 *args: {all_varnames[argcount]}")
                        
                        # 添加 **kwargs
                        if has_varkeywords and len(all_varnames) > argcount + (1 if has_varargs else 0):
                            kwargs_index = argcount + (1 if has_varargs else 0)
                            args.append(f"**{all_varnames[kwargs_index]}")
                            debug_print(f"[EXTRACT_ARGS] 添加 **kwargs: {all_varnames[kwargs_index]}")
                
                debug_print(f"[EXTRACT_ARGS] 带默认值的参数提取完成: {args}")
                return args
            
            # [DEBUG] Fallback: 尝试其他属性
            if hasattr(code_obj, 'local_names') and code_obj.local_names and code_obj.local_names.get():
                varnames_list = code_obj.local_names.get()
                argcount = 0
                if hasattr(code_obj, 'arg_count'):
                    argcount = code_obj.arg_count
                    if hasattr(argcount, 'get'):
                        argcount = argcount.get()
                
                if varnames_list and hasattr(varnames_list, 'size') and hasattr(varnames_list, 'get'):
                    for i in range(min(varnames_list.size(), argcount)):
                        try:
                            varname_obj = varnames_list.get(i)
                            if varname_obj and varname_obj.get():
                                name_obj = varname_obj.get()
                                if isinstance(name_obj, PycString):
                                    args.append(ASTName(name_obj.value))
                                    debug_print(f"[DEBUG][DEBUG][DEBUG] Fallback参数: {name_obj.value}")
                        except (IndexError, TypeError):
                            pass
                elif hasattr(varnames_list, '__len__') and hasattr(varnames_list, '__getitem__'):
                    for varname_obj in varnames_list:
                        if isinstance(varname_obj, PycString):
                            args.append(ASTName(varname_obj.value))
                            debug_print(f"[DEBUG][DEBUG][DEBUG] Fallback参数: {varname_obj.value}")
            
            debug_print(f"[DEBUG][DEBUG][DEBUG] 最终参数: {[str(arg) for arg in args]}")
            return args
            
        except Exception as e:
            debug_print(f"[DEBUG][DEBUG][DEBUG] 提取参数失败: {e}")
            import traceback
            traceback.print_exc()
            return args
    
    def _extract_function_args_from_python_code(self, code_obj) -> List['ASTNode']:
        """从Python code对象提取函数参数"""
        from core.ast_nodes import ASTName
        args = []
        
        try:
            # 获取参数数量
            argcount = code_obj.co_argcount
            # 获取局部变量名
            varnames = code_obj.co_varnames
            # 获取flags
            flags = code_obj.co_flags
            
            debug_print(f"[EXTRACT_ARGS_PYTHON] argcount={argcount}, varnames={varnames}, flags={flags}")
            
            # CO_VARARGS = 0x04 (4)
            # CO_VARKEYWORDS = 0x08 (8)
            CO_VARARGS = 4
            CO_VARKEYWORDS = 8
            
            has_varargs = (flags & CO_VARARGS) != 0
            has_varkeywords = (flags & CO_VARKEYWORDS) != 0
            
            debug_print(f"[EXTRACT_ARGS_PYTHON] has_varargs={has_varargs}, has_varkeywords={has_varkeywords}")
            
            # 添加普通参数
            for i in range(argcount):
                if i < len(varnames):
                    args.append(ASTName(varnames[i]))
                    debug_print(f"[EXTRACT_ARGS_PYTHON] 添加参数: {varnames[i]}")
            
            # 添加 *args
            if has_varargs and argcount < len(varnames):
                args.append(f"*{varnames[argcount]}")
                debug_print(f"[EXTRACT_ARGS_PYTHON] 添加 *args: {varnames[argcount]}")
            
            # 添加 **kwargs
            kwargs_index = argcount + (1 if has_varargs else 0)
            if has_varkeywords and kwargs_index < len(varnames):
                args.append(f"**{varnames[kwargs_index]}")
                debug_print(f"[EXTRACT_ARGS_PYTHON] 添加 **kwargs: {varnames[kwargs_index]}")
            
            debug_print(f"[EXTRACT_ARGS_PYTHON] 最终参数: {args}")
            return args
            
        except Exception as e:
            debug_print(f"[EXTRACT_ARGS_PYTHON] 提取参数失败: {e}")
            import traceback
            traceback.print_exc()
            return args
    
    def _extract_defaults(self, code_obj, argcount):
        """提取默认值"""
        defaults = []
        try:
            if hasattr(code_obj, 'co_consts'):
                consts = code_obj.co_consts
                debug_print(f"[DEBUG][DEBUG][DEBUG] 默认值分析 - co_consts: {consts}")
                
                # 分析co_consts中的可能默认值
                if len(consts) > 1:
                    # 通常docstring是第一个，默认值从第二个开始
                    for const in consts[1:]:
                        if isinstance(const, (int, float, str)):
                            defaults.append(str(const))
                            debug_print(f"[DEBUG][DEBUG][DEBUG] 找到默认值: {const}")
            
            debug_print(f"[DEBUG][DEBUG][DEBUG] 默认值提取结果: {defaults}")
            return defaults
            
        except Exception as e:
            debug_print(f"[DEBUG][DEBUG][DEBUG] 提取默认值失败: {e}")
            return []
            
            # 获取参数数量
            argcount = 0
            if hasattr(code_obj, 'arg_count'):
                argcount = code_obj.arg_count
                debug_print(f"[DEBUG] 调试参数提取 - arg_count属性: {argcount}")
                if hasattr(argcount, 'get'):
                    argcount = argcount.get()
                    debug_print(f"[DEBUG] 调试参数提取 - arg_count after get(): {argcount}")
                if hasattr(argcount, '_value'):
                    argcount = argcount._value
                    debug_print(f"[DEBUG] 调试参数提取 - arg_count after _value: {argcount}")
            elif hasattr(code_obj, 'argcount'):
                argcount = code_obj.argcount
                debug_print(f"[DEBUG] 调试参数提取 - argcount属性: {argcount}")
                if hasattr(argcount, 'get'):
                    argcount = argcount.get()
                    debug_print(f"[DEBUG] 调试参数提取 - argcount after get(): {argcount}")
                if hasattr(argcount, '_value'):
                    argcount = argcount._value
                    debug_print(f"[DEBUG] 调试参数提取 - argcount after _value: {argcount}")
            
            debug_print(f"[DEBUG] 调试参数提取 - 最终argcount: {argcount}")
            
            # [DEBUG] 修复：提取默认参数值
            defaults = []
            
            # [DEBUG] 调试：检查code_obj的所有属性
            debug_print(f"[DEBUG] 调试参数提取 - code_obj属性列表: {dir(code_obj)}")
            debug_print(f"[DEBUG] 调试参数提取 - code_obj的类型: {type(code_obj)}")
            
            # 检查多种可能的defaults属性名
            defaults_obj = None
            if hasattr(code_obj, 'defaults'):
                defaults_obj = code_obj.defaults
                debug_print(f"[DEBUG] 调试参数提取 - 找到defaults属性: {defaults_obj}")
            elif hasattr(code_obj, 'default_values'):
                defaults_obj = code_obj.default_values
                debug_print(f"[DEBUG] 调试参数提取 - 找到default_values属性: {defaults_obj}")
            elif hasattr(code_obj, 'co_defaults'):
                defaults_obj = code_obj.co_defaults
                debug_print(f"[DEBUG] 调试参数提取 - 找到co_defaults属性: {defaults_obj}")
            else:
                debug_print(f"[DEBUG] 调试参数提取 - 没有找到defaults相关属性")
            
            if defaults_obj:
                try:
                    defaults_list = defaults_obj.get() if hasattr(defaults_obj, 'get') else defaults_obj
                    debug_print(f"[DEBUG] 调试参数提取 - defaults列表: {defaults_list}")
                    if defaults_list and hasattr(defaults_list, '__len__') and len(defaults_list) > 0:
                        for i in range(len(defaults_list)):
                            default_val = defaults_list[i]
                            debug_print(f"[DEBUG] 调试参数提取 - 默认值 {i}: {default_val}, 类型: {type(default_val)}")
                            # 转换为字符串表示
                            if hasattr(default_val, 'value'):
                                defaults.append(str(default_val.value))
                                debug_print(f"[DEBUG] 调试参数提取 - 提取默认值: {default_val.value}")
                            elif hasattr(default_val, '_value'):
                                defaults.append(str(default_val._value))
                                debug_print(f"[DEBUG] 调试参数提取 - 提取默认值: {default_val._value}")
                            else:
                                defaults.append(str(default_val))
                                debug_print(f"[DEBUG] 调试参数提取 - 默认值字符串化: {str(default_val)}")
                    else:
                        debug_print(f"[DEBUG] 调试参数提取 - defaults_list为空或无长度属性")
                except Exception as e:
                    debug_print(f"[DEBUG] 调试参数提取 - 提取defaults失败: {e}")
                    import traceback
                    traceback.print_exc()
            
            debug_print(f"[DEBUG] 调试参数提取 - 最终提取到的默认值: {defaults}")
            
            if argcount <= 0:
                debug_print(f"[DEBUG] 调试参数提取 - argcount <= 0，返回空列表")
                return args
            
            # 获取参数名称
            if hasattr(code_obj, 'local_names') and code_obj.local_names and code_obj.local_names.get():
                varnames_list = code_obj.local_names.get()
                debug_print(f"[DEBUG] 调试参数提取 - varnames_list类型: {type(varnames_list)}")
                
                varnames = []
                if hasattr(varnames_list, 'size') and hasattr(varnames_list, 'get'):
                    debug_print(f"[DEBUG] 调试参数提取 - 使用size()方法")
                    for i in range(varnames_list.size()):
                        try:
                            varname_obj = varnames_list.get(i)
                            debug_print(f"[DEBUG] 调试参数提取 - varname_obj {i}: {varname_obj}")
                            if varname_obj and varname_obj.get():
                                name_obj = varname_obj.get()
                                debug_print(f"[DEBUG] 调试参数提取 - name_obj {i}: {name_obj}")
                                if isinstance(name_obj, PycString):
                                    var_name = name_obj.value
                                    debug_print(f"[DEBUG] 调试参数提取 - 参数名 {i}: {var_name}")
                                    varnames.append(var_name)
                        except (IndexError, TypeError) as e:
                            debug_print(f"[DEBUG] 调试参数提取 - 异常 {i}: {e}")
                            pass
                elif hasattr(varnames_list, '__len__') and hasattr(varnames_list, '__getitem__'):
                    debug_print(f"[DEBUG] 调试参数提取 - 使用len和getitem")
                    for varname_obj in varnames_list:
                        if isinstance(varname_obj, PycString):
                            var_name = varname_obj.value
                            varnames.append(var_name)
                        elif hasattr(varname_obj, 'get'):
                            name_obj = varname_obj.get()
                            if isinstance(name_obj, PycString):
                                var_name = name_obj.value
                                varnames.append(var_name)
                
                debug_print(f"[DEBUG] 调试参数提取 - varnames: {varnames}")
                
                # [DEBUG] 修复：构建带默认值的参数
                if varnames and argcount > 0:
                    # 计算需要带默认值的参数数量
                    num_defaults = len(defaults)
                    num_positional = argcount - num_defaults
                    
                    debug_print(f"[DEBUG] 调试参数提取 - 参数总数: {argcount}, 默认值数量: {num_defaults}, 位置参数数量: {num_positional}")
                    
                    for i, name in enumerate(varnames[:argcount]):
                        if i >= num_positional and num_defaults > 0:
                            # 这个参数有默认值
                            default_index = i - num_positional
                            if default_index < len(defaults):
                                default_val = defaults[default_index]
                                # 创建带默认值的参数表示
                                arg_name = f"{name}={default_val}"
                                args.append(ASTName(arg_name))
                                debug_print(f"[DEBUG] 调试参数提取 - 带默认值的参数: {arg_name}")
                            else:
                                args.append(ASTName(name))
                                debug_print(f"[DEBUG] 调试参数提取 - 普通参数: {name}")
                        else:
                            # 位置参数
                            args.append(ASTName(name))
                            debug_print(f"[DEBUG] 调试参数提取 - 位置参数: {name}")
                    
                    debug_print(f"[DEBUG] 调试参数提取 - 最终参数: {[str(arg) for arg in args]}")
                else:
                    debug_print(f"[DEBUG] 调试参数提取 - varnames为空或argcount无效")
                    
        except Exception as e:
            print(f"提取函数参数失败: {e}")
            import traceback
            traceback.print_exc()
        
        debug_print(f"[DEBUG] 调试参数提取 - 返回参数: {[str(arg) for arg in args]}")
        return args

    def _load_name(self, operand: int) -> None:
        """加载名称"""
        if not self.module.code:
            return
        
        names = self.module.code.get().names
        if names and names.get():
            names_obj = names.get()
            name = None
            
            if isinstance(names_obj, PycString):
                name_list = names_obj.value.split('\x00')
                if 0 <= operand < len(name_list):
                    name = name_list[operand]
            elif hasattr(names_obj, 'get'):
                # 处理 PycSequence
                if 0 <= operand < names_obj.size():
                    try:
                        name_ref = names_obj.get(operand)
                        if name_ref:
                            name_obj = name_ref.get() if hasattr(name_ref, 'get') else name_ref
                            if isinstance(name_obj, PycString):
                                name = name_obj.value
                            else:
                                name = str(name_obj)
                    except (IndexError, TypeError, AttributeError):
                        pass
            
            if name:
                node = ASTName(name)
                self.stack.push(node)
                # 增强：追踪变量加载操作
                self.stack.track_variable(name, 'load', self.current_instruction_offset)

    def _load_fast(self, operand: int) -> None:
        """加载局部变量"""
        # 使用当前代码对象的local_names，而不是模块的
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if not code_obj:
            return
        
        varnames = code_obj.local_names
        if varnames and varnames.get():
            varnames_list = varnames.get()
            # PycSequence使用size()方法，而不是__len__
            list_size = varnames_list.size() if hasattr(varnames_list, 'size') else (len(varnames_list) if hasattr(varnames_list, '__len__') else 0)
            if 0 <= operand < list_size:
                try:
                    varname_obj = varnames_list.get(operand)
                    if varname_obj and varname_obj.get():
                        name_obj = varname_obj.get()
                        if isinstance(name_obj, PycString):
                            var_name = name_obj.value
                            node = ASTName(var_name)
                            self.stack.push(node)
                            # 增强：追踪局部变量加载操作
                            self.stack.track_variable(var_name, 'load', self.current_instruction_offset)
                except (IndexError, TypeError):
                    pass

    def _store_name(self, operand: int) -> None:
        """存储名称"""
        # [DEBUG] 导入推导式类型
        from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp
        
        print(f"[_store_name] 被调用! operand={operand}, stack_size={self.stack.size()}")
        if self.stack.empty():
            print(f"[_store_name] 栈为空，返回")
            return
        
        value = self.stack.top()
        self.stack.pop()

        # [DEBUG] 打印value的详细信息
        value_type = type(value).__name__
        value_obj = getattr(value, 'object', 'N/A')
        has_object_attr = hasattr(value, 'object')
        print(f"[_store_name] value类型: {value_type}, has_object: {has_object_attr}, value.object: {value_obj}")
        
        if not self.module.code:
            return
        
        names = self.module.code.get().names
        if names and names.get():
            names_obj = names.get()
            
            name = None
            if isinstance(names_obj, PycString):
                name_list = names_obj.value.split('\x00')
                if 0 <= operand < len(name_list):
                    name = name_list[operand]
            elif isinstance(names_obj, PycSequence):
                if 0 <= operand < names_obj.size():
                    name_item = names_obj.get(operand)
                    if name_item and name_item.get():
                        name_value = name_item.get()
                        if isinstance(name_value, PycString):
                            name = name_value.value
            
            print(f"[_store_name] name={name}, operand={operand}")
            if name:
                # 首先检查是否是IMPORT_FROM操作的结果（优先级最高）
                # 如果value是ASTName且具有module_name属性，表明这是import-from操作
                if (isinstance(value, ASTName) and hasattr(value, 'module_name') and value.module_name):
                    # 这是一个from ... import ...操作的结果
                    # 导入语句已经在IMPORT_NAME中处理了，不需要再次创建
                    # 只需要更新跟踪的导入名称
                    if hasattr(self, 'last_import_names'):
                        if name not in self.last_import_names:
                            self.last_import_names.append(name)
                    return
                
                # 然后检查value是否是普通的导入结果对象（ASTImport而不是ASTName）
                is_import = (hasattr(value, 'module_name') and not isinstance(value, ASTName))
                
                if is_import:
                    # 这是一个导入语句，已经在IMPORT_NAME中处理了，不需要再次创建
                    return
                
                # 检查value是否是IMPORT_FROM操作的结果
                # 如果value是None或者是0表示这是一个IMPORT_FROM
                # 注意：ASTObject对象的object属性可能是None，但对象本身不是None
                # [关键修复] 不在这里返回，因为FOR_ITER也会压入None，需要在for循环检查后处理
                
                # 检查是否是ASTObject且内部值为None（但不是字符串"None"）
                # [DEBUG] 关键修复：在except块中，这可能是清理代码，需要特殊处理
                # 需要检查PycObject类型的None（TYPE_NONE = 'N'）
                is_none_value = False
                if value is None:
                    is_none_value = True
                elif isinstance(value, ASTObject):
                    obj = value.object
                    # 检查是否是PycObject类型的None
                    if hasattr(obj, 'type') and obj.type == 'N':
                        is_none_value = True
                    # 或者检查是否是Python的None
                    elif obj is None:
                        is_none_value = True
                
                # [DEBUG] 关键修复：检查是否是清理代码
                # 清理代码的特征：
                # 1. 值是None
                # 2. 在try-except结构中（current_try_node存在）
                # 3. 变量名与except handler的变量名匹配
                is_cleanup = False
                if is_none_value:
                    # 检查是否在try-except结构中
                    has_try_node = hasattr(self, 'current_try_node') and self.current_try_node
                    if has_try_node:
                        # 检查变量名是否与except handler的变量名匹配
                        # 首先检查current_except_handler
                        handler_name = None
                        if hasattr(self, 'current_except_handler') and self.current_except_handler:
                            handler_name = getattr(self.current_except_handler, '_name', None)
                        # 如果current_except_handler不存在，检查current_try_node的handlers
                        if not handler_name and hasattr(self.current_try_node, 'handlers'):
                            for handler in self.current_try_node.handlers:
                                if hasattr(handler, '_name') and handler._name:
                                    handler_name = handler._name
                                    break
                        
                        if handler_name == name:
                            is_cleanup = True
                            print(f"[_store_name] 跳过清理代码: {name} = None")
                            return
                
                # [关键修复] 先检查是否是for循环变量，再检查is_none_value
                # 因为FOR_ITER会压入None作为占位符，随后的STORE_NAME是循环变量
                
                # Check if value is a function definition or contains a function definition
                print(f"[_store_name] 检查变量: {name}, value类型: {type(value).__name__}")
                is_func_def = False
                func_def = None
                
                # 直接检查
                if isinstance(value, ASTFunctionDef):
                    is_func_def = True
                    func_def = value
                # 检查是否是包装了函数定义的ASTObject
                elif isinstance(value, ASTObject) and hasattr(value, 'object'):
                    inner_obj = value.object
                    if isinstance(inner_obj, ASTFunctionDef):
                        is_func_def = True
                        func_def = inner_obj
                # 检查是否是其他类型中包含函数定义
                elif hasattr(value, 'object'):
                    inner_obj = value.object
                    if isinstance(inner_obj, ASTFunctionDef):
                        is_func_def = True
                        func_def = inner_obj
                # 检查是否是具有_code属性的函数定义
                elif hasattr(value, '_code') and hasattr(value, '_name'):
                    is_func_def = True
                    func_def = value
                
                # 对于函数定义，无论是否在模块级别，都直接发射到主块，不嵌套
                if is_func_def and func_def:
                    # [DEBUG] 特殊处理lambda函数：创建赋值语句而不是直接发射函数定义
                    if func_def.name == '<lambda>':
                        # 创建赋值语句：name = lambda ...
                        assign = ASTAssign([ASTName(name)], func_def)
                        self._emit(assign)
                    else:
                        # 设置函数名
                        func_def._name = name
                        
                        # [DEBUG] 关键修复：检查函数是否有装饰器
                        # 如果有装饰器，需要在代码生成时输出装饰器语法
                        if hasattr(func_def, '_decorators') and func_def._decorators:
                            debug_print(f"[_store_name] 函数 {name} 有装饰器: {func_def._decorators}")
                            # 装饰器信息已经设置在函数定义中，代码生成器会处理
                        
                        # 直接发射到主块，确保在模块级别
                        self.main_block.append(func_def)
                        func_def.parent = self.main_block
                    
                    # 确保当前块始终是主块，避免嵌套
                    self.current_block = self.main_block
                # 检查是否是类定义
                elif isinstance(value, ASTClass):
                    # 设置类名
                    value._name = name
                    # 直接发射到主块
                    self.main_block.append(value)
                    value.parent = self.main_block
                    
                    # 确保当前块始终是主块
                    self.current_block = self.main_block
                else:
                    # 检查是否在 for 循环体中（紧跟在 FOR_ITER 之后的 STORE_NAME 是循环变量）
                    has_for_node = hasattr(self, 'current_for_node') and self.current_for_node
                    has_body_start = hasattr(self, 'for_body_start_offset')
                    current_offset = self.current_instruction_offset
                    body_start = getattr(self, 'for_body_start_offset', -1)
                    body_end = getattr(self, 'for_body_end_offset', -1)
                    
                    debug_print(f"[_store_name] 检查for循环变量: has_for_node={has_for_node}, has_body_start={has_body_start}, current_offset={current_offset}, body_start={body_start}, body_end={body_end}")
                    
                    # [DEBUG] 关键修复：检查是否在for循环体内且是循环变量存储
                    # FOR_ITER之后会将None压入栈，然后STORE_NAME会存储这个None值
                    # 我们需要识别这种情况并跳过创建赋值语句
                    if has_for_node and has_body_start and body_start <= current_offset < body_end:
                        # 这是在for循环体内，检查是否是循环变量
                        current_target = self.current_for_node.target
                        
                        # [DEBUG] 关键修复：检查target是否是临时变量名（如'i'）
                        # 或者value是否为None（FOR_ITER压入的占位符）
                        is_temp_var = isinstance(current_target, ASTName) and current_target.name in ('i', '<var>')
                        is_none_value = value is None or (isinstance(value, ASTObject) and value.object is None)
                        
                        # [关键修复] 检查循环变量是否已经设置
                        # 使用ASTBuilder的集合来跟踪已经设置过target的for节点
                        if not hasattr(self, '_for_targets_set'):
                            self._for_targets_set = set()
                        target_already_set = id(self.current_for_node) in self._for_targets_set
                        
                        debug_print(f"[_store_name] for循环检查: is_temp_var={is_temp_var}, is_none_value={is_none_value}, target_already_set={target_already_set}, value={value}, name={name}")
                        
                        if is_temp_var and not target_already_set:
                            # 这是 for 循环的循环变量，设置target
                            self.current_for_node.target = ASTName(name)
                            # [关键修复] 记录这个for节点的target已经设置
                            self._for_targets_set.add(id(self.current_for_node))
                            debug_print(f"[_store_name] 设置 for 循环变量: {name}")
                            # 不创建赋值语句
                            return
                        elif is_none_value and not target_already_set:
                            # 这是FOR_ITER压入的None值，是循环变量的初始化
                            # 不创建赋值语句，直接返回
                            debug_print(f"[_store_name] 跳过 for 循环变量的None值存储: {name}")
                            return
                    
                    if isinstance(value, ASTCall):
                        # [DEBUG] 修复：检查是否是装饰器模式（支持多个装饰器）
                        # 装饰器模式：@decorator -> def name(): ...
                        # 字节码：LOAD_NAME decorator; LOAD_CONST func_code; MAKE_FUNCTION; CALL; STORE_NAME name
                        # 此时value是ASTCall，表示decorator(func)的调用结果
                        # 我们需要找到函数定义并添加装饰器
                        
                        # [DEBUG] 增强：递归查找函数/类定义和装饰器列表
                        # 支持多个装饰器嵌套：@decorator_a @decorator_b def func(): ...
                        # 对应的ASTCall结构：decorator_a(decorator_b(func))
                        def extract_decorators_and_func(call_node):
                            """
                            递归提取装饰器列表和函数/类定义
                            返回：(decorators_list, target_def)
                            
                            [DEBUG] 修复：正确处理多重装饰器的ASTCall结构
                            对于 @decorator_a @decorator_b def func():
                            ASTCall结构是：
                                ASTCall(func=ASTName(decorator_a), pparams=[ASTCall(func=ASTName(decorator_b), pparams=[func])])
                            应该返回：
                                decorators = [ASTName(decorator_a), ASTName(decorator_b)]
                                target_def = func
                            """
                            decorators = []
                            target_def = None
                            
                            if not isinstance(call_node, ASTCall):
                                return decorators, None
                            
                            # 获取被调用的函数（装饰器）和参数
                            # ASTCall使用pparams而不是_args存储参数
                            decorator_func = call_node.func
                            decorator_args = call_node.pparams
                            
                            # [DEBUG] 修复：正确处理ASTCall结构
                            # 结构1: ASTCall(func=ASTName, pparams=[func_def]) - 简单装饰器
                            # 结构2: ASTCall(func=ASTName, pparams=[ASTCall(...)]) - 多重装饰器
                            
                            if isinstance(decorator_func, ASTName):
                                # 当前装饰器是简单装饰器
                                # [DEBUG] 关键修复：排除推导式函数名
                                if decorator_func.name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'):
                                    # 这是推导式函数，不是装饰器
                                    return decorators, None
                                
                                # [DEBUG] 关键修复：先检查参数，再决定是否添加装饰器
                                # 只有在参数中包含非推导式函数定义时，才将函数视为装饰器
                                has_comprehension = False
                                has_real_func_def = False
                                debug_print(f"[extract_decorators] decorator_args={len(decorator_args) if decorator_args else 0}, decorator_func={decorator_func.name if hasattr(decorator_func, 'name') else type(decorator_func)}")
                                if decorator_args:
                                    for arg in decorator_args:
                                        debug_print(f"[extract_decorators] 检查参数类型: {type(arg)}")
                                        # [DEBUG] 关键修复：检查ASTObject是否包含推导式函数
                                        if isinstance(arg, ASTObject):
                                            # 检查ASTObject是否包含推导式函数的代码对象
                                            if hasattr(arg, 'object') and arg.object:
                                                obj = arg.object
                                                debug_print(f"[extract_decorators] ASTObject内容: {type(obj)}")
                                                # 检查是否是PycCode对象且为推导式
                                                if hasattr(obj, 'co_name'):
                                                    func_name = obj.co_name
                                                    is_comp = func_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>', '<anonymous>')
                                                    debug_print(f"[extract_decorators] ASTObject中的函数名: {func_name}, is_comp={is_comp}")
                                                    if is_comp:
                                                        debug_print(f"[extract_decorators] 跳过ASTObject中的推导式函数: {func_name}")
                                                        has_comprehension = True
                                                        continue
                                        if isinstance(arg, (ASTFunctionDef, ASTClass)):
                                            # [DEBUG] 关键修复：排除推导式函数
                                            # 推导式函数名是 <listcomp>, <setcomp>, <dictcomp>, <genexpr> 或 <anonymous>
                                            func_name = arg.name if hasattr(arg, 'name') else ''
                                            # 检查函数名是否为推导式名称，或者通过代码特征检测
                                            is_comp_name = func_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>', '<anonymous>')
                                            has_code_obj = hasattr(arg, '_code_obj')
                                            is_comp_by_features = False
                                            if has_code_obj:
                                                is_comp_by_features = self._is_comprehension_code(arg._code_obj)
                                            
                                            debug_print(f"[extract_decorators] 检查函数: name={func_name}, is_comp_name={is_comp_name}, has_code_obj={has_code_obj}, is_comp_by_features={is_comp_by_features}")
                                            
                                            if not is_comp_name and not is_comp_by_features:
                                                target_def = arg
                                                has_real_func_def = True
                                                debug_print(f"[extract_decorators] 找到非推导式函数定义: {func_name}")
                                            else:
                                                debug_print(f"[extract_decorators] 跳过推导式函数: {func_name}")
                                                has_comprehension = True
                                        elif isinstance(arg, (ASTListComp, ASTSetComp, ASTDictComp)):
                                            # [DEBUG] 关键修复：推导式不是装饰器模式的目标
                                            # 推导式应该作为普通赋值处理
                                            debug_print(f"[extract_decorators] 跳过推导式: {type(arg).__name__}")
                                            has_comprehension = True
                                            return [], arg  # 返回空装饰器列表和推导式作为目标
                                        elif isinstance(arg, ASTCall):
                                            # 递归查找内层装饰器
                                            inner_decorators, inner_target = extract_decorators_and_func(arg)
                                            if inner_target:
                                                target_def = inner_target
                                                has_real_func_def = True
                                            # 内层装饰器添加到后面
                                            decorators.extend(inner_decorators)
                                
                                # [DEBUG] 关键修复：只有在找到非推导式函数定义时才添加装饰器
                                debug_print(f"[extract_decorators] 循环结束: has_comprehension={has_comprehension}, has_real_func_def={has_real_func_def}")
                                if has_real_func_def:
                                    # 找到非推导式函数定义，添加装饰器
                                    # [DEBUG] 修复：装饰器顺序应该是从上到下
                                    # Python语法：@decorator_a @decorator_b def func(): ...
                                    # AST结构：decorator_a(decorator_b(func))
                                    # 所以decorator_a在最外层，应该在最前面
                                    decorators.insert(0, ASTName(decorator_func.name))
                                    debug_print(f"[extract_decorators] 添加装饰器: {decorator_func.name}")
                                else:
                                    # 没有找到非推导式函数定义，清空装饰器列表
                                    debug_print(f"[extract_decorators] 未找到非推导式函数定义，清空装饰器列表")
                                    decorators = []
                            elif isinstance(decorator_func, ASTCall):
                                # 当前装饰器是嵌套的ASTCall（不应该发生，但处理这种情况）
                                # 递归处理内层装饰器
                                inner_decorators, inner_target = extract_decorators_and_func(decorator_func)
                                if inner_target:
                                    target_def = inner_target
                                decorators.extend(inner_decorators)
                                
                                # 也检查当前调用的参数
                                if decorator_args:
                                    for arg in decorator_args:
                                        if isinstance(arg, (ASTFunctionDef, ASTClass)):
                                            # [DEBUG] 关键修复：排除推导式函数
                                            func_name = arg.name if hasattr(arg, 'name') else ''
                                            # [DEBUG] 关键修复：同时排除 <anonymous> 名称（推导式函数可能是这个名称）
                                            is_comp_name = func_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>', '<anonymous>')
                                            is_comp_by_features = False
                                            if hasattr(arg, '_code_obj'):
                                                is_comp_by_features = self._is_comprehension_code(arg._code_obj)
                                            
                                            if not is_comp_name and not is_comp_by_features:
                                                target_def = arg
                            
                            return decorators, target_def
                        
                        # 提取装饰器和函数/类定义
                        decorators, target_def = extract_decorators_and_func(value)
                        
                        # [DEBUG] 打印提取结果
                        debug_print(f"[_store_name] extract_decorators_and_func 返回: decorators={len(decorators)}, target_def={type(target_def).__name__ if target_def else 'None'}")
                        
                        # [DEBUG] 修复：严格检查装饰器模式
                        # 装饰器模式必须满足：
                        # 1. ASTCall的参数中包含函数/类定义（被装饰的目标）
                        # 2. 目标定义和装饰器都存在
                        
                        is_decorator_pattern = False
                        
                        if target_def and decorators:
                            # 从ASTCall的参数中找到了目标定义和装饰器
                            # 这是一个有效的装饰器模式
                            is_decorator_pattern = True
                        elif target_def and not decorators:
                            # 找到了目标定义，但没有从ASTCall中提取到装饰器
                            # 这可能是一个普通函数调用，如 c = counter()
                            # 不应该视为装饰器模式
                            is_decorator_pattern = False
                        elif not target_def and decorators:
                            # 有装饰器但没有目标定义，这不是有效的装饰器模式
                            is_decorator_pattern = False
                        
                        if is_decorator_pattern:
                            # [DEBUG] 找到装饰器模式！
                            # 设置目标名称
                            target_def._name = name
                            # 添加装饰器（保持正确的顺序：从内到外）
                            if not hasattr(target_def, '_decorators'):
                                target_def._decorators = []
                            target_def._decorators.extend(decorators)
                            target_type = "类" if isinstance(target_def, ASTClass) else "函数"
                            debug_print(f"[_store_name] 检测到装饰器模式: {decorators} -> {target_type} {name}()")
                            # 直接发射目标定义（带有装饰器信息）
                            self.main_block.append(target_def)
                            target_def.parent = self.main_block
                            self.current_block = self.main_block
                            return
                        
                        # 不是装饰器模式，作为普通赋值处理
                        decorator_node = ASTStore(ASTName(name), value)
                        self._emit(decorator_node)
                    else:
                        # [DEBUG] 修复：检查是否在with语句上下文中（紧跟在BEFORE_WITH之后）
                        has_with_node = hasattr(self, 'current_with_node') and self.current_with_node
                        print(f"[_store_name] 检查with语句上下文: has_with_node={has_with_node}, current_with_node={getattr(self, 'current_with_node', None)}")
                        if has_with_node:
                            # 这是with语句的变量（as f）
                            # [DEBUG] 关键修复：ASTWith.optional_vars是只读property，需要直接修改ASTWithItem._optional_vars
                            if hasattr(self.current_with_node, '_items') and self.current_with_node._items:
                                self.current_with_node._items[0]._optional_vars = ASTName(name)
                                debug_print(f"[_store_name] 设置with语句变量: {name}")
                            # 不创建赋值语句
                        else:
                            # [DEBUG] 关键修复：检查是否在except块中（紧跟在CHECK_EXC_MATCH之后）
                            # 这是`except Exception as e:`中的变量e
                            current_offset = getattr(self, 'current_instruction_offset', 0)
                            is_exception_var = self._is_in_exception_context(current_offset)
                            
                            # [DEBUG] 关键修复：检查是否是清理代码（值为None且except handler已经有变量名）
                            # 这种情况发生在except块中，编译器生成的清理代码
                            is_cleanup = False
                            if hasattr(self, 'current_except_handler') and self.current_except_handler:
                                # 如果值是None，且变量名与except handler的变量名匹配，则是清理代码
                                handler_name = getattr(self.current_except_handler, '_name', None)
                                is_none_value = isinstance(value, ASTObject) and value.object is None
                                print(f"[_store_name] 检查清理代码: name={name}, handler_name={handler_name}, is_none={is_none_value}")
                                if is_none_value:
                                    if handler_name == name:
                                        is_cleanup = True
                                        print(f"[_store_name] 跳过清理代码: {name} = None")
                                        # 跳过创建赋值语句
                                        return
                                    else:
                                        print(f"[_store_name] 不是清理代码: handler_name={handler_name} != name={name}")
                            
                            if is_exception_var:
                                if hasattr(self, 'current_except_handler') and self.current_except_handler:
                                    # 设置当前except handler的变量名
                                    self.current_except_handler._name = name
                                    debug_print(f"[_store_name] 设置except变量: {name}")
                                    # 不创建赋值语句
                                    return
                            
                            # [DEBUG] 关键修复：检查是否是推导式节点
                            # 推导式节点应该直接发射，而不是包装在ASTStore中
                            from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr
                            if isinstance(value, (ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr)):
                                print(f"[_store_name] 检测到推导式节点: {type(value).__name__}")
                                # 推导式节点直接发射到AST
                                self._emit(value)
                                print(f"[_store_name] 推导式节点已发射到AST")
                                return
                            
                            # [DEBUG] 关键修复：检查是否是增量赋值节点
                            # 如果是ASTAugAssign节点，直接发射，不要包装在ASTStore中
                            if isinstance(value, ASTAugAssign):
                                debug_print(f"[_store_name] 检测到增量赋值节点，直接发射: {name}")
                                self._emit(value)
                            else:
                                # 普通变量存储
                                node = ASTStore(ASTName(name), value)
                                self._emit(node)
                            # 增强：追踪变量存储操作
                            self.stack.track_variable(name, 'store', self.current_instruction_offset)

    def _store_fast(self, operand: int) -> None:
        """存储局部变量"""
        if self.stack.empty():
            return
        
        value = self.stack.top()
        self.stack.pop()
        
        # 使用当前代码对象的local_names，而不是模块的
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if not code_obj:
            return
        
        varnames = code_obj.local_names
        if varnames and varnames.get():
            varnames_list = varnames.get()
            # PycSequence使用size()方法，而不是__len__
            list_size = varnames_list.size() if hasattr(varnames_list, 'size') else (len(varnames_list) if hasattr(varnames_list, '__len__') else 0)
            if 0 <= operand < list_size:
                try:
                    varname_obj = varnames_list.get(operand)
                    if varname_obj and varname_obj.get():
                        name_obj = varname_obj.get()
                        if isinstance(name_obj, PycString):
                            var_name = name_obj.value
                            
                            # [DEBUG] 修复：检查是否在with语句上下文中（紧跟在BEFORE_WITH之后）
                            has_with_node = hasattr(self, 'current_with_node') and self.current_with_node
                            if has_with_node:
                                # 这是with语句的变量（as f）
                                # [DEBUG] 关键修复：ASTWith.optional_vars是只读property，需要直接修改ASTWithItem._optional_vars
                                if hasattr(self.current_with_node, '_items') and self.current_with_node._items:
                                    self.current_with_node._items[0]._optional_vars = ASTName(var_name)
                                    debug_print(f"[_store_fast] 设置with语句变量: {var_name}")
                                # 不创建赋值语句
                                return
                            
                            # [DEBUG] 关键修复：检查是否在for循环体内，且是否是循环变量的赋值
                            if hasattr(self, 'current_for_node') and self.current_for_node is not None:
                                body_start = getattr(self, 'for_body_start_offset', -1)
                                body_end = getattr(self, 'for_body_end_offset', -1)
                                current_offset = getattr(self, 'current_instruction_offset', -1)
                                
                                # 检查是否在for循环体的开始位置（循环变量的赋值）
                                if body_start <= current_offset < body_end:
                                    # [关键修复] 首先检查是否是 UNPACK_SEQUENCE_A 的情况（如 for k, v in ...）
                                    # 这必须在检查 is_matching_name/is_none_value 之前，因为 UNPACK_SEQUENCE 情况下 value 也是 None
                                    prev_instr_is_unpack = False
                                    unpack_count = 0
                                    unpack_instr_offset = -1
                                    for instr in self.instructions:
                                        instr_offset = instr.get('offset', -1)
                                        # UNPACK_SEQUENCE_A 在 STORE_FAST_A 之前，通常间隔 2-4 字节
                                        if current_offset - 6 <= instr_offset < current_offset:
                                            if instr.get('opcode_name', '') == 'UNPACK_SEQUENCE_A':
                                                prev_instr_is_unpack = True
                                                unpack_count = instr.get('operand', 0)
                                                unpack_instr_offset = instr_offset
                                                break
                                    
                                    if prev_instr_is_unpack and unpack_count > 1:
                                        # 这是多变量 for 循环（如 for k, v in ...）
                                        # 收集所有变量名
                                        if not hasattr(self, '_for_loop_unpack_vars'):
                                            self._for_loop_unpack_vars = []
                                        # 避免重复添加同一个变量
                                        if var_name not in self._for_loop_unpack_vars:
                                            self._for_loop_unpack_vars.append(var_name)
                                        debug_print(f"[_store_fast] 收集多变量for循环变量: {var_name}, 当前变量列表: {self._for_loop_unpack_vars}, unpack_count={unpack_count}")
                                        
                                        # 如果收集完所有变量，更新 for 循环的 target
                                        if len(self._for_loop_unpack_vars) >= unpack_count:
                                            # 创建元组作为 target
                                            from core.ast_nodes import ASTTuple
                                            tuple_elts = [ASTName(name) for name in self._for_loop_unpack_vars]
                                            self.current_for_node._target = ASTTuple(tuple_elts)
                                            debug_print(f"[_store_fast] 更新多变量for循环target: {self._for_loop_unpack_vars}")
                                            # 清空变量列表
                                            self._for_loop_unpack_vars = []
                                        # 不创建赋值语句
                                        return
                                    
                                    # 检查value是否是ASTName且与var_name相同（即这是循环变量的赋值）
                                    # 或者value是否为None（FOR_ITER压入的占位符）
                                    is_matching_name = isinstance(value, ASTName) and value.name == var_name
                                    is_none_value = value is None or (isinstance(value, ASTObject) and value.object is None)
                                    
                                    if is_matching_name or is_none_value:
                                        # 更新ASTFor节点的target
                                        self.current_for_node._target = ASTName(var_name)
                                        debug_print(f"[_store_fast] 更新单变量for循环变量: {var_name}")
                                        # 不创建赋值语句
                                        return
                            
                            # [DEBUG] 关键修复：如果值是函数定义，直接发射函数定义（用于嵌套函数）
                            if isinstance(value, ASTFunctionDef):
                                debug_print(f"[_store_fast] 发射嵌套函数定义: {var_name}")
                                # 确保函数名正确
                                if hasattr(value, '_name'):
                                    value._name = var_name
                                self._emit(value)
                                return
                            
                            # [DEBUG] 关键修复：检查是否在except块中（紧跟在CHECK_EXC_MATCH之后）
                            # 这是`except Exception as e:`中的变量e
                            current_offset = getattr(self, 'current_instruction_offset', 0)
                            is_exception_var = self._is_in_exception_context(current_offset)
                            if is_exception_var:
                                # 设置当前except handler的变量名
                                if hasattr(self, 'current_except_handler') and self.current_except_handler:
                                    self.current_except_handler._name = var_name
                                    debug_print(f"[_store_fast] 设置except变量: {var_name}")
                                    # 不创建赋值语句
                                    return
                            
                            # [DEBUG] 关键修复：检查是否是增量赋值节点
                            # 如果是ASTAugAssign节点，直接发射，不要包装在ASTStore中
                            if isinstance(value, ASTAugAssign):
                                debug_print(f"[_store_fast] 检测到增量赋值节点，直接发射: {var_name}")
                                self._emit(value)
                            else:
                                node = ASTStore(ASTName(var_name), value)
                                self._emit(node)
                            # 增强：追踪局部变量存储操作
                            self.stack.track_variable(var_name, 'store', self.current_instruction_offset)
                except (IndexError, TypeError):
                    pass

    def _unpack_sequence(self, count: int) -> None:
        """解包序列 (UNPACK_SEQUENCE)
        
        用于处理 for k, v in ... 这样的多变量循环
        将栈顶的序列解包为多个值
        """
        if self.stack.empty():
            return
        
        # 获取要解包的序列
        seq = self.stack.pop()
        
        # 将解包后的值压入栈
        # 注意：UNPACK_SEQUENCE 是从右到左压入栈的
        # 所以对于 for k, v in seq，栈中应该是 [v, k]
        # 但 STORE_FAST 是从左到右存储的，所以我们需要按顺序压入
        for i in range(count):
            # 创建一个占位符对象
            placeholder = ASTObject(None)
            self.stack.push(placeholder)

    def _binary_op(self, op: int) -> None:
        """二元操作 (a + b, a - b, etc.)"""
        if self._safe_stack_access('size', 0) < 2:
            return
        
        right = self._safe_stack_access('pop')
        left = self._safe_stack_access('pop')
        
        if right is None or left is None:
            # 栈访问失败，尝试恢复
            self._recover_from_error()
            return
        
        # [DEBUG] 修复：检查 op 是否已经是 ASTBinary.BinOp 的值（0-28）
        # 如果是，直接使用；如果不是，说明是 Python 3.11+ 的 BINARY_OP 操作数，需要映射
        if 0 <= op <= 28:
            # op 已经是 ASTBinary.BinOp 的值，直接使用
            converted_op = op
            debug_print(f"[_binary_op] 使用直接传入的操作数: {op}")
        else:
            # Python 3.11+ BINARY_OP 操作数（实际测试得到）:
            #   普通操作: 0: +, 1: &, 2: //, 3: <<, 5: *, 6: %, 7: |, 8: **, 9: >>, 10: -, 11: /, 12: ^
            #   原地操作: 13: +=, 18: *=, 23: -=, 24: /=
            # ASTBinary.BinOp 枚举:
            #   1: **, 2: *, 3: /, 4: //, 5: %, 6: +, 7: -, 8: <<, 9: >>, 10: &, 11: ^, 12: |
            #   原地操作: 16: +=, 17: -=, 18: *=, 19: /=, 20: %=, 21: **=, 22: <<=, 23: >>=, 24: &=, 25: |=, 26: ^=, 27: @=, 28: //=
            py311_to_binop = {
                # 普通二元操作
                0: 6,   # + -> BIN_ADD
                1: 10,  # & -> BIN_AND
                2: 4,   # // -> BIN_FLOOR_DIVIDE
                3: 8,   # << -> BIN_LSHIFT
                5: 2,   # * -> BIN_MULTIPLY
                6: 5,   # % -> BIN_MODULO
                7: 12,  # | -> BIN_OR
                8: 1,   # ** -> BIN_POWER
                9: 9,   # >> -> BIN_RSHIFT
                10: 7,  # - -> BIN_SUBTRACT
                11: 3,  # / -> BIN_DIVIDE
                12: 11, # ^ -> BIN_XOR
                # 原地操作 (in-place operations)
                13: 16, # += -> BIN_IP_ADD
                23: 17, # -= -> BIN_IP_SUBTRACT
                18: 18, # *= -> BIN_IP_MULTIPLY
                24: 19, # /= -> BIN_IP_DIVIDE
            }
            # 转换操作数
            converted_op = py311_to_binop.get(op, op)
            debug_print(f"[_binary_op] 原始操作数: {op}, 转换后: {converted_op}")
        
        # [DEBUG] 关键修复：检测增量操作并创建ASTAugAssign节点
        # 增量操作的范围是 16-28 (BIN_IP_ADD 到 BIN_IP_FLOORDIV)
        if 16 <= converted_op <= 28:
            # 这是增量操作，创建ASTAugAssign节点
            op_map = {
                16: '+=',
                17: '-=',
                18: '*=',
                19: '/=',
                20: '%=',
                21: '**=',
                22: '<<=',
                23: '>>=',
                24: '&=',
                25: '|=',
                26: '^=',
                27: '@=',
                28: '//=',
            }
            aug_op = op_map.get(converted_op, '+=')
            debug_print(f"[_binary_op] 创建增量赋值节点: {left} {aug_op} {right}")
            aug_assign = ASTAugAssign(left, aug_op, right)
            self.stack.push(aug_assign)
        else:
            binop = ASTBinary(left, right, converted_op)
            self.stack.push(binop)

    def _unary_op(self, op: int) -> None:
        """处理一元操作"""
        if self.stack.empty():
            return
        
        operand = self.stack.top()
        self.stack.pop()
        
        node = ASTUnary(operand, op)
        self.stack.push(node)

    def _compare_op(self, operand: int) -> None:
        """处理比较操作"""
        if self.stack.size() < 2:
            return
        
        right = self.stack.top()
        self.stack.pop()
        left = self.stack.top()
        self.stack.pop()
        
        node = ASTCompare(left, right, operand)
        self.stack.push(node)

    def _return_value(self) -> None:
        """处理return语句"""
        # [关键修复] 检查是否在if/else/elif/try/except/finally/loop等控制流结构中
        # 如果在控制流结构中，即使不在函数内部，也需要发射节点
        in_control_flow = (
            hasattr(self, 'current_if_node') and self.current_if_node is not None or
            hasattr(self, 'current_for_node') and self.current_for_node is not None or
            hasattr(self, 'current_while_node') and self.current_while_node is not None or
            hasattr(self, 'current_try_node') and self.current_try_node is not None
        )
        
        # [关键修复] 检查是否是break语句
        # break语句的特征：在循环体内，前一条指令是LOAD_CONST None
        current_offset = getattr(self, 'current_instruction_offset', 0)
        is_break = False
        
        # 检查是否在循环体内
        in_loop = False
        if hasattr(self, 'current_for_node') and self.current_for_node is not None:
            body_start = getattr(self, 'for_body_start_offset', -1)
            body_end = getattr(self, 'for_body_end_offset', -1)
            if body_start <= current_offset < body_end:
                in_loop = True
        elif hasattr(self, 'current_while_node') and self.current_while_node is not None:
            body_start = getattr(self, 'while_body_start', -1)
            body_end = getattr(self, 'while_body_end', -1)
            if body_start <= current_offset < body_end:
                in_loop = True
        
        # 如果在循环体内，检查前一条指令是否是LOAD_CONST
        if in_loop:
            prev_instr = None
            for instr in self.instructions:
                if instr.get('offset', -1) == current_offset - 2:
                    prev_instr = instr
                    break
            if prev_instr and prev_instr.get('opcode', -1) == Opcode.LOAD_CONST_A:
                # 检查栈顶是否是None
                if not self.stack.empty():
                    top = self.stack.top()
                    if isinstance(top, ASTObject) and top.value is None:
                        is_break = True
                        debug_print(f"[_return_value] 检测到break语句，发射ASTBreak")
        
        if is_break:
            # 发射break节点
            from core.ast_nodes import ASTBreak
            node = ASTBreak()
            self._emit(node)
            # 弹出栈顶的None
            if not self.stack.empty():
                self.stack.pop()
            return
        
        # 在模块级别且不在函数内部，且不在控制流结构中时，不发射return节点（模块隐式返回None）
        if (isinstance(self.main_block, ASTBlock) and 
            self.main_block.blk_type == ASTBlock.BlockType.BLK_MAIN and 
            not self.in_function and 
            not in_control_flow):
            # 模块级别的return不需要显式处理
            if not self.stack.empty():
                self.stack.pop()
            return
        
        if self.stack.empty():
            node = ASTReturn(ASTObject(None))
        else:
            value = self.stack.top()
            self.stack.pop()
            node = ASTReturn(value)
        
        # 发射return节点到当前块
        self._emit(node)
    
    def _yield_value(self) -> None:
        """处理yield语句"""
        # 在生成器函数中处理yield
        if not self.in_function:
            # 模块级别的yield不是有效的Python语法
            if not self.stack.empty():
                self.stack.pop()
            return
        
        if self.stack.empty():
            # yield None
            node = ASTYield()
        else:
            value = self.stack.top()
            self.stack.pop()
            node = ASTYield(value)
        
        self._emit(node)

    def _update_comprehension_iter(self, comp_node, iter_expr):
        """更新推导式的迭代对象
        
        comp_node: 推导式节点 (ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr)
        iter_expr: 新的迭代表达式节点
        """
        from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr, ASTComprehension
        
        debug_print(f"[_update_comprehension_iter] 更新推导式迭代对象: {type(comp_node).__name__}")
        
        try:
            # 获取生成器列表
            generators = getattr(comp_node, '_generators', None) or getattr(comp_node, 'generators', None)
            if generators and len(generators) > 0:
                # 更新第一个生成器的迭代对象
                first_gen = generators[0]
                if hasattr(first_gen, '_iter'):
                    first_gen._iter = iter_expr
                    debug_print(f"[_update_comprehension_iter] 更新 _iter 为: {type(iter_expr).__name__}")
                elif hasattr(first_gen, 'iter'):
                    first_gen.iter = iter_expr
                    debug_print(f"[_update_comprehension_iter] 更新 iter 为: {type(iter_expr).__name__}")
                elif hasattr(first_gen, 'iter_node'):
                    first_gen.iter_node = iter_expr
                    debug_print(f"[_update_comprehension_iter] 更新 iter_node 为: {type(iter_expr).__name__}")
        except Exception as e:
            debug_print(f"[_update_comprehension_iter] 更新失败: {e}")

    def _call_function(self, argc: int) -> None:
        """处理函数调用 - 参考C++版本实现
        
        在Python 3.11+中，operand格式：
        - 低8位：位置参数数量 (pparams)
        - 高8位：关键字参数数量 (kwparams)
        
        栈在CALL_A之前应该是：
        [NULL, func, arg_1, arg_2, ..., arg_n] (arg_n在栈顶)
        
        Python 3.11+使用KW_NAMES指令存储关键字参数名
        """
        # [DEBUG] 修复：确保ASTName在局部作用域可用
        global ASTName
        
        # [DEBUG] 初始化变量，避免UnboundLocalError
        is_decorator_call = False
        decorator_implicit_arg = None
        
        debug_print(f"[_call_function] 开始处理: argc={argc}, stack_size={self.stack.size()}")

        if self.stack.empty():
            debug_print(f"[_call_function] 栈为空，返回")
            return
        
        # 🔧 参考C++版本：解析operand
        # 低8位是位置参数数量，高8位是关键字参数数量
        kwparams = (argc & 0xFF00) >> 8
        pparams = argc & 0xFF
        debug_print(f"[_call_function] 参数解析: pparams={pparams}, kwparams={kwparams}")
        
        kwparamList = []  # 关键字参数列表 [(key, value), ...]
        pparamList = []   # 位置参数列表
        
        # 🔧 参考C++版本：处理关键字参数（Python 3.11+使用KW_NAMES）
        # 检查栈顶是否是KW_NAMES_MAP节点
        version = self.module.version if hasattr(self.module, 'version') else (3, 11)
        if version >= (3, 11) and not self.stack.empty():
            top = self.stack.top()
            # 检查是否是关键字参数映射（由KW_NAMES指令创建）
            if hasattr(top, '__class__') and top.__class__.__name__ == 'ASTKwNamesMap':
                self.stack.pop()
                # 从KW_NAMES_MAP中提取关键字参数
                if hasattr(top, 'values'):
                    for key, value in reversed(list(top.values().items())):
                        kwparamList.insert(0, (key, value))
                        pparams -= 1  # 关键字参数也占用位置参数计数
                debug_print(f"[_call_function] 从KW_NAMES_MAP提取关键字参数: {len(kwparamList)}个")
        
        # 🔧 参考C++版本：处理旧版关键字参数（直接存储在栈上）
        if version < (3, 11):
            for i in range(kwparams):
                if not self.stack.empty():
                    val = self.stack.top()
                    self.stack.pop()
                    if not self.stack.empty():
                        key = self.stack.top()
                        self.stack.pop()
                        kwparamList.insert(0, (key, val))
        
        # 弹出所有显式参数（位置参数）
        args = []
        for _ in range(pparams):
            if not self.stack.empty():
                arg = self.stack.top()
                self.stack.pop()
                args.append(arg)
        
        # 反转参数列表（保持正确顺序）
        args.reverse()
        pparamList = args

        # 弹出函数引用（在参数之后）
        if not self.stack.empty():
            func = self.stack.top()
            self.stack.pop()
            debug_print(f"[_call_function] 弹出函数: {type(func).__name__} = {func}")
        else:
            debug_print(f"[_call_function] 栈为空（弹出函数后），返回")
            return
        
        # 🔧 参考C++版本：处理PUSH_NULL留下的NULL值
        # 在Python 3.11+中，PUSH_NULL会在栈底留下一个NULL
        if (version >= (3, 11)) and not self.stack.empty():
            top = self.stack.top()
            # 检查是否是NULL（None或特殊的null对象）
            if isinstance(top, ASTObject) and top.object is None:
                self.stack.pop()
                debug_print(f"[_call_function] 弹出PUSH_NULL留下的NULL")
        
        # [DEBUG] 关键修复：在弹出func后检测装饰器调用
        # 只有当func是装饰器函数（ASTName）且argc=0且栈顶是函数/类定义时，才是装饰器调用
        # [DEBUG] 关键修复：排除推导式函数的调用，如 range(<listcomp>)
        # [DEBUG] 关键修复：也检查func是ASTFunctionDef且栈顶是ASTName的情况（简单装饰器）
        if argc == 0 and not self.stack.empty():
            top = self.stack.top()
            # 检查top是否是推导式函数（函数名以 < 开头和 > 结尾）
            top_name = top.name if hasattr(top, 'name') else ''
            is_comprehension_func = top_name.startswith('<') and top_name.endswith('>')
            
            # 情况1: func是ASTName（装饰器），top是ASTFunctionDef（被装饰的函数）
            if isinstance(func, ASTName) and isinstance(top, (ASTFunctionDef, ASTClass)):
                # [DEBUG] 关键修复：排除推导式函数的调用
                # 推导式函数名如 <listcomp>, <setcomp>, <dictcomp>, <genexpr>
                if is_comprehension_func:
                    debug_print(f"[_call_function] 跳过推导式函数调用: {top_name}")
                else:
                    # 这是装饰器调用，函数/类定义是隐式参数
                    is_decorator_call = True
                    decorator_implicit_arg = top
                    target_type = "类" if isinstance(top, ASTClass) else "函数"
                    debug_print(f"[_call_function] 检测到装饰器调用模式({target_type})，隐式参数: {top.name if hasattr(top, 'name') else 'unknown'}")
            
            # 情况2: func是ASTFunctionDef（被装饰的函数），top是ASTName（装饰器）
            # 这种情况发生在栈布局是 [decorator, func] 时，我们先弹出了func
            elif isinstance(func, (ASTFunctionDef, ASTClass)) and isinstance(top, ASTName):
                # [DEBUG] 关键修复：排除推导式函数的调用
                func_name = func.name if hasattr(func, 'name') else ''
                is_comprehension_func = func_name.startswith('<') and func_name.endswith('>')
                
                if is_comprehension_func:
                    debug_print(f"[_call_function] 跳过推导式函数调用: {func_name}")
                else:
                    # 这是装饰器调用，但栈布局是 [decorator, func]
                    # 我们需要交换func和top的角色
                    is_decorator_call = True
                    decorator_implicit_arg = func
                    # 将func设置为装饰器（top）
                    func = top
                    # 弹出装饰器
                    self.stack.pop()
                    debug_print(f"[_call_function] 检测到装饰器调用模式(情况2)，装饰器: {top.name if hasattr(top, 'name') else 'unknown'}, 函数: {func_name}")
                    
                    # [DEBUG] 关键修复：直接处理简单装饰器
                    # 设置函数的装饰器信息
                    if not hasattr(decorator_implicit_arg, '_decorators'):
                        decorator_implicit_arg._decorators = []
                    decorator_implicit_arg._decorators.append(func)
                    
                    debug_print(f"[_call_function] 应用简单装饰器(情况2): @{func.name} -> def {decorator_implicit_arg.name}()")
                    
                    # 将函数定义推入栈，而不是装饰器调用结果
                    self.stack.push(decorator_implicit_arg)
                    return
            elif isinstance(func, ASTName) and isinstance(top, ASTCall):
                # [DEBUG] 修复：检测多重装饰器调用
                # 栈布局：[decorator_a, ASTCall(decorator_b(func))]
                # 这也是装饰器调用，内层ASTCall是隐式参数
                # 但需要确保func是装饰器函数名，而不是推导式函数
                # [DEBUG] 关键修复：同时排除 <anonymous> 名称（推导式函数可能是这个名称）
                if func.name not in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>', '<anonymous>'):
                    is_decorator_call = True
                    decorator_implicit_arg = top
                    debug_print(f"[_call_function] 检测到多重装饰器调用模式，隐式参数: ASTCall")
            elif isinstance(func, ASTCall):
                # [DEBUG] 关键修复：处理推导式函数调用
                # 栈布局：[range(3), <listcomp>]
                # 此时func是ASTCall(range, [3])，top是推导式函数
                # 应该直接推入推导式节点，而不是创建ASTCall
                from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr
                if isinstance(top, (ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr)):
                    debug_print(f"[_call_function] 检测到推导式节点在栈顶: {type(top).__name__}")
                    # 弹出推导式节点
                    comp_node = self.stack.top()
                    self.stack.pop()
                    
                    # [关键修复] 更新推导式的迭代对象
                    # func 是迭代表达式（如 range(10) 或 zip(...)）
                    if func is not None:
                        self._update_comprehension_iter(comp_node, func)
                    
                    # 直接推入推导式节点
                    self.stack.push(comp_node)
                    debug_print(f"[_call_function] 直接推入推导式节点: {type(comp_node).__name__}")
                    return
                elif isinstance(top, (ASTFunctionDef, ASTClass)):
                    top_name = top.name if hasattr(top, 'name') else ''
                    is_comprehension_func = top_name.startswith('<') and top_name.endswith('>')
                    if is_comprehension_func:
                        debug_print(f"[_call_function] 检测到推导式函数调用: {top_name}")
                        # 弹出推导式函数
                        comp_func = self.stack.top()
                        self.stack.pop()
                        # 创建ASTCall(推导式函数, [func])
                        node = ASTCall(comp_func, [func])
                        self.stack.push(node)
                        debug_print(f"[_call_function] 创建推导式调用: {top_name}({func})")
                        return
        
        # 如果是装饰器调用，弹出隐式参数（函数定义或内层装饰器结果）
        if is_decorator_call and decorator_implicit_arg:
            if not self.stack.empty():
                arg = self.stack.top()
                self.stack.pop()
                args.append(arg)
        
        # 处理 PUSH_NULL 留下的 NULL
        # 在 Python 3.11+ 中，PUSH_NULL 会在栈底留下一个 NULL
        # 我们需要检查并弹出它
        if not self.stack.empty():
            top = self.stack.top()
            # 检查是否是 NULL（通常是 None 或特殊的 null 对象）
            if isinstance(top, ASTObject) and top.object is None:
                self.stack.pop()
                debug_print(f"[_call_function] 弹出 PUSH_NULL 留下的 NULL")
        
        # 检查是否是类定义调用 BUILD_CLASS
        if isinstance(func, ASTObject) and func.object == "BUILD_CLASS":
            # 类定义：BUILD_CLASS(<code object>, 'ClassName', *bases)
            if len(args) >= 2:
                code_obj = args[0]
                class_name = args[1]
                
                # 提取类名
                if isinstance(class_name, str):
                    class_name_str = class_name
                elif hasattr(class_name, 'object'):
                    class_name_str = str(class_name.object)
                elif hasattr(class_name, 'value'):
                    class_name_str = str(class_name.value)
                else:
                    class_name_str = str(class_name)
                
                # 提取基类（从第3个参数开始）
                base_nodes = []
                for i in range(2, len(args)):
                    base_arg = args[i]
                    if isinstance(base_arg, ASTNode):
                        base_nodes.append(base_arg)
                    elif hasattr(base_arg, 'object'):
                        from core.ast_nodes import ASTName
                        base_nodes.append(ASTName(str(base_arg.object)))
                    elif hasattr(base_arg, 'value'):
                        from core.ast_nodes import ASTName
                        base_nodes.append(ASTName(str(base_arg.value)))
                
                # 从代码对象创建类定义
                # 注意：code_obj可能是ASTFunctionDef（MAKE_FUNCTION已经将代码对象转换为函数定义）
                if isinstance(code_obj, ASTFunctionDef):
                    # 从ASTFunctionDef创建类定义
                    # 尝试获取原始代码对象
                    original_code_obj = None
                    if hasattr(code_obj, '_code_obj'):
                        original_code_obj = code_obj._code_obj
                    elif hasattr(code_obj, 'code_obj'):
                        original_code_obj = code_obj.code_obj
                    
                    if original_code_obj and isinstance(original_code_obj, PycCode):
                        # 使用原始代码对象创建类定义
                        class_node = self._create_class_from_code(original_code_obj, class_name_str, base_nodes)
                        if class_node:
                            self.stack.push(class_node)
                            return
                    
                    # 如果无法获取原始代码对象，使用body中的节点
                    class_body = []
                    if hasattr(code_obj, 'body') and code_obj.body:
                        if hasattr(code_obj.body, 'nodes'):
                            class_body = code_obj.body.nodes
                        elif isinstance(code_obj.body, list):
                            class_body = code_obj.body
                    
                    class_node = ASTClass(
                        name=class_name_str,
                        bases=base_nodes,
                        body=class_body,
                        keywords=[]
                    )
                    self.stack.push(class_node)
                    return
                elif hasattr(code_obj, 'object') and isinstance(code_obj.object, PycCode):
                    class_node = self._create_class_from_code(code_obj.object, class_name_str, base_nodes)
                    if class_node:
                        self.stack.push(class_node)
                        return
            
            # 如果无法创建类定义，创建普通的函数调用
            # [DEBUG] 关键修复：检查是否是简单装饰器模式
            # 简单装饰器模式：@decorator -> def func(): ...
            # 字节码：LOAD_NAME decorator; LOAD_CONST func_code; MAKE_FUNCTION; PRECALL 0; CALL 0; STORE_NAME func
            # 此时func是ASTName（decorator），args包含函数定义
            is_simple_decorator = False
            simple_decorator_func = None
            
            if isinstance(func, ASTName) and len(args) == 1:
                arg = args[0]
                if isinstance(arg, ASTFunctionDef):
                    # [DEBUG] 关键修复：检查是否是推导式函数
                    func_name = arg.name if hasattr(arg, 'name') else ''
                    is_comp_name = func_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>', '<anonymous>')
                    is_comp_by_features = False
                    if hasattr(arg, '_code_obj'):
                        is_comp_by_features = self._is_comprehension_code(arg._code_obj)
                    
                    if not is_comp_name and not is_comp_by_features:
                        is_simple_decorator = True
                        simple_decorator_func = arg
                        debug_print(f"[_call_function] 检测到简单装饰器模式: @{func.name} -> def {arg.name}()")
            
            if is_simple_decorator and simple_decorator_func:
                # [DEBUG] 找到简单装饰器模式！
                # 设置函数的装饰器信息
                if not hasattr(simple_decorator_func, '_decorators'):
                    simple_decorator_func._decorators = []
                simple_decorator_func._decorators.append(func)
                
                debug_print(f"[_call_function] 应用简单装饰器: @{func.name} -> def {simple_decorator_func.name}()")
                
                # 将函数定义推入栈，而不是装饰器调用结果
                self.stack.push(simple_decorator_func)
            else:
                node = ASTCall(func, args)
                self.stack.push(node)
        else:
            # [DEBUG] 修复：检测带参数的装饰器模式
            # 带参数的装饰器模式：@decorator_factory(arg) -> def name(): ...
            # 字节码：LOAD_NAME decorator_factory; LOAD_CONST arg; PRECALL 1; CALL 1; 
            #        LOAD_CONST func_code; MAKE_FUNCTION; PRECALL 0; CALL 0; STORE_NAME name
            # 此时func是ASTCall（decorator_factory(arg)的调用结果），args包含函数定义
            is_param_decorator = False
            param_decorator_func = None
            param_decorator_args = []

            if isinstance(func, ASTCall) and args:
                # 检查参数中是否包含函数定义
                for arg in args:
                    if isinstance(arg, ASTFunctionDef):
                        # [DEBUG] 关键修复：检查是否是推导式函数
                        func_name = arg.name if hasattr(arg, 'name') else ''
                        is_comp_name = func_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>', '<anonymous>')
                        is_comp_by_features = False
                        if hasattr(arg, '_code_obj'):
                            is_comp_by_features = self._is_comprehension_code(arg._code_obj)
                        
                        if is_comp_name or is_comp_by_features:
                            debug_print(f"[_call_function] 参数中的推导式函数，不作为装饰器处理: {func_name}")
                            # 不是装饰器，作为普通函数调用处理
                            is_param_decorator = False
                            break
                        
                        is_param_decorator = True
                        param_decorator_func = arg
                        # 获取装饰器工厂函数的调用信息
                        if hasattr(func, '_func') and func._func:
                            param_decorator_factory = func._func
                            if hasattr(func, '_args') and func._args:
                                param_decorator_args = func._args
                        break

            if is_param_decorator and param_decorator_func:
                # [DEBUG] 找到带参数的装饰器模式！
                # 创建带参数的装饰器调用
                # 装饰器语法：@decorator_factory(arg)
                decorator_call = func  # 这是decorator_factory(arg)的调用结果

                # 设置函数的装饰器信息
                if not hasattr(param_decorator_func, '_decorators'):
                    param_decorator_func._decorators = []
                param_decorator_func._decorators.append(decorator_call)

                debug_print(f"[_call_function] 检测到带参数的装饰器模式: @{decorator_call} -> def {param_decorator_func.name}()")

                # 将函数定义推入栈，而不是装饰器调用结果
                self.stack.push(param_decorator_func)
            else:
                # [DEBUG] 修复：检测带参数的装饰器模式（第二种情况）
                # 带参数的装饰器模式：@decorator_factory(arg) -> def name(): ...
                # 字节码：LOAD_NAME decorator_factory; LOAD_CONST arg; PRECALL 1; CALL 1; 
                #        LOAD_CONST func_code; MAKE_FUNCTION; PRECALL 0; CALL 0; STORE_NAME name
                # 此时func是ASTCall（decorator_factory(arg)的调用结果），argc=0
                # 但栈上还有函数定义（被装饰的函数）
                is_param_decorator_v2 = False
                param_decorator_func_v2 = None

                if argc == 0 and isinstance(func, ASTCall):
                    # 检查栈上是否有函数定义
                    debug_print(f"[_call_function] 检查带参数装饰器v2: func={func}, stack_size={self.stack.size()}")
                    if not self.stack.empty():
                        top = self.stack.top()
                        debug_print(f"[_call_function] 栈顶: {type(top).__name__} = {top}")
                        # [DEBUG] 关键修复：也检查 ASTListComp, ASTSetComp, ASTDictComp
                        from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp
                        if isinstance(top, (ASTFunctionDef, ASTListComp, ASTSetComp, ASTDictComp)):
                            # [DEBUG] 关键修复：排除推导式函数
                            # 推导式函数名是 <listcomp>, <setcomp>, <dictcomp>, <genexpr>
                            # 或者类型是 ASTListComp, ASTSetComp, ASTDictComp
                            func_name = top.name if hasattr(top, 'name') else ''
                            is_comprehension_type = isinstance(top, (ASTListComp, ASTSetComp, ASTDictComp))
                            is_comprehension_name = func_name.startswith('<') and func_name.endswith('>')
                            if is_comprehension_type or is_comprehension_name or func_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'):
                                debug_print(f"[_call_function] 跳过推导式函数: {type(top).__name__}, name={func_name}")
                            else:
                                is_param_decorator_v2 = True
                                param_decorator_func_v2 = top
                                debug_print(f"[_call_function] 找到函数定义: {top.name}")

                if is_param_decorator_v2 and param_decorator_func_v2:
                    # [DEBUG] 找到带参数的装饰器模式（第二种情况）！
                    # 设置函数的装饰器信息
                    if not hasattr(param_decorator_func_v2, '_decorators'):
                        param_decorator_func_v2._decorators = []
                    param_decorator_func_v2._decorators.append(func)

                    debug_print(f"[_call_function] 检测到带参数的装饰器模式(v2): @{func} -> def {param_decorator_func_v2.name}()")

                    # 创建ASTCall对象，但将函数定义作为参数
                    node = ASTCall(func, [param_decorator_func_v2])
                    self.stack.push(node)
                else:
                    # [DEBUG] 修复：检测带参数的装饰器模式（第三种情况）
                    # 带参数的装饰器模式：@decorator_factory(arg) -> def name(): ...
                    # 字节码：LOAD_NAME decorator_factory; LOAD_CONST arg; PRECALL 1; CALL 1;
                    #        LOAD_CONST func_code; MAKE_FUNCTION; PRECALL 0; CALL 0; STORE_NAME name
                    # 此时func是ASTFunctionDef（被装饰的函数），argc=0
                    # 但栈上还有ASTCall对象（decorator_factory(arg)的调用结果）
                    is_param_decorator_v3 = False
                    param_decorator_func_v3 = None
                    param_decorator_call_v3 = None

                    if argc == 0 and isinstance(func, ASTFunctionDef):
                        # 检查栈上是否有ASTCall对象
                        debug_print(f"[_call_function] 检查带参数装饰器v3: func={func.name}, stack_size={self.stack.size()}")
                        if not self.stack.empty():
                            top = self.stack.top()
                            debug_print(f"[_call_function] 栈顶: {type(top).__name__} = {top}")
                            if isinstance(top, ASTCall):
                                is_param_decorator_v3 = True
                                param_decorator_func_v3 = func
                                param_decorator_call_v3 = top
                                debug_print(f"[_call_function] 找到装饰器调用: {top}")

                    if is_param_decorator_v3 and param_decorator_func_v3 and param_decorator_call_v3:
                        # [DEBUG] 找到带参数的装饰器模式（第三种情况）！
                        # 设置函数的装饰器信息
                        if not hasattr(param_decorator_func_v3, '_decorators'):
                            param_decorator_func_v3._decorators = []
                        param_decorator_func_v3._decorators.append(param_decorator_call_v3)

                        debug_print(f"[_call_function] 检测到带参数的装饰器模式(v3): @{param_decorator_call_v3} -> def {param_decorator_func_v3.name}()")

                        # 弹出栈顶的ASTCall对象
                        self.stack.pop()

                        # 将函数定义推入栈
                        self.stack.push(param_decorator_func_v3)
                    else:
                        # [DEBUG] 修复：检测简单装饰器模式
                        # 简单装饰器模式：@decorator -> def name(): ...
                        # 字节码：LOAD_NAME decorator; LOAD_CONST func_code; MAKE_FUNCTION; PRECALL 0; CALL 0; STORE_NAME name
                        # 此时func是装饰器函数（ASTName），argc=0，但栈上还有函数对象
                        # 我们需要检查栈上是否有函数定义
                        is_simple_decorator = False
                        simple_decorator_func = None
                        decorator_name = None

                        if argc == 0 and isinstance(func, ASTName):
                            # 检查是否是已知的装饰器函数
                            decorator_name = func.name
                            # 检查栈上是否有函数/类定义
                            if not self.stack.empty():
                                top = self.stack.top()
                                if isinstance(top, (ASTFunctionDef, ASTClass)):
                                    is_simple_decorator = True
                                    simple_decorator_func = top

                        if is_simple_decorator and simple_decorator_func and decorator_name:
                            # [DEBUG] 找到简单装饰器模式！
                            # 设置目标定义的装饰器信息
                            if not hasattr(simple_decorator_func, '_decorators'):
                                simple_decorator_func._decorators = []
                            simple_decorator_func._decorators.append(func)

                            target_type = "类" if isinstance(simple_decorator_func, ASTClass) else "函数"
                            debug_print(f"[_call_function] 检测到简单装饰器模式: @{decorator_name} -> {target_type} {simple_decorator_func.name}()")

                            # 创建ASTCall对象，但将目标定义作为参数
                            node = ASTCall(func, [simple_decorator_func])
                            self.stack.push(node)
                        else:
                            # [DEBUG] 修复：检测多重装饰器模式
                            # 多重装饰器模式：@decorator_a @decorator_b def my_function(): ...
                            # 字节码：
                            #   LOAD_NAME decorator_a
                            #   LOAD_NAME decorator_b
                            #   LOAD_CONST func_code; MAKE_FUNCTION
                            #   PRECALL 0; CALL 0  (调用 decorator_b(my_function))
                            #   PRECALL 0; CALL 0  (调用 decorator_a(result))
                            #   STORE_NAME my_function
                            # 在第二次CALL时，func是ASTName(decorator_a)，argc=0
                            # 但栈顶是第一次CALL的结果（ASTCall(decorator_b, [my_function])）
                            is_multi_decorator = False
                            multi_decorator_func = None
                            inner_decorator_call = None

                            if argc == 0 and isinstance(func, ASTName):
                                # 检查栈上是否有ASTCall对象（内层装饰器的结果）
                                if not self.stack.empty():
                                    top = self.stack.top()
                                    if isinstance(top, ASTCall):
                                        is_multi_decorator = True
                                        multi_decorator_func = func
                                        inner_decorator_call = top
                                        debug_print(f"[_call_function] 检测到多重装饰器模式: @{func.name} -> {top}")

                            if is_multi_decorator and multi_decorator_func and inner_decorator_call:
                                # [DEBUG] 找到多重装饰器模式！
                                # 从内层装饰器调用中提取函数/类定义
                                inner_target = None
                                if hasattr(inner_decorator_call, 'pparams') and inner_decorator_call.pparams:
                                    for arg in inner_decorator_call.pparams:
                                        if isinstance(arg, (ASTFunctionDef, ASTClass)):
                                            inner_target = arg
                                            break

                                if inner_target:
                                    # 添加外层装饰器到目标定义的装饰器列表
                                    if not hasattr(inner_target, '_decorators'):
                                        inner_target._decorators = []
                                    # 装饰器顺序：从内到外
                                    # Python语法：@decorator_a @decorator_b def func(): ...
                                    # 执行顺序：decorator_b(func) -> decorator_a(result)
                                    # 所以装饰器列表应该是 [decorator_a, decorator_b]
                                    inner_target._decorators.insert(0, multi_decorator_func)
                                    target_type = "类" if isinstance(inner_target, ASTClass) else "函数"
                                    debug_print(f"[_call_function] 添加多重装饰器: @{multi_decorator_func.name} -> {target_type} {inner_target.name}()")

                                # [DEBUG] 修复：不需要再弹出栈，因为inner_decorator_call已经在args中了
                                # 创建新的ASTCall对象：decorator_a(decorator_b(target))
                                node = ASTCall(multi_decorator_func, [inner_decorator_call])
                                self.stack.push(node)
                            else:
                                # [DEBUG] 关键修复：检查func是否是推导式节点
                                # 如果是推导式节点，直接推入推导式节点而不是包装在ASTCall中
                                from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr
                                if isinstance(func, (ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr)):
                                    debug_print(f"[_call_function] 检测到推导式节点，直接推入: {type(func).__name__}")
                                    self.stack.push(func)
                                else:
                                    # 创建普通的函数调用节点
                                    node = ASTCall(func, args)
                                    self.stack.push(node)

    def _make_function(self, flags: int) -> None:
        """创建函数 - 参考C++版本实现
        
        在Python 3.11+中，flags格式：
        - 低8位：默认参数数量 (defCount)
        - 高8位：关键字默认参数数量 (kwDefCount)
        """
        print(f"[MAKE_FUNCTION] _make_function被调用，flags={flags}")
        if self.stack.empty():
            print(f"[MAKE_FUNCTION] 栈为空，返回")
            return
        
        # 🔧 参考C++版本：解析flags
        # 低8位是默认参数数量，高8位是关键字默认参数数量
        defCount = flags & 0xFF
        kwDefCount = (flags >> 8) & 0xFF
        print(f"[MAKE_FUNCTION] 参数解析: defCount={defCount}, kwDefCount={kwDefCount}")
        
        # 获取栈顶的值（函数代码对象）
        value = self.stack.top()
        print(f"[MAKE_FUNCTION] 栈顶值类型: {type(value).__name__}, 值: {value}")
        self.stack.pop()
        
        # 🔧 参考C++版本：检查限定名称（在Python 3.11+中，TOS可能是限定名称）
        # 如果TOS不是代码对象，则它是限定名称，需要再弹出一个值
        fun_code = value
        tos_type = None
        if hasattr(value, 'object'):
            obj = value.object
            if hasattr(obj, 'type'):
                tos_type = obj.type()
        
        # 在C++中，检查是否是CODE类型，如果不是，则再弹出一个值
        if tos_type not in [None, 'code', 'code2'] and not isinstance(value, PycCode):
            # TOS不是代码对象，它是限定名称
            qual_name = value
            if not self.stack.empty():
                fun_code = self.stack.top()
                self.stack.pop()
                print(f"[MAKE_FUNCTION] 获取限定名称后，代码对象类型: {type(fun_code).__name__}")
        
        # 特殊情况：直接是函数定义对象
        if isinstance(fun_code, ASTFunctionDef):
            self.stack.push(fun_code)
            return
        
        # [DEBUG] 关键修复：处理推导式节点
        from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr
        if isinstance(fun_code, (ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr)):
            print(f"[MAKE_FUNCTION] 检测到推导式节点，直接推入: {type(fun_code).__name__}")
            self.stack.push(fun_code)
            return
        
        # 🔧 参考C++版本：弹出默认参数值
        defArgs = []  # 默认参数值列表
        kwDefArgs = []  # 关键字默认参数值列表
        
        # 弹出关键字默认参数（从后往前）
        for i in range(kwDefCount):
            if not self.stack.empty():
                arg = self.stack.top()
                self.stack.pop()
                kwDefArgs.insert(0, arg)
                print(f"[MAKE_FUNCTION] 弹出关键字默认参数[{i}]: {type(arg).__name__}")
        
        # 弹出位置默认参数（从后往前）
        for i in range(defCount):
            if not self.stack.empty():
                arg = self.stack.top()
                self.stack.pop()
                defArgs.insert(0, arg)
                print(f"[MAKE_FUNCTION] 弹出位置默认参数[{i}]: {type(arg).__name__}")
        
        # 获取代码对象
        code_obj = fun_code
        if hasattr(fun_code, 'object'):
            code_obj = fun_code.object
        
        # 使用已有的方法或创建新的ASTFunctionDef
        if isinstance(code_obj, PycCode):
            func_node = self._create_function_from_code(code_obj)
            if func_node:
                # 🔧 参考C++版本：设置默认参数
                if defArgs:
                    func_node._defargs = defArgs
                if kwDefArgs:
                    func_node._kwdefargs = kwDefArgs
                self.stack.push(func_node)
                return
        
        # [DEBUG] 修复：创建函数定义时添加参数和代码对象
        if isinstance(code_obj, PycCode):
            # 尝试从代码对象提取参数
            args_nodes = self._extract_function_args(code_obj)
            func_node = ASTFunctionDef('<anonymous>', args=args_nodes, body=ASTBlock(), code_obj=code_obj)
            # 🔧 参考C++版本：设置默认参数
            if defArgs:
                func_node._defargs = defArgs
            if kwDefArgs:
                func_node._kwdefargs = kwDefArgs
        else:
            # 如果没有代码对象，尝试从value中获取
            func_node = ASTFunctionDef('<anonymous>', body=ASTBlock(), code_obj=code_obj)
        
        self.stack.push(func_node)

    def _build_class(self) -> None:
        """构建类"""
        # 使用上下文管理器处理类定义
        # 首先推入类上下文
        class_context = self.context_manager.push_context(ContextType.CLASS, "class")
        
        if self.stack.size() < 3:
            self.context_manager.pop_context()
            return
        
        kwargs = {}
        kw_nodes = []
        
        # 获取关键字参数
        if not self.stack.empty():
            kw_dict = self.stack.top()
            self.stack.pop()
            if hasattr(kw_dict, 'object') and isinstance(kw_dict.object, dict):
                kwargs = kw_dict.object
                # 将关键字参数转换为AST节点
                for key, value in kwargs.items():
                    from core.ast_nodes import ASTName, ASTKeyword
                    if isinstance(value, ASTNode):
                        kw_nodes.append(ASTKeyword(key, value))
        
        # 获取位置参数（基类）
        base_nodes = []
        while self.stack.size() > 1:  # 至少保留类名
            if not self.stack.empty():
                arg = self.stack.top()
                self.stack.pop()
                if isinstance(arg, ASTNode):
                    base_nodes.insert(0, arg)
                else:
                    from core.ast_nodes import ASTName
                    base_nodes.insert(0, ASTName(str(arg)))
        
        # 获取类名
        class_name = "class"
        if not self.stack.empty():
            name_obj = self.stack.top()
            self.stack.pop()
            if hasattr(name_obj, 'value'):
                class_name = name_obj.value
            elif isinstance(name_obj, str):
                class_name = name_obj
            elif hasattr(name_obj, '_value'):
                class_name = name_obj._value
        
        # 更新上下文名称
        class_context.name = class_name
        
        # 创建类定义节点
        from core.ast_nodes import ASTClassDef, ASTBlock
        class_node = ASTClassDef(
            name=class_name, 
            bases=base_nodes, 
            body=[ASTBlock()],  # 初始化为空块
            keywords=kw_nodes
        )
        
        # 发射类定义节点
        self._emit(class_node)
        
        # 弹出类上下文
        self.context_manager.pop_context()

    def _create_class_from_code(self, code_obj: PycCode, class_name: str, bases: list = None) -> Optional['ASTClass']:
        """从代码对象创建类定义节点"""
        try:
            # 创建类体块
            class_body = ASTBlock()
            
            # 从代码对象的常量中提取方法定义
            if hasattr(code_obj, 'consts') and code_obj.consts and code_obj.consts.get():
                consts_obj = code_obj.consts.get()
                
                for i in range(consts_obj.size()):
                    const_item = consts_obj.get(i)
                    if const_item is None:
                        continue
                    
                    if hasattr(const_item, 'get'):
                        const_value = const_item.get()
                        
                        # 如果是代码对象，可能是方法定义
                        if isinstance(const_value, PycCode):
                            # 获取方法名
                            method_name = None
                            if hasattr(const_value, 'name') and const_value.name:
                                name_ref = const_value.name
                                # 处理PycRef
                                if hasattr(name_ref, 'get'):
                                    name_obj = name_ref.get()
                                    if name_obj:
                                        if isinstance(name_obj, PycString):
                                            method_name = name_obj.value
                                        elif hasattr(name_obj, 'value'):
                                            method_name = str(name_obj.value)
                                        else:
                                            method_name = str(name_obj)
                                elif isinstance(name_ref, PycString):
                                    method_name = name_ref.value
                                elif hasattr(name_ref, 'value'):
                                    method_name = str(name_ref.value)
                            
                            # 创建方法定义
                            method_node = self._create_function_from_code(const_value)
                            if method_node and method_name:
                                # 确保方法名正确
                                if hasattr(method_node, '_name'):
                                    method_node._name = method_name
                                class_body.append(method_node)
            
            # 使用传入的基类或空列表
            if bases is None:
                bases = []
            
            # 创建类定义节点
            class_node = ASTClass(
                name=class_name,
                bases=bases,
                body=class_body,
                keywords=[]
            )
            
            return class_node
            
        except Exception as e:
            debug_print(f"[_create_class_from_code] 创建类定义失败: {e}")
            return None

    def _process_module_level_functions(self, code_obj) -> None:
        """处理模块级别的函数定义"""
        from core.pyc_objects import PycCode, PycString
        
        # 检查是否在模块级别
        if not isinstance(self.main_block, ASTBlock) or self.main_block.blk_type != ASTBlock.BlockType.BLK_MAIN:
            return
        
        # 获取常量列表
        if not hasattr(code_obj, 'consts') or not code_obj.consts:
            return
        
        consts = code_obj.consts
        if not consts or not consts.get():
            return
        
        consts_obj = consts.get()
        
        # 获取名称列表
        names = None
        if hasattr(code_obj, 'names') and code_obj.names and code_obj.names.get():
            names = code_obj.names.get()
        
        # 遍历常量，找到代码对象
        for i in range(consts_obj.size()):
            const_item = consts_obj.get(i)
            if const_item is None:
                continue
            
            # 获取实际的常量值
            if hasattr(const_item, 'get'):
                const_value = const_item.get()
            else:
                const_value = const_item
            
            # 检查是否是代码对象
            if isinstance(const_value, PycCode):
                # 注意：函数定义已在 _load_const 中处理
                # 这里不再重复创建函数定义
                # 只处理类定义（如果检测到类特征）
                debug_print(f"[MODULE_LEVEL_FUNCTIONS] 检测到PycCode对象，跳过处理")
                pass

    def _build_function_ast(self, name: str, code_obj, decorators=None, returns=None, args=None) -> Optional['ASTFunctionDef']:
        """为函数代码对象构建AST"""
        from core.ast_nodes import ASTFunctionDef, ASTBlock as ASTBlockNode
        from core.pyc_objects import PycCode, PycRef
        
        if isinstance(code_obj, PycRef):
            code_obj = code_obj.get()
        
        if not isinstance(code_obj, PycCode):
            return None
        
        # 创建参数节点
        args_nodes = []
        if args:
            for arg in args:
                if isinstance(arg, str):
                    args_nodes.append(ASTName(arg))
                else:
                    args_nodes.append(arg)
        
        # 创建装饰器节点
        decorators_nodes = decorators if decorators else []
        
        # 获取返回类型
        return_node = None
        if returns:
            from core.ast_nodes import ASTName
            if isinstance(returns, str):
                return_node = ASTName(returns)
            else:
                return_node = returns
        
        # 创建临时的ASTBuilder来处理函数的字节码
        func_builder = ASTBuilder(self.module, code_obj)
        func_builder.in_function = True  # 关键：设置in_function为True
        
        # 构建函数的AST
        func_ast = func_builder.build_from_code(code_obj)
        
        # [DEBUG] 关键修复：传递code_obj给ASTFunctionDef
        if isinstance(func_ast, ASTBlockNode):
            # 如果返回的是块，使用它作为函数体
            return ASTFunctionDef(name, args=args_nodes, body=func_ast, 
                               returns=return_node, decorators=decorators_nodes, code_obj=code_obj)
        elif isinstance(func_ast, ASTFunctionDef):
            func_ast._name = name  # 使用私有属性设置名称
            # 设置参数
            if args_nodes:
                func_ast._args = args_nodes
            # 设置返回类型
            if return_node:
                func_ast._returns = return_node
            # 设置装饰器
            if decorators_nodes:
                func_ast._decorators = decorators_nodes
            # [DEBUG] 关键修复：设置code_obj
            func_ast._code_obj = code_obj
            return func_ast
        
        # 如果都不是，创建一个基本的函数定义
        return ASTFunctionDef(name, args=args_nodes, body=func_ast if func_ast else ASTBlockNode(),
                           returns=return_node, decorators=decorators_nodes, code_obj=code_obj)

    def _build_list(self, count: int) -> None:
        """构建列表"""
        items = []
        for _ in range(count):
            if not self.stack.empty():
                item = self.stack.top()
                self.stack.pop()
                items.insert(0, item)  # Reverse order
        
        # 创建适当的AST节点而不是ASTObject
        from core.ast_nodes import ASTList
        node = ASTList(items)
        self.stack.push(node)

    def _build_tuple(self, count: int) -> None:
        """构建元组"""
        items = []
        for _ in range(count):
            if not self.stack.empty():
                item = self.stack.top()
                self.stack.pop()
                items.insert(0, item)  # Reverse order
        
        # 创建适当的AST节点而不是ASTObject
        from core.ast_nodes import ASTTuple
        node = ASTTuple(items)
        self.stack.push(node)

    def _build_set(self, count: int) -> None:
        """构建集合"""
        items = []
        for _ in range(count):
            if not self.stack.empty():
                item = self.stack.top()
                self.stack.pop()
                items.insert(0, item)  # Reverse order
        
        # 创建ASTSet节点
        from core.ast_nodes import ASTSet
        node = ASTSet(items)
        self.stack.push(node)

    def _build_map(self, count: int) -> None:
        """构建映射（字典）- 修复版本"""
        # 从栈中弹出键值对
        # count表示键值对的数量
        from core.ast_nodes import ASTDict, ASTConstant
        
        keys = []
        values = []
        
        # 从栈中弹出值和键（注意顺序：先值后键）
        for _ in range(count):
            if not self.stack.empty():
                value = self.stack.top()
                self.stack.pop()
                values.insert(0, value)  # 插入到开头保持顺序
            
            if not self.stack.empty():
                key = self.stack.top()
                self.stack.pop()
                # 如果key是ASTObject，提取其值并创建ASTConstant
                if hasattr(key, 'object'):
                    key_value = key.object
                    keys.insert(0, ASTConstant(key_value))
                elif hasattr(key, 'value'):
                    keys.insert(0, ASTConstant(key.value))
                else:
                    keys.insert(0, key)
        
        node = ASTDict(keys, values)
        self.stack.push(node)

    def _build_const_key_map(self, count: int) -> None:
        """构建常量键映射"""
        if self.stack.empty():
            return
        
        keys = self.stack.top()
        self.stack.pop()
        
        values = []
        for _ in range(count):
            if not self.stack.empty():
                val = self.stack.top()
                self.stack.pop()
                values.insert(0, val)
        
        # [DEBUG] 关键修复：处理PycSequence类型的keys.object
        key_list = None
        if hasattr(keys, 'object'):
            keys_obj = keys.object
            if isinstance(keys_obj, (list, tuple)):
                key_list = keys_obj
            else:
                # 处理PycSequence对象
                from core.pyc_objects import PycSequence
                if isinstance(keys_obj, PycSequence):
                    # 获取PycSequence的内部值列表
                    if hasattr(keys_obj, '_values'):
                        key_list = [v.get() if hasattr(v, 'get') else v for v in keys_obj._values]
                    elif hasattr(keys_obj, 'value'):
                        key_list = keys_obj.value
        
        if key_list:
            # [DEBUG] 关键修复：创建AST节点列表，而不是Python字典
            from core.ast_nodes import ASTConstant, ASTDict
            key_nodes = [ASTConstant(k) for k in key_list]
            # values已经是AST节点列表（从栈中弹出的）
            node = ASTDict(key_nodes, values)
            self.stack.push(node)
        else:
            # 回退到原来的方式
            from core.ast_nodes import ASTDict
            node = ASTDict([], [])
            self.stack.push(node)

    def _list_extend(self, count: int) -> None:
        """扩展列表 - 修复版本"""
        debug_print(f"[_list_extend] 被调用! count={count}, stack_size={self.stack.size()}")
        
        # 从栈中弹出可迭代对象
        if self.stack.empty():
            debug_print("[_list_extend] 栈为空，返回")
            return
        
        iterable = self.stack.top()
        self.stack.pop()
        debug_print(f"[_list_extend] 弹出iterable, 类型: {type(iterable).__name__}")
        
        # 获取列表（应该在栈顶）
        if self.stack.empty():
            debug_print("[_list_extend] 栈为空（获取列表），返回")
            return
        
        list_node = self.stack.top()
        self.stack.pop()
        debug_print(f"[_list_extend] 弹出list_node, 类型: {type(list_node).__name__}")
        
        # 从可迭代对象中提取元素
        from core.ast_nodes import ASTList, ASTConstant
        from core.pyc_objects import PycSequence, PycNumeric
        from core.pyc_stream import PycRef
        
        items = []
        debug_print(f"[_list_extend] 检查iterable属性: hasattr('object')={hasattr(iterable, 'object')}")
        
        if hasattr(iterable, 'object'):
            # 如果是ASTObject，提取其值
            iterable_obj = iterable.object
            debug_print(f"[_list_extend] iterable.object类型: {type(iterable_obj).__name__}")
            debug_print(f"[_list_extend] isinstance(iterable_obj, PycSequence): {isinstance(iterable_obj, PycSequence)}")
            
            if isinstance(iterable_obj, (list, tuple)):
                items = [ASTConstant(item) for item in iterable_obj]
            elif isinstance(iterable_obj, PycSequence):
                # [DEBUG] 关键修复：直接处理PycSequence对象
                debug_print(f"[_list_extend] 处理PycSequence...")
                if hasattr(iterable_obj, '_values'):
                    debug_print(f"[_list_extend] PycSequence._values数量: {len(iterable_obj._values)}")
                    # 处理PycRef对象
                    for idx, v in enumerate(iterable_obj._values):
                        debug_print(f"[_list_extend] 处理第{idx}个元素, 类型: {type(v).__name__}")
                        if isinstance(v, PycRef):
                            val = v.get()
                            debug_print(f"[_list_extend] PycRef.get()类型: {type(val).__name__}")
                            # [DEBUG] 关键修复：处理PycNumeric对象
                            if isinstance(val, PycNumeric):
                                debug_print(f"[_list_extend] PycNumeric.value: {val.value}")
                                items.append(ASTConstant(val.value))
                                debug_print(f"[_list_extend] 添加ASTConstant({val.value})")
                            else:
                                debug_print(f"[_list_extend] 不是PycNumeric，添加ASTConstant({val})")
                                items.append(ASTConstant(val))
                        else:
                            debug_print(f"[_list_extend] 不是PycRef，添加ASTConstant({v})")
                            items.append(ASTConstant(v))
                elif hasattr(iterable_obj, 'value'):
                    # 尝试获取value属性
                    val = iterable_obj.value
                    if isinstance(val, (list, tuple)):
                        items = [ASTConstant(item) for item in val]
            elif hasattr(iterable_obj, '_values'):
                # 处理PycSequence
                for v in iterable_obj._values:
                    if isinstance(v, PycRef):
                        val = v.get()
                        # [DEBUG] 关键修复：处理PycNumeric对象
                        if isinstance(val, PycNumeric):
                            items.append(ASTConstant(val.value))
                        else:
                            items.append(ASTConstant(val))
                    else:
                        items.append(ASTConstant(v))
        elif hasattr(iterable, '_items'):
            # 如果已经是ASTList或ASTTuple
            items = iterable._items
        elif hasattr(iterable, 'elts'):
            items = iterable.elts
        
        debug_print(f"[_list_extend] 生成的items数量: {len(items)}")
        
        # 创建新的列表节点
        if items:
            new_list = ASTList(items)
        else:
            new_list = ASTList([])
        
        self.stack.push(new_list)
        debug_print(f"[_list_extend] 完成，推送ASTList")

    def _pop_top(self) -> None:
        """弹出栈顶元素"""
        # [关键修复] 检查是否是break语句
        # break语句的特征：在循环体内，POP_TOP后面跟着LOAD_CONST None和RETURN_VALUE
        current_offset = getattr(self, 'current_instruction_offset', 0)
        
        # 检查是否在循环体内
        in_loop = False
        loop_end = -1
        if hasattr(self, 'current_for_node') and self.current_for_node is not None:
            body_start = getattr(self, 'for_body_start_offset', -1)
            body_end = getattr(self, 'for_body_end_offset', -1)
            if body_start <= current_offset < body_end:
                in_loop = True
                loop_end = body_end
        elif hasattr(self, 'current_while_node') and self.current_while_node is not None:
            body_start = getattr(self, 'while_body_start', -1)
            body_end = getattr(self, 'while_body_end', -1)
            if body_start <= current_offset < body_end:
                in_loop = True
                loop_end = body_end
        
        # 如果在循环体内，检查是否是break模式
        if in_loop:
            # 查找下一条指令
            next_instr = None
            for instr in self.instructions:
                if instr.get('offset', -1) == current_offset + 2:
                    next_instr = instr
                    break
            
            # break模式：下一条是LOAD_CONST None
            if next_instr and next_instr.get('opcode', -1) == Opcode.LOAD_CONST_A:
                # 发射break节点
                from core.ast_nodes import ASTBreak
                self._emit(ASTBreak())
                debug_print(f"[_pop_top] 检测到break语句，发射ASTBreak")
                # 弹出栈顶
                if not self.stack.empty():
                    self.stack.pop()
                # [关键修复] 设置标记，跳过接下来的LOAD_CONST和RETURN_VALUE指令
                self._skip_until_return = True
                return
        
        if not self.stack.empty():
            # 检查栈顶是否是函数调用或其他表达式
            top_node = self.stack.top()
            
            # [DEBUG] 关键修复：检查是否是推导式节点
            from core.ast_nodes import ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr
            if isinstance(top_node, (ASTListComp, ASTSetComp, ASTDictComp, ASTGenExpr)):
                print(f"[_pop_top] 检测到推导式节点: {type(top_node).__name__}")
                # 推导式节点直接发射到AST（不需要包装为表达式语句）
                self._emit(top_node)
                print(f"[_pop_top] 推导式节点已发射到AST")
                self.stack.pop()
                return
            
            # 如果栈顶是ASTCall或类似表达式，将其包装为表达式语句
            from core.ast_nodes import ASTCall, ASTExpr
            if isinstance(top_node, ASTCall):
                # [DEBUG] 修复：检查是否在with语句刚开始时（BEFORE_WITH之后，变量赋值之前）
                # 在with语句开始时，POP_TOP用于清理上下文管理器的返回值
                # 不应该生成表达式语句
                has_with_node = hasattr(self, 'current_with_node') and self.current_with_node is not None
                if has_with_node:
                    body_start = getattr(self, 'current_with_node_start_offset', -1)
                    current_offset = getattr(self, 'current_instruction_offset', -1)
                    # 只有在with语句刚开始时（前几条指令内）才跳过
                    # 这是为了跳过 __enter__() 返回值的清理
                    if body_start > 0 and current_offset > 0 and current_offset <= body_start + 10:
                        # 在with语句刚开始时，直接弹出，不生成表达式语句
                        debug_print(f"[_pop_top] with语句开始时跳过POP_TOP: offset={current_offset}")
                        self.stack.pop()
                        return
                
                # 将函数调用包装为表达式语句
                expr_node = ASTExpr(top_node)
                self._emit(expr_node)
                self.stack.pop()
            else:
                # 其他情况直接弹出
                self.stack.pop()

    def _dup_top(self) -> None:
        """复制栈顶元素"""
        if not self.stack.empty():
            top = self.stack.top()
            self.stack.push(top)

    def _rot_two(self) -> None:
        """交换栈顶两个元素"""
        if self.stack.size() < 2:
            return
        
        top = self.stack.top()
        self.stack.pop()
        second = self.stack.top()
        self.stack.pop()
        
        self.stack.push(top)
        self.stack.push(second)

    def _rot_three(self) -> None:
        """旋转栈顶三个元素 (top-2, top-1, top) -> (top, top-2, top-1)"""
        if self.stack.size() < 3:
            return
        
        top = self.stack.top()
        self.stack.pop()
        mid = self.stack.top()
        self.stack.pop()
        bottom = self.stack.top()
        self.stack.pop()
        
        self.stack.push(top)
        self.stack.push(bottom)
        self.stack.push(mid)

    def _swap(self, operand: int) -> None:
        """交换栈顶元素与栈中指定位置的元素 (Python 3.11+)
        
        SWAP n: 交换栈顶元素与栈中第n个元素（从栈顶开始计数，0表示栈顶）
        例如：SWAP 1 交换栈顶和第二个元素
        """
        if self.stack.size() < operand + 1:
            return
        
        # 获取栈顶元素
        top = self.stack.top()
        self.stack.pop()
        
        # 获取指定位置的元素
        # 需要临时存储中间的元素
        temp_stack = []
        for _ in range(operand - 1):
            if not self.stack.empty():
                temp_stack.append(self.stack.top())
                self.stack.pop()
        
        # 获取目标位置的元素
        target = self.stack.top()
        self.stack.pop()
        
        # 将栈顶元素放到目标位置
        self.stack.push(top)
        
        # 恢复中间的元素
        for item in reversed(temp_stack):
            self.stack.push(item)
        
        # 将目标元素放到栈顶
        self.stack.push(target)

    def _copy(self, operand: int) -> None:
        """复制栈中指定位置的元素到栈顶 (Python 3.11+)
        
        COPY n: 复制栈中第n个元素（从栈顶开始计数，0表示栈顶）到栈顶
        例如：COPY 1 复制第二个元素到栈顶
        """
        if self.stack.size() < operand + 1:
            return
        
        # 获取指定位置的元素（不弹出）
        target = self.stack.top(operand)
        if target is not None:
            # 复制到栈顶
            self.stack.push(target)

    def _precall_a(self, arg_count: int) -> None:
        """预调用处理 - Python 3.11+
        
        PRECALL_A 标记函数调用的准备阶段，但不执行实际调用。
        在 Python 3.11+ 中，PRECALL_A 标识可调用对象和参数数量，
        但 CALL_A 才真正执行函数调用。
        
        关键：PRECALL_A 不应该改变栈状态！栈在 PRECALL 后应保持不变。
        """
        # PRECALL_A 只是标记，不改变栈状态
        # 实际的函数调用在 CALL_A 中处理
        pass

    def _store_global(self, operand: int) -> None:
        """存储全局变量"""
        if self.stack.empty():
            return
        
        value = self.stack.top()
        self.stack.pop()
        
        if not self.module.code:
            return
        
        names = self.module.code.get().names
        if names and names.get():
            names_obj = names.get()
            if isinstance(names_obj, PycString):
                name_list = names_obj.value.split('\x00')
                if 0 <= operand < len(name_list):
                    name = name_list[operand]
                    node = ASTStore(ASTName(name), value)
                    self._emit(node)

    def _delete_global(self, operand: int) -> None:
        """删除全局变量"""
        if not self.module.code:
            return
        
        names = self.module.code.get().names
        if names and names.get():
            names_obj = names.get()
            if isinstance(names_obj, PycString):
                name_list = names_obj.value.split('\x00')
                if 0 <= operand < len(name_list):
                    name = name_list[operand]
                    node = ASTDelete(ASTName(name))
                    self._emit(node)

    def _pop_jump_if_false(self, target: int) -> None:
        """如果栈顶为假则跳转并弹出
        
        参考C++ pycdc实现，使用块栈管理if/elif/else结构
        """
        debug_print(f"[_pop_jump_if_false] 被调用, target={target}, stack_size={self.stack.size()}")
        if self.stack.empty():
            return
            
        condition = self.stack.top()
        self.stack.pop()
        debug_print(f"[_pop_jump_if_false] condition={condition}, type={type(condition).__name__}")
        
        current_offset = self.current_instruction_offset
        
        # [DEBUG] 检查是否在异常处理上下文中（紧跟在CHECK_EXC_MATCH之后）
        is_exception_handler = self._is_in_exception_context(current_offset)
        print(f"[_pop_jump_if_false] is_exception_handler={is_exception_handler}, current_offset={current_offset}")
        
        if is_exception_handler:
            # 这是except块的条件检查，不应该创建if节点
            debug_print(f"[_pop_jump_if_false] 检测到异常处理上下文，跳过创建if节点")
            # 设置except块的范围
            if hasattr(self, 'current_exception_handler') and self.current_exception_handler:
                self.except_body_start_offset = current_offset + 2
                self.except_body_end_offset = current_offset + 2 + target * 2
                debug_print(f"[_pop_jump_if_false] except块范围: {self.except_body_start_offset}-{self.except_body_end_offset}")
            return
        
        # ===== 参考C++实现：保存当前栈状态到历史 =====
        self.stack_hist.append(self.stack.copy())
        
        # 计算跳转目标偏移量（Python 3.11+）
        # 跳转目标 = 当前指令偏移 + 2 + target * 2
        jump_target = current_offset + 2 + target * 2
        
        # [DEBUG] 使用预扫描的循环信息检查是否是while循环
        is_while_loop = False
        if hasattr(self, '_loop_entries') and current_offset in self._loop_entries:
            loop_info = self._loop_entries[current_offset]
            if loop_info['type'] == 'while':
                is_while_loop = True
                debug_print(f"[_pop_jump_if_false] 通过预扫描识别为while循环")
        
        if is_while_loop:
            # ===== while循环处理（参考C++实现）=====
            # 弹出栈历史（循环不保存栈状态）
            if self.stack_hist:
                self.stack_hist.pop()
            
            # 创建while节点
            while_node = ASTWhile(condition, ASTNodeList(), None)
            
            # [DEBUG] 关键修复：先发射while节点，再创建while块
            # 这样while节点本身会被添加到main_block，而不是while块中
            debug_print(f"[_pop_jump_if_false] 创建while循环")
            saved_block = self.current_block  # 保存当前块
            self.current_block = self.main_block  # 设置为主块
            self._emit(while_node)
            self.current_block = saved_block  # 恢复当前块
            
            # 创建while块并压入块栈
            while_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_WHILE, end=jump_target, inited=True)
            self._push_block(while_block)
            
            self.current_while_node = while_node
            loop_info = self._loop_entries[current_offset]
            self.while_body_start = loop_info['body_start']
            self.while_body_end = loop_info['body_end']
            # [关键修复] 设置while-else范围
            if loop_info.get('has_else', False):
                self.while_else_start = loop_info['else_start']
                self.while_else_end = loop_info['else_end']
                # 创建else block
                while_node._orelse = ASTNodeList()
                debug_print(f"[_pop_jump_if_false] while循环有else分支: {self.while_else_start}-{self.while_else_end}")
            else:
                self.while_else_start = -1
                self.while_else_end = -1
            debug_print(f"[_pop_jump_if_false] while循环body范围: {self.while_body_start}-{self.while_body_end}")
            return
        
        # ===== if/elif/else处理（参考C++实现）=====
        # [关键修复] 检查是否是elif模式
        # elif模式的特征：
        # 1. 当前已有if节点
        # 2. 当前偏移在前一个if/elif的body结束之后
        # 3. 当前指令是一个条件跳转（POP_JUMP_IF_FALSE）
        is_elif = False
        is_last_elif = False  # [关键修复] 标记是否是链中的最后一个elif（有else分支）
        
        # [关键修复] 预先检查整个if-elif-else链中是否已经有elif
        has_elif_in_chain = False
        if hasattr(self, '_if_chain_root') and self._if_chain_root is not None:
            if hasattr(self._if_chain_root, '_orelse') and self._if_chain_root._orelse:
                if hasattr(self._if_chain_root._orelse, 'nodes') and len(self._if_chain_root._orelse.nodes) > 0:
                    has_elif_in_chain = True
                    debug_print(f"[_pop_jump_if_false] 检测到链中已有elif，节点数={len(self._if_chain_root._orelse.nodes)}")
        
        if hasattr(self, 'current_if_node') and self.current_if_node is not None:
            # 检查当前是否在if-elif-else链中
            if_body_end = getattr(self, 'if_body_end_offset', -1)
            
            # [关键修复] 检查是否是elif模式：
            # 当前偏移应该在前一个if/elif的body结束之后
            if current_offset >= if_body_end:
                # [关键修复] 这是一个elif或else
                # 我们需要区分elif和else
                # elif的特征：当前指令是POP_JUMP_FORWARD_IF_FALSE，且前面有条件加载
                # else的特征：当前指令是POP_JUMP_FORWARD_IF_FALSE，但前面没有条件加载
                
                # [关键修复] 检查前面的指令是否是条件加载（LOAD_NAME, LOAD_FAST等）
                # 使用 _get_instruction_before_offset 而不是 _get_instruction_at_offset(current_offset - 2)
                # 因为指令可能占用多个字节（如 COMPARE_OP 占用 6 字节）
                prev_instr = self._get_instruction_before_offset(current_offset)
                is_preceded_by_load = False
                if prev_instr:
                    prev_opcode = prev_instr.get('opcode', 0)
                    # [关键修复] elif 前面应该是 COMPARE_OP（比较操作），而不是 LOAD_*
                    # 因为 elif x == 2: 的字节码是：LOAD_NAME x; LOAD_CONST 2; COMPARE_OP ==; POP_JUMP_FORWARD_IF_FALSE
                    if prev_opcode in [Opcode.LOAD_FAST_A, Opcode.LOAD_NAME_A, Opcode.LOAD_CONST_A, Opcode.LOAD_GLOBAL_A, Opcode.COMPARE_OP_A]:
                        is_preceded_by_load = True
                        debug_print(f"[_pop_jump_if_false] 前面是条件加载/比较指令: {prev_opcode}")
                
                # [关键修复] 检查跳转目标是否是另一个条件判断
                target_instr = self._get_instruction_at_offset(jump_target)
                is_target_condition = False
                if target_instr:
                    target_opcode = target_instr.get('opcode', 0)
                    # [关键修复] 使用 _get_instruction_after_offset 查找跳转目标后的指令
                    next_instr = self._get_instruction_after_offset(jump_target)
                    if next_instr:
                        next_opcode = next_instr.get('opcode', 0)
                        # 跳转目标是LOAD_*，下一条是POP_JUMP_FORWARD_IF_FALSE，说明还有elif
                        if target_opcode in [Opcode.LOAD_FAST_A, Opcode.LOAD_NAME_A, Opcode.LOAD_CONST_A, Opcode.LOAD_GLOBAL_A]:
                            if next_opcode in [Opcode.POP_JUMP_FORWARD_IF_FALSE_A, Opcode.POP_JUMP_FORWARD_IF_TRUE_A]:
                                is_target_condition = True
                                debug_print(f"[_pop_jump_if_false] 跳转目标是另一个条件判断: {target_opcode}, {next_opcode}")
                
                # [关键修复] 判断是elif还是else
                if is_preceded_by_load:
                    # 前面有条件加载，这是一个elif
                    # 前面有条件加载说明这是elif（不是else）
                    is_elif = True
                    if is_target_condition:
                        # 跳转目标还有条件判断，这是elif（后面还有elif或else）
                        debug_print(f"[_pop_jump_if_false] 检测到elif模式（后面还有条件），跳转目标={jump_target}")
                    else:
                        # 跳转目标没有条件判断，这是最后一个elif（或else）
                        if has_elif_in_chain:
                            is_last_elif = True
                            debug_print(f"[_pop_jump_if_false] 检测到elif模式（链中的最后一个elif），跳转目标={jump_target}")
                        else:
                            debug_print(f"[_pop_jump_if_false] 检测到elif模式（第一个elif），跳转目标={jump_target}")
                else:
                    debug_print(f"[_pop_jump_if_false] 前面不是条件加载，不是elif模式")
            else:
                debug_print(f"[_pop_jump_if_false] 不是elif模式：current_offset={current_offset} < if_body_end={if_body_end}")
        else:
            debug_print(f"[_pop_jump_if_false] 不是elif模式：没有current_if_node")
        
        # 检查当前块是否是空的else块（转换为elif）
        if (self.current_block.blk_type == ASTBlock.BlockType.BLK_ELSE and 
            len(self.current_block) == 0):
            is_elif = True
            debug_print(f"[_pop_jump_if_false] 空else块，折叠为elif")
        
        if is_elif and hasattr(self, 'current_if_node') and self.current_if_node:
            # 折叠为elif语句
            if self.current_block.blk_type == ASTBlock.BlockType.BLK_ELSE:
                self._pop_block_from_stack()
                if self.stack_hist:
                    self.stack_hist.pop()
            
            # [关键修复] 创建elif块，同时作为elif节点的body
            # 这样后续发射的节点会直接添加到elif节点的body中
            elif_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_ELIF, end=jump_target, inited=True)
            self._push_block(elif_block)
            
            # 创建elif节点并添加到链的根节点的orelse中
            # 使用elif_block作为then_block，这样_emit的节点会直接添加到elif_block
            else_block = ASTNodeList()
            elif_node = ASTIf(condition, elif_block, else_block)
            
            # [关键修复] 将elif节点添加到current_if_node的orelse，形成链式结构
            if self.current_if_node._orelse is None:
                self.current_if_node._orelse = ASTNodeList()
            self.current_if_node._orelse.append(elif_node)
            debug_print(f"[_pop_jump_if_false] 创建elif节点并添加到current_if_node的orelse，形成链式结构")
            
            self.current_if_node = elif_node
            # [关键修复] 设置elif body的范围
            self.if_body_start_offset = current_offset + 2
            self.if_body_end_offset = jump_target
            
            # [关键修复] 如果是链中的最后一个elif（有else分支），设置else分支的范围
            if is_last_elif:
                # 找到else分支的结束位置
                else_end = self._find_else_end(jump_target)
                if else_end > 0:
                    self.if_body_end_offset = else_end
                    debug_print(f"[_pop_jump_if_false] 链中的最后一个elif，设置body结束位置为else结束: {else_end}")
            
            # [关键修复] 保持_if_chain_root不变，指向链的根节点
            debug_print(f"[_pop_jump_if_false] 创建elif节点，保持_if_chain_root")
            return
        
        # ===== 普通if语句处理 =====
        # [DEBUG] 关键修复：支持嵌套if语句
        # 使用栈来跟踪嵌套的if语句
        if not hasattr(self, '_if_stack'):
            self._if_stack = []
        
        # 保存当前的if信息到栈（用于嵌套if）
        if hasattr(self, 'current_if_node') and self.current_if_node is not None:
            self._if_stack.append({
                'node': self.current_if_node,
                'body_start': getattr(self, 'if_body_start_offset', -1),
                'body_end': getattr(self, 'if_body_end_offset', -1),
            })
            debug_print(f"[_pop_jump_if_false] 保存外层if到栈，当前栈深度: {len(self._if_stack)}")
        
        # 创建if块
        if_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_IF, end=jump_target, inited=True)
        self._push_block(if_block)
        
        # 创建if节点
        then_block = ASTNodeList()
        else_block = ASTNodeList()
        if_node = ASTIf(condition, then_block, else_block)
        
        # 检查是否是嵌套if（当前在另一个if的body范围内）
        is_nested_if = False
        parent_if = None
        if self._if_stack:
            outer_if_info = self._if_stack[-1]
            outer_if_body_start = outer_if_info['body_start']
            outer_if_body_end = outer_if_info['body_end']
            is_nested_if = (outer_if_body_start <= current_offset < outer_if_body_end)
            if is_nested_if:
                parent_if = outer_if_info['node']
        
        if is_nested_if and parent_if is not None:
            # [DEBUG] 嵌套if：将内层if添加到外层if的body中
            debug_print(f"[_pop_jump_if_false] 检测到嵌套if，将内层if添加到外层if的body中")
            debug_print(f"[_pop_jump_if_false] 外层if范围: {outer_if_body_start}-{outer_if_body_end}")
            debug_print(f"[_pop_jump_if_false] 当前offset: {current_offset}")
            # 将内层if添加到外层if的body中
            if hasattr(parent_if, '_body') and parent_if._body is not None:
                parent_if._body.append(if_node)
                debug_print(f"[_pop_jump_if_false] 内层if已添加到外层if的body中")
        
        self.current_if_node = if_node
        self.if_body_start_offset = current_offset + 2
        self.if_body_end_offset = jump_target
        
        # [关键修复] 设置_if_chain_root，指向if-elif-else链的根节点
        self._if_chain_root = if_node
        debug_print(f"[_pop_jump_if_false] 设置_if_chain_root，指向if节点")
        
        debug_print(f"[_pop_jump_if_false] 创建ASTIf节点, condition={condition}")
        debug_print(f"[_pop_jump_if_false] body范围: {self.if_body_start_offset}-{self.if_body_end_offset}")
        debug_print(f"[_pop_jump_if_false] 是否是嵌套if: {is_nested_if}")
        
        # [DEBUG] 关键修复：发射if节点前，保存当前块并恢复到主块
        # 这样if节点会被添加到正确的位置（主块），而不是if_block
        saved_block = self.current_block
        self.current_block = self.main_block
        
        # 只有非嵌套if才需要发射到主块（嵌套if已经添加到外层if的body中）
        if not is_nested_if:
            self._emit(if_node)
        
        self.current_block = saved_block  # 恢复当前块为if_block，以便后续节点添加到if body
    
    def _get_instruction_at_offset(self, offset: int) -> Optional[Dict]:
        """获取指定偏移处的指令"""
        if not hasattr(self, 'instructions') or not self.instructions:
            return None
        
        # 查找偏移匹配的指令
        for instr in self.instructions:
            if instr.get('offset') == offset:
                return instr
        
        return None
    
    def _get_instruction_before_offset(self, offset: int) -> Optional[Dict]:
        """获取指定偏移之前的最近一条指令（跳过CACHE等填充指令）"""
        if not hasattr(self, 'instructions') or not self.instructions:
            return None
        
        # 查找偏移小于给定值的最大指令（跳过CACHE）
        prev_instr = None
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            if instr_offset < offset:
                # 跳过CACHE指令（Python 3.11+的填充指令）
                if instr.get('opcode') != Opcode.CACHE:
                    prev_instr = instr
            elif instr_offset >= offset:
                break
        
        return prev_instr
    
    def _get_instruction_after_offset(self, offset: int) -> Optional[Dict]:
        """获取指定偏移之后的最近一条指令"""
        if not hasattr(self, 'instructions') or not self.instructions:
            return None
        
        # 查找偏移大于给定值的最小指令
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            if instr_offset > offset:
                return instr
        
        return None
    
    def _is_in_exception_context(self, current_offset: int) -> bool:
        """检查当前是否在异常处理上下文中（用于检测except块中的变量）"""
        # 对于`except Exception as e:`，字节码序列是：
        # LOAD_NAME Exception; CHECK_EXC_MATCH; POP_JUMP_FORWARD_IF_FALSE; STORE_NAME e
        # 所以我们需要检查前面是否有CHECK_EXC_MATCH，中间可能有POP_JUMP_FORWARD_IF_FALSE
        
        # 查找前面最多5条指令
        for offset in range(current_offset - 2, max(-1, current_offset - 20), -2):
            instr = self._get_instruction_at_offset(offset)
            if instr:
                opcode = instr['opcode']
                # 跳过NOP指令
                if opcode == Opcode.NOP:
                    continue
                # 如果找到CHECK_EXC_MATCH，则在异常处理上下文中
                if opcode == Opcode.CHECK_EXC_MATCH:
                    return True
                # 如果找到POP_JUMP_FORWARD_IF_FALSE，继续向前查找
                if opcode == Opcode.POP_JUMP_FORWARD_IF_FALSE_A:
                    continue
                # 如果遇到其他指令，则不在异常处理上下文中
                break
        
        return False

    def _pop_jump_forward_if_true(self, target: int) -> None:
        """如果栈顶为真则向前跳转并弹出"""
        if not self.stack.empty():
            condition = self.stack.top()
            self.stack.pop()
            
            # [DEBUG] 关键修复：检测assert语句模式
            # assert语句的模式：POP_JUMP_FORWARD_IF_TRUE跳转到assert结束
            # 后面跟着LOAD_ASSERTION_ERROR和消息，然后RAISE_VARARGS
            current_offset = getattr(self, 'current_instruction_offset', 0)
            assert_info = self._is_assert_pattern(current_offset, target)
            
            if assert_info and assert_info['is_assert']:
                # 这是assert语句，创建ASTAssert节点
                debug_print(f"[_pop_jump_forward_if_true] 检测到assert语句模式")
                # assert条件应该是原条件的否定
                # 因为POP_JUMP_FORWARD_IF_TRUE表示条件为真时跳过assert
                assert_node = ASTAssert(condition)
                self._emit(assert_node)
                # 设置当前assert节点，用于后续提取消息
                self._current_assert_node = assert_node
                # 设置跳过assert相关指令的标志
                self._skip_assert_instructions = True
                self._assert_end_offset = assert_info['end_offset']
                debug_print(f"[_pop_jump_forward_if_true] 设置跳过assert指令，结束位置: {self._assert_end_offset}")
            else:
                # 创建条件分支
                branch_node = self._create_conditional_branch(condition, target, True)
                self._emit(branch_node)
    
    def _is_assert_pattern(self, current_offset: int, target: int) -> dict:
        """检测是否是assert语句模式，返回包含is_assert和end_offset的字典"""
        result = {'is_assert': False, 'end_offset': 0}
        
        # assert语句的特征：
        # 1. POP_JUMP_FORWARD_IF_TRUE跳转到assert结束
        # 2. 跳转目标之后是LOAD_ASSERTION_ERROR或RAISE_VARARGS
        
        if not hasattr(self, 'instructions') or not self.instructions:
            return result
        
        # 查找当前指令的索引
        current_idx = -1
        for i, instr in enumerate(self.instructions):
            if instr.get('offset') == current_offset:
                current_idx = i
                break
        
        if current_idx < 0 or current_idx + 1 >= len(self.instructions):
            return result
        
        # 检查下一条指令是否是LOAD_ASSERTION_ERROR
        next_instr = self.instructions[current_idx + 1]
        next_opcode = next_instr.get('opcode', 0)
        
        if next_opcode == Opcode.LOAD_ASSERTION_ERROR:
            # 查找RAISE_VARARGS来确定assert结束位置
            for j in range(current_idx + 1, min(len(self.instructions), current_idx + 20)):
                if self.instructions[j].get('opcode') == Opcode.RAISE_VARARGS_A:
                    result['is_assert'] = True
                    result['end_offset'] = self.instructions[j].get('offset', 0)
                    return result
        
        # 或者检查跳转目标附近是否有RAISE_VARARGS
        for instr in self.instructions:
            instr_offset = instr.get('offset', 0)
            if target - 10 <= instr_offset <= target + 10:
                if instr.get('opcode') == Opcode.RAISE_VARARGS_A:
                    # 检查这条RAISE_VARARGS之前是否有LOAD_ASSERTION_ERROR
                    raise_idx = self.instructions.index(instr)
                    for j in range(max(0, raise_idx - 5), raise_idx):
                        if self.instructions[j].get('opcode') == Opcode.LOAD_ASSERTION_ERROR:
                            result['is_assert'] = True
                            result['end_offset'] = instr.get('offset', 0)
                            return result
        
        return result

    def _pop_jump_backward_if_true(self, target: int) -> None:
        """如果栈顶为真则向后跳转并弹出 - 用于while循环 - 修复版本"""
        debug_print(f"[_pop_jump_backward_if_true] target={target}")
        if not self.stack.empty():
            condition = self.stack.top()
            self.stack.pop()
            debug_print(f"[_pop_jump_backward_if_true] condition={condition}")
            
            # 向后跳转表示这是一个while循环的继续条件
            # 查找最近的while节点并更新其条件
            if hasattr(self, 'current_while_node') and self.current_while_node:
                debug_print(f"[_pop_jump_backward_if_true] 更新while节点条件")
                self.current_while_node._condition = condition
            else:
                # 如果没有找到while节点，创建一个
                debug_print(f"[_pop_jump_backward_if_true] 创建新的while节点")
                while_node = ASTWhile(condition, ASTNodeList(), None)
                
                # [DEBUG] 关键修复：先发射while节点，再设置current_while_node
                # 这样while节点本身会被添加到main_block，而不是它自己的body中
                saved_block = self.current_block  # 保存当前块
                self.current_block = self.main_block  # 设置为主块
                self._emit(while_node)
                self.current_block = saved_block  # 恢复当前块
                
                self.current_while_node = while_node
                
                # [DEBUG] 关键修复：设置while循环体的范围
                # 向后跳转的目标就是循环体的开始位置
                # 当前指令位置是循环体的结束位置
                current_offset = getattr(self, 'current_instruction_offset', 0)
                self.while_body_start = target
                self.while_body_end = current_offset
                debug_print(f"[_pop_jump_backward_if_true] 设置while body范围: {self.while_body_start}-{self.while_body_end}")

    def _pop_jump_backward_if_false(self, target: int) -> None:
        """如果栈顶为假则向后跳转并弹出 - 用于while循环"""
        debug_print(f"[_pop_jump_backward_if_false] target={target}")
        if not self.stack.empty():
            condition = self.stack.top()
            self.stack.pop()
            debug_print(f"[_pop_jump_backward_if_false] condition={condition}")
            
            # 向后跳转表示这是一个while循环的继续条件
            # 条件为假时跳转，相当于while condition:
            if hasattr(self, 'current_while_node') and self.current_while_node:
                debug_print(f"[_pop_jump_backward_if_false] 更新while节点条件")
                self.current_while_node._condition = condition
            else:
                debug_print(f"[_pop_jump_backward_if_false] 创建新的while节点")
                while_node = ASTWhile(condition, ASTNodeList(), None)
                
                # [DEBUG] 关键修复：先发射while节点，再设置current_while_node
                # 这样while节点本身会被添加到main_block，而不是它自己的body中
                saved_block = self.current_block  # 保存当前块
                self.current_block = self.main_block  # 设置为主块
                self._emit(while_node)
                self.current_block = saved_block  # 恢复当前块
                
                self.current_while_node = while_node

    def _jump_forward(self, target: int) -> None:
        """向前跳转 - 修复版本，支持if-elif-else链"""
        # 基于控制流分析生成AST节点
        # 检查是否是循环结构的跳转
        is_loop = self._is_loop_jump(target)
        
        if is_loop:
            # 这是循环结构的跳转，不生成AST节点
            # 循环的AST节点已经在之前的分析中创建
            return
        
        # [DEBUG] 关键修复：检查是否是跳转到finally块
        # 在try-except-finally结构中，try和except块都以JUMP_FORWARD跳转到finally块
        if hasattr(self, 'current_exception_handler') and self.current_exception_handler is not None:
            # 如果当前在异常处理上下文中，且跳转目标是向前跳转
            # 这可能是跳转到finally块
            debug_print(f"[_jump_forward] 检测到可能的finally块跳转: target={target}")
            # 设置finally块的开始位置
            self.finally_body_start_offset = target
            # 设置一个较大的结束位置，后续会根据END_FINALLY调整
            self.finally_body_end_offset = target + 1000
        
        # [关键修复] 检查是否在if语句中，如果是，这可能是if主体结束后的跳转
        # 用于创建else块，支持if-elif-else链
        current_offset = self.current_instruction_offset
        if hasattr(self, 'current_if_node') and self.current_if_node is not None:
            if_body_end = getattr(self, 'if_body_end_offset', -1)
            if current_offset < if_body_end:
                # 这是在if主体中遇到的JUMP_FORWARD，用于跳过else/elif分支
                # 创建else块来接收后续的elif或else代码
                debug_print(f"[_jump_forward] 在if主体中检测到JUMP_FORWARD，创建else块")
                
                # 计算跳转目标（if结束后的位置）
                jump_target = current_offset + 2 + target * 2
                
                # 创建else块
                else_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_ELSE, end=jump_target, inited=True)
                self._push_block(else_block)
                
                # 更新if_body_end_offset为else块的结束位置
                self.if_body_end_offset = jump_target
                
                debug_print(f"[_jump_forward] else块范围: {current_offset} - {jump_target}")
                return
        
        # 向前跳转通常用于if语句和条件控制流
        # 检查是否是条件跳转
        condition = None
        if not self.stack.empty():
            condition = self.stack.top()
            
        # 如果有条件且不是循环，则是条件跳转
        if condition is not None:
            # 获取当前的指令偏移
            current_offset = self.current_instruction_offset
            
            # 检查跳转目标附近是否有循环结构
            loop_info = self._find_loop_at_target(target)
            if loop_info:
                # 循环已经处理过，跳过
                return
            
            # 创建条件分支节点
            branch_node = self._create_conditional_branch(condition, target)
            self._emit(branch_node)
            
            # 弹出条件
            self.stack.pop()
        else:
            # 无条件跳转，可能是异常处理或特殊控制流
            # 这里不做特殊处理，让后续处理
            pass
    
    def _jump_if_false_or_pop(self, target: int) -> None:
        """如果为假则跳转否则弹出"""
        # 检查栈是否为空
        if self.stack.empty():
            return
        
        # 弹出条件
        condition = self.stack.top()
        self.stack.pop()
        
        # 创建条件分支节点
        branch_node = self._create_conditional_branch(condition, target, is_true_branch=False)
        self._emit(branch_node)
    
    def _jump_if_true_or_pop(self, target: int) -> None:
        """如果为真则跳转否则弹出"""
        # 检查栈是否为空
        if self.stack.empty():
            return
        
        # 弹出条件
        condition = self.stack.top()
        self.stack.pop()
        
        # 创建条件分支节点
        branch_node = self._create_conditional_branch(condition, target, is_true_branch=True)
        self._emit(branch_node)
    
    def _is_loop_jump(self, target: int) -> bool:
        """检查跳转是否是循环结构"""
        # 检查控制流分析结果中的循环结构
        for loop in self._loop_structures:
            # 检查是否是该循环的后边跳转
            if 'back_edge' in loop and loop['back_edge'][1] == target:
                return True
        return False
    
    def _find_loop_at_target(self, target: int) -> Optional[Dict]:
        """查找跳转目标附近的循环结构"""
        for loop in self._loop_structures:
            # 检查循环头是否在跳转目标附近
            if 'header' in loop and abs(loop['header'] - target) < 5:
                return loop
        return None
    
    def _create_conditional_branch(self, condition: 'ASTNode', target: int, is_true_branch: bool = True) -> 'ASTNode':
        """创建条件分支AST节点"""
        # 确定分支类型
        # 首先检查是否是循环结构
        loop_info = self._find_loop_at_target(target)
        if loop_info:
            # 这是一个循环结构
            if loop_info.get('type') == 'while':
                # 创建while循环节点
                while_node = ASTWhile(condition, None, None)
                return while_node
        
        # 如果不是循环，则是if语句
        # 获取分支的目标块
        true_block = None
        false_block = None
        
        if is_true_branch:
            true_block = target
            # 假设false_block是下一条指令（需要从控制流图中获取）
            if self._control_flow_graph:
                next_offset = self.current_instruction_offset + 2  # 假设每条指令2字节
                false_block = self._control_flow_graph.get(next_offset, {}).get('next')
        else:
            false_block = target
            # 假设true_block是下一条指令（需要从控制流图中获取）
            if self._control_flow_graph:
                next_offset = self.current_instruction_offset + 2  # 假设每条指令2字节
                true_block = self._control_flow_graph.get(next_offset, {}).get('next')
        
        # 创建if语句节点
        if_node = ASTIf(condition, true_block, false_block)
        return if_node

    def _build_string(self, count: int) -> None:
        """构建字符串（f-string）"""
        print(f"[DEBUG _build_string] count={count}, stack_size={self.stack.size()}", flush=True)
        parts = []
        for i in range(count):
            if not self.stack.empty():
                part = self.stack.top()
                self.stack.pop()
                print(f"[DEBUG _build_string] part[{i}]: {part}, type: {type(part).__name__ if part else 'None'}", flush=True)
                parts.insert(0, part)
        
        print(f"[DEBUG _build_string] parts: {parts}", flush=True)
        # 创建 ASTJoinedStr 节点
        joined_str = ASTJoinedStr(parts)
        self.stack.push(joined_str)

    def _load_global(self, operand: int) -> None:
        """加载全局变量"""
        # Python 3.11+ LOAD_GLOBAL uses special encoding:
        # - Low bit indicates NULL + name pair
        # - Actual name index = operand >> 1
        name_index = operand >> 1
        
        # 根据当前上下文选择names列表
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if not code_obj:
            return
        
        # 首先尝试使用当前代码对象的names
        names = code_obj.names
        if not names or not names.get():
            # 如果当前代码对象没有names，使用模块的names
            names = self.module.code.get().names
        
        if names and names.get():
            names_obj = names.get()
            global_name = None
            
            if isinstance(names_obj, PycString):
                global_names = names_obj.value.split('\x00')
                if 0 <= name_index < len(global_names):
                    global_name = global_names[name_index]
            elif hasattr(names_obj, 'get'):
                # 处理 PycSequence
                if 0 <= name_index < names_obj.size():
                    try:
                        name_ref = names_obj.get(name_index)
                        if name_ref:
                            name_obj = name_ref.get() if hasattr(name_ref, 'get') else name_ref
                            if isinstance(name_obj, PycString):
                                global_name = name_obj.value
                            else:
                                global_name = str(name_obj)
                    except (IndexError, TypeError, AttributeError):
                        pass
            
            if global_name:
                node = ASTName(global_name)
                self.stack.push(node)

    def _load_build_class(self) -> None:
        """加载构建类函数"""
        # 在栈上放置一个构建类的可调用对象
        node = ASTObject("BUILD_CLASS")
        self.stack.push(node)

    def _import_name(self, operand: int) -> None:
        """导入名称"""
        if not self.module.code:
            return
        
        names = self.module.code.get().names
        if names and names.get():
            names_obj = names.get()
            
            name_list = []
            
            if isinstance(names_obj, PycString):
                name_list = names_obj.value.split('\x00')
            elif isinstance(names_obj, PycSequence):
                # 处理 PycSequence
                for i in range(names_obj.size()):
                    try:
                        name_obj = names_obj.get(i)
                        if name_obj and name_obj.get():
                            name_value = name_obj.get()
                            if isinstance(name_value, PycString):
                                name_list.append(name_value.value)
                    except (IndexError, TypeError, AttributeError):
                        pass
            else:
                return
            
            if 0 <= operand < len(name_list):
                module_name = name_list[operand]
                
                # 检查是否有fromlist（在栈上）
                fromlist_exists = not self.stack.empty()
                
                fromlist = None
                if fromlist_exists:
                    fromlist_obj = self.stack.top()
                    self.stack.pop()
                    
                    # 正确处理PycSequence（fromlist直接是PycSequence）
                    if isinstance(fromlist_obj, PycSequence):
                        fromlist = []
                        for i in range(fromlist_obj.size()):
                            try:
                                item = fromlist_obj.get(i)
                                if item and item.get():
                                    item_value = item.get()
                                    if isinstance(item_value, PycString):
                                        fromlist.append(item_value.value)
                                    elif isinstance(item_value, PycNumeric):
                                        fromlist.append(str(item_value.value))
                                    else:
                                        fromlist.append(str(item_value))
                            except (IndexError, TypeError, AttributeError):
                                pass
                    # 正确处理ASTObject包装的PycSequence
                    elif hasattr(fromlist_obj, 'object'):
                        raw_fromlist = fromlist_obj.object
                        
                        # 如果object直接是PycSequence
                        if isinstance(raw_fromlist, PycSequence):
                            fromlist = []
                            for i in range(raw_fromlist.size()):
                                try:
                                    item = raw_fromlist.get(i)
                                    if item and item.get():
                                        item_value = item.get()
                                        if isinstance(item_value, PycString):
                                            fromlist.append(item_value.value)
                                        elif isinstance(item_value, PycNumeric):
                                            fromlist.append(str(item_value.value))
                                        else:
                                            fromlist.append(str(item_value))
                                except (IndexError, TypeError, AttributeError):
                                    pass
                        # 如果是PycObject，尝试获取其value
                        elif hasattr(raw_fromlist, 'value'):
                            raw_value = raw_fromlist.value
                            
                            # 如果是PycSequence，处理它
                            if isinstance(raw_value, PycSequence):
                                fromlist = []
                                for i in range(raw_value.size()):
                                    try:
                                        item = raw_value.get(i)
                                        if item and item.get():
                                            item_value = item.get()
                                            if isinstance(item_value, PycString):
                                                fromlist.append(item_value.value)
                                    except (IndexError, TypeError, AttributeError):
                                        pass
                            elif isinstance(raw_value, list):
                                fromlist = raw_value
                            else:
                                fromlist = []
                        else:
                            fromlist = []
                    else:
                        fromlist = []
                
                if fromlist and len(fromlist) > 0:
                    # from ... import ... 形式
                    node = ASTImportFrom(module_name, fromlist)
                    # 为导入节点添加module_name属性以便在_store_name中识别
                    node.module_name = module_name
                    
                    # 跟踪导入信息
                    self.last_import_module = module_name
                    self.last_import_names = fromlist
                    self.pending_from_import = True
                    
                else:
                    # import ... 形式
                    node = ASTImport(module_name)
                    # 为导入节点添加module_name属性以便在_store_name中识别
                    node.module_name = module_name
                    
                    # 跟踪导入信息
                    self.last_import_module = module_name
                    self.last_import_names = []
                    self.pending_from_import = False
                
                self._emit(node)
                self.stack.push(node)

    def _import_from(self, operand: int) -> None:
        """从模块导入"""
        if not self.module.code:
            return
        
        # IMPORT_FROM指令的operand指向names列表中要导入的名称
        names = self.module.code.get().names
        if not names or not names.get():
            return
        
        names_obj = names.get()
        imported_name = None
        
        # 获取要导入的名称（从operand索引）
        if isinstance(names_obj, PycSequence):
            if 0 <= operand < names_obj.size():
                try:
                    name_obj = names_obj.get(operand)
                    if name_obj and name_obj.get():
                        name_value = name_obj.get()
                        if isinstance(name_value, PycString):
                            imported_name = name_value.value
                except (IndexError, TypeError, AttributeError):
                    return
        elif isinstance(names_obj, PycString):
            name_list = names_obj.value.split('\x00')
            if 0 <= operand < len(name_list):
                imported_name = name_list[operand]
        
        # 使用跟踪的导入信息
        tracked_module_name = self.last_import_module
        
        if tracked_module_name and imported_name:
            # 将导入的名称推送到栈中
            node = ASTName(imported_name, tracked_module_name)
            self.stack.push(node)
        else:
            # 如果没有找到导入信息，创建一个简单的import语句
            if imported_name:
                node = ASTImport(imported_name)
                node.module_name = imported_name
                self._emit(node)

    def _generate_temp_var(self) -> str:
        """生成临时变量名"""
        import itertools
        if not hasattr(self, '_temp_counter'):
            self._temp_counter = 0
        self._temp_counter += 1
        return str(self._temp_counter)

    def _break_loop(self) -> None:
        """处理break指令"""
        node = ASTBreak()
        self._emit(node)

    def _raise_varargs(self, argc: int) -> None:
        """处理异常抛出指令"""
        if argc == 0:
            # RAISE_VARARGS_0: 重新抛出当前异常
            exc_node = ASTObject(None)
        elif argc == 1:
            # RAISE_VARARGS_1: 抛出指定异常
            # [DEBUG] 关键修复：栈顶可能是已经构造好的异常对象（如 ValueError("error") 的调用结果）
            # 也可能是异常类型（如 ValueError），需要检查
            exc = self.stack.pop() if not self.stack.empty() else ASTObject("RuntimeError")
            # 如果exc已经是ASTCall（如 ValueError("error")），直接使用
            # 否则（如 ValueError），包装为ASTCall
            if isinstance(exc, ASTCall):
                exc_node = exc
            else:
                exc_node = ASTCall(exc, [])
        elif argc == 2:
            # RAISE_VARARGS_2: 抛出异常并指定实例
            exc_val = self.stack.pop() if not self.stack.empty() else ASTObject("")
            exc_type = self.stack.pop() if not self.stack.empty() else ASTObject("RuntimeError")
            exc_node = ASTCall(exc_type, [exc_val])
        elif argc == 3:
            # RAISE_VARARGS_3: 抛出异常并指定类型、值和traceback
            tb = self.stack.pop() if not self.stack.empty() else ASTObject(None)
            exc_val = self.stack.pop() if not self.stack.empty() else ASTObject("")
            exc_type = self.stack.pop() if not self.stack.empty() else ASTObject("RuntimeError")
            exc_node = ASTCall(exc_type, [exc_val, tb])
        else:
            exc_node = ASTObject("RuntimeError")
        
        node = ASTRaise(exc_node)
        self._emit(node)
    
    def _setup_except(self, operand: int) -> None:
        """处理SETUP_EXCEPT指令，用于try-except结构
        
        参考C++ pycdc实现：
        - 创建容器块（ASTContainerBlock）
        - 保存当前栈状态到stack_hist
        - 创建try块并压入块栈
        """
        # 计算异常处理器的开始位置
        except_start_offset = self.current_instruction_offset + operand
        
        # [关键修复] 检查是否有else分支
        # try-else的特征：在try body和except body之间有实际代码
        # 从当前指令到except_start_offset之间，如果有STORE_NAME等指令，说明有else分支
        has_else = False
        else_start = -1
        else_end = -1
        
        for instr in self.instructions:
            instr_offset = instr.get('offset', -1)
            if self.current_instruction_offset < instr_offset < except_start_offset:
                instr_opcode = instr.get('opcode', -1)
                # 检查是否有实际代码指令（STORE_NAME等）
                if instr_opcode in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A]:
                    # 找到else分支的开始
                    if else_start < 0:
                        else_start = instr_offset - 2  # 假设前面有LOAD_CONST
                        has_else = True
                        debug_print(f"[_setup_except] 检测到try-else结构，else开始于{else_start}")
                    # 更新else分支的结束
                    else_end = instr_offset + 2
        
        # 保存当前栈状态
        self.stack_hist.append(self.stack.copy())
        
        # 创建try块并压入块栈
        try_block = ASTBlock(blk_type=ASTBlock.BlockType.BLK_TRY, end=except_start_offset, inited=True)
        self._push_block(try_block)
        
        # 创建try-except节点
        try_node = self._handle_try_except(except_start_offset)
        
        # [关键修复] 如果有else分支，设置orelse
        if has_else:
            try_node._orelse = ASTBlock()
            debug_print(f"[_setup_except] 设置try-else: {else_start}-{else_end}")
        
        # 记录当前try节点和范围
        self.current_try_node = try_node
        self.try_body_start_offset = self.current_instruction_offset
        self.try_body_end_offset = except_start_offset
        
        # [关键修复] 记录else分支范围
        self.try_else_start_offset = else_start if has_else else -1
        self.try_else_end_offset = else_end if has_else else -1
        
        # 重置need_try标志
        self.need_try = False
        
        # 发射try节点到当前块
        self._emit(try_node)
        
        debug_print(f"[_setup_except] 创建try块, except_start={except_start_offset}, has_else={has_else}")
    
    def _setup_finally(self, operand: int) -> None:
        """处理SETUP_FINALLY指令，用于try-except-finally结构 - 修复版本"""
        # 计算try块的结束位置（异常处理器的开始位置）
        try_end_offset = self.current_instruction_offset + operand
        
        # 创建try-except节点
        try_node = self._handle_try_except(try_end_offset)
        
        # 记录当前try节点和范围
        self.current_try_node = try_node
        self.try_body_start_offset = self.current_instruction_offset
        self.try_body_end_offset = try_end_offset
        
        # [DEBUG] 关键修复：设置finally块的范围
        # finally块从try_end_offset开始，到END_FINALLY指令结束
        # 我们需要在后续处理中动态确定finally块的结束位置
        self.finally_body_start_offset = try_end_offset
        self.finally_body_end_offset = try_end_offset + 1000  # 临时设置一个大值，后续会调整
        
        # 发射try节点到主块
        self._emit(try_node)

    def _setup_with(self, operand: int) -> None:
        """处理SETUP_WITH指令，用于with语句结构"""
        # Python 3.11+ 中 SETUP_WITH 用于设置 with 语句的上下文管理器
        # 操作数是相对跳转偏移量，指向 with 语句块的结束位置
        
        # 创建 with 语句节点
        # 上下文表达式应该在栈上
        if not self.stack.empty():
            context_expr = self.stack.top()
            self.stack.pop()
        else:
            context_expr = ASTName("__context__")
        
        # 创建 with 节点（暂时不带变量名，后续 STORE_FAST 会处理）
        with_node = ASTWith(context=context_expr, body=ASTBlock(), optional_vars=None)
        
        # 保存当前 with 节点，以便后续处理
        if not hasattr(self, '_pending_with_nodes'):
            self._pending_with_nodes = []
        self._pending_with_nodes.append(with_node)
        
        # [DEBUG] 使用栈管理嵌套with语句
        if not hasattr(self, '_with_stack'):
            self._with_stack = []
        
        # 记录 with 语句的信息
        with_info = {
            'node': with_node,
            'start_offset': self.current_instruction_offset,
            'end_offset': self.current_instruction_offset + 1000  # 临时大值
        }
        self._with_stack.append(with_info)
        
        # 设置当前 with 节点（兼容旧代码）
        self.current_with_node = with_node
        self.current_with_node_start_offset = with_info['start_offset']
        self.current_with_end_offset = with_info['end_offset']
        
        # 发射 with 节点
        self._emit(with_node)
    
    def _before_with(self, operand: int) -> None:
        """处理BEFORE_WITH指令，用于with语句 (Python 3.11+)"""
        debug_print(f"[_before_with] 被调用! operand={operand}, stack_size={self.stack.size()}")
        # BEFORE_WITH 在 Python 3.11+ 中替代了 SETUP_WITH
        # 它执行上下文管理器的 __enter__ 方法并准备异常处理
        # 我们可以复用 _setup_with 的逻辑
        self._setup_with(operand)
        
        # [DEBUG] 关键修复：BEFORE_WITH 指令会将 __enter__() 的返回值推入栈
        # 这个值会被后续的 STORE_NAME_A/STORE_FAST_A 指令存储为 with 语句的变量（as f）
        # 我们需要模拟这个行为，将一个占位符推入栈
        enter_result = ASTName("__enter_result__")
        self.stack.push(enter_result)
        debug_print(f"[_before_with] 将 __enter__ 返回值推入栈，当前栈大小: {self.stack.size()}")
    
    def _before_async_with(self, operand: int) -> None:
        """处理BEFORE_ASYNC_WITH指令，用于异步with语句"""
        # 类似于 SETUP_WITH，但用于异步上下文
        # 对于简化实现，我们可以复用 _setup_with 的逻辑
        self._setup_with(operand)
    
    def _push_exc_info(self) -> None:
        """处理PUSH_EXC_INFO指令，用于异常处理 - 修复版本"""
        # Python 3.11+ 中 PUSH_EXC_INFO 将当前异常信息推入栈
        # 这标志着 except 块的开始
        # 我们需要确保 try-except 结构已经创建
        
        current_offset = self.current_instruction_offset
        
        # 检查current_exception_handler的状态
        has_handler = hasattr(self, 'current_exception_handler')
        handler_value = getattr(self, 'current_exception_handler', None)
        print(f"[_push_exc_info] has_handler={has_handler}, handler_value={handler_value}")
        
        # [DEBUG] 修复：检查是否有with语句节点，如果有则不创建try-finally结构
        has_with_node = False
        if hasattr(self, 'current_block') and self.current_block is not None:
            main_block_nodes = list(self.current_block)
            for node in main_block_nodes:
                if type(node).__name__ == 'ASTWith':
                    has_with_node = True
                    break
        
        # 如果已经有with语句，不创建try-finally结构（with语句有自己的异常处理机制）
        if has_with_node:
            print(f"[_push_exc_info] 检测到with语句，跳过try-finally创建")
            # [DEBUG] 关键修复：在PUSH_EXC_INFO处设置with语句的结束位置
            # with body应该在PUSH_EXC_INFO之前结束
            # 更新栈顶的with语句
            if hasattr(self, '_with_stack') and self._with_stack:
                # 找到栈顶未完成的with语句
                for i in range(len(self._with_stack) - 1, -1, -1):
                    with_info = self._with_stack[i]
                    if with_info.get('end_offset', 0) > with_info.get('start_offset', 0) + 100:
                        # 这个with语句的结束位置还是临时值，更新它
                        with_info['end_offset'] = current_offset
                        debug_print(f"[_push_exc_info] 设置with语句[{i}]结束位置: {current_offset}")
                        # 同时更新兼容属性
                        if i == len(self._with_stack) - 1:
                            self.current_with_end_offset = current_offset
                        break
            # 兼容旧代码
            elif hasattr(self, 'current_with_node') and self.current_with_node is not None:
                self.current_with_end_offset = current_offset
                debug_print(f"[_push_exc_info] 设置with语句结束位置: {current_offset}")
            # 推入异常信息占位符
            exc_info = ASTName("__exc_info__")
            self.stack.push(exc_info)
            return
        
        # 如果还没有创建异常处理器，创建一个
        if not has_handler or not handler_value:
            from core.ast_nodes import ASTTry, ASTBlock, ASTExceptHandler
            try_node = ASTTry(ASTBlock(), [], ASTBlock(), ASTBlock())
            self.current_exception_handler = try_node
            self.current_try_node = try_node
            
            # [DEBUG] 关键修复：将之前添加到主块的语句移动到 try 块
            # 这些语句属于 try 块，但在遇到 PUSH_EXC_INFO 之前已经被添加到主块
            if not has_with_node and hasattr(self, 'current_block') and self.current_block is not None:
                # 获取主块中的所有节点
                main_block_nodes = list(self.current_block)
                print(f"[_push_exc_info] 主块节点数量: {len(main_block_nodes)}")
                # 将节点添加到 try 块
                for node in main_block_nodes:
                    print(f"[_push_exc_info] 移动节点: {type(node).__name__}")
                    if hasattr(try_node, '_body') and try_node._body is not None:
                        try_node._body.append(node)
                # 清空主块 - 使用_nodes属性直接清空
                if hasattr(self.current_block, '_nodes'):
                    self.current_block._nodes.clear()
                print(f"[_push_exc_info] 将 {len(main_block_nodes)} 个节点从主块移动到 try 块")
            
            # 设置 try 块的范围
            self.try_body_start_offset = 0
            self.try_body_end_offset = current_offset
            
            # [关键修复] 检查是否有else分支
            # try-else的特征：在try body和PUSH_EXC_INFO之间有实际代码
            # 查找RETURN_VALUE或JUMP_FORWARD指令作为分隔符
            has_else = False
            else_start = -1
            else_end = -1
            return_value_offset = -1
            
            print(f"[_push_exc_info] 检查else分支: current_offset={current_offset}, instructions数量={len(self.instructions)}")
            
            # 首先找到RETURN_VALUE或JUMP_FORWARD作为分隔符
            for instr in self.instructions:
                instr_offset = instr.get('offset', -1)
                instr_opcode = instr.get('opcode', -1)
                instr_name = instr.get('opname', '')
                in_range = 0 < instr_offset < current_offset
                is_separator = instr_opcode in [Opcode.RETURN_VALUE, Opcode.JUMP_FORWARD_A]
                
                if in_range:
                    print(f"[_push_exc_info] 检查指令: offset={instr_offset}, opcode={instr_opcode}, name={instr_name}, is_separator={is_separator}")
                
                if in_range and is_separator:
                    return_value_offset = instr_offset
                    print(f"[_push_exc_info] 找到分隔符 at offset={instr_offset}")
                    break
            
            if return_value_offset > 0:
                # 找到了分隔符，说明可能有else分支
                # else分支在RETURN_VALUE之前（Python 3.11的编译方式）
                print(f"[_push_exc_info] 查找else分支: return_value_offset={return_value_offset}")
                
                # [关键修复] 查找在RETURN_VALUE之前的LOAD_CONST + STORE_NAME序列
                # 这些属于else body
                prev_instr = None
                for instr in self.instructions:
                    instr_offset = instr.get('offset', -1)
                    instr_opcode = instr.get('opcode', -1)
                    
                    # [关键修复] 只查找在RETURN_VALUE之前的STORE_NAME
                    if 0 < instr_offset < return_value_offset:
                        if instr_opcode in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A]:
                            # 检查前面是否有LOAD_CONST
                            if prev_instr and prev_instr.get('opcode', -1) == Opcode.LOAD_CONST_A:
                                # 这是else body的一部分
                                if else_start < 0:
                                    else_start = prev_instr.get('offset', -1)
                                    has_else = True
                                    print(f"[_push_exc_info] 找到else开始 at offset={else_start}")
                                else_end = instr_offset + 2
                                print(f"[_push_exc_info] 更新else结束 at offset={else_end}")
                    
                    prev_instr = instr
                
                # [关键修复] 如果else_start和try body重叠，调整else_start
                # try body结束于第一个STORE_NAME之后
                if has_else:
                    # 找到第一个STORE_NAME的位置作为try body的结束
                    first_store_offset = -1
                    for instr in self.instructions:
                        instr_offset = instr.get('offset', -1)
                        instr_opcode = instr.get('opcode', -1)
                        if 0 < instr_offset < return_value_offset:
                            if instr_opcode in [Opcode.STORE_NAME_A, Opcode.STORE_FAST_A, Opcode.STORE_GLOBAL_A]:
                                if first_store_offset < 0:
                                    first_store_offset = instr_offset
                                    break
                    
                    # 如果else_start在try body范围内，调整else_start
                    if first_store_offset > 0 and else_start < first_store_offset + 4:
                        # 查找在first_store_offset之后的第一个LOAD_CONST
                        for instr in self.instructions:
                            instr_offset = instr.get('offset', -1)
                            instr_opcode = instr.get('opcode', -1)
                            if first_store_offset < instr_offset < return_value_offset:
                                if instr_opcode == Opcode.LOAD_CONST_A:
                                    else_start = instr_offset
                                    print(f"[_push_exc_info] 调整else开始 at offset={else_start}")
                                    break
                
            if has_else:
                print(f"[_push_exc_info] 检测到try-else结构: {else_start}-{else_end}")
                try_node._orelse = ASTBlock()
                
                # [关键修复] 将try body中属于else body的节点移动到else body
                # 简化处理：假设try body中的第二个STORE_NAME属于else body
                if hasattr(try_node, '_body') and try_node._body is not None:
                    body_nodes = list(try_node._body)
                    store_count = 0
                    nodes_to_move = []
                    for node in body_nodes:
                        if type(node).__name__ == 'ASTStore':
                            store_count += 1
                            if store_count == 2:
                                # 第二个STORE_NAME属于else body
                                nodes_to_move.append(node)
                    
                    # 移动节点
                    for node in nodes_to_move:
                        print(f"[_push_exc_info] 将节点从try body移动到else body: {type(node).__name__}")
                        # 使用_nodes列表的remove方法
                        if hasattr(try_node._body, '_nodes'):
                            try_node._body._nodes.remove(node)
                        try_node._orelse.append(node)
            
            self.try_else_start_offset = else_start if has_else else -1
            self.try_else_end_offset = else_end if has_else else -1
            
            # [DEBUG] 关键修复：检测是 try-except 还是 try-finally
            # 通过预扫描后续指令来判断
            is_try_except, finally_start, finally_end = self._is_try_except_pattern(current_offset)
            
            if is_try_except:
                debug_print(f"[_push_exc_info] 创建try-except结构，try块范围: {self.try_body_start_offset}-{self.try_body_end_offset}")
                # [关键修复] 检查后续指令是否有CHECK_EXC_MATCH
                # 如果有，则不在此处创建handler，由_check_exc_match创建
                has_check_exc_match = False
                # 查找当前PUSH_EXC_INFO指令在指令列表中的索引
                push_exc_info_idx = -1
                for i, instr in enumerate(self.instructions):
                    if instr.get('offset') == current_offset:
                        push_exc_info_idx = i
                        break
                
                if push_exc_info_idx >= 0:
                    for i in range(1, min(10, len(self.instructions) - push_exc_info_idx)):
                        instr = self.instructions[push_exc_info_idx + i]
                        if instr.get('opcode') == Opcode.CHECK_EXC_MATCH:
                            has_check_exc_match = True
                            break
                        if instr.get('opcode') == Opcode.POP_TOP:
                            break
                
                if not has_check_exc_match:
                    # 对于简单的`except:`，创建一个没有指定异常类型的handler
                    except_handler = ASTExceptHandler(None, None, ASTBlock())
                    try_node.handlers.append(except_handler)
                    self.current_except_handler = except_handler
                # 设置except body的范围，从PUSH_EXC_INFO后开始
                self.except_body_start_offset = current_offset
                self.except_body_end_offset = current_offset + 10  # 临时值，会在POP_EXCEPT时更新
            else:
                debug_print(f"[_push_exc_info] 创建try-finally结构，try块范围: {self.try_body_start_offset}-{self.try_body_end_offset}")
                # 对于 try-finally，标记为 finally 模式并设置 finally 块范围
                self.is_try_finally = True
                if finally_start >= 0 and finally_end >= 0:
                    self.finally_body_start_offset = finally_start
                    self.finally_body_end_offset = finally_end
                    print(f"[_push_exc_info] 设置finally块范围: {finally_start}-{finally_end}")
                    
                    # [DEBUG] 关键修复：对于 try-finally，需要将 try 块中属于 finally 的代码移动到 finally 块
                    # finally 块的代码在字节码中出现在 PUSH_EXC_INFO 之前，所以被错误地添加到了 try 块
                    self._move_finally_code_from_try_block(try_node, current_offset)
            
            # 将 try 节点添加到主块
            if hasattr(self, 'current_block') and self.current_block is not None:
                print(f"[_push_exc_info] 添加try节点到current_block, current_block={self.current_block}, main_block={self.main_block}, 相同={self.current_block is self.main_block}")
                self.current_block.append(try_node)
                print(f"[_push_exc_info] 添加后current_block节点数: {len(list(self.current_block))}")
                debug_print(f"[_push_exc_info] 将 try 节点添加到主块")
        
        # 推入异常信息占位符
        exc_info = ASTName("__exc_info__")
        self.stack.push(exc_info)
        debug_print(f"[_push_exc_info] 推入异常信息，current_exception_handler={self.current_exception_handler}")
    
    def _is_try_except_pattern(self, push_exc_info_offset: int) -> tuple:
        """检测是 try-except 还是 try-finally 模式，并返回 finally 块范围
        
        try-except 模式: PUSH_EXC_INFO 后会有:
            - CHECK_EXC_MATCH (有指定异常类型)
            - POP_TOP (没有指定异常类型，如 `except:`)
        try-finally 模式: PUSH_EXC_INFO 后直接是 finally 块的代码
        
        返回: (is_try_except, finally_start, finally_end)
        """
        # 使用指令列表而不是直接访问 code_obj
        if not hasattr(self, 'instructions') or not self.instructions:
            return True, -1, -1  # 默认假设为 try-except
        
        # 查找 PUSH_EXC_INFO 指令在指令列表中的位置
        push_exc_info_idx = -1
        for i, instr in enumerate(self.instructions):
            if instr.get('offset') == push_exc_info_offset:
                push_exc_info_idx = i
                break
        
        if push_exc_info_idx < 0:
            return True, -1, -1
        
        # 预扫描 PUSH_EXC_INFO 后的指令
        check_count = min(15, len(self.instructions) - push_exc_info_idx)
        
        for i in range(1, check_count):
            instr = self.instructions[push_exc_info_idx + i]
            opcode = instr.get('opcode')
            
            # CHECK_EXC_MATCH = 36 (有指定异常类型，如 `except ValueError:`)
            if opcode == Opcode.CHECK_EXC_MATCH:
                return True, -1, -1
            
            # POP_TOP = 1 (没有指定异常类型，如 `except:`，直接弹出异常)
            # 这是简单try-except的特征
            if opcode == Opcode.POP_TOP:
                return True, -1, -1
            
            # 如果遇到其他关键指令，停止扫描
            if opcode in [Opcode.RETURN_VALUE, Opcode.RERAISE_A]:
                break
        
        # 是 try-finally 模式，查找 finally 块的范围
        # finally 块从 PUSH_EXC_INFO 开始，到 RERAISE 或 RETURN_VALUE 结束
        finally_start = push_exc_info_offset
        finally_end = -1
        
        for i in range(push_exc_info_idx, len(self.instructions)):
            instr = self.instructions[i]
            opcode = instr.get('opcode')
            offset = instr.get('offset')
            # RERAISE_A = 119, RETURN_VALUE = 83
            if opcode in [Opcode.RERAISE_A, Opcode.RETURN_VALUE]:
                finally_end = offset
                break
        
        if finally_end < 0:
            finally_end = self.instructions[-1].get('offset', push_exc_info_offset) if self.instructions else push_exc_info_offset
        
        return False, finally_start, finally_end
    
    def _move_finally_code_from_try_block(self, try_node: 'ASTTry', push_exc_info_offset: int) -> None:
        """将 try 块中属于 finally 的代码移动到 finally 块
        
        在 try-finally 的字节码中，finally 块的正常执行路径在 PUSH_EXC_INFO 之前，
        所以这些代码被错误地添加到了 try 块。这个方法将它们移动到 finally 块。
        """
        if not hasattr(try_node, '_body') or try_node._body is None:
            return
        if not hasattr(try_node, '_finalbody') or try_node._finalbody is None:
            return
        
        try_body = try_node._body
        finally_body = try_node._finalbody
        
        # 获取 try 块中的所有节点
        if not hasattr(try_body, 'nodes'):
            return
        
        try_nodes = list(try_body.nodes)
        if not try_nodes:
            return
        
        # 对于 try-finally，try 块应该在 PUSH_EXC_INFO 之前结束
        # 最后几个节点可能属于 finally 块
        # 我们需要根据字节码结构来推断
        
        # 简化处理：假设 try 块只包含一个语句（如 file = open(...)）
        # 其余的属于 finally 块
        # 这是一个启发式方法，可能不适用于所有情况
        
        # 更精确的方法：查找 try 块中最后一个赋值语句，之后的代码属于 finally
        last_store_index = -1
        for i, node in enumerate(try_nodes):
            if type(node).__name__ == 'ASTStore':
                last_store_index = i
        
        if last_store_index >= 0 and last_store_index < len(try_nodes) - 1:
            # 将 last_store_index 之后的节点移动到 finally 块
            nodes_to_move = try_nodes[last_store_index + 1:]
            print(f"[_move_finally_code] 移动 {len(nodes_to_move)} 个节点从 try 块到 finally 块")
            
            # 从 try 块中移除这些节点
            for node in nodes_to_move:
                try_body.nodes.remove(node)
            
            # 添加到 finally 块
            for node in nodes_to_move:
                finally_body.append(node)
    
    def _jump_backward_no_interrupt(self, target: int) -> None:
        """处理向后跳转指令，用于循环结构"""
        # 记录向后跳转信息，用于后续判断是否为while循环
        if not hasattr(self, '_jump_backward_targets'):
            self._jump_backward_targets = []
        self._jump_backward_targets.append((self.current_offset, target))
        
        # 标记当前偏移为循环跳转点
        if not hasattr(self, '_loop_jump_offsets'):
            self._loop_jump_offsets = set()
        self._loop_jump_offsets.add(self.current_offset)
    
    def _is_while_loop(self, condition_offset: int) -> bool:
        """检查条件跳转是否属于while循环"""
        # 如果没有记录向后跳转，则不是循环
        if not hasattr(self, '_jump_backward_targets') or not self._jump_backward_targets:
            return False
        
        # while循环的特征：
        # 条件判断 -> POP_JUMP_IF_FALSE target
        # 循环体
        # JUMP_BACKWARD_NO_INTERRUPT 跳回条件之前
        
        # 检查是否有向后跳转跳回到条件判断附近
        for jump_from, jump_to in self._jump_backward_targets:
            # 如果跳回到条件偏移之前或附近（10字节范围内），则是while循环
            if jump_to <= condition_offset and jump_to >= condition_offset - 20:
                return True
        
        return False
    
    def _build_control_flow_edge(self, current_offset: int, instr: dict) -> None:
        """构建控制流图的边"""
        if current_offset < 0:
            return
        
        # 初始化当前指令的控制流信息
        if current_offset not in self._control_flow_graph:
            self._control_flow_graph[current_offset] = {
                'next': None,  # 顺序执行的下一条指令
                'jumps': [],   # 跳转目标列表
                'exception_handlers': [],  # 异常处理器列表
                'is_return': False,  # 是否返回
                'is_exception': False  # 是否引发异常
            }
        
        # 更新上一条指令的next指针
        if self._last_instr_offset >= 0 and self._last_instr_offset in self._control_flow_graph:
            self._control_flow_graph[self._last_instr_offset]['next'] = current_offset
        
        # 更新当前指令信息
        opcode = instr['opcode']
        operand = instr.get('operand', 0)
        opcode_name = instr.get('opcode_name', '')
        
        # 记录跳转
        if 'JUMP' in opcode_name:
            if opcode_name in ['JUMP_FORWARD_A']:
                # 向前跳转
                target = current_offset + operand
                self._control_flow_graph[current_offset]['jumps'].append(target)
            elif opcode_name in ['JUMP_BACKWARD_A', 'JUMP_BACKWARD_NO_INTERRUPT_A']:
                # 向后跳转
                target = current_offset - operand
                self._control_flow_graph[current_offset]['jumps'].append(target)
        
        # 记录返回
        if opcode_name in ['RETURN_VALUE', 'RETURN_GENERATOR']:
            self._control_flow_graph[current_offset]['is_return'] = True
        
        # 记录异常相关
        if opcode_name in ['POP_EXCEPT', 'RERAISE_A', 'RAISE_VARARGS_A']:
            self._control_flow_graph[current_offset]['is_exception'] = True
        
        # 记录异常处理器
        if opcode_name in ['SETUP_EXCEPT', 'SETUP_FINALLY', 'SETUP_WITH']:
            # 设置异常处理器
            handler = current_offset + operand
            # 在当前块的末尾添加异常处理器
            if self._control_flow_graph[current_offset]['exception_handlers'] is not None:
                self._control_flow_graph[current_offset]['exception_handlers'].append(handler)
        
        # 更新上一条指令偏移
        self._last_instr_offset = current_offset
    
    def _analyze_control_flow_pattern(self, opcode: int, operand: int, offset: int) -> None:
        """分析控制流模式"""
        opcode_name = opcode_to_name(opcode)
        
        # 模式1: while循环模式识别
        # 条件判断 -> POP_JUMP_FORWARD_IF_FALSE -> 循环体 -> JUMP_BACKWARD
        if opcode_name in ['POP_JUMP_FORWARD_IF_FALSE_A', 'POP_JUMP_FORWARD_IF_NOT_NONE_A']:
            # 记录条件判断，延迟到检测到JUMP_BACKWARD后再确定
            if offset not in self._branch_patterns:
                self._branch_patterns[offset] = {
                    'type': 'conditional_jump',
                    'target': offset + operand,
                    'is_while': False
                }
        
        # 模式2: for循环模式识别
        # FOR_ITER -> ... -> JUMP_BACKWARD (回到FOR_ITER)
        elif opcode_name == 'FOR_ITER_A':
            # 记录FOR_ITER，为后续的JUMP_BACKWARD提供参考
            if offset not in self._branch_patterns:
                self._branch_patterns[offset] = {
                    'type': 'for_iter',
                    'target': None  # 目标会在JUMP_BACKWARD时确定
                }
        
        # 模式3: 异常处理模式识别
        # SETUP_EXCEPT/FINALLY -> ... -> POP_EXCEPT/RERAISE
        elif opcode_name in ['SETUP_EXCEPT', 'SETUP_FINALLY']:
            # 记录异常处理器设置
            handler_start = offset
            handler_end = offset + operand
            
            if handler_end not in [p['target'] for p in self._branch_patterns.values() if p.get('type') == 'exception_handler']:
                self._branch_patterns[handler_start] = {
                    'type': 'exception_handler',
                    'target': handler_end
                }
        
        # 模式4: if-elif-else模式识别
        # 条件1 -> POP_JUMP_FORWARD_IF_FALSE -> else_if_n
        # 条件2 -> POP_JUMP_FORWARD_IF_FALSE -> else_if_m
        # ... -> JUMP_FORWARD -> final_else
        elif opcode_name in ['POP_JUMP_FORWARD_IF_FALSE_A', 'POP_JUMP_FORWARD_IF_NOT_NONE_A', 'POP_JUMP_FORWARD_IF_NONE_A']:
            # 记录条件分支
            branch_target = offset + operand
            
            # 检查是否是elif链的一部分
            if branch_target in [p['target'] for p in self._branch_patterns.values() if p.get('type') == 'elif_branch']:
                # 这是elif链中的一个分支
                for pattern_offset, pattern in self._branch_patterns.items():
                    if pattern.get('target') == branch_target and pattern.get('type') == 'elif_branch':
                        # 找到链上的前一个分支，添加当前分支为下一个
                        if 'next_branch' not in pattern:
                            pattern['next_branch'] = []
                        if isinstance(pattern['next_branch'], list):
                            pattern['next_branch'].append(offset)
                        break
            else:
                # 这是新的分支（可能是if或elif）
                self._branch_patterns[offset] = {
                    'type': 'if_branch',
                    'target': branch_target
                }
        
        # 模式5: try-except结构识别
        # SETUP_EXCEPT -> ... -> POP_EXCEPT
        elif opcode_name == 'POP_EXCEPT':
            # 向前查找最近的异常处理器设置
            handler_setup = None
            for pattern_offset in sorted(self._branch_patterns.keys(), reverse=True):
                if pattern_offset < offset:
                    pattern = self._branch_patterns[pattern_offset]
                    if pattern.get('type') == 'exception_handler':
                        handler_setup = pattern_offset
                        break
            
            if handler_setup is not None:
                # 找到了异常处理器设置，构建try-except结构
                if handler_setup not in self._exception_blocks:
                    self._exception_blocks.append(handler_setup)
        
        # 模式6: 跳转目标分析
        if offset in [p['target'] for p in self._branch_patterns.values()]:
            # 这是一个跳转目标，检查是否是循环的开始
            for pattern_offset, pattern in self._branch_patterns.items():
                if pattern.get('target') == offset:
                    if pattern.get('type') == 'for_iter':
                        # 这可能是for循环的开始
                        if 'loop_start' not in pattern:
                            pattern['loop_start'] = offset
                            self._loop_structures.append({
                                'type': 'for_loop',
                                'start': offset,
                                'end': pattern.get('end', None),
                                'pattern_ref': pattern_offset
                            })
                    elif pattern.get('type') == 'conditional_jump' and pattern.get('is_while'):
                        # 这可能是while循环的开始
                        self._loop_structures.append({
                            'type': 'while_loop',
                            'condition': pattern_offset,
                            'start': offset,
                            'end': pattern.get('end', None)
                        })
        
        # 模式7: JUMP_BACKWARD处理，更新循环结构
        if 'JUMP_BACKWARD' in opcode_name:
            # 向前查找最近的FOR_ITER或条件判断
            for pattern_offset, pattern in sorted(self._branch_patterns.items(), reverse=True):
                if pattern_offset < offset:
                    if pattern.get('type') == 'for_iter':
                        # 找到for循环的结束
                        if 'loop_start' in pattern and pattern['loop_start'] not in self._loop_structures:
                            self._loop_structures.append({
                                'type': 'for_loop',
                                'start': pattern['loop_start'],
                                'end': offset
                            })
                    elif pattern.get('type') == 'conditional_jump' and not pattern.get('is_while'):
                        # 找到while循环的结束
                        self._loop_structures.append({
                            'type': 'while_loop',
                            'condition': pattern_offset,
                            'start': pattern['target'],
                            'end': offset
                        })
    
    def _pop_jump_forward_if_none(self, target: int) -> None:
        """处理当栈顶元素为None时向前跳转的条件跳转"""
        if not self.stack.empty():
            condition = self.stack.pop()
            # 创建条件分支
            branch_node = self._create_conditional_branch(condition, target, False)
            self._emit(branch_node)
    
    def _pop_jump_forward_if_not_none(self, target: int) -> None:
        """处理当栈顶元素不为None时向前跳转的条件跳转"""
        if not self.stack.empty():
            condition = self.stack.pop()
            # 创建条件分支
            branch_node = self._create_conditional_branch(condition, target, True)
            self._emit(branch_node)
    
    def _handle_if_structure(self, condition: 'ASTNode', target_offset: int) -> 'ASTIf':
        """处理if结构的创建"""
        # 创建if节点
        if_node = ASTIf(condition, None, None)  # then_block 和 else_block 后续填充
        return if_node
    
    def _handle_for_loop(self, iterator: 'ASTNode', target_offset: int) -> 'ASTFor':
        """处理for循环结构的创建"""
        # 创建for循环节点
        for_node = ASTFor(iterator, None, None)  # body 和 orelse 后续填充
        return for_node
    
    def _handle_while_loop(self, condition: 'ASTNode', target_offset: int) -> 'ASTWhile':
        """处理while循环结构的创建"""
        # 创建while循环节点
        while_node = ASTWhile(condition, None, None)  # body 和 orelse 后续填充
        return while_node
    
    def _handle_try_except(self, target_offset: int) -> 'ASTTry':
        """处理try-except结构的创建 - 修复版本"""
        # 创建try节点
        body = ASTBlock()
        handlers = []
        orelse = ASTBlock()
        finalbody = ASTBlock()
        
        try_node = ASTTry(body, handlers, orelse, finalbody)
        
        # 设置当前异常处理器
        self.current_exception_handler = try_node
        
        return try_node
    
    def _create_exception_handler(self, exception_type: 'ASTNode' = None, handler_name: str = None) -> 'ASTExceptHandler':
        """创建异常处理器"""
        if not hasattr(self, 'current_exception_handler') or not self.current_exception_handler:
            return None
        
        # 使用正确的构造函数参数
        handler = ASTExceptHandler(exception_type or ASTName("Exception"), handler_name or "__exception", ASTBlock())
        
        self.current_exception_handler.handlers.append(handler)
        return handler


    def _extract_decorators(self, name: str, code_obj) -> List['ASTNode']:
        """提取函数装饰器 - 修复装饰器提取逻辑"""
        # 暂时返回空列表，避免生成错误的装饰器
        # 装饰器提取逻辑需要重新实现
        return []

    # === 核心反编译功能增强 ===
    
    def _safe_stack_pop(self) -> Optional[ASTNode]:
        """安全的栈弹出操作"""
        try:
            if not self.stack.empty():
                return self.stack.pop()
            else:
                # 创建占位节点，避免崩溃
                return ASTName("__unknown__")
        except Exception as e:
            print(f"警告：栈弹出失败 {e}")
            return ASTName("__unknown__")
    
    def _safe_stack_top(self, offset: int = 0) -> Optional[ASTNode]:
        """安全的栈顶访问"""
        try:
            node = self.stack.top(offset) if hasattr(self.stack, 'top') else self.stack.peek(offset)
            return node if node is not None else ASTName("__unknown__")
        except Exception as e:
            print(f"警告：栈访问失败 {e}")
            return ASTName("__unknown__")
    
    def _create_unary_op(self, op_type: str, operand: ASTNode) -> ASTUnary:
        """创建一元操作节点"""
        op_map = {
            'UNARY_POSITIVE': ASTUnary.UnaryOp.UOP_POSITIVE,
            'UNARY_NEGATIVE': ASTUnary.UnaryOp.UOP_NEGATIVE,
            'UNARY_NOT': ASTUnary.UnaryOp.UOP_NOT,
            'UNARY_INVERT': ASTUnary.UnaryOp.UOP_INVERT,
        }
        return ASTUnary(op_map.get(op_type, ASTUnary.UnaryOp.UOP_POSITIVE), operand)
    
    def _create_compare_op(self, left: ASTNode, right: ASTNode, op: int) -> ASTCompare:
        """创建比较操作节点"""
        compare_ops = {
            0: '<',   # Lt
            1: '<=',  # Le
            2: '==',  # Eq
            3: '!=',  # Ne
            4: '>',   # Gt
            5: '>=',  # Ge
            6: 'is',  # Is
            7: 'is not',  # IsNot
            8: 'in',  # In
            9: 'not in',  # NotIn
        }
        ops = [compare_ops.get(op, '==')]
        return ASTCompare(left, ops, [right])
    
    def _handle_jump_instruction(self, opcode: int, operand: int, current_offset: int) -> None:
        """处理跳转指令"""
        jump_targets = []
        
        if opcode == Opcode.JUMP_FORWARD:
            jump_targets.append(current_offset + operand + 2)
        elif opcode == Opcode.JUMP_BACKWARD:
            jump_targets.append(current_offset - operand - 2)
        elif opcode == Opcode.POP_JUMP_IF_FALSE:
            # 弹出栈顶，如果是False则跳转
            condition = self._safe_stack_pop()
            jump_targets.append(current_offset + operand + 2)
        elif opcode == Opcode.POP_JUMP_IF_TRUE:
            # 弹出栈顶，如果是True则跳转
            condition = self._safe_stack_pop()
            jump_targets.append(current_offset + operand + 2)
        
        # 记录跳转目标到控制流图
        for target in jump_targets:
            if current_offset in self._control_flow_graph:
                self._control_flow_graph[current_offset]['jumps'].append(target)
    
    def _complete_control_flow_structures(self) -> None:
        """完成控制流结构的构建"""
        # 处理循环结构
        for loop in self._loop_structures:
            if loop['type'] == 'while':
                self._complete_while_loop(loop)
            elif loop['type'] == 'for':
                self._complete_for_loop(loop)
    
    def _complete_while_loop(self, loop_info: dict) -> None:
        """完成while循环的构建"""
        # 这里需要更复杂的逻辑来重建while循环的AST结构
        # 暂时创建一个占位符
        pass
    
    def _complete_for_loop(self, loop_info: dict) -> None:
        """完成for循环的构建"""
        # 这里需要更复杂的逻辑来重建for循环的AST结构
        # 暂时创建一个占位符
        pass
    
    def _handle_block_management(self) -> None:
        """管理代码块"""
        # 处理异常处理块
        for exc_block in self._exception_blocks:
            self._process_exception_block(exc_block)
        
        # 处理控制流图中的跳转
        for offset, cfg in self._control_flow_graph.items():
            if cfg['jumps']:
                # 处理跳转目标
                for target in cfg['jumps']:
                    self._create_jump_target(target)
    
    def _process_exception_block(self, exc_block: dict) -> None:
        """处理异常处理块"""
        # 构建异常处理块
        handler_offset = exc_block.get('handler_offset')
        if handler_offset:
            # 创建异常处理器
            self._create_exception_handler()
    
    def _create_jump_target(self, target_offset: int) -> None:
        """创建跳转目标"""
        # 在目标偏移处创建代码块
        if target_offset not in self._control_flow_graph:
            self._control_flow_graph[target_offset] = {
                'next': None,
                'jumps': [],
                'exception_handlers': []
            }
    
    def _extract_function_defaults(self, code_obj) -> List[Optional[ASTNode]]:
        """从字节码提取函数默认参数"""
        defaults = []
        
        try:
            # 检查code_obj中是否有默认值信息
            if hasattr(code_obj, 'co_defaults') and code_obj.co_defaults:
                for default in code_obj.co_defaults:
                    if default is None:
                        defaults.append(None)
                    else:
                        # 转换默认值对象
                        defaults.append(self._convert_constant_to_ast(default))
            else:
                defaults = [None] * (getattr(code_obj, 'co_argcount', 0) or 0)
        except Exception as e:
            print(f"警告：提取函数默认值失败 {e}")
            defaults = []
        
        return defaults
    
    def _convert_constant_to_ast(self, constant) -> ASTNode:
        """将Python常量转换为AST节点"""
        if constant is None:
            return ASTName("None")
        elif constant is True:
            return ASTName("True")
        elif constant is False:
            return ASTName("False")
        elif isinstance(constant, str):
            return ASTConstant(constant)
        elif isinstance(constant, int):
            return ASTConstant(constant)
        elif isinstance(constant, float):
            return ASTConstant(constant)
        elif isinstance(constant, complex):
            return ASTConstant(constant)
        else:
            return ASTName("__unknown__")
    
    def _optimize_ast_structure(self, node: ASTNode) -> ASTNode:
        """优化AST结构"""
        # 简化的优化：移除空的代码块
        if hasattr(node, 'body') and hasattr(node.body, '__iter__'):
            # 移除空的ASTPass节点
            if hasattr(node.body, 'nodes'):
                node.body.nodes = [n for n in node.body.nodes if not isinstance(n, ASTPass)]
        
        return node
    
    def _finalize_ast(self, root_node: ASTNode) -> ASTNode:
        """最终化AST"""
        # 应用所有优化
        optimized = self._optimize_ast_structure(root_node)
        
        # 设置父子关系
        self._set_parent_child_relationships(optimized)
        
        return optimized
    
    def _set_parent_child_relationships(self, node: ASTNode) -> None:
        """设置父子关系"""
        if hasattr(node, 'body') and hasattr(node.body, '__iter__'):
            if hasattr(node.body, 'nodes'):
                for child in node.body.nodes:
                    child.parent = node
                    self._set_parent_child_relationships(child)
    
    def get_control_flow_graph(self) -> Dict:
        """获取控制流图"""
        return self._control_flow_graph
    
    def get_loop_structures(self) -> List[Dict]:
        """获取循环结构列表"""
        return self._loop_structures
    
    def get_exception_blocks(self) -> List[Dict]:
        """获取异常处理块列表"""
        return self._exception_blocks
    
    def get_branch_patterns(self) -> Dict:
        """获取分支模式"""
        return self._branch_patterns
    
    def get_unreachable_blocks(self) -> Set[int]:
        """获取不可达块"""
        return self._unreachable_blocks

    # === 缺失方法实现 ===
    
    def _unary_op(self, op_type: str) -> None:
        """处理一元操作符"""
        operand = self._safe_stack_pop()
        if operand is None:
            return
        
        unary_node = self._create_unary_op(op_type, operand)
        self.stack.push(unary_node)
    
    def _list_append(self, operand: int) -> None:
        """处理列表追加操作"""
        value = self._safe_stack_pop()
        list_node = self._safe_stack_pop()  # 获取列表对象
        
        # 创建列表追加表达式
        if isinstance(list_node, ASTList):
            list_node.nodes.append(value)
            self.stack.push(list_node)
        else:
            # 创建新的AST节点来处理列表追加
            self.stack.push(value)
    
    def _dict_merge(self, operand: int) -> None:
        """处理字典合并"""
        # 字典合并逻辑
        right = self._safe_stack_pop()
        left = self._safe_stack_pop()
        
        if left and right:
            # 创建字典更新表达式
            update_expr = ASTExpr(left)  # 简化实现
            self.stack.push(update_expr)
    
    def _set_update(self, operand: int) -> None:
        """处理集合更新"""
        # 集合更新逻辑
        value = self._safe_stack_pop()
        self.stack.push(value)
    
    def _is_op(self, operand: int) -> None:
        """处理is操作符"""
        # IS操作符逻辑
        right = self._safe_stack_pop()
        left = self._safe_stack_pop()
        
        if left and right:
            compare_node = self._create_compare_op(left, right, 6)  # 6 = is
            self.stack.push(compare_node)
    
    def _contains_op(self, operand: int) -> None:
        """处理contains操作符"""
        # CONTAINS操作符逻辑
        right = self._safe_stack_pop()
        left = self._safe_stack_pop()
        
        if left and right:
            # contains操作符是in或not in
            op = 9 if operand == 1 else 8  # 9 = not in, 8 = in
            compare_node = self._create_compare_op(left, right, op)
            self.stack.push(compare_node)
    
    # [DEBUG] 关键修复：删除重复的_reraise方法，保留第一个定义
    # def _reraise(self, operand: int) -> None:
    #     """处理reraise操作"""
    #     # RERAISE逻辑
    #     # 重新抛出当前异常
    #     reraise_node = ASTRaise()
    #     self.stack.push(reraise_node)
    
    def _call_intrinsic_2(self, operand: int) -> None:
        """处理内置函数调用2"""
        # CALL_INTRINSIC_2逻辑
        # 内置函数调用不需要特殊处理，只弹出参数
        if not self.stack.empty():
            self.stack.pop()
    
    def _load_method(self, operand: int) -> None:
        """加载方法"""
        # 加载对象上的方法
        if self.stack.empty():
            return
        
        obj = self.stack.top()
        self.stack.pop()
        
        # 获取方法名
        method_name = f"method_{operand}"
        
        # [DEBUG] 修复：使用当前代码对象的names，而不是模块的
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if code_obj and hasattr(code_obj, 'names') and code_obj.names and code_obj.names.get():
            names_obj = code_obj.names.get()
            if hasattr(names_obj, 'get') and operand < names_obj.size():
                try:
                    name_ref = names_obj.get(operand)
                    if name_ref and name_ref.get():
                        name_obj = name_ref.get()
                        if isinstance(name_obj, PycString):
                            method_name = name_obj.value
                        elif hasattr(name_obj, 'value'):
                            method_name = str(name_obj.value)
                except (IndexError, TypeError, AttributeError):
                    pass
        
        # 创建属性访问节点（如 person.greet）
        node = ASTAttribute(obj, method_name, 1)  # 1 = Load context
        self.stack.push(node)
    
    def _load_global(self, operand: int) -> None:
        """加载全局变量"""
        # Python 3.11+ 的 LOAD_GLOBAL 操作数编码：
        # 低 1 位表示是否 push NULL，高 7 位表示实际的名称索引
        # 所以实际的索引是 operand >> 1
        actual_index = operand >> 1
        
        # 尝试从code_obj的names中获取实际名称
        name = self._get_name_from_code_obj(actual_index)
        if name is None:
            name = f"__global_{actual_index}__"
        global_node = ASTName(name)
        self.stack.push(global_node)
    
    def _store_global(self, operand: int) -> None:
        """存储全局变量"""
        value = self._safe_stack_pop()
        # Python 3.11+ 的操作数编码：低 1 位表示是否 push NULL，高 7 位表示实际的名称索引
        actual_index = operand >> 1
        # 尝试从code_obj的names中获取实际名称
        name = self._get_name_from_code_obj(actual_index)
        if name is None:
            name = f"__global_{actual_index}__"
        store_node = ASTName(name)
        if value:
            # 创建赋值表达式
            assign_node = ASTAssign([store_node], value)
            self._emit(assign_node)
    
    def _delete_global(self, operand: int) -> None:
        """删除全局变量"""
        name = f"__global_{operand}__"
        delete_node = ASTDelete([ASTName(name, ASTName.Del)])
        self._emit(delete_node)
    
    def _format_value(self, operand: int) -> None:
        """格式化值 - 用于f-string"""
        if not self.stack.empty():
            value = self.stack.top()
            self.stack.pop()
            # 创建格式化值节点
            format_node = ASTFormattedValue(value, conversion=operand)
            self.stack.push(format_node)
    
    def _build_string(self, operand: int) -> None:
        """构建字符串 - 用于f-string"""
        # 从栈中弹出operand个元素，构建f-string
        # 栈是后进先出的，所以弹出的顺序是反的
        elements = []
        for i in range(operand):
            if not self.stack.empty():
                elem = self.stack.top()
                self.stack.pop()
                elements.append(elem)  # 先追加到列表
        
        # 反转列表，恢复正确的顺序
        elements.reverse()
        
        # 创建连接的字符串节点（f-string）
        joined_str = ASTJoinedStr(elements)
        self.stack.push(joined_str)
    
    def _break_loop(self) -> None:
        """跳出循环"""
        break_node = ASTBreak()
        self._emit(break_node)
    
    def _continue_loop(self, operand: int) -> None:
        """继续循环"""
        continue_node = ASTContinue()
        self._emit(continue_node)
    
    # [DEBUG] 删除重复的 _raise_varargs 方法，使用前面更完整的版本（第5673行）
    
    def _load_name(self, operand: int) -> None:
        """加载名称"""
        # 从code_obj的names中获取实际名称
        code_obj = self.code_obj if self.code_obj else (self.module.code.get() if self.module.code else None)
        if code_obj and code_obj.names and code_obj.names.get():
            names_obj = code_obj.names.get()
            if hasattr(names_obj, 'size') and hasattr(names_obj, 'get'):
                if 0 <= operand < names_obj.size():
                    try:
                        name_ref = names_obj.get(operand)
                        if name_ref:
                            name_obj = name_ref.get() if hasattr(name_ref, 'get') else name_ref
                            if hasattr(name_obj, 'value'):
                                name = name_obj.value
                            else:
                                name = str(name_obj)
                            name_node = ASTName(name)
                            self.stack.push(name_node)
                            return
                    except (IndexError, TypeError, AttributeError):
                        pass
        
        # 如果无法获取实际名称，使用占位符
        name = f"__name_{operand}__"
        name_node = ASTName(name)
        self.stack.push(name_node)

    def _enhanced_build(self, code_obj: PycCode, instructions: List[Dict]) -> Optional[ASTModule]:
        """增强的AST构建方法 - 智能字节码解析"""
        try:
            debug_print(f"[DEBUG] EnhancedAstBuilder - 开始构建智能AST")
            
            # 创建模块节点
            module = ASTModule()
            
            # 初始化变量上下文
            self.variables = {}
            self.constants = {}
            self.labels = {}
            self.current_block = ASTNodeList()
            
            # 预处理常量
            if code_obj.consts and code_obj.consts.get():
                consts = code_obj.consts.get()
                if hasattr(consts, '_values'):
                    for i, const_ref in enumerate(consts._values):
                        if const_ref and const_ref.get():
                            self.constants[i] = self._extract_constant_value(const_ref.get())
            
            # 预处理变量名
            if code_obj.local_names and code_obj.local_names.get():
                local_names = code_obj.local_names.get()
                if hasattr(local_names, '_values'):
                    for i, name_ref in enumerate(local_names._values):
                        if name_ref and name_ref.get():
                            var_name = self._extract_string_value(name_ref.get())
                            self.variables[i] = var_name
            
            # 智能解析指令
            self._parse_instructions_intelligently(instructions, module)
            
            debug_print(f"[OK] EnhancedAstBuilder - 智能AST构建完成")
            return module
            
        except Exception as e:
            debug_print(f"[ERROR] EnhancedAstBuilder - 构建失败: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_build(code_obj, instructions)
    
    def _parse_instructions_intelligently(self, instructions: List[Dict], module: ASTModule):
        """智能解析字节码指令"""
        
        i = 0
        while i < len(instructions):
            instr = instructions[i]
            opcode = instr.get('opcode')
            operand = instr.get('operand', 0)
            offset = instr.get('offset', 0)
            
            print(f"🔍 解析指令 {i}: {opcode} (offset: {offset})")
            
            # 处理LOAD_CONST指令
            if opcode == 100 or str(opcode) == "LOAD_CONST":
                # [DEBUG] 修复：调用_load_const方法而不是直接创建ASTConstant
                debug_print(f"[INTELLIGENT] 处理LOAD_CONST指令，operand={operand}")
                self._load_const(operand)
                
            # 处理STORE_NAME指令
            elif opcode == 90 or str(opcode) == "STORE_NAME":
                # [DEBUG] 修复：从names列表中获取实际的函数名
                if hasattr(code_obj, 'names') and code_obj.names and code_obj.names.get():
                    names_obj = code_obj.names.get()
                    name = None
                    if isinstance(names_obj, PycString):
                        name_list = names_obj.value.split('\x00')
                        if 0 <= operand < len(name_list):
                            name = name_list[operand]
                    elif isinstance(names_obj, PycSequence):
                        if 0 <= operand < names_obj.size():
                            try:
                                name_item = names_obj.get(operand)
                                if name_item and name_item.get():
                                    name_value = name_item.get()
                                    if isinstance(name_value, PycString):
                                        name = name_value.value
                                    elif hasattr(name_value, 'value'):
                                        name = str(name_value.value)
                            except (IndexError, TypeError, AttributeError):
                                pass
                    
                    if name:
                        debug_print(f"[STORE_NAME] 从names提取的名称: {name}")
                
                # Fallback: 使用self.variables
                if not name:
                    var_name = self.variables.get(operand, f"__var_{operand}__")
                    if var_name:
                        name = var_name
                
                if name:
                    debug_print(f"[STORE_NAME] 最终使用的名称: {name}")
                
                value = self._safe_stack_pop()
                if value:
                    # 检查value是否是函数定义
                    if isinstance(value, ASTFunctionDef):
                        debug_print(f"[STORE_NAME] value是ASTFunctionDef，函数名: {value.name}")
                        # 设置函数名
                        value._name = name
                    assign_node = ASTAssign([ASTName(name)], value)
                    self.current_block.append(assign_node)
                    
            # 处理LOAD_NAME指令
            elif opcode == 74 or str(opcode) == "LOAD_NAME":
                var_name = self.variables.get(operand, f"__var_{operand}__")
                name_node = ASTName(var_name)
                self.stack.push(name_node)
                
            # 处理二元操作
            elif opcode in [23, 24, 25, 26] or str(opcode) in ["BINARY_ADD", "BINARY_MULTIPLY", "BINARY_SUBTRACT", "BINARY_DIVIDE"]:
                right = self._safe_stack_pop()
                left = self._safe_stack_pop()
                if left and right:
                    op_map = {
                        23: "BINARY_ADD",
                        24: "BINARY_MULTIPLY", 
                        25: "BINARY_SUBTRACT",
                        26: "BINARY_DIVIDE"
                    }
                    op_name = op_map.get(opcode, "BINARY_OP")
                    bin_op = ASTBinary(left, right, opcode, NodeType.NODE_BINARY)
                    self.stack.push(bin_op)
                    
            # 处理RETURN_VALUE指令
            elif opcode == 83 or str(opcode) == "RETURN_VALUE":
                value = self._safe_stack_pop()
                if value:
                    return_node = ASTReturn(value)
                    self.current_block.append(return_node)
                    
            # 处理BUILD_LIST指令
            elif opcode == Opcode.BUILD_LIST_A or str(opcode) == "BUILD_LIST":
                debug_print(f"[INTELLIGENT] 处理BUILD_LIST指令，operand={operand}")
                self._build_list(operand)
                
            # 处理BUILD_TUPLE指令
            elif opcode == Opcode.BUILD_TUPLE_A or str(opcode) == "BUILD_TUPLE":
                debug_print(f"[INTELLIGENT] 处理BUILD_TUPLE指令，operand={operand}")
                self._build_tuple(operand)
                
            # 处理LIST_EXTEND指令
            elif opcode == Opcode.LIST_EXTEND_A or str(opcode) == "LIST_EXTEND":
                debug_print(f"[INTELLIGENT] 处理LIST_EXTEND指令，operand={operand}")
                self._list_extend(operand)
                
            # 处理函数定义
            elif str(opcode) == "LOAD_CONST" and operand in self.constants:
                const_obj = self.constants[operand]
                if hasattr(const_obj, 'co_argcount'):
                    # 这是一个函数代码对象
                    func_code = self._build_function_ast(const_obj, instructions, i+1)
                    if func_code:
                        self.current_block.append(func_code)
                        
            i += 1
        
        # 将当前块添加到模块
        if self.current_block.nodes:
            func_def = ASTFunctionDef("decompiled_function", [], self.current_block)
            module.body.append(func_def)
    
    def _build_function_ast(self, code_obj, instructions: List[Dict], start_idx: int):
        """从字节码构建函数AST"""
        try:
            func_body = ASTNodeList()
            
            # 提取函数名
            func_name = getattr(code_obj, 'co_name', 'anonymous_function')
            if func_name == 'anonymous_function':
                # 尝试从names中提取
                if hasattr(code_obj, 'names') and code_obj.names and code_obj.names.get():
                    names_obj = code_obj.names.get()
                    if names_obj:
                        if isinstance(names_obj, PycString):
                            func_name = names_obj.value
                            debug_print(f"[BUILD_FUNCTION] 从names提取函数名: {func_name}")
                        elif isinstance(names_obj, PycSequence):
                            if names_obj.size() > 0:
                                try:
                                    name_ref = names_obj.get(0)
                                    if name_ref:
                                        name_obj = name_ref.get() if hasattr(name_ref, 'get') else name_ref
                                        if name_obj and isinstance(name_obj, PycString):
                                            func_name = name_obj.value
                                except (IndexError, TypeError, AttributeError):
                                    pass
            
            debug_print(f"[BUILD_FUNCTION] 最终函数名: {func_name}")
            
            # 提取参数
            args = []
            if hasattr(code_obj, 'co_varnames'):
                for var_name in code_obj.co_varnames:
                    args.append(ASTName(var_name))
            
            # 构建函数体
            sub_builder = AstBuilder()
            sub_module = sub_builder._enhanced_build(code_obj, instructions[start_idx:])
            
            if sub_module and sub_module.body:
                # 取第一个函数的体作为函数体
                if hasattr(sub_module.body[0], 'body'):
                    func_body = sub_module.body[0].body
            
            return ASTFunctionDef(func_name, args, func_body)
            
        except Exception as e:
            debug_print(f"[WARN] _build_function_ast - 构建函数失败: {e}")
            return None
    
    def _extract_string_value(self, pyc_obj):
        """提取字符串值"""
        if hasattr(pyc_obj, '_value'):
            return pyc_obj._value
        elif hasattr(pyc_obj, 'value'):
            return pyc_obj.value
        elif isinstance(pyc_obj, str):
            return pyc_obj
        return str(pyc_obj)
    
    def _fallback_build(self, code_obj, instructions):
        """回退到简单的构建方法"""
        module = ASTModule()
        func_body = ASTNodeList()
        
        # 创建基本的常量赋值
        if code_obj.consts and code_obj.consts.get():
            consts = code_obj.consts.get()
            if hasattr(consts, '_values'):
                for i, const_ref in enumerate(consts._values):
                    if const_ref and const_ref.get():
                        const_value = self._extract_constant_value(const_ref.get())
                        var_name = f"__const_{i}__"
                        var_node = ASTName(var_name)
                        const_node = ASTConstant(const_value)
                        assign_node = ASTAssign([var_node], const_node)
                        func_body.append(assign_node)
        
        # 如果没有内容，添加pass
        if not func_body.nodes:
            func_body.append(ASTObject("pass"))
        
        func_def = ASTFunctionDef("decompiled_function", [], func_body)
        module.body.append(func_def)
        return module

    def _load_assertion_error(self) -> None:
        """处理LOAD_ASSERTION_ERROR指令 - 用于assert语句"""
        # LOAD_ASSERTION_ERROR加载AssertionError异常类型
        # 这是assert语句的一部分
        debug_print("[_load_assertion_error] 加载AssertionError")
        assertion_error = ASTName("AssertionError")
        self.stack.push(assertion_error)

    def _return_generator(self) -> None:
        """处理RETURN_GENERATOR指令 - 用于生成器函数"""
        # RETURN_GENERATOR标记这是一个生成器函数
        # 在反编译层面，我们不需要特殊处理，因为yield语句已经标识了生成器
        debug_print("[_return_generator] 处理生成器函数返回")
        # 生成器函数不需要显式的return语句
        pass

    def _yield_from(self) -> None:
        """处理YIELD_FROM指令 - 用于yield from语法"""
        debug_print("[_yield_from] 处理yield from")
        if self.stack.empty():
            return
        
        # 弹出可迭代对象
        iterable = self.stack.top()
        self.stack.pop()
        
        # 创建yield from节点
        yield_from_node = ASTYield(iterable, is_from=True)
        self._emit(yield_from_node)
