"""
AST生成器模块 V2 - 改进版

改进的AST生成器，提供更好的指令处理和表达式重建。
"""

import types
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from collections import deque

from .basic_block import BasicBlock, Instruction
from .cfg_builder import ControlFlowGraph
from .structured_analyzer import (
    ControlStructure, ControlStructureType,
    IfStructure, LoopStructure, TryExceptStructure, WithStructure,
    StructuredAnalyzer
)


class ExpressionReconstructor:
    """
    表达式重建器
    
    从字节码指令序列重建Python表达式。
    """
    
    def __init__(self, cfg=None):
        self.stack: List[Dict[str, Any]] = []
        self.temp_vars: Dict[str, Any] = {}
        self.temp_counter = 0
        self.last_instr_was_copy = False  # [海象运算符] 跟踪上一条指令是否是 COPY
        self.copy_depth = 0  # [海象运算符] COPY 指令的深度参数
        self.cfg = cfg  # [关键修复] 保存CFG引用，用于检查函数标志
    
    def reset(self):
        """重置状态"""
        self.stack = []
        self.temp_vars = {}
        self.temp_counter = 0
        self.last_instr_was_copy = False
        self.copy_depth = 0
    
    def reconstruct(self, instructions: List[Instruction], initial_stack: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """
        从指令序列重建表达式
        
        Args:
            instructions: 指令列表
            initial_stack: 初始栈状态，用于链式比较的后续条件块
            
        Returns:
            表达式AST
        """
        self.reset()
        
        # [关键修复] 如果有初始栈状态，使用它（用于链式比较）
        if initial_stack is not None:
            self.stack = initial_stack.copy()
        
        for instr in instructions:
            self._process_instruction(instr)
        
        # [关键修复] 返回栈上最后一个非PUSH_NULL元素
        # 栈上可能有PUSH_NULL标记，我们需要跳过它们
        if self.stack:
            for item in reversed(self.stack):
                if item.get('type') != 'PUSH_NULL':
                    return item
        return None
    
    def _process_instruction(self, instr: Instruction) -> None:
        """处理单条指令"""
        opname = instr.opname
        
        # [海象运算符] COPY 指令 - 复制栈顶值，用于 := 运算符
        # 必须在重置标志之前处理
        if opname == 'COPY':
            if self.stack:
                # COPY n 复制栈上第 n 个值（从栈顶开始计数，1表示栈顶）
                depth = instr.arg if instr.arg is not None else 1
                if depth == 1:
                    # 复制栈顶值，用于海象运算符
                    top_value = self.stack[-1]
                    self.stack.append(top_value.copy() if isinstance(top_value, dict) else top_value)
                    self.last_instr_was_copy = True
                    self.copy_depth = depth
                    return
                else:
                    # [关键修复] 对于 depth > 1 的 COPY 指令，用于链式比较
                    # 复制栈上深度为depth的元素
                    # depth=2: 复制栈顶第二个元素 (stack[-2])
                    # [关键修复] 检查栈中是否有足够的元素
                    if len(self.stack) >= depth:
                        self.stack.append(self.stack[-depth])
                    else:
                        # 栈中元素不足，创建一个占位符
                        # 这在链式比较的后续条件块中可能发生
                        self.stack.append({
                            'type': 'Name',
                            'id': f'<copy_placeholder_{depth}>',
                            'ctx': 'Load',
                            'lineno': instr.starts_line
                        })
                    return
        
        # [海象运算符] STORE 指令 - 检查是否是海象运算符模式
        if opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
            if self.stack:
                value = self.stack.pop()
                
                # [海象运算符] 如果上一条指令是 COPY，则生成 NamedExpr (:=)
                if self.last_instr_was_copy and self.copy_depth == 1:
                    self.stack.append({
                        'type': 'NamedExpr',
                        'target': {
                            'type': 'Name',
                            'id': instr.argval,
                            'ctx': 'Store',
                            'lineno': instr.starts_line
                        },
                        'value': value,
                        'lineno': instr.starts_line
                    })
                    self.last_instr_was_copy = False
                else:
                    # 普通赋值
                    self.stack.append({
                        'type': 'Assign',
                        'targets': [{
                            'type': 'Name',
                            'id': instr.argval,
                            'ctx': 'Store',
                            'lineno': instr.starts_line
                        }],
                        'value': value,
                        'lineno': instr.starts_line
                    })
            # 对于非栈操作的情况，也要重置标志
            self.last_instr_was_copy = False
            return
        
        # [海象运算符] 其他指令重置 COPY 标志
        self.last_instr_was_copy = False
        
        # 加载常量
        if opname in ('LOAD_CONST', 'LOAD_CONSTANT'):
            self.stack.append({
                'type': 'Constant',
                'value': instr.argval,
                'lineno': instr.starts_line
            })
        
        # [关键修复] PUSH_NULL - Python 3.11+ 的null推送，用于函数调用
        elif opname == 'PUSH_NULL':
            # PUSH_NULL 推送一个null值到栈上，用于标记函数调用的开始
            # 在表达式重建中，我们将其作为一个特殊标记处理
            self.stack.append({
                'type': 'PUSH_NULL',
                'value': None,
                'lineno': instr.starts_line
            })
        
        # 加载变量
        elif opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF'):
            self.stack.append({
                'type': 'Name',
                'id': instr.argval,
                'ctx': 'Load',
                'lineno': instr.starts_line
            })
        
        # 加载属性
        elif opname == 'LOAD_ATTR':
            if self.stack:
                value = self.stack.pop()
                self.stack.append({
                    'type': 'Attribute',
                    'value': value,
                    'attr': instr.argval,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })
        
        # [关键修复] 加载方法 (Python 3.11+)
        # LOAD_METHOD 将对象和方法名组合成属性访问
        elif opname == 'LOAD_METHOD':
            if self.stack:
                obj = self.stack.pop()
                # 将方法加载转换为属性访问
                self.stack.append({
                    'type': 'Attribute',
                    'value': obj,
                    'attr': instr.argval,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })
        
        # 二元操作 (Python 3.11+ 使用 BINARY_OP)
        elif opname == 'BINARY_OP':
            if len(self.stack) >= 2:
                right = self.stack.pop()
                left = self.stack.pop()
                # Python 3.11+ 中，BINARY_OP 的参数值决定操作符
                op = self._get_binary_op_from_arg(instr.argval)
                self.stack.append({
                    'type': 'BinOp',
                    'left': left,
                    'op': op,
                    'right': right,
                    'lineno': instr.starts_line
                })

        # 下标操作 (必须在通用 BINARY_ 处理之前)
        elif opname == 'BINARY_SUBSCR':
            if len(self.stack) >= 2:
                slice_val = self.stack.pop()
                value = self.stack.pop()
                self.stack.append({
                    'type': 'Subscript',
                    'value': value,
                    'slice': slice_val,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

        # [关键修复] BUILD_SLICE - 构建切片对象
        elif opname == 'BUILD_SLICE':
            argc = instr.arg if instr.arg is not None else 0
            if argc == 2 and len(self.stack) >= 2:
                # 两个参数: start:stop
                stop = self.stack.pop()
                start = self.stack.pop()
                self.stack.append({
                    'type': 'Slice',
                    'lower': start,
                    'upper': stop,
                    'step': None,
                    'lineno': instr.starts_line
                })
            elif argc == 3 and len(self.stack) >= 3:
                # 三个参数: start:stop:step
                step = self.stack.pop()
                stop = self.stack.pop()
                start = self.stack.pop()
                self.stack.append({
                    'type': 'Slice',
                    'lower': start,
                    'upper': stop,
                    'step': step,
                    'lineno': instr.starts_line
                })

        # 二元操作 (Python 3.8-3.10)
        # [关键修复] 排除 BINARY_SUBSCR，因为它已经作为下标操作处理
        elif (opname.startswith('BINARY_') or opname.startswith('INPLACE_')) and opname != 'BINARY_SUBSCR':
            if len(self.stack) >= 2:
                right = self.stack.pop()
                left = self.stack.pop()
                op = self._get_binary_op(opname)
                self.stack.append({
                    'type': 'BinOp',
                    'left': left,
                    'op': op,
                    'right': right,
                    'lineno': instr.starts_line
                })

        # 一元操作
        elif opname.startswith('UNARY_'):
            if self.stack:
                operand = self.stack.pop()
                op = self._get_unary_op(opname)
                self.stack.append({
                    'type': 'UnaryOp',
                    'op': op,
                    'operand': operand,
                    'lineno': instr.starts_line
                })

        # [关键修复] SWAP 指令 - Python 3.11+ 的栈交换指令，用于链式比较
        elif opname == 'SWAP':
            if self.stack and len(self.stack) >= 2:
                depth = instr.arg if instr.arg is not None else 1
                if depth == 2 and len(self.stack) >= 2:
                    # 交换栈顶的两个元素
                    self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]
        
        # [关键修复] COPY 指令 - Python 3.11+ 的复制指令，用于链式比较
        # 注意：这里的COPY不是海象运算符的COPY，而是用于链式比较的栈复制
        # COPY n 复制栈上深度为n的元素（从栈顶开始计数，1表示栈顶）
        elif opname == 'COPY':
            if self.stack:
                depth = instr.arg if instr.arg is not None else 1
                if depth >= 1 and depth <= len(self.stack):
                    # 复制栈上深度为depth的元素
                    # depth=1: 复制栈顶元素 (stack[-1])
                    # depth=2: 复制栈顶第二个元素 (stack[-2])
                    self.stack.append(self.stack[-depth])
        
        # 比较操作
        elif opname == 'COMPARE_OP':
            if len(self.stack) >= 2:
                right = self.stack.pop()
                left = self.stack.pop()
                op = self._get_compare_op(instr.argval)

                # [关键修复] 检测链式比较模式
                # 如果 left 是一个 Compare 节点，则合并为链式比较
                if left.get('type') == 'Compare':
                    # 链式比较：将当前比较添加到前一个比较中
                    # 前一个比较的最后一个比较器作为当前比较的左操作数
                    left['comparators'].append(right)
                    left['ops'].append(op)
                    self.stack.append(left)
                else:
                    self.stack.append({
                        'type': 'Compare',
                        'left': left,
                        'ops': [op],
                        'comparators': [right],
                        'lineno': instr.starts_line
                    })

        # [关键修复] CONTAINS_OP 指令 - Python 3.11+ 的成员运算符 (in/not in)
        elif opname == 'CONTAINS_OP':
            if len(self.stack) >= 2:
                right = self.stack.pop()
                left = self.stack.pop()
                # arg=0 表示 in, arg=1 表示 not in
                not_in = False
                if instr.arg is not None:
                    not_in = bool(instr.arg)
                elif instr.argval is not None:
                    not_in = bool(instr.argval)
                cmp_op = 'not in' if not_in else 'in'
                self.stack.append({
                    'type': 'Compare',
                    'left': left,
                    'ops': [cmp_op],
                    'comparators': [right],
                    'lineno': instr.starts_line
                })

        # 函数调用
        elif opname in ('CALL_FUNCTION', 'CALL', 'CALL_METHOD'):
            argc = instr.arg if instr.arg is not None else 0
            args = []
            kwargs = []
            
            # 弹出关键字参数
            # 注意：这里简化处理，实际应该解析kwargs
            
            # 弹出位置参数
            for _ in range(argc):
                if self.stack:
                    args.insert(0, self.stack.pop())
            
            # 弹出函数对象
            if self.stack:
                func = self.stack.pop()
                
                # [关键修复] 如果func是PUSH_NULL标记，跳过它并继续弹出真正的函数对象
                # Python 3.11+ 的函数调用栈布局: [PUSH_NULL, func, arg1, arg2, ...]
                while func and func.get('type') == 'PUSH_NULL':
                    if self.stack:
                        func = self.stack.pop()
                    else:
                        func = None
                        break
                
                if func:
                    self.stack.append({
                        'type': 'Call',
                        'func': func,
                        'args': args,
                        'kwargs': kwargs,
                        'lineno': instr.starts_line
                    })
        
        # 构建列表
        elif opname == 'BUILD_LIST':
            count = instr.arg if instr.arg is not None else 0
            elts = []
            for _ in range(count):
                if self.stack:
                    elts.insert(0, self.stack.pop())
            self.stack.append({
                'type': 'List',
                'elts': elts,
                'ctx': 'Load',
                'lineno': instr.starts_line
            })
        
        # 构建元组
        elif opname == 'BUILD_TUPLE':
            count = instr.arg if instr.arg is not None else 0
            elts = []
            for _ in range(count):
                if self.stack:
                    elts.insert(0, self.stack.pop())
            self.stack.append({
                'type': 'Tuple',
                'elts': elts,
                'ctx': 'Load',
                'lineno': instr.starts_line
            })
        
        # 构建字典
        elif opname == 'BUILD_MAP':
            count = instr.arg if instr.arg is not None else 0
            keys = []
            values = []
            for _ in range(count):
                if len(self.stack) >= 2:
                    values.insert(0, self.stack.pop())
                    keys.insert(0, self.stack.pop())
            self.stack.append({
                'type': 'Dict',
                'keys': keys,
                'values': values,
                'lineno': instr.starts_line
            })
        
        # [关键修复] LIST_EXTEND - Python 3.11+ 的列表扩展指令
        elif opname == 'LIST_EXTEND':
            if len(self.stack) >= 2:
                # 弹出要扩展的序列（元组、列表等）
                extend_values = self.stack.pop()
                # 弹出列表对象
                list_obj = self.stack.pop()
                # 创建一个新的列表，包含扩展后的元素
                elts = list_obj.get('elts', [])
                if extend_values.get('type') == 'Tuple' or extend_values.get('type') == 'Constant':
                    # 如果是元组或常量，提取其元素
                    extend_elts = extend_values.get('elts', [])
                    if not extend_elts and isinstance(extend_values.get('value'), (tuple, list)):
                        extend_elts = [{'type': 'Constant', 'value': v} for v in extend_values.get('value')]
                    elts = elts + extend_elts
                self.stack.append({
                    'type': 'List',
                    'elts': elts,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })
        
        # [关键修复] DICT_MERGE - Python 3.11+ 的字典合并指令（用于**kwargs）
        elif opname == 'DICT_MERGE':
            # DICT_MERGE用于合并字典，通常在CALL_FUNCTION_EX之前使用
            # 栈状态: [dict1, dict2] -> [merged_dict]
            if len(self.stack) >= 2:
                dict2 = self.stack.pop()
                dict1 = self.stack.pop()
                # 创建合并后的字典
                # 保留两个字典的引用，在代码生成时处理合并
                merged = {
                    'type': 'DictMerge',
                    'dict1': dict1,
                    'dict2': dict2,
                    'lineno': instr.starts_line
                }
                self.stack.append(merged)

        # 返回语句
        elif opname in ('RETURN_VALUE', 'RETURN_CONST'):
            if self.stack:
                value = self.stack.pop()
                self.stack.append({
                    'type': 'Return',
                    'value': value,
                    'lineno': instr.starts_line
                })
            else:
                self.stack.append({
                    'type': 'Return',
                    'value': None,
                    'lineno': instr.starts_line
                })
        
        # [关键修复] Python 3.11+ PRECALL 指令 - 预调用，不执行实际操作
        elif opname == 'PRECALL':
            # PRECALL 只是预调用指令，不改变栈状态
            pass
        
        # [关键修复] Python 3.11+ KW_NAMES 指令 - 关键字参数名称
        elif opname == 'KW_NAMES':
            # KW_NAMES 指定了关键字参数的名称
            # 存储在临时变量中，供后续的 CALL 指令使用
            self.temp_vars['kw_names'] = instr.argval
        
        # [关键修复] Python 3.11+ CALL 指令 - 函数调用
        elif opname == 'CALL':
            argc = instr.arg if instr.arg is not None else 0
            args = []
            kwargs = []
            
            # 从栈中弹出参数
            for _ in range(argc):
                if self.stack:
                    args.insert(0, self.stack.pop())
            
            # 弹出函数对象
            if self.stack:
                func = self.stack.pop()
                
                # [关键修复] 处理 PUSH_NULL 标记
                while func and func.get('type') == 'PUSH_NULL':
                    if self.stack:
                        func = self.stack.pop()
                    else:
                        func = None
                        break
                
                # [关键修复] 检查是否是推导式调用
                # 推导式调用的特点：argc=0且func是FunctionObject（推导式函数）
                if argc == 0 and func and func.get('type') == 'FunctionObject':
                    code_value = func.get('code')
                    
                    # 支持多种code存储格式
                    if isinstance(code_value, types.CodeType):
                        code_obj = code_value
                    elif isinstance(code_value, dict):
                        if code_value.get('type') == 'CodeObject':
                            code_obj = code_value.get('code')
                        elif code_value.get('type') == 'Constant':
                            code_obj = code_value.get('value')
                        else:
                            code_obj = None
                    else:
                        code_obj = None
                    
                    # [关键修复] ExpressionReconstructor 不处理推导式调用
                    # 推导式调用应该在 ASTGeneratorV2 中处理
                    # 这里简单地创建普通Call节点
                    if func:
                        self.stack.append({
                            'type': 'Call',
                            'func': func,
                            'args': args,
                            'kwargs': kwargs,
                            'lineno': instr.starts_line
                        })
                else:
                    # 不是推导式调用，创建普通Call
                    if func:
                        self.stack.append({
                            'type': 'Call',
                            'func': func,
                            'args': args,
                            'kwargs': kwargs,
                            'lineno': instr.starts_line
                        })
        
        # [关键修复] Python 3.11+ CALL_FUNCTION_EX 指令 - 扩展函数调用
        elif opname == 'CALL_FUNCTION_EX':
            # 处理 *args 和 **kwargs
            flags = instr.arg if instr.arg is not None else 0
            kwargs_dict = None
            args_obj = None
            
            # 如果设置了 CALL_FUNCTION_EX 标志，先弹出 kwargs
            if flags & 1:
                if self.stack:
                    kwargs_dict = self.stack.pop()
            
            # 弹出 args（可能是元组、Name或其他类型）
            if self.stack:
                args_obj = self.stack.pop()
            
            # 弹出函数对象
            if self.stack:
                func = self.stack.pop()
                while func and func.get('type') == 'PUSH_NULL':
                    if self.stack:
                        func = self.stack.pop()
                    else:
                        func = None
                        break
                
                if func:
                    # [关键修复] 处理args和kwargs
                    args = []
                    kwargs = []
                    
                    # 处理args_obj - 可能是Tuple、Name或其他类型
                    if args_obj:
                        if args_obj.get('type') == 'Tuple':
                            # 如果是元组，展开其元素作为位置参数
                            args = args_obj.get('elts', [])
                        elif args_obj.get('type') in ('Name', 'Constant'):
                            # 如果是变量名（如*args），保留为星号参数
                            args = [{'type': 'Starred', 'value': args_obj}]
                    
                    # 处理kwargs_dict - 可能是Dict、DictMerge或其他类型
                    if kwargs_dict:
                        if kwargs_dict.get('type') == 'Dict':
                            # 如果是字典，检查是否为空（BUILD_MAP 0的结果）
                            keys = kwargs_dict.get('keys', [])
                            values = kwargs_dict.get('values', [])
                            if len(keys) == 0:
                                # 空字典，可能是BUILD_MAP 0的结果
                                # 这种情况下kwargs实际上是单独的变量
                                pass
                            else:
                                # 非空字典，转换为关键字参数
                                for i, key in enumerate(keys):
                                    if i < len(values):
                                        kwargs.append({
                                            'type': 'keyword',
                                            'arg': key.get('value') if key.get('type') == 'Constant' else key,
                                            'value': values[i]
                                        })
                        
                        # 检查是否是DictMerge对象（DICT_MERGE指令的结果）
                        if kwargs_dict.get('type') == 'DictMerge':
                            # DictMerge包含dict1和dict2
                            # dict1是BUILD_MAP 0的结果（空字典）
                            # dict2是kwargs变量
                            dict2 = kwargs_dict.get('dict2')
                            if dict2 and dict2.get('type') == 'Name':
                                # 这是**kwargs模式
                                kwargs = [{'type': 'KeywordStarred', 'value': dict2}]
                        elif kwargs_dict.get('type') == 'Name':
                            # 如果是变量名，表示**kwargs
                            kwargs = [{'type': 'KeywordStarred', 'value': kwargs_dict}]
                    
                    self.stack.append({
                        'type': 'Call',
                        'func': func,
                        'args': args,
                        'kwargs': kwargs,
                        'lineno': instr.starts_line
                    })
        
        # [关键修复] Python 3.11+ CALL_METHOD 指令 - 方法调用
        elif opname == 'CALL_METHOD':
            argc = instr.arg if instr.arg is not None else 0
            args = []
            
            for _ in range(argc):
                if self.stack:
                    args.insert(0, self.stack.pop())
            
            # 弹出 self 和 方法
            if len(self.stack) >= 2:
                method = self.stack.pop()
                self_obj = self.stack.pop()
                
                # 创建方法调用
                if method and method.get('type') == 'Attribute':
                    self.stack.append({
                        'type': 'Call',
                        'func': method,
                        'args': args,
                        'kwargs': [],
                        'lineno': instr.starts_line
                    })
        
        # [关键修复] Python 3.11+ LOAD_ASSERTION_ERROR 指令
        elif opname == 'LOAD_ASSERTION_ERROR':
            self.stack.append({
                'type': 'Name',
                'id': 'AssertionError',
                'ctx': 'Load',
                'lineno': instr.starts_line
            })
        
        # [关键修复] Python 3.11+ RAISE 指令
        elif opname == 'RAISE':
            if self.stack:
                exc = self.stack.pop()
                self.stack.append({
                    'type': 'Raise',
                    'exc': exc,
                    'lineno': instr.starts_line
                })
        
        # [关键修复] Python 3.11+ RERAISE 指令
        elif opname == 'RERAISE':
            self.stack.append({
                'type': 'Reraise',
                'lineno': instr.starts_line
            })
        
        # [关键修复] RAISE_VARARGS 指令 (Python 3.8+)
        elif opname == 'RAISE_VARARGS':
            if instr.arg == 1:
                # RAISE_VARARGS 1: raise exception
                if self.stack:
                    exc = self.stack.pop()
                    self.stack.append({
                        'type': 'Raise',
                        'exc': exc,
                        'lineno': instr.starts_line
                    })
            elif instr.arg == 0:
                # RAISE_VARARGS 0: reraise current exception
                self.stack.append({
                    'type': 'Reraise',
                    'lineno': instr.starts_line
                })
        
        # [关键修复] Python 3.11+ CHECK_EXC_MATCH 指令
        elif opname == 'CHECK_EXC_MATCH':
            if len(self.stack) >= 2:
                exc_type = self.stack.pop()
                exc = self.stack.pop()
                self.stack.append({
                    'type': 'CheckExcMatch',
                    'exc': exc,
                    'exc_type': exc_type,
                    'lineno': instr.starts_line
                })
        
        # [关键修复] Python 3.11+ POP_EXCEPT 指令
        elif opname == 'POP_EXCEPT':
            pass  # 不改变栈状态
        
        # [关键修复] Python 3.11+ PUSH_EXC_INFO 指令
        elif opname == 'PUSH_EXC_INFO':
            pass  # 不改变栈状态
        
        # [关键修复] Python 3.11+ NOP 指令
        elif opname == 'NOP':
            pass  # 无操作
        
        # [关键修复] Python 3.11+ RESUME 指令
        elif opname == 'RESUME':
            pass  # 无操作，用于性能分析
        
        # [关键修复] Python 3.11+ CACHE 指令
        elif opname == 'CACHE':
            pass  # 无操作，用于缓存
        
        # [关键修复] Python 3.11+ FORMAT_VALUE 指令
        elif opname == 'FORMAT_VALUE':
            if self.stack:
                value = self.stack.pop()
                flags = instr.arg if instr.arg is not None else 0
                
                # 处理格式标志
                conversion = None
                if flags & 1:  # FVC_STR
                    conversion = 's'
                elif flags & 2:  # FVC_REPR
                    conversion = 'r'
                elif flags & 3:  # FVC_ASCII
                    conversion = 'a'
                
                # [关键修复] 处理格式说明符（format spec）
                # flags & 4 在Python 3.11+ 也表示有格式说明符
                format_spec = None
                if flags & 4 and self.stack:
                    # 格式说明符在栈上
                    format_spec_node = self.stack.pop()
                    if format_spec_node.get('type') == 'Constant':
                        format_spec = format_spec_node.get('value')
                
                formatted_value = {
                    'type': 'FormattedValue',
                    'value': value,
                    'conversion': conversion,
                    'format_spec': format_spec,
                    'lineno': instr.starts_line
                }
                
                # [关键修复] 只压入FormattedValue，不自动包装为JoinedStr
                # BUILD_STRING指令会处理多个部分的组合
                self.stack.append(formatted_value)
        
        # [关键修复] Python 3.11+ BUILD_STRING 指令
        elif opname == 'BUILD_STRING':
            count = instr.arg if instr.arg is not None else 0
            values = []
            for _ in range(count):
                if self.stack:
                    values.insert(0, self.stack.pop())
            
            self.stack.append({
                'type': 'JoinedStr',
                'values': values,
                'lineno': instr.starts_line
            })
        
        # [关键修复] Python 3.11+ IS_OP 指令
        elif opname == 'IS_OP':
            if len(self.stack) >= 2:
                right = self.stack.pop()
                left = self.stack.pop()
                # arg=0: is, arg=1: is not
                op = 'is not' if instr.arg == 1 else 'is'
                self.stack.append({
                    'type': 'Compare',
                    'left': left,
                    'ops': [op],
                    'comparators': [right],
                    'lineno': instr.starts_line
                })
        
        # [关键修复] Python 3.11+ MAKE_CELL 指令
        elif opname == 'MAKE_CELL':
            pass  # 不改变栈状态
        
        # [关键修复] Python 3.11+ COPY_FREE_VARS 指令
        elif opname == 'COPY_FREE_VARS':
            pass  # 不改变栈状态
        
        # [关键修复] Python 3.11+ MAKE_FUNCTION 指令
        elif opname == 'MAKE_FUNCTION':
            # MAKE_FUNCTION flags (Python 3.11+):
            # 0x01 (1): 有位置参数默认值 (tuple)
            # 0x02 (2): 有关键字-only参数默认值 (dict)
            # 0x04 (4): 有注解
            # 0x08 (8): 有闭包
            flags = instr.arg if instr.arg is not None else 0
            
            # 从栈中弹出code对象 (栈顶)
            if self.stack:
                code_value = self.stack.pop()
                
                # [关键修复] 处理默认值和注解 - 注意弹出顺序与压入顺序相反
                # 栈布局(从底到顶): [位置默认值, 关键字-only默认值, 注解元组, 闭包元组, code]
                kw_defaults = None  # flags & 2
                pos_defaults = None  # flags & 1
                annotations = None  # flags & 4
                closure = None  # flags & 8
                
                # flags & 8: 有闭包，从栈中弹出闭包元组
                if flags & 8:
                    if self.stack:
                        closure = self.stack.pop()
                
                # flags & 4: 有注解，从栈中弹出注解元组
                if flags & 4:
                    if self.stack:
                        annotations = self.stack.pop()
                
                # flags & 2: 有关键字-only参数默认值，从栈中弹出
                if flags & 2:
                    if self.stack:
                        kw_defaults = self.stack.pop()
                
                # flags & 1: 有位置参数默认值，从栈中弹出
                if flags & 1:
                    if self.stack:
                        pos_defaults = self.stack.pop()
                
                # 创建FunctionObject节点，包含默认值和注解信息
                func_obj = {
                    'type': 'FunctionObject',
                    'code': code_value,
                    'lineno': instr.starts_line
                }
                if pos_defaults:
                    func_obj['defaults'] = pos_defaults
                if kw_defaults:
                    func_obj['kw_defaults'] = kw_defaults
                if annotations:
                    func_obj['annotations'] = annotations
                if closure:
                    func_obj['closure'] = closure
                
                self.stack.append(func_obj)
    
    def _get_binary_op(self, opname: str) -> str:
        """获取二元操作符"""
        op_map = {
            'BINARY_ADD': '+',
            'BINARY_SUBTRACT': '-',
            'BINARY_MULTIPLY': '*',
            'BINARY_DIVIDE': '/',
            'BINARY_TRUE_DIVIDE': '/',
            'BINARY_FLOOR_DIVIDE': '//',
            'BINARY_MODULO': '%',
            'BINARY_POWER': '**',
            'BINARY_LSHIFT': '<<',
            'BINARY_RSHIFT': '>>',
            'BINARY_AND': '&',
            'BINARY_OR': '|',
            'BINARY_XOR': '^',
            'INPLACE_ADD': '+=',
            'INPLACE_SUBTRACT': '-=',
            'INPLACE_MULTIPLY': '*=',
        }
        return op_map.get(opname, opname)

    def _get_binary_op_from_arg(self, arg) -> str:
        """从 BINARY_OP 参数获取操作符 (Python 3.11+)
        
        [关键修复] 通过实际测试Python 3.11得到的正确映射
        """
        op_map = {
            0: '+',      # NB_ADD
            1: '&',      # NB_AND
            2: '//',     # NB_FLOOR_DIVIDE
            3: '<<',     # NB_LSHIFT
            4: '@',      # NB_MATRIX_MULTIPLY
            5: '*',      # NB_MULTIPLY
            6: '%',      # NB_REMAINDER
            7: '|',      # NB_OR
            8: '**',     # NB_POWER
            9: '>>',     # NB_RSHIFT
            10: '-',     # NB_SUBTRACT
            11: '/',     # NB_TRUE_DIVIDE
            12: '^',     # NB_XOR
        }
        if isinstance(arg, int):
            return op_map.get(arg, '+')
        elif isinstance(arg, str):
            try:
                num = int(arg.split()[0])
                return op_map.get(num, '+')
            except (ValueError, IndexError):
                pass
        return '+'

    def _get_unary_op(self, opname: str) -> str:
        """获取一元操作符"""
        op_map = {
            'UNARY_POSITIVE': '+',
            'UNARY_NEGATIVE': '-',
            'UNARY_NOT': 'not',
            'UNARY_INVERT': '~',
        }
        return op_map.get(opname, opname)
    
    def _get_compare_op(self, opname: str) -> str:
        """获取比较操作符"""
        op_map = {
            '<': '<',
            '>': '>',
            '==': '==',
            '!=': '!=',
            '<=': '<=',
            '>=': '>=',
            'in': 'in',
            'not in': 'not in',
            'is': 'is',
            'is not': 'is not',
            'exception match': 'exception match',
        }
        return op_map.get(opname, opname)
    
    def _load_instr_to_ast(self, instr) -> Dict[str, Any]:
        """将加载指令转换为AST节点"""
        opname = instr.opname
        if opname in ('LOAD_CONST', 'LOAD_CONSTANT'):
            return {
                'type': 'Constant',
                'value': instr.argval,
                'lineno': instr.starts_line
            }
        elif opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF'):
            return {
                'type': 'Name',
                'id': instr.argval,
                'ctx': 'Load',
                'lineno': instr.starts_line
            }
        else:
            # 默认返回一个占位符
            return {
                'type': 'Name',
                'id': f'<{opname}>',
                'ctx': 'Load',
                'lineno': instr.starts_line
            }


class ASTGeneratorV2:
    """
    改进的AST生成器
    
    提供更好的指令处理和表达式重建。
    """
    
    def __init__(self, cfg: ControlFlowGraph, recursive: bool = True):
        self.cfg = cfg
        self.structured_analyzer = StructuredAnalyzer(cfg)
        self.expr_reconstructor = ExpressionReconstructor(cfg)
        
        self.structures: List[ControlStructure] = []
        self.generated_blocks: Set[BasicBlock] = set()
        self.processed_structure_ids: Set[int] = set()  # [关键修复] 跟踪已处理的结构ID
        self.recursive = recursive  # 是否递归反编译嵌套函数
        self.current_block: Optional[BasicBlock] = None  # [关键修复] 当前处理的基本块
        self._unpack_state = None  # [关键修复] 解包赋值状态跟踪
        self._if_ast_cache: Dict[int, Dict[str, Any]] = {}  # [关键修复] 缓存已生成的if结构AST
        self._for_loop_ast_cache: Dict[int, Dict[str, Any]] = {}  # [关键修复] 缓存已生成的for循环AST
        self._has_return_generated: bool = False  # [关键修复] 跟踪是否已经生成了return语句
        self._loop_depth: int = 0  # [关键修复] 跟踪当前循环深度，用于break语句检测
    
    def generate(self) -> Dict[str, Any]:
        """生成AST"""
        # [关键修复] 检测推导式函数（<listcomp>, <dictcomp>, <setcomp>, <genexpr>）
        # 这些函数需要特殊处理，直接反编译为推导式表达式
        func_name = self.cfg.name
        if func_name in ('<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>'):
            return self._generate_comprehension_function()
        
        # [关键修复] 只有在structures为空时才调用analyze()
        # 这允许外部预先分析结构并传入
        if not self.structures:
            self.structures = self.structured_analyzer.analyze()

        ast_nodes = []

        # 按顺序处理：先处理入口块，然后处理结构
        entry_block = self.cfg.entry_block
        if entry_block and entry_block not in self.generated_blocks:
            # 处理入口块直到遇到结构化的控制流
            entry_ast = self._generate_entry_sequence(entry_block)
            if entry_ast:
                ast_nodes.append(entry_ast)

        # [关键修复] 按入口块偏移量排序结构，确保按代码顺序处理
        sorted_structures = sorted(
            self.structures,
            key=lambda s: s.entry_block.start_offset if s.entry_block else float('inf')
        )

        # 处理结构（按它们在代码中出现的顺序）
        # [关键修复] 只处理顶层结构，嵌套结构由父结构处理
        for struct in sorted_structures:
            # 检查结构是否已经被处理
            if id(struct) not in self.processed_structure_ids:
                # [关键修复] 检查结构的entry_block是否已经被标记为已生成
                # 如果是，说明该结构已经被其他结构处理过了，跳过
                # [关键修复] 但对于IfStructure和LoopStructure，即使entry_block已生成，也需要处理
                # 因为它们的entry_block在_generate_entry_sequence中被处理（生成初始化代码），
                # 但结构本身需要由对应的_generate_*_ast函数处理
                # [关键修复] 对于复合条件结构，即使entry_block已生成，也需要处理
                is_if_structure = isinstance(struct, IfStructure)
                is_loop_structure = isinstance(struct, LoopStructure)
                is_try_except_structure = isinstance(struct, TryExceptStructure)
                is_compound = getattr(struct, 'is_compound_condition', False)
                if hasattr(struct, 'entry_block') and struct.entry_block in self.generated_blocks and not is_if_structure and not is_loop_structure and not is_try_except_structure and not is_compound:
                    continue
                
                # [关键修复] 检查这个结构是否是其他if结构的elif_conditions的一部分
                is_elif_of_other = False
                if isinstance(struct, IfStructure):
                    for other_struct in self.structures:
                        if other_struct != struct and isinstance(other_struct, IfStructure):
                            if struct.entry_block in getattr(other_struct, 'elif_conditions', []):
                                is_elif_of_other = True
                                break
                
                # 如果是其他if结构的elif，跳过，由父结构处理
                if is_elif_of_other:
                    continue
                
                # [关键修复] 跳过SEQUENCE结构，因为它们通常是try-except结构的辅助结构
                # 或者已经被其他结构处理了
                if hasattr(struct, 'struct_type') and struct.struct_type == ControlStructureType.SEQUENCE:
                    # 检查是否是try-except结构的一部分
                    is_part_of_try_except = False
                    for other_struct in self.structures:
                        if isinstance(other_struct, TryExceptStructure):
                            if struct.entry_block in other_struct.try_body:
                                is_part_of_try_except = True
                                break
                    if is_part_of_try_except:
                        self.processed_structure_ids.add(id(struct))
                        continue
                
                # [关键修复] 对于TryExceptStructure，不再检查parent
                # 因为try-except结构应该被独立处理，即使它嵌套在循环或if中
                # 嵌套的try结构（try中包含try）仍然由父结构递归处理
                if isinstance(struct, TryExceptStructure):
                    # 只跳过真正的嵌套try（try中包含try）
                    if hasattr(struct, 'parent') and struct.parent is not None:
                        if isinstance(struct.parent, TryExceptStructure):
                            # 这是嵌套在另一个try中的try，由父结构处理
                            continue
                
                # [关键修复] 跳过属于TryExceptStructure的except handler的block
                # 这些block应该由_generate_try_except_ast处理，而不是作为独立结构处理
                if hasattr(struct, 'entry_block'):
                    is_except_handler_block = False
                    for other_struct in self.structures:
                        if isinstance(other_struct, TryExceptStructure):
                            for handler_info in other_struct.except_handlers:
                                if len(handler_info) == 3:
                                    _, _, handler_blocks = handler_info
                                else:
                                    _, handler_blocks = handler_info
                                if struct.entry_block in handler_blocks:
                                    is_except_handler_block = True
                                    break
                            if is_except_handler_block:
                                break
                    if is_except_handler_block:
                        self.processed_structure_ids.add(id(struct))
                        continue
                
                ast_result = self._generate_structure(struct)
                if ast_result:
                    if isinstance(ast_result, list):
                        ast_nodes.extend(ast_result)
                    else:
                        ast_nodes.append(ast_result)

        # 处理剩余的未处理块
        unprocessed = self._get_unprocessed_blocks()
        for block in unprocessed:
            ast_node = self._generate_block_sequence(block)
            if ast_node:
                ast_nodes.append(ast_node)

        # [关键修复] 后处理：合并复合条件
        # 复合条件如 x > 0 and y > 0 会被识别为多个if结构
        # 这里将它们合并为一个复合条件表达式
        # 注意：当前禁用复合条件合并，因为它会破坏AST结构
        # ast_nodes = self._merge_compound_conditions_in_ast(ast_nodes)

        # [关键修复] 检测是否是函数反编译（通过检查CFG是否有code属性）
        code_obj = getattr(self.cfg, 'code', None)
        
        # [关键修复] 使用code_obj.co_name而不是cfg.name来判断代码类型
        # cfg.name可能是传入的标签，而code_obj.co_name是代码对象的真实名称
        func_name = code_obj.co_name if code_obj else self.cfg.name
        
        # 检查是否是函数或类（排除模块、推导式等特殊名称）
        is_code_object = (code_obj and 
                         func_name not in ('<module>', '<listcomp>', '<dictcomp>', '<setcomp>', '<genexpr>', '<lambda>') and
                         not func_name.startswith('<'))
        
        if is_code_object:
            # [关键修复] 检测是类还是函数
            # 类定义的特点：
            # 1. argcount = 0（类定义没有参数）
            # 2. co_names 中包含 __module__, __qualname__（类定义使用这些特殊名称）
            # 3. co_flags = 0（类定义没有特殊的函数标志）
            is_class = False
            if code_obj:
                # 检查是否是类定义
                names = list(code_obj.co_names)
                has_class_attrs = '__module__' in names and '__qualname__' in names
                is_class = has_class_attrs and code_obj.co_argcount == 0 and code_obj.co_flags == 0
            
            if is_class:
                # [关键修复] 返回ClassDef节点
                return {
                    'type': 'ClassDef',
                    'name': func_name,
                    'body': ast_nodes,
                    'structures': len(self.structures),
                    'blocks': len(self.cfg.blocks)
                }
            else:
                # [关键修复] 检测异步函数
                is_async = False
                if code_obj:
                    # CO_COROUTINE = 128 (0x80), CO_ITERABLE_COROUTINE = 256 (0x100)
                    is_async = bool(code_obj.co_flags & 0x80) or bool(code_obj.co_flags & 0x100)
                
                # 获取函数参数
                args = []
                vararg = None
                kwarg = None
                if code_obj:
                    argcount = code_obj.co_argcount
                    varnames = list(code_obj.co_varnames)
                    args = varnames[:argcount]
                    
                    # [关键修复] 处理 *args 和 **kwargs
                    # CO_VARARGS = 0x04, CO_VARKEYWORDS = 0x08
                    has_varargs = bool(code_obj.co_flags & 0x04)
                    has_varkeywords = bool(code_obj.co_flags & 0x08)
                    
                    # 计算 *args 和 **kwargs 的位置
                    # 在 varnames 中，顺序是：普通参数, *args, **kwargs
                    if has_varargs and len(varnames) > argcount:
                        vararg = varnames[argcount]
                    if has_varkeywords and len(varnames) > argcount + (1 if has_varargs else 0):
                        kwarg_index = argcount + (1 if has_varargs else 0)
                        kwarg = varnames[kwarg_index]
                
                return {
                    'type': 'FunctionDef',
                    'name': func_name,
                    'args': args,
                    'vararg': vararg,
                    'kwarg': kwarg,
                    'body': ast_nodes,
                    'is_async': is_async,
                    'structures': len(self.structures),
                    'blocks': len(self.cfg.blocks)
                }
        
        # [关键修复] 获取原始常量池信息，用于保持字节码一致性
        code_obj = getattr(self.cfg, 'code', None)
        original_consts = None
        if code_obj and hasattr(code_obj, 'co_consts'):
            original_consts = list(code_obj.co_consts)
        
        return {
            'type': 'Module',
            'name': func_name,
            'body': ast_nodes,
            'structures': len(self.structures),
            'blocks': len(self.cfg.blocks),
            'original_consts': original_consts  # [关键修复] 保留原始常量池
        }

    def _get_used_const_indices(self) -> Set[int]:
        """
        [关键修复] 获取所有被使用的常量索引
        
        遍历所有指令，收集所有LOAD_CONST指令使用的常量索引。
        用于识别常量池中未使用的常量（如被优化掉的else分支中的常量）。
        
        Returns:
            被使用的常量索引集合
        """
        used_indices = set()
        
        for block in self.cfg.blocks:
            for instr in block.instructions:
                if instr.opname == 'LOAD_CONST':
                    if instr.arg is not None:
                        used_indices.add(instr.arg)
        
        return used_indices

    def _get_unused_consts(self) -> List[Any]:
        """
        [关键修复] 获取常量池中未使用的常量
        
        对比原始常量池和实际使用的常量，找出未使用的常量。
        这些常量可能来自被编译器优化掉的代码（如if True: ... else: ...中的else分支）。
        
        Returns:
            未使用的常量值列表
        """
        code_obj = getattr(self.cfg, 'code', None)
        if not code_obj or not hasattr(code_obj, 'co_consts'):
            return []
        
        original_consts = list(code_obj.co_consts)
        used_indices = self._get_used_const_indices()
        
        unused_consts = []
        for i, const in enumerate(original_consts):
            if i not in used_indices:
                # 跳过None（通常是返回值）和code对象
                if const is not None and not isinstance(const, types.CodeType):
                    unused_consts.append(const)
        
        return unused_consts

    def _merge_compound_conditions_in_ast(self, ast_nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        后处理：合并AST中的复合条件
        
        复合条件如 x > 0 and y > 0 会被识别为多个if结构。
        这个方法检测这些模式并将它们合并为一个复合条件表达式。
        
        识别模式：
        - 连续的if节点，其中前一个的body只包含一个if节点
        - 且它们的orelse相同
        """
        if len(ast_nodes) < 2:
            return ast_nodes
        
        result = []
        i = 0
        while i < len(ast_nodes):
            node = ast_nodes[i]
            
            # 检查是否是if节点
            if node.get('type') == 'If':
                # 检查是否是复合条件的一部分
                # 模式：当前if的body只包含一个if节点，且它们的orelse相同
                merged = self._try_merge_compound_condition(ast_nodes, i)
                if merged:
                    result.append(merged['node'])
                    i = merged['next_index']
                    continue
            
            result.append(node)
            i += 1
        
        return result

    def _try_merge_compound_condition(self, ast_nodes: List[Dict[str, Any]], start_index: int) -> Optional[Dict[str, Any]]:
        """
        尝试从指定位置开始合并复合条件
        
        复合条件的特征：
        - 第一个if的body为空或只包含一个if节点
        - 第二个if的orelse包含实际的else分支
        - 或者：第一个if的orelse包含第二个if（elif链中的复合条件）
        
        [关键修复] 禁用此优化以提高字节码匹配率
        保持原始代码结构，不进行if合并
        
        Returns:
            {'node': 合并后的节点, 'next_index': 下一个处理的索引} 或 None
        """
        # [关键修复] 禁用嵌套if合并优化，保持原始代码结构以提高字节码匹配率
        return None
        
        # 以下代码被禁用以禁用if合并优化
        """
        if start_index >= len(ast_nodes):
            return None
        
        first_if = ast_nodes[start_index]
        if first_if.get('type') != 'If':
            return None
        
        # 检查是否有下一个if节点
        if start_index + 1 >= len(ast_nodes):
            return None
        
        second_if = ast_nodes[start_index + 1]
        if second_if.get('type') != 'If':
            return None
        
        # 检查是否是复合条件模式
        first_body = first_if.get('body', [])
        first_orelse = first_if.get('orelse', [])
        
        is_compound = False
        merged_body = None
        merged_orelse = None
        conditions = []
        
        # 模式1: 第一个if的body为空或只包含pass/return，第二个if有实际的body和orelse
        if len(first_body) == 0 or all(
            node.get('type') in ('Pass', 'Return') or 
            (node.get('type') == 'Expr' and node.get('value', {}).get('type') == 'Constant' and node.get('value', {}).get('value') is None)
            for node in first_body
        ):
            second_body = second_if.get('body', [])
            second_orelse = second_if.get('orelse', [])
            
            if len(second_body) > 0:
                is_compound = True
                conditions = [first_if.get('test'), second_if.get('test')]
                merged_body = second_body
                merged_orelse = second_orelse
        
        # 模式2: 第一个if的orelse包含第二个if（elif链中的复合条件）
        elif len(first_orelse) == 1 and first_orelse[0].get('type') == 'If':
            nested_if = first_orelse[0]
            if nested_if == second_if:
                is_compound = True
                conditions = [first_if.get('test'), second_if.get('test')]
                merged_body = second_if.get('body', [])
                merged_orelse = second_if.get('orelse', [])
        
        if not is_compound:
            return None
        
        # 检查是否有更多的条件（三重and等）
        i = start_index + 2
        while i < len(ast_nodes):
            next_if = ast_nodes[i]
            if next_if.get('type') != 'If':
                break
            
            # 检查是否是复合条件的一部分
            next_orelse = next_if.get('orelse', [])
            if next_orelse == merged_orelse:
                conditions.append(next_if.get('test'))
                i += 1
            else:
                break
        
        # 构建复合条件表达式
        merged_test = self._build_compound_test(conditions, 'And')
        
        # 构建合并后的if节点
        merged_if = {
            'type': 'If',
            'test': merged_test,
            'body': merged_body,
            'orelse': merged_orelse,
            'lineno': first_if.get('lineno')
        }
        
        return {'node': merged_if, 'next_index': i}
        """

    def _build_compound_test(self, conditions: List[Dict[str, Any]], op: str) -> Dict[str, Any]:
        """
        构建复合条件表达式
        
        Args:
            conditions: 条件列表
            op: 操作符（'And' 或 'Or'）
            
        Returns:
            BoolOp节点
        """
        if len(conditions) == 1:
            return conditions[0]
        
        return {
            'type': 'BoolOp',
            'op': op,
            'values': conditions,
            'lineno': conditions[0].get('lineno') if conditions else None
        }

    def _extract_function_args(self, code_obj: types.CodeType, defaults_tuple: tuple = None, kw_defaults_dict: dict = None, annotations: Any = None) -> Dict[str, Any]:
        """
        从code对象提取函数参数信息
        
        Args:
            code_obj: Python code对象
            defaults_tuple: 位置参数默认值元组（从MAKE_FUNCTION指令获取）
            kw_defaults_dict: 关键字-only参数默认值字典（从MAKE_FUNCTION指令获取）
            annotations: 类型注解元组或字典（从MAKE_FUNCTION指令获取）
            
        Returns:
            参数字典，包含args, defaults, kwonlyargs, kw_defaults, vararg, kwarg, returns
        """
        # CO_* flags
        CO_VARARGS = 0x0004
        CO_VARKEYWORDS = 0x0008
        
        args = []
        defaults = []
        kwonlyargs = []
        kw_defaults = []
        vararg = None
        kwarg = None
        
        # 获取参数名列表
        varnames = list(code_obj.co_varnames)
        argcount = code_obj.co_argcount
        posonlyargcount = code_obj.co_posonlyargcount if hasattr(code_obj, 'co_posonlyargcount') else 0
        kwonlyargcount = code_obj.co_kwonlyargcount if hasattr(code_obj, 'co_kwonlyargcount') else 0
        flags = code_obj.co_flags if hasattr(code_obj, 'co_flags') else 0
        
        # 提取位置参数（包括仅限位置参数）
        total_pos_args = posonlyargcount + argcount
        for i in range(total_pos_args):
            if i < len(varnames):
                args.append({
                    'type': 'arg',
                    'arg': varnames[i],
                    'lineno': 1
                })
        
        # [关键修复] 处理位置参数默认值
        # defaults对应最后argcount个参数中的后len(defaults)个
        if defaults_tuple:
            # 将默认值转换为AST节点
            for default_val in defaults_tuple:
                defaults.append({
                    'type': 'Constant',
                    'value': default_val,
                    'lineno': 1
                })
        
        # [关键修复] Python 3.11+ 的 varnames 顺序：
        # 1. 位置参数 (co_argcount 个)
        # 2. 关键字-only参数 (co_kwonlyargcount 个)
        # 3. *args (如果有 CO_VARARGS)
        # 4. **kwargs (如果有 CO_VARKEYWORDS)
        
        # 提取 *args (在关键字-only参数之后)
        if flags & CO_VARARGS:
            vararg_idx = total_pos_args + kwonlyargcount
            if vararg_idx < len(varnames):
                vararg = {
                    'type': 'arg',
                    'arg': varnames[vararg_idx],
                    'lineno': 1
                }
        
        # 提取仅限关键字参数 (在位置参数之后，*args之前)
        kw_start = total_pos_args
        for i in range(kwonlyargcount):
            idx = kw_start + i
            if idx < len(varnames):
                kwonlyargs.append({
                    'type': 'arg',
                    'arg': varnames[idx],
                    'lineno': 1
                })
        
        # [关键修复] 处理关键字-only参数默认值
        # kw_defaults_dict 是从 MAKE_FUNCTION 获取的字典 {参数名: 默认值}
        if kw_defaults_dict and isinstance(kw_defaults_dict, dict):
            for kwarg in kwonlyargs:
                kw_name = kwarg.get('arg', '')
                if kw_name in kw_defaults_dict:
                    default_val = kw_defaults_dict[kw_name]
                    kw_defaults.append({
                        'type': 'Constant',
                        'value': default_val,
                        'lineno': 1
                    })
        
        # [关键修复] 提取 **kwargs
        # Python 3.11+ 的 varnames 顺序：位置参数, 关键字-only参数, *args, **kwargs, 局部变量
        # **kwargs 的位置 = 位置参数 + 关键字-only参数 + (1 if *args else 0)
        if flags & CO_VARKEYWORDS:
            # 计算 **kwargs 的正确位置
            kwarg_idx = total_pos_args + kwonlyargcount
            if flags & CO_VARARGS:
                kwarg_idx += 1  # 跳过 *args
            
            if kwarg_idx < len(varnames):
                kwarg = {
                    'type': 'arg',
                    'arg': varnames[kwarg_idx],
                    'lineno': 1
                }
        
        # [关键修复] 处理类型注解
        # annotations 是一个元组，格式为 (name1, type1, name2, type2, ..., 'return', return_type)
        returns = None
        if annotations:
            if isinstance(annotations, dict) and annotations.get('type') == 'Tuple':
                # 从AST节点提取注解
                elts = annotations.get('elts', [])
                i = 0
                while i < len(elts) - 1:
                    name_node = elts[i]
                    type_node = elts[i + 1]
                    
                    # 获取参数名
                    if isinstance(name_node, dict):
                        if name_node.get('type') == 'Constant':
                            name = name_node.get('value')
                        else:
                            name = name_node.get('id') if name_node.get('type') == 'Name' else str(name_node)
                    else:
                        name = str(name_node)
                    
                    # 如果是 'return'，设置返回类型
                    if name == 'return':
                        returns = type_node
                    else:
                        # 为参数添加注解
                        # 查找对应的参数
                        for arg in args:
                            if arg.get('arg') == name:
                                arg['annotation'] = type_node
                                break
                        for kwarg in kwonlyargs:
                            if kwarg.get('arg') == name:
                                kwarg['annotation'] = type_node
                                break
                    
                    i += 2
        
        return {
            'args': args,
            'defaults': defaults,
            'kwonlyargs': kwonlyargs,
            'kw_defaults': kw_defaults,
            'vararg': vararg,
            'kwarg': kwarg,
            'returns': returns  # [关键修复] 添加返回类型注解
        }

    def _decompile_comprehension(self, code_obj: types.CodeType, iter_obj: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        反编译推导式 code 对象
        
        Args:
            code_obj: 推导式的 code 对象（<listcomp>, <setcomp>, <dictcomp>, <genexpr>）
            iter_obj: 迭代对象（如 range(10)）
            
        Returns:
            推导式的 AST 字典
        """
        import dis
        
        comp_name = code_obj.co_name
        
        # 获取推导式的变量名（通常是 .0）
        varnames = list(code_obj.co_varnames)
        if len(varnames) < 1:
            return None

        # [关键修复] 推导式的目标变量名确定
        # 如果 varnames 有多个元素，第二个元素是目标变量名
        # 如果只有一个元素（.0），需要从 STORE_FAST/STORE_DEREF 指令中提取
        if len(varnames) > 1:
            target_name = varnames[1]
        else:
            # 从字节码中提取目标变量名
            instructions = list(dis.get_instructions(code_obj))
            target_name = 'x'  # 默认值
            for instr in instructions:
                if instr.opname in ('STORE_FAST', 'STORE_DEREF', 'STORE_NAME'):
                    target_name = instr.argval
                    break

        # 创建目标表达式
        target = {
            'type': 'Name',
            'id': target_name,
            'ctx': 'Store',
            'lineno': 1
        }

        # [关键修复] 提取推导式的条件（ifs）
        ifs = self._extract_comprehension_ifs(code_obj, target_name)

        # [关键修复] 检查是否有 UNPACK_SEQUENCE 指令（表示多个迭代变量）
        instructions = list(dis.get_instructions(code_obj))
        has_unpack = any(instr.opname == 'UNPACK_SEQUENCE' for instr in instructions)
        
        if has_unpack and comp_name == '<dictcomp>':
            # 有 UNPACK_SEQUENCE，说明有多个迭代变量（如 k, v）
            # 查找所有的 STORE_FAST 指令来获取变量名
            store_vars = []
            for instr in instructions:
                if instr.opname == 'STORE_FAST' and instr.argval not in store_vars:
                    store_vars.append(instr.argval)
            
            if len(store_vars) >= 2:
                # 创建元组目标 (k, v)
                target = {
                    'type': 'Tuple',
                    'elts': [
                        {'type': 'Name', 'id': store_vars[0], 'ctx': 'Store', 'lineno': 1},
                        {'type': 'Name', 'id': store_vars[1], 'ctx': 'Store', 'lineno': 1}
                    ],
                    'ctx': 'Store',
                    'lineno': 1
                }
        
        # 创建生成器
        generators = [{
            'type': 'comprehension',
            'target': target,
            'iter': iter_obj,
            'ifs': ifs,
            'is_async': 0
        }]
        
        # 获取推导式的元素表达式（通过反编译 code 对象的字节码）
        # 对于列表推导式 [x**2 for x in range(10)]，元素是 x**2
        elt = self._extract_comprehension_element(code_obj, target_name)
        
        if comp_name == '<listcomp>':
            return {
                'type': 'ListComp',
                'elt': elt,
                'generators': generators,
                'lineno': 1
            }
        elif comp_name == '<setcomp>':
            return {
                'type': 'SetComp',
                'elt': elt,
                'generators': generators,
                'lineno': 1
            }
        elif comp_name == '<dictcomp>':
            key, value = self._extract_dict_comprehension_elements(code_obj, target_name)
            return {
                'type': 'DictComp',
                'key': key,
                'value': value,
                'generators': generators,
                'lineno': 1
            }
        elif comp_name == '<genexpr>':
            return {
                'type': 'GeneratorExp',
                'elt': elt,
                'generators': generators,
                'lineno': 1
            }
        
        return None
    
    def _extract_comprehension_ifs(self, code_obj: types.CodeType, target_name: str) -> List[Dict[str, Any]]:
        """
        [关键修复] 从推导式 code 对象中提取条件表达式（ifs）
        
        例如，对于 [x for x in range(20) if x % 2 == 0]，返回 [x % 2 == 0] 的 AST
        """
        import dis
        
        ifs = []
        instructions = list(dis.get_instructions(code_obj))
        
        # 查找 POP_JUMP_BACKWARD_IF_FALSE 或 POP_JUMP_IF_FALSE 指令
        # 这些指令表示推导式的条件
        for i, instr in enumerate(instructions):
            if instr.opname in ('POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                               'POP_JUMP_FORWARD_IF_FALSE'):
                # 条件表达式是在这个指令之前计算的
                # 从 STORE_FAST (target_name) 之后开始，到条件跳转指令之前
                cond_instrs = []
                store_idx = -1
                
                # 找到 STORE_FAST target_name 的位置
                for j, prev_instr in enumerate(instructions[:i]):
                    if prev_instr.opname in ('STORE_FAST', 'STORE_DEREF') and prev_instr.argval == target_name:
                        store_idx = j
                
                if store_idx >= 0:
                    # 提取条件指令（从 STORE_FAST 之后到条件跳转之前）
                    for j in range(store_idx + 1, i):
                        prev_instr = instructions[j]
                        # 排除循环相关的指令
                        if prev_instr.opname not in ('FOR_ITER', 'JUMP_BACKWARD', 'JUMP_FORWARD',
                                                      'GET_ITER', 'RETURN_VALUE', 'RESUME', 'CACHE'):
                            cond_instrs.append(prev_instr)
                
                if cond_instrs:
                    # 使用表达式重建器来解析条件指令
                    reconstructor = ExpressionReconstructor()
                    for cond_instr in cond_instrs:
                        reconstructor._process_instruction(cond_instr)
                    
                    if reconstructor.stack:
                        ifs.append(reconstructor.stack[-1])
        
        return ifs
    
    def _extract_comprehension_element(self, code_obj: types.CodeType, target_name: str) -> Dict[str, Any]:
        """
        从推导式 code 对象中提取元素表达式
        
        例如，对于 [x**2 for x in range(10)]，返回 x**2 的 AST
        对于嵌套列表推导式 [[row[i] for row in matrix] for i in range(len(matrix[0]))]，
        返回内层列表推导式的 AST
        """
        import dis
        import types
        
        # 获取推导式的字节码指令
        instructions = list(dis.get_instructions(code_obj))
        
        # 查找 LIST_APPEND/SET_ADD/MAP_ADD 指令
        # 元素表达式是在这个指令之前计算的
        for i, instr in enumerate(instructions):
            if instr.opname in ('LIST_APPEND', 'SET_ADD', 'YIELD_VALUE'):
                # 元素表达式是从开始到这里的所有指令（除了加载.0和迭代相关）
                expr_instrs = instructions[:i]
                
                # [关键修复] 检查是否是嵌套列表推导式
                # 嵌套列表推导式的模式：
                #   LOAD_CLOSURE <var> / BUILD_TUPLE / LOAD_CONST <code> / MAKE_FUNCTION / ... / CALL
                # 其中 LOAD_CONST 加载的是内层列表推导式的 code 对象
                # [关键修复] 对于嵌套推导式，我们需要返回外层推导式的元素，
                # 而不是直接返回内层推导式
                inner_comprehension = None
                for j, expr_instr in enumerate(expr_instrs):
                    if expr_instr.opname == 'LOAD_CONST':
                        const_val = expr_instr.argval
                        # 检查是否加载了 code 对象
                        if isinstance(const_val, types.CodeType):
                            # 检查是否是推导式（列表/集合/字典推导式或生成器表达式）
                            if const_val.co_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'):
                                # 这是嵌套推导式！递归反编译它
                                # 找到对应的迭代对象（在 MAKE_FUNCTION 之后，GET_ITER 之前）
                                iter_obj = None
                                for k in range(j + 1, len(expr_instrs)):
                                    if expr_instrs[k].opname == 'GET_ITER':
                                        # 迭代对象是 GET_ITER 之前的指令
                                        # [关键修复] 从 MAKE_FUNCTION 之后开始，因为 MAKE_FUNCTION 之前的指令是内层推导式的code对象
                                        # 找到 MAKE_FUNCTION 指令的位置
                                        make_function_idx = -1
                                        for m in range(j + 1, k):
                                            if expr_instrs[m].opname == 'MAKE_FUNCTION':
                                                make_function_idx = m
                                                break
                                        
                                        # 从 MAKE_FUNCTION 之后开始提取迭代对象
                                        start_idx = make_function_idx + 1 if make_function_idx >= 0 else j + 1
                                        iter_instrs = expr_instrs[start_idx:k]
                                        
                                        # 重建迭代对象表达式
                                        iter_reconstructor = ExpressionReconstructor()
                                        for iter_instr in iter_instrs:
                                            # [关键修复] 不要排除CALL/PRECALL指令，因为迭代对象可能是函数调用（如range(5)）
                                            if iter_instr.opname not in ('STORE_FAST', 'STORE_DEREF',
                                                                          'GET_ITER', 'FOR_ITER', 'RETURN_VALUE', 'POP_TOP',
                                                                          'RESUME', 'CACHE', 'MAKE_CELL', 'LOAD_CLOSURE',
                                                                          'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP', 'BUILD_TUPLE',
                                                                          'MAKE_FUNCTION'):
                                                iter_reconstructor._process_instruction(iter_instr)
                                        if iter_reconstructor.stack:
                                            iter_obj = iter_reconstructor.stack[-1]
                                        break
                                
                                # 递归反编译内层推导式
                                if iter_obj:
                                    inner_comp = self._decompile_comprehension(const_val, iter_obj)
                                    if inner_comp:
                                        # [关键修复] 不要直接返回，而是保存内层推导式
                                        # 继续处理外层推导式的其他指令
                                        inner_comprehension = inner_comp
                                        break
                
                # [关键修复] 如果找到了内层推导式，返回它作为元素
                # 这是嵌套推导式的正确处理方式
                if inner_comprehension:
                    return inner_comprehension
                
                # 使用表达式重建器来解析这些指令（非嵌套情况）
                # [关键修复] 不要排除LOAD_FAST和LOAD_DEREF，因为它们是变量加载指令
                # [关键修复] 排除BUILD_LIST/BUILD_SET/BUILD_MAP，因为它们会创建容器对象
                # [关键修复] 排除MAKE_FUNCTION/CALL，因为它们用于嵌套推导式
                reconstructor = ExpressionReconstructor()
                for expr_instr in expr_instrs:
                    if expr_instr.opname not in ('STORE_FAST', 'STORE_DEREF',
                                                  'GET_ITER', 'FOR_ITER', 'RETURN_VALUE', 'POP_TOP',
                                                  'RESUME', 'CACHE', 'MAKE_CELL', 'LOAD_CLOSURE',
                                                  'BUILD_LIST', 'BUILD_SET', 'BUILD_MAP', 'BUILD_TUPLE',
                                                  'MAKE_FUNCTION', 'CALL', 'PRECALL'):
                        reconstructor._process_instruction(expr_instr)
                
                if reconstructor.stack:
                    return reconstructor.stack[-1]
                
                # 如果无法解析，返回一个简单的表达式
                break
        
        # 默认返回目标变量本身
        return {
            'type': 'Name',
            'id': target_name,
            'ctx': 'Load',
            'lineno': 1
        }
    
    def _extract_dict_comprehension_elements(self, code_obj: types.CodeType, target_name: str) -> tuple:
        """
        从字典推导式 code 对象中提取 key 和 value 表达式
        
        例如，对于 {x: x**2 for x in range(5)}，返回 (x, x**2) 的 AST
        对于 {k: v for k, v in enumerate(...)}，返回 (k, v) 的 AST
        """
        import dis
        
        # 获取推导式的字节码指令
        instructions = list(dis.get_instructions(code_obj))
        
        # [关键修复] 检查是否有 UNPACK_SEQUENCE 指令（表示多个迭代变量）
        has_unpack = any(instr.opname == 'UNPACK_SEQUENCE' for instr in instructions)
        
        if has_unpack:
            # 有 UNPACK_SEQUENCE，说明有多个迭代变量（如 k, v）
            # 查找所有的 STORE_FAST 指令来获取变量名
            store_vars = []
            for instr in instructions:
                if instr.opname == 'STORE_FAST' and instr.argval not in store_vars:
                    store_vars.append(instr.argval)
            
            # 查找 MAP_ADD 指令
            for i, instr in enumerate(instructions):
                if instr.opname == 'MAP_ADD':
                    # key 和 value 在 MAP_ADD 之前被压入栈
                    # 使用表达式重建器来解析 key 和 value
                    expr_instrs = []
                    # 找到 POP_JUMP_BACKWARD_IF_FALSE 之后的指令（跳过条件表达式）
                    cond_jump_idx = -1
                    for j in range(i):
                        if instructions[j].opname in ('POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_IF_FALSE'):
                            cond_jump_idx = j
                    
                    # 从条件跳转之后开始收集指令
                    start_idx = cond_jump_idx + 1 if cond_jump_idx >= 0 else 0
                    for j in range(start_idx, i):
                        if instructions[j].opname not in ('STORE_FAST', 'STORE_DEREF',
                                                          'GET_ITER', 'FOR_ITER', 'RETURN_VALUE', 'POP_TOP',
                                                          'UNPACK_SEQUENCE', 'RESUME', 'CACHE',
                                                          'POP_JUMP_BACKWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                                                          'POP_JUMP_FORWARD_IF_FALSE', 'JUMP_BACKWARD'):
                            expr_instrs.append(instructions[j])
                    
                    reconstructor = ExpressionReconstructor()
                    for expr_instr in expr_instrs:
                        reconstructor._process_instruction(expr_instr)
                    
                    if len(reconstructor.stack) >= 2:
                        # 栈顶是 value，下面是 key
                        value = reconstructor.stack.pop()
                        key = reconstructor.stack.pop()
                        return key, value
                    
                    # 如果表达式重建失败，回退到原来的简单方法
                    load_vars = []
                    for j in range(i - 1, -1, -1):
                        if instructions[j].opname == 'LOAD_FAST':
                            load_vars.append(instructions[j].argval)
                        if len(load_vars) >= 2:
                            break
                    
                    if len(load_vars) >= 2:
                        # load_vars[0] 是 value，load_vars[1] 是 key（因为是逆序）
                        key = {
                            'type': 'Name',
                            'id': load_vars[1],
                            'ctx': 'Load',
                            'lineno': 1
                        }
                        value = {
                            'type': 'Name',
                            'id': load_vars[0],
                            'ctx': 'Load',
                            'lineno': 1
                        }
                        return key, value
        
        # 查找 MAP_ADD 指令（单变量情况）
        for i, instr in enumerate(instructions):
            if instr.opname == 'MAP_ADD':
                # key 和 value 在 MAP_ADD 之前被压入栈
                # 简化处理：使用表达式重建器
                expr_instrs = instructions[:i]
                
                reconstructor = ExpressionReconstructor()
                for expr_instr in expr_instrs:
                    # [关键修复] 字典推导式需要处理LOAD_FAST和LOAD_CONST来重建key和value
                    if expr_instr.opname not in ('STORE_FAST', 'STORE_DEREF',
                                                  'GET_ITER', 'FOR_ITER', 'RETURN_VALUE', 'POP_TOP',
                                                  'UNPACK_SEQUENCE', 'RESUME', 'CACHE'):
                        reconstructor._process_instruction(expr_instr)
                
                if len(reconstructor.stack) >= 2:
                    # 栈顶是 value，下面是 key
                    value = reconstructor.stack.pop()
                    key = reconstructor.stack.pop()
                    return key, value
                
                break
        
        # 默认返回目标变量作为 key 和 value
        key = {
            'type': 'Name',
            'id': target_name,
            'ctx': 'Load',
            'lineno': 1
        }
        value = {
            'type': 'Name',
            'id': target_name,
            'ctx': 'Load',
            'lineno': 1
        }
        return key, value

    def _generate_comprehension_function(self) -> Dict[str, Any]:
        """
        [关键修复] 生成推导式函数的AST
        
        推导式函数（<listcomp>, <dictcomp>, <setcomp>, <genexpr>）需要特殊处理，
        因为它们实际上是内部函数，但应该被反编译为推导式表达式。
        
        推导式函数的字节码结构：
        1. BUILD_LIST/BUILD_SET/BUILD_MAP 创建容器
        2. LOAD_FAST .0 加载隐式迭代器
        3. FOR_ITER 循环
        4. STORE_FAST 存储循环变量
        5. 元素表达式
        6. LIST_APPEND/SET_ADD/DICT_ADD 添加元素
        7. JUMP_BACKWARD 跳回循环
        8. RETURN_VALUE 返回容器
        """
        import dis
        
        func_name = self.cfg.name
        
        # 获取代码对象 - 需要从CFG中提取
        # CFG本身不包含代码对象，我们需要从原始函数获取
        # 这里我们直接从CFG的基本块中提取指令
        
        # 收集所有指令
        all_instructions = []
        for block in self.cfg.get_blocks_in_order():
            all_instructions.extend(block.instructions)
        
        # 按偏移量排序
        all_instructions.sort(key=lambda i: i.offset)
        
        # 查找目标变量名（从STORE_FAST指令）
        target_name = 'x'  # 默认值
        for instr in all_instructions:
            if instr.opname in ('STORE_FAST', 'STORE_DEREF', 'STORE_NAME'):
                if instr.argval != '.0':  # 排除隐式迭代器
                    target_name = instr.argval
                    break
        
        # 创建目标表达式
        target = {
            'type': 'Name',
            'id': target_name,
            'ctx': 'Store',
            'lineno': 1
        }
        
        # 创建迭代对象（使用占位符，实际使用时会被替换）
        iter_obj = {
            'type': 'Name',
            'id': '<iterator>',
            'ctx': 'Load',
            'lineno': 1
        }
        
        # 提取元素表达式
        # 推导式的元素表达式在STORE_FAST之后，LIST_APPEND/SET_ADD之前
        elt_instructions = []
        in_element = False
        for instr in all_instructions:
            if instr.opname in ('STORE_FAST', 'STORE_DEREF', 'STORE_NAME') and instr.argval == target_name:
                in_element = True
                continue
            if in_element:
                if instr.opname in ('LIST_APPEND', 'SET_ADD', 'MAP_ADD', 'DICT_ADD', 'YIELD_VALUE'):
                    break
                if instr.opname not in ('JUMP_BACKWARD', 'JUMP_FORWARD', 'FOR_ITER', 'RETURN_VALUE'):
                    elt_instructions.append(instr)
        
        # 重建元素表达式
        reconstructor = ExpressionReconstructor()
        elt = reconstructor.reconstruct(elt_instructions)
        
        if not elt:
            elt = {
                'type': 'Name',
                'id': target_name,
                'ctx': 'Load',
                'lineno': 1
            }
        
        # 创建生成器
        generators = [{
            'type': 'comprehension',
            'target': target,
            'iter': iter_obj,
            'ifs': [],
            'is_async': 0
        }]
        
        # 根据函数名创建对应的推导式AST
        if func_name == '<listcomp>':
            comp_ast = {
                'type': 'ListComp',
                'elt': elt,
                'generators': generators,
                'lineno': 1
            }
        elif func_name == '<setcomp>':
            comp_ast = {
                'type': 'SetComp',
                'elt': elt,
                'generators': generators,
                'lineno': 1
            }
        elif func_name == '<dictcomp>':
            # 字典推导式需要key和value
            # 简化处理：假设元素是一个元组
            comp_ast = {
                'type': 'DictComp',
                'key': elt,
                'value': elt,
                'generators': generators,
                'lineno': 1
            }
        elif func_name == '<genexpr>':
            comp_ast = {
                'type': 'GeneratorExp',
                'elt': elt,
                'generators': generators,
                'lineno': 1
            }
        else:
            comp_ast = elt
        
        # 返回Module结构，包含推导式作为返回值
        return {
            'type': 'Module',
            'name': func_name,
            'body': [{
                'type': 'Return',
                'value': comp_ast,
                'lineno': 1
            }],
            'structures': 0,
            'blocks': len(self.cfg.blocks),
            'is_comprehension': True  # 标记这是一个推导式函数
        }

    def _generate_entry_sequence(self, start_block: BasicBlock) -> Optional[Dict[str, Any]]:
        """生成入口块的AST序列，在遇到结构化的控制流之前停止"""
        statements = []
        current = start_block
        # [关键修复] 跨块共享的栈，用于处理逻辑表达式
        shared_stack = []

        while current and current not in self.generated_blocks:
            # [关键修复] 首先检查这个块是否是with结构的入口
            # 如果是，完全跳过该块的处理，让 _generate_with_ast 来处理
            is_with_entry = False
            for struct in self.structures:
                if isinstance(struct, WithStructure) and struct.entry_block == current:
                    is_with_entry = True
                    break
            
            if is_with_entry:
                # 这是with结构的入口，跳过该块，让with结构处理
                break

            # [关键修复] 检查这个块是否是try-except结构的入口
            # 如果是，只处理try范围之外的指令，try范围内的指令由_generate_try_except_ast处理
            is_try_except_entry = False
            try_struct_for_entry = None
            for struct in self.structures:
                if isinstance(struct, TryExceptStructure) and struct.entry_block == current:
                    is_try_except_entry = True
                    try_struct_for_entry = struct
                    break
            
            if is_try_except_entry and try_struct_for_entry:
                # [关键修复] 这是try-except结构的入口，只处理try范围之外的指令
                # try范围内的指令由_generate_try_except_ast处理
                try_start = try_struct_for_entry.try_start_offset
                try_end = try_struct_for_entry.try_end_offset
                
                # 过滤出try范围之外的指令（不包括NOP、RESUME、CACHE等填充指令）
                pre_try_instrs = [instr for instr in current.instructions 
                                  if instr.offset < try_start and 
                                  instr.opname not in ('NOP', 'RESUME', 'CACHE', 'PUSH_EXC_INFO', 'POP_EXCEPT', 'COPY', 'RERAISE')]
                
                if pre_try_instrs:
                    # 创建临时块来处理try范围之外的指令
                    temp_block = BasicBlock(current.start_offset)
                    temp_block.end_offset = try_start
                    temp_block.instructions = pre_try_instrs
                    temp_block.successors = []
                    temp_block.predecessors = current.predecessors
                    
                    # 生成try范围之外的指令的AST
                    block_ast = self._generate_block_content_v2(temp_block)
                    if block_ast:
                        if isinstance(block_ast, list):
                            statements.extend(block_ast)
                        else:
                            statements.append(block_ast)
                
                # 跳过该块，让try-except结构处理try范围内的指令
                break

            # 检查这个块是否是 for 循环的前驱块（包含 GET_ITER）
            is_for_predecessor = False
            for struct in self.structures:
                if (hasattr(struct, 'header_block') and 
                    struct.header_block in current.successors and
                    struct.struct_type == ControlStructureType.FOR_LOOP):
                    # 检查当前块是否包含 GET_ITER
                    if any(instr.opname == 'GET_ITER' for instr in current.instructions):
                        is_for_predecessor = True
                        break

            # [关键修复] 检查块是否只包含异常处理框架指令（清理代码）
            # 这些块不应该被生成
            is_cleanup_block = False
            if all(instr.opname in ('LOAD_CONST', 'STORE_FAST', 'DELETE_FAST', 'RERAISE', 'COPY', 'POP_EXCEPT', 'PUSH_EXC_INFO')
                   for instr in current.instructions):
                # 检查是否包含清理代码模式（LOAD_CONST None + STORE_FAST + DELETE_FAST）
                for i, instr in enumerate(current.instructions):
                    if instr.opname == 'LOAD_CONST' and instr.argval is None:
                        if i + 2 < len(current.instructions):
                            if (current.instructions[i + 1].opname == 'STORE_FAST' and
                                current.instructions[i + 2].opname == 'DELETE_FAST'):
                                is_cleanup_block = True
                                break
            
            if is_cleanup_block:
                # 这是清理代码块，标记为已处理并跳过
                self.generated_blocks.add(current)
                # 继续处理后继块
                if current.successors:
                    # [关键修复] successors是集合，不能直接用索引访问
                    current = next(iter(current.successors))
                else:
                    break
                continue
            
            # [关键修复] 检查这个块是否是某个"真实"结构的入口（跳过 SEQUENCE）
            # 如果是，我们不应该将块标记为已生成，让结构处理逻辑来处理
            is_structure_entry = False
            entry_structure = None
            for struct in self.structures:
                if struct.entry_block == current:
                    # 只考虑非 SEQUENCE 的结构
                    if struct.struct_type != ControlStructureType.SEQUENCE:
                        is_structure_entry = True
                        entry_structure = struct
                        break
            
            # [关键修复] 检查这个块是否是IfStructure的入口
            # 如果是，只生成条件之前的代码，然后停止
            # 让 _generate_if_ast 来处理if结构和条件之后的代码
            if is_structure_entry and isinstance(entry_structure, IfStructure):
                # [关键修复] 如果是复合条件，整个块都是条件的一部分，不应该提取pre_condition_instrs
                is_compound = getattr(entry_structure, 'is_compound_condition', False)
                
                # 找到条件跳转指令的位置
                jump_index = None
                for i, instr in enumerate(current.instructions):
                    if instr.opname in (
                        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                        'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                        'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'
                    ):
                        jump_index = i
                        break
                
                # 生成条件之前的代码（仅对非复合条件）
                if jump_index is not None and jump_index > 0 and not is_compound:
                    pre_condition_instrs = current.instructions[:jump_index]
                    content = self._generate_instructions_content(pre_condition_instrs)
                    if content:
                        filtered_content = self._filter_isolated_statements(content)
                        if filtered_content:
                            if isinstance(filtered_content, list):
                                statements.extend(filtered_content)
                            else:
                                statements.append(filtered_content)
                
                # [关键修复] 标记块为已生成，这样 _generate_if_ast 不会重复生成条件之前的代码
                self.generated_blocks.add(current)
                
                # 停止处理，让 _generate_if_ast 来处理if结构
                break
            
            # [关键修复] 检查当前块是否是某个while循环的init_block
            # 如果是，只生成初始化相关的指令，而不是整个块的内容
            is_while_init_block = False
            for struct in self.structures:
                if isinstance(struct, LoopStructure) and struct.struct_type == ControlStructureType.WHILE_LOOP:
                    if hasattr(struct, 'init_blocks') and current in struct.init_blocks:
                        is_while_init_block = True
                        break
            
            # [关键修复] 只有当块不是结构入口时才标记为已生成
            self.generated_blocks.add(current)
            
            if is_for_predecessor:
                # 这是 for 循环的前驱块，只生成非迭代器相关的语句
                content = self._generate_block_content_skip_iterator(current)
            elif is_while_init_block:
                # [关键修复] 这是while循环的初始化块，只生成初始化相关的指令
                content = self._generate_init_block_content(current)
            else:
                # [关键修复] 传递共享栈以支持跨块的逻辑表达式
                content = self._generate_block_content_v2(current, shared_stack)
            
            if content:
                # [关键修复] 过滤掉孤立的表达式语句（如单独的变量名、函数调用等）
                filtered_content = self._filter_isolated_statements(content)
                if filtered_content:
                    if isinstance(filtered_content, list):
                        statements.extend(filtered_content)
                    else:
                        statements.append(filtered_content)

            # [关键修复] 处理多后继块的情况
            # 如果当前块有多个后继，检查是否是条件结构的前驱
            # 如果是，我们已经处理了当前块的内容，应该停止
            # 条件分支的处理会由结构处理逻辑来完成
            if len(current.successors) > 1:
                # 检查是否是某个条件结构的入口块的前驱
                is_conditional_predecessor = False
                for struct in self.structures:
                    if struct.struct_type in (ControlStructureType.IF_THEN_ELSE, 
                                               ControlStructureType.IF_THEN):
                        if current in struct.entry_block.predecessors or struct.entry_block == current:
                            is_conditional_predecessor = True
                            break
                
                # [关键修复] 检查当前块是否是while循环的init_block
                # 如果是，停止处理，让while循环结构处理逻辑来处理
                is_while_init_block = False
                for struct in self.structures:
                    if isinstance(struct, LoopStructure) and struct.struct_type == ControlStructureType.WHILE_LOOP:
                        if hasattr(struct, 'init_blocks') and current in struct.init_blocks:
                            is_while_init_block = True
                            break
                
                # [关键修复] 对于WHILE_LOOP，不要在这里停止
                # 因为while循环的header块需要被标记为已生成，然后在_generate_loop_ast中处理
                # 如果在这里停止，header块不会被标记为已生成，导致循环被重复处理
                if is_conditional_predecessor or is_while_init_block:
                    # 这是条件结构的前驱或while循环的init_block，停止处理，让结构处理逻辑处理分支
                    break
                else:
                    # [关键修复] 检查是否是逻辑表达式 (and/or)
                    # 如果当前块以 JUMP_IF_FALSE_OR_POP 或 JUMP_IF_TRUE_OR_POP 结束
                    # 并且不是条件结构的前驱，那么可能是逻辑表达式
                    last_instr = current.instructions[-1] if current.instructions else None
                    if last_instr and last_instr.opname in ('JUMP_IF_FALSE_OR_POP', 'JUMP_IF_TRUE_OR_POP'):
                        # 这是逻辑表达式，需要特殊处理
                        # 找到 fall-through 块（即跳转目标之外的块）
                        jump_target = last_instr.argval
                        fall_through_block = None
                        for succ in current.successors:
                            if succ.start_offset != jump_target:
                                fall_through_block = succ
                                break
                        if fall_through_block:
                            # 继续处理 fall-through 块
                            current = fall_through_block
                            continue
                    # [关键修复] 检查当前块是否是LoopStructure的header块
                    # 如果是，不应该继续处理后继，因为后继是循环的body块和退出块
                    # 这些应该由_generate_loop_ast处理
                    is_loop_header = False
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure) and struct.header_block == current:
                            is_loop_header = True
                            break
                    
                    if is_loop_header:
                        # 这是循环的header块，停止处理，让_generate_loop_ast处理循环
                        break
                    
                    # 不是条件结构的前驱，也不是循环header，选择第一个后继继续
                    # 这通常发生在模块级别，函数定义之后还有其他代码
                    next_block = min(current.successors, key=lambda b: b.start_offset)
                    current = next_block
            elif len(current.successors) == 1:
                next_block = list(current.successors)[0]
                # [关键修复] 检查下一个块是否是某个结构的入口
                # 如果是，停止处理，让结构处理逻辑来处理
                is_next_structure_entry = False
                for struct in self.structures:
                    if struct.entry_block == next_block:
                        if struct.struct_type != ControlStructureType.SEQUENCE:
                            is_next_structure_entry = True
                            break
                if is_next_structure_entry:
                    break
                current = next_block
            else:
                break

        # [关键修复] 检查共享栈中是否有剩余的 Await 节点
        # 这在异步函数中很重要，await 表达式的值没有被赋给变量时需要作为 Expr 语句处理
        if shared_stack:
            for expr in shared_stack[:]:
                if expr.get('type') == 'Await':
                    statements.append({
                        'type': 'Expr',
                        'value': expr,
                        'lineno': expr.get('lineno')
                    })
                    shared_stack.remove(expr)
        
        if not statements:
            return None

        if len(statements) == 1:
            return statements[0]

        return {
            'type': 'Sequence',
            'statements': statements,
            'lineno': self._get_block_line(start_block)
        }
    
    def _generate_block_content_skip_iterator(self, block: BasicBlock) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """生成基本块内容的AST，跳过 for 循环的迭代器准备代码"""
        # [关键修复] 设置当前块，供continue检测使用
        self.current_block = block
        
        # 找到 GET_ITER 指令的位置
        get_iter_index = None
        for i, instr in enumerate(block.instructions):
            if instr.opname == 'GET_ITER':
                get_iter_index = i
                break
        
        if get_iter_index is not None:
            # [关键修复] 找到迭代器表达式的开始位置
            # 迭代器表达式通常以 LOAD_GLOBAL, LOAD_NAME, LOAD_FAST 等开始
            # 向前查找，直到找到非加载指令
            iterator_start = get_iter_index
            for i in range(get_iter_index - 1, -1, -1):
                if block.instructions[i].opname in ('LOAD_GLOBAL', 'LOAD_NAME', 'LOAD_FAST', 
                                                     'LOAD_ATTR', 'LOAD_METHOD', 'LOAD_DEREF'):
                    iterator_start = i
                elif block.instructions[i].opname in ('PRECALL', 'CALL', 'CALL_FUNCTION', 
                                                      'CALL_METHOD', 'CALL_KW'):
                    # 这些指令也是迭代器表达式的一部分
                    continue
                else:
                    # 找到了迭代器表达式的开始位置
                    break
            
            # 只跳过从 iterator_start  to get_iter_index 的指令
            # 保留 iterator_start 之前的指令
            # [关键修复] 保留 JUMP_IF_TRUE_OR_POP 和 JUMP_IF_FALSE_OR_POP 用于重建 and/or 表达式
            # [关键修复] 保留 JUMP_BACKWARD 用于 continue 检测
            non_jump_instrs = [
                instr for instr in block.instructions[:iterator_start]
                if instr.opname not in {
                    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                    'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                    'FOR_ITER', 'FOR_ITER_RANGE', 'GET_ITER'
                }
            ]
            # 添加 GET_ITER 之后的指令
            non_jump_instrs.extend([
                instr for instr in block.instructions[get_iter_index + 1:]
                if instr.opname not in {
                    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                    'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                    'FOR_ITER', 'FOR_ITER_RANGE', 'GET_ITER'
                }
            ])
        else:
            # 没有 GET_ITER，使用正常的过滤
            # [关键修复] 保留 JUMP_IF_TRUE_OR_POP 和 JUMP_IF_FALSE_OR_POP 用于重建 and/or 表达式
            # [关键修复] 保留 JUMP_BACKWARD 用于 continue 检测
            non_jump_instrs = [
                instr for instr in block.instructions
                if instr.opname not in {
                    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                    'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                    'FOR_ITER', 'FOR_ITER_RANGE', 'GET_ITER'
                }
            ]

        if not non_jump_instrs:
            return None

        # 使用栈模拟执行来处理指令
        statements = []
        stack = []
        last_was_copy = False  # [海象运算符] 跟踪上一条指令是否是 COPY
        copy_depth = 0  # [海象运算符] COPY 指令的深度参数

        for instr in non_jump_instrs:
            opname = instr.opname

            # 忽略 Python 3.11+ 的特殊指令
            if opname in ('RESUME', 'CACHE'):
                continue
            
            # [关键修复] PUSH_NULL - Python 3.11+ 的null推送
            if opname == 'PUSH_NULL':
                stack.append({
                    'type': 'Constant',
                    'value': None,
                    'lineno': instr.starts_line
                })
                last_was_copy = False
                continue
            
            # [关键修复] PRECALL - Python 3.11+ 的预调用指令，不修改栈
            if opname == 'PRECALL':
                last_was_copy = False
                continue
            
            # [关键修复] KW_NAMES - Python 3.11+ 的关键字参数名指令
            if opname == 'KW_NAMES':
                # 存储关键字参数名，供后续的 CALL 指令使用
                # instr.arg 是常量表索引，需要从 code.co_consts 中获取关键字参数名元组
                # [关键修复] instr.argval 可能是 <unknown>，需要使用 instr.arg 从常量表获取
                try:
                    if hasattr(self, 'cfg') and self.cfg and hasattr(self.cfg, 'code'):
                        kw_names = self.cfg.code.co_consts[instr.arg]
                        self._kw_names = kw_names
                    else:
                        # 备用方案：尝试使用 argval
                        self._kw_names = instr.argval
                except (IndexError, AttributeError):
                    self._kw_names = instr.argval
                last_was_copy = False
                continue
            
            # [关键修复] COPY - Python 3.11+ 的复制指令，用于海象运算符 (:=) 和链式比较
            # COPY 1 复制栈顶的值，用于在赋值的同时保留值在栈上
            # COPY 2 复制栈顶第二个值，用于链式比较
            if opname == 'COPY':
                if stack:
                    # COPY n 复制栈上第 n 个值（从栈顶开始计数，1表示栈顶）
                    depth = instr.arg if instr.arg is not None else 1
                    if depth >= 1 and depth <= len(stack):
                        # 复制栈上深度为depth的元素
                        value_to_copy = stack[-depth]
                        stack.append(value_to_copy.copy() if isinstance(value_to_copy, dict) else value_to_copy)
                        if depth == 1:
                            last_was_copy = True
                            copy_depth = depth
                continue

            # [关键修复] SWAP 指令 - Python 3.11+ 的栈交换指令，用于链式比较
            if opname == 'SWAP':
                if stack and len(stack) >= 2:
                    depth = instr.arg if instr.arg is not None else 1
                    if depth == 2 and len(stack) >= 2:
                        # 交换栈顶的两个元素
                        stack[-1], stack[-2] = stack[-2], stack[-1]
                last_was_copy = False
                continue

            # 存储指令（赋值）- 必须在重置标志之前处理
            if opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                if stack:
                    value = stack.pop()
                    
                    # [关键修复] 如果值是 BoolOpPending，需要与栈中下一个值合并
                    if value.get('type') == 'BoolOpPending' and stack:
                        right = stack.pop()
                        value = {
                            'type': 'BoolOp',
                            'op': value['op'],
                            'values': [value['left'], right],
                            'lineno': value.get('lineno')
                        }
                    
                    # [关键修复] 如果栈中有 BoolOpPending，需要与之合并
                    # 这发生在布尔表达式跨多个基本块时
                    if stack and stack[-1].get('type') == 'BoolOpPending':
                        bool_op_pending = stack.pop()
                        value = {
                            'type': 'BoolOp',
                            'op': bool_op_pending['op'],
                            'values': [bool_op_pending['left'], value],
                            'lineno': bool_op_pending.get('lineno')
                        }
                    
                    # [关键修复] 检查是否是类定义（通过CALL创建，且func是__build_class__）
                    if (value.get('type') == 'Call' and 
                        value.get('func', {}).get('id') == '__build_class__' and
                        len(value.get('args', [])) >= 2):
                        # 这是类定义
                        class_name_arg = value['args'][1] if len(value['args']) > 1 else None
                        if class_name_arg and class_name_arg.get('type') == 'Constant':
                            class_name = class_name_arg.get('value', instr.argval)
                        else:
                            class_name = instr.argval
                        
                        # 提取基类（从args[2]开始）
                        bases = []
                        for base_arg in value['args'][2:]:
                            if base_arg.get('type') == 'Name':
                                bases.append(base_arg)
                        
                        statements.append({
                            'type': 'ClassDef',
                            'name': class_name if isinstance(class_name, str) else instr.argval,
                            'bases': bases,
                            'keywords': [],
                            'body': [],
                            'decorator_list': [],
                            'lineno': instr.starts_line
                        })
                    # [关键修复] 检查是否是函数定义
                    elif value.get('type') == 'FunctionObject':
                        # 递归反编译函数体
                        func_code = value.get('code')
                        if isinstance(func_code, types.CodeType):
                            # 提取函数参数（包括类型注解）
                            args_info = self._extract_function_args(
                                func_code,
                                value.get('defaults'),
                                value.get('kw_defaults'),
                                value.get('annotations')  # [关键修复] 传递类型注解
                            )
                            
                            # 递归反编译函数体
                            from .cfg_builder import build_cfg
                            func_cfg = build_cfg(func_code, func_code.co_name)
                            func_generator = ASTGeneratorV2(func_cfg, recursive=self.recursive)
                            func_ast = func_generator.generate()
                            
                            # [关键修复] 提取并添加文档字符串
                            func_body = func_ast.get('body', [])
                            # Python 3.11+中，文档字符串存储在co_consts[0]，不再通过LOAD_CONST加载
                            if (func_code and hasattr(func_code, 'co_consts') and 
                                len(func_code.co_consts) > 0):
                                first_const = func_code.co_consts[0]
                                if isinstance(first_const, str) and first_const:
                                    # 检查文档字符串是否已经在body中
                                    docstring_in_body = False
                                    if func_body:
                                        first_stmt = func_body[0]
                                        if (first_stmt.get('type') == 'Expr' and
                                            first_stmt.get('value', {}).get('type') == 'Constant' and
                                            first_stmt.get('value', {}).get('value') == first_const):
                                            docstring_in_body = True
                                    
                                    if not docstring_in_body:
                                        # 添加文档字符串作为函数体的第一个语句
                                        docstring_node = {
                                            'type': 'Expr',
                                            'value': {
                                                'type': 'Constant',
                                                'value': first_const,
                                                'lineno': instr.starts_line
                                            },
                                            'lineno': instr.starts_line
                                        }
                                        func_body.insert(0, docstring_node)
                            
                            # [异步] 检测是否是异步函数
                            # CO_COROUTINE = 128 (0x80)
                            # CO_ITERABLE_COROUTINE = 256 (0x100)
                            is_async = False
                            if hasattr(func_code, 'co_flags'):
                                is_async = bool(func_code.co_flags & 0x80) or bool(func_code.co_flags & 0x100)
                            
                            # [关键修复] 从args_info中提取returns
                            returns = args_info.pop('returns', None) if isinstance(args_info, dict) else None
                            
                            # 创建函数定义AST
                            func_def = {
                                'type': 'FunctionDef',
                                'name': instr.argval,
                                'args': args_info,
                                'body': func_body,
                                'decorator_list': [],
                                'returns': returns,  # [关键修复] 添加返回类型注解
                                'is_async': is_async,  # [异步] 添加异步标志
                                'lineno': instr.starts_line
                            }
                            statements.append(func_def)
                        else:
                            # 无法获取code对象，创建简单的赋值
                            statements.append({
                                'type': 'Assign',
                                'targets': [{
                                    'type': 'Name',
                                    'id': instr.argval,
                                    'ctx': 'Store',
                                    'lineno': instr.starts_line
                                }],
                                'value': {'type': 'Constant', 'value': None},
                                'lineno': instr.starts_line
                            })
                    # [海象运算符] 如果上一条指令是 COPY，则生成 NamedExpr (:=)
                    elif last_was_copy and copy_depth == 1:
                        # 创建海象运算符表达式，但不作为独立语句
                        # 而是将 NamedExpr 压回栈中供后续使用
                        named_expr = {
                            'type': 'NamedExpr',
                            'target': {
                                'type': 'Name',
                                'id': instr.argval,
                                'ctx': 'Store',
                                'lineno': instr.starts_line
                            },
                            'value': value,
                            'lineno': instr.starts_line
                        }
                        stack.append(named_expr)
                        last_was_copy = False
                    else:
                        # [关键修复] 检查是否是增强赋值（AugAssign）
                        if value.get('type') == 'AugAssign':
                            # 增强赋值：total += item
                            statements.append({
                                'type': 'AugAssign',
                                'target': {
                                    'type': 'Name',
                                    'id': instr.argval,
                                    'ctx': 'Store',
                                    'lineno': instr.starts_line
                                },
                                'op': value.get('op', '+='),
                                'value': value.get('value'),
                                'lineno': instr.starts_line
                            })
                        else:
                            statements.append({
                                'type': 'Assign',
                                'targets': [{
                                    'type': 'Name',
                                    'id': instr.argval,
                                    'ctx': 'Store',
                                    'lineno': instr.starts_line
                                }],
                                'value': value,
                                'lineno': instr.starts_line
                            })
                last_was_copy = False
                continue  # 已经处理，跳过下面的代码
            
            # [海象运算符] 其他指令重置 COPY 标志
            last_was_copy = False

            # 加载常量
            if opname in ('LOAD_CONST', 'LOAD_CONSTANT'):
                # [关键修复] 检查是否是code对象（函数或类定义）
                if isinstance(instr.argval, types.CodeType):
                    # 这是函数或类的code对象，保留原始code对象
                    stack.append({
                        'type': 'CodeObject',
                        'code': instr.argval,
                        'lineno': instr.starts_line
                    })
                else:
                    stack.append({
                        'type': 'Constant',
                        'value': instr.argval,
                        'lineno': instr.starts_line
                    })

            # 加载变量
            elif opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF'):
                stack.append({
                    'type': 'Name',
                    'id': instr.argval,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # [关键修复] 加载类构建器 - LOAD_BUILD_CLASS的argval是None
            elif opname == 'LOAD_BUILD_CLASS':
                stack.append({
                    'type': 'Name',
                    'id': '__build_class__',
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # 二元操作 (Python 3.11+)
            elif opname == 'BINARY_OP':
                if len(self.stack) >= 2:
                    right = self.stack.pop()
                    left = self.stack.pop()
                    # [关键修复] 使用instr.arg而不是instr.argval
                    op_arg = instr.arg if instr.arg is not None else 0
                    op = self._get_binary_op_from_arg(op_arg)
                    
                    # [关键修复] 检查是否是增强赋值操作符 (13-25)
                    if instr.arg is not None and instr.arg >= 13:
                        # 增强赋值：+=, -=, *=, 等
                        self.stack.append({
                            'type': 'AugAssign',
                            'target': left,
                            'op': op,
                            'value': right,
                            'lineno': instr.starts_line
                        })
                    else:
                        # 普通二元操作
                        self.stack.append({
                            'type': 'BinOp',
                            'left': left,
                            'op': op,
                            'right': right,
                            'lineno': instr.starts_line
                        })

            # 二元操作 (Python 3.8-3.10)
            # [关键修复] 排除 BINARY_SUBSCR，它应该作为下标操作处理
            elif opname.startswith('BINARY_') and opname != 'BINARY_SUBSCR':
                if len(self.stack) >= 2:
                    right = self.stack.pop()
                    left = self.stack.pop()
                    op = self._get_binary_op(opname)
                    self.stack.append({
                        'type': 'BinOp',
                        'left': left,
                        'op': op,
                        'right': right,
                        'lineno': instr.starts_line
                    })

            # [关键修复] BINARY_SUBSCR - 下标操作
            elif opname == 'BINARY_SUBSCR':
                if len(self.stack) >= 2:
                    slice_val = self.stack.pop()
                    value = self.stack.pop()
                    self.stack.append({
                        'type': 'Subscript',
                        'value': value,
                        'slice': slice_val,
                        'ctx': 'Load',
                        'lineno': instr.starts_line
                    })

            # [关键修复] 增强赋值操作 (Python 3.8-3.10)
            elif opname.startswith('INPLACE_'):
                if len(self.stack) >= 2:
                    right = self.stack.pop()
                    left = self.stack.pop()
                    op = self._get_binary_op(opname)
                    self.stack.append({
                        'type': 'AugAssign',
                        'target': left,
                        'op': op,
                        'value': right,
                        'lineno': instr.starts_line
                    })

            # 一元操作
            elif opname.startswith('UNARY_'):
                if self.stack:
                    operand = self.stack.pop()
                    op = self._get_unary_op(opname)
                    self.stack.append({
                        'type': 'UnaryOp',
                        'op': op,
                        'operand': operand,
                        'lineno': instr.starts_line
                    })

            # 比较操作
            elif opname == 'COMPARE_OP':
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    cmp_op = self._get_compare_op(instr.argval)
                    stack.append({
                        'type': 'Compare',
                        'left': left,
                        'ops': [cmp_op],
                        'comparators': [right],
                        'lineno': instr.starts_line
                    })

            # [关键修复] IS_OP 指令 - Python 3.11+ 的身份运算符 (is/is not)
            elif opname == 'IS_OP':
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    # arg=0 表示 is, arg=1 表示 is not
                    # 同时检查arg和argval，确保正确处理
                    is_not = False
                    if instr.arg is not None:
                        is_not = bool(instr.arg)
                    elif instr.argval is not None:
                        is_not = bool(instr.argval)
                    cmp_op = 'is not' if is_not else 'is'
                    stack.append({
                        'type': 'Compare',
                        'left': left,
                        'ops': [cmp_op],
                        'comparators': [right],
                        'lineno': instr.starts_line
                    })

            # [关键修复] CONTAINS_OP 指令 - Python 3.11+ 的成员运算符 (in/not in)
            elif opname == 'CONTAINS_OP':
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    # arg=0 表示 in, arg=1 表示 not in
                    # 同时检查arg和argval，确保正确处理
                    not_in = False
                    if instr.arg is not None:
                        not_in = bool(instr.arg)
                    elif instr.argval is not None:
                        not_in = bool(instr.argval)
                    cmp_op = 'not in' if not_in else 'in'
                    stack.append({
                        'type': 'Compare',
                        'left': left,
                        'ops': [cmp_op],
                        'comparators': [right],
                        'lineno': instr.starts_line
                    })

            # [关键修复] MAKE_FUNCTION 指令 - Python 3.11+
            elif opname == 'MAKE_FUNCTION':
                flags = instr.arg if instr.arg is not None else 0
                if stack:
                    # 弹出code对象 (栈顶)
                    code_value = stack.pop()
                    
                    # 从CodeObject中提取实际的code对象
                    if isinstance(code_value, dict) and code_value.get('type') == 'CodeObject':
                        actual_code = code_value.get('code')
                    elif isinstance(code_value, types.CodeType):
                        actual_code = code_value
                    else:
                        actual_code = None
                    
                    # 处理默认值和注解 - 注意弹出顺序与压入顺序相反
                    # flags & 8: 有闭包
                    if flags & 8:
                        if stack:
                            stack.pop()  # 弹出闭包
                    
                    # flags & 4: 有注解
                    if flags & 4:
                        if stack:
                            stack.pop()  # 弹出注解
                    
                    # flags & 2: 有关键字-only参数默认值
                    if flags & 2:
                        if stack:
                            stack.pop()  # 弹出关键字默认值
                    
                    # flags & 1: 有位置参数默认值
                    if flags & 1:
                        if stack:
                            stack.pop()  # 弹出位置默认值
                    
                    # 创建 FunctionObject
                    if actual_code:
                        stack.append({
                            'type': 'FunctionObject',
                            'code': actual_code,
                            'lineno': instr.starts_line
                        })

            # 函数调用
            elif opname in ('CALL_FUNCTION', 'CALL', 'CALL_METHOD'):
                argc = instr.arg if instr.arg is not None else 0
                args = []
                kwargs = []
                
                # [关键修复] 检查是否有 KW_NAMES 存储的关键字参数名
                kw_names = getattr(self, '_kw_names', None)
                if kw_names and isinstance(kw_names, tuple):
                    # 有关键字参数，最后 len(kw_names) 个参数是关键字参数
                    kw_arg_count = len(kw_names)
                    pos_arg_count = argc - kw_arg_count
                    
                    # 弹出关键字参数（从后往前）
                    for i in range(kw_arg_count - 1, -1, -1):
                        if stack:
                            value = stack.pop()
                            kwargs.insert(0, {
                                'type': 'keyword',
                                'arg': kw_names[i],
                                'value': value
                            })
                    
                    # 弹出位置参数
                    for _ in range(pos_arg_count):
                        if stack:
                            args.insert(0, stack.pop())
                    
                    # 清除 KW_NAMES
                    self._kw_names = None
                else:
                    # 没有关键字参数，所有参数都是位置参数
                    for _ in range(argc):
                        if stack:
                            args.insert(0, stack.pop())
                
                # [关键修复] 检查是否是推导式调用
                # 推导式调用的特点：argc=0且栈中有FunctionObject（推导式函数）
                # Python 3.11+ 的栈布局: [FunctionObject, null, iter_obj] (CALL 0)
                if argc == 0:
                    func_object_idx = None
                    for i in range(len(stack)):
                        if stack[i].get('type') == 'FunctionObject':
                            func_object_idx = i
                            break
                    
                    if func_object_idx is not None:
                        func_object = stack[func_object_idx]
                        code_value = func_object.get('code')
                        
                        # [关键修复] 支持多种code存储格式
                        if isinstance(code_value, types.CodeType):
                            code_obj = code_value
                        elif isinstance(code_value, dict):
                            if code_value.get('type') == 'CodeObject':
                                code_obj = code_value.get('code')
                            elif code_value.get('type') == 'Constant':
                                code_obj = code_value.get('value')
                            else:
                                code_obj = None
                        else:
                            code_obj = None
                        
                        if code_obj and hasattr(code_obj, 'co_name'):
                            comp_name = code_obj.co_name
                            if comp_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'):
                                # [关键修复] 推导式调用的栈布局: [FunctionObject, null, iter_obj]
                                # iter_obj在栈顶，需要从栈顶向下找
                                iter_obj_idx = len(stack) - 1
                                # 跳过null值（在FunctionObject和iter_obj之间）
                                while iter_obj_idx > func_object_idx:
                                    candidate = stack[iter_obj_idx]
                                    if candidate.get('type') == 'Constant' and candidate.get('value') is None:
                                        iter_obj_idx -= 1  # 跳过null
                                    else:
                                        break
                                
                                if iter_obj_idx > func_object_idx:
                                    iter_obj = stack[iter_obj_idx]
                                    # 移除FunctionObject、null（如果有）和iter_obj
                                    new_stack = stack[:func_object_idx] + stack[iter_obj_idx + 1:]
                                    stack.clear()
                                    stack.extend(new_stack)
                                else:
                                    iter_obj = {'type': 'Name', 'id': 'range'}
                                
                                # 递归反编译推导式 code 对象
                                comp_ast = self._decompile_comprehension(code_obj, iter_obj)
                                if comp_ast:
                                    stack.append(comp_ast)
                                    continue
                
                if stack:
                    func = stack.pop()
                    
                    # [关键修复] 如果func是null（来自PUSH_NULL），跳过它
                    if func.get('type') == 'Constant' and func.get('value') is None:
                        if stack:
                            func = stack.pop()
                    
                    call_node = {
                        'type': 'Call',
                        'func': func,
                        'args': args,
                        'lineno': instr.starts_line
                    }
                    
                    # [关键修复] 添加关键字参数
                    if kwargs:
                        call_node['kwargs'] = kwargs
                    
                    stack.append(call_node)

            # [关键修复] GET_AWAITABLE - Python 3.11+ 的异步等待指令
            elif opname == 'GET_AWAITABLE':
                # GET_AWAITABLE 将栈顶的可等待对象转换为 awaitable
                # 在反编译中，我们需要将其标记为 Await 表达式
                if stack:
                    value = stack.pop()
                    stack.append({
                        'type': 'Await',
                        'value': value,
                        'lineno': instr.starts_line
                    })

            # [关键修复] SEND - Python 3.11+ 的生成器发送指令 (用于 async/await)
            elif opname == 'SEND':
                # SEND 指令用于向生成器发送值，在异步函数中用于 await
                # 通常跟在 GET_AWAITABLE 之后
                # [关键修复] 在异步函数中，SEND 的结果应该保留栈上的 Await 节点
                # 因为 await 表达式的值已经在 GET_AWAITABLE 时创建
                is_async_func = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    is_async_func = bool(self.cfg.code.co_flags & 0x80) or bool(self.cfg.code.co_flags & 0x100)
                
                if is_async_func and stack:
                    # 在异步函数中，SEND 的结果应该是 Await 节点
                    # 检查栈顶是否是 Await 节点，如果不是，创建一个
                    if stack and isinstance(stack[-1], dict) and stack[-1].get('type') != 'Await':
                        # 栈顶不是 Await 节点，需要创建
                        value = stack.pop()
                        stack.append({
                            'type': 'Await',
                            'value': value,
                            'lineno': instr.starts_line
                        })

            # 加载属性
            elif opname == 'LOAD_ATTR':
                if stack:
                    value = stack.pop()
                    stack.append({
                        'type': 'Attribute',
                        'value': value,
                        'attr': instr.argval,
                        'ctx': 'Load',
                        'lineno': instr.starts_line
                    })

            # POP_TOP - 弹出栈顶值
            elif opname == 'POP_TOP':
                if stack:
                    value = stack.pop()
                    # [关键修复] 如果弹出的是有意义的表达式，生成表达式语句
                    # 包括函数调用、比较操作、二元操作等
                    if value and value.get('type') in ('Call', 'Compare', 'BinOp', 'UnaryOp', 'BoolOp', 'Name', 'Constant', 'Attribute', 'Subscript', 'Await'):
                        statements.append({
                            'type': 'Expr',
                            'value': value,
                            'lineno': instr.starts_line
                        })

            # Yield指令
            elif opname in ('YIELD_VALUE', 'YIELD'):
                # [关键修复] 检查当前是否在异步函数中
                # 异步函数中的 YIELD_VALUE 是 await 的内部实现，不应该生成 yield 语句
                is_async_func = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_COROUTINE = 128 (0x80), CO_ITERABLE_COROUTINE = 256 (0x100)
                    is_async_func = bool(self.cfg.code.co_flags & 0x80) or bool(self.cfg.code.co_flags & 0x100)
                
                if not is_async_func:
                    if stack:
                        value = stack.pop()
                        statements.append({
                            'type': 'Yield',
                            'value': value,
                            'lineno': instr.starts_line
                        })
                    else:
                        statements.append({
                            'type': 'Yield',
                            'value': None,
                            'lineno': instr.starts_line
                        })
                # [关键修复] 在异步函数中，YIELD_VALUE 不应该弹出栈
                # 因为 await 的结果需要保留到 STORE_FAST
                # 栈上的 Await 节点应该保持不变

            # RETURN_GENERATOR - Python 3.11+ 生成器返回，忽略
            elif opname == 'RETURN_GENERATOR':
                # 生成器没有实际的返回语句，忽略此指令
                pass

            # [关键修复] 构建列表
            elif opname == 'BUILD_LIST':
                count = instr.arg if instr.arg is not None else 0
                elts = []
                for _ in range(count):
                    if stack:
                        elts.insert(0, stack.pop())
                stack.append({
                    'type': 'List',
                    'elts': elts,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # [关键修复] 构建元组
            elif opname == 'BUILD_TUPLE':
                count = instr.arg if instr.arg is not None else 0
                elts = []
                for _ in range(count):
                    if stack:
                        elts.insert(0, stack.pop())
                stack.append({
                    'type': 'Tuple',
                    'elts': elts,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # [关键修复] 构建集合
            elif opname == 'BUILD_SET':
                count = instr.arg if instr.arg is not None else 0
                elts = []
                for _ in range(count):
                    if stack:
                        elts.insert(0, stack.pop())
                stack.append({
                    'type': 'Set',
                    'elts': elts,
                    'lineno': instr.starts_line
                })

            # [关键修复] 构建字典
            elif opname == 'BUILD_MAP':
                count = instr.arg if instr.arg is not None else 0
                keys = []
                values = []
                for _ in range(count):
                    if len(stack) >= 2:
                        values.insert(0, stack.pop())
                        keys.insert(0, stack.pop())
                stack.append({
                    'type': 'Dict',
                    'keys': keys,
                    'values': values,
                    'lineno': instr.starts_line
                })

            # POP_TOP - 弹出栈顶值
            elif opname == 'POP_TOP':
                if stack:
                    value = stack.pop()
                    # [关键修复] 如果弹出的是函数调用结果或 Await 表达式，生成表达式语句
                    if value and value.get('type') in ('Call', 'Await'):
                        statements.append({
                            'type': 'Expr',
                            'value': value,
                            'lineno': instr.starts_line
                        })
                    # [关键修复] 如果弹出的是Yield结果，忽略它（生成器中的POP_TOP）
                    elif value and value.get('type') == 'Yield':
                        # Yield的结果被POP_TOP丢弃，这是正常的生成器行为
                        pass

            # Yield指令
            elif opname in ('YIELD_VALUE', 'YIELD'):
                # [关键修复] 检查当前是否在异步函数中
                # 异步函数中的 YIELD_VALUE 是 await 的内部实现，不应该生成 yield 语句
                is_async_func = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_COROUTINE = 128 (0x80), CO_ITERABLE_COROUTINE = 256 (0x100)
                    is_async_func = bool(self.cfg.code.co_flags & 0x80) or bool(self.cfg.code.co_flags & 0x100)
                
                if not is_async_func:
                    if stack:
                        value = stack.pop()
                        statements.append({
                            'type': 'Yield',
                            'value': value,
                            'lineno': instr.starts_line
                        })
                    else:
                        statements.append({
                            'type': 'Yield',
                            'value': None,
                            'lineno': instr.starts_line
                        })

            # RETURN_GENERATOR - Python 3.11+ 生成器返回，忽略
            elif opname == 'RETURN_GENERATOR':
                # 生成器没有实际的返回语句，忽略此指令
                pass

            # POP_TOP - 弹出栈顶值
            elif opname == 'POP_TOP':
                if stack:
                    value = stack.pop()
                    # [关键修复] 如果弹出的是函数调用结果或 Await 表达式，生成表达式语句
                    if value and value.get('type') in ('Call', 'Await'):
                        statements.append({
                            'type': 'Expr',
                            'value': value,
                            'lineno': instr.starts_line
                        })

            # Yield指令
            elif opname in ('YIELD_VALUE', 'YIELD'):
                # [关键修复] 检查当前是否在异步函数中
                # 异步函数中的 YIELD_VALUE 是 await 的内部实现，不应该生成 yield 语句
                is_async_func = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_COROUTINE = 128 (0x80), CO_ITERABLE_COROUTINE = 256 (0x100)
                    is_async_func = bool(self.cfg.code.co_flags & 0x80) or bool(self.cfg.code.co_flags & 0x100)
                
                if not is_async_func:
                    if stack:
                        value = stack.pop()
                        statements.append({
                            'type': 'Yield',
                            'value': value,
                            'lineno': instr.starts_line
                        })
                    else:
                        statements.append({
                            'type': 'Yield',
                            'value': None,
                            'lineno': instr.starts_line
                        })

            # RETURN_GENERATOR - Python 3.11+ 生成器返回，忽略
            elif opname == 'RETURN_GENERATOR':
                # 生成器没有实际的返回语句，忽略此指令
                pass

            # [关键修复] GET_ITER - 获取迭代器，用于推导式检测
            elif opname == 'GET_ITER':
                # GET_ITER 将栈顶的可迭代对象转换为迭代器
                # 对于推导式检测，我们保留栈顶的值作为迭代对象
                if stack:
                    # 栈顶是可迭代对象，保持不变
                    pass
            
            # [关键修复] JUMP_BACKWARD - 可能是continue，也可能是for循环的正常迭代
            elif opname == 'JUMP_BACKWARD':
                # 在循环中，JUMP_BACKWARD可能是：
                # 1. for循环体末尾的正常迭代跳转（不应生成continue）
                # 2. 显式的continue语句（应该生成continue）
                # 区分方法：检查该块是否是循环体的最后一个块（有跳转到循环头部的JUMP_BACKWARD）
                current_block = self.current_block
                if current_block and self._loop_depth > 0:
                    # [关键修复] 检查当前块是否是if语句的then分支或else分支中的块
                    is_if_body_block = False
                    for struct in self.structures:
                        if isinstance(struct, IfStructure):
                            if hasattr(struct, 'then_body') and current_block in struct.then_body:
                                is_if_body_block = True
                                break
                            if hasattr(struct, 'else_body') and current_block in struct.else_body:
                                is_if_body_block = True
                                break
                    
                    # [关键修复] 生成continue的条件：
                    # 1. 只有当块是if body块，且块中只有JUMP_BACKWARD一条指令时，才是显式的continue
                    #    例如：if i % 2 == 0: continue 编译后if body块只有JUMP_BACKWARD
                    # 2. 如果if body块中有其他指令，即使是NOP或PASS，也不是显式的continue
                    # 3. 如果块不是if body块，JUMP_BACKWARD是for循环的正常迭代，不生成continue
                    should_generate_continue = False
                    
                    if is_if_body_block:
                        # 检查块中是否只有JUMP_BACKWARD一条有效指令
                        block_instrs = current_block.instructions if hasattr(current_block, 'instructions') else []
                        non_control_instr_count = 0
                        for bi in block_instrs:
                            # 只统计非控制流指令（排除RESUME, CACHE等）
                            if bi.opname not in ('RESUME', 'CACHE', 'NOP'):
                                non_control_instr_count += 1
                        
                        # 如果块中只有JUMP_BACKWARD一条指令，才是显式的continue
                        if non_control_instr_count == 1:  # 只有JUMP_BACKWARD
                            should_generate_continue = True
                            print(f"[DEBUG] should_generate_continue=True (if body block with only JUMP_BACKWARD)")
                        else:
                            print(f"[DEBUG] should_generate_continue=False (if body block has {non_control_instr_count} non-control instructions)")
                    else:
                        print(f"[DEBUG] should_generate_continue=False (not if body block, normal loop iteration)")
                    
                    if should_generate_continue:
                        statements.append({
                            'type': 'Continue',
                            'lineno': instr.starts_line
                        })

            # 返回指令
            elif opname == 'RETURN_CONST':
                # [关键修复] 如果已经生成了return语句，跳过
                if self._has_return_generated:
                    continue
                
                # [关键修复] 检查当前是否在函数内部（模块级别不应该有return）
                is_module_level = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_name'):
                    is_module_level = (self.cfg.code.co_name == '<module>')
                
                # 模块级别的return不应该生成
                if is_module_level:
                    continue
                
                # 检查是否是生成器函数
                is_generator = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_GENERATOR 标志：1 << 5 (32)
                    is_generator = bool(self.cfg.code.co_flags & 32)
                
                # 生成器函数不应该有return语句
                if not is_generator:
                    # 检查是否在with语句的body中
                    # 如果是，跳过生成return语句，因为这是with语句的清理代码
                    in_with_body = False
                    if hasattr(self, 'current_block') and self.current_block:
                        # 检查当前块是否属于with结构的body
                        for struct in self.structures:
                            if isinstance(struct, WithStructure) and self.current_block in struct.with_body:
                                in_with_body = True
                                break
                    
                    if not in_with_body:
                        statements.append({
                            'type': 'Return',
                            'value': {
                                'type': 'Constant',
                                'value': instr.argval,
                                'lineno': instr.starts_line
                            },
                            'lineno': instr.starts_line
                        })
                        # [关键修复] 标记已经生成了return语句
                        self._has_return_generated = True

            elif opname == 'RETURN_VALUE':
                # [关键修复] 如果已经生成了return语句，跳过
                if self._has_return_generated:
                    continue
                
                # [关键修复] 检查当前是否在函数内部（模块级别不应该有return）
                is_module_level = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_name'):
                    is_module_level = (self.cfg.code.co_name == '<module>')
                
                # [关键修复] 检查是否是break语句（在循环体内的模块级别return）
                # break语句的特征：
                # 1. 在模块级别（is_module_level = True）
                # 2. 在循环体内（self._loop_depth > 0）
                # 3. 返回None（LOAD_CONST None, RETURN_VALUE）
                is_break = False
                print(f"[DEBUG] RETURN_VALUE check: is_module_level={is_module_level}, _loop_depth={self._loop_depth}, stack_len={len(stack)}")
                if len(stack) > 0:
                    print(f"[DEBUG] stack top: {stack[-1]}")
                if is_module_level and self._loop_depth > 0:
                    # 检查是否返回None（LOAD_CONST None, RETURN_VALUE）
                    # 这是break语句的特征
                    returns_none = False
                    if len(stack) > 0:
                        top = stack[-1]
                        if top.get('type') == 'Constant' and top.get('value') is None:
                            returns_none = True
                    
                    print(f"[DEBUG] returns_none={returns_none}")
                    if returns_none:
                        is_break = True
                
                # [关键修复] 如果是break语句，生成Break而不是Return
                print(f"[DEBUG] is_break check: is_break={is_break}, is_module_level={is_module_level}, _loop_depth={self._loop_depth}")
                if is_break:
                    print(f"[DEBUG] Generating Break statement")
                    statements.append({
                        'type': 'Break',
                        'lineno': instr.starts_line
                    })
                    continue
                
                # 模块级别的return不应该生成（除非是break语句）
                if is_module_level and not is_break:
                    continue
                
                # 检查是否是生成器函数
                is_generator = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_GENERATOR 标志：1 << 5 (32)
                    is_generator = bool(self.cfg.code.co_flags & 32)
                
                # 生成器函数不应该有return语句
                if not is_generator:
                    # 检查是否在with语句的body中
                    # 如果是，跳过生成return语句，因为这是with语句的清理代码
                    in_with_body = False
                    if hasattr(self, 'current_block') and self.current_block:
                        # 检查当前块是否属于with结构的body
                        for struct in self.structures:
                            if isinstance(struct, WithStructure) and self.current_block in struct.with_body:
                                in_with_body = True
                                break
                    
                    if not in_with_body:
                        if stack:
                            value = stack.pop()
                            # [关键修复] 如果值是 BoolOpPending ，需要与栈中下一个值合并
                            if value.get('type') == 'BoolOpPending' and stack:
                                right = stack.pop()
                                value = {
                                    'type': 'BoolOp',
                                    'op': value['op'],
                                    'values': [value['left'], right],
                                    'lineno': value.get('lineno')
                                }
                            statements.append({
                                'type': 'Return',
                                'value': value,
                                'lineno': instr.starts_line
                            })
                            # [关键修复] 标记已经生成了return语句
                            self._has_return_generated = True

        # 处理栈中剩余的表达式（但在 for 前驱块中，这些通常是迭代器，应该丢弃）
        # 不将栈中剩余的内容添加到 statements
        
        # [关键修复] 重置当前块
        self.current_block = None

        if len(statements) == 1:
            return statements[0]
        return statements if statements else None
    
    def _generate_structure(self, struct: ControlStructure) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """生成控制结构的AST"""
        # [关键修复] 首先检查结构是否已经被处理过
        # 这防止在_generate循环中重复处理同一个结构
        if id(struct) in self.processed_structure_ids:
            print(f"[DEBUG] _generate_structure: Structure {struct.entry_block.start_offset if hasattr(struct, 'entry_block') else 'unknown'} already processed, skipping")
            return None
        
        if isinstance(struct, IfStructure):
            print(f"[DEBUG] _generate_structure called for IfStructure {struct.entry_block.start_offset}")
            # [关键修复] 检查该IfStructure是否是另一个IfStructure的嵌套结构
            # 如果是，并且外层结构已经被处理，跳过这个嵌套结构
            is_nested = False
            for other_struct in self.structures:
                if isinstance(other_struct, IfStructure) and other_struct is not struct:
                    print(f"[DEBUG] _generate_structure: Checking if {struct.entry_block.start_offset} is nested in {other_struct.entry_block.start_offset}")
                    print(f"[DEBUG] _generate_structure: other_struct.then_body={[b.start_offset for b in other_struct.then_body]}, else_body={[b.start_offset for b in other_struct.else_body]}")
                    # [关键修复] 检查IfStructure是否直接嵌套在other_struct的then_body或else_body中
                    is_directly_nested = struct.entry_block in other_struct.then_body or struct.entry_block in other_struct.else_body
                    # [关键修复] 检查IfStructure是否嵌套在other_struct的then_body或else_body中的循环结构中
                    is_nested_in_loop = False
                    if not is_directly_nested:
                        # 收集other_struct的then_body和else_body中的所有循环结构的body_blocks
                        all_blocks_in_other_struct = set(other_struct.then_body) | set(other_struct.else_body)
                        for loop_struct in self.structures:
                            if isinstance(loop_struct, LoopStructure):
                                # 检查循环结构是否在other_struct的then_body或else_body中
                                if loop_struct.header_block in all_blocks_in_other_struct or loop_struct.entry_block in all_blocks_in_other_struct:
                                    # 检查IfStructure的entry_block是否在循环结构的body_blocks中
                                    if struct.entry_block in loop_struct.body_blocks:
                                        is_nested_in_loop = True
                                        print(f"[DEBUG] IfStructure {struct.entry_block.start_offset} is nested in loop {loop_struct.header_block.start_offset} which is in IfStructure {other_struct.entry_block.start_offset}")
                                        break
                    if is_directly_nested or is_nested_in_loop:
                        print(f"[DEBUG] IfStructure {struct.entry_block.start_offset} is nested in IfStructure {other_struct.entry_block.start_offset}")
                        is_nested = True
                        
                        # [关键修复] 检查嵌套if结构是否包含内层while循环
                        # 如果包含，不应该跳过，需要在这里处理
                        has_inner_while = False
                        print(f"[DEBUG] Checking if struct {struct.entry_block.start_offset} has inner while loop")
                        for block in struct.then_body:
                            print(f"[DEBUG] Checking block {block.start_offset} in then_body")
                            # 检查块是否是while循环的条件块
                            for instr in block.instructions:
                                if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                                    print(f"[DEBUG] Found POP_JUMP_FORWARD_IF_FALSE in block {block.start_offset}, target={instr.argval}")
                                    if instr.argval is not None:
                                        # 找到fall-through后继
                                        for succ in block.successors:
                                            print(f"[DEBUG] Checking successor {succ.start_offset}")
                                            if succ.start_offset != instr.argval:
                                                print(f"[DEBUG] Found fall-through successor {succ.start_offset}")
                                                # 检查fall-through后继是否包含POP_JUMP_BACKWARD_IF_TRUE指令
                                                for succ_instr in succ.instructions:
                                                    print(f"[DEBUG] Checking succ_instr {succ_instr.opname}")
                                                    if 'POP_JUMP_BACKWARD_IF_TRUE' in succ_instr.opname:
                                                        print(f"[DEBUG] Found POP_JUMP_BACKWARD_IF_TRUE in successor {succ.start_offset}, target={succ_instr.argval}")
                                                        if succ_instr.argval is not None and succ_instr.argval == succ.start_offset:
                                                            # 这是while循环的条件块
                                                            print(f"[DEBUG] Found inner while loop in struct {struct.entry_block.start_offset}")
                                                            has_inner_while = True
                                                            break
                                            if has_inner_while:
                                                break
                                    if has_inner_while:
                                        break
                            if has_inner_while:
                                break
                        
                        print(f"[DEBUG] Struct {struct.entry_block.start_offset} has_inner_while={has_inner_while}")
                        
                        # [关键修复] 如果包含内层while循环，继续处理，不跳过
                        if has_inner_while:
                            break
                        
                        # [关键修复] 只有当外层结构已经被处理时，才跳过这个嵌套结构
                        if id(other_struct) in self.processed_structure_ids:
                            # 外层结构已经处理过了，这是重复处理，跳过
                            # [关键修复] 标记为已处理，避免在_generate中重复处理
                            self.processed_structure_ids.add(id(struct))
                            # [关键修复] 将嵌套if结构的所有块标记为已生成
                            for b in struct.then_body:
                                self.generated_blocks.add(b)
                            for b in struct.else_body:
                                self.generated_blocks.add(b)
                            return None
                        
                        # [关键修复] 如果外层结构还没有被处理，不要在这里处理嵌套结构
                        # 它会在外层结构处理时被递归处理
                        # 但是，如果外层结构是循环结构，我们需要在这里处理嵌套if结构
                        # 因为循环结构不会递归处理嵌套的if结构
                        # [关键修复] 对于嵌套在if结构中的if结构，递归处理它
                        print(f"[DEBUG] Struct {struct.entry_block.start_offset} is nested in {other_struct.entry_block.start_offset}, processing recursively")
                        # 递归处理嵌套if结构
                        # [关键修复] 传递 _skip_processed_check=False 以确保结构被正确标记为已处理
                        nested_if_ast = self._generate_if_ast(struct, is_top_level=False, _skip_processed_check=False, _entry_block_processed=False)
                        if nested_if_ast:
                            return nested_if_ast
                        return None
            
            # [关键修复] 检查是否是异常处理相关的If结构
            # 异常处理块的特征：包含 PUSH_EXC_INFO, WITH_EXCEPT_START 等指令
            entry_block = struct.entry_block
            is_exception_handler = False
            for instr in entry_block.instructions:
                if instr.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'CHECK_EXC_MATCH'):
                    is_exception_handler = True
                    break
            
            if is_exception_handler:
                # 这是异常处理相关的If结构，不应该生成为普通if语句
                # 标记为已处理，但不生成AST
                self.processed_structure_ids.add(id(struct))
                return None
            
            return self._generate_if_ast(struct, is_top_level=True)
        elif isinstance(struct, LoopStructure):
            return self._generate_loop_ast(struct)
        elif isinstance(struct, TryExceptStructure):
            return self._generate_try_except_ast(struct)
        elif isinstance(struct, WithStructure):
            return self._generate_with_ast(struct)
        else:
            return self._generate_generic_structure(struct)
    
    def _is_not_condition(self, block: BasicBlock, if_struct: IfStructure) -> bool:
        """
        检查一个条件块是否是NOT条件。
        
        [关键修复] NOT条件的核心特征：
        1. 使用 POP_JUMP_IF_TRUE 指令（而不是 POP_JUMP_IF_FALSE）
        2. 条件为真时跳转到else分支，条件为假时执行then分支
        
        这与普通if的区别：
        - 普通if：条件为真时执行then分支（fall-through），条件为假时跳转到else分支
        - NOT条件：条件为真时跳转到else分支，条件为假时执行then分支（fall-through）
        
        在Python字节码中，NOT条件（如 `if not x > 0`）的编译方式是：
        1. 先计算 `x > 0` 的条件
        2. 使用 `POP_JUMP_IF_TRUE` 跳转到else分支
        3. 如果条件为假（x <= 0），执行then分支
        
        这与普通if（如 `if x > 0`）的区别：
        - 普通if使用 `POP_JUMP_IF_FALSE` 跳转到else分支
        - NOT条件使用 `POP_JUMP_IF_TRUE` 跳转到else分支
        
        Args:
            block: 条件块
            if_struct: 包含该条件块的IfStructure
            
        Returns:
            如果是NOT条件返回True，否则返回False
        """
        # 查找跳转指令
        jump_instr = None
        for instr in block.instructions:
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'
            ):
                jump_instr = instr
                break
        
        if not jump_instr:
            return False
        
        # [关键修复] NOT条件使用 POP_JUMP_IF_TRUE 指令
        # 普通if使用 POP_JUMP_IF_FALSE 指令
        if 'IF_TRUE' in jump_instr.opname:
            # 使用 IF_TRUE，可能是NOT条件
            # 需要进一步确认：检查fall-through是否是then分支（有实际内容）
            # 且跳转目标是else分支
            
            # 获取跳转目标块和fall-through块
            if jump_instr.argval is None:
                return False
            
            jump_target = None
            fall_through = None
            for succ in block.successors:
                if succ.start_offset == jump_instr.argval:
                    jump_target = succ
                else:
                    fall_through = succ
            
            if not jump_target or not fall_through:
                return False
            
            # [关键修复] 检查fall-through是否是then分支（有实际内容）
            # 且跳转目标是否是else分支（可能是另一个if或最终else）
            # 如果fall-through有实际内容（不是条件块），这是NOT条件
            
            # 检查fall-through是否包含条件跳转指令
            fall_through_has_condition = False
            for instr in fall_through.instructions:
                if instr.opname in (
                    'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                    'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                    'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'
                ):
                    fall_through_has_condition = True
                    break
            
            # [关键修复] 如果fall-through没有条件跳转指令，且有实际内容
            # 则这是NOT条件
            if not fall_through_has_condition:
                # 进一步检查fall-through是否有实际内容（不只是pass/return）
                has_meaningful_content = False
                for instr in fall_through.instructions:
                    if instr.opname not in ('RESUME', 'CACHE', 'POP_TOP', 'RETURN_VALUE', 'RETURN_CONST'):
                        has_meaningful_content = True
                        break
                
                if has_meaningful_content:
                    return True
        
        return False
    
    def _generate_nop_if_ast(self, if_struct: IfStructure, is_top_level: bool = True, _skip_processed_check: bool = False, _entry_block_processed: bool = False) -> List[Dict[str, Any]]:
        """生成NOP生成的if结构的AST（对应优化后的if True:语句）
        
        当Python编译器遇到if True:时，会生成NOP指令作为占位符。
        为了保持字节码一致性，我们需要保留这些if True:语句。
        
        [关键修复] 处理elif链模式：当连续的NOP块形成elif链时，
        生成带有elif的if结构，而不是多个独立的if结构。
        
        Args:
            if_struct: IfStructure对象（is_nop_generated=True）
            is_top_level: 是否是最外层的if结构
            _skip_processed_check: 内部使用
            _entry_block_processed: 内部使用
        """
        entry_block = if_struct.entry_block
        print(f"[DEBUG] _generate_nop_if_ast called for IfStructure {entry_block.start_offset}")
        
        # [关键修复] 检查是否是elif链的一部分
        # 如果当前NOP块的前驱是另一个NOP生成的if结构，
        # 并且当前块包含NOP指令，则这可能是elif链的一部分
        # 
        # [关键修复] 区分elif链和嵌套if结构：
        # - elif链：当前块是前驱的跳转目标或fall-through后继（不是then_body的一部分）
        # - 嵌套if：当前块是前驱的then_body的一部分（嵌套在if语句内部）
        is_elif_chain_part = False
        for pred in entry_block.predecessors:
            for struct in self.structures:
                if isinstance(struct, IfStructure) and struct.entry_block == pred:
                    if getattr(struct, 'is_nop_generated', False):
                        # 检查当前块是否包含NOP指令
                        current_has_nop = any(
                            instr.opname == 'NOP'
                            for instr in entry_block.instructions
                        )
                        if current_has_nop:
                            # [关键修复] 检查当前块是否是前驱的then_body的一部分
                            # 如果是，这是嵌套if结构，不是elif链
                            is_in_then_body = entry_block in getattr(struct, 'then_body', [])
                            
                            # [关键修复] 也检查当前块是否是前驱的else_body的一部分
                            is_in_else_body = entry_block in getattr(struct, 'else_body', [])
                            
                            if is_in_then_body or is_in_else_body:
                                # 这是嵌套在if结构内部的if，不是elif链
                                # 继续生成独立的if结构
                                print(f"[DEBUG] _generate_nop_if_ast: Block {entry_block.start_offset} is nested in then/else body, not elif chain")
                                break
                            
                            # [关键修复] 检查当前块是否只包含NOP（没有其他实际代码）
                            # 如果当前块包含非NOP指令（如LOAD_FAST等），这是包含实际代码的块
                            # 不应该被识别为elif链的一部分
                            current_has_only_nop = all(
                                instr.opname in ('NOP', 'RESUME', 'CACHE', 'PRECALL')
                                for instr in entry_block.instructions
                            )
                            if not current_has_only_nop:
                                print(f"[DEBUG] _generate_nop_if_ast: Block {entry_block.start_offset} has non-NOP instructions, not elif chain")
                                # 这是包含实际代码的块，不是elif链
                                break
                            
                            # 这是elif链的一部分，跳过
                            is_elif_chain_part = True
                            print(f"[DEBUG] _generate_nop_if_ast: Block {entry_block.start_offset} is part of elif chain, skipping")
                            break
            if is_elif_chain_part:
                break
        
        if is_elif_chain_part:
            # 标记为已处理，但不生成独立的if结构
            self.processed_structure_ids.add(id(if_struct))
            self.generated_blocks.add(entry_block)
            return []
        
        # [关键修复] 检查是否有后续的NOP块形成elif链
        # 收集所有连续的NOP生成的if结构
        # [重要修复] 区分elif链和嵌套if：
        # - elif链：后继块是前驱的跳转目标（不是then_body的一部分）
        # - 嵌套if：后继块是前驱then_body的一部分
        elif_chain = []
        current_block = entry_block
        print(f"[DEBUG] _generate_nop_if_ast: Checking for elif chain from block {entry_block.start_offset}")
        while True:
            # 查找后继块是否是NOP生成的if结构
            found_next = False
            print(f"[DEBUG] _generate_nop_if_ast: current_block = {current_block.start_offset}, successors = {[s.start_offset for s in current_block.successors]}")
            for succ in current_block.successors:
                print(f"[DEBUG] _generate_nop_if_ast: Checking successor {succ.start_offset}")
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == succ:
                        print(f"[DEBUG] _generate_nop_if_ast: Found IfStructure with entry_block {succ.start_offset}")
                        print(f"[DEBUG] _generate_nop_if_ast: is_nop_generated = {getattr(struct, 'is_nop_generated', False)}")
                        print(f"[DEBUG] _generate_nop_if_ast: processed = {id(struct) in self.processed_structure_ids}")
                        if (getattr(struct, 'is_nop_generated', False) and
                            id(struct) not in self.processed_structure_ids):
                            # 检查后继块是否包含NOP
                            succ_has_nop = any(
                                instr.opname == 'NOP'
                                for instr in succ.instructions
                            )
                            print(f"[DEBUG] _generate_nop_if_ast: succ_has_nop = {succ_has_nop}")
                            if succ_has_nop:
                                # [关键修复] 检查后继块是否是当前if结构的then_body的一部分
                                # 如果是，这是嵌套if，不是elif链
                                is_nested_in_then = succ in getattr(if_struct, 'then_body', [])
                                
                                # 也检查是否是elif链中最后一个结构的then_body的一部分
                                if elif_chain and not is_nested_in_then:
                                    is_nested_in_then = succ in getattr(elif_chain[-1], 'then_body', [])
                                
                                if is_nested_in_then:
                                    print(f"[DEBUG] _generate_nop_if_ast: Successor {succ.start_offset} is in then_body, not elif chain")
                                    # 这是嵌套if，不要添加到elif_chain
                                    break
                                
                                # [关键修复] 检查后继块是否只包含NOP（没有其他实际代码）
                                # 如果后继块包含非NOP指令（如LOAD_FAST等），这是包含实际代码的块
                                # 不应该被识别为elif链的一部分
                                succ_has_only_nop = all(
                                    instr.opname in ('NOP', 'RESUME', 'CACHE', 'PRECALL')
                                    for instr in succ.instructions
                                )
                                if not succ_has_only_nop:
                                    print(f"[DEBUG] _generate_nop_if_ast: Successor {succ.start_offset} has non-NOP instructions, not elif chain")
                                    # 这是包含实际代码的块，不是elif链
                                    break
                                
                                elif_chain.append(struct)
                                self.processed_structure_ids.add(id(struct))
                                self.generated_blocks.add(succ)
                                current_block = succ
                                found_next = True
                                print(f"[DEBUG] _generate_nop_if_ast: Added to elif_chain")
                                break
                if found_next:
                    break
            if not found_next:
                break
        print(f"[DEBUG] _generate_nop_if_ast: elif_chain length = {len(elif_chain)}")
        
        # 生成if True:条件
        condition = {'type': 'Constant', 'value': True, 'lineno': self._get_block_line(entry_block)}
        
        # [关键修复] 如果有elif链，条件改为False（对应if False:）
        # 但只在elif链不是由嵌套if引起的情况下
        if elif_chain:
            condition = {'type': 'Constant', 'value': False, 'lineno': self._get_block_line(entry_block)}
        
        # 处理then_body
        then_body = []
        
        # [关键修复] 检查是否是NOP作为行号标记的情况
        # 这种情况下，then_body块包含NOP和实际代码
        print(f"[DEBUG] _generate_nop_if_ast: Checking nop_is_line_marker for block {entry_block.start_offset}: {getattr(if_struct, 'nop_is_line_marker', False)}")
        if getattr(if_struct, 'nop_is_line_marker', False):
            print(f"[DEBUG] _generate_nop_if_ast: Processing nop_is_line_marker for block {entry_block.start_offset}")
            print(f"[DEBUG] _generate_nop_if_ast: then_body={[b.start_offset for b in if_struct.then_body]}")
            # 处理then_body中的块，生成实际的代码，但跳过NOP指令
            for block in if_struct.then_body:
                print(f"[DEBUG] _generate_nop_if_ast: Processing block {block.start_offset} in then_body, in generated_blocks={block in self.generated_blocks}")
                if block not in self.generated_blocks:
                    self.generated_blocks.add(block)
                    # 过滤掉NOP、RESUME等指令，只生成实际的代码
                    filtered_instrs = [instr for instr in block.instructions 
                                       if instr.opname not in ('NOP', 'RESUME', 'CACHE')]
                    if filtered_instrs:
                        # 创建临时块来生成代码
                        from .basic_block import BasicBlock
                        temp_block = BasicBlock(block.start_offset)
                        temp_block.instructions = filtered_instrs
                        block_ast = self._generate_block_content_v2(temp_block)
                        if block_ast:
                            if isinstance(block_ast, list):
                                then_body.extend(block_ast)
                            else:
                                then_body.append(block_ast)
            
            # 标记entry_block
            self.generated_blocks.add(entry_block)
        else:
            # NOP生成的if结构，then_body块只包含NOP
            # [关键修复] 首先检查then_body中是否有嵌套结构
            print(f"[DEBUG] _generate_nop_if_ast: Processing then_body for block {entry_block.start_offset}, then_body={[b.start_offset for b in if_struct.then_body]}")
            for block in if_struct.then_body:
                print(f"[DEBUG] _generate_nop_if_ast: Processing then_body block {block.start_offset}, in generated_blocks={block in self.generated_blocks}")
                if block in self.generated_blocks:
                    print(f"[DEBUG] _generate_nop_if_ast: Block {block.start_offset} already in generated_blocks, skipping")
                    continue
                
                # 检查块是否是嵌套if结构的入口
                nested_if_struct = None
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == block and struct != if_struct:
                        nested_if_struct = struct
                        break
                
                if nested_if_struct and id(nested_if_struct) not in self.processed_structure_ids:
                    # 递归处理嵌套if结构
                    # [关键修复] 对于NOP生成的if结构，调用_generate_nop_if_ast
                    if getattr(nested_if_struct, 'is_nop_generated', False):
                        nested_ast = self._generate_nop_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True)
                    else:
                        nested_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True)
                    if nested_ast:
                        if isinstance(nested_ast, list):
                            then_body.extend(nested_ast)
                        else:
                            then_body.append(nested_ast)
                else:
                    # 生成块内容，但跳过NOP指令
                    self.generated_blocks.add(block)
                    filtered_instrs = [instr for instr in block.instructions 
                                       if instr.opname not in ('NOP', 'RESUME', 'CACHE')]
                    if filtered_instrs:
                        from .basic_block import BasicBlock
                        temp_block = BasicBlock(block.start_offset)
                        temp_block.instructions = filtered_instrs
                        block_ast = self._generate_block_content_v2(temp_block)
                        if block_ast:
                            if isinstance(block_ast, list):
                                then_body.extend(block_ast)
                            else:
                                then_body.append(block_ast)
            
            # [关键修复] 对于包含实际代码的NOP if结构（如最后一个if True:），
            # 代码可能在entry_block中，而不是在then_body中
            # 检查entry_block是否包含非NOP指令
            if not then_body and entry_block not in self.generated_blocks:
                filtered_instrs = [instr for instr in entry_block.instructions 
                                   if instr.opname not in ('NOP', 'RESUME', 'CACHE')]
                if filtered_instrs:
                    from .basic_block import BasicBlock
                    temp_block = BasicBlock(entry_block.start_offset)
                    temp_block.instructions = filtered_instrs
                    block_ast = self._generate_block_content_v2(temp_block)
                    if block_ast:
                        if isinstance(block_ast, list):
                            then_body.extend(block_ast)
                        else:
                            then_body.append(block_ast)
                    self.generated_blocks.add(entry_block)
            
            # [关键修复] 检查后继块是否也是NOP块
            # 如果是，递归生成嵌套的if True:结构
            successor = if_struct.merge_block
            if successor and successor not in self.generated_blocks:
                # 检查后继块是否只包含NOP
                succ_nop_only = True
                succ_has_nop = False
                for instr in successor.instructions:
                    if instr.opname == 'NOP':
                        succ_has_nop = True
                    elif instr.opname not in ('RESUME', 'CACHE', 'PRECALL'):
                        succ_nop_only = False
                        break
                
                # 如果后继块也是NOP块，递归生成嵌套的if True:结构
                if succ_nop_only and succ_has_nop:
                    # [关键修复] 直接递归调用_generate_nop_if_ast，而不是_generate_if_ast
                    # 这样可以避免重复生成if结构
                    for struct in self.structures:
                        if isinstance(struct, IfStructure) and struct.entry_block == successor:
                            if id(struct) not in self.processed_structure_ids:
                                # 标记结构为已处理
                                self.processed_structure_ids.add(id(struct))
                                # 递归生成嵌套的if结构
                                nested_ast = self._generate_nop_if_ast(struct, is_top_level=False, _skip_processed_check=True)
                                if nested_ast:
                                    if isinstance(nested_ast, list):
                                        then_body.extend(nested_ast)
                                    else:
                                        then_body.append(nested_ast)
                            break
            
            # 标记entry_block
            self.generated_blocks.add(entry_block)
        
        # [关键修复] 处理elif链的代码生成
        elif_tests = []
        elif_bodies = []
        
        if elif_chain:
            print(f"[DEBUG] _generate_nop_if_ast: Generating elif chain with {len(elif_chain)} items")
            # 为每个elif生成条件和body
            for elif_struct in elif_chain:
                elif_block = elif_struct.entry_block
                print(f"[DEBUG] _generate_nop_if_ast: Processing elif block {elif_block.start_offset}")
                # 生成elif条件（True，对应elif True:）
                elif_condition = {'type': 'Constant', 'value': True, 'lineno': self._get_block_line(elif_block)}
                elif_tests.append(elif_condition)
                
                # 生成elif的body（过滤掉NOP指令）
                elif_body = []
                
                # [关键修复] 从entry_block本身提取代码（因为它包含代码）
                print(f"[DEBUG] _generate_nop_if_ast: Extracting code from elif_block {elif_block.start_offset}")
                print(f"[DEBUG] _generate_nop_if_ast: elif_block instructions: {[instr.opname for instr in elif_block.instructions]}")
                filtered_instrs = [instr for instr in elif_block.instructions 
                                  if instr.opname not in ('NOP', 'RESUME', 'CACHE')]
                print(f"[DEBUG] _generate_nop_if_ast: filtered_instrs: {[instr.opname for instr in filtered_instrs]}")
                if filtered_instrs:
                    from .basic_block import BasicBlock
                    temp_block = BasicBlock(elif_block.start_offset)
                    temp_block.instructions = filtered_instrs
                    block_ast = self._generate_block_content_v2(temp_block)
                    print(f"[DEBUG] _generate_nop_if_ast: block_ast = {block_ast}")
                    if block_ast:
                        if isinstance(block_ast, list):
                            elif_body.extend(block_ast)
                        else:
                            elif_body.append(block_ast)
                
                # 也检查then_body中的块
                for block in elif_struct.then_body:
                    if block != elif_block:  # 避免重复处理
                        filtered_instrs = [instr for instr in block.instructions 
                                          if instr.opname not in ('NOP', 'RESUME', 'CACHE')]
                        if filtered_instrs:
                            from .basic_block import BasicBlock
                            temp_block = BasicBlock(block.start_offset)
                            temp_block.instructions = filtered_instrs
                            block_ast = self._generate_block_content_v2(temp_block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    elif_body.extend(block_ast)
                                else:
                                    elif_body.append(block_ast)
                
                print(f"[DEBUG] _generate_nop_if_ast: elif_body length = {len(elif_body)}")
                elif_bodies.append(elif_body)
        
        # [关键修复] 处理else分支
        else_body = []
        if getattr(if_struct, 'merge_block', None) and not elif_chain:
            # 有merge_block且不是elif链，说明有else分支
            merge_block = if_struct.merge_block
            if merge_block not in self.generated_blocks:
                self.generated_blocks.add(merge_block)
                # 生成else分支的代码
                block_ast = self._generate_block_content_v2(merge_block)
                if block_ast:
                    if isinstance(block_ast, list):
                        else_body.extend(block_ast)
                    else:
                        else_body.append(block_ast)
        
        # 构建if节点
        if_node = {
            'type': 'If',
            'test': condition,
            'body': then_body,
            'orelse': else_body,
            'lineno': getattr(if_struct, 'nop_line_number', self._get_block_line(entry_block))
        }
        
        # [关键修复] 添加elif链
        if elif_tests:
            if_node['elif_test'] = elif_tests
            if_node['elif_body'] = elif_bodies
        
        return [if_node]
    
    def _generate_if_ast(self, if_struct: IfStructure, is_top_level: bool = True, _skip_processed_check: bool = False, _entry_block_processed: bool = False) -> List[Dict[str, Any]]:
        """生成if结构的AST
        
        返回列表，因为入口块可能包含条件之前的代码（如函数/类定义）
        
        Args:
            if_struct: IfStructure对象
            is_top_level: 是否是最外层的if结构（用于控制elif链提取）
            _skip_processed_check: 内部使用，跳过processed_structure_ids检查
            _entry_block_processed: 内部使用，入口块已经被处理，不要重复提取pre_condition_statements
        """
        entry_block = if_struct.entry_block
        print(f"[DEBUG] _generate_if_ast called for IfStructure {if_struct.entry_block.start_offset}, processed={id(if_struct) in self.processed_structure_ids}, _loop_depth={self._loop_depth}")
        
        # [关键修复] 检查该结构是否已经被处理（作为elif链的一部分）
        # 但如果是递归调用（_skip_processed_check=True），跳过这个检查
        if not _skip_processed_check and id(if_struct) in self.processed_structure_ids:
            print(f"[DEBUG] IfStructure {if_struct.entry_block.start_offset} already processed, returning cached AST")
            # [关键修复] 返回缓存的AST，而不是None
            cached_ast = self._if_ast_cache.get(id(if_struct))
            if cached_ast:
                return cached_ast
            return None
        
        # [关键修复] 立即标记结构为已处理，避免在递归处理期间被重复调用
        # 这在处理嵌套结构时特别重要，防止父结构被重复处理
        if not _skip_processed_check:
            self.processed_structure_ids.add(id(if_struct))
        
        # [关键修复] 处理NOP生成的if结构（对应优化后的if True:语句）
        # 这必须在其他处理之前，因为NOP生成的结构没有条件跳转指令
        if getattr(if_struct, 'is_nop_generated', False):
            # [关键修复] 对于NOP生成的if结构，不要在此时标记entry_block为generated
            # 因为_generate_nop_if_ast可能需要处理entry_block中的代码
            return self._generate_nop_if_ast(if_struct, is_top_level, _skip_processed_check, _entry_block_processed)
        
        # [关键修复] 检查该块是否已经在_generate_entry_sequence中处理过了
        # 如果已经处理过，跳过条件之前的代码处理
        # 但如果是递归调用（_skip_processed_check=True），不要跳过，需要生成完整的AST
        block_already_processed = entry_block in self.generated_blocks or _entry_block_processed
        print(f"[DEBUG] _generate_if_ast: entry_block={entry_block.start_offset}, block_already_processed={block_already_processed}, in generated_blocks={entry_block in self.generated_blocks}, _entry_block_processed={_entry_block_processed}")
        if entry_block in self.generated_blocks:
            print(f"[DEBUG] _generate_if_ast: entry_block {entry_block.start_offset} already in generated_blocks!")
        if not _skip_processed_check:
            self.generated_blocks.add(entry_block)
        
        # [关键修复] 处理入口块中条件之前的代码
        pre_condition_statements = []
        condition = None
        
        # 找到条件跳转指令的位置
        jump_index = None
        for i, instr in enumerate(entry_block.instructions):
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                # [关键修复] 支持None检查跳转指令
                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'
            ):
                jump_index = i
                break
        
        # [关键修复] 如果块已经处理过，跳过条件之前的代码处理
        # 这包括：1. 非递归调用时块已处理；2. 递归调用时_entry_block_processed为True
        if block_already_processed:
            # 块已经在_generate_entry_sequence中处理过了
            # 只需要提取条件，不需要处理条件之前的代码
            if jump_index is not None:
                jump_instr = entry_block.instructions[jump_index]
                
                # [关键修复] 处理 POP_JUMP_*_IF_NONE / POP_JUMP_*_IF_NOT_NONE 指令
                if jump_instr.opname in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                                        'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'):
                    # 提取变量表达式
                    condition_instrs = entry_block.instructions[:jump_index]
                    expr = self.expr_reconstructor.reconstruct(condition_instrs)
                    if expr:
                        # 构建 is None / is not None 比较
                        # [关键修复] 跳转指令语义与条件相反：
                        # POP_JUMP_*_IF_NOT_NONE 表示 "如果不是None则跳转"，对应 if x is None
                        # POP_JUMP_*_IF_NONE 表示 "如果是None则跳转"，对应 if x is not None
                        is_not_none = 'NOT_NONE' not in jump_instr.opname
                        condition = {
                            'type': 'Compare',
                            'left': expr,
                            'ops': ['is not' if is_not_none else 'is'],
                            'comparators': [{
                                'type': 'Constant',
                                'value': None,
                                'lineno': jump_instr.starts_line
                            }],
                            'lineno': jump_instr.starts_line
                        }
                else:
                    # [关键修复] 当块已经处理过时，只提取条件部分的指令
                    # 条件部分从比较操作指令（COMPARE_OP, CONTAINS_OP, IS_OP）之前开始
                    
                    # [关键修复] 首先检查是否是海象运算符模式
                    # 如果在比较指令前有 COPY + STORE 模式，这是海象运算符
                    has_walrus = False
                    walrus_copy_idx = -1
                    walrus_store_idx = -1
                    for i in range(jump_index - 1, 0, -1):
                        instr = entry_block.instructions[i]
                        if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            if i > 0 and entry_block.instructions[i - 1].opname == 'COPY':
                                has_walrus = True
                                walrus_store_idx = i
                                walrus_copy_idx = i - 1
                                break
                    
                    if has_walrus:
                        # [海象运算符] 从海象运算符的开始位置算起
                        # 海象运算符模式：PUSH_NULL; LOAD_NAME len; ...; CALL; COPY 1; STORE_NAME n; ...
                        # 从 COPY 指令向前查找，直到找到 PUSH_NULL
                        condition_start = walrus_copy_idx
                        for j in range(walrus_copy_idx - 1, -1, -1):
                            prev_instr = entry_block.instructions[j]
                            if prev_instr.opname == 'PUSH_NULL':
                                condition_start = j
                                break
                            elif prev_instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_ATTR'):
                                condition_start = j
                                # 继续向前查找 PUSH_NULL
                                if j > 0 and entry_block.instructions[j - 1].opname == 'PUSH_NULL':
                                    condition_start = j - 1
                                break
                            elif prev_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                                # 遇到赋值语句，停止
                                break
                    else:
                        # 普通条件，从比较操作的操作数开始
                        condition_start = 0
                        for i in range(jump_index - 1, -1, -1):
                            instr = entry_block.instructions[i]
                            # 找到比较操作指令，这就是条件的开始
                            if instr.opname in ('COMPARE_OP', 'CONTAINS_OP', 'IS_OP'):
                                # 从比较操作的操作数开始（通常是LOAD_*指令）
                                # 向前查找直到找到完整的表达式
                                condition_start = i
                                stack_depth = 2  # 比较操作需要两个操作数
                                for j in range(i - 1, -1, -1):
                                    prev_instr = entry_block.instructions[j]
                                    if prev_instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                                            'LOAD_CONST', 'LOAD_ATTR'):
                                        stack_depth -= 1
                                        condition_start = j
                                        if stack_depth <= 0:
                                            break
                                    elif prev_instr.opname in ('BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT',
                                                               'BINARY_MULTIPLY', 'BINARY_DIVIDE', 'BINARY_MODULO',
                                                               'BINARY_FLOOR_DIVIDE', 'BINARY_TRUE_DIVIDE'):
                                        # [关键修复] BINARY_OP 指令消耗两个操作数，产生一个结果
                                        # 所以需要增加 stack_depth 来继续查找操作数
                                        stack_depth += 1
                                    elif prev_instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD'):
                                        # [关键修复] CALL 指令消耗 (arg_count + 1) 个值（函数对象 + 参数），产生1个结果
                                        # 为了找到函数调用的操作数，需要增加 stack_depth
                                        arg_count = prev_instr.arg if prev_instr.arg is not None else 0
                                        stack_depth += arg_count
                                    elif prev_instr.opname == 'PRECALL':
                                        # [关键修复] PRECALL 指令不改变栈状态，跳过
                                        pass
                                    elif prev_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                                        # 遇到赋值指令，停止查找
                                        condition_start = j + 1
                                        break
                                break
                    
                    # 提取条件（从condition_start到跳转指令）
                    condition_instrs = entry_block.instructions[condition_start:jump_index]
                    condition = self.expr_reconstructor.reconstruct(condition_instrs)
                    
                    # [关键修复] 检查是否是NOT条件
                    if condition and self._is_not_condition(entry_block, if_struct):
                        condition = {
                            'type': 'UnaryOp',
                            'op': 'not',
                            'operand': condition,
                            'lineno': condition.get('lineno')
                        }
        elif jump_index is not None and jump_index > 0:
            # 有条件跳转指令，且前面有代码
            # [关键修复] 条件指令是跳转指令之前的所有指令（因为它们会生成一个值给POP_JUMP消费）
            # 所以 pre_condition 应该是空，或者只包含真正的前置代码
            # [关键修复] 改进条件提取逻辑
            # 从跳转指令向前查找，直到找到一个完整的表达式
            condition_start = 0
            
            # 首先尝试找到COMPARE_OP或类似的比较指令
            compare_idx = -1
            for i in range(jump_index - 1, -1, -1):
                instr = entry_block.instructions[i]
                if instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP'):
                    compare_idx = i
                    break
            
            if compare_idx >= 0:
                # 找到了比较指令，条件应该包含比较指令及其操作数
                # [关键修复] 更准确地确定条件的起始位置
                # 从比较指令向前查找，直到找到条件的起始（通常是第一个LOAD指令）
                condition_start = compare_idx
                
                # [海象运算符] 首先检查是否是海象运算符模式
                # 如果在比较指令前有 COPY + STORE 模式，这是海象运算符
                has_walrus = False
                for i in range(compare_idx - 1, 0, -1):
                    instr = entry_block.instructions[i]
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                        if i > 0 and entry_block.instructions[i - 1].opname == 'COPY':
                            has_walrus = True
                            break
                
                if has_walrus:
                    # [海象运算符] 如果有海象运算符，从海象运算符的开始位置算起
                    # 海象运算符模式：PUSH_NULL; LOAD_NAME len; ...; CALL; COPY 1; STORE_NAME n; ...
                    # 需要找到 PUSH_NULL 或 LOAD_NAME 指令作为起始
                    # 从 COPY 指令向前查找，直到找到 PUSH_NULL 或 LOAD_NAME
                    walrus_start = 0
                    for i in range(compare_idx - 1, -1, -1):
                        instr = entry_block.instructions[i]
                        if instr.opname == 'COPY':
                            # 找到 COPY 指令，从它前面开始
                            walrus_start = i
                            # 向前查找 PUSH_NULL 或 LOAD_NAME
                            for j in range(i - 1, -1, -1):
                                prev_instr = entry_block.instructions[j]
                                if prev_instr.opname == 'PUSH_NULL':
                                    # 找到 PUSH_NULL，这是函数调用的开始
                                    walrus_start = j
                                    break
                                elif prev_instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_ATTR'):
                                    # 找到 LOAD_NAME，但还需要检查前面是否有 PUSH_NULL
                                    walrus_start = j
                                    # 继续向前查找 PUSH_NULL
                                    if j > 0 and entry_block.instructions[j - 1].opname == 'PUSH_NULL':
                                        walrus_start = j - 1
                                    break
                                elif prev_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL'):
                                    # 遇到赋值语句，停止
                                    break
                            break
                    condition_start = walrus_start
                else:
                    # 我们需要找到两个操作数，每个操作数可能由多个指令组成
                    # 从比较指令向前遍历，跟踪栈深度
                    stack_depth = 2  # 比较操作需要两个操作数
                    i = compare_idx - 1
                    while i >= 0 and stack_depth > 0:
                        instr = entry_block.instructions[i]
                        # 这些指令会消耗栈上的值
                        if instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'BINARY_OP', 'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY', 'BINARY_DIVIDE'):
                            stack_depth += 1  # 这些指令会产生一个结果，但需要两个输入
                        elif instr.opname.startswith('LOAD_') or instr.opname.startswith('CONST_'):
                            stack_depth -= 1  # 这些指令会压入一个值
                        elif instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD'):
                            arg_count = instr.arg if instr.arg is not None else 0
                            # CALL消耗arg_count+1个值（函数对象 + 参数），产生1个结果
                            # 净变化: -(arg_count + 1) + 1 = -arg_count
                            stack_depth -= arg_count
                        elif instr.opname in ('GET_ATTR', 'GET_ITER'):
                            stack_depth -= 0  # 这些指令消耗1个值，产生1个结果
                        elif instr.opname in ('UNARY_NOT', 'UNARY_POSITIVE', 'UNARY_NEGATIVE'):
                            stack_depth -= 0  # 一元操作消耗1个值，产生1个结果
                        elif instr.opname == 'COPY':
                            # [海象运算符] COPY 指令复制栈顶值，不改变栈深度
                            stack_depth -= 0
                        elif instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF'):
                            # 普通赋值，停止查找
                            condition_start = i + 1
                            break
                        
                        if stack_depth <= 0:
                            condition_start = i
                            break
                        i -= 1
                    
                    # 如果还没有找到起始位置，默认从块开头开始
                    if stack_depth > 0:
                        condition_start = 0
            else:
                # 没有找到比较指令，尝试其他方法
                # 查找任何可能生成条件的指令序列
                for i in range(jump_index - 1, -1, -1):
                    instr = entry_block.instructions[i]
                    if instr.opname in ('BINARY_OP', 'UNARY_NOT', 'CALL', 'CALL_FUNCTION'):
                        condition_start = i
                        # 向前查找，构建完整的表达式
                        # 对于函数调用，需要包含函数对象和参数
                        while condition_start > 0:
                            prev_instr = entry_block.instructions[condition_start - 1]
                            # [关键修复] 扩展前缀匹配，包含PUSH_NULL, PRECALL等Python 3.11+指令
                            if prev_instr.opname.startswith(('LOAD_', 'BINARY_', 'UNARY_', 'CALL', 'PUSH_NULL', 'PRECALL')):
                                condition_start -= 1
                            else:
                                break
                        break
            
            # 提取条件（从 condition_start 到 jump_index）
            condition_instrs = entry_block.instructions[condition_start:jump_index]
            condition = self.expr_reconstructor.reconstruct(condition_instrs)
            
            # [关键修复] 检查是否是 POP_JUMP_*_IF_NONE / POP_JUMP_*_IF_NOT_NONE 指令
            jump_instr = entry_block.instructions[jump_index]
            if jump_instr.opname in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                                    'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'):
                if condition:
                    # 构建 is None / is not None 比较
                    # [关键修复] 跳转指令语义与条件相反：
                    # POP_JUMP_*_IF_NOT_NONE 表示 "如果不是None则跳转"，对应 if x is None
                    # POP_JUMP_*_IF_NONE 表示 "如果是None则跳转"，对应 if x is not None
                    is_not_none = 'NOT_NONE' not in jump_instr.opname
                    condition = {
                        'type': 'Compare',
                        'left': condition,
                        'ops': ['is not' if is_not_none else 'is'],
                        'comparators': [{
                            'type': 'Constant',
                            'value': None,
                            'lineno': jump_instr.starts_line
                        }],
                        'lineno': jump_instr.starts_line
                    }
            
            # [关键修复] 检查条件是否为常量（如True, False, 0, 100等）
            # 如果是常量，可能是优化后的代码或重建失败，使用占位符
            if condition and condition.get('type') == 'Constant':
                const_value = condition.get('value')
                if const_value in (True, False, 0, 100, None, '', []):
                    # 使用占位符代替常量
                    jump_instr = entry_block.instructions[jump_index]
                    target_offset = getattr(jump_instr, 'argval', 0)
                    condition = {
                        'type': 'Name',
                        'id': f'<condition_{target_offset}>',
                        'ctx': 'Load',
                        'lineno': jump_instr.starts_line
                    }
            
            # [关键修复] 检查是否是NOT条件
            if condition and self._is_not_condition(entry_block, if_struct):
                condition = {
                    'type': 'UnaryOp',
                    'op': 'not',
                    'operand': condition,
                    'lineno': condition.get('lineno')
                }
            
            # 处理条件之前的代码（真正的前置语句）
            if condition_start > 0:
                pre_condition_instrs = entry_block.instructions[:condition_start]
                pre_condition_statements = self._generate_instructions_content(pre_condition_instrs)
        else:
            # 没有条件跳转指令，或者条件在块开头
            # [关键修复] 检查是否是常量折叠的if（如if True:或if False:）
            is_constant_folded = getattr(if_struct, 'is_constant_folded', False)
            if is_constant_folded:
                # 对于常量折叠的if，条件应该是True（因为编译器只保留可达分支）
                # 获取NOP指令的行号
                nop_line = getattr(if_struct, 'nop_line_number', None)
                condition = {
                    'type': 'Constant',
                    'value': True,
                    'lineno': nop_line
                }
            else:
                condition = self._extract_condition_v2(entry_block)
        
        # [关键修复] 初始化then_body
        then_body = []
        
        # [关键修复] 初始化is_chain_compare标志
        # 这个标志用于标识是否是链式比较，后面的代码需要使用它
        is_chain_compare = False
        chain_compare_first_block = None  # 链式比较的第一个条件块（如果有的话）
        
        # [关键修复] 检测链式比较
        # 链式比较的特征：condition_chain中有多个块，且包含COPY指令
        chain_len = len(getattr(if_struct, 'condition_chain', []))
        print(f"[DEBUG] 检测链式比较: is_compound={if_struct.is_compound_condition}, chain_len={chain_len}")
        if if_struct.is_compound_condition and chain_len > 1:
            # 检查是否包含COPY指令（链式比较使用COPY 2复制中间值）
            has_copy_instr = False
            for condition_block in if_struct.condition_chain:
                for instr in condition_block.instructions:
                    if instr.opname == 'COPY' and instr.arg == 2:
                        has_copy_instr = True
                        break
                if has_copy_instr:
                    break
            
            # 检查所有跳转指令是否指向同一个目标（链式比较的特征）
            if has_copy_instr:
                jump_targets = set()
                for condition_block in if_struct.condition_chain:
                    for instr in condition_block.instructions:
                        if instr.opname.startswith('POP_JUMP') or instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                            jump_targets.add(getattr(instr, 'argval', 0))
                            break
                # [关键修复] 对于链式比较，跳转目标可能不同，但都是else分支
                # 检查是否有COPY 2指令，这是链式比较的特征
                if has_copy_instr:
                    is_chain_compare = True
                    # [关键修复] 检查是否有前一个结构包含当前结构的入口块
                    # 或者当前结构的入口块是另一个结构的入口块的后继
                    # [关键修复] 只检查前一个结构是否也是链式比较（有多个condition_chain块）
                    for other_struct in self.structures:
                        if (hasattr(other_struct, 'entry_block') and 
                            other_struct != if_struct and
                            hasattr(other_struct, 'is_compound_condition') and
                            other_struct.is_compound_condition and
                            len(getattr(other_struct, 'condition_chain', [])) > 1):
                            # 检查当前结构的入口块是否是另一个结构的入口块的后继
                            if if_struct.entry_block in other_struct.entry_block.successors:
                                chain_compare_first_block = other_struct.entry_block
                                print(f"[DEBUG] 在第一个检测逻辑中设置chain_compare_first_block={chain_compare_first_block.start_offset}")
                                break
                            # 或者检查当前结构的入口块是否在另一个结构的then_body中
                            elif hasattr(other_struct, 'then_body'):
                                then_body_offsets = {b.start_offset for b in other_struct.then_body}
                                if if_struct.entry_block.start_offset in then_body_offsets:
                                    chain_compare_first_block = other_struct.entry_block
                                    print(f"[DEBUG] 在第一个检测逻辑中设置chain_compare_first_block={chain_compare_first_block.start_offset}")
                                    break
        
        # [关键修复] 检测链式比较的第一部分
        # 如果当前结构的then_body包含另一个复合条件结构的入口块，这可能是链式比较
        is_chain_compare_first_part = False
        print(f"[DEBUG] 检测链式比较第一部分: is_chain_compare={is_chain_compare}, is_compound={if_struct.is_compound_condition}")
        if not is_chain_compare and not if_struct.is_compound_condition:
            print(f"[DEBUG] 进入第一部分检测逻辑")
            for other_struct in self.structures:
                if (hasattr(other_struct, 'is_compound_condition') and 
                    other_struct.is_compound_condition and
                    len(other_struct.condition_chain) > 1):
                    print(f"[DEBUG] 检查other_struct: entry={other_struct.entry_block.start_offset}")
                    # 检查当前结构的then_body是否包含other_struct的入口块
                    then_body_offsets = {b.start_offset for b in if_struct.then_body}
                    print(f"[DEBUG] then_body_offsets={then_body_offsets}, other_entry={other_struct.entry_block.start_offset}")
                    if other_struct.entry_block.start_offset in then_body_offsets:
                        # 检查other_struct是否包含COPY指令
                        has_copy_instr = False
                        for condition_block in other_struct.condition_chain:
                            for instr in condition_block.instructions:
                                if instr.opname == 'COPY' and instr.arg == 2:
                                    has_copy_instr = True
                                    break
                            if has_copy_instr:
                                break
                        print(f"[DEBUG] 找到包含关系, has_copy_instr={has_copy_instr}")
                        if has_copy_instr:
                            is_chain_compare = True
                            chain_compare_first_block = if_struct.entry_block
                            is_chain_compare_first_part = True
                            print(f"[DEBUG] 设置is_chain_compare_first_part=True")
                            break
        
        # [关键修复] 检测链式比较的后续部分
        # 如果当前结构是复合条件，且入口块被另一个结构的then_body包含，这可能是链式比较的后续部分
        chain_len = len(getattr(if_struct, 'condition_chain', []))
        print(f"[DEBUG] 检测链式比较后续部分: is_chain_compare={is_chain_compare}, is_compound={if_struct.is_compound_condition}, chain_len={chain_len}")
        if not is_chain_compare and if_struct.is_compound_condition and chain_len > 1:
            print(f"[DEBUG] 进入检测逻辑")
            for other_struct in self.structures:
                if (hasattr(other_struct, 'then_body') and 
                    other_struct != if_struct):
                    # 检查other_struct的then_body是否包含当前结构的入口块
                    then_body_offsets = {b.start_offset for b in other_struct.then_body}
                    print(f"[DEBUG] 检查other_struct: entry={other_struct.entry_block.start_offset}, then_body={then_body_offsets}, current_entry={if_struct.entry_block.start_offset}")
                    if if_struct.entry_block.start_offset in then_body_offsets:
                        # 检查当前结构是否包含COPY指令
                        has_copy_instr = False
                        for condition_block in if_struct.condition_chain:
                            for instr in condition_block.instructions:
                                if instr.opname == 'COPY' and instr.arg == 2:
                                    has_copy_instr = True
                                    break
                            if has_copy_instr:
                                break
                        print(f"[DEBUG] 找到包含关系, has_copy_instr={has_copy_instr}")
                        if has_copy_instr:
                            is_chain_compare = True
                            chain_compare_first_block = other_struct.entry_block
                            print(f"[DEBUG] 设置chain_compare_first_block={chain_compare_first_block.start_offset}")
                            break
        
        # [关键修复] 处理复合条件
        # 如果是复合条件，需要合并所有条件的表达式，并使用最后一个条件的then_body
        chain_len = len(getattr(if_struct, 'condition_chain', []))
        if if_struct.is_compound_condition and chain_len > 1:
            # [关键修复] 标记条件链中的所有块为已生成
            for condition_block in if_struct.condition_chain:
                self.generated_blocks.add(condition_block)
            
            # [关键修复] 处理链式比较
            # 链式比较如 0 < a < b < c < 100 应该被合并为一个Compare节点
            if is_chain_compare or chain_compare_first_block:
                print(f"[DEBUG] 处理链式比较: is_chain_compare={is_chain_compare}, chain_compare_first_block={chain_compare_first_block.start_offset if chain_compare_first_block else None}")
                print(f"[DEBUG] if_struct.condition_chain: {[b.start_offset for b in if_struct.condition_chain]}")
                # 提取链式比较的所有部分
                chain_left = None  # 最左边的操作数
                chain_ops = []     # 所有操作符
                chain_comparators = []  # 所有比较数
                
                # [关键修复] 如果有chain_compare_first_block，先处理它
                all_condition_blocks = []
                if chain_compare_first_block:
                    all_condition_blocks.append(chain_compare_first_block)
                all_condition_blocks.extend(if_struct.condition_chain)
                print(f"[DEBUG] all_condition_blocks: {[b.start_offset for b in all_condition_blocks]}")
                
                for i, condition_block in enumerate(all_condition_blocks):
                    # 查找LOAD_CONST, LOAD_GLOBAL等加载指令和COMPARE_OP指令
                    # [关键修复] 只提取最后一个COMPARE_OP之前的最后两个LOAD_*指令
                    loaded_values = []
                    compare_op = None
                    has_swap = False  # [关键修复] 检测是否有SWAP指令
                    
                    # 先找到最后一个COMPARE_OP的位置
                    last_compare_idx = -1
                    for idx, instr in enumerate(condition_block.instructions):
                        if instr.opname == 'COMPARE_OP':
                            last_compare_idx = idx
                            compare_op = self.expr_reconstructor._get_compare_op(instr.argval)
                    
                    # 只提取最后一个COMPARE_OP之前的LOAD_*指令
                    if last_compare_idx >= 0:
                        for instr in condition_block.instructions[:last_compare_idx+1]:
                            if instr.opname in ('LOAD_CONST', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_NAME'):
                                loaded_values.append(instr)
                            elif instr.opname == 'SWAP':
                                has_swap = True
                    
                    # [关键修复] 只保留最后两个LOAD_*指令（链式比较只需要两个操作数）
                    if len(loaded_values) > 2:
                        loaded_values = loaded_values[-2:]
                    
                    # 第一个块：提取左操作数和第一个比较数
                    if i == 0:
                        if len(loaded_values) >= 2:
                            # [关键修复] 如果有SWAP指令，操作数顺序需要交换
                            # 例如：0 < x 的字节码是 LOAD_CONST 0, LOAD_NAME x, SWAP 2, COPY 2, COMPARE_OP
                            # 加载顺序是 [0, x]，但有SWAP后实际比较是 0 < x
                            # 所以左操作数是 loaded_values[0]，比较数是 loaded_values[1]
                            if has_swap:
                                # 有SWAP：加载顺序就是比较顺序
                                chain_left = self.expr_reconstructor._load_instr_to_ast(loaded_values[0])
                                chain_comparators.append(self.expr_reconstructor._load_instr_to_ast(loaded_values[1]))
                            else:
                                # 无SWAP：正常顺序
                                chain_left = self.expr_reconstructor._load_instr_to_ast(loaded_values[0])
                                chain_comparators.append(self.expr_reconstructor._load_instr_to_ast(loaded_values[1]))
                            if compare_op:
                                chain_ops.append(compare_op)
                    else:
                        # 后续块：提取比较数
                        # 对于链式比较，每个块加载的是下一个比较数
                        # 例如：0 < a < b < c 中，后续块分别加载 b, c
                        if loaded_values:
                            # 第一个加载的是下一个比较数
                            chain_comparators.append(self.expr_reconstructor._load_instr_to_ast(loaded_values[0]))
                            if compare_op:
                                chain_ops.append(compare_op)
                
                # 构建链式比较表达式
                print(f"[DEBUG] 链式比较提取结果: chain_left={chain_left}, chain_ops={chain_ops}, chain_comparators={chain_comparators}")
                if chain_left and chain_ops and chain_comparators:
                    # 安全获取第一个块
                    if all_condition_blocks:
                        first_block = all_condition_blocks[0]
                    elif if_struct.condition_chain:
                        first_block = if_struct.condition_chain[0]
                    else:
                        first_block = if_struct.entry_block
                    condition = {
                        'type': 'Compare',
                        'left': chain_left,
                        'ops': chain_ops,
                        'comparators': chain_comparators,
                        'lineno': self._get_block_line(first_block)
                    }
                    # 跳过正常的复合条件处理
                    and_expressions = [condition]
                    print(f"[DEBUG] 构建链式比较条件: {condition}")
                else:
                    and_expressions = []
                    print(f"[DEBUG] 链式比较条件构建失败")
                
                # 跳过正常的复合条件处理，直接使用and_expressions
                pass
            else:
                # [关键修复] 将条件链分组为OR分隔的AND组
                # 对于复杂布尔表达式如 (a and b) or (not c and a) or (b or not a)
                # 需要将条件链分组为: [(a, b), (not c, a), (b, not a)]
                # 然后组内是AND关系，组间是OR关系
                
                and_groups = []  # 每个元素是一个AND组，包含多个条件块
                if if_struct.condition_chain:
                    current_and_group = [if_struct.condition_chain[0]]
                else:
                    # 处理空condition_chain的情况
                    current_and_group = []
                
                for i in range(1, len(if_struct.condition_chain)):
                    prev_block = if_struct.condition_chain[i-1]
                    curr_block = if_struct.condition_chain[i]
                    
                    # [关键修复] 判断prev_block和curr_block之间是AND还是OR关系
                    # 关键观察：在条件链中，连续的块通过fall-through连接
                    # 如果prev_block的fall-through是curr_block，它们是AND关系
                    # 如果prev_block的跳转目标是then_body，它是OR的结束
                    
                    # 获取prev_block的跳转指令
                    prev_jump = None
                    for instr in prev_block.instructions:
                        if instr.opname.startswith('POP_JUMP'):
                            prev_jump = instr
                            break
                    
                    is_or_separator = False
                    if prev_jump and prev_jump.argval is not None:
                        then_body_offsets = {b.start_offset for b in if_struct.then_body}
                        
                        # [关键修复] 判断OR分隔的正确逻辑：
                        # 1. OR的特征：prev_block的条件为真时直接跳到then_body
                        if prev_jump.argval in then_body_offsets and 'IF_TRUE' in prev_jump.opname:
                            is_or_separator = True
                        # 2. 检查prev_block的fall-through是否是curr_block
                        # fall-through块是不是跳转目标的那个后继
                        else:
                            fall_through = None
                            for succ in prev_block.successors:
                                if succ.start_offset != prev_jump.argval:
                                    fall_through = succ
                                    break
                            
                            # 如果fall-through不是curr_block，这是OR分隔
                            if fall_through != curr_block:
                                is_or_separator = True
                    
                    if is_or_separator:
                        # OR分隔，结束当前AND组，开始新组
                        and_groups.append(current_and_group)
                        current_and_group = [curr_block]
                    else:
                        # AND关系，继续当前组
                        current_and_group.append(curr_block)
                
                # 添加最后一个AND组
                if current_and_group:
                    and_groups.append(current_and_group)
                
                # 现在提取每个AND组的条件表达式
                and_expressions = []
                for group in and_groups:
                    if len(group) == 1:
                        # 单个块，需要判断是否是NOT条件
                        block = group[0]
                        is_not = False
                        for instr in block.instructions:
                            if 'POP_JUMP' in instr.opname and 'IF_TRUE' in instr.opname:
                                then_body_offsets = {b.start_offset for b in if_struct.then_body}
                                # 如果IF_TRUE的跳转目标不在then_body中，这是NOT条件
                                if instr.argval not in then_body_offsets:
                                    is_not = True
                                break
                        
                        cond = self._extract_condition_v2(block, is_not_condition=is_not)
                        if cond:
                            and_expressions.append(cond)
                    else:
                        # 多个块，需要组合成AND表达式
                        # 第一个块
                        first_block = group[0]
                        is_first_not = False
                        for instr in first_block.instructions:
                            if 'POP_JUMP' in instr.opname and 'IF_TRUE' in instr.opname:
                                # 检查跳转目标
                                then_body_offsets = {b.start_offset for b in if_struct.then_body}
                                if instr.argval not in then_body_offsets and instr.argval != group[1].start_offset:
                                    is_first_not = True
                                break
                        
                        expr = self._extract_condition_v2(first_block, is_not_condition=is_first_not)
                        
                        # 后续块
                        for i in range(1, len(group)):
                            block = group[i]
                            # 检查是否是not条件
                            is_not = False
                            for instr in block.instructions:
                                if 'POP_JUMP' in instr.opname and 'IF_TRUE' in instr.opname:
                                    then_body_offsets = {b.start_offset for b in if_struct.then_body}
                                    # 如果跳转目标不在then_body中，且不是下一个块，则是not
                                    if i + 1 < len(group):
                                        if instr.argval not in then_body_offsets and instr.argval != group[i+1].start_offset:
                                            is_not = True
                                    else:
                                        if instr.argval not in then_body_offsets:
                                            is_not = True
                                    break
                            
                            next_cond = self._extract_condition_v2(block, is_not_condition=is_not)
                            if next_cond and expr:
                                expr = {
                                    'type': 'BoolOp',
                                    'op': 'And',
                                    'values': [expr, next_cond],
                                    'lineno': self._get_block_line(block)
                                }
                            elif next_cond:
                                expr = next_cond
                        
                        if expr:
                            and_expressions.append(expr)
            
            # [关键修复] 使用and_expressions构建最终的条件表达式
            # and_expressions已经包含了按AND分组的表达式，现在需要用OR连接它们
            if len(and_expressions) == 0:
                # 如果没有提取到任何条件，使用占位符
                condition = {
                    'type': 'Name',
                    'id': f'<condition_{entry_block.id if entry_block else "unknown"}>',
                    'ctx': 'Load',
                    'lineno': self._get_block_line(entry_block)
                }
            elif len(and_expressions) == 1:
                condition = and_expressions[0]
            else:
                # 用OR连接所有的AND组
                condition = and_expressions[0]
                for expr in and_expressions[1:]:
                    condition = {
                        'type': 'BoolOp',
                        'op': 'Or',
                        'values': [condition, expr],
                        'lineno': self._get_block_line(entry_block)
                    }
            
            # [关键修复] 对于复合条件，也使用if_struct.then_body
            # 这样可以正确处理链式比较，其中then_body可能包含多个块
            # 例如：if 0 < x < 10: print(...) 的then_body是[JUMP_FORWARD块, print块]
            
            # [关键修复] 首先收集当前if结构中所有的嵌套if结构
            nested_structs_in_then = set()
            for block in if_struct.then_body:
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == block and struct != if_struct:
                        nested_structs_in_then.add(id(struct))
                        break
            
            # [关键修复] 对于链式比较，then_body中的第一个条件块已经作为条件表达式处理了
            # 不应该再被识别为嵌套的if结构，需要从nested_structs_in_then中排除
            skip_first_conditional = False
            first_then_block = None
            first_then_nested_struct_id = None
            # [关键修复] 收集链式比较中JUMP_FORWARD目标块的内容
            chain_compare_then_blocks = set()
            if is_chain_compare and if_struct.then_body:
                first_then_block = if_struct.then_body[0]
                has_jump = any(i.opname.startswith('POP_JUMP') for i in first_then_block.instructions)
                if has_jump and len(first_then_block.successors) == 2:
                    skip_first_conditional = True
                    # 找到这个块对应的嵌套结构，从nested_structs_in_then中排除
                    for struct in self.structures:
                        if isinstance(struct, IfStructure) and struct.entry_block == first_then_block and struct != if_struct:
                            first_then_nested_struct_id = id(struct)
                            nested_structs_in_then.discard(first_then_nested_struct_id)
                            break
                
                # [关键修复] 对于链式比较，如果then_body中的块只包含JUMP_FORWARD
                # 需要收集JUMP_FORWARD目标块的内容作为then分支
                for block in if_struct.then_body:
                    non_trivial = [i for i in block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                    if len(non_trivial) == 1 and non_trivial[0].opname == 'JUMP_FORWARD':
                        # 这是JUMP_FORWARD块，收集目标块
                        for succ in block.successors:
                            if succ not in if_struct.then_body and succ not in if_struct.else_body:
                                chain_compare_then_blocks.add(succ)
            
            # [关键修复] 收集所有嵌套结构的块（这些块不应该被当前结构处理）
            blocks_in_nested_structs = set()
            for struct in self.structures:
                if isinstance(struct, IfStructure) and id(struct) in nested_structs_in_then:
                    for b in struct.then_body:
                        blocks_in_nested_structs.add(b)
                    for b in struct.else_body:
                        blocks_in_nested_structs.add(b)
            
            print(f"[DEBUG] Processing then_body with {len(if_struct.then_body)} blocks for IfStructure {if_struct.entry_block.start_offset}")
            print(f"[DEBUG] All IfStructures: {[(s.entry_block.start_offset if s.entry_block else 'N/A') for s in self.structures if isinstance(s, IfStructure)]}")
            for block in if_struct.then_body:
                print(f"[DEBUG] _generate_if_ast: Processing block {block.start_offset} in then_body of IfStructure {if_struct.entry_block.start_offset}")
                print(f"[DEBUG] Processing block in then_body: {block}, type: {type(block)}, offset: {getattr(block, 'start_offset', 'N/A')}")
                # [关键修复] 检查块是否是某个if结构的入口块
                nested_if_struct = None
                for struct in self.structures:
                    if isinstance(struct, IfStructure):
                        print(f"[DEBUG] Checking IfStructure {struct.entry_block.start_offset if struct.entry_block else 'N/A'} against block {block.start_offset}, match={struct.entry_block == block}")
                        if struct.entry_block == block and struct != if_struct:
                            # [关键修复] 对于链式比较，如果这是then_body中的第一个条件块，不要识别为嵌套结构
                            if skip_first_conditional and block == first_then_block:
                                continue
                            nested_if_struct = struct
                            break
                
                # 如果块是嵌套if结构的入口，且该结构还没有被处理，递归处理它
                if nested_if_struct:
                    print(f"[DEBUG] 发现嵌套if结构: entry_block={nested_if_struct.entry_block.id}, processed={id(nested_if_struct) in self.processed_structure_ids}")
                    if id(nested_if_struct) not in self.processed_structure_ids:
                        # [关键修复] 首先生成入口块中的赋值语句
                        # 这些指令在条件检查之前执行，应该被包含在then_body中
                        print(f"[DEBUG] 处理嵌套if结构: entry_block={nested_if_struct.entry_block.id}")
                        if block not in self.generated_blocks:
                            self.generated_blocks.add(block)
                            # 只生成赋值相关的指令（STORE_NAME, STORE_FAST等）
                            # 这些指令在条件检查之前执行
                            assign_instrs = []
                            found_store = False
                            for instr in block.instructions:
                                # 跳过无用指令
                                if instr.opname in ('RESUME', 'CACHE', 'NOP'):
                                    continue
                                # 只收集赋值指令及其前置指令
                                if instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                                    assign_instrs.append(instr)
                                    found_store = True
                                    # 赋值语句结束，停止收集
                                    break
                                elif instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                                      'LOAD_CONST', 'LOAD_ATTR', 'BINARY_SUBSCR',
                                                      'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
                                                      'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET'):
                                    # 这些是指令的前置操作，也需要收集
                                    assign_instrs.append(instr)
                                else:
                                    # 遇到其他指令（如条件跳转），停止收集
                                    break
                            
                            # 只有找到完整的赋值语句（有STORE）才生成
                            if assign_instrs and found_store:
                                block_ast = self._generate_instructions_content(assign_instrs)
                                if block_ast:
                                    then_body.extend(block_ast)
                        
                        # 递归处理嵌套的if结构
                        # [关键修复] 只将entry_block标记为已生成，不要标记then_body和else_body
                        # 让递归调用_generate_if_ast来处理then_body和else_body
                        # [关键修复] 使用 _skip_processed_check=True 跳过重复检查
                        # [关键修复] 同时传递 _entry_block_processed=True，因为block已经被添加到generated_blocks
                        nested_if_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True, _entry_block_processed=True)
                        print(f"[DEBUG] 嵌套if结构生成完成: entry_block={nested_if_struct.entry_block.id}, ast={nested_if_ast is not None}")
                        if nested_if_ast:
                            print(f"[DEBUG] 添加嵌套if结构到then_body: len={len(nested_if_ast) if isinstance(nested_if_ast, list) else 1}")
                            if isinstance(nested_if_ast, list):
                                then_body.extend(nested_if_ast)
                            else:
                                then_body.append(nested_if_ast)
                    # [关键修复] 如果嵌套结构已经被处理，跳过，避免重复生成
                    continue
                
                # [关键修复] 如果块属于嵌套结构，跳过（由嵌套结构处理）
                if block in blocks_in_nested_structs:
                    continue
                
                # [关键修复] 处理普通块
                print(f"[DEBUG] Processing block {block.start_offset}, in generated_blocks: {block in self.generated_blocks}")
                
                # [关键修复] 检查块是否包含JUMP_BACKWARD指令（continue语句）
                has_jump_backward = any(instr.opname == 'JUMP_BACKWARD' for instr in block.instructions)
                
                # [关键修复] 检查块是否是while循环的条件块（但不是循环结构的header_block）
                # 特征：块包含POP_JUMP_FORWARD_IF_FALSE指令，且fall-through后继包含POP_JUMP_BACKWARD_IF_TRUE指令
                # [关键修复] 额外检查：fall-through后继必须是while循环的header_block
                # [关键修复] 额外检查：fall-through后继不应该包含实际代码（如print语句）
                is_while_condition = False
                for instr in block.instructions:
                    if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                        if instr.argval is not None:
                            # 找到fall-through后继
                            for succ in block.successors:
                                if succ.start_offset != instr.argval:
                                    # 检查fall-through后继是否包含POP_JUMP_BACKWARD_IF_TRUE指令
                                    has_backward_jump = False
                                    for succ_instr in succ.instructions:
                                        if 'POP_JUMP_BACKWARD_IF_TRUE' in succ_instr.opname:
                                            if succ_instr.argval is not None and succ_instr.argval == succ.start_offset:
                                                has_backward_jump = True
                                                break
                                    
                                    # [关键修复] 只有当fall-through后继是某个循环结构的header_block时，才是while条件块
                                    if has_backward_jump:
                                        is_loop_header = False
                                        for struct in self.structures:
                                            if isinstance(struct, LoopStructure):
                                                if struct.header_block == succ:
                                                    is_loop_header = True
                                                    break
                                        
                                        # [关键修复] 检查fall-through后继是否包含实际代码（如print语句）
                                        # 如果包含实际代码，这是一个if条件块，不是while条件块
                                        has_real_code = False
                                        for succ_instr in succ.instructions:
                                            if succ_instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_KW', 'PRECALL',
                                                                      'PRINT_EXPR', 'PRINT_ITEM', 'PRINT_NEWLINE'):
                                                has_real_code = True
                                                break
                                        
                                        # [关键修复] 只有当fall-through后继是循环header且不包含实际代码时，才是while条件块
                                        # 否则这是一个if条件块，fall-through后继只是包含内层while循环
                                        if is_loop_header and not has_real_code:
                                            is_while_condition = True
                                            print(f"[DEBUG] Block {block.start_offset} is_while_condition=True: fall-through succ {succ.start_offset} is loop header without real code")
                                        else:
                                            print(f"[DEBUG] Block {block.start_offset} is_while_condition=False: fall-through succ {succ.start_offset} is_loop_header={is_loop_header}, has_real_code={has_real_code}")
                                    
                                    if is_while_condition:
                                        break
                        if is_while_condition:
                            break
                
                # [关键修复] 即使块已经在generated_blocks中，如果包含JUMP_BACKWARD或是while循环的条件块，也要处理
                # 因为JUMP_BACKWARD可能是continue语句，需要在if body中生成
                # while循环的条件块需要生成while循环结构
                print(f"[DEBUG] Block {block.start_offset}: has_jump_backward={has_jump_backward}, is_while_condition={is_while_condition}")
                
                # [调试] 打印调用栈，查看Block 50何时被标记为已生成
                if block.start_offset == 50:
                    import traceback
                    print("[DEBUG] Block 50 call stack:")
                    traceback.print_stack()
                
                # [关键修复] 如果是递归调用（_skip_processed_check=True），即使块已经在generated_blocks中，也要处理
                # 因为这可能是嵌套if结构的then_body块，需要生成其内容
                if block not in self.generated_blocks or has_jump_backward or is_while_condition or _skip_processed_check:
                    # [关键修复] 检查块是否是任何循环结构的header_block
                    # 如果是，不将其标记为已生成，让循环结构来处理它
                    is_loop_header = False
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure) and struct.header_block == block:
                            is_loop_header = True
                            break
                    
                    # [关键修复] 只有在不是递归调用时，才将块标记为已生成
                    if not is_loop_header and block not in self.generated_blocks:
                        self.generated_blocks.add(block)
                    
                    # [关键修复] 检查块是否是while循环的条件块（但不是循环结构的header_block）
                    # 特征：块包含POP_JUMP_FORWARD_IF_FALSE指令，且fall-through后继包含POP_JUMP_BACKWARD_IF_TRUE指令
                    # [关键修复] 额外检查：fall-through后继必须是while循环的header_block
                    is_while_condition = False
                    for instr in block.instructions:
                        if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                            if instr.argval is not None:
                                # 找到fall-through后继
                                for succ in block.successors:
                                    if succ.start_offset != instr.argval:
                                        # 检查fall-through后继是否包含POP_JUMP_BACKWARD_IF_TRUE指令
                                        has_backward_jump = False
                                        for succ_instr in succ.instructions:
                                            if 'POP_JUMP_BACKWARD_IF_TRUE' in succ_instr.opname:
                                                if succ_instr.argval is not None and succ_instr.argval == succ.start_offset:
                                                    has_backward_jump = True
                                                    break
                                        
                                        # [关键修复] 只有当fall-through后继是某个循环结构的header_block时，才是while条件块
                                        if has_backward_jump:
                                            is_loop_header = False
                                            for struct in self.structures:
                                                if isinstance(struct, LoopStructure):
                                                    if struct.header_block == succ:
                                                        is_loop_header = True
                                                        break
                                            
                                            # [关键修复] 检查fall-through后继是否包含实际代码（如print语句）
                                            # 如果包含实际代码，这是一个if条件块，不是while条件块
                                            has_real_code = False
                                            for succ_instr in succ.instructions:
                                                if succ_instr.opname in ('CALL', 'CALL_FUNCTION', 'CALL_METHOD', 'CALL_KW', 'PRECALL',
                                                                          'PRINT_EXPR', 'PRINT_ITEM', 'PRINT_NEWLINE'):
                                                    has_real_code = True
                                                    break
                                            
                                            # [关键修复] 只有当fall-through后继是循环header且不包含实际代码时，才是while条件块
                                            # 否则这是一个if条件块，fall-through后继只是包含内层while循环
                                            if is_loop_header and not has_real_code:
                                                is_while_condition = True
                                                print(f"[DEBUG] Block {block.start_offset} is_while_condition=True (2nd check): fall-through succ {succ.start_offset} is loop header without real code")
                                            else:
                                                print(f"[DEBUG] Block {block.start_offset} is_while_condition=False (2nd check): fall-through succ {succ.start_offset} is_loop_header={is_loop_header}, has_real_code={has_real_code}")
                                        
                                        if is_while_condition:
                                            break
                            if is_while_condition:
                                break
                    
                    # [关键修复] 检查块是否包含内层while循环
                    # 特征：包含POP_JUMP_BACKWARD_IF_TRUE指令，跳转目标是块自己
                    has_inner_while = False
                    for instr in block.instructions:
                        if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                            if instr.argval is not None and instr.argval == block.start_offset:
                                has_inner_while = True
                                break
                    
                    if is_while_condition:
                        # [关键修复] 生成while循环
                        block_ast = self._generate_while_from_condition_block(block)
                    elif has_inner_while:
                        # [关键修复] 生成内层while循环
                        block_ast = self._generate_inner_while_from_block(block)
                    else:
                        block_ast = self._generate_block_content_v2(block)
                    
                    print(f"[DEBUG] Block {block.start_offset} generated AST: {block_ast}")
                    if block_ast:
                        if isinstance(block_ast, list):
                            then_body.extend(block_ast)
                        else:
                            then_body.append(block_ast)
                else:
                    print(f"[DEBUG] Block {block.start_offset} already in generated_blocks, skipping")
            
            # [关键修复] 处理链式比较中JUMP_FORWARD目标块的内容
            if chain_compare_then_blocks:
                for block in chain_compare_then_blocks:
                    if block not in self.generated_blocks:
                        self.generated_blocks.add(block)
                        block_ast = self._generate_block_content_v2(block)
                        if block_ast:
                            if isinstance(block_ast, list):
                                then_body.extend(block_ast)
                            else:
                                then_body.append(block_ast)
        else:
            # 处理普通条件的then_body
            # [关键修复] 首先收集当前if结构中所有的嵌套if结构和循环结构
            nested_structs_in_then = set()
            nested_loops_in_then = set()
            for block in if_struct.then_body:
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == block and struct != if_struct:
                        nested_structs_in_then.add(id(struct))
                        break
                    # [关键修复] 检查是否是嵌套循环结构的入口块
                    elif isinstance(struct, LoopStructure) and struct.entry_block == block:
                        nested_loops_in_then.add(id(struct))
                        break
            
            # [关键修复] 收集所有嵌套结构的块（这些块不应该被当前结构处理）
            blocks_in_nested_structs = set()
            for struct in self.structures:
                if isinstance(struct, IfStructure) and id(struct) in nested_structs_in_then:
                    for b in struct.then_body:
                        blocks_in_nested_structs.add(b)
                    for b in struct.else_body:
                        blocks_in_nested_structs.add(b)
                # [关键修复] 收集嵌套循环结构的块
                elif isinstance(struct, LoopStructure) and id(struct) in nested_loops_in_then:
                    if hasattr(struct, 'body_blocks'):
                        for b in struct.body_blocks:
                            blocks_in_nested_structs.add(b)
                    if hasattr(struct, 'else_body'):
                        for b in struct.else_body:
                            blocks_in_nested_structs.add(b)
            
            print(f"[DEBUG] Processing then_body for IfStructure {if_struct.entry_block.start_offset}, _skip_processed_check={_skip_processed_check}")
            for block in if_struct.then_body:
                print(f"[DEBUG] Processing then_body block {block.start_offset}, in generated_blocks: {block in self.generated_blocks}")
                # [关键修复] 检查块是否是某个if结构的入口块
                nested_if_struct = None
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == block and struct != if_struct:
                        nested_if_struct = struct
                        break
                
                # 如果块是嵌套if结构的入口，且该结构还没有被处理，递归处理它
                if nested_if_struct:
                    if id(nested_if_struct) not in self.processed_structure_ids:
                        # 递归处理嵌套的if结构
                        self.generated_blocks.add(block)
                        # [关键修复] 使用 _skip_processed_check=True 跳过重复检查
                        # [关键修复] 同时传递 _entry_block_processed=True，因为block已经被添加到generated_blocks
                        nested_if_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True, _entry_block_processed=True)
                        if nested_if_ast:
                            # [关键修复] 标记这是嵌套的if，不是elif
                            if isinstance(nested_if_ast, list):
                                for node in nested_if_ast:
                                    if node.get('type') == 'If':
                                        node['_is_nested_if'] = True
                                then_body.extend(nested_if_ast)
                            else:
                                if nested_if_ast.get('type') == 'If':
                                    nested_if_ast['_is_nested_if'] = True
                                then_body.append(nested_if_ast)
                    # [关键修复] 如果嵌套结构已经被处理，跳过，避免重复生成
                    continue
                
                # [关键修复] 检查块是否是某个循环结构的入口块或header块
                nested_loop_struct = None
                for struct in self.structures:
                    if isinstance(struct, LoopStructure):
                        if struct.entry_block == block:
                            nested_loop_struct = struct
                            break
                        # [关键修复] 检查块是否是循环结构的header_block
                        elif struct.header_block == block:
                            nested_loop_struct = struct
                            break
                
                # 如果块是嵌套循环结构的入口，且该结构还没有被处理，递归处理它
                if nested_loop_struct:
                    if id(nested_loop_struct) not in self.processed_structure_ids:
                        # 递归处理嵌套的循环结构
                        self.generated_blocks.add(block)
                        nested_loop_ast = self._generate_loop_ast(nested_loop_struct)
                        if nested_loop_ast:
                            if isinstance(nested_loop_ast, list):
                                then_body.extend(nested_loop_ast)
                            else:
                                then_body.append(nested_loop_ast)
                    # [关键修复] 如果嵌套结构已经被处理，跳过，避免重复生成
                    continue
                
                # [关键修复] 检查块是否是try-except结构的入口块
                nested_try_struct = None
                for struct in self.structures:
                    if isinstance(struct, TryExceptStructure) and struct.entry_block == block:
                        nested_try_struct = struct
                        break
                
                # 如果块是嵌套try-except结构的入口，且该结构还没有被处理，递归处理它
                if nested_try_struct:
                    if id(nested_try_struct) not in self.processed_structure_ids:
                        # 递归处理嵌套的try-except结构
                        self.generated_blocks.add(block)
                        nested_try_ast = self._generate_try_except_ast(nested_try_struct)
                        if nested_try_ast:
                            then_body.append(nested_try_ast)
                    # [关键修复] 如果嵌套结构已经被处理，跳过，避免重复生成
                    continue
                
                # [关键修复] 如果块属于嵌套结构，跳过（由嵌套结构处理）
                if block in blocks_in_nested_structs:
                    continue
                
                # [关键修复] 如果块已经在generated_blocks中，且不属于当前结构，跳过
                # 但如果是递归调用（_skip_processed_check=True），不要跳过，需要生成完整的AST
                # [关键修复] 对于NOP生成的if结构（如if True:），即使块已生成也要处理，因为块的内容就是then_body
                is_nop_generated = getattr(if_struct, 'is_nop_generated', False)
                if not _skip_processed_check and block in self.generated_blocks and not is_nop_generated:
                    continue
                
                # 处理普通块
                self.generated_blocks.add(block)
                
                # [关键修复] 检查是否是嵌套for循环的前驱块
                # 如果是，需要跳过迭代器表达式，避免生成孤立的range()等调用
                is_nested_for_predecessor = False
                for struct in self.structures:
                    if (hasattr(struct, 'header_block') and 
                        struct.header_block in block.successors and
                        struct.struct_type == ControlStructureType.FOR_LOOP and
                        struct.entry_block != block):  # 不是当前处理的结构
                        if any(instr.opname == 'GET_ITER' for instr in block.instructions):
                            is_nested_for_predecessor = True
                            break
                
                # [关键修复] 对于NOP生成的if结构，只生成非条件相关的指令（跳过NOP）
                if is_nop_generated:
                    # 过滤掉NOP、RESUME等指令，只生成实际的代码
                    filtered_instrs = [instr for instr in block.instructions 
                                       if instr.opname not in ('NOP', 'RESUME', 'CACHE')]
                    if filtered_instrs:
                        # 创建临时块来生成代码
                        from .basic_block import BasicBlock
                        temp_block = BasicBlock(block.start_offset)
                        temp_block.instructions = filtered_instrs
                        block_ast = self._generate_block_content_v2(temp_block)
                elif is_nested_for_predecessor:
                    # [关键修复] 对于嵌套for循环的前驱块，跳过迭代器表达式
                    block_ast = self._generate_block_content_skip_iterator(block)
                else:
                    block_ast = self._generate_block_content_v2(block)
                if block_ast:
                    if isinstance(block_ast, list):
                        then_body.extend(block_ast)
                    else:
                        then_body.append(block_ast)
        
        # 处理else_body
        else_body = []
        
        # [关键修复] 重置return生成标志，因为else分支是一个新的控制流路径
        # 这样可以确保else分支中的return语句被正确生成
        old_has_return_generated = self._has_return_generated
        self._has_return_generated = False
        
        # [关键修复] 首先收集当前if结构的else_body中所有的嵌套if结构和循环结构
        nested_structs_in_else = set()
        nested_loops_in_else = set()
        for block in if_struct.else_body:
            for struct in self.structures:
                if isinstance(struct, IfStructure) and struct.entry_block == block and struct != if_struct:
                    nested_structs_in_else.add(id(struct))
                    break
                # [关键修复] 检查是否是嵌套循环结构的入口块或header块
                elif isinstance(struct, LoopStructure):
                    if struct.entry_block == block:
                        nested_loops_in_else.add(id(struct))
                        break
                    # [关键修复] 检查块是否是循环结构的header_block
                    elif struct.header_block == block:
                        nested_loops_in_else.add(id(struct))
                        break
        
        # [关键修复] 收集所有嵌套结构的块（这些块不应该被当前结构处理）
        blocks_in_nested_structs_else = set()
        for struct in self.structures:
            if isinstance(struct, IfStructure) and id(struct) in nested_structs_in_else:
                for b in struct.then_body:
                    blocks_in_nested_structs_else.add(b)
                for b in struct.else_body:
                    blocks_in_nested_structs_else.add(b)
            # [关键修复] 收集嵌套循环结构的块
            elif isinstance(struct, LoopStructure) and id(struct) in nested_loops_in_else:
                # [关键修复] 对于for循环，entry_block可能不在body_blocks中
                # 需要将entry_block也添加到blocks_in_nested_structs_else中
                if hasattr(struct, 'entry_block') and struct.entry_block in if_struct.else_body:
                    blocks_in_nested_structs_else.add(struct.entry_block)
                if hasattr(struct, 'body_blocks'):
                    for b in struct.body_blocks:
                        blocks_in_nested_structs_else.add(b)
                if hasattr(struct, 'else_body'):
                    for b in struct.else_body:
                        blocks_in_nested_structs_else.add(b)
        
        # [关键修复] 收集elif_conditions中的块
        elif_condition_blocks = set()
        if hasattr(if_struct, 'elif_conditions') and if_struct.elif_conditions:
            for elif_block in if_struct.elif_conditions:
                elif_condition_blocks.add(elif_block)
        
        # [关键修复] 第一遍：处理普通块（非嵌套结构入口块）
        # 这样可以确保普通块在嵌套结构之前被处理，保持正确的顺序
        nested_if_structs = []  # 收集嵌套if结构，稍后处理
        nested_loop_structs = []  # [关键修复] 收集嵌套循环结构，稍后处理
        # 收集所有嵌套结构的入口块
        nested_entry_blocks = set()
        
        # 首先收集所有嵌套结构
        for block in if_struct.else_body:
            # 检查块是否是某个if结构的入口块
            block_struct = None
            for struct in self.structures:
                if isinstance(struct, IfStructure) and struct.entry_block == block and struct != if_struct:
                    block_struct = struct
                    break
                # [关键修复] 检查是否是嵌套循环结构的入口块或header块
                elif isinstance(struct, LoopStructure):
                    if struct.entry_block == block:
                        block_struct = struct
                        # [关键修复] 对于for循环，entry_block和header_block可能不同
                        # 需要将header_block也添加到nested_entry_blocks中
                        if struct.header_block != block and struct.header_block in if_struct.else_body:
                            nested_entry_blocks.add(struct.header_block)
                        break
                    # [关键修复] 检查块是否是循环结构的header_block
                    elif struct.header_block == block:
                        block_struct = struct
                        # [关键修复] 对于for循环，entry_block和header_block可能不同
                        # 如果entry_block也在else_body中，需要将entry_block也添加到nested_entry_blocks中
                        if struct.entry_block != block and struct.entry_block in if_struct.else_body:
                            nested_entry_blocks.add(struct.entry_block)
                        break
            
            # 如果块是嵌套结构的入口块，收集起来稍后处理
            if block_struct:
                if id(block_struct) not in self.processed_structure_ids:
                    if isinstance(block_struct, IfStructure):
                        nested_if_structs.append((block, block_struct))
                    elif isinstance(block_struct, LoopStructure):
                        # [关键修复] 检查该循环是否已经在nested_loop_structs中
                        # 对于for循环，entry_block和header_block可能都在else_body中
                        # 避免将同一个循环添加两次
                        already_added = any(id(existing_struct) == id(block_struct) for _, existing_struct in nested_loop_structs)
                        if not already_added:
                            nested_loop_structs.append((block, block_struct))
                    nested_entry_blocks.add(block)
                # [关键修复] 跳过嵌套结构的入口块，由嵌套结构处理
                continue
        
        # 然后处理普通块
        for block in if_struct.else_body:
            # 跳过嵌套结构的入口块
            if block in nested_entry_blocks:
                continue
            
            # [关键修复] 如果块属于嵌套结构，跳过（由嵌套结构处理）
            if block in blocks_in_nested_structs_else:
                continue
            
            # [关键修复] 如果块是elif_conditions中的块，跳过（由elif_conditions处理）
            if block in elif_condition_blocks:
                continue
            
            # [关键修复] 如果块是循环尾部（包含向后跳转指令），跳过
            # 这些块已经在循环结构中被处理了，不应该在if的else分支中重复处理
            # [关键修复] 但只有跳转到当前循环头部的BACKWARD才是循环尾部
            # 跳转到外层循环的BACKWARD不是循环尾部，应该被处理
            is_loop_tail = False
            for instr in block.instructions:
                if 'BACKWARD' in instr.opname:
                    # 检查跳转目标是否是当前循环的头部
                    jump_target = instr.offset + 2 + instr.arg * 2
                    # 查找包含当前块的循环
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure):
                            if struct.header_block and struct.header_block.start_offset == jump_target:
                                # 跳转到当前循环头部，是循环尾部
                                if block in (struct.body_blocks if hasattr(struct, 'body_blocks') else []):
                                    is_loop_tail = True
                                    break
                    if is_loop_tail:
                        break
            if is_loop_tail:
                continue
            
            # 如果块已经在generated_blocks中，跳过
            # 但如果是递归调用（_skip_processed_check=True），不要跳过，需要生成完整的AST
            if not _skip_processed_check and block in self.generated_blocks:
                continue
            
            # 处理普通块
            # [关键修复] 检查块是否是任何循环结构的header_block或entry_block
            # 如果是，不将其标记为已生成，让循环结构来处理它
            is_loop_header = False
            is_loop_entry = False
            for struct in self.structures:
                if isinstance(struct, LoopStructure):
                    if struct.header_block == block:
                        is_loop_header = True
                        break
                    # [关键修复] 对于for循环，entry_block可能包含GET_ITER指令
                    # 不应该在这里处理，而应该由循环结构来处理
                    if struct.entry_block == block and struct.entry_block != struct.header_block:
                        is_loop_entry = True
                        break
            
            # [关键修复] 如果是循环的entry_block，跳过它，让循环结构来处理
            if is_loop_entry:
                continue
            
            if not is_loop_header:
                self.generated_blocks.add(block)
            
            # [关键修复] 检查是否是跨块赋值（一个块计算表达式，下一个块存储结果）
            # 例如：Block 14 计算 not flag，Block 15 以 STORE_FAST 开头存储到 condition
            is_cross_block_assignment = False
            cross_block_value = None
            
            # 检查块是否以 STORE 指令开头
            first_instr = None
            for instr in block.instructions:
                if instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                    first_instr = instr
                    break
            
            if first_instr and first_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                # 检查前驱块是否在 else_body 中，且前驱块生成的是表达式
                for pred in block.predecessors:
                    if pred in if_struct.else_body:
                        # 生成前驱块的内容
                        pred_ast = self._generate_block_content_v2(pred)
                        if pred_ast and pred_ast.get('type') == 'Expr':
                            # 这是跨块赋值
                            is_cross_block_assignment = True
                            cross_block_value = pred_ast.get('value')
                            # 标记前驱块为已生成
                            if pred not in self.generated_blocks:
                                self.generated_blocks.add(pred)
                            # 从 else_body 中移除前驱块生成的表达式（因为它会被包含在赋值语句中）
                            else_body = [node for node in else_body if not (
                                node.get('type') == 'Expr' and 
                                node.get('value') == cross_block_value
                            )]
                            break
            
            if is_cross_block_assignment and cross_block_value:
                # 生成跨块赋值语句
                store_instr = first_instr
                else_body.append({
                    'type': 'Assign',
                    'targets': [{
                        'type': 'Name',
                        'id': store_instr.argval,
                        'ctx': 'Store',
                        'lineno': store_instr.starts_line
                    }],
                    'value': cross_block_value,
                    'lineno': store_instr.starts_line
                })
                
                # 生成块中剩余的内容（除了 STORE 指令）
                remaining_instrs = []
                found_store = False
                for instr in block.instructions:
                    if found_store:
                        remaining_instrs.append(instr)
                    elif instr.opname == store_instr.opname and instr.argval == store_instr.argval:
                        found_store = True
                
                if remaining_instrs:
                    remaining_ast = self._generate_instructions_content(remaining_instrs)
                    if remaining_ast:
                        else_body.extend(remaining_ast)
            else:
                # [关键修复] 检查块是否是嵌套for循环的前驱块
                # 如果是，跳过迭代器表达式
                is_nested_for_predecessor = False
                for struct in self.structures:
                    if (hasattr(struct, 'header_block') and 
                        struct.header_block in block.successors and
                        struct.struct_type == ControlStructureType.FOR_LOOP and
                        struct.entry_block != block):  # 不是当前处理的结构
                        if any(instr.opname == 'GET_ITER' for instr in block.instructions):
                            is_nested_for_predecessor = True
                            break
                
                # 生成普通块的内容
                if is_nested_for_predecessor:
                    # [关键修复] 对于嵌套for循环的前驱块，跳过迭代器表达式
                    block_ast = self._generate_block_content_skip_iterator(block)
                else:
                    block_ast = self._generate_block_content_v2(block)
                if block_ast:
                    if isinstance(block_ast, list):
                        else_body.extend(block_ast)
                    else:
                        else_body.append(block_ast)
        
        # [关键修复] 第二遍：处理嵌套的if结构
        # 这样可以确保嵌套结构在普通块之后被处理，保持正确的顺序
        for block, block_struct in nested_if_structs:
            
            # [关键修复] 首先生成入口块中的赋值语句（在条件检查之前执行）
            # 这些指令应该属于当前if的else分支，而不是嵌套if的一部分
            if block not in self.generated_blocks:
                self.generated_blocks.add(block)
                
                # [关键修复] 检查是否是跨块赋值（STORE_FAST在入口块，但计算在前驱块）
                # 例如：Block 14 计算 not flag，Block 15 以 STORE_FAST 开头存储到 condition
                cross_block_value = None
                first_instr = None
                for instr in block.instructions:
                    if instr.opname not in ('RESUME', 'CACHE', 'NOP'):
                        first_instr = instr
                        break
                
                if first_instr and first_instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                    # 入口块以 STORE 开头，可能是跨块赋值
                    # 检查前驱块是否在 else_body 中
                    for pred in block.predecessors:
                        if pred in if_struct.else_body:
                            # 前驱块在 else_body 中，需要检查是否是跨块赋值
                            # 生成前驱块的内容，获取计算结果
                            pred_ast = None
                            pred_was_generated = pred in self.generated_blocks
                            if not pred_was_generated:
                                self.generated_blocks.add(pred)
                                pred_ast = self._generate_block_content_v2(pred)
                            else:
                                # 前驱块已生成，尝试重新生成获取内容
                                pred_ast = self._generate_block_content_v2(pred)
                            
                            if pred_ast:
                                # 如果前驱块生成的是表达式，提取其值用于赋值
                                if isinstance(pred_ast, dict) and pred_ast.get('type') == 'Expr':
                                    cross_block_value = pred_ast.get('value')
                                    # [关键修复] 如果前驱块之前已经生成并添加到else_body，需要移除它
                                    if pred_was_generated:
                                        # 从else_body中移除对应的Expr节点
                                        else_body = [n for n in else_body if not (
                                            isinstance(n, dict) and 
                                            n.get('type') == 'Expr' and 
                                            n.get('value') == cross_block_value
                                        )]
                                elif isinstance(pred_ast, list) and len(pred_ast) == 1:
                                    if pred_ast[0].get('type') == 'Expr':
                                        cross_block_value = pred_ast[0].get('value')
                                        # [关键修复] 如果前驱块之前已经生成并添加到else_body，需要移除它
                                        if pred_was_generated:
                                            else_body = [n for n in else_body if not (
                                                isinstance(n, dict) and 
                                                n.get('type') == 'Expr' and 
                                                n.get('value') == cross_block_value
                                            )]
                            break
                    
                    # 生成所有赋值相关的指令（STORE_NAME, STORE_FAST等）
                    # 这些指令在条件检查之前执行
                    assign_instrs = []
                    current_instrs = []
                    for instr in block.instructions:
                        # 跳过无用指令
                        if instr.opname in ('RESUME', 'CACHE', 'NOP'):
                            continue
                        
                        # 如果是STORE指令，收集当前指令组并开始新的指令组
                        if instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                            current_instrs.append(instr)
                            assign_instrs.extend(current_instrs)
                            current_instrs = []
                        elif instr.opname in ('LOAD_NAME', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_DEREF',
                                              'LOAD_CONST', 'LOAD_ATTR', 'BINARY_SUBSCR',
                                              'BINARY_ADD', 'BINARY_SUBTRACT', 'BINARY_MULTIPLY', 'BINARY_DIVIDE',
                                              'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP', 'BUILD_SET',
                                              'BINARY_OP', 'CONTAINS_OP', 'UNARY_NOT', 'BINARY_OR', 'BINARY_AND'):
                            # 这些是指令的前置操作，也需要收集
                            current_instrs.append(instr)
                        else:
                            # 遇到其他指令（如条件跳转），停止收集
                            break
                    
                    # 检查是否找到完整的赋值语句
                    found_store = any(instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF') for instr in assign_instrs)
                    
                    # 只有找到完整的赋值语句（有STORE）才生成
                    if assign_instrs and found_store:
                        # 找到真正的STORE指令
                        store_instr = None
                        for instr in assign_instrs:
                            if instr.opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                                store_instr = instr
                                break
                        
                        if cross_block_value and store_instr:
                            # [关键修复] 跨块赋值：使用前驱块的计算结果创建赋值语句
                            else_body.append({
                                'type': 'Assign',
                                'targets': [{
                                    'type': 'Name',
                                    'id': store_instr.argval,
                                    'ctx': 'Store',
                                    'lineno': store_instr.starts_line
                                }],
                                'value': cross_block_value,
                                'lineno': store_instr.starts_line
                            })
                        else:
                            block_ast = self._generate_instructions_content(assign_instrs)
                            if block_ast:
                                else_body.extend(block_ast)
            
            # 递归处理嵌套的if结构
            # [关键修复] 将入口块标记为已生成，避免嵌套结构重复提取赋值语句
            # 入口块中的赋值语句已经在上面提取过了
            self.generated_blocks.add(block)
            # [关键修复] 使用 _skip_processed_check=True 跳过重复检查
            # [关键修复] 使用 _entry_block_processed=True 避免重复提取pre_condition_statements
            nested_if_ast = self._generate_if_ast(block_struct, is_top_level=False, _skip_processed_check=True, _entry_block_processed=True)
            if nested_if_ast:
                # [关键修复] 标记这是嵌套的if，不是elif
                if isinstance(nested_if_ast, list):
                    for node in nested_if_ast:
                        if node.get('type') == 'If':
                            node['_is_nested_if'] = True
                    else_body.extend(nested_if_ast)
                else:
                    if nested_if_ast.get('type') == 'If':
                        nested_if_ast['_is_nested_if'] = True
                    else_body.append(nested_if_ast)
        
        # [关键修复] 处理嵌套的循环结构
        for block, block_struct in nested_loop_structs:
            # [关键修复] 如果循环结构的entry_block或header_block是当前if结构的then_body或else_body的一部分
            # 这意味着循环是在if分支内部，应该在这里处理
            # 只有当循环结构不在当前if结构的then_body或else_body中时，才跳过
            in_current_if = (block_struct.header_block in if_struct.else_body or 
                            block_struct.header_block in if_struct.then_body or
                            block_struct.entry_block in if_struct.else_body or
                            block_struct.entry_block in if_struct.then_body)
            
            if not in_current_if:
                # 循环结构不在当前if结构中，跳过，让它由外部的循环处理逻辑来处理
                continue
            
            # [关键修复] 处理entry_block中的非迭代器代码
            # 当entry_block不在当前if结构的else_body中时，需要单独处理entry_block中的代码
            if (block_struct.entry_block != block_struct.header_block and 
                block_struct.entry_block not in self.generated_blocks and
                block_struct.entry_block not in if_struct.else_body and
                block_struct.entry_block not in if_struct.then_body):
                # entry_block不在当前if结构中，但可能被当前if结构的条件块引用
                # 检查entry_block是否是当前if结构的条件块的前驱
                for condition_block in if_struct.condition_chain:
                    if block_struct.entry_block in condition_block.successors:
                        # entry_block是条件块的后继，需要处理
                        entry_ast = self._generate_block_content_skip_iterator(block_struct.entry_block)
                        if entry_ast:
                            if isinstance(entry_ast, list):
                                else_body.extend(entry_ast)
                            else:
                                else_body.append(entry_ast)
                        self.generated_blocks.add(block_struct.entry_block)
                        break
            
            # 递归处理嵌套的循环结构
            self.generated_blocks.add(block)
            nested_loop_ast = self._generate_loop_ast(block_struct)
            if nested_loop_ast:
                if isinstance(nested_loop_ast, list):
                    else_body.extend(nested_loop_ast)
                else:
                    else_body.append(nested_loop_ast)
        
        # 移除特殊处理Block 14和Block 15的代码块
        # 现在使用 _generate_block_content_v2 方法生成赋值语句
        # 这样可以避免重复生成赋值语句
        
        # [关键修复] 对于链式比较，merge_block中的代码应该作为then分支的一部分
        # 例如：if 0 < a < b < c < 100: return True; return False
        # 其中 return True 在 merge_block 中（then分支）
        # return False 在 else_body 中
        if is_chain_compare and if_struct.merge_block:
            merge_block = if_struct.merge_block
            if merge_block not in self.generated_blocks:
                self.generated_blocks.add(merge_block)
                merge_ast = self._generate_block_content_v2(merge_block)
                if merge_ast:
                    if isinstance(merge_ast, list):
                        then_body.extend(merge_ast)
                    else:
                        then_body.append(merge_ast)
        
        # [关键修复] 恢复原来的return生成标志
        # 如果else分支中生成了return，或者之前已经生成了return，保持True
        self._has_return_generated = old_has_return_generated or self._has_return_generated
        
        # [关键修复] 检测复合条件模式
        # 如果当前if的body为空，且orelse包含一个if节点，可能是复合条件
        # 注意：当前禁用复合条件检测，因为它会错误地将elif链识别为复合条件
        # compound_condition = self._detect_compound_condition_in_ast(then_body, else_body)
        # if compound_condition:
        #     # 使用复合条件表达式
        #     if_node = {
        #         'type': 'If',
        #         'test': compound_condition,
        #         'body': self._get_compound_body(then_body, else_body),
        #         'orelse': self._get_compound_else_body(then_body, else_body),
        #         'lineno': self._get_block_line(entry_block)
        #     }
        # else:
        #     # 构建普通if节点
        #     if_node = {
        #         'type': 'If',
        #         'test': condition if condition else {'type': 'Constant', 'value': True},
        #         'body': then_body,
        #         'orelse': else_body,
        #         'lineno': self._get_block_line(entry_block)
        #     }
        
        # [关键修复] 检测elif链并转换为elif_test/elif_body格式
        # 递归提取所有elif链，返回最终的else分支
        def extract_elif_chain(orelse_nodes):
            """递归提取elif链，返回(elif_tests, elif_bodies, final_else)"""
            elif_tests = []
            elif_bodies = []
            
            # [关键修复] 处理多个连续的if节点（多个elif）
            # [关键修复] 使用副本，避免修改原始列表时影响迭代
            current_nodes = orelse_nodes[:]
            processed_count = 0  # 记录已处理的节点数
            
            while current_nodes:
                # 查找第一个if节点
                if_node = None
                if_index = -1
                for i, node in enumerate(current_nodes):
                    if node.get('type') == 'If':
                        if_node = node
                        if_index = i
                        break
                
                if if_node is None:
                    # 没有更多的if节点，返回剩余的节点作为else分支
                    # [关键修复] 从orelse_nodes中移除已处理的节点
                    for _ in range(processed_count):
                        if orelse_nodes:
                            orelse_nodes.pop(0)
                    return elif_tests, elif_bodies, current_nodes
                
                # [关键修复] 检查if节点是否是嵌套的if（不是elif）
                # 嵌套的if有 _is_nested_if 标记，应该作为独立的if语句处理
                if if_node.get('_is_nested_if'):
                    # 这是嵌套的if，不是elif，返回剩余的节点
                    # [关键修复] 不从orelse_nodes中移除嵌套的if节点，而是将它们保留在else块内
                    # 计算需要移除的非if节点数（只移除已处理的非if节点）
                    non_if_nodes_to_remove = if_index
                    # 从orelse_nodes中移除已处理的非if节点
                    for _ in range(non_if_nodes_to_remove):
                        if orelse_nodes and orelse_nodes[0].get('type') != 'If':
                            orelse_nodes.pop(0)
                    return elif_tests, elif_bodies, current_nodes[if_index:]
                
                # [关键修复] 检查if节点是否已经包含elif_test和elif_body
                # 如果是，直接使用这些属性，但只使用一次，防止递归重复
                if 'elif_test' in if_node and 'elif_body' in if_node and not if_node.get('_elif_extracted', False):
                    existing_elif_test = if_node['elif_test']
                    existing_elif_body = if_node['elif_body']
                    if isinstance(existing_elif_test, list):
                        elif_tests.extend(existing_elif_test)
                        elif_bodies.extend(existing_elif_body)
                    else:
                        elif_tests.append(existing_elif_test)
                        elif_bodies.append(existing_elif_body)
                    # 标记已经提取过
                    if_node['_elif_extracted'] = True
                    # 使用当前if节点的orelse作为下一个elif链
                    current_nodes = if_node.get('orelse', [])
                    processed_count += 1
                    continue
                
                # 检查是否是elif链（不是独立的if语句）
                if if_node.get('body') and len(if_node.get('body', [])) > 0:
                    # 这是elif链的一部分，提取elif的条件和body
                    elif_tests.append(if_node.get('test'))
                    elif_bodies.append(if_node.get('body'))
                    
                    # [关键修复] 如果if节点还包含elif_test和elif_body，也提取它们
                    if 'elif_test' in if_node and 'elif_body' in if_node:
                        existing_elif_test = if_node['elif_test']
                        existing_elif_body = if_node['elif_body']
                        if isinstance(existing_elif_test, list):
                            elif_tests.extend(existing_elif_test)
                            elif_bodies.extend(existing_elif_body)
                        else:
                            elif_tests.append(existing_elif_test)
                            elif_bodies.append(existing_elif_body)
                    
                    # 继续处理该if节点的orelse（更深层的elif或else分支）
                    current_nodes = if_node.get('orelse', [])
                    processed_count += 1
                else:
                    # 这不是elif链，返回剩余的节点
                    # [关键修复] 从orelse_nodes中移除已处理的节点
                    remaining = current_nodes
                    for _ in range(processed_count):
                        if orelse_nodes:
                            orelse_nodes.pop(0)
                    return elif_tests, elif_bodies, remaining
            
            # 处理完所有节点，没有else分支
            # [关键修复] 从orelse_nodes中移除所有节点
            for _ in range(processed_count):
                if orelse_nodes:
                    orelse_nodes.pop(0)
            return elif_tests, elif_bodies, []
        
        # [关键修复] 提取elif链
        elif_tests = []
        elif_bodies = []
        final_else = []
        
        # [关键修复] 使用结构化分析器检测到的elif_conditions
        # 无论是顶层还是嵌套的if结构，都应该处理elif_conditions
        print(f"[DEBUG] Processing elif_conditions for IfStructure {if_struct.entry_block.start_offset}, elif_conditions={[b.start_offset for b in if_struct.elif_conditions]}")
        if hasattr(if_struct, 'elif_conditions') and if_struct.elif_conditions:
            # 从elif_conditions中提取条件和body
            for elif_block in if_struct.elif_conditions:
                # [关键修复] 检查elif_block是否已经被识别为其他复合条件的condition_chain的一部分
                # 但只有当它不是该复合条件的入口块时才跳过
                # 如果是入口块，它应该被处理为独立的结构（如复合条件赋值）
                is_part_of_other_compound = False
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct != if_struct:
                        if hasattr(struct, 'condition_chain') and elif_block in struct.condition_chain:
                            # [关键修复] 只有当elif_block不是该复合条件的入口块时才跳过
                            if elif_block != struct.entry_block:
                                # 这个块是其他复合条件的非入口部分，跳过
                                is_part_of_other_compound = True
                                print(f"[DEBUG] elif_block {elif_block.start_offset} is part of other compound condition, skipping")
                                break
                if is_part_of_other_compound:
                    continue
                print(f"[DEBUG] Processing elif_block {elif_block.start_offset}")

                # [关键修复] 查找elif_block对应的IfStructure
                elif_if_struct = None
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == elif_block:
                        elif_if_struct = struct
                        break

                # [关键修复] 如果找到IfStructure且是复合条件，合并condition_chain中的所有条件
                if elif_if_struct and elif_if_struct.is_compound_condition and len(elif_if_struct.condition_chain) > 1:
                    # [关键修复] 合并condition_chain中的所有条件
                    conditions = []
                    for condition_block in elif_if_struct.condition_chain:
                        cond = self._extract_condition_v2(condition_block)
                        if cond:
                            conditions.append(cond)

                    # [关键修复] 构建复合条件表达式
                    if conditions:
                        elif_condition = conditions[0]
                        for i in range(1, len(conditions)):
                            # [关键修复] 确定操作符
                            # 检查当前块（conditions[i]）对应的condition_chain[i]的跳转指令
                            # 来确定与前一个条件的逻辑关系
                            is_and = True  # 默认AND
                            current_block = elif_if_struct.condition_chain[i]
                            prev_block = elif_if_struct.condition_chain[i-1]

                            # [关键修复] 检查前一个块的跳转指令类型
                            # POP_JUMP_IF_FALSE/JUMP_IF_FALSE_OR_POP → AND（条件为假时短路）
                            # POP_JUMP_IF_TRUE/JUMP_IF_TRUE_OR_POP → OR（条件为真时短路）
                            for instr in prev_block.instructions:
                                if instr.opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                                    # 普通AND：条件为假时跳转到else分支
                                    is_and = True
                                    break
                                elif instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE'):
                                    # 普通OR：条件为真时跳转到then分支
                                    is_and = False
                                    break
                                elif instr.opname == 'JUMP_IF_FALSE_OR_POP':
                                    # 复合AND：条件为假时短路
                                    is_and = True
                                    break
                                elif instr.opname == 'JUMP_IF_TRUE_OR_POP':
                                    # 复合OR：条件为真时短路
                                    is_and = False
                                    break

                            op = 'And' if is_and else 'Or'
                            elif_condition = {
                                'type': 'BoolOp',
                                'op': op,
                                'values': [elif_condition, conditions[i]],
                                'lineno': self._get_block_line(elif_block)
                            }

                        # [关键修复] 检查是否是复合条件赋值
                        compound_assignment = self._detect_compound_condition_assignment(elif_if_struct, elif_condition, elif_block)
                        if compound_assignment:
                            # [关键修复] 这是复合条件赋值，生成赋值语句而不是elif
                            if pre_condition_statements is None:
                                pre_condition_statements = []
                            pre_condition_statements.append(compound_assignment)
                            # 标记这个结构为已处理
                            self.processed_structure_ids.add(id(elif_if_struct))
                            # [关键修复] 标记condition_chain中的所有块为已生成
                            for condition_block in elif_if_struct.condition_chain:
                                self.generated_blocks.add(condition_block)
                            continue

                # 提取条件
                elif_condition = self._extract_condition_v2(elif_block)
                print(f"[DEBUG] Extracted elif_condition from block {elif_block.start_offset}: {elif_condition is not None}")
                if elif_condition:
                    elif_tests.append(elif_condition)
                    print(f"[DEBUG] Appended to elif_tests, length={len(elif_tests)}")

                    # 提取elif的body
                    elif_body = []
                    # 找到elif的then分支（fall-through块）
                    elif_jump = None
                    for instr in elif_block.instructions:
                        if instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                           'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                           'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                            elif_jump = instr
                            break

                    if elif_jump and elif_jump.argval is not None:
                        # [关键修复] 重置return生成标志，因为每个elif分支是一个新的控制流路径
                        old_elif_return_generated = self._has_return_generated
                        self._has_return_generated = False

                        # 找到fall-through块（then分支）
                        for succ in elif_block.successors:
                            if succ.start_offset != elif_jump.argval:
                                # [关键修复] 检查fall-through块是否是嵌套if结构的入口
                                nested_if_struct = None
                                for struct in self.structures:
                                    if isinstance(struct, IfStructure) and struct.entry_block == succ:
                                        nested_if_struct = struct
                                        break

                                if nested_if_struct and id(nested_if_struct) not in self.processed_structure_ids:
                                    # [关键修复] 标记嵌套结构为已处理，防止在generate()中重复处理
                                    self.processed_structure_ids.add(id(nested_if_struct))
                                    # 递归处理嵌套的if结构
                                    self.generated_blocks.add(succ)
                                    # [关键修复] 使用 _skip_processed_check=True 跳过重复检查
                                    nested_if_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True)
                                    if nested_if_ast:
                                        if isinstance(nested_if_ast, list):
                                            elif_body = nested_if_ast
                                        else:
                                            elif_body = [nested_if_ast]
                                elif nested_if_struct and id(nested_if_struct) in self.processed_structure_ids:
                                    # [关键修复] 嵌套结构已经被处理，但需要获取它的AST
                                    # 重新生成嵌套结构的AST（不标记为已处理）
                                    nested_if_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True)
                                    if nested_if_ast:
                                        if isinstance(nested_if_ast, list):
                                            elif_body = nested_if_ast
                                        else:
                                            elif_body = [nested_if_ast]
                                elif succ not in self.generated_blocks:
                                    # 生成then分支的内容
                                    self.generated_blocks.add(succ)
                                    block_ast = self._generate_block_content_v2(succ)
                                    if block_ast:
                                        if isinstance(block_ast, list):
                                            elif_body = block_ast
                                        else:
                                            elif_body = [block_ast]
                                else:
                                    # [关键修复] fall-through块已经在generated_blocks中
                                    # 但仍然需要生成elif_body
                                    # 尝试生成block content（不标记为已处理）
                                    block_ast = self._generate_block_content_v2(succ)
                                    if block_ast:
                                        if isinstance(block_ast, list):
                                            elif_body = block_ast
                                        else:
                                            elif_body = [block_ast]
                                break

                    # [关键修复] 恢复return生成标志
                    self._has_return_generated = old_elif_return_generated or self._has_return_generated

                    elif_bodies.append(elif_body)
                    print(f"[DEBUG] Appended to elif_bodies, length={len(elif_bodies)}")
            
            # [关键修复] 从else_body中排除elif_conditions对应的块
            # 剩余的块作为final_else
            # 但如果存在elif_conditions，final_else应该来自最后一个elif的else_body
            print(f"[DEBUG] Checking elif_conditions: hasattr={hasattr(if_struct, 'elif_conditions')}, value={getattr(if_struct, 'elif_conditions', 'N/A')}")
            if if_struct.elif_conditions:
                # 找到最后一个elif对应的IfStructure
                last_elif_block = if_struct.elif_conditions[-1]
                last_elif_struct = None
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == last_elif_block:
                        last_elif_struct = struct
                        break
                
                if last_elif_struct:
                    # 从最后一个elif的else_body中提取final_else
                    for block in last_elif_struct.else_body:
                        # 生成块的内容
                        if block not in self.generated_blocks:
                            self.generated_blocks.add(block)
                            block_ast = self._generate_block_content_v2(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    final_else.extend(block_ast)
                                else:
                                    final_else.append(block_ast)
                        else:
                            # 块已经被处理，尝试获取内容
                            block_ast = self._generate_block_content_v2(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    final_else.extend(block_ast)
                                else:
                                    final_else.append(block_ast)
                else:
                    # [关键修复] 找不到对应的IfStructure（elif被识别为条件但没有独立结构）
                    # 直接使用if_struct.else_body作为final_else
                    # 因为这些块已经在结构化分析阶段被正确识别为else分支
                    for block in if_struct.else_body:
                        if block not in self.generated_blocks:
                            self.generated_blocks.add(block)
                            block_ast = self._generate_block_content_v2(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    final_else.extend(block_ast)
                                else:
                                    final_else.append(block_ast)
                        else:
                            # 块已经被处理，尝试获取内容
                            block_ast = self._generate_block_content_v2(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    final_else.extend(block_ast)
                                else:
                                    final_else.append(block_ast)
        
        # [关键修复] 如果没有elif_conditions，从else_body中提取final_else
        # 这段代码在if块之外，确保无论是否有elif_conditions都会执行
        if not if_struct.elif_conditions:
            print(f"[DEBUG] Processing else_body for final_else (no elif_conditions), else_body length={len(else_body)}")
            remaining_else_body = []
            for node in else_body:
                print(f"[DEBUG] Processing node: type={node.get('type') if isinstance(node, dict) else type(node)}")
                if node.get('type') != 'If':
                    print(f"[DEBUG] Adding to final_else")
                    final_else.append(node)
                else:
                    remaining_else_body.append(node)
            else_body = remaining_else_body
            print(f"[DEBUG] After processing, final_else length={len(final_else)}, else_body length={len(else_body)}")
        elif is_top_level and not elif_tests:
            # [备用] 从AST节点中提取elif链（仅当没有从elif_conditions提取到数据时）
            elif_tests, elif_bodies, final_else = extract_elif_chain(else_body)
        
        # [关键修复] 检测复合条件赋值模式
        # 复合条件赋值的特征：复合条件的值被赋给变量，而不是用于控制流
        compound_assignment = self._detect_compound_condition_assignment(if_struct, condition, entry_block)
        print(f"[DEBUG] compound_assignment={compound_assignment is not None}")

        if compound_assignment:
            # [关键修复] compound_assignment可能是列表（包含merge_block中的其他语句）
            if isinstance(compound_assignment, list):
                # 返回条件之前的语句 + 复合条件赋值列表
                if pre_condition_statements:
                    return pre_condition_statements + compound_assignment
                else:
                    return compound_assignment
            else:
                # 生成复合条件赋值节点
                if_node = compound_assignment
        else:
            # [关键修复] 检测条件表达式（三元运算符）模式
            # 条件表达式的特征：then_body和else_body都只有一个赋值语句，且赋值给同一个变量
            if_exp_result = self._detect_conditional_expression(if_struct, condition, entry_block)

            if if_exp_result:
                # [关键修复] 处理返回值可能是列表的情况（Assign + Return）
                if isinstance(if_exp_result, list):
                    # 返回列表，包含Assign和Return
                    # 将Assign作为主要节点，Return需要单独处理
                    if_node = if_exp_result[0]  # Assign节点
                    # 将Return节点存储起来，稍后处理
                    if len(if_exp_result) > 1 and if_exp_result[1].get('type') == 'Return':
                        # 标记需要生成return语句
                        self._pending_return = if_exp_result[1]
                else:
                    # 返回单个节点
                    if_node = if_exp_result
            else:
                # [关键修复] 如果有elif链，需要从orelse中移除嵌套的if节点
                # 因为elif链已经通过elif_test/elif_body包含了这些条件
                filtered_orelse = else_body
                if elif_tests:
                    # 只保留非if的节点（真正的else分支）
                    filtered_orelse = [node for node in else_body if node.get('type') != 'If']
                
                # [关键修复] 处理常量折叠的if语句中的死代码消除问题
                # 当编译器优化if True: ... else: ...时，else分支被移除，但常量池中保留了else分支的常量
                # 我们需要重建else分支来保持常量池的一致性
                is_constant_folded = getattr(if_struct, 'is_constant_folded', False)
                if is_constant_folded and not filtered_orelse:
                    # 检查是否有未使用的常量（来自被优化掉的else分支）
                    unused_consts = self._get_unused_consts()
                    if unused_consts:
                        # 获取then_body中的赋值目标变量名
                        then_var_names = set()
                        for node in then_body:
                            if node.get('type') == 'Assign':
                                for target in node.get('targets', []):
                                    if target.get('type') == 'Name':
                                        then_var_names.add(target.get('id'))
                        
                        # 为每个未使用的常量创建else分支中的赋值语句
                        # 假设这些常量对应被优化掉的else分支中的赋值
                        for const in unused_consts:
                            # 为每个在then分支中赋值的变量创建else分支赋值
                            for var_name in then_var_names:
                                filtered_orelse.append({
                                    'type': 'Assign',
                                    'targets': [{
                                        'type': 'Name',
                                        'id': var_name,
                                        'ctx': 'Store',
                                        'lineno': self._get_block_line(entry_block)
                                    }],
                                    'value': {
                                        'type': 'Constant',
                                        'value': const,
                                        'lineno': self._get_block_line(entry_block)
                                    },
                                    'lineno': self._get_block_line(entry_block)
                                })
                            # 只处理第一个未使用的常量（通常只有一个）
                            break
                
                # 构建普通if节点
                # print(f"[DEBUG] 构建if节点: then_body长度={len(then_body)}, entry_block={entry_block.id if hasattr(entry_block, 'id') else 'N/A'}")
                # for i, node in enumerate(then_body):
                #     print(f"[DEBUG] then_body[{i}]: type={node.get('type')}")
                if_node = {
                    'type': 'If',
                    'test': condition if condition else {'type': 'Constant', 'value': True},
                    'body': then_body,
                    'orelse': filtered_orelse,
                    'lineno': self._get_block_line(entry_block)
                }

                # [关键修复] 如果有elif链，添加到if节点
                if elif_tests:
                    if_node['elif_test'] = elif_tests
                    if_node['elif_body'] = elif_bodies
                if final_else:
                    # [关键修复] 将final_else作为单独字段添加到if节点
                    # 这样_convert_if函数可以正确处理elif链的else分支
                    if_node['final_else'] = final_else
                    
                    # [关键修复] 同时添加到orelse中，以保持向后兼容
                    # [关键修复] 标记嵌套的if节点，避免被当作elif链处理
                    for node in final_else:
                        if node.get('type') == 'If':
                            node['_is_nested_if'] = True
                    
                    # [关键修复] 检查节点是否已经在orelse中，避免重复
                    existing_nodes = set()
                    for node in if_node['orelse']:
                        if node.get('type') == 'Assign':
                            # 使用目标和值作为唯一标识
                            targets = str(node.get('targets', ''))
                            value = str(node.get('value', ''))
                            existing_nodes.add((node['type'], targets, value))
                    
                    for node in final_else:
                        if node.get('type') == 'Assign':
                            targets = str(node.get('targets', ''))
                            value = str(node.get('value', ''))
                            node_id = (node['type'], targets, value)
                            if node_id not in existing_nodes:
                                if_node['orelse'].append(node)
                                existing_nodes.add(node_id)
                        else:
                            # 非Assign节点，直接添加
                            if node not in if_node['orelse']:
                                if_node['orelse'].append(node)
        
        # [关键修复] 标记结构为已处理
        self.processed_structure_ids.add(id(if_struct))
        
        # [关键修复] 缓存if节点的AST
        self._if_ast_cache[id(if_struct)] = if_node
        
        print(f"[DEBUG] _generate_if_ast finished for IfStructure {if_struct.entry_block.start_offset}, then_body={len(then_body)}, else_body={len(else_body)}, final_else={len(final_else)}, orelse={len(if_node.get('orelse', []))}")
        print(f"[DEBUG] else_body contents: {[n.get('type') if isinstance(n, dict) else str(n) for n in else_body]}")
        print(f"[DEBUG] final_else contents: {[n.get('type') if isinstance(n, dict) else str(n) for n in final_else]}")
        print(f"[DEBUG] elif_tests length={len(elif_tests)}, elif_bodies length={len(elif_bodies)}")
        if elif_tests:
            print(f"[DEBUG] elif_tests contents: {elif_tests}")
            print(f"[DEBUG] elif_bodies contents: {elif_bodies}")
        
        # 返回条件之前的语句 + if节点
        if pre_condition_statements:
            # [关键修复] 先append再返回，避免返回None
            pre_condition_statements.append(if_node)
            result = pre_condition_statements
        else:
            result = [if_node]
        
        # [关键修复] 如果有pending的return语句（来自条件表达式），添加到结果中
        if hasattr(self, '_pending_return') and self._pending_return:
            result.append(self._pending_return)
            self._pending_return = None  # 清除pending状态
        
        # print(f"[DEBUG] _generate_if_ast返回: entry_block={entry_block.id if entry_block else 'N/A'}, result长度={len(result)}")
        
        return result
    
    def _detect_compound_condition_in_ast(self, then_body: List[Dict], else_body: List[Dict]) -> Optional[Dict]:
        """
        检测复合条件模式
        
        复合条件的特征：
        - then_body为空或只包含pass/return
        - else_body包含一个if节点，且该if节点有实际的body
        
        Returns:
            复合条件表达式，如果不是复合条件则返回None
        """
        # 检查then_body是否为空或只包含pass/return
        if then_body and not all(
            node.get('type') in ('Pass', 'Return') or
            (node.get('type') == 'Expr' and node.get('value', {}).get('type') == 'Constant' and node.get('value', {}).get('value') is None)
            for node in then_body
        ):
            return None
        
        # 检查else_body是否包含一个if节点
        if len(else_body) != 1 or else_body[0].get('type') != 'If':
            return None
        
        nested_if = else_body[0]
        
        # 检查嵌套的if是否有实际的body
        nested_body = nested_if.get('body', [])
        if not nested_body:
            return None
        
        # 递归检测复合条件链
        conditions = []
        current = nested_if
        
        while current and current.get('type') == 'If':
            conditions.append(current.get('test'))
            
            # 检查是否有更多的条件
            current_orelse = current.get('orelse', [])
            if len(current_orelse) == 1 and current_orelse[0].get('type') == 'If':
                next_if = current_orelse[0]
                # 检查是否是复合条件的一部分
                current_body = current.get('body', [])
                if (not current_body or all(
                    node.get('type') in ('Pass', 'Return') or
                    (node.get('type') == 'Expr' and node.get('value', {}).get('type') == 'Constant' and node.get('value', {}).get('value') is None)
                    for node in current_body
                )):
                    current = next_if
                else:
                    break
            else:
                break
        
        # 如果只有一个条件，不是复合条件
        if len(conditions) < 2:
            return None
        
        # 构建复合条件表达式（使用and连接）
        result = conditions[0]
        for i in range(1, len(conditions)):
            result = {
                'type': 'BoolOp',
                'op': 'And',
                'values': [result, conditions[i]],
                'lineno': result.get('lineno')
            }
        
        return result
    
    def _detect_compound_condition_assignment(self, if_struct: IfStructure, condition: Dict, entry_block: BasicBlock) -> Optional[Dict]:
        """
        检测复合条件赋值模式

        复合条件赋值的特征：
        1. 是复合条件（is_compound_condition=True）
        2. then_body和else_body中的块都是条件块（有跳转指令），且都汇入merge_block
        3. merge_block执行STORE_FAST，将复合条件的值赋给变量
        4. [关键修复] then_body和else_body必须为空或只包含条件跳转，不包含实际的赋值语句

        例如：
        - condition = x > 0 and (y < 10 or z == 'test' and not flag)

        Returns:
            Assign 节点，如果不是复合条件赋值则返回 None
        """
        # 检查是否是复合条件
        if not if_struct.is_compound_condition:
            return None

        # [关键修复] 如果merge_block为None，尝试从条件链的后继块中找到包含STORE_FAST的块
        merge_block = if_struct.merge_block
        if not merge_block:
            # 收集所有条件链中最后一个块的后继
            if if_struct.condition_chain:
                last_cond_block = if_struct.condition_chain[-1]
                for succ in last_cond_block.successors:
                    # 检查这个后继块是否包含STORE_FAST
                    has_store = any(
                        instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL')
                        for instr in succ.instructions
                    )
                    if has_store:
                        merge_block = succ
                        break
            
            # 如果仍然没有找到，尝试从then_body中找
            if not merge_block and if_struct.then_body:
                for block in if_struct.then_body:
                    has_store = any(
                        instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL')
                        for instr in block.instructions
                    )
                    if has_store:
                        merge_block = block
                        break
        
        # 检查merge_block是否存在
        if not merge_block:
            return None
        
        # [关键修复] 区分链式比较和复合条件赋值
        # 链式比较（如 0 < x < 100）使用 POP_JUMP_FORWARD_IF_FALSE 指令
        # 复合条件赋值（如 condition = x > 0 and y < 10）使用 JUMP_IF_TRUE_OR_POP / JUMP_IF_FALSE_OR_POP 指令
        has_compound_assignment_jump = False
        for cond_block in if_struct.condition_chain:
            for instr in cond_block.instructions:
                if instr.opname in ('JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP'):
                    has_compound_assignment_jump = True
                    break
            if has_compound_assignment_jump:
                break
        
        if not has_compound_assignment_jump:
            # 这是链式比较，不是复合条件赋值
            return None

        # [关键修复] 检查then_body和else_body是否包含实际的赋值语句
        # 如果包含，这不是复合条件赋值，而是普通的if语句
        def has_actual_assignment_before_first_store(blocks):
            """检查块列表中第一个STORE之前是否包含实际的赋值语句"""
            for block in blocks:
                # 找到第一个STORE_FAST/STORE_NAME/STORE_GLOBAL的位置
                first_store_idx = -1
                for idx, instr in enumerate(block.instructions):
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                        first_store_idx = idx
                        break
                
                # 检查第一个STORE之前的指令
                for idx, instr in enumerate(block.instructions):
                    if first_store_idx >= 0 and idx >= first_store_idx:
                        break  # 只检查第一个STORE之前的指令
                    
                    # 如果包含STORE_FAST/STORE_NAME/STORE_GLOBAL且不是条件跳转的一部分
                    if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                        # 检查这个块是否有条件跳转指令
                        has_jump = any(
                            'JUMP' in i.opname or 'POP_JUMP' in i.opname
                            for i in block.instructions
                        )
                        # 如果没有跳转指令，这是一个实际的赋值
                        if not has_jump:
                            return True
                        # 如果有跳转指令，但STORE_FAST在跳转之后，这也是实际赋值
                        jump_idx = -1
                        store_idx = -1
                        for i, instr2 in enumerate(block.instructions):
                            if 'JUMP' in instr2.opname or 'POP_JUMP' in instr2.opname:
                                jump_idx = i
                            if instr2.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                                store_idx = i
                        if store_idx > jump_idx and jump_idx >= 0:
                            return True
            return False
        
        # [关键修复] 如果then_body或else_body在第一个STORE之前包含实际赋值，这不是复合条件赋值
        # 第一个STORE通常是复合条件赋值的目标变量（如condition）
        # 第一个STORE之后的赋值（如bitwise_and = x & y）是允许的
        if has_actual_assignment_before_first_store(if_struct.then_body):
            return None
        if has_actual_assignment_before_first_store(if_struct.else_body):
            return None

        # 检查merge_block是否包含STORE_FAST指令
        target_var = None
        for instr in merge_block.instructions:
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                target_var = instr.argval
                break

        if not target_var:
            return None

        # [关键修复] 检查then_body中的块是否都是条件块或复合条件的最后一部分，且都汇入merge_block
        # 如果是，则这些块也是复合条件的一部分
        def is_condition_or_last_part(block, merge_block):
            """检查块是否是条件块或复合条件的最后一部分，且汇入merge_block"""
            has_jump = False
            jump_target = None
            for instr in block.instructions:
                if 'JUMP' in instr.opname:
                    has_jump = True
                    jump_target = getattr(instr, 'argval', None)
                    break

            if has_jump:
                # 有跳转指令，检查跳转目标是否是merge_block
                if merge_block in block.successors:
                    return True, 'conditional'  # 条件块
                if jump_target == merge_block.start_offset:
                    return True, 'conditional'  # 条件块
                return False, None
            else:
                # 没有跳转指令，检查是否直接连接到merge_block
                # 这可能是复合条件的最后一部分（如 not flag）
                if len(block.successors) == 1 and merge_block in block.successors:
                    return True, 'last_part'  # 复合条件的最后一部分
                return False, None

        # [关键修复] 检查then_body中的所有块是否都是条件块或复合条件的最后一部分
        all_then_are_conditions = True
        then_body_types = []  # 记录每个块的类型
        for block in if_struct.then_body:
            is_valid, block_type = is_condition_or_last_part(block, merge_block)
            if not is_valid:
                all_then_are_conditions = False
                break
            then_body_types.append(block_type)

        # [关键修复] 检查else_body是否为空或只包含条件块
        def is_empty_or_conditions(body_blocks, merge_block_param):
            if not body_blocks:
                return True
            for block in body_blocks:
                is_valid, _ = is_condition_or_last_part(block, merge_block_param)
                if not is_valid:
                    return False
            return True

        if not is_empty_or_conditions(if_struct.else_body, merge_block):
            return None

        # [关键修复] 如果then_body中的块都是条件块或复合条件的最后一部分，将它们合并到条件表达式中
        if all_then_are_conditions and if_struct.then_body:
            # 提取then_body中所有块的表达式
            then_conditions = []
            for block in if_struct.then_body:
                cond = self._extract_condition_v2(block)
                if cond:
                    then_conditions.append(cond)

            # 合并条件表达式
            # 需要根据块的类型确定操作符（AND或OR）
            if then_conditions:
                for i, block in enumerate(if_struct.then_body):
                    block_type = then_body_types[i]

                    # 确定操作符
                    if block_type == 'conditional':
                        # 条件块，根据跳转指令类型确定操作符
                        is_and = False
                        for instr in block.instructions:
                            if instr.opname in ('POP_JUMP_IF_FALSE', 'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_BACKWARD_IF_FALSE', 'JUMP_IF_FALSE_OR_POP'):
                                is_and = True
                                break
                            elif instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_TRUE', 'JUMP_IF_TRUE_OR_POP'):
                                is_and = False
                                break
                            elif instr.opname in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE'):
                                # None检查：如果为None则跳转（相当于条件为假）
                                is_and = True
                                break
                            elif instr.opname in ('POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'):
                                # Not None检查：如果不为None则跳转（相当于条件为真）
                                is_and = False
                                break
                        op = 'And' if is_and else 'Or'
                    else:
                        # 复合条件的最后一部分（如 not flag），默认使用AND
                        op = 'And'

                    condition = {
                        'type': 'BoolOp',
                        'op': op,
                        'values': [condition, then_conditions[i]],
                        'lineno': self._get_block_line(entry_block)
                    }

        # [关键修复] 处理merge_block中的其他语句（除了STORE_FAST）
        # 例如位运算赋值语句
        merge_block_statements = []
        store_fast_found = False
        for instr in merge_block.instructions:
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                if not store_fast_found:
                    # 第一个STORE_FAST是复合条件赋值，跳过
                    store_fast_found = True
                    continue
                else:
                    # 后续的STORE_FAST是其他赋值，需要处理
                    # 这里需要重建赋值语句，但简化处理：先标记块，让后续处理
                    break
        
        # 如果merge_block中有其他语句（除了第一个STORE_FAST），先生成它们
        if len(merge_block.instructions) > 1:
            # 找到第一个STORE_FAST的位置
            store_fast_idx = -1
            for i, instr in enumerate(merge_block.instructions):
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                    store_fast_idx = i
                    break
            
            # 如果STORE_FAST不是最后一条指令，处理后面的指令
            if store_fast_idx >= 0 and store_fast_idx < len(merge_block.instructions) - 1:
                # 提取STORE_FAST之后的指令
                remaining_instrs = merge_block.instructions[store_fast_idx + 1:]
                
                # [关键修复] 检查是否有条件跳转指令（嵌套if）
                jump_idx = -1
                for i, instr in enumerate(remaining_instrs):
                    if instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                       'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                       'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                        jump_idx = i
                        break
                
                if jump_idx >= 0:
                    # [关键修复] 有嵌套if结构，但需要区分位运算赋值和if条件
                    # 位运算赋值：LOAD_GLOBAL x, LOAD_GLOBAL y, BINARY_OP, STORE_FAST bitwise_and
                    # if条件：LOAD_CONST name, LOAD_GLOBAL my_dict, CONTAINS_OP, POP_JUMP_FORWARD_IF_FALSE
                    
                    # 找到所有完整的赋值语句（以STORE_FAST结尾）
                    assignment_end_indices = []
                    for i, instr in enumerate(remaining_instrs[:jump_idx]):
                        if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                            assignment_end_indices.append(i)
                    
                    # 处理每个完整的赋值语句
                    last_end = 0
                    for end_idx in assignment_end_indices:
                        # 提取从last_end到end_idx的指令（包含STORE_FAST）
                        assignment_instrs = remaining_instrs[last_end:end_idx + 1]
                        if assignment_instrs:
                            # [关键修复] 直接调用_process_instruction_sequence处理完整赋值
                            assignment_ast = self._process_instruction_sequence(assignment_instrs)
                            merge_block_statements.extend(assignment_ast)
                        last_end = end_idx + 1
                    
                    # [关键修复] 处理merge_block中的嵌套if结构
                    # 查找merge_block对应的IfStructure
                    from core.cfg.structured_analyzer import IfStructure
                    nested_if_struct = None
                    for struct in self.structures:
                        if isinstance(struct, IfStructure) and struct.entry_block == merge_block:
                            nested_if_struct = struct
                            break
                    
                    if nested_if_struct:
                        # [关键修复] 递归调用_generate_if_ast处理嵌套if结构
                        # 标记merge_block为已处理，避免重复处理
                        self.generated_blocks.add(merge_block)
                        nested_if_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True, _entry_block_processed=True)
                        if nested_if_ast:
                            merge_block_statements.extend(nested_if_ast)
                else:
                    # 没有嵌套if结构，生成所有指令的AST
                    # [关键修复] 直接调用_process_instruction_sequence，避免_generate_instructions_content中的栈问题
                    remaining_ast = self._process_instruction_sequence(remaining_instrs)
                    merge_block_statements.extend(remaining_ast)

        # [关键修复] 只标记merge_block中的第一个STORE_FAST为已处理
        # 不标记整个merge_block，因为merge_block中可能还包含其他代码（如嵌套if）
        # 这些代码需要由_generate_if_ast函数处理
        for block in if_struct.else_body:
            self.generated_blocks.add(block)
        # 注意：不标记then_body和merge_block，因为它们可能包含其他需要处理的代码

        # 构建赋值语句
        compound_assign = {
            'type': 'Assign',
            'targets': [{'type': 'Name', 'id': target_var, 'ctx': 'Store'}],
            'value': condition,
            'lineno': self._get_block_line(entry_block)
        }
        
        # [关键修复] 如果有merge_block中的其他语句，返回列表
        if merge_block_statements:
            return [compound_assign] + merge_block_statements
        else:
            return compound_assign

    def _detect_conditional_expression(self, if_struct: IfStructure, condition: Dict, entry_block: BasicBlock) -> Optional[Dict]:
        """
        检测条件表达式（三元运算符）模式

        条件表达式的特征：
        1. then_body 和 else_body 都只有一个块
        2. 每个块都只有一个值加载（不是完整的赋值语句），或者 then 块包含嵌套的条件表达式
        3. 条件表达式之后有一个共同的块，包含赋值语句

        例如：
        - result = '正数' if x > 0 else '非正数'
        - value = (x if x > 0 else 0) if x is not None else -1  (嵌套条件表达式)

        Returns:
            IfExp 节点，如果不是条件表达式则返回 None
        """
        # 从 if_struct 获取 then_body 和 else_body 块
        then_blocks = if_struct.then_body
        else_blocks = if_struct.else_body
        
        # [关键修复] 处理嵌套条件表达式的情况
        # 对于嵌套条件表达式如 (x if x > 0 else 0) if x is not None else -1
        # 外层的 then_body 可能是空的，因为结构化分析器将内层条件表达式识别为独立的结构
        # 这种情况下，我们需要从 entry_block 的后继中找到内层条件表达式的 entry_block
        
        # 检查 then_body 是否为空或包含条件块
        is_nested_conditional = False
        nested_if_struct = None
        then_block = None
        
        if len(then_blocks) == 1:
            then_block = then_blocks[0]
            then_instrs = [i for i in then_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
            
            # 检查 then_block 是否是嵌套条件表达式
            has_pop_jump = any(i.opname.startswith('POP_JUMP') for i in then_instrs)
            has_two_successors = len(then_block.successors) == 2
            
            if has_pop_jump and has_two_successors:
                # 查找对应的 IfStructure
                for struct in self.structures:
                    if isinstance(struct, IfStructure) and struct.entry_block == then_block:
                        is_nested_conditional = True
                        nested_if_struct = struct
                        break
        
        # [关键修复] 如果 then_body 为空，检查 entry_block 的后继是否包含条件块
        if len(then_blocks) == 0 and len(else_blocks) == 1:
            # 获取 entry_block 的跳转指令
            jump_instr = None
            for instr in entry_block.instructions:
                if instr.opname.startswith('POP_JUMP'):
                    jump_instr = instr
                    break
            
            if jump_instr:
                # 找到 fall-through 后继（即 then_branch）
                for succ in entry_block.successors:
                    if jump_instr.argval is not None and succ.start_offset != jump_instr.argval:
                        # 这是 fall-through 后继，可能是内层条件表达式的 entry_block
                        succ_instrs = [i for i in succ.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                        has_pop_jump = any(i.opname.startswith('POP_JUMP') for i in succ_instrs)
                        has_two_successors = len(succ.successors) == 2
                        
                        if has_pop_jump and has_two_successors:
                            # 这是一个嵌套的条件表达式
                            is_nested_conditional = True
                            then_block = succ
                            
                            # 查找对应的 IfStructure
                            for struct in self.structures:
                                if isinstance(struct, IfStructure) and struct.entry_block == succ:
                                    nested_if_struct = struct
                                    break
                            break
        
        # [关键修复] 处理复合条件的情况（如 b if b > 0 and c > 0 else -1）
        # 复合条件的特征：
        # 1. then_body 有多个块，每个块都是条件块
        # 2. 所有 then_body 中的块都汇入同一个 merge_block
        # 3. merge_block 包含赋值语句
        is_compound_conditional = False
        compound_then_value = None
        
        if len(then_blocks) > 1 and len(else_blocks) == 1:
            # 检查 then_body 中的所有块是否都是条件块（有 POP_JUMP 指令）
            all_are_conditional = all(
                any(i.opname.startswith('POP_JUMP') for i in b.instructions)
                for b in then_blocks
            )
            
            if all_are_conditional:
                # 找到 then_body 中所有块的共同后继（merge_block）
                common_succs = None
                for block in then_blocks:
                    succs = set(s.start_offset for s in block.successors)
                    if common_succs is None:
                        common_succs = succs
                    else:
                        common_succs &= succs
                
                if common_succs:
                    # 找到 merge_block
                    merge_block = None
                    for block in then_blocks[0].successors:
                        if block.start_offset in common_succs:
                            merge_block = block
                            break
                    
                    if merge_block:
                        # 检查 merge_block 是否包含值加载（条件表达式的 then 值）
                        merge_instrs = [i for i in merge_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                        if len(merge_instrs) >= 1 and merge_instrs[0].opname.startswith('LOAD_'):
                            # 这是复合条件表达式模式
                            is_compound_conditional = True
                            compound_then_value = self._instr_to_ast(merge_instrs[0])
                            # 使用 merge_block 作为 then_block
                            then_block = merge_block
        
        # 检查 then_body 和 else_body 是否都只有一个块
        # [关键修复] 对于嵌套条件表达式，允许 then_body 为空或包含条件块
        # [关键修复] 对于复合条件表达式，允许 then_body 有多个块
        if len(then_blocks) > 1 and not is_compound_conditional:
            return None
        if len(else_blocks) != 1:
            return None
        
        # 如果没有找到 then_block（非嵌套情况），使用 then_body 中的块
        if then_block is None and len(then_blocks) == 1:
            then_block = then_blocks[0]
        
        if then_block is None:
            return None
        
        # [关键修复] 获取 else_block（else_blocks 只有一个元素）
        else_block = else_blocks[0]
        
        # [关键修复] 检查 then 和 else 块是否只包含值加载（LOAD_CONST）
        # 这是条件表达式的特征
        then_instrs = [i for i in then_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
        else_instrs = [i for i in else_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
        
        # [关键修复] 检查 then 块是否有 1-2 个指令（LOAD_* 和可选的 JUMP_FORWARD）
        # else 块应该有 1 个指令（LOAD_*）
        # [关键修复] 支持嵌套条件表达式：then 块可能包含完整的条件表达式结构
        if len(then_instrs) < 1 or len(then_instrs) > 2:
            if not is_nested_conditional:
                return None
        
        # [关键修复] 支持嵌套条件表达式：else 块可能包含 1-2 个指令（LOAD_* 和可选的 JUMP_FORWARD）
        if len(else_instrs) < 1 or len(else_instrs) > 2:
            return None
        
        # [关键修复] 处理嵌套条件表达式
        if is_nested_conditional:
            if nested_if_struct:
                # 递归检测内层条件表达式
                # 首先提取内层条件的条件表达式
                inner_condition = self._extract_condition_v2(then_block)
                if not inner_condition:
                    return None
                
                # 递归调用检测内层条件表达式
                inner_if_exp = self._detect_conditional_expression(nested_if_struct, inner_condition, then_block)
                if not inner_if_exp:
                    return None
                
                # 内层条件表达式的值就是 then_value
                if isinstance(inner_if_exp, list):
                    inner_assign = inner_if_exp[0]
                else:
                    inner_assign = inner_if_exp
                
                if inner_assign.get('type') == 'Assign' and inner_assign.get('value', {}).get('type') == 'IfExp':
                    then_value = inner_assign['value']
                else:
                    return None
                
                # 标记内层结构为已处理
                self.processed_structure_ids.add(id(nested_if_struct))
                for b in nested_if_struct.then_body:
                    self.generated_blocks.add(b)
                for b in nested_if_struct.else_body:
                    self.generated_blocks.add(b)
            else:
                # [关键修复] 如果没有找到对应的 IfStructure，直接从 then_block 的后继构建内层条件表达式
                # 这对于嵌套条件表达式如 (x if x > 0 else 0) if x is not None else -1 是必需的
                # 因为结构化分析器可能没有将内层条件表达式识别为独立的 IfStructure
                
                # 获取 then_block 的跳转指令
                inner_jump = None
                for instr in then_block.instructions:
                    if instr.opname.startswith('POP_JUMP'):
                        inner_jump = instr
                        break
                
                if not inner_jump:
                    return None
                
                # 确定内层的 then_block 和 else_block
                inner_then_block = None
                inner_else_block = None
                for succ in then_block.successors:
                    if inner_jump.argval is not None and succ.start_offset == inner_jump.argval:
                        # 跳转目标
                        if 'IF_FALSE' in inner_jump.opname or 'IF_NONE' in inner_jump.opname:
                            inner_else_block = succ
                        else:
                            inner_then_block = succ
                    else:
                        # fall-through
                        if 'IF_FALSE' in inner_jump.opname or 'IF_NONE' in inner_jump.opname:
                            inner_then_block = succ
                        else:
                            inner_else_block = succ
                
                if not inner_then_block or not inner_else_block:
                    return None
                
                # 提取内层条件
                inner_condition = self._extract_condition_v2(then_block)
                if not inner_condition:
                    return None
                
                # 提取内层 then_value 和 else_value
                inner_then_instrs = [i for i in inner_then_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                inner_else_instrs = [i for i in inner_else_block.instructions if i.opname not in ('RESUME', 'CACHE', 'NOP')]
                
                inner_then_load = None
                for instr in inner_then_instrs:
                    if instr.opname.startswith('LOAD_'):
                        inner_then_load = instr
                        break
                
                inner_else_load = None
                for instr in inner_else_instrs:
                    if instr.opname.startswith('LOAD_'):
                        inner_else_load = instr
                        break
                
                if not inner_then_load or not inner_else_load:
                    return None
                
                inner_then_value = self._instr_to_ast(inner_then_load)
                inner_else_value = self._instr_to_ast(inner_else_load)
                
                if not inner_then_value or not inner_else_value:
                    return None
                
                # 构建内层 IfExp
                then_value = {
                    'type': 'IfExp',
                    'test': inner_condition,
                    'body': inner_then_value,
                    'orelse': inner_else_value,
                    'lineno': self._get_block_line(then_block)
                }
                
                # 标记内层块为已处理
                self.generated_blocks.add(then_block)
                self.generated_blocks.add(inner_then_block)
                self.generated_blocks.add(inner_else_block)
        elif is_compound_conditional and compound_then_value:
            # [关键修复] 使用复合条件的 then 值
            then_value = compound_then_value
            # 标记所有 then_body 中的块为已处理
            for b in then_blocks:
                self.generated_blocks.add(b)
        else:
            # 获取值加载指令（忽略 JUMP_FORWARD）
            then_load_instr = None
            for instr in then_instrs:
                if instr.opname.startswith('LOAD_'):
                    then_load_instr = instr
                    break
            
            if not then_load_instr:
                return None
            
            # 提取 then 的值
            then_value = self._instr_to_ast(then_load_instr)
            if not then_value:
                return None
        
        else_load_instr = else_instrs[0]
        
        # 检查是否是值加载指令
        if not else_load_instr.opname.startswith('LOAD_'):
            return None
        
        # 提取 else 的值
        else_value = self._instr_to_ast(else_load_instr)
        if not else_value:
            return None
        
        # 找到条件表达式之后的共同块（即 then 和 else 都跳转到的块）
        # 这个块应该包含赋值语句
        common_block = self._find_common_successor(then_block, else_block)
        
        if not common_block:
            return None
        
        # 检查共同块是否包含赋值语句
        common_content = self._extract_block_content(common_block)
        
        target_var = None
        
        if len(common_content) == 1:
            common_stmt = common_content[0]
            # 检查是否是赋值语句
            if common_stmt.get('type') == 'Assign':
                targets = common_stmt.get('targets', [])
                if len(targets) == 1:
                    target = targets[0]
                    if target.get('type') == 'Name':
                        target_var = target.get('id')
        
        # [关键修复] 如果共同块没有生成赋值语句，检查是否只包含 STORE_FAST
        if target_var is None:
            store_instr = None
            for instr in common_block.instructions:
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                    store_instr = instr
                    break
            
            if store_instr:
                target_var = store_instr.argval
            else:
                # [关键修复] 检查是否是lambda函数中的条件表达式
                # lambda函数中的条件表达式直接返回，没有STORE_FAST
                # 特征：common_block包含RETURN_VALUE
                has_return = any(instr.opname in ('RETURN_VALUE', 'RETURN_CONST') for instr in common_block.instructions)
                if has_return:
                    # 使用特殊标记表示这是lambda返回值
                    target_var = '__lambda_result__'
                else:
                    return None
        
        if not then_value or not else_value:
            return None
        
        # 标记块为已处理
        self.generated_blocks.add(then_block)
        self.generated_blocks.add(else_block)
        # [关键修复] 不要将common_block完全标记为已处理
        # 只标记STORE_FAST指令，让RETURN_VALUE等指令由后续代码处理
        # self.generated_blocks.add(common_block)
        
        # [关键修复] 检查common_block中是否有RETURN_VALUE指令
        # 如果有，需要生成return语句
        return_stmt = None
        for instr in common_block.instructions:
            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                # 找到RETURN_VALUE指令，生成return语句
                # 检查栈上是否有值
                if instr.opname == 'RETURN_CONST':
                    return_stmt = {
                        'type': 'Return',
                        'value': {
                            'type': 'Constant',
                            'value': instr.argval,
                            'lineno': instr.starts_line
                        },
                        'lineno': instr.starts_line
                    }
                else:
                    # RETURN_VALUE，需要检查前面的指令
                    # 对于条件表达式，通常是LOAD_FAST result
                    load_instr = None
                    for i in common_block.instructions:
                        if i.opname in ('LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                            load_instr = i
                            break
                    if load_instr:
                        return_stmt = {
                            'type': 'Return',
                            'value': {
                                'type': 'Name',
                                'id': load_instr.argval,
                                'ctx': 'Load',
                                'lineno': load_instr.starts_line
                            },
                            'lineno': instr.starts_line
                        }
                    else:
                        return_stmt = {
                            'type': 'Return',
                            'value': None,
                            'lineno': instr.starts_line
                        }
                # 标记RETURN_VALUE指令为已处理
                self._has_return_generated = True
                break
        
        # 构建 IfExp 节点（三元运算符）
        if_exp_value = {
            'type': 'IfExp',
            'test': condition,
            'body': then_value,
            'orelse': else_value,
            'lineno': self._get_block_line(entry_block)
        }
        
        # [关键修复] 如果是lambda函数中的条件表达式，直接返回IfExp
        if target_var == '__lambda_result__':
            return if_exp_value
        
        if_exp_node = {
            'type': 'Assign',
            'targets': [{'type': 'Name', 'id': target_var, 'ctx': 'Store'}],
            'value': if_exp_value,
            'lineno': self._get_block_line(entry_block)
        }
        
        # [关键修复] 如果有return语句，返回列表
        if return_stmt:
            return [if_exp_node, return_stmt]
        else:
            return if_exp_node
    
    def _find_common_successor(self, block1: BasicBlock, block2: BasicBlock) -> Optional[BasicBlock]:
        """找到两个块的共同后继块"""
        successors1 = set(block1.successors)
        successors2 = set(block2.successors)
        
        common = successors1 & successors2
        
        if common:
            return common.pop()
        
        # [关键修复] 对于嵌套条件表达式，需要递归查找后继的后继
        # 例如：外层条件表达式的 then_block 是内层条件表达式的 entry_block
        # 它的后继是内层 then 和 else，而这两个块都汇入同一个 merge 点
        # 外层 else_block 也汇入同一个 merge 点
        # 所以需要递归查找 block1 的所有后继，看是否与 block2 的后继有交集
        
        def get_all_successors(block, visited=None):
            """获取块的所有后继（递归）"""
            if visited is None:
                visited = set()
            if block in visited:
                return set()
            visited.add(block)
            
            result = set(block.successors)
            for succ in block.successors:
                result.update(get_all_successors(succ, visited))
            return result
        
        # 获取 block1 的所有后继
        all_successors1 = get_all_successors(block1)
        
        # 检查 block2 的后继是否在 all_successors1 中
        for succ2 in successors2:
            if succ2 in all_successors1:
                return succ2
        
        return None
    
    def _instr_to_ast(self, instr) -> Optional[Dict]:
        """将单条指令转换为 AST 节点"""
        if instr.opname == 'LOAD_CONST':
            return {
                'type': 'Constant',
                'value': instr.argval,
                'lineno': instr.starts_line
            }
        elif instr.opname == 'LOAD_FAST' or instr.opname == 'LOAD_NAME' or instr.opname == 'LOAD_GLOBAL':
            return {
                'type': 'Name',
                'id': instr.argval,
                'ctx': 'Load',
                'lineno': instr.starts_line
            }
        
        return None
    
    def _extract_block_content(self, block: BasicBlock) -> List[Dict[str, Any]]:
        """提取块中的内容（语句列表）"""
        content = []
        
        # 使用 _generate_block_content_v2 提取块内容
        block_ast = self._generate_block_content_v2(block)
        if block_ast:
            if isinstance(block_ast, list):
                content = block_ast
            else:
                content = [block_ast]
        
        return content
    
    def _get_compound_body(self, then_body: List[Dict], else_body: List[Dict]) -> List[Dict]:
        """获取复合条件的body"""
        if len(else_body) == 1 and else_body[0].get('type') == 'If':
            # 递归查找最后一个if的body
            current = else_body[0]
            while current and current.get('type') == 'If':
                current_body = current.get('body', [])
                current_orelse = current.get('orelse', [])
                
                if len(current_orelse) == 1 and current_orelse[0].get('type') == 'If':
                    next_if = current_orelse[0]
                    next_body = next_if.get('body', [])
                    if not next_body:
                        return current_body
                    current = next_if
                else:
                    return current_body
        return then_body
    
    def _get_compound_else_body(self, then_body: List[Dict], else_body: List[Dict]) -> List[Dict]:
        """获取复合条件的else body"""
        if len(else_body) == 1 and else_body[0].get('type') == 'If':
            # 递归查找最后一个if的orelse
            current = else_body[0]
            while current and current.get('type') == 'If':
                current_orelse = current.get('orelse', [])
                
                if len(current_orelse) == 1 and current_orelse[0].get('type') == 'If':
                    next_if = current_orelse[0]
                    next_body = next_if.get('body', [])
                    if not next_body:
                        return current_orelse
                    current = next_if
                else:
                    return current_orelse
        return []
    
    def _generate_loop_ast(self, loop: LoopStructure) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """生成循环结构的AST"""
        # [关键修复] 对于while循环，先处理初始化代码，然后再标记header为已生成
        # 这是因为header块可能包含初始化代码（如counter = 0）
        if loop.loop_type != ControlStructureType.FOR_LOOP:
            # 先处理while循环，它会处理初始化代码
            result = self._generate_while_loop_v2(loop)
            # 标记结构为已处理
            self.processed_structure_ids.add(id(loop))
            return result
        
        # [关键修复] 对于for循环，entry_block包含GET_ITER指令和迭代器表达式
        # 不应该在这里标记entry_block为已生成，而是让_generate_for_loop_v2来处理
        # 这样可以确保迭代器表达式被正确处理，而不是被生成为独立表达式
        if loop.entry_block != loop.header_block:
            # entry_block和header_block不同，说明有独立的GET_ITER块
            # 不标记entry_block为已生成，让_generate_for_loop_v2处理
            pass
        else:
            # entry_block和header_block相同，标记entry_block为已生成
            self.generated_blocks.add(loop.entry_block)
        
        # [关键修复] 标记结构为已处理
        self.processed_structure_ids.add(id(loop))
        
        if loop.loop_type == ControlStructureType.FOR_LOOP:
            return self._generate_for_loop_v2(loop)
        else:
            return self._generate_while_loop_v2(loop)
    
    def _generate_for_loop_v2(self, loop: LoopStructure) -> Dict[str, Any]:
        """生成for循环的AST（改进版）"""
        # [关键修复] 增加循环深度，用于break语句检测
        self._loop_depth += 1
        
        try:
            # [关键修复] 处理entry_block中的非迭代器代码
            # 当entry_block和header_block不同时，entry_block可能包含额外的赋值语句
            # 如：result = [] 在 for row in matrix 之前
            pre_loop_statements = []
            if (loop.entry_block != loop.header_block and 
                loop.entry_block not in self.generated_blocks):
                # 生成entry_block中的非迭代器代码
                pre_loop_statements = self._generate_block_content_skip_iterator(loop.entry_block)
                if pre_loop_statements:
                    if not isinstance(pre_loop_statements, list):
                        pre_loop_statements = [pre_loop_statements]
                else:
                    pre_loop_statements = []
                self.generated_blocks.add(loop.entry_block)
            
            # 尝试提取迭代器和循环变量
            iterator = self._extract_iterator_v2(loop.header_block)
            target = self._extract_loop_target(loop.header_block, loop.body_blocks)

            body = []
            print(f"[DEBUG] _generate_for_loop_v2: processing {len(loop.body_blocks)} body blocks")
            for block in loop.body_blocks:
                print(f"[DEBUG] Processing loop body block {getattr(block, 'start_offset', 'N/A')}, in generated_blocks: {block in self.generated_blocks}, is_header: {block == loop.header_block}")
                # [关键修复] 检查块是否属于try-except结构
                # 如果是，强制生成循环体，即使块已经被标记为已生成
                # [关键修复] 包括loop.parent是TryExceptStructure的情况
                is_in_nested_try = False
                for struct in self.structures:
                    if isinstance(struct, TryExceptStructure):
                        if block in struct.try_body:
                            is_in_nested_try = True
                            break
                
                # [关键修复] 如果块在嵌套try中，强制生成；否则检查是否已生成
                should_process = (is_in_nested_try or block not in self.generated_blocks) and block != loop.header_block
                if should_process:
                    # [关键修复] 首先检查块是否是嵌套for循环的前驱块
                    # 这比检查是否是某个结构的入口块更重要，因为嵌套循环的前驱块
                    # 可能同时是SEQUENCE结构的入口块
                    nested_for_struct = None
                    is_nested_for_predecessor = False
                    for struct in self.structures:
                        if (hasattr(struct, 'header_block') and 
                            struct.header_block in block.successors and
                            struct.struct_type == ControlStructureType.FOR_LOOP and
                            struct.entry_block != loop.header_block):  # 不是当前循环
                            if any(instr.opname == 'GET_ITER' for instr in block.instructions):
                                is_nested_for_predecessor = True
                                nested_for_struct = struct
                                break
                    
                    # [关键修复] 如果是嵌套for循环的前驱块，处理嵌套循环
                    if is_nested_for_predecessor and nested_for_struct:
                        # [关键修复] 标记块为已生成
                        self.generated_blocks.add(block)
                        
                        # [关键修复] 如果当前块也是嵌套循环的entry_block
                        if nested_for_struct.entry_block == block:
                            # [关键修复] 先生成当前块中非迭代器相关的代码（如循环变量存储）
                            block_ast = self._generate_block_content_skip_iterator(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    body.extend(block_ast)
                                else:
                                    body.append(block_ast)
                            
                            # 然后处理嵌套for循环结构
                            if id(nested_for_struct) not in self.processed_structure_ids:
                                nested_ast = self._generate_structure(nested_for_struct)
                                if nested_ast:
                                    if isinstance(nested_ast, list):
                                        body.extend(nested_ast)
                                    else:
                                        body.append(nested_ast)
                        else:
                            # 先处理前驱块的内容（跳过迭代器表达式）
                            block_ast = self._generate_block_content_skip_iterator(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    body.extend(block_ast)
                                else:
                                    body.append(block_ast)
                            
                            # [关键修复] 然后处理嵌套for循环结构
                            if id(nested_for_struct) not in self.processed_structure_ids:
                                nested_ast = self._generate_structure(nested_for_struct)
                                if nested_ast:
                                    if isinstance(nested_ast, list):
                                        body.extend(nested_ast)
                                    else:
                                        body.append(nested_ast)
                        continue  # [关键修复] 处理完嵌套循环后，继续下一个块
                    
                    # [关键修复] 检查块是否是某个结构的入口块
                    nested_struct = self._find_structure_by_entry_block(block)
                    if hasattr(block, 'start_offset') and block.start_offset == 74:
                        print(f"[DEBUG] Block 74: nested_struct={nested_struct}, processed={id(nested_struct) in self.processed_structure_ids if nested_struct else 'N/A'}")
                    if nested_struct and id(nested_struct) not in self.processed_structure_ids:
                        # [关键修复] 防止循环递归：如果嵌套结构是循环且与当前循环相同，跳过
                        if isinstance(nested_struct, LoopStructure) and nested_struct is loop:
                            continue
                        # [关键修复] 防止循环递归：如果嵌套结构的header_block与当前循环相同，跳过
                        if isinstance(nested_struct, LoopStructure) and nested_struct.header_block == loop.header_block:
                            continue
                        # 处理嵌套结构
                        nested_ast = self._generate_structure(nested_struct)
                        if nested_ast:
                            if isinstance(nested_ast, list):
                                body.extend(nested_ast)
                            else:
                                body.append(nested_ast)
                        # [关键修复] 如果嵌套结构返回None（如SEQUENCE结构被跳过），
                        # 仍然需要处理块本身的内容
                        if not nested_ast:
                            # 处理块内容
                            self.generated_blocks.add(block)
                            block_ast = self._generate_block_content_v2(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    body.extend(block_ast)
                                else:
                                    body.append(block_ast)
                    elif nested_struct and id(nested_struct) in self.processed_structure_ids:
                        # [关键修复] 嵌套结构已经被处理，尝试从缓存中获取AST
                        if isinstance(nested_struct, IfStructure):
                            cached_ast = self._if_ast_cache.get(id(nested_struct))
                            if cached_ast:
                                body.append(cached_ast)
                        # 标记块为已生成
                        if hasattr(block, 'start_offset') and block.start_offset == 88:
                            import traceback
                            print(f"[DEBUG] Block 88 added to generated_blocks at line 6556")
                            traceback.print_stack(limit=5)
                        self.generated_blocks.add(block)
                    else:
                        # [关键修复] 检查块是否是while循环的条件检查块
                        # 特征：
                        # 1. 包含POP_JUMP_FORWARD_IF_FALSE指令
                        # 2. fall-through后继可以到达包含POP_JUMP_BACKWARD_IF_TRUE的块
                        # 3. 不是IfStructure的entry_block（避免将if条件块误判为while条件块）
                        is_while_condition = False
                        
                        # [关键修复] 首先检查块是否是IfStructure的entry_block
                        is_if_entry = False
                        for struct in self.structures:
                            if isinstance(struct, IfStructure) and struct.entry_block == block:
                                is_if_entry = True
                                break
                        
                        if not is_if_entry:
                            for instr in block.instructions:
                                if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                                    # 找到fall-through后继
                                    jump_target_offset = instr.argval
                                    fall_through_succ = None
                                    for succ in block.successors:
                                        if succ.start_offset != jump_target_offset:
                                            fall_through_succ = succ
                                            break
                                    
                                    # 检查从fall-through后继是否可以到达包含POP_JUMP_BACKWARD_IF_TRUE的块
                                    if fall_through_succ:
                                        visited = set()
                                        stack = [fall_through_succ]
                                        while stack:
                                            current = stack.pop()
                                            if current in visited:
                                                continue
                                            visited.add(current)
                                            
                                            # 检查当前块是否包含POP_JUMP_BACKWARD_IF_TRUE
                                            for current_instr in current.instructions:
                                                if 'POP_JUMP_BACKWARD_IF_TRUE' in current_instr.opname:
                                                    is_while_condition = True
                                                    break
                                            if is_while_condition:
                                                break
                                            
                                            # 添加后继到栈
                                            for succ in current.successors:
                                                if succ not in visited:
                                                    stack.append(succ)
                                    
                                if is_while_condition:
                                    break
                        
                        if is_while_condition:
                            # [关键修复] 生成while循环
                            while_ast = self._generate_while_from_condition_block(block)
                            if while_ast:
                                if isinstance(while_ast, list):
                                    body.extend(while_ast)
                                else:
                                    body.append(while_ast)
                            continue
                        
                        # [关键修复] 检查块是否属于某个if结构的then_body或else_body
                        containing_if = self._find_if_structure_containing_block(block)
                        if containing_if:
                            # [关键修复] 如果if结构已经被处理，从缓存中获取AST
                            if id(containing_if) in self.processed_structure_ids:
                                cached_ast = self._if_ast_cache.get(id(containing_if))
                                if cached_ast and cached_ast not in body:
                                    body.append(cached_ast)
                                    self.generated_blocks.add(block)
                                    continue
                            # [关键修复] 如果if结构未被处理，生成它
                            if id(containing_if) not in self.processed_structure_ids:
                                if_ast = self._generate_if_ast(containing_if, is_top_level=False)
                                if if_ast:
                                    if isinstance(if_ast, list):
                                        body.extend(if_ast)
                                    else:
                                        body.append(if_ast)
                                    self.generated_blocks.add(block)
                                    continue
                            # 块属于某个if结构，跳过它
                            continue
                        
                        # 处理普通块
                        if hasattr(block, 'start_offset') and block.start_offset == 88:
                            import traceback
                            print(f"[DEBUG] Block 88 added to generated_blocks at line 6559")
                            traceback.print_stack(limit=5)
                        self.generated_blocks.add(block)
                        block_ast = self._generate_block_content_v2(block)
                        if block_ast:
                            if isinstance(block_ast, list):
                                body.extend(block_ast)
                            else:
                                body.append(block_ast)

            # [关键修复] 处理for-else的else块
            orelse = []
            if hasattr(loop, 'else_body') and loop.else_body:
                for block in loop.else_body:
                    if block not in self.generated_blocks:
                        # [关键修复] 检查块是否是if结构的入口块
                        # 如果是，应该递归处理if结构，而不是只生成块内容
                        nested_if_struct = None
                        for struct in self.structures:
                            if isinstance(struct, IfStructure) and struct.entry_block == block:
                                nested_if_struct = struct
                                break
                        
                        if nested_if_struct and id(nested_if_struct) not in self.processed_structure_ids:
                            # 递归处理嵌套的if结构
                            self.generated_blocks.add(block)
                            nested_if_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True, _entry_block_processed=True)
                            if nested_if_ast:
                                if isinstance(nested_if_ast, list):
                                    for node in nested_if_ast:
                                        if node.get('type') == 'If':
                                            node['_is_nested_if'] = True
                                    orelse.extend(nested_if_ast)
                                else:
                                    if nested_if_ast.get('type') == 'If':
                                        nested_if_ast['_is_nested_if'] = True
                                    orelse.append(nested_if_ast)
                        else:
                            # [关键修复] 对于else_body中的块，只处理块本身的内容
                            # 不递归处理结构，避免处理后继块（如return语句）
                            self.generated_blocks.add(block)
                            block_ast = self._generate_block_content_v2(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    orelse.extend(block_ast)
                                else:
                                    orelse.append(block_ast)

            for_ast = {
                'type': 'For',
                'target': target,
                'iter': iterator,
                'body': body,
                'orelse': orelse,  # [关键修复] 添加else块
                'lineno': self._get_block_line(loop.header_block)
            }
            
            # [关键修复] 缓存for循环的AST
            self._for_loop_ast_cache[id(loop)] = for_ast
            
            # [关键修复] 如果有pre_loop_statements，返回列表包含pre_loop_statements和for循环
            if pre_loop_statements:
                result = pre_loop_statements + [for_ast]
            else:
                result = for_ast
            
            return result
        finally:
            # [关键修复] 减少循环深度
            self._loop_depth -= 1
    
    def _find_structure_by_entry_block(self, block: BasicBlock) -> Optional[ControlStructure]:
        """
        查找以指定块为入口块的结构
        
        Args:
            block: 基本块
            
        Returns:
            如果找到返回结构，否则返回None
        """
        for struct in self.structures:
            if struct.entry_block == block:
                return struct
        return None
    
    def _find_if_structure_containing_block(self, block: BasicBlock) -> Optional[IfStructure]:
        """
        查找包含指定块在其then_body或else_body中的if结构
        
        Args:
            block: 基本块
            
        Returns:
            如果找到返回IfStructure，否则返回None
        """
        for struct in self.structures:
            if isinstance(struct, IfStructure):
                # 检查块是否在then_body中
                if hasattr(struct, 'then_body') and block in struct.then_body:
                    return struct
                # 检查块是否在else_body中
                if hasattr(struct, 'else_body') and block in struct.else_body:
                    return struct
        return None
    
    def _find_if_ast_by_entry_block(self, entry_block: BasicBlock) -> Optional[Dict[str, Any]]:
        """
        从已生成的AST中找到以指定块为入口的if结构的AST
        
        Args:
            entry_block: if结构的入口块
            
        Returns:
            如果找到返回if结构的AST，否则返回None
        """
        # 从缓存中查找
        # 首先找到对应的if结构
        if_struct = self._find_structure_by_entry_block(entry_block)
        if if_struct and isinstance(if_struct, IfStructure):
            # 从缓存中获取AST
            return self._if_ast_cache.get(id(if_struct))
        return None
    
    def _generate_init_block_content(self, init_block: BasicBlock) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """生成初始化块内容的AST（只包含初始化指令，不包含条件检查）
        
        对于作为初始化块的块（如while循环前的i = 0），
        它可能同时包含初始化代码和条件检查代码。
        这个方法只提取初始化相关的指令（完整的赋值语句）。
        """
        # [关键修复] 找到所有完整的赋值语句
        # 赋值语句通常是：LOAD_*, STORE_* 这种模式
        # 我们需要找到所有STORE指令，然后回溯到对应的LOAD指令
        init_instrs = []
        i = 0
        while i < len(init_block.instructions):
            instr = init_block.instructions[i]
            
            # 跳过RESUME和CACHE指令
            if instr.opname in ('RESUME', 'CACHE'):
                i += 1
                continue
            
            # 如果遇到条件跳转指令，停止处理
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'
            ):
                break
            
            # 检查是否是赋值语句的开始（LOAD_*）
            if instr.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                # 向前查找对应的STORE指令
                # 收集从当前位置到STORE指令之间的所有指令
                stmt_instrs = [instr]
                j = i + 1
                found_store = False
                is_walrus = False  # [海象运算符] 标记是否是海象运算符模式
                while j < len(init_block.instructions):
                    next_instr = init_block.instructions[j]
                    
                    # 如果遇到条件跳转，停止
                    if next_instr.opname in (
                        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'
                    ):
                        break
                    
                    # 收集指令
                    stmt_instrs.append(next_instr)
                    
                    # [海象运算符] 检查是否是COPY指令
                    if next_instr.opname == 'COPY':
                        is_walrus = True
                    
                    # 如果遇到STORE指令，这是一个完整的赋值语句
                    if next_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                        # [海象运算符] 检查前面是否有COPY指令
                        # 如果是海象运算符模式，不作为初始化代码
                        if is_walrus or (j > 0 and init_block.instructions[j - 1].opname == 'COPY'):
                            is_walrus = True
                        found_store = True
                        break
                    
                    # 如果遇到另一个LOAD指令，说明之前的不是赋值语句
                    if next_instr.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                        # 重新开始
                        stmt_instrs = [next_instr]
                        is_walrus = False
                    
                    j += 1
                
                if found_store and not is_walrus:
                    # 这是一个完整的赋值语句，添加到初始化指令列表
                    init_instrs.extend(stmt_instrs)
                    i = j + 1
                else:
                    # 不是完整的赋值语句或者是海象运算符，跳过
                    i += 1
            else:
                i += 1
        
        if init_instrs:
            return self._generate_instructions_content(init_instrs)
        return None
    
    def _generate_while_loop_v2(self, loop: LoopStructure) -> Dict[str, Any]:
        """生成while循环的AST（改进版）"""
        # [关键修复] 增加循环深度，用于break语句检测
        self._loop_depth += 1
        
        try:
            # [关键修复] 使用condition_block（真正的循环条件）而不是header_block
            condition_block = loop.condition_block if loop.condition_block else loop.header_block
            condition = self._extract_condition_v2(condition_block)

            # [关键修复] 处理初始化块（如count = 0）
            # 对于Python 3.11+的while循环，初始化代码在loop.init_blocks中
            init_statements = []
            if hasattr(loop, 'init_blocks') and loop.init_blocks:
                for init_block in loop.init_blocks:
                    if init_block not in self.generated_blocks:
                        # [关键修复] 对于初始化块，只生成初始化相关的指令
                        # 而不是整个块的内容（块可能也包含条件检查代码）
                        self.generated_blocks.add(init_block)
                        init_ast = self._generate_init_block_content(init_block)
                        if init_ast:
                            if isinstance(init_ast, list):
                                init_statements.extend(init_ast)
                            else:
                                init_statements.append(init_ast)
            
            # [关键修复] 处理entry_block（循环入口块）本身包含初始化代码的情况
            # 对于Python 3.11+的while循环，entry_block可能同时包含初始化代码和条件代码
            # 例如：i = 0; while i < 3: ...
            entry_block = loop.entry_block
            if entry_block and hasattr(entry_block, 'has_init_code') and entry_block.has_init_code:
                # 从entry_block中提取初始化代码
                if entry_block not in self.generated_blocks:
                    # 生成初始化语句（只包含初始化指令，不包含条件指令）
                    init_ast = self._generate_init_from_header(entry_block)
                    if init_ast:
                        if isinstance(init_ast, list):
                            init_statements.extend(init_ast)
                        else:
                            init_statements.append(init_ast)
                    self.generated_blocks.add(entry_block)
            
            # [兼容性保留] 也检查header_block（为了向后兼容）
            header = loop.header_block
            if header and header != entry_block and hasattr(header, 'has_init_code') and header.has_init_code:
                if header not in self.generated_blocks:
                    init_ast = self._generate_init_from_header(header)
                    if init_ast:
                        if isinstance(init_ast, list):
                            init_statements.extend(init_ast)
                        else:
                            init_statements.append(init_ast)
                    self.generated_blocks.add(header)

            body = []

            # [关键修复] 处理header block也是body block的情况（Python 3.11+的while循环结构）
            if loop.header_block:
                if loop.header_block in loop.body_blocks:
                    # [关键修复] 检查header block是否是if结构的入口块
                    header_if_struct = None
                    for struct in self.structures:
                        if isinstance(struct, IfStructure) and struct.entry_block == loop.header_block:
                            header_if_struct = struct
                            break
                    
                    if header_if_struct and id(header_if_struct) not in self.processed_structure_ids:
                        # Header block是if结构的入口块，递归处理该if结构
                        self.generated_blocks.add(loop.header_block)
                        if_ast = self._generate_if_ast(header_if_struct, is_top_level=False)
                        if if_ast:
                            if isinstance(if_ast, list):
                                body.extend(if_ast)
                            else:
                                body.append(if_ast)
                    else:
                        # [关键修复] 检查是否有if结构在循环体内
                        # 如果是，说明if结构应该在循环体内处理，不应该在这里生成header_block的内容
                        if_struct_in_loop = None
                        for struct in self.structures:
                            if isinstance(struct, IfStructure) and id(struct) not in self.processed_structure_ids:
                                # 检查if结构的entry_block是否在循环的body_blocks中
                                if struct.entry_block in loop.body_blocks:
                                    if_struct_in_loop = struct
                                    break
                        
                        if if_struct_in_loop:
                            # [关键修复] 先处理if结构，再处理header block的内容
                            # 先生成if结构（不包含else_body中的header_block内容）
                            if_ast = self._generate_if_from_block(if_struct_in_loop.entry_block, loop, skip_else_branch=True)
                            if if_ast:
                                if isinstance(if_ast, list):
                                    body.extend(if_ast)
                                else:
                                    body.append(if_ast)
                            # [关键修复] 将if结构标记为已处理，防止在模块级别重复生成
                            self.processed_structure_ids.add(id(if_struct_in_loop))
                            # 然后处理header block的内容
                            body_ast = self._generate_while_body_from_header(loop.header_block)
                            if body_ast:
                                if isinstance(body_ast, list):
                                    body.extend(body_ast)
                                else:
                                    body.append(body_ast)
                            self.generated_blocks.add(loop.header_block)
                        else:
                            # Header block不是if结构的入口块，提取循环体内容
                            body_ast = self._generate_while_body_from_header(loop.header_block)
                            if body_ast:
                                if isinstance(body_ast, list):
                                    body.extend(body_ast)
                                else:
                                    body.append(body_ast)
                            self.generated_blocks.add(loop.header_block)
                elif loop.header_block not in self.generated_blocks:
                    # [关键修复] 检查header block是否是if结构的入口块
                    header_if_struct = None
                    for struct in self.structures:
                        if isinstance(struct, IfStructure) and struct.entry_block == loop.header_block:
                            header_if_struct = struct
                            break
                    
                    if header_if_struct and id(header_if_struct) not in self.processed_structure_ids:
                        # Header block是if结构的入口块，递归处理该if结构
                        self.generated_blocks.add(loop.header_block)
                        if_ast = self._generate_if_ast(header_if_struct, is_top_level=False)
                        if if_ast:
                            if isinstance(if_ast, list):
                                body.extend(if_ast)
                            else:
                                body.append(if_ast)
                    else:
                        # Header block不是if结构的入口块，提取循环体语句
                        body_ast = self._generate_while_body_from_header(loop.header_block)
                        if body_ast:
                            if isinstance(body_ast, list):
                                body.extend(body_ast)
                            else:
                                body.append(body_ast)
                        self.generated_blocks.add(loop.header_block)

            # 处理其他body blocks（排除已处理的header block）
            for block in loop.body_blocks:
                if block not in self.generated_blocks:
                    # [关键修复] 首先检查块是否是循环体内的if条件块
                    # 这需要在检查结构映射之前进行，因为entry_block可能被映射到LoopStructure
                    # 特征：
                    # 1. 有两个后继
                    # 2. 包含POP_JUMP_IF_*指令
                    # 3. 不包含向后跳转指令（避免将循环条件识别为if条件）
                    has_pop_jump = any('POP_JUMP' in instr.opname for instr in block.instructions)
                    has_backward_jump = any('BACKWARD' in instr.opname for instr in block.instructions)
                    is_if_condition = (len(block.successors) == 2 and 
                                      has_pop_jump and 
                                      not has_backward_jump)
                    
                    if is_if_condition:
                        # [关键修复] 手动生成if结构
                        if_ast = self._generate_if_from_block(block, loop)
                        if if_ast:
                            if isinstance(if_ast, list):
                                body.extend(if_ast)
                            else:
                                body.append(if_ast)
                        continue
                    
                    # [关键修复] 检查块是否是某个结构的入口块
                    nested_struct = self._find_structure_by_entry_block(block)
                    if nested_struct and id(nested_struct) not in self.processed_structure_ids:
                        # [关键修复] 防止循环递归：如果嵌套结构是循环且与当前循环相同，跳过
                        if isinstance(nested_struct, LoopStructure) and nested_struct is loop:
                            continue
                        # [关键修复] 防止循环递归：如果嵌套结构的header_block与当前循环相同，跳过
                        if isinstance(nested_struct, LoopStructure) and nested_struct.header_block == loop.header_block:
                            continue
                        
                        # 处理嵌套结构
                        nested_ast = self._generate_structure(nested_struct)
                        if nested_ast:
                            if isinstance(nested_ast, list):
                                body.extend(nested_ast)
                            else:
                                body.append(nested_ast)
                    elif nested_struct and id(nested_struct) in self.processed_structure_ids:
                        # [关键修复] 该结构已经被处理，跳过该块
                        # 这通常发生在elif链中，父结构的else_body包含子结构的块
                        continue
                    else:
                        # [关键修复] 检查块是否属于某个if结构的then_body或else_body
                        # 如果是，跳过该块，让if结构来处理它
                        belongs_to_if = False
                        for struct in self.structures:
                            if isinstance(struct, IfStructure) and id(struct) not in self.processed_structure_ids:
                                if block in struct.then_body or block in struct.else_body:
                                    belongs_to_if = True
                                    break
                        
                        if belongs_to_if:
                            continue
                        
                        # 处理普通块
                        self.generated_blocks.add(block)
                        block_ast = self._generate_block_content_v2(block)
                        if block_ast:
                            if isinstance(block_ast, list):
                                body.extend(block_ast)
                            else:
                                body.append(block_ast)

            # [关键修复] 处理while-else的else块
            orelse = []
            if hasattr(loop, 'else_body') and loop.else_body:
                for block in loop.else_body:
                    if block not in self.generated_blocks:
                        # [关键修复] 检查块是否是if结构的入口块
                        # 如果是，应该递归处理if结构，而不是只生成块内容
                        nested_if_struct = None
                        for struct in self.structures:
                            if isinstance(struct, IfStructure) and struct.entry_block == block:
                                nested_if_struct = struct
                                break
                        
                        if nested_if_struct and id(nested_if_struct) not in self.processed_structure_ids:
                            # 递归处理嵌套的if结构
                            self.generated_blocks.add(block)
                            nested_if_ast = self._generate_if_ast(nested_if_struct, is_top_level=False, _skip_processed_check=True, _entry_block_processed=True)
                            if nested_if_ast:
                                if isinstance(nested_if_ast, list):
                                    for node in nested_if_ast:
                                        if node.get('type') == 'If':
                                            node['_is_nested_if'] = True
                                    orelse.extend(nested_if_ast)
                                else:
                                    if nested_if_ast.get('type') == 'If':
                                        nested_if_ast['_is_nested_if'] = True
                                    orelse.append(nested_if_ast)
                        else:
                            self.generated_blocks.add(block)
                            block_ast = self._generate_block_content_v2(block)
                            if block_ast:
                                if isinstance(block_ast, list):
                                    orelse.extend(block_ast)
                                else:
                                    orelse.append(block_ast)

            # [关键修复] 如果有初始化语句，返回列表包含初始化语句和while循环
            while_loop = {
                'type': 'While',
                'test': condition,
                'body': body,
                'orelse': orelse,  # [关键修复] 添加else块
                'lineno': self._get_block_line(loop.header_block)
            }
            
            if init_statements:
                # 返回初始化语句和while循环的列表
                return init_statements + [while_loop]
            else:
                return while_loop
        finally:
            # [关键修复] 减少循环深度
            self._loop_depth -= 1

    def _generate_init_from_header(self, header_block: BasicBlock) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """从header块中提取初始化语句
        
        对于Python 3.11+的while循环，header块可能同时包含初始化代码和条件代码。
        这个方法只提取初始化代码（STORE_FAST等），不提取条件代码。
        """
        if not hasattr(header_block, 'init_instr_indices') or not header_block.init_instr_indices:
            return None
        
        # 获取初始化指令的索引
        init_indices = header_block.init_instr_indices
        
        # 提取初始化指令
        init_instrs = []
        for i in init_indices:
            if i < len(header_block.instructions):
                init_instrs.append(header_block.instructions[i])
        
        if not init_instrs:
            return None
        
        # 找到初始化代码的起始位置
        # 初始化代码通常是：LOAD_CONST, STORE_FAST 这种模式
        # 我们需要找到LOAD_CONST指令的位置
        init_start = init_indices[0]
        for i in range(init_indices[0], -1, -1):
            instr = header_block.instructions[i]
            # [关键修复] 初始化代码通常以LOAD_*开始
            # 我们需要一直向前扫描直到找到LOAD指令
            if instr.opname in ('LOAD_CONST', 'LOAD_FAST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                init_start = i
                # 找到了LOAD指令，停止扫描
                break
            elif instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                # 这是存储指令，继续向前扫描
                continue
            else:
                # 其他指令，停止扫描
                break
        
        # 提取完整的初始化指令序列
        # 从init_start到init_indices[-1] + 1
        full_init_instrs = header_block.instructions[init_start:init_indices[-1] + 1]
        
        # 使用 _generate_instructions_content 处理指令
        return self._generate_instructions_content(full_init_instrs)
    
    def _generate_if_from_block(self, block: BasicBlock, loop: LoopStructure, skip_else_branch: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """从基本块生成if结构的AST（用于循环体内的if条件）
        
        Args:
            block: if条件的entry_block
            loop: 包含该if条件的循环结构
            skip_else_branch: 如果为True，跳过else_branch的处理（用于else_branch是循环header_block的情况）
        """
        # [关键修复] 首先处理entry_block中的非条件指令（如赋值语句）
        pre_condition_stmts = []
        jump_index = None
        for i, instr in enumerate(block.instructions):
            if 'POP_JUMP' in instr.opname:
                jump_index = i
                break
        
        if jump_index is not None and jump_index > 0:
            # 有非条件指令在条件检查之前
            pre_condition_instrs = block.instructions[:jump_index]
            # 找到完整的赋值语句
            stmt_start = 0
            for i, instr in enumerate(pre_condition_instrs):
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                    # 这是一个完整的赋值语句
                    stmt_instrs = pre_condition_instrs[stmt_start:i+1]
                    stmt_ast = self._generate_instructions_content(stmt_instrs)
                    if stmt_ast:
                        if isinstance(stmt_ast, list):
                            pre_condition_stmts.extend(stmt_ast)
                        else:
                            pre_condition_stmts.append(stmt_ast)
                    stmt_start = i + 1
        
        # [关键修复] 提取条件表达式
        condition = self._extract_condition_v2(block)
        if not condition:
            # 如果没有条件表达式，返回非条件指令
            if pre_condition_stmts:
                self.generated_blocks.add(block)
                return pre_condition_stmts
            return None
        
        # [关键修复] 确定then分支和else分支
        succs = list(block.successors)
        if len(succs) != 2:
            return None
        
        # [关键修复] 找到跳转指令
        jump_instr = None
        for instr in block.instructions:
            if 'POP_JUMP' in instr.opname:
                jump_instr = instr
                break
        
        if not jump_instr or jump_instr.argval is None:
            return None
        
        # [关键修复] 确定then分支和else分支
        # POP_JUMP_IF_FALSE: 如果条件为假，跳转到else分支
        # POP_JUMP_IF_TRUE: 如果条件为真，跳转到then分支
        if 'FALSE' in jump_instr.opname:
            # 跳转到else分支
            else_branch = None
            then_branch = None
            for succ in succs:
                if succ.start_offset == jump_instr.argval:
                    else_branch = succ
                else:
                    then_branch = succ
        else:
            # 跳转到then分支
            else_branch = None
            then_branch = None
            for succ in succs:
                if succ.start_offset == jump_instr.argval:
                    then_branch = succ
                else:
                    else_branch = succ
        
        if not then_branch or not else_branch:
            return None
        
        # [关键修复] 生成then_body
        then_body = []
        if then_branch not in self.generated_blocks:
            # [关键修复] 首先检查then_branch是否是某个控制结构的entry_block
            # 例如try-except结构，需要递归处理
            then_struct = self._find_structure_by_entry_block(then_branch)
            if then_struct and id(then_struct) not in self.processed_structure_ids:
                # 递归处理嵌套结构
                nested_ast = self._generate_structure(then_struct)
                if nested_ast:
                    if isinstance(nested_ast, list):
                        then_body.extend(nested_ast)
                    else:
                        then_body.append(nested_ast)
            else:
                # 检查是否是break语句
                # break语句的特征：
                # 1. 在循环体内的if分支中，包含LOAD_CONST None, RETURN_VALUE（模块级别）
                # 2. 在循环体内的if分支中，包含POP_TOP, JUMP_FORWARD（函数内部，Python 3.11+）
                is_break = False
                has_load_const_none = False
                has_return = False
                has_pop_top = False
                has_jump_forward = False
                
                for instr in then_branch.instructions:
                    if instr.opname == 'LOAD_CONST' and instr.argval is None:
                        has_load_const_none = True
                    elif instr.opname == 'RETURN_VALUE':
                        has_return = True
                    elif instr.opname == 'POP_TOP':
                        has_pop_top = True
                    elif instr.opname == 'JUMP_FORWARD':
                        has_jump_forward = True
                
                # 如果在循环体内且返回None，则是break（模块级别）
                if has_load_const_none and has_return and self._loop_depth > 0:
                    is_break = True
                # 如果在循环体内且有POP_TOP + JUMP_FORWARD，则是break（函数内部，Python 3.11+）
                elif has_pop_top and has_jump_forward and self._loop_depth > 0:
                    is_break = True
                
                if is_break:
                    then_body.append({'type': 'Break'})
                    self.generated_blocks.add(then_branch)
                else:
                    # [关键修复] 检查then_branch是否包含内层while循环
                    # 特征：包含POP_JUMP_BACKWARD_IF_TRUE指令，跳转目标是then_branch自己
                    has_inner_while = False
                    for instr in then_branch.instructions:
                        if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                            if instr.argval is not None and instr.argval == then_branch.start_offset:
                                has_inner_while = True
                                break
                    
                    if has_inner_while:
                        # [关键修复] 生成内层while循环
                        while_ast = self._generate_inner_while_from_block(then_branch)
                        if while_ast:
                            if isinstance(while_ast, list):
                                then_body.extend(while_ast)
                            else:
                                then_body.append(while_ast)
                    else:
                        # 生成普通块内容
                        self.generated_blocks.add(then_branch)
                        block_ast = self._generate_block_content_v2(then_branch)
                        if block_ast:
                            if isinstance(block_ast, list):
                                then_body.extend(block_ast)
                            else:
                                then_body.append(block_ast)
        
        # [关键修复] 生成else_body
        else_body = []
        if not skip_else_branch and else_branch not in self.generated_blocks:
            # [关键修复] 检查else_branch是否是循环尾部
            # 特征：包含向后跳转到if条件块的指令
            is_loop_tail = False
            for instr in else_branch.instructions:
                if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                    if instr.argval is not None and instr.argval == block.start_offset:
                        # 向后跳转到if条件块，这是循环尾部
                        is_loop_tail = True
                        break
            
            if is_loop_tail:
                # 这是循环尾部，不应该生成else分支
                # 循环尾部的内容（如j += 1）应该在if结构之后生成
                pass
            elif else_branch == loop.header_block:
                # [关键修复] 如果else_branch是循环的header_block，提取header_block的内容（除了条件检查）
                body_ast = self._generate_while_body_from_header(else_branch)
                if body_ast:
                    if isinstance(body_ast, list):
                        else_body.extend(body_ast)
                    else:
                        else_body.append(body_ast)
                # 不标记header_block为已生成，让循环处理逻辑来处理条件检查
            else:
                # [关键修复] 首先检查else_branch是否是某个控制结构的entry_block
                else_struct = self._find_structure_by_entry_block(else_branch)
                if else_struct and id(else_struct) not in self.processed_structure_ids:
                    # 递归处理嵌套结构
                    nested_ast = self._generate_structure(else_struct)
                    if nested_ast:
                        if isinstance(nested_ast, list):
                            else_body.extend(nested_ast)
                        else:
                            else_body.append(nested_ast)
                else:
                    # [关键修复] 检查是否是break语句（else分支中的break）
                    # break语句的特征：在循环体内的else分支中，包含POP_TOP, JUMP_FORWARD（函数内部，Python 3.11+）
                    is_break = False
                    has_pop_top = False
                    has_jump_forward = False
                    
                    for instr in else_branch.instructions:
                        if instr.opname == 'POP_TOP':
                            has_pop_top = True
                        elif instr.opname == 'JUMP_FORWARD':
                            has_jump_forward = True
                    
                    # 如果在循环体内且有POP_TOP + JUMP_FORWARD，则是break（函数内部，Python 3.11+）
                    if has_pop_top and has_jump_forward and self._loop_depth > 0:
                        is_break = True
                    
                    if is_break:
                        else_body.append({'type': 'Break'})
                        self.generated_blocks.add(else_branch)
                    else:
                        # 普通块，直接生成内容
                        self.generated_blocks.add(else_branch)
                        block_ast = self._generate_block_content_v2(else_branch)
                        if block_ast:
                            if isinstance(block_ast, list):
                                else_body.extend(block_ast)
                            else:
                                else_body.append(block_ast)
        
        # [关键修复] 构建if节点
        if_node = {
            'type': 'If',
            'test': condition,
            'body': then_body if then_body else [{'type': 'Pass'}],
            'orelse': else_body if else_body else []
        }
        
        # 标记块为已生成
        self.generated_blocks.add(block)
        
        # [关键修复] 如果有非条件指令，将它们添加到if节点之前
        if pre_condition_stmts:
            result = pre_condition_stmts + [if_node]
            return result
        
        return if_node
    
    def _generate_inner_while_from_block(self, block: BasicBlock) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        从基本块生成内层while循环的AST
        
        用于处理嵌套在if语句中的while循环，如：
        if j > 1:
            while j < 5:
                ...
        
        这种结构的字节码特点是：
        - 块包含POP_JUMP_BACKWARD_IF_TRUE指令
        - 跳转目标是块自己（循环回跳）
        - 条件表达式在循环体之后
        """
        # 找到POP_JUMP_BACKWARD_IF_TRUE指令
        jump_index = None
        jump_instr = None
        for i, instr in enumerate(block.instructions):
            if 'POP_JUMP_BACKWARD_IF_TRUE' in instr.opname:
                jump_index = i
                jump_instr = instr
                break
        
        if jump_index is None or jump_instr is None:
            # 没有找到向后跳转指令，使用普通块内容生成
            self.generated_blocks.add(block)
            return self._generate_block_content_v2(block)
        
        # 提取条件表达式（向后跳转之前的指令）
        condition_instrs = []
        condition_start = jump_index
        
        # 从后向前扫描，找到条件表达式的起始位置
        for i in range(jump_index - 1, -1, -1):
            instr = block.instructions[i]
            # 条件表达式通常包含COMPARE_OP
            if instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'NOT'):
                condition_start = i
            elif instr.opname in ('LOAD_FAST', 'LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                condition_start = i
            elif instr.opname in ('BINARY_OP', 'UNARY_NOT'):
                condition_start = i
            elif instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                # 遇到存储指令，停止扫描（这是循环体的结束）
                break
            else:
                # 遇到其他指令，停止扫描
                break
        
        # 提取条件表达式
        condition_instrs = block.instructions[condition_start:jump_index]
        
        # 生成条件表达式
        condition = None
        if condition_instrs:
            condition = self._generate_instructions_content(condition_instrs)
            if isinstance(condition, list) and len(condition) > 0:
                condition = condition[0]
            # 如果条件表达式是赋值语句，提取其值
            if isinstance(condition, dict) and condition.get('type') == 'Assign':
                condition = condition.get('value')
            # [关键修复] 如果条件表达式是Expr语句，提取其值
            if isinstance(condition, dict) and condition.get('type') == 'Expr':
                condition = condition.get('value')
        
        if not condition:
            condition = {'type': 'Constant', 'value': True, 'lineno': None}
        
        # 提取循环体（条件表达式之前的指令）
        body_instrs = block.instructions[:condition_start]
        
        # 生成循环体
        body = []
        if body_instrs:
            body_ast = self._generate_instructions_content(body_instrs)
            if body_ast:
                if isinstance(body_ast, list):
                    body.extend(body_ast)
                else:
                    body.append(body_ast)
        
        # 标记块为已生成
        self.generated_blocks.add(block)
        
        # 构建while循环节点
        while_node = {
            'type': 'While',
            'test': condition,
            'body': body if body else [{'type': 'Pass'}],
            'orelse': [],
            'lineno': self._get_block_line(block)
        }
        
        return while_node
    
    def _generate_while_from_condition_block(self, block: BasicBlock) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        从while循环的条件块生成while循环的AST
        
        用于处理嵌套在if语句中的while循环，如：
        if j > 1:
            while j < 5:
                ...
        
        这种结构的字节码特点是：
        - 条件块包含POP_JUMP_FORWARD_IF_FALSE指令
        - fall-through后继包含POP_JUMP_BACKWARD_IF_TRUE指令，跳转目标是fall-through后继自己
        """
        # 找到POP_JUMP_FORWARD_IF_FALSE指令
        jump_instr = None
        jump_index = None
        for i, instr in enumerate(block.instructions):
            if 'POP_JUMP_FORWARD_IF_FALSE' in instr.opname:
                jump_instr = instr
                jump_index = i
                break
        
        if jump_instr is None or jump_index is None:
            # 没有找到跳转指令，使用普通块内容生成
            self.generated_blocks.add(block)
            return self._generate_block_content_v2(block)
        
        # 提取条件表达式（跳转指令之前的指令）
        condition_start = 0
        for i in range(jump_index - 1, -1, -1):
            instr = block.instructions[i]
            # 条件表达式通常包含COMPARE_OP
            if instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'NOT'):
                condition_start = i
            elif instr.opname in ('LOAD_FAST', 'LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                condition_start = i
            elif instr.opname in ('BINARY_OP', 'UNARY_NOT'):
                condition_start = i
            elif instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                # 遇到存储指令，停止扫描（这是循环体的结束）
                break
            else:
                # 遇到其他指令，停止扫描
                break
        
        # 提取条件表达式
        condition_instrs = block.instructions[condition_start:jump_index]
        
        # 生成条件表达式
        condition = None
        if condition_instrs:
            condition = self._generate_instructions_content(condition_instrs)
            if isinstance(condition, list) and len(condition) > 0:
                condition = condition[0]
            # 如果条件表达式是赋值语句，提取其值
            if isinstance(condition, dict) and condition.get('type') == 'Assign':
                condition = condition.get('value')
            # [关键修复] 如果条件表达式是Expr语句，提取其值
            if isinstance(condition, dict) and condition.get('type') == 'Expr':
                condition = condition.get('value')
        
        if not condition:
            condition = {'type': 'Constant', 'value': True, 'lineno': None}
        
        # 找到fall-through后继（while循环的body块）
        body_block = None
        for succ in block.successors:
            if succ.start_offset != jump_instr.argval:
                body_block = succ
                break
        
        # 生成循环体
        body = []
        if body_block:
            # [关键修复] 检查body_block是否是if结构的entry_block
            # 如果是，需要生成if结构而不是普通块内容
            if_struct = None
            for struct in self.structures:
                if isinstance(struct, IfStructure) and struct.entry_block == body_block:
                    if_struct = struct
                    break
            
            if if_struct and id(if_struct) not in self.processed_structure_ids:
                # body_block是if条件的entry_block，生成if结构
                self.generated_blocks.add(block)  # 标记条件块为已生成
                # [关键修复] 使用_skip_processed_check=True，因为body_block可能已经被标记为已生成
                if_ast = self._generate_if_ast(if_struct, is_top_level=False, _skip_processed_check=True)
                if if_ast:
                    if isinstance(if_ast, list):
                        body.extend(if_ast)
                    else:
                        body.append(if_ast)
                
                # [关键修复] 处理if结构之后的块（如while循环的增量部分）
                # 这些块原本被识别为if的else_body，但因为包含向后跳转到if条件块的指令，
                # 所以else_body被设置为空。这些块应该在if之后执行。
                if if_struct.else_body:
                    for else_block in if_struct.else_body:
                        if else_block not in self.generated_blocks:
                            else_ast = self._generate_block_content_v2(else_block)
                            if else_ast:
                                if isinstance(else_ast, list):
                                    body.extend(else_ast)
                                else:
                                    body.append(else_ast)
                else:
                    # [关键修复] else_body为空，但可能有块包含向后跳转到while条件块或if条件块的指令
                    # 这些块是while循环的增量部分，需要被包含在while循环的body中
                    # 找到这些块：从body_block开始，沿着后继链查找，直到遇到向后跳转到while条件块或if条件块的块
                    visited = set()
                    stack = list(body_block.successors)
                    while stack:
                        current = stack.pop()
                        if current in visited:
                            continue
                        visited.add(current)
                        
                        # 检查是否是if条件块，如果是则跳过
                        if current == body_block:
                            continue
                        
                        # 检查是否包含向后跳转到while条件块或if条件块的指令
                        has_backward_to_loop = False
                        for instr in current.instructions:
                            if 'BACKWARD' in instr.opname:
                                # 检查是否跳转到while条件块
                                if instr.argval is not None and instr.argval == block.start_offset:
                                    has_backward_to_loop = True
                                    print(f"[DEBUG] Found backward jump to while condition block {block.start_offset} from block {current.start_offset}")
                                    break
                                # 检查是否跳转到if条件块（body_block）
                                if instr.argval is not None and instr.argval == body_block.start_offset:
                                    has_backward_to_loop = True
                                    print(f"[DEBUG] Found backward jump to if condition block {body_block.start_offset} from block {current.start_offset}")
                                    break
                        
                        if has_backward_to_loop:
                            # 这是while循环的增量部分，生成它
                            if current not in self.generated_blocks:
                                increment_ast = self._generate_block_content_v2(current)
                                if increment_ast:
                                    if isinstance(increment_ast, list):
                                        body.extend(increment_ast)
                                    else:
                                        body.append(increment_ast)
                            break
                        
                        # 继续查找后继
                        for succ in current.successors:
                            if succ not in visited:
                                stack.append(succ)
            else:
                # 生成body_block的内容
                body_ast = self._generate_inner_while_from_block(body_block)
                if body_ast:
                    if isinstance(body_ast, list):
                        body.extend(body_ast)
                    else:
                        body.append(body_ast)
        
        # 标记块为已生成
        self.generated_blocks.add(block)
        
        # 构建while循环节点
        while_node = {
            'type': 'While',
            'test': condition,
            'body': body if body else [{'type': 'Pass'}],
            'orelse': [],
            'lineno': self._get_block_line(block)
        }
        
        return while_node
    
    def _generate_while_body_from_header(self, header_block: BasicBlock) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """从while循环的header block中提取循环体语句"""
        # 找到条件跳转指令的位置
        jump_index = None
        for i, instr in enumerate(header_block.instructions):
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'
            ):
                jump_index = i
                break

        if jump_index is None:
            # 没有找到条件跳转，使用正常的块内容生成
            return self._generate_block_content_v2(header_block)

        # [关键修复] Python 3.11+的while循环结构：
        # - 循环体在条件跳转之前（backward跳转）
        # - 需要提取条件跳转之前的指令作为循环体
        
        # 检查是否是backward跳转（循环回跳）
        jump_instr = header_block.instructions[jump_index]
        is_backward_jump = 'BACKWARD' in jump_instr.opname
        
        if is_backward_jump:
            # Backward跳转：循环体在条件跳转之前
            # [关键修复] 需要排除条件表达式（如 count < 3）
            # 条件表达式通常是 COMPARE_OP 或类似的比较指令
            # 找到条件表达式的起始位置（从后往前找）
            all_body_instrs = header_block.instructions[:jump_index]
            
            # [关键修复] 找到条件表达式的边界
            # 条件表达式通常是：LOAD_FAST, LOAD_CONST, COMPARE_OP 这种模式
            # 从后往前扫描，找到条件表达式的起始
            condition_start = len(all_body_instrs)
            # [海象运算符] 标记是否处于海象运算符模式
            in_walrus_mode = False
            for i in range(len(all_body_instrs) - 1, -1, -1):
                instr = all_body_instrs[i]
                # 如果指令是条件比较相关的，继续向前扫描
                if instr.opname in ('COMPARE_OP', 'IS_OP', 'CONTAINS_OP', 'NOT'):
                    condition_start = i
                elif instr.opname in ('LOAD_FAST', 'LOAD_CONST', 'LOAD_NAME', 'LOAD_GLOBAL'):
                    # 这些指令可能是条件表达式的一部分
                    if condition_start <= len(all_body_instrs):
                        condition_start = i
                    else:
                        break
                elif instr.opname in ('BINARY_OP', 'UNARY_NOT'):
                    condition_start = i
                elif instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_ATTR', 'STORE_SUBSCR'):
                    # [海象运算符] 检查前面是否有COPY指令
                    # 如果是COPY + STORE模式，这是海象运算符的一部分，继续向前扫描
                    if i > 0 and all_body_instrs[i - 1].opname == 'COPY':
                        in_walrus_mode = True
                        condition_start = i - 1  # 包含COPY指令
                        continue  # 继续向前扫描
                    # [关键修复] 遇到存储指令，这是循环体的结束
                    # STORE指令标志着赋值语句的结束，不应该作为条件的一部分
                    # 停止扫描，保留当前condition_start
                    break
                elif instr.opname == 'COPY':
                    # [海象运算符] COPY指令，标记为海象运算符模式
                    in_walrus_mode = True
                    condition_start = i
                elif instr.opname in ('CALL', 'CALL_FUNCTION', 'PRECALL'):
                    # [海象运算符] 函数调用指令，继续向前扫描
                    condition_start = i
                elif instr.opname == 'PUSH_NULL':
                    # [海象运算符] PUSH_NULL是函数调用的开始
                    condition_start = i
                    break
                else:
                    # 遇到非条件相关指令，停止扫描
                    break
            
            # 只保留条件表达式之前的指令作为循环体
            body_instrs = all_body_instrs[:condition_start]
        else:
            # Forward跳转：循环体在条件跳转之后（传统结构）
            body_instrs = header_block.instructions[jump_index + 1:]

        if not body_instrs:
            return None

        # [关键修复] 使用 _generate_instructions_content 处理指令
        # 这样可以复用完整的指令处理逻辑（包括CALL, LOAD_METHOD等）
        # [关键修复] 设置current_block以便continue检测
        self.current_block = header_block
        result = self._generate_instructions_content(body_instrs)
        self.current_block = None
        return result
    
    def _generate_try_except_ast(self, try_struct: TryExceptStructure) -> Dict[str, Any]:
        """生成try-except结构的AST"""
        # [关键修复] 标记结构为已处理
        self.processed_structure_ids.add(id(try_struct))
        
        try_body = []
        
        # [关键修复] 首先处理嵌套的子try-except结构
        # 对于嵌套的try-except，子结构应该作为父结构try_body的一部分
        if try_struct.children:
            for child_struct in try_struct.children:
                if isinstance(child_struct, TryExceptStructure):
                    if id(child_struct) not in self.processed_structure_ids:
                        child_ast = self._generate_try_except_ast(child_struct)
                        if child_ast:
                            try_body.append(child_ast)
        
        # [关键修复] 确定哪些块也是else块的一部分
        else_blocks_set = set(try_struct.else_body) if try_struct.else_body else set()
        
        # [关键修复] 收集try_body中的嵌套with结构
        nested_withs = []
        for struct in self.structures:
            if isinstance(struct, WithStructure):
                # 检查with结构是否在try_body中
                if struct.entry_block in try_struct.try_body:
                    nested_withs.append(struct)
        
        # [关键修复] 收集try_body中的嵌套if结构
        nested_ifs = []
        for struct in self.structures:
            if isinstance(struct, IfStructure):
                # 检查if结构是否在try_body中
                # [关键修复] 检查entry_block是否在try_body中
                if struct.entry_block in try_struct.try_body:
                    nested_ifs.append(struct)
                else:
                    # [关键修复] 检查then_body或else_body中的任何块是否在try_body中
                    # 这可以捕获嵌套在循环体内的if结构
                    for block in try_struct.try_body:
                        if block in struct.then_body or block in struct.else_body:
                            nested_ifs.append(struct)
                            break
        
        # [关键修复] 收集try_body中的嵌套循环结构
        nested_loops = []
        for struct in self.structures:
            if isinstance(struct, LoopStructure):
                # 检查循环结构是否在try_body中
                if struct.entry_block in try_struct.try_body:
                    nested_loops.append(struct)
                    print(f"[DEBUG _generate_try_except_ast] Added loop (entry in try_body): entry={struct.entry_block.start_offset}")
                else:
                    # [关键修复] 检查body_blocks中的任何块是否在try_body中
                    # 这可以捕获嵌套在循环体内的循环结构
                    for block in try_struct.try_body:
                        if block in struct.body_blocks:
                            nested_loops.append(struct)
                            print(f"[DEBUG _generate_try_except_ast] Added loop (body in try_body): entry={struct.entry_block.start_offset}, body_block={block.start_offset}")
                            break
        
        print(f"[DEBUG _generate_try_except_ast] nested_loops count: {len(nested_loops)}")
        
        for block in try_struct.try_body:
            # [关键修复] 检查这个块是否是嵌套with结构的entry_block
            nested_with = None
            for w in nested_withs:
                if w.entry_block == block:
                    nested_with = w
                    break
            
            # [关键修复] 检查这个块是否是嵌套if结构的entry_block
            nested_if = None
            for if_struct in nested_ifs:
                if if_struct.entry_block == block:
                    nested_if = if_struct
                    break
            
            # [关键修复] 检查这个块是否是嵌套循环结构的entry_block
            nested_loop = None
            for loop_struct in nested_loops:
                if loop_struct.entry_block == block:
                    nested_loop = loop_struct
                    break
            
            # [关键修复] 对于try_body块，如果它已经在generated_blocks中，且不是嵌套结构的entry_block，跳过它
            # 这避免了代码重复生成（如循环体中的代码在try块中再次生成）
            is_already_generated = block in self.generated_blocks
            is_nested_struct_entry = nested_with or nested_if or nested_loop
            if is_already_generated and not is_nested_struct_entry:
                continue
            
            # [关键修复] 如果块是嵌套结构的entry_block，不要在这里标记为已处理
            # 让嵌套结构的处理函数来标记它
            is_nested_struct_entry = (nested_with and id(nested_with) not in self.processed_structure_ids) or \
                                     (nested_if and id(nested_if) not in self.processed_structure_ids) or \
                                     (nested_loop and id(nested_loop) not in self.processed_structure_ids)
            
            # [关键修复] 检查块是否属于任何嵌套循环的body_blocks
            # 如果是，不要在这里标记为已处理，让循环生成函数来处理
            is_in_nested_loop_body = False
            for loop_struct in nested_loops:
                is_processed = id(loop_struct) in self.processed_structure_ids
                in_body = block in loop_struct.body_blocks
                print(f"[DEBUG] Checking loop entry={loop_struct.entry_block.start_offset}, block={block.start_offset}, processed={is_processed}, in_body={in_body}")
                if not is_processed and in_body:
                    is_in_nested_loop_body = True
                    # [关键修复] 如果没有找到entry_block，使用这个循环
                    if not nested_loop:
                        nested_loop = loop_struct
                    print(f"[DEBUG] Block {block.start_offset} is in nested loop body")
                    break
            
            # [关键修复] 如果块也是else块的一部分，不要在这里标记为已处理
            # 如果块是嵌套结构的entry_block，也不要在这里标记为已处理
            # 如果块属于嵌套循环的body_blocks，也不要在这里标记为已处理
            if block not in else_blocks_set and not is_nested_struct_entry and not is_in_nested_loop_body:
                self.generated_blocks.add(block)
            
            if nested_with and id(nested_with) not in self.processed_structure_ids:
                # [关键修复] 这个块包含嵌套的with结构，使用_generate_with_ast处理
                with_ast = self._generate_with_ast(nested_with)
                if with_ast:
                    try_body.append(with_ast)
            elif nested_if and id(nested_if) not in self.processed_structure_ids:
                # [关键修复] 这个块包含嵌套的if结构，使用_generate_if_ast处理
                # [关键修复] 使用_skip_processed_check=True来确保即使块已经被标记为已生成，也能正确处理
                if_ast = self._generate_if_ast(nested_if, is_top_level=False, _skip_processed_check=True)
                if if_ast:
                    if isinstance(if_ast, list):
                        try_body.extend(if_ast)
                    else:
                        try_body.append(if_ast)
            elif nested_loop:
                if id(nested_loop) not in self.processed_structure_ids:
                    # [关键修复] 这个块包含嵌套的循环结构，使用_generate_loop_ast处理
                    print(f"[DEBUG _generate_try_except_ast] Processing nested loop at block {block.start_offset}")
                    loop_ast = self._generate_loop_ast(nested_loop)
                    if loop_ast:
                        try_body.append(loop_ast)
                else:
                    # [关键修复] 嵌套循环已经被处理，从缓存中获取它的AST
                    print(f"[DEBUG _generate_try_except_ast] Nested loop at block {block.start_offset} already processed, adding to try_body")
                    cached_ast = self._for_loop_ast_cache.get(id(nested_loop))
                    if cached_ast:
                        try_body.append(cached_ast)
            else:
                    # [关键修复] 对于所有try_body块，都应该根据try_start_offset和try_end_offset过滤指令
                    # 这确保不会生成try范围之外的指令（如NOP填充）
                    try_start = try_struct.try_start_offset
                    try_end = try_struct.try_end_offset
                    
                    # [关键修复] 检查这个块是否是内层try的entry_block
                    # 如果是，跳过这个块，因为内层try的代码已经作为子结构生成了
                    is_nested_try_entry = False
                    for child in try_struct.children:
                        if isinstance(child, TryExceptStructure):
                            if block == child.entry_block:
                                is_nested_try_entry = True
                                break
                    
                    # [关键修复] 如果块是内层try的entry_block，跳过它
                    if is_nested_try_entry:
                        continue
                    
                    # [关键修复] 检查这个块是否包含内层try的代码（但不是entry_block）
                    # 如果包含，不过滤指令，因为内层try的代码也是外层try的一部分
                    has_nested_try_code = False
                    for child in try_struct.children:
                        if isinstance(child, TryExceptStructure):
                            if block in child.try_body and block != child.entry_block:
                                has_nested_try_code = True
                                break
                    
                    # [关键修复] 如果块也是else块的一部分，需要更严格的过滤
                    if block in else_blocks_set:
                        # 只生成try范围内的指令
                        filtered_instrs = [instr for instr in block.instructions if try_start <= instr.offset < try_end]
                    elif has_nested_try_code:
                        # [关键修复] 如果块包含内层try的代码，不过滤指令
                        # 因为这些指令是内层try的一部分，也是外层try的一部分
                        filtered_instrs = block.instructions
                    else:
                        # [关键修复] 对于普通try块，过滤出try范围内的指令
                        # 但不要过滤掉return语句和JUMP_FORWARD，因为它们可能在try_end之后
                        # [关键修复] 排除NOP指令，因为NOP是try块的开始标记，不应该生成if True:
                        filtered_instrs = []
                        for instr in block.instructions:
                            if instr.opname == 'NOP':
                                # 跳过NOP指令，这是try块的开始标记
                                continue
                            elif try_start <= instr.offset < try_end:
                                # 指令在try范围内
                                filtered_instrs.append(instr)
                            elif instr.opname in ('RETURN_VALUE', 'RETURN_CONST', 'JUMP_FORWARD'):
                                # return和JUMP_FORWARD语句即使在try范围外也保留
                                # JUMP_FORWARD是try块结束后的跳转，必须保留
                                filtered_instrs.append(instr)
                        
                        # [关键修复] 如果没有过滤出任何指令，但块有指令，使用原始指令（排除NOP）
                        # 这可能发生在try_start和try_end覆盖整个块的情况下
                        if not filtered_instrs and block.instructions:
                            filtered_instrs = [instr for instr in block.instructions if instr.opname != 'NOP']
                    
                    if filtered_instrs:
                        # 创建临时块来处理过滤后的指令
                        temp_block = BasicBlock(block.start_offset)
                        temp_block.end_offset = block.end_offset
                        temp_block.instructions = filtered_instrs
                        temp_block.successors = block.successors
                        temp_block.predecessors = block.predecessors
                        block_ast = self._generate_block_content_v2(temp_block)
                    else:
                        block_ast = None
                    if block_ast:
                        if isinstance(block_ast, list):
                            # 过滤掉空的None语句和多余的return语句
                            filtered_try_body = []
                            for stmt in block_ast:
                                # 跳过空的None语句
                                if stmt.get('type') == 'Expr' and stmt.get('value') is None:
                                    continue
                                elif stmt.get('type') == 'Expr' and isinstance(stmt.get('value'), dict) and stmt.get('value').get('type') == 'Constant' and stmt.get('value').get('value') is None:
                                    continue
                                # 跳过空的return语句
                                elif stmt.get('type') == 'Return' and stmt.get('value') is None:
                                    continue
                                # 跳过其他可能的空语句
                                elif stmt.get('type') == 'Pass':
                                    continue
                                filtered_try_body.append(stmt)
                            if filtered_try_body:
                                try_body.extend(filtered_try_body)
                        else:
                            # 检查单个语句是否是None或空return或pass
                            if not (
                                (block_ast.get('type') == 'Expr' and block_ast.get('value') is None) or
                                (block_ast.get('type') == 'Expr' and isinstance(block_ast.get('value'), dict) and block_ast.get('value').get('type') == 'Constant' and block_ast.get('value').get('value') is None) or
                                (block_ast.get('type') == 'Return' and block_ast.get('value') is None) or
                                (block_ast.get('type') == 'Pass')
                            ):
                                try_body.append(block_ast)
        
        handlers = []
        # [关键修复] 新的except_handlers格式是(exc_type, exc_name, handler_blocks)
        for handler_info in try_struct.except_handlers:
            if len(handler_info) == 3:
                exc_type, exc_name, handler_blocks = handler_info
            else:
                # 兼容旧格式
                exc_type, handler_blocks = handler_info
                exc_name = None
            
            handler_body = []
            for block in handler_blocks:
                if block not in self.generated_blocks:
                    self.generated_blocks.add(block)
                    # [关键修复] 过滤掉异常处理相关的指令
                    block_ast = self._generate_except_handler_block(block, exc_name)
                    if block_ast:
                        if isinstance(block_ast, list):
                            handler_body.extend(block_ast)
                        else:
                            handler_body.append(block_ast)
                    # [关键修复] 如果_generate_except_handler_block返回None，说明这是异常处理框架块
                    # 不应该再尝试直接生成内容，即使它不包含框架指令
                    # 清理代码块（如e = None; del e）会被_generate_except_handler_block过滤掉
                    # 这些块不应该生成任何代码
            
            # 构建except handler字典 - 注意：'type'是异常类型，不是节点类型
            exc_type_expr = None
            if exc_type:
                exc_type_expr = {
                    'type': 'Name',
                    'id': exc_type,
                    'lineno': None
                }
            
            # 正确的handler格式
            handler = {
                'type': 'ExceptHandler',
                'exc_type': exc_type_expr,  # 异常类型表达式
                'name': exc_name,  # as 名称（except-as）
                'body': handler_body
            }
            handlers.append(handler)
        
        # [关键修复] 生成else子句的AST
        orelse = []
        if try_struct.has_else and try_struct.else_body:
            # [关键修复] 保存当前的_return_generated状态
            saved_has_return_generated = self._has_return_generated
            
            for block in try_struct.else_body:
                if block not in self.generated_blocks:
                    self.generated_blocks.add(block)
                    
                    # [关键修复] 如果else块和try块是同一个块，需要过滤指令
                    # 只保留try范围之外的指令
                    try_end = try_struct.try_end_offset
                    
                    filtered_instrs = []
                    for instr in block.instructions:
                        if instr.offset >= try_end:
                            # 跳过JUMP_FORWARD指令（它是else块的结束标记）
                            if instr.opname != 'JUMP_FORWARD':
                                filtered_instrs.append(instr)
                    
                    if filtered_instrs:
                        # [关键修复] 重置_return_generated，允许else块中的return语句生成
                        self._has_return_generated = False
                        
                        # 创建临时块来处理过滤后的指令
                        temp_block = BasicBlock(block.start_offset)
                        temp_block.end_offset = block.end_offset
                        temp_block.instructions = filtered_instrs
                        temp_block.successors = block.successors
                        temp_block.predecessors = block.predecessors
                        
                        block_ast = self._generate_block_content_v2(temp_block)
                        if block_ast:
                            if isinstance(block_ast, list):
                                orelse.extend(block_ast)
                            else:
                                orelse.append(block_ast)
                    # [关键修复] 如果filtered_instrs为空，说明这个块只有try范围内的指令
                    # 这种情况下不应该处理整个块
            
            # [关键修复] 恢复_return_generated状态
            self._has_return_generated = saved_has_return_generated
        
        # [关键修复] 生成finally子句的AST
        finalbody = []
        if try_struct.has_finally:
            # [关键修复] 对于try-finally，finally代码在多个地方：
            # 1. try_body块中try范围之后的指令（正常路径）
            # 2. except_handlers块中（异常路径）
            # 3. finally_body块中（清理代码）
            
            # [关键修复] 只从正常路径提取finally代码，避免重复
            # 异常路径的finally代码是重复的，不应该被提取
            else_blocks_set = set(try_struct.else_body) if try_struct.else_body else set()
            for block in try_struct.try_body:
                # [关键修复] 跳过也是else_body的块
                if block in else_blocks_set:
                    continue
                    
                try_end = try_struct.try_end_offset
                
                # 提取try范围之后的指令（finally代码）
                finally_instrs = []
                for instr in block.instructions:
                    if instr.offset >= try_end:
                        # 跳过JUMP_FORWARD和RETURN_VALUE
                        if instr.opname not in ('JUMP_FORWARD', 'RETURN_VALUE', 'RESUME', 'CACHE'):
                            finally_instrs.append(instr)
                
                if finally_instrs:
                    # 创建临时块来处理finally指令
                    temp_block = BasicBlock(block.start_offset)
                    temp_block.end_offset = block.end_offset
                    temp_block.instructions = finally_instrs
                    temp_block.successors = block.successors
                    temp_block.predecessors = block.predecessors
                    
                    # [关键修复] 使用_generate_except_handler_block来过滤异常清理代码
                    # 这会过滤掉e = None, DELETE_FAST等清理代码
                    block_ast = self._generate_except_handler_block(temp_block, exc_name=None)
                    if block_ast:
                        if isinstance(block_ast, list):
                            finalbody.extend(block_ast)
                        else:
                            finalbody.append(block_ast)
                    break  # 只处理第一个有finally代码的块
            
            # [关键修复] 不再从except_handlers中提取finally代码
            # 因为异常路径的finally代码与正常路径是重复的
            # 只从finally_body中提取（如果前面的步骤没有找到）
            if not finalbody and try_struct.finally_body:
                # [关键修复] 处理finally_body中的所有块
                # 正常路径的块生成AST，异常路径的块标记为已处理并跳过
                for block in try_struct.finally_body:
                    if block not in self.generated_blocks:
                        # [关键修复] 检查块是否包含异常处理指令
                        # 如果包含，这是异常路径的finally代码，应该跳过
                        has_exception_instr = False
                        for instr in block.instructions:
                            if instr.opname in ('PUSH_EXC_INFO', 'RERAISE', 'COPY', 'POP_EXCEPT'):
                                has_exception_instr = True
                                break
                        
                        # [关键修复] 跳过包含异常处理指令的块，并标记为已处理
                        # 这些块是异常路径的finally代码，不应该生成源代码
                        if has_exception_instr:
                            self.generated_blocks.add(block)
                            continue
                        
                        # [关键修复] 标记块为已处理
                        self.generated_blocks.add(block)
                        
                        # [关键修复] 使用_generate_except_handler_block来过滤异常清理代码
                        # 这会过滤掉LOAD_CONST None等清理代码
                        block_ast = self._generate_except_handler_block(block, exc_name=None)
                        if block_ast:
                            # [关键修复] 检查是否已经存在相同的AST，避免重复
                            is_duplicate = False
                            if isinstance(block_ast, list):
                                for item in block_ast:
                                    if item in finalbody:
                                        is_duplicate = True
                                        break
                                if not is_duplicate:
                                    finalbody.extend(block_ast)
                            else:
                                if block_ast not in finalbody:
                                    finalbody.append(block_ast)
                        # [关键修复] 继续处理其他块，不要break，以确保所有异常路径的块都被标记为已处理
        
        # [关键修复] 对于纯try-finally（没有except，只有finally），清空handlers
        if try_struct.has_finally and not try_struct.except_handlers:
            handlers = []
        
        # [关键修复] 如果没有except handlers，不能有else子句
        # Python语法规定：else子句必须跟在except子句之后
        if not handlers:
            orelse = []
        
        return {
            'type': 'Try',
            'body': try_body,
            'handlers': handlers,
            'orelse': orelse,  # [关键修复] 使用生成的else子句
            'finalbody': finalbody,  # [关键修复] 使用生成的finally子句
            'lineno': try_struct.try_body[0].instructions[0].starts_line if try_struct.try_body else None
        }
    
    def _generate_with_ast(self, with_struct: WithStructure) -> Dict[str, Any]:
        """生成with结构的AST"""
        # [关键修复] 标记结构为已处理
        self.processed_structure_ids.add(id(with_struct))
        
        entry_block = with_struct.entry_block
        
        # [关键修复] 检查是否有并行的with语句（同一个entry_block中的多个with）
        parallel_withs = self._find_parallel_withs(entry_block, with_struct)
        
        # 构建with items列表
        items = []
        for w in parallel_withs:
            resource_expr = w.resource_expr
            target = w.target
            
            # 构建上下文表达式AST
            if resource_expr:
                context_expr_ast = self._parse_resource_expr(resource_expr)
            else:
                context_expr_ast = {'type': 'Name', 'id': 'context_manager'}
            
            # 构建可选变量AST
            if target:
                optional_vars_ast = {'type': 'Name', 'id': target}
            else:
                optional_vars_ast = None
            
            items.append({
                'type': 'withitem',
                'context_expr': context_expr_ast,
                'optional_vars': optional_vars_ast
            })
            
            # 标记并行的with结构为已处理
            if w != with_struct:
                self.processed_structure_ids.add(id(w))
        
        # [关键修复] 生成with体 - 只提取with体的实际代码部分
        body = []
        
        # 找到最后一个with的STORE_FAST/STORE_NAME位置
        last_store_fast_idx = -1
        for w in parallel_withs:
            target = w.target
            for i, instr in enumerate(entry_block.instructions):
                if instr.opname == 'BEFORE_WITH':
                    # 查找这个BEFORE_WITH之后的STORE_FAST/STORE_NAME
                    for j in range(i + 1, len(entry_block.instructions)):
                        if entry_block.instructions[j].opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                            if entry_block.instructions[j].argval == target:
                                last_store_fast_idx = max(last_store_fast_idx, j)
                            break
        
        # [关键修复] 提取with体的指令（在最后一个STORE_FAST之后，清理代码之前）
        if last_store_fast_idx >= 0:
            # with体代码从最后一个STORE_FAST之后开始
            body_start_idx = last_store_fast_idx + 1
            
            # 找到清理代码的开始位置（LOAD_CONST None, LOAD_CONST <exit>, PRECALL/CALL 或 RETURN 指令）
            cleanup_start_idx = len(entry_block.instructions)
            for i in range(body_start_idx, len(entry_block.instructions)):
                instr = entry_block.instructions[i]
                # 清理代码模式1：LOAD_CONST None, LOAD_CONST <exit>, PRECALL 2, CALL 2, POP_TOP
                # [关键修复] 支持多个LOAD_CONST None的情况（如 with 语句的清理代码）
                if instr.opname == 'LOAD_CONST' and instr.argval is None:
                    # 检查后面是否是PRECALL/CALL模式（允许中间有多个LOAD_CONST None）
                    # 模式：LOAD_CONST None [, LOAD_CONST None ...] PRECALL/CALL
                    found_precall_or_call = False
                    for j in range(i + 1, min(i + 10, len(entry_block.instructions))):
                        next_instr = entry_block.instructions[j]
                        if next_instr.opname in ('PRECALL', 'CALL'):
                            found_precall_or_call = True
                            break
                        elif next_instr.opname not in ('LOAD_CONST', 'CACHE'):
                            # 如果不是LOAD_CONST或CACHE，也不是PRECALL/CALL，则不是清理代码
                            break
                    if found_precall_or_call:
                        cleanup_start_idx = i
                        break
                # 清理代码模式2：RETURN_VALUE 或 RETURN_CONST（函数返回）
                # [关键修复] 如果RETURN前面没有LOAD_CONST None，这不是清理代码，而是with体的正常return
                elif instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    # 检查前面是否是LOAD_CONST None（清理代码模式）
                    is_cleanup = False
                    if i > 0:
                        for j in range(i-1, max(i-5, body_start_idx-1), -1):
                            if entry_block.instructions[j].opname == 'LOAD_CONST' and entry_block.instructions[j].argval is None:
                                is_cleanup = True
                                break
                            elif entry_block.instructions[j].opname not in ('POP_TOP', 'CACHE', 'NOP'):
                                break
                    if is_cleanup:
                        cleanup_start_idx = i
                        break
                    # [关键修复] 如果不是清理代码，继续处理，不中断
                # 清理代码模式3：PUSH_EXC_INFO（异常处理开始）
                elif instr.opname == 'PUSH_EXC_INFO':
                    cleanup_start_idx = i
                    break
                # 清理代码模式4：POP_EXCEPT（异常处理结束）
                elif instr.opname == 'POP_EXCEPT':
                    # 检查前面是否是异常处理相关指令
                    if i > 0 and entry_block.instructions[i-1].opname in ('WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'POP_JUMP_FORWARD_IF_TRUE'):
                        cleanup_start_idx = i - 1
                        break
            
            # 提取with体的指令
            body_instructions = entry_block.instructions[body_start_idx:cleanup_start_idx]
            
            # [关键修复] 不要过滤掉JUMP_FORWARD指令
            # 因为with体后面的代码（如return语句）可能通过JUMP_FORWARD连接
            # 这些指令是with语句的正常后续，不是清理代码
            
            # [关键修复] 生成with体的AST，使用空栈开始
            # with语句体的指令应该从空栈开始执行，不受之前指令的影响
            if body_instructions:
                body_ast = self._generate_instructions_content(body_instructions, shared_stack=[])
                if body_ast:
                    if isinstance(body_ast, list):
                        # 过滤掉空的None语句和多余的return语句
                        filtered_body = []
                        for stmt in body_ast:
                            # 跳过空的None语句
                            if stmt.get('type') == 'Expr' and stmt.get('value') is None:
                                continue
                            elif stmt.get('type') == 'Expr' and isinstance(stmt.get('value'), dict) and stmt.get('value').get('type') == 'Constant' and stmt.get('value').get('value') is None:
                                continue
                            # 跳过空的return语句
                            elif stmt.get('type') == 'Return' and stmt.get('value') is None:
                                continue
                            # 跳过其他可能的空语句
                            elif stmt.get('type') == 'Pass':
                                continue
                            filtered_body.append(stmt)
                        if filtered_body:
                            body.extend(filtered_body)
                    else:
                        # 检查单个语句是否是None或空return或pass
                        if not (
                            (body_ast.get('type') == 'Expr' and body_ast.get('value') is None) or
                            (body_ast.get('type') == 'Expr' and isinstance(body_ast.get('value'), dict) and body_ast.get('value').get('type') == 'Constant' and body_ast.get('value').get('value') is None) or
                            (body_ast.get('type') == 'Return' and body_ast.get('value') is None) or
                            (body_ast.get('type') == 'Pass')
                        ):
                            body.append(body_ast)
        
        # 标记entry_block为已处理
        if entry_block not in self.generated_blocks:
            self.generated_blocks.add(entry_block)
        
        # [关键修复] 标记with_body中的所有块为已处理
        for block in with_struct.with_body:
            if block not in self.generated_blocks:
                self.generated_blocks.add(block)
        
        # [关键修复] 处理with语句体内的其他块（如if语句的分支）
        # 这些块是entry_block的后继，但不是异常处理块
        for succ_block in entry_block.successors:
            # 跳过异常处理块和清理代码块
            is_exception_block = False
            # [关键修复] 检查是否是函数返回块
            is_return_block = False
            for instr in succ_block.instructions:
                if instr.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'POP_EXCEPT'):
                    is_exception_block = True
                    break
                # 清理代码块特征：LOAD_CONST None 后面跟着 PRECALL/CALL
                if instr.opname == 'LOAD_CONST' and instr.argval is None:
                    is_exception_block = True
                    break
                # [关键修复] 函数返回块不应该被包含在with体中
                if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                    is_return_block = True
                    break
            
            if is_exception_block:
                continue
            
            # [关键修复] 跳过函数返回块，这些块是with语句之后的代码
            if is_return_block:
                continue
            
            # 跳过已经处理过的块
            if succ_block in self.generated_blocks:
                continue
            
            # [关键修复] 检查这个后继块是否属于某个控制流结构
            # 如果是IfStructure，应该调用_generate_if_ast而不是简单的块内容
            is_struct_processed = False
            for struct in self.structures:
                if isinstance(struct, IfStructure) and struct.entry_block == succ_block:
                    if id(struct) not in self.processed_structure_ids:
                        self.processed_structure_ids.add(id(struct))
                        if_ast = self._generate_if_ast(struct)
                        if if_ast:
                            body.append(if_ast)
                        is_struct_processed = True
                        break
                # [关键修复] 检查是否是WithStructure的entry_block
                # 如果是，跳过，让那个with语句自己处理
                elif isinstance(struct, WithStructure) and struct.entry_block == succ_block:
                    is_struct_processed = True
                    break
            
            if is_struct_processed:
                continue
            
            # 生成后继块的AST（对于简单的块）
            self.generated_blocks.add(succ_block)
            block_ast = self._generate_block_content_v2(succ_block)
            if block_ast:
                if isinstance(block_ast, list):
                    body.extend(block_ast)
                else:
                    body.append(block_ast)
        
        # [关键修复] 检查是否有异常处理块（包含 PUSH_EXC_INFO 等指令）
        # 这些块应该被包含在with语句的body中
        for struct in self.structures:
            if isinstance(struct, IfStructure):
                # 检查是否是异常处理相关的If结构
                entry_block = struct.entry_block
                is_exception_handler = False
                for instr in entry_block.instructions:
                    if instr.opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'CHECK_EXC_MATCH'):
                        is_exception_handler = True
                        break
                
                if is_exception_handler:
                    # 检查这个异常处理块是否与当前with语句相关
                    # 检查异常处理块的前驱是否是with语句的entry_block
                    if entry_block.predecessors and with_struct.entry_block in entry_block.predecessors:
                        # 生成异常处理块的AST
                        if id(struct) not in self.processed_structure_ids:
                            self.processed_structure_ids.add(id(struct))
                            # [关键修复] 只生成 then_body 的内容，不生成 else_body
                            # then_body 包含异常处理成功的代码（如赋值给变量）
                            # else_body 包含异常处理失败后的代码（如 RERAISE），不应该添加到 with 语句体中
                            for block in struct.then_body:
                                if block not in self.generated_blocks:
                                    self.generated_blocks.add(block)
                                    block_ast = self._generate_block_content_v2(block)
                                    if block_ast:
                                        if isinstance(block_ast, list):
                                            # 过滤掉空的None语句和多余的return语句
                                            filtered_body = []
                                            for stmt in block_ast:
                                                # 跳过空的None语句
                                                if stmt.get('type') == 'Expr' and stmt.get('value') is None:
                                                    continue
                                                elif stmt.get('type') == 'Expr' and isinstance(stmt.get('value'), dict) and stmt.get('value').get('type') == 'Constant' and stmt.get('value').get('value') is None:
                                                    continue
                                                # 跳过空的return语句
                                                elif stmt.get('type') == 'Return' and stmt.get('value') is None:
                                                    continue
                                                # 跳过其他可能的空语句
                                                elif stmt.get('type') == 'Pass':
                                                    continue
                                                filtered_body.append(stmt)
                                            if filtered_body:
                                                body.extend(filtered_body)
                                        else:
                                            # 检查单个语句是否是None或空return或pass
                                            if not (
                                                (block_ast.get('type') == 'Expr' and block_ast.get('value') is None) or
                                                (block_ast.get('type') == 'Expr' and isinstance(block_ast.get('value'), dict) and block_ast.get('value').get('type') == 'Constant' and block_ast.get('value').get('value') is None) or
                                                (block_ast.get('type') == 'Return' and block_ast.get('value') is None) or
                                                (block_ast.get('type') == 'Pass')
                                            ):
                                                body.append(block_ast)
                            # [关键修复] 不处理 else_body，因为它包含的是异常处理失败后的代码
                            # 这些代码不应该被添加到 with 语句体中
        
        return {
            'type': 'With',
            'items': items,
            'body': body,
            'lineno': self._get_block_line(with_struct.entry_block)
        }
    
    def _find_parallel_withs(self, entry_block: BasicBlock, current_with: WithStructure) -> List[WithStructure]:
        """查找同一个entry_block中的所有并行with结构"""
        parallel_withs = [current_with]
        
        # 查找所有与当前with结构有相同entry_block的其他with结构
        for struct in self.structures:
            if isinstance(struct, WithStructure) and struct != current_with:
                if struct.entry_block == entry_block:
                    # 检查是否已经被处理
                    if id(struct) not in self.processed_structure_ids:
                        parallel_withs.append(struct)
        
        # 按BEFORE_WITH的位置排序
        def get_before_with_offset(w):
            for i, instr in enumerate(entry_block.instructions):
                if instr.opname == 'BEFORE_WITH':
                    # 查找对应的target
                    for j in range(i + 1, len(entry_block.instructions)):
                        if entry_block.instructions[j].opname == 'STORE_FAST':
                            if entry_block.instructions[j].argval == w.target:
                                return i
                            break
            return float('inf')
        
        parallel_withs.sort(key=get_before_with_offset)
        
        return parallel_withs
    
    def _filter_with_body_statements(self, statements: List[Dict[str, Any]], target_var: str = None) -> List[Dict[str, Any]]:
        """过滤with体中的语句，只移除with语句的资源表达式赋值"""
        filtered = []
        for stmt in statements:
            # 只跳过与with资源表达式相关的赋值语句
            if stmt.get('type') == 'Assign' and target_var:
                # 检查是否是 with 语句的资源表达式赋值（即target变量的赋值）
                targets = stmt.get('targets', [])
                if targets and any(t.get('id') == target_var for t in targets if isinstance(t, dict)):
                    continue
            
            filtered.append(stmt)
        
        return filtered
    
    def _parse_resource_expr(self, expr_str: str) -> Dict[str, Any]:
        """解析资源表达式字符串为AST
        
        支持的形式:
        - 函数调用: CustomContextManager(), open('file.txt', 'w')
        - 方法调用: obj.method()
        - 变量: context_manager
        """
        expr_str = expr_str.strip()
        
        # 检查是否是函数调用
        if '(' in expr_str and expr_str.endswith(')'):
            # 解析函数调用
            func_name = expr_str[:expr_str.index('(')].strip()
            args_str = expr_str[expr_str.index('(')+1:-1].strip()
            
            # 解析参数
            args = []
            if args_str:
                # 简单解析逗号分隔的参数
                for arg in args_str.split(','):
                    arg = arg.strip()
                    if arg:
                        args.append(self._parse_arg(arg))
            
            # 构建函数调用AST
            return {
                'type': 'Call',
                'func': self._parse_func_name(func_name),
                'args': args
            }
        
        # 简单变量名
        return {'type': 'Name', 'id': expr_str}
    
    def _parse_func_name(self, func_name: str) -> Dict[str, Any]:
        """解析函数名为AST"""
        if '.' in func_name:
            # 方法调用: obj.method
            parts = func_name.split('.')
            return {
                'type': 'Attribute',
                'value': {'type': 'Name', 'id': parts[0]},
                'attr': parts[1]
            }
        return {'type': 'Name', 'id': func_name}
    
    def _parse_arg(self, arg_str: str) -> Dict[str, Any]:
        """解析参数为AST"""
        arg_str = arg_str.strip()
        
        # 字符串字面量
        if (arg_str.startswith("'") and arg_str.endswith("'")) or \
           (arg_str.startswith('"') and arg_str.endswith('"')):
            return {'type': 'Constant', 'value': arg_str[1:-1]}
        
        # 数字
        try:
            num = int(arg_str)
            return {'type': 'Constant', 'value': num}
        except ValueError:
            try:
                num = float(arg_str)
                return {'type': 'Constant', 'value': num}
            except ValueError:
                pass
        
        # 变量名
        return {'type': 'Name', 'id': arg_str}
    
    def _extract_with_context(self, block: BasicBlock) -> Dict[str, Any]:
        """提取with语句的上下文管理器表达式"""
        # 查找BEFORE_WITH或SETUP_WITH指令之前的表达式
        for i, instr in enumerate(block.instructions):
            if instr.opname in ('BEFORE_WITH', 'SETUP_WITH'):
                # 上下文管理器表达式在指令之前
                expr_instrs = block.instructions[:i]
                if expr_instrs:
                    # 重建表达式
                    return self._reconstruct_expression_from_instrs(expr_instrs)
        
        # [临时修复] 如果无法提取上下文表达式，使用占位符
        # TODO: 修复上下文表达式提取
        return {'type': 'Name', 'id': 'context_manager'}
    
    def _reconstruct_expression_from_instrs(self, instrs: List[Instruction]) -> Dict[str, Any]:
        """从指令序列重建表达式"""
        # 使用表达式重建器
        reconstructor = ExpressionReconstructor()
        return reconstructor.reconstruct(instrs)
    
    def _generate_except_handler_block(self, block: BasicBlock, exc_name: Optional[str] = None) -> Optional[Any]:
        """
        生成except handler块的AST，过滤掉异常处理相关的指令
        
        异常处理块的结构（Python 3.11+）：
        - PUSH_EXC_INFO
        - LOAD_GLOBAL <异常类型>
        - CHECK_EXC_MATCH
        - POP_JUMP_FORWARD_IF_FALSE <不匹配时跳转>
        - POP_TOP  <- 匹配成功，弹出异常
        - STORE_FAST <name>  <- except-as的变量绑定（如果有）
        - <实际handler代码>
        - POP_EXCEPT
        - JUMP_FORWARD <跳出>
        - RERAISE  <- 不匹配时重新抛出
        
        Args:
            block: handler块
            exc_name: except-as的变量名（如 except Exception as e: 中的e）
        """
        # [关键修复] 不要在这里检查generated_blocks，因为调用者已经检查过了
        # 如果块已经被处理，调用者不会调用这个方法
        
        # 过滤掉异常处理框架指令
        filtered_instrs = []
        in_handler_code = False  # 是否已进入实际handler代码
        pop_top_seen = False  # 是否已看到POP_TOP
        
        # [关键修复] 检查块是否包含POP_TOP
        has_pop_top = any(instr.opname == 'POP_TOP' for instr in block.instructions)
        
        for i, instr in enumerate(block.instructions):
            # 标记进入实际handler代码（在POP_TOP之后）
            if instr.opname == 'POP_TOP':
                # 检查前一条是否是 POP_JUMP_FORWARD_IF_FALSE（匹配成功分支）
                if i > 0 and block.instructions[i-1].opname == 'POP_JUMP_FORWARD_IF_FALSE':
                    in_handler_code = True
                    pop_top_seen = True
                    continue  # 跳过这个POP_TOP
                # [关键修复] 如果POP_TOP前一条是CALL，这是函数调用结果的POP_TOP
                # 用于生成表达式语句，不应该跳过
                if i > 0 and block.instructions[i-1].opname in ('CALL', 'CALL_FUNCTION'):
                    in_handler_code = True
                    pop_top_seen = True
                    # 不跳过这个POP_TOP，因为它用于生成Expr语句
                    pass
                # [关键修复] 如果POP_TOP是块的第一条指令，也设置in_handler_code
                # 这种情况发生在POP_JUMP_FORWARD_IF_FALSE和POP_TOP不在同一个块中时
                if i == 0:
                    in_handler_code = True
                    pop_top_seen = True
                    continue  # 跳过这个POP_TOP
            
            # [关键修复] 跳过except-as的变量绑定
            if instr.opname == 'STORE_FAST':
                if exc_name and instr.argval == exc_name:
                    if pop_top_seen and not in_handler_code:
                        # POP_TOP之后的STORE_FAST（在包含POP_TOP的块中）
                        in_handler_code = True
                        continue
                    elif not has_pop_top and i == 0:
                        # 不包含POP_TOP的块中的第一条STORE_FAST（except-as的实际代码块）
                        in_handler_code = True
                        continue
            
            # 跳过异常处理框架指令
            # [关键修复] 对于裸except（except:），JUMP_FORWARD可能是except块内部的跳转
            # 不应该无条件过滤掉，需要根据上下文判断
            if instr.opname in ('PUSH_EXC_INFO', 'CHECK_EXC_MATCH', 'POP_EXCEPT', 
                               'RERAISE', 'COPY',
                               'POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_IF_FALSE',
                               'DELETE_FAST'):
                continue
            
            # [关键修复] 对于JUMP_FORWARD，需要特殊处理
            # 如果这是except块内部的跳转（in_handler_code为True），保留它
            # 如果这是异常处理框架的一部分（in_handler_code为False），跳过它
            if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE'):
                if not in_handler_code:
                    # 这是异常处理框架的跳转，跳过
                    continue
                # 否则保留，这是except块内部的跳转
            
            # 跳过 LOAD_GLOBAL 异常类型（在 CHECK_EXC_MATCH 之前的）
            if instr.opname in ('LOAD_GLOBAL', 'LOAD_NAME') and not in_handler_code:
                # 检查后续是否有 CHECK_EXC_MATCH
                has_check_exc_match = False
                for j in range(i + 1, len(block.instructions)):
                    next_instr = block.instructions[j]
                    if next_instr.opname == 'CHECK_EXC_MATCH':
                        has_check_exc_match = True
                        break
                    elif next_instr.opname in ('BUILD_TUPLE', 'LOAD_GLOBAL', 'LOAD_NAME'):
                        continue
                    else:
                        break
                if has_check_exc_match:
                    continue
            
            # 跳过 BUILD_TUPLE（异常类型元组）
            if instr.opname == 'BUILD_TUPLE' and not in_handler_code:
                continue
            
            # 跳过清理代码（LOAD_CONST None + STORE_FAST + DELETE_FAST）
            # 这种模式出现在except-as的末尾，用于清理异常变量
            if instr.opname == 'LOAD_CONST' and instr.argval is None:
                # 检查后续是否是 STORE_FAST + DELETE_FAST 模式（清理异常变量）
                if i + 2 < len(block.instructions):
                    next_instr = block.instructions[i + 1]
                    next_next_instr = block.instructions[i + 2]
                    if (next_instr.opname == 'STORE_FAST' and 
                        next_next_instr.opname == 'DELETE_FAST'):
                        # 跳过这三条指令（清理异常变量的模式）
                        continue
                # [关键修复] 检查是否是except handler块中的LOAD_CONST None
                # 如果是，这是清理代码的一部分，应该跳过
                # 特征：块中包含POP_EXCEPT或RERAISE
                is_except_cleanup = any(
                    i.opname in ('POP_EXCEPT', 'RERAISE', 'PUSH_EXC_INFO')
                    for i in block.instructions
                )
                if is_except_cleanup:
                    continue
            
            if instr.opname == 'STORE_FAST':
                # [关键修复] 检查前一条是否是 LOAD_CONST None（清理异常变量模式的一部分）
                # 包括两种情况：
                # 1. LOAD_CONST None + STORE_FAST + DELETE_FAST（完整的清理模式）
                # 2. LOAD_CONST None + STORE_FAST（简化的清理模式，没有DELETE_FAST）
                if i > 0 and block.instructions[i - 1].opname == 'LOAD_CONST':
                    if block.instructions[i - 1].argval is None:
                        # 这是清理异常变量的模式，跳过STORE_FAST
                        # 不需要检查下一条是否是DELETE_FAST，因为有些编译器优化会省略DELETE_FAST
                        continue
                # 检查是否是直接的None赋值（旧逻辑）
                if instr.argval is None:
                    continue
            
            # 跳过 DELETE_FAST（清理异常变量模式的一部分）
            if instr.opname == 'DELETE_FAST':
                # 检查前两条是否是 LOAD_CONST None + STORE_FAST
                if i >= 2:
                    if (block.instructions[i - 2].opname == 'LOAD_CONST' and
                        block.instructions[i - 2].argval is None and
                        block.instructions[i - 1].opname == 'STORE_FAST'):
                        continue
            
            filtered_instrs.append(instr)
        
        # 如果没有剩余指令，返回空或pass
        if not filtered_instrs:
            # [关键修复] 检查是否是裸except（只有异常处理框架指令）
            # 如果是，返回pass语句
            has_push_exc_info = any(instr.opname == 'PUSH_EXC_INFO' for instr in block.instructions)
            has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in block.instructions)
            if has_push_exc_info and has_pop_except:
                # 这是裸except，返回pass
                return {'type': 'Pass', 'lineno': None}
            return None
        
        # 创建临时块来生成AST
        temp_block = BasicBlock(block.start_offset)
        temp_block.end_offset = block.end_offset
        temp_block.instructions = filtered_instrs
        temp_block.successors = block.successors
        temp_block.predecessors = block.predecessors
        
        # [关键修复] 检查这个块是否是嵌套try-except结构的entry_block
        # 如果是，需要生成嵌套try-except的AST而不是普通块内容
        for struct in self.structures:
            if isinstance(struct, TryExceptStructure) and struct.entry_block == block:
                if id(struct) not in self.processed_structure_ids:
                    # 这是嵌套在except handler中的try-except结构
                    return self._generate_try_except_ast(struct)
        
        return self._generate_block_content_v2(temp_block)
    
    def _generate_generic_structure(self, struct: ControlStructure) -> Optional[Dict[str, Any]]:
        """生成通用结构的AST"""
        # [关键修复] 检查该结构是否包含return语句
        is_return_stmt = False
        entry_block = struct.entry_block
        for instr in entry_block.instructions:
            if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                is_return_stmt = True
                break
        
        # [关键修复] 如果已经生成了return语句，跳过这个结构
        # 这防止了异常处理路径中的重复return语句
        # [关键修复] 但是如果该结构包含return语句，不跳过
        if self._has_return_generated and not is_return_stmt:
            # 标记为已处理，但不生成AST
            self.processed_structure_ids.add(id(struct))
            return None
        
        # [关键修复] 检查该结构是否是其他结构的嵌套结构
        # 如果是，跳过，因为它会在处理外层结构时被递归处理
        # [关键修复] 但是如果该结构包含return语句，不跳过
        
        if not is_return_stmt:
            for other_struct in self.structures:
                if other_struct is not struct:
                    if isinstance(other_struct, IfStructure):
                        # [关键修复] 检查entry_block是否是其他if结构的entry_block、then_body或else_body
                        if (struct.entry_block == other_struct.entry_block or
                            struct.entry_block in other_struct.then_body or 
                            struct.entry_block in other_struct.else_body):
                            # 这是嵌套结构，跳过
                            self.processed_structure_ids.add(id(struct))
                            return None
                    elif isinstance(other_struct, LoopStructure):
                        if hasattr(other_struct, 'body_blocks') and struct.entry_block in other_struct.body_blocks:
                            # 这是循环体内的结构，跳过
                            self.processed_structure_ids.add(id(struct))
                            return None
                        if hasattr(other_struct, 'else_body') and struct.entry_block in other_struct.else_body:
                            # 这是循环else块内的结构，跳过
                            self.processed_structure_ids.add(id(struct))
                            return None
        
        # [关键修复] 检查该块是否是break/continue语句
        # 这些语句应该属于循环或if结构，不应该作为独立的SEQUENCE结构
        # [关键修复] 但是return语句需要被生成，它不属于循环或if结构
        entry_block = struct.entry_block
        is_control_flow_stmt = False
        is_return_stmt = False
        for instr in entry_block.instructions:
            if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD'):
                # 检查是否是break或continue
                # break和continue通常只有一个跳转指令
                if len(entry_block.instructions) <= 2:
                    is_control_flow_stmt = True
                    break
            elif instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                # return语句
                is_return_stmt = True
                break
        
        if is_control_flow_stmt:
            # 这是一个控制流语句（break/continue），不应该作为独立的SEQUENCE结构
            # 标记为已处理，但不生成AST
            self.processed_structure_ids.add(id(struct))
            return None
        # [关键修复] return语句不需要特殊处理，直接继续处理
        
        # 对于通用结构，直接使用块序列生成
        result = self._generate_block_sequence(struct.entry_block)
        
        # [关键修复] 检查生成的内容是否包含return语句
        if result:
            if isinstance(result, list):
                for stmt in result:
                    if isinstance(stmt, dict) and stmt.get('type') == 'Return':
                        self._has_return_generated = True
                        break
            elif isinstance(result, dict) and result.get('type') == 'Return':
                self._has_return_generated = True
        
        return result
    
    def _generate_block_sequence(self, start_block: BasicBlock) -> Optional[Dict[str, Any]]:
        """生成基本块序列的AST"""
        if start_block in self.generated_blocks:
            return None
        
        statements = []
        current = start_block
        
        while current and current not in self.generated_blocks:
            self.generated_blocks.add(current)
            content = self._generate_block_content_v2(current)
            if content:
                # [关键修复] 过滤掉孤立的表达式语句（如单独的变量名、函数调用等）
                filtered_content = self._filter_isolated_statements(content)
                if filtered_content:
                    if isinstance(filtered_content, list):
                        statements.extend(filtered_content)
                    else:
                        statements.append(filtered_content)
            
            if len(current.successors) == 1:
                next_block = list(current.successors)[0]
                # [关键修复] 检查下一个块是否是某个结构的入口
                # 如果是，停止处理，让结构处理逻辑来处理
                is_next_structure_entry = False
                for struct in self.structures:
                    if struct.entry_block == next_block:
                        if struct.struct_type != ControlStructureType.SEQUENCE:
                            is_next_structure_entry = True
                            break
                if is_next_structure_entry:
                    break
                current = next_block
            else:
                break
        
        if not statements:
            return None
        
        if len(statements) == 1:
            return statements[0]
        
        return {
            'type': 'Sequence',
            'statements': statements,
            'lineno': self._get_block_line(start_block)
        }
    
    def _filter_isolated_statements(self, content):
        """
        过滤掉孤立的表达式语句
        
        孤立语句是指那些不应该单独出现的表达式，如：
        - 单独的变量名（如 my_list, x 等）
        - 单独的字面量（如 100, 'string' 等）
        - 单独的函数调用结果未使用（如 range(10) 等）
        """
        if isinstance(content, list):
            filtered = []
            for stmt in content:
                if not self._is_isolated_statement(stmt):
                    filtered.append(stmt)
            return filtered if filtered else None
        else:
            if self._is_isolated_statement(content):
                return None
            return content
    
    def _is_isolated_statement(self, stmt):
        """检查是否为孤立语句"""
        if not isinstance(stmt, dict):
            return False
        
        stmt_type = stmt.get('type', '')
        
        # Expr语句（表达式语句）可能是孤立的
        if stmt_type == 'Expr':
            value = stmt.get('value', {})
            value_type = value.get('type', '')
            
            # 单独的变量引用是孤立的
            if value_type == 'Name':
                return True
            
            # 单独的字面量是孤立的
            if value_type == 'Constant':
                return True
            
            # 单独的调用（如果结果未被使用）可能是孤立的
            # 但我们需要谨慎，因为有些调用可能有副作用（如print）
            if value_type == 'Call':
                func = value.get('func', {})
                func_name = func.get('id', '') if isinstance(func, dict) else ''
                # 如果调用的是range()且结果未被使用，是孤立的
                if func_name == 'range':
                    return True
            
            # [关键修复] 单独的一元操作（如+(flag)）是孤立的
            if value_type == 'UnaryOp':
                return True
            
            # [关键修复] 单独的比较操作（如y == 10）如果没有被使用，是孤立的
            if value_type == 'Compare':
                return True
            
            # [关键修复] 单独的二元操作（如List + int）是孤立的
            if value_type == 'BinOp':
                return True
            
            # [关键修复] 单独的Attribute访问（如my_dict.name）如果没有被使用，是孤立的
            if value_type == 'Attribute':
                return True
            
            # [关键修复] 单独的Subscript访问（如my_dict['key']）如果没有被使用，是孤立的
            if value_type == 'Subscript':
                return True
        
        # [关键修复] Pass语句在大多数情况下可以被视为孤立的（除非是空的if/while/for体）
        if stmt_type == 'Pass':
            # 暂时不过滤Pass，因为它们是合法的空语句
            return False
        
        return False
    
    def _generate_instructions_content(self, instructions: List[Instruction], 
                                       shared_stack: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """从指令列表生成AST语句列表"""
        # [关键修复] 保留 POP_JUMP_* 指令以便正确处理栈上的条件值
        # 这些指令会在 _process_instruction_sequence 中被处理
        # [关键修复] 保留 GET_ITER 指令以便推导式检测代码能够正确识别推导式调用
        # [关键修复] 保留 JUMP_FORWARD 以便正确处理 break/continue
        # [关键修复] 保留 JUMP_IF_TRUE_OR_POP 和 JUMP_IF_FALSE_OR_POP 用于重建 and/or 表达式
        # [关键修复] 保留 JUMP_BACKWARD 以便正确处理 continue 语句
        non_jump_instrs = [
            instr for instr in instructions
            if instr.opname not in {
                'JUMP_ABSOLUTE',
                'FOR_ITER', 'FOR_ITER_RANGE'
            }
        ]

        if not non_jump_instrs:
            return []
        
        # [关键修复] 处理NOP指令 - 将指令列表分成NOP前和NOP后两部分
        # 找到第一个NOP的位置
        first_nop_idx = -1
        last_nop_idx = -1
        for i, instr in enumerate(non_jump_instrs):
            if instr.opname == 'NOP':
                if first_nop_idx == -1:
                    first_nop_idx = i
                last_nop_idx = i
        
        # 如果没有NOP，正常处理
        if first_nop_idx == -1:
            return self._process_instruction_sequence(non_jump_instrs, shared_stack)
        
        # [关键修复] 检查是否是编译器优化后的残留NOP
        # 特征：
        # 1. 多个连续的NOP指令
        # 2. 没有条件跳转指令（POP_JUMP_*）
        # 这种情况下，NOP只是行号标记，不应该生成if语句
        nop_count = 0
        has_conditional_jump = False
        for instr in non_jump_instrs:
            if instr.opname == 'NOP':
                nop_count += 1
            elif instr.opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                                 'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                                 'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                has_conditional_jump = True
                break
        
        # 如果有多个NOP或没有条件跳转，这是优化残留，不创建if结构
        if nop_count > 1 or not has_conditional_jump:
            # 过滤掉NOP指令，只处理实际代码
            filtered_instrs = [instr for instr in non_jump_instrs if instr.opname != 'NOP']
            return self._process_instruction_sequence(filtered_instrs, shared_stack)
        
        # [关键修复] 处理NOP指令
        # NOP之前的指令正常处理
        pre_nop_instrs = non_jump_instrs[:first_nop_idx]
        # NOP之后的指令（包括NOP）需要特殊处理
        nop_and_after = non_jump_instrs[first_nop_idx:]
        
        # 统计连续的NOP数量
        nop_count = 0
        for instr in nop_and_after:
            if instr.opname == 'NOP':
                nop_count += 1
            else:
                break
        
        # NOP之后的实际指令
        after_nop_instrs = nop_and_after[nop_count:]
        
        # 处理NOP之前的指令
        pre_statements = []
        if pre_nop_instrs:
            pre_statements = self._process_instruction_sequence(pre_nop_instrs, shared_stack)
        
        # 处理NOP之后的指令
        after_statements = []
        if after_nop_instrs:
            after_statements = self._process_instruction_sequence(after_nop_instrs, shared_stack)
        
        # 如果有NOP，创建嵌套的if True:语句
        if nop_count > 0 and after_statements:
            lineno = after_statements[0].get('lineno') if after_statements else None
            
            # 创建最内层的if语句，包含NOP之后的所有语句
            nested_if = {
                'type': 'If',
                'test': {'type': 'Constant', 'value': True, 'lineno': lineno},
                'body': after_statements,
                'orelse': [],
                'lineno': lineno
            }
            
            # 为剩余的NOP创建嵌套的if语句
            for _ in range(nop_count - 1):
                nested_if = {
                    'type': 'If',
                    'test': {'type': 'Constant', 'value': True, 'lineno': lineno},
                    'body': [nested_if],
                    'orelse': [],
                    'lineno': lineno
                }
            
            # 合并pre_statements和嵌套if
            if pre_statements:
                pre_statements.append(nested_if)
                return pre_statements
            else:
                return [nested_if]
        elif nop_count > 0:
            # 只有NOP，没有后续语句
            lineno = None
            nested_if = {
                'type': 'If',
                'test': {'type': 'Constant', 'value': True, 'lineno': lineno},
                'body': [],
                'orelse': [],
                'lineno': lineno
            }
            
            for _ in range(nop_count - 1):
                nested_if = {
                    'type': 'If',
                    'test': {'type': 'Constant', 'value': True, 'lineno': lineno},
                    'body': [nested_if],
                    'orelse': [],
                    'lineno': lineno
                }
            
            if pre_statements:
                pre_statements.append(nested_if)
                return pre_statements
            else:
                return [nested_if]
        
        # 没有NOP，正常返回
        return pre_statements if pre_statements else []

    def _generate_block_content_v2(self, block: BasicBlock, 
                                    shared_stack: Optional[List[Dict[str, Any]]] = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """生成基本块内容的AST（改进版）"""
        # [关键修复] 设置当前块，供指令处理使用
        self.current_block = block
        statements = self._generate_instructions_content(block.instructions, shared_stack)
        self.current_block = None
        
        if not statements:
            return None
        
        if len(statements) == 1:
            return statements[0]
        
        return statements
    
    def _process_instruction_sequence(self, instructions: List[Instruction],
                                      shared_stack: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """处理指令序列，返回AST语句列表"""
        statements = []
        # [关键修复] 使用共享栈或创建新栈
        stack = shared_stack if shared_stack is not None else []
        last_was_copy = False  # [海象运算符] 跟踪上一条指令是否是 COPY
        copy_depth = 0  # [海象运算符] COPY 指令的深度参数
        # [关键修复] 使用实例变量跟踪解包状态，以便跨基本块保持状态
        unpack_state = self._unpack_state

        # [关键修复] 统计连续的NOP指令数量
        nop_count = 0
        # [关键修复] 标记是否已经遇到NOP
        nop_encountered = False
        # [关键修复] NOP之前的语句
        pre_nop_statements = []
        
        for instr in instructions:
            opname = instr.opname

            # 忽略 Python 3.11+ 的特殊指令
            if opname in ('RESUME', 'CACHE'):
                continue
            
            # [关键修复] NOP指令 - 对应优化后的if True:语句
            if opname == 'NOP':
                nop_count += 1
                nop_encountered = True
                continue
            
            # [关键修复] POP_JUMP_* 指令 - 消费栈顶的条件值，不生成语句
            # 这些指令在控制流分析时处理，这里只需要清空栈上的条件值
            if opname in ('POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                         'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                         'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'):
                if stack:
                    # 弹出条件值，但不使用它（条件在if结构中提取）
                    stack.pop()
                last_was_copy = False
                continue
            
            # [关键修复] JUMP_IF_FALSE_OR_POP - 逻辑与(and)的短路求值
            # 如果条件为False，跳转到目标地址；否则弹出条件值并继续
            if opname == 'JUMP_IF_FALSE_OR_POP':
                if stack:
                    # 弹出左侧条件值
                    left = stack.pop()
                    # [关键修复] 检查栈中是否已经有 BoolOpPending，如果是，合并它们
                    if stack and stack[-1].get('type') == 'BoolOpPending':
                        existing = stack.pop()
                        # 合并为新的 BoolOpPending
                        left = {
                            'type': 'BoolOp',
                            'op': existing['op'],
                            'values': [existing['left'], left],
                            'lineno': existing.get('lineno')
                        }
                    # 标记这是一个逻辑与的左操作数，等待右操作数
                    stack.append({
                        'type': 'BoolOpPending',
                        'op': 'and',
                        'left': left,
                        'lineno': instr.starts_line
                    })
                last_was_copy = False
                continue
            
            # [关键修复] JUMP_IF_TRUE_OR_POP - 逻辑或(or)的短路求值
            # 如果条件为True，跳转到目标地址；否则弹出条件值并继续
            if opname == 'JUMP_IF_TRUE_OR_POP':
                if stack:
                    # 弹出左侧条件值
                    left = stack.pop()
                    # [关键修复] 检查栈中是否已经有 BoolOpPending，如果是，合并它们
                    if stack and stack[-1].get('type') == 'BoolOpPending':
                        existing = stack.pop()
                        # 合并为新的 BoolOpPending
                        left = {
                            'type': 'BoolOp',
                            'op': existing['op'],
                            'values': [existing['left'], left],
                            'lineno': existing.get('lineno')
                        }
                    # 标记这是一个逻辑或的左操作数，等待右操作数
                    stack.append({
                        'type': 'BoolOpPending',
                        'op': 'or',
                        'left': left,
                        'lineno': instr.starts_line
                    })
                last_was_copy = False
                continue
            
            # [关键修复] PUSH_NULL - Python 3.11+ 的null推送
            if opname == 'PUSH_NULL':
                stack.append({
                    'type': 'Constant',
                    'value': None,
                    'lineno': instr.starts_line
                })
                last_was_copy = False
                continue
            
            # [海象运算符] COPY 指令 - 复制栈顶值，用于 := 运算符和链式比较
            if opname == 'COPY':
                if stack:
                    # COPY n 复制栈上第 n 个值（从栈顶开始计数，1表示栈顶）
                    depth = instr.arg if instr.arg is not None else 1
                    if depth >= 1 and depth <= len(stack):
                        # 复制栈上第 depth 个值
                        # depth=1 表示栈顶，depth=2 表示栈顶下面一个，以此类推
                        value_to_copy = stack[-depth]
                        stack.append(value_to_copy.copy() if isinstance(value_to_copy, dict) else value_to_copy)
                        last_was_copy = True
                        copy_depth = depth
                continue

            # [关键修复] SWAP 指令 - Python 3.11+ 的栈交换指令，用于链式比较和增强赋值
            if opname == 'SWAP':
                if stack and len(stack) >= 2:
                    # SWAP n 交换栈顶和第 n 个元素（从栈顶开始计数，1表示栈顶）
                    depth = instr.arg if instr.arg is not None else 1
                    if depth == 2 and len(stack) >= 2:
                        # 交换栈顶的两个元素
                        stack[-1], stack[-2] = stack[-2], stack[-1]
                    elif depth == 3 and len(stack) >= 3:
                        # [关键修复] SWAP 3用于增强赋值，交换栈顶和第3个元素
                        # 栈布局: [a, b, c] -> [c, b, a]
                        stack[-1], stack[-3] = stack[-3], stack[-1]
                last_was_copy = False
                continue

            # [关键修复] RAISE_VARARGS 指令 - raise 语句
            if opname == 'RAISE_VARARGS':
                if instr.arg == 1:
                    # RAISE_VARARGS 1: raise exception
                    if stack:
                        exc = stack.pop()
                        statements.append({
                            'type': 'Raise',
                            'exc': exc,
                            'lineno': instr.starts_line
                        })
                elif instr.arg == 0:
                    # RAISE_VARARGS 0: reraise current exception
                    statements.append({
                        'type': 'Raise',
                        'exc': None,
                        'lineno': instr.starts_line
                    })
                last_was_copy = False
                continue
            
            # [关键修复] 异常处理指令 - 处理 with 语句的异常处理块
            if opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'POP_EXCEPT', 'RERAISE', 'CHECK_EXC_MATCH'):
                # 这些指令是异常处理的框架指令，不生成实际的 Python 代码
                # 但需要正确处理栈状态，避免栈溢出或栈不足
                if opname == 'PUSH_EXC_INFO':
                    # 压入异常信息到栈上
                    # 生成一个特殊的异常信息对象
                    stack.append({
                        'type': 'ExceptionInfo',
                        'value': None,
                        'lineno': instr.starts_line
                    })
                elif opname == 'WITH_EXCEPT_START':
                    # 开始 with 语句的异常处理
                    # 从栈顶弹出异常信息，不生成代码
                    if stack:
                        stack.pop()
                elif opname == 'POP_EXCEPT':
                    # 结束异常处理
                    # 不需要特殊处理，只需要跳过
                    pass
                elif opname == 'RERAISE':
                    # 重新抛出异常
                    # 这是异常处理框架的一部分，不生成实际的 raise 语句
                    # 只需要处理栈状态
                    pass
                elif opname == 'CHECK_EXC_MATCH':
                    # 检查异常匹配
                    # 这是异常处理框架的一部分，不生成实际的代码
                    # 只需要处理栈状态
                    pass
                last_was_copy = False
                continue

            # [关键修复] UNPACK_SEQUENCE 指令 - 解包序列赋值
            if opname == 'UNPACK_SEQUENCE':
                if stack:
                    # 弹出要解包的值
                    value = stack.pop()
                    # 初始化解包状态
                    unpack_state = {
                        'count': instr.arg if instr.arg is not None else 2,  # 解包的目标数量
                        'targets': [],  # 目标变量列表
                        'value': value,  # 要解包的值
                        'line': instr.starts_line  # 行号
                    }
                    # [关键修复] 将解包后的值压入栈中（从右到左）
                    # 这样后续的 STORE_FAST 可以正常弹出值
                    if value.get('type') == 'Constant' and isinstance(value.get('value'), tuple):
                        tuple_values = value['value']
                        for item in reversed(tuple_values):
                            stack.append({
                                'type': 'Constant',
                                'value': item,
                                'lineno': instr.starts_line
                            })
                    else:
                        # 对于非元组，创建占位符
                        for i in range(instr.arg if instr.arg is not None else 2):
                            stack.append({
                                'type': 'UnpackItem',
                                'index': i,
                                'lineno': instr.starts_line
                            })
                last_was_copy = False
                continue

            # [海象运算符] STORE 指令 - 检查是否是海象运算符模式
            if opname in ('STORE_NAME', 'STORE_FAST', 'STORE_GLOBAL', 'STORE_DEREF'):
                if stack:
                    value = stack.pop()
                    
                    # [关键修复] 检查栈中是否有 BoolOpPending，这是逻辑运算赋值（如 a = x and y）
                    # 逻辑运算赋值的字节码：LOAD_FAST x; JUMP_IF_FALSE_OR_POP; LOAD_FAST y; STORE_FAST a
                    # 此时栈中应该有 BoolOpPending 和右操作数 y
                    if stack and stack[-1].get('type') == 'BoolOpPending':
                        boolop_pending = stack.pop()
                        # 合并为完整的 BoolOp
                        value = {
                            'type': 'BoolOp',
                            'op': boolop_pending['op'],
                            'values': [boolop_pending['left'], value],
                            'lineno': boolop_pending.get('lineno')
                        }
                    
                    # [关键修复] 检查是否是导入别名模式
                    # import numpy as np -> value是ImportPending，instr.argval是'np'
                    # from os.path import join as path_join -> value是ImportFromPending，instr.argval是'path_join'
                    if isinstance(value, dict) and value.get('type') == 'ImportPending':
                        # import ... as ... 形式
                        module_name = value.get('module')
                        alias = instr.argval
                        statements.append({
                            'type': 'Import',
                            'names': [{'name': module_name, 'asname': alias if alias != module_name else None}],
                            'lineno': instr.starts_line
                        })
                        last_was_copy = False
                        continue
                    # [关键修复] 检查是否是from import别名模式
                    # 栈中应该有ImportFromPending标记，value是Name节点（导入名）
                    # 需要查找栈中的ImportFromPending标记
                    import_from_pending = None
                    import_from_pending_idx = -1
                    for i in range(len(stack) - 1, -1, -1):
                        if isinstance(stack[i], dict) and stack[i].get('type') == 'ImportFromPending':
                            import_from_pending = stack[i]
                            import_from_pending_idx = i
                            break
                    
                    if import_from_pending and isinstance(value, dict) and value.get('type') == 'Name':
                        # from ... import ... as ... 形式
                        module_name = import_from_pending.get('module')
                        original_name = value.get('id')  # 导入的原始名称
                        alias = instr.argval  # 别名（存储的名称）
                        
                        # [关键修复] 查找是否已经有相同模块的ImportFrom语句
                        existing_import_from = None
                        for stmt in reversed(statements):
                            if stmt.get('type') == 'ImportFrom' and stmt.get('module') == module_name:
                                existing_import_from = stmt
                                break
                        
                        if existing_import_from:
                            # 添加到现有的ImportFrom语句
                            existing_import_from['names'].append({
                                'name': original_name,
                                'asname': alias if alias != original_name else None
                            })
                        else:
                            # 创建新的ImportFrom语句
                            statements.append({
                                'type': 'ImportFrom',
                                'module': module_name,
                                'names': [{'name': original_name, 'asname': alias if alias != original_name else None}],
                                'lineno': instr.starts_line
                            })
                        
                        # 移除ImportFromPending标记（可选，取决于是否还有更多的导入）
                        # 这里不移除，因为可能有多个from import语句
                        
                        last_was_copy = False
                        continue
                    
                    # [海象运算符] 如果上一条指令是 COPY，则生成 NamedExpr (:=)
                    if last_was_copy and copy_depth == 1:
                        # [关键修复] 海象运算符模式：COPY + STORE_FAST
                        # COPY 指令复制了栈顶值，STORE_FAST 弹出复制的值
                        # 但原始值仍然在栈中（在复制的值下面），需要移除
                        # 检查栈中是否还有与 value 相同的原始值
                        if stack and len(stack) >= 1:
                            # 栈顶现在是 NamedExpr 或其他值
                            # 我们需要找到并移除原始的 Call 节点
                            for i in range(len(stack) - 1, -1, -1):
                                if stack[i] == value or (isinstance(stack[i], dict) and isinstance(value, dict) and
                                    stack[i].get('type') == value.get('type') and
                                    stack[i].get('func', {}).get('id') == value.get('func', {}).get('id')):
                                    # 移除原始值
                                    stack.pop(i)
                                    break
                        
                        # 创建海象运算符表达式，压回栈中供后续使用
                        named_expr = {
                            'type': 'NamedExpr',
                            'target': {
                                'type': 'Name',
                                'id': instr.argval,
                                'ctx': 'Store',
                                'lineno': instr.starts_line
                            },
                            'value': value,
                            'lineno': instr.starts_line
                        }
                        stack.append(named_expr)
                        last_was_copy = False
                    else:
                        # [关键修复] 检查是否是装饰器调用后的赋值
                        # 支持两种情况：
                        # 1. 单层装饰器: Call(args=[FunctionObject])
                        # 2. 多层装饰器: Call(func=Call(...), args=[])
                        is_decorator = False
                        func_object = None
                        decorator_list = []
                        
                        if value.get('type') == 'Call' and value.get('func', {}).get('id') != '__build_class__':
                            # [关键修复] 处理多层装饰器和带参数的装饰器
                            # 支持：
                            # 1. 单层装饰器: Call(func=Name, args=[FunctionObject])
                            # 2. 多层装饰器: Call(func=Name, args=[Call(...)])
                            # 3. 带参数装饰器: Call(func=Call(func=Name, args=[...]), args=[FunctionObject])
                            def extract_decorators_v2(call_node):
                                """递归提取装饰器列表和FunctionObject（从内到外）"""
                                if call_node.get('type') == 'FunctionObject':
                                    return [], call_node
                                
                                if call_node.get('type') == 'Call':
                                    func = call_node.get('func', {})
                                    args = call_node.get('args', [])
                                    
                                    # func 是 Name：当前层的装饰器（无参数）
                                    if func.get('type') == 'Name':
                                        if args:
                                            # 单层装饰器：args[0] 是 FunctionObject
                                            if args[0].get('type') == 'FunctionObject':
                                                return [func], args[0]
                                            # 多层装饰器：args[0] 是另一个 Call
                                            elif args[0].get('type') == 'Call':
                                                inner_decs, func_obj = extract_decorators_v2(args[0])
                                                if func_obj:
                                                    return inner_decs + [func], func_obj
                                    
                                    # func 是 Call：带参数的装饰器
                                    # 例如: @decorator_with_args('hello', 'world')
                                    elif func.get('type') == 'Call':
                                        inner_func = func.get('func', {})
                                        inner_args = func.get('args', [])
                                        if inner_func.get('type') == 'Name' and args:
                                            # args[0] 应该是 FunctionObject
                                            if args[0].get('type') == 'FunctionObject':
                                                # 构造带参数的装饰器节点
                                                decorator_with_args = {
                                                    'type': 'Call',
                                                    'func': inner_func,
                                                    'args': inner_args
                                                }
                                                return [decorator_with_args], args[0]
                                            # 多层带参数装饰器
                                            elif args[0].get('type') == 'Call':
                                                inner_decs, func_obj = extract_decorators_v2(args[0])
                                                if func_obj:
                                                    decorator_with_args = {
                                                        'type': 'Call',
                                                        'func': inner_func,
                                                        'args': inner_args
                                                    }
                                                    return inner_decs + [decorator_with_args], func_obj
                                
                                return [], None
                            
                            decorators, func_object = extract_decorators_v2(value)
                            
                            if func_object:
                                decorator_list = decorators
                                is_decorator = True
                        
                        if is_decorator and func_object:
                            func_name = instr.argval
                            code_value = func_object.get('code')
                            
                            # [关键修复] 支持两种code存储格式：直接CodeType或CodeObject字典
                            if isinstance(code_value, types.CodeType):
                                code_obj = code_value
                            elif isinstance(code_value, dict) and code_value.get('type') == 'CodeObject':
                                code_obj = code_value.get('code')
                            else:
                                code_obj = None
                            
                            # [关键修复] 从code对象提取参数信息，包括默认值
                            func_args = {'args': [], 'defaults': [], 'kwonlyargs': [], 'kw_defaults': []}
                            
                            # [关键修复] 从FunctionObject获取位置参数默认值
                            defaults_value = func_object.get('defaults', {})
                            defaults_tuple = defaults_value.get('value') if isinstance(defaults_value, dict) else None
                            
                            # [关键修复] 从FunctionObject获取关键字-only参数默认值
                            kw_defaults_value = func_object.get('kw_defaults', {})
                            # [关键修复] kw_defaults可能是Dict节点或普通字典
                            if isinstance(kw_defaults_value, dict):
                                if kw_defaults_value.get('type') == 'Dict':
                                    # 从Dict节点提取键值对
                                    keys = kw_defaults_value.get('keys', [])
                                    values = kw_defaults_value.get('values', [])
                                    kw_defaults_dict = {}
                                    for i, key in enumerate(keys):
                                        if key.get('type') == 'Constant':
                                            key_name = key.get('value')
                                            if i < len(values):
                                                val = values[i]
                                                if val.get('type') == 'Constant':
                                                    kw_defaults_dict[key_name] = val.get('value')
                                else:
                                    kw_defaults_dict = kw_defaults_value.get('value')
                            else:
                                kw_defaults_dict = None
                            
                            # [关键修复] 从FunctionObject获取类型注解
                            annotations = value.get('annotations')
                            
                            if code_obj and hasattr(code_obj, 'co_code'):
                                func_args = self._extract_function_args(code_obj, defaults_tuple, kw_defaults_dict, annotations)
                            
                            # [关键修复] 递归反编译函数体
                            func_body = []
                            if self.recursive and code_obj:
                                try:
                                    from .cfg_builder import build_cfg
                                    func_cfg = build_cfg(code_obj, func_name)
                                    func_generator = ASTGeneratorV2(func_cfg, recursive=True)
                                    func_ast = func_generator.generate()
                                    if func_ast and func_ast.get('body'):
                                        func_body = func_ast['body']
                                        
                                        # [关键修复] 提取并添加文档字符串
                                        # Python 3.11+中，文档字符串存储在co_consts[0]，不再通过LOAD_CONST加载
                                        if (code_obj and hasattr(code_obj, 'co_consts') and 
                                            len(code_obj.co_consts) > 0):
                                            first_const = code_obj.co_consts[0]
                                            if isinstance(first_const, str) and first_const:
                                                # 检查文档字符串是否已经在body中
                                                docstring_in_body = False
                                                if func_body:
                                                    first_stmt = func_body[0]
                                                    if (first_stmt.get('type') == 'Expr' and
                                                        first_stmt.get('value', {}).get('type') == 'Constant' and
                                                        first_stmt.get('value', {}).get('value') == first_const):
                                                        docstring_in_body = True
                                                
                                                if not docstring_in_body:
                                                    # 添加文档字符串作为函数体的第一个语句
                                                    docstring_node = {
                                                        'type': 'Expr',
                                                        'value': {
                                                            'type': 'Constant',
                                                            'value': first_const,
                                                            'lineno': instr.starts_line
                                                        },
                                                        'lineno': instr.starts_line
                                                    }
                                                    func_body.insert(0, docstring_node)
                                        
                                        # [调试] 记录成功反编译的函数
                                        import os
                                        if os.environ.get('PYCDC_DEBUG'):
                                            print(f"[DEBUG] 函数 {func_name} 反编译成功，{len(func_body)} 个节点")
                                    else:
                                        import os
                                        if os.environ.get('PYCDC_DEBUG'):
                                            print(f"[DEBUG] 函数 {func_name} AST为空")
                                except Exception as e:
                                    # [调试] 记录异常
                                    import os
                                    if os.environ.get('PYCDC_DEBUG'):
                                        print(f"[DEBUG] 函数 {func_name} 反编译失败: {e}")
                            
                            if not func_body:
                                func_body = [{'type': 'Pass', 'lineno': instr.starts_line}]
                            
                            # [异步] 检测是否是异步函数
                            # CO_COROUTINE = 128 (0x80)
                            # CO_ITERABLE_COROUTINE = 256 (0x100)
                            is_async = False
                            if code_obj and hasattr(code_obj, 'co_flags'):
                                is_async = bool(code_obj.co_flags & 0x80) or bool(code_obj.co_flags & 0x100)
                            
                            # [关键修复] 从func_args提取returns字段
                            returns = func_args.get('returns') if isinstance(func_args, dict) else None
                            
                            # 创建带装饰器的函数定义
                            func_def = {
                                'type': 'FunctionDef',
                                'name': func_name,
                                'args': func_args,
                                'body': func_body,
                                'decorator_list': decorator_list,
                                'is_async': is_async,  # [异步] 添加异步标志
                                'lineno': instr.starts_line
                            }
                            
                            # [关键修复] 添加返回类型注解
                            if returns:
                                func_def['returns'] = returns
                            
                            statements.append(func_def)
                        # [关键修复] 检查是否是函数定义
                        elif value.get('type') == 'FunctionObject':
                            # 创建函数定义节点
                            func_name = instr.argval
                            code_value = value.get('code')
                            
                            # [关键修复] 支持两种code存储格式：直接CodeType或CodeObject字典
                            if isinstance(code_value, types.CodeType):
                                code_obj = code_value
                            elif isinstance(code_value, dict) and code_value.get('type') == 'CodeObject':
                                code_obj = code_value.get('code')
                            else:
                                code_obj = None
                            
                            # [关键修复] 检查是否是lambda函数（code对象的名字为<lambda>）
                            is_lambda = code_obj and hasattr(code_obj, 'co_name') and code_obj.co_name == '<lambda>'
                            
                            # [关键修复] 从code对象提取参数信息，包括默认值
                            func_args = {'args': [], 'defaults': [], 'kwonlyargs': [], 'kw_defaults': []}
                            
                            # [关键修复] 从FunctionObject获取位置参数默认值
                            defaults_value = value.get('defaults', {})
                            defaults_tuple = defaults_value.get('value') if isinstance(defaults_value, dict) else None
                            
                            # [关键修复] 从FunctionObject获取关键字-only参数默认值
                            kw_defaults_value = value.get('kw_defaults', {})
                            # [关键修复] kw_defaults可能是Dict节点或普通字典
                            if isinstance(kw_defaults_value, dict):
                                if kw_defaults_value.get('type') == 'Dict':
                                    # 从Dict节点提取键值对
                                    keys = kw_defaults_value.get('keys', [])
                                    values = kw_defaults_value.get('values', [])
                                    kw_defaults_dict = {}
                                    for i, key in enumerate(keys):
                                        if key.get('type') == 'Constant':
                                            key_name = key.get('value')
                                            if i < len(values):
                                                val = values[i]
                                                if val.get('type') == 'Constant':
                                                    kw_defaults_dict[key_name] = val.get('value')
                                else:
                                    kw_defaults_dict = kw_defaults_value.get('value')
                            else:
                                kw_defaults_dict = None
                            
                            # [关键修复] 从FunctionObject获取类型注解
                            annotations = value.get('annotations')
                            
                            if code_obj and hasattr(code_obj, 'co_code'):
                                func_args = self._extract_function_args(code_obj, defaults_tuple, kw_defaults_dict, annotations)
                            
                            # [关键修复] 递归反编译函数体
                            func_body = []
                            if self.recursive and code_obj:
                                # 递归构建CFG并生成AST
                                try:
                                    from .cfg_builder import build_cfg
                                    func_cfg = build_cfg(code_obj, func_name)
                                    func_generator = ASTGeneratorV2(func_cfg, recursive=True)
                                    func_ast = func_generator.generate()
                                    if func_ast and func_ast.get('body'):
                                        func_body = func_ast['body']
                                        
                                        # [关键修复] 提取并添加文档字符串
                                        # Python 3.11+中，文档字符串存储在co_consts[0]，不再通过LOAD_CONST加载
                                        if (code_obj and hasattr(code_obj, 'co_consts') and 
                                            len(code_obj.co_consts) > 0):
                                            first_const = code_obj.co_consts[0]
                                            if isinstance(first_const, str) and first_const:
                                                # 检查文档字符串是否已经在body中
                                                docstring_in_body = False
                                                if func_body:
                                                    first_stmt = func_body[0]
                                                    if (first_stmt.get('type') == 'Expr' and
                                                        first_stmt.get('value', {}).get('type') == 'Constant' and
                                                        first_stmt.get('value', {}).get('value') == first_const):
                                                        docstring_in_body = True
                                                
                                                if not docstring_in_body:
                                                    # 添加文档字符串作为函数体的第一个语句
                                                    docstring_node = {
                                                        'type': 'Expr',
                                                        'value': {
                                                            'type': 'Constant',
                                                            'value': first_const,
                                                            'lineno': instr.starts_line
                                                        },
                                                        'lineno': instr.starts_line
                                                    }
                                                    func_body.insert(0, docstring_node)
                                except Exception as e:
                                    # [调试] 记录异常
                                    import os
                                    if os.environ.get('PYCDC_DEBUG'):
                                        print(f"[DEBUG] 函数(普通) {func_name} 反编译失败: {e}")
                                    # 递归失败，使用空body
                                    pass
                            
                            # 如果body为空，添加pass语句
                            if not func_body:
                                func_body = [{'type': 'Pass', 'lineno': instr.starts_line}]
                            
                            # [关键修复] 如果是lambda函数，创建Lambda节点
                            if is_lambda:
                                # 提取lambda体（应该是单个表达式）
                                lambda_body = None
                                if func_body:
                                    # 过滤掉Pass和return None
                                    filtered_body = [stmt for stmt in func_body if stmt.get('type') != 'Pass']
                                    if filtered_body:
                                        # lambda体应该是return语句或表达式
                                        first_stmt = filtered_body[0]
                                        if first_stmt.get('type') == 'Return' and first_stmt.get('value'):
                                            lambda_body = first_stmt['value']
                                        elif first_stmt.get('type') == 'Expr' and first_stmt.get('value'):
                                            lambda_body = first_stmt['value']
                                        elif first_stmt.get('type') == 'If':
                                            # [关键修复] 处理条件表达式 (x if cond else y)
                                            # If节点在lambda体中表示条件表达式
                                            # 转换为IfExp节点
                                            test = first_stmt.get('test')
                                            body = first_stmt.get('body')
                                            orelse = first_stmt.get('orelse')
                                            
                                            # 提取body和orelse中的实际值
                                            if body and len(body) > 0:
                                                body_stmt = body[0]
                                                if body_stmt.get('type') == 'Return' and body_stmt.get('value'):
                                                    body_val = body_stmt['value']
                                                elif body_stmt.get('type') == 'Expr' and body_stmt.get('value'):
                                                    body_val = body_stmt['value']
                                                else:
                                                    body_val = body_stmt
                                            else:
                                                body_val = {'type': 'Constant', 'value': None}
                                            
                                            if orelse and len(orelse) > 0:
                                                orelse_stmt = orelse[0]
                                                if orelse_stmt.get('type') == 'Return' and orelse_stmt.get('value'):
                                                    orelse_val = orelse_stmt['value']
                                                elif orelse_stmt.get('type') == 'Expr' and orelse_stmt.get('value'):
                                                    orelse_val = orelse_stmt['value']
                                                else:
                                                    orelse_val = orelse_stmt
                                            else:
                                                orelse_val = {'type': 'Constant', 'value': None}
                                            
                                            lambda_body = {
                                                'type': 'IfExp',
                                                'test': test,
                                                'body': body_val,
                                                'orelse': orelse_val,
                                                'lineno': first_stmt.get('lineno')
                                            }
                                        else:
                                            lambda_body = first_stmt
                                
                                # 创建赋值语句，值为lambda表达式
                                statements.append({
                                    'type': 'Assign',
                                    'targets': [{
                                        'type': 'Name',
                                        'id': func_name,
                                        'ctx': 'Store',
                                        'lineno': instr.starts_line
                                    }],
                                    'value': {
                                        'type': 'Lambda',
                                        'args': func_args,
                                        'body': lambda_body if lambda_body else {'type': 'Constant', 'value': None},
                                        'lineno': instr.starts_line
                                    },
                                    'lineno': instr.starts_line
                                })
                            else:
                                # [异步] 检测是否是异步函数
                                # CO_COROUTINE = 128 (0x80)
                                # CO_ITERABLE_COROUTINE = 256 (0x100)
                                is_async = False
                                if code_obj and hasattr(code_obj, 'co_flags'):
                                    is_async = bool(code_obj.co_flags & 0x80) or bool(code_obj.co_flags & 0x100)
                                
                                # [关键修复] 从func_args中提取returns
                                returns = func_args.pop('returns', None) if isinstance(func_args, dict) else None
                                
                                statements.append({
                                    'type': 'FunctionDef',
                                    'name': func_name,
                                    'args': func_args,
                                    'body': func_body,
                                    'decorator_list': [],
                                    'returns': returns,  # [关键修复] 添加返回类型注解
                                    'is_async': is_async,  # [异步] 添加异步标志
                                    'lineno': instr.starts_line
                                })
                        # [关键修复] 检查是否是类定义（通过CALL创建，且func是__build_class__）
                        elif (value.get('type') == 'Call' and
                              value.get('func', {}).get('id') == '__build_class__' and
                              len(value.get('args', [])) >= 2):
                            # 这是类定义
                            # args[0]是类体函数，args[1]是类名，args[2:]是基类
                            class_body_func = value['args'][0] if len(value['args']) > 0 else None
                            class_name_arg = value['args'][1] if len(value['args']) > 1 else None
                            if class_name_arg and class_name_arg.get('type') == 'Constant':
                                class_name = class_name_arg.get('value', instr.argval)
                            else:
                                class_name = instr.argval

                            # 提取基类（从args[2]开始）和关键字参数
                            bases = []
                            keywords = []
                            for base_arg in value['args'][2:]:
                                if base_arg.get('type') == 'Name':
                                    bases.append(base_arg)
                            
                            # [关键修复] 提取关键字参数（如metaclass=MetaClass）
                            call_kwargs = value.get('kwargs', [])
                            for kw in call_kwargs:
                                if isinstance(kw, dict) and kw.get('type') == 'keyword':
                                    keywords.append({
                                        'type': 'keyword',
                                        'arg': kw.get('arg', ''),
                                        'value': kw.get('value', {})
                                    })

                            # [关键修复] 递归反编译类体
                            class_body = []
                            if self.recursive and class_body_func:
                                code_value = class_body_func.get('code')
                                # [关键修复] 支持两种code存储格式：直接CodeType或CodeObject字典
                                if isinstance(code_value, types.CodeType):
                                    code_obj = code_value
                                elif isinstance(code_value, dict) and code_value.get('type') == 'CodeObject':
                                    code_obj = code_value.get('code')
                                else:
                                    code_obj = None
                                if code_obj and hasattr(code_obj, 'co_code'):
                                    try:
                                        from .cfg_builder import build_cfg
                                        class_cfg = build_cfg(code_obj, class_name)
                                        class_generator = ASTGeneratorV2(class_cfg, recursive=True)
                                        class_ast = class_generator.generate()
                                        if class_ast and class_ast.get('body'):
                                            class_body = class_ast['body']
                                    except Exception as e:
                                        pass

                            # 如果body为空，添加pass语句
                            if not class_body:
                                class_body = [{'type': 'Pass', 'lineno': instr.starts_line}]

                            statements.append({
                                'type': 'ClassDef',
                                'name': class_name if isinstance(class_name, str) else instr.argval,
                                'bases': bases,
                                'keywords': keywords,
                                'body': class_body,
                                'decorator_list': [],
                                'lineno': instr.starts_line
                            })
                        # [关键修复] 检查是否是增强赋值（AugAssign）
                        elif value.get('type') == 'AugAssign':
                            # 增强赋值：total += item
                            statements.append({
                                'type': 'AugAssign',
                                'target': {
                                    'type': 'Name',
                                    'id': instr.argval,
                                    'ctx': 'Store',
                                    'lineno': instr.starts_line
                                },
                                'op': value.get('op', '+='),
                                'value': value.get('value'),
                                'lineno': instr.starts_line
                            })
                        # [关键修复] 检查是否是导入结果，如果是则跳过赋值
                        elif value.get('type') == 'ImportResult':
                            # 这是导入语句的结果，不需要生成赋值
                            pass
                        # [关键修复] 检查是否是解包赋值模式
                        elif unpack_state is not None:
                            # 正在处理解包赋值，收集目标变量
                            unpack_state['targets'].append({
                                'type': 'Name',
                                'id': instr.argval,
                                'ctx': 'Store',
                                'lineno': instr.starts_line
                            })
                            # 检查是否收集完所有目标
                            if len(unpack_state['targets']) >= unpack_state['count']:
                                # 生成解包赋值语句
                                statements.append({
                                    'type': 'Assign',
                                    'targets': [{
                                        'type': 'Tuple',
                                        'elts': unpack_state['targets'],
                                        'ctx': 'Store',
                                        'lineno': unpack_state['line']
                                    }],
                                    'value': unpack_state['value'],
                                    'lineno': unpack_state['line']
                                })
                                # 重置解包状态
                                unpack_state = None
                                # [关键修复] 同时更新实例变量
                                self._unpack_state = None
                        else:
                            # [关键修复] 检查是否是 BoolOpPending，需要合并为 BoolOp
                            # 这发生在复合条件赋值时，如：result = a and b or c
                            if value.get('type') == 'BoolOpPending':
                                # 右操作数是 BoolOpPending 的 left，需要找到实际的右操作数
                                boolop_pending = value
                                # 在栈中查找实际的右操作数（非 BoolOpPending）
                                right_value = None
                                for i in range(len(stack) - 1, -1, -1):
                                    if stack[i].get('type') != 'BoolOpPending':
                                        right_value = stack.pop(i)
                                        break
                                
                                if right_value:
                                    value = {
                                        'type': 'BoolOp',
                                        'op': boolop_pending['op'],
                                        'values': [boolop_pending['left'], right_value],
                                        'lineno': boolop_pending.get('lineno')
                                    }
                            
                            # 普通赋值
                            # [关键修复] 如果值是FormattedValue，包装为JoinedStr
                            # 这对于简单的f-string如f'{x:.2f}'是必需的
                            if isinstance(value, dict) and value.get('type') == 'FormattedValue':
                                value = {
                                    'type': 'JoinedStr',
                                    'values': [value],
                                    'lineno': value.get('lineno')
                                }
                            statements.append({
                                'type': 'Assign',
                                'targets': [{
                                    'type': 'Name',
                                    'id': instr.argval,
                                    'ctx': 'Store',
                                    'lineno': instr.starts_line
                                }],
                                'value': value,
                                'lineno': instr.starts_line
                            })
                last_was_copy = False
                continue
            
            # [关键修复] STORE_SUBSCR 指令 - 字典/列表赋值，如 attrs['key'] = value
            if opname == 'STORE_SUBSCR':
                if len(stack) >= 3:
                    # [关键修复] STORE_SUBSCR 的栈布局: 值在底部，容器在中间，下标在栈顶
                    # 弹出顺序: 先弹出下标，然后容器，最后值
                    index = stack.pop()      # 栈顶 - 下标
                    container = stack.pop()  # 中间 - 容器
                    value = stack.pop()      # 底部 - 值
                    
                    # [关键修复] 检查是否是增强赋值模式
                    # 增强赋值的特征：value是AugAssign节点，或者value是BinOp且target匹配container[index]
                    is_aug_assign = False
                    if isinstance(value, dict):
                        if value.get('type') == 'AugAssign':
                            is_aug_assign = True
                        elif value.get('type') == 'BinOp':
                            # 检查是否是增强赋值的展开形式
                            # 例如：result['count'] + 1 对应 result['count'] += 1
                            left = value.get('left', {})
                            if (left.get('type') == 'Subscript' and
                                left.get('value', {}).get('id') == container.get('id') and
                                left.get('slice', {}).get('value') == index.get('value')):
                                # 这是增强赋值的展开形式，转换为AugAssign
                                is_aug_assign = True
                                value = {
                                    'type': 'AugAssign',
                                    'target': left,
                                    'op': value.get('op'),
                                    'value': value.get('right'),
                                    'lineno': instr.starts_line
                                }
                    
                    if is_aug_assign and isinstance(value, dict) and value.get('type') == 'AugAssign':
                        # 生成增强赋值语句
                        statements.append(value)
                    else:
                        # 生成普通Subscript赋值语句
                        statements.append({
                            'type': 'Assign',
                            'targets': [{
                                'type': 'Subscript',
                                'value': container,
                                'slice': index,
                                'ctx': 'Store',
                                'lineno': instr.starts_line
                            }],
                            'value': value,
                            'lineno': instr.starts_line
                        })
                last_was_copy = False
                continue
            
            # [海象运算符] 其他指令重置 COPY 标志
            last_was_copy = False
            
            # [关键修复] PRECALL - Python 3.11+ 的预调用指令，不修改栈
            if opname == 'PRECALL':
                continue
            
            # [关键修复] KW_NAMES - Python 3.11+ 的关键字参数名指令
            if opname == 'KW_NAMES':
                # 存储关键字参数名，供后续的 CALL 指令使用
                # instr.arg 是常量表索引，需要从 code.co_consts 中获取关键字参数名元组
                try:
                    if hasattr(self, 'cfg') and self.cfg and hasattr(self.cfg, 'code'):
                        kw_names = self.cfg.code.co_consts[instr.arg]
                        self._kw_names = kw_names
                    else:
                        # 备用方案：尝试使用 argval
                        self._kw_names = instr.argval
                except (IndexError, AttributeError):
                    self._kw_names = instr.argval
                continue

            # [关键修复] IMPORT_NAME - 导入模块
            if opname == 'IMPORT_NAME':
                # 从栈中弹出fromlist（如果存在）
                fromlist = None
                if stack:
                    fromlist_obj = stack.pop()
                    # 处理fromlist，可能是tuple/list/Constant
                    if isinstance(fromlist_obj, dict):
                        if fromlist_obj.get('type') == 'Constant':
                            fromlist = fromlist_obj.get('value')
                        elif fromlist_obj.get('type') == 'Tuple':
                            fromlist = [elt.get('value') for elt in fromlist_obj.get('elts', [])]
                
                # 获取模块名
                module_name = instr.argval
                
                # [关键修复] 对于import语句，不立即创建导入节点
                # 而是压入一个特殊标记，让STORE_NAME处理别名
                if fromlist and len(fromlist) > 0:
                    # from ... import ... 形式
                    # 压入标记，包含模块名和导入名列表
                    stack.append({
                        'type': 'ImportFromPending',
                        'module': module_name,
                        'names': fromlist,
                        'lineno': instr.starts_line
                    })
                else:
                    # import ... 形式
                    # 压入标记，包含模块名
                    stack.append({
                        'type': 'ImportPending',
                        'module': module_name,
                        'lineno': instr.starts_line
                    })
                continue

            # [关键修复] IMPORT_FROM - 从模块导入特定名称
            if opname == 'IMPORT_FROM':
                # [关键修复] 不将导入名压入栈，而是查找并更新ImportFromPending标记
                # 实际的导入处理在STORE_NAME时完成
                imported_name = instr.argval
                
                # 查找栈中的ImportFromPending标记
                for i in range(len(stack) - 1, -1, -1):
                    if isinstance(stack[i], dict) and stack[i].get('type') == 'ImportFromPending':
                        # 更新标记，记录当前正在处理的导入名
                        stack[i]['current_name'] = imported_name
                        break
                
                # 仍然将导入名压入栈，以便非别名导入能正常工作
                stack.append({
                    'type': 'Name',
                    'id': imported_name,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })
                continue

            # 加载常量
            if opname in ('LOAD_CONST', 'LOAD_CONSTANT'):
                # [关键修复] 检查是否是code对象（函数或类定义）
                if isinstance(instr.argval, types.CodeType):
                    # 这是函数或类的code对象，保留原始code对象
                    stack.append({
                        'type': 'CodeObject',
                        'code': instr.argval,
                        'lineno': instr.starts_line
                    })
                else:
                    stack.append({
                        'type': 'Constant',
                        'value': instr.argval,
                        'lineno': instr.starts_line
                    })

            # 加载变量
            elif opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF'):
                stack.append({
                    'type': 'Name',
                    'id': instr.argval,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # [关键修复] 加载类构建器 - LOAD_BUILD_CLASS的argval是None
            elif opname == 'LOAD_BUILD_CLASS':
                stack.append({
                    'type': 'Name',
                    'id': '__build_class__',
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # 二元操作 (Python 3.11+)
            elif opname == 'BINARY_OP':
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    op = self._get_binary_op_from_arg(instr.argval)
                    
                    # [关键修复] 检查是否是增强赋值操作符 (13-25)
                    if instr.arg is not None and instr.arg >= 13:
                        # 增强赋值：+=, -=, *=, 等
                        stack.append({
                            'type': 'AugAssign',
                            'target': left,
                            'op': op,
                            'value': right,
                            'lineno': instr.starts_line
                        })
                    else:
                        # 普通二元操作
                        stack.append({
                            'type': 'BinOp',
                            'left': left,
                            'op': op,
                            'right': right,
                            'lineno': instr.starts_line
                        })

            # 二元操作 (Python 3.8-3.10)
            # [关键修复] 排除 BINARY_SUBSCR，它应该作为下标操作处理
            elif (opname.startswith('BINARY_') and opname != 'BINARY_SUBSCR') or opname.startswith('INPLACE_'):
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    op = self._get_binary_op(opname)
                    stack.append({
                        'type': 'BinOp',
                        'left': left,
                        'op': op,
                        'right': right,
                        'lineno': instr.starts_line
                    })

            # [关键修复] BINARY_SUBSCR - 下标操作
            elif opname == 'BINARY_SUBSCR':
                if len(stack) >= 2:
                    slice_val = stack.pop()
                    value = stack.pop()
                    stack.append({
                        'type': 'Subscript',
                        'value': value,
                        'slice': slice_val,
                        'ctx': 'Load',
                        'lineno': instr.starts_line
                    })

            # [关键修复] BUILD_SLICE - 构建切片对象
            elif opname == 'BUILD_SLICE':
                argc = instr.arg if instr.arg is not None else 0
                if argc == 2 and len(stack) >= 2:
                    # 两个参数: start:stop
                    stop = stack.pop()
                    start = stack.pop()
                    stack.append({
                        'type': 'Slice',
                        'lower': start,
                        'upper': stop,
                        'step': None,
                        'lineno': instr.starts_line
                    })
                elif argc == 3 and len(stack) >= 3:
                    # 三个参数: start:stop:step
                    step = stack.pop()
                    stop = stack.pop()
                    start = stack.pop()
                    stack.append({
                        'type': 'Slice',
                        'lower': start,
                        'upper': stop,
                        'step': step,
                        'lineno': instr.starts_line
                    })

            # 一元操作
            elif opname.startswith('UNARY_'):
                if stack:
                    operand = stack.pop()
                    op = self._get_unary_op(opname)
                    stack.append({
                        'type': 'UnaryOp',
                        'op': op,
                        'operand': operand,
                        'lineno': instr.starts_line
                    })

            # 比较操作
            elif opname == 'COMPARE_OP':
                if len(stack) >= 2:
                    right = stack.pop()
                    left = stack.pop()
                    cmp_op = self._get_compare_op(instr.argval)
                    stack.append({
                        'type': 'Compare',
                        'left': left,
                        'ops': [cmp_op],
                        'comparators': [right],
                        'lineno': instr.starts_line
                    })

            # 函数调用
            elif opname in ('CALL_FUNCTION', 'CALL', 'CALL_METHOD'):
                argc = instr.arg if instr.arg is not None else 0
                args = []
                kwargs = []

                # [关键修复] 检查是否有 KW_NAMES 存储的关键字参数名
                kw_names = getattr(self, '_kw_names', None)
                if kw_names and isinstance(kw_names, tuple):
                    # 有关键字参数，最后 len(kw_names) 个参数是关键字参数
                    kw_arg_count = len(kw_names)
                    pos_arg_count = argc - kw_arg_count

                    # 弹出关键字参数（从后往前）
                    for i in range(kw_arg_count - 1, -1, -1):
                        if stack:
                            value = stack.pop()
                            kwargs.insert(0, {
                                'type': 'keyword',
                                'arg': kw_names[i],
                                'value': value
                            })

                    # 弹出位置参数
                    for _ in range(pos_arg_count):
                        if stack:
                            args.insert(0, stack.pop())

                    # 清除 KW_NAMES
                    self._kw_names = None
                else:
                    # 没有关键字参数，所有参数都是位置参数
                    for _ in range(argc):
                        if stack:
                            args.insert(0, stack.pop())

                # [关键修复] 处理装饰器调用：如果栈顶是FunctionObject，将其作为参数
                if stack and stack[-1].get('type') == 'FunctionObject':
                    # 这是装饰器调用，FunctionObject是参数
                    func_object = stack.pop()  # 弹出FunctionObject作为参数
                    if stack:
                        func = stack.pop()  # 弹出装饰器函数
                        args = [func_object]  # FunctionObject作为参数
                        stack.append({
                            'type': 'Call',
                            'func': func,
                            'args': args,
                            'lineno': instr.starts_line
                        })
                        continue

                # [关键修复] 处理多层装饰器调用：如果栈顶是Call（内层装饰器结果）
                # 且次栈顶是装饰器函数（Name类型）
                if (stack and len(stack) >= 2 and
                    stack[-1].get('type') == 'Call' and
                    stack[-2].get('type') == 'Name' and
                    argc == 0):
                    # 这是装饰器链：栈上应该是 [decorator, inner_call]
                    inner_call = stack.pop()  # 弹出内层Call
                    func = stack.pop()  # 弹出外层装饰器
                    # 创建新的Call，func是外层装饰器，args包含内层Call的结果
                    stack.append({
                        'type': 'Call',
                        'func': func,
                        'args': [inner_call],
                        'lineno': instr.starts_line
                    })
                    continue

                # [关键修复] 检查是否是推导式调用
                # 推导式调用的特点：argc=0且栈中有FunctionObject（推导式函数）
                # Python 3.11+ 的栈布局: [FunctionObject, null, iter_obj] (CALL 0)
                # FunctionObject在栈底（最先压入），iter_obj在栈顶（最后被压入）
                if argc == 0:
                    func_object_idx = None
                    for i in range(len(stack)):
                        if stack[i].get('type') == 'FunctionObject':
                            func_object_idx = i
                            break
                    
                    if func_object_idx is not None:
                        func_object = stack[func_object_idx]
                        code_value = func_object.get('code')
                        
                        # [关键修复] 支持多种code存储格式
                        if isinstance(code_value, types.CodeType):
                            code_obj = code_value
                        elif isinstance(code_value, dict):
                            if code_value.get('type') == 'CodeObject':
                                code_obj = code_value.get('code')
                            elif code_value.get('type') == 'Constant':
                                code_obj = code_value.get('value')
                            else:
                                code_obj = None
                        else:
                            code_obj = None
                        
                        if code_obj and hasattr(code_obj, 'co_name'):
                            comp_name = code_obj.co_name
                            if comp_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'):
                                # [关键修复] 推导式调用的栈布局: [FunctionObject, null, iter_obj]
                                # iter_obj在栈顶，需要从栈顶向下找
                                iter_obj_idx = len(stack) - 1
                                # 跳过null值（在FunctionObject和iter_obj之间）
                                while iter_obj_idx > func_object_idx:
                                    candidate = stack[iter_obj_idx]
                                    if candidate.get('type') == 'Constant' and candidate.get('value') is None:
                                        iter_obj_idx -= 1  # 跳过null
                                    else:
                                        break
                                
                                if iter_obj_idx > func_object_idx:
                                    iter_obj = stack[iter_obj_idx]
                                    # 移除FunctionObject、null（如果有）和iter_obj
                                    new_stack = stack[:func_object_idx] + stack[iter_obj_idx + 1:]
                                    stack.clear()
                                    stack.extend(new_stack)
                                else:
                                    iter_obj = {'type': 'Name', 'id': 'range'}
                                
                                # 递归反编译推导式 code 对象
                                comp_ast = self._decompile_comprehension(code_obj, iter_obj)
                                if comp_ast:
                                    stack.append(comp_ast)
                                    continue
                
                if stack:
                    func = stack.pop()
                    
                    # [关键修复] 如果func是null（来自PUSH_NULL），跳过它
                    # 使用循环跳过所有连续的null值
                    while (func.get('type') == 'Constant' and func.get('value') is None) or \
                          (func.get('type') == 'PUSH_NULL'):
                        if stack:
                            func = stack.pop()
                        else:
                            break
                    
                    # [关键修复] 过滤掉None(None, None)这种内部调用（with语句的__exit__）
                    if (func.get('type') == 'Constant' and func.get('value') is None and
                        len(args) == 2 and
                        all(a.get('type') == 'Constant' and a.get('value') is None for a in args)):
                        # 这是with语句的__exit__调用，跳过
                        continue
                    
                    call_node = {
                        'type': 'Call',
                        'func': func,
                        'args': args,
                        'lineno': instr.starts_line
                    }
                    
                    # [关键修复] 添加关键字参数
                    if kwargs:
                        call_node['kwargs'] = kwargs
                    
                    stack.append(call_node)
            
            # [关键修复] GET_AWAITABLE - Python 3.11+ 的异步等待指令
            elif opname == 'GET_AWAITABLE':
                # GET_AWAITABLE 将栈顶的可等待对象转换为 awaitable
                # 在反编译中，我们需要将其标记为 Await 表达式
                if stack:
                    value = stack.pop()
                    stack.append({
                        'type': 'Await',
                        'value': value,
                        'lineno': instr.starts_line
                    })

            # [关键修复] SEND - Python 3.11+ 的生成器发送指令 (用于 async/await)
            elif opname == 'SEND':
                # SEND 指令用于向生成器发送值，在异步函数中用于 await
                # 通常跟在 GET_AWAITABLE 之后
                # 这里我们不需要特殊处理，因为 GET_AWAITABLE 已经创建了 Await 节点
                pass

            # 加载属性
            elif opname == 'LOAD_ATTR':
                if stack:
                    value = stack.pop()
                    stack.append({
                        'type': 'Attribute',
                        'value': value,
                        'attr': instr.argval,
                        'ctx': 'Load',
                        'lineno': instr.starts_line
                    })

            # [关键修复] 加载方法 (Python 3.11+)
            # LOAD_METHOD 将对象和方法名组合成属性访问
            elif opname == 'LOAD_METHOD':
                if stack:
                    obj = stack.pop()
                    # 将方法加载转换为属性访问
                    stack.append({
                        'type': 'Attribute',
                        'value': obj,
                        'attr': instr.argval,
                        'ctx': 'Load',
                        'lineno': instr.starts_line
                    })

            # [关键修复] 构建字典
            elif opname == 'BUILD_MAP':
                count = instr.arg if instr.arg is not None else 0
                keys = []
                values = []
                for _ in range(count):
                    if len(stack) >= 2:
                        values.insert(0, stack.pop())
                        keys.insert(0, stack.pop())
                stack.append({
                    'type': 'Dict',
                    'keys': keys,
                    'values': values,
                    'lineno': instr.starts_line
                })

            # [关键修复] DICT_MERGE - Python 3.11+ 的字典合并指令（用于**kwargs）
            elif opname == 'DICT_MERGE':
                # DICT_MERGE用于合并字典，通常在CALL_FUNCTION_EX之前使用
                # 栈状态: [dict1, dict2] -> [merged_dict]
                if len(stack) >= 2:
                    dict2 = stack.pop()
                    dict1 = stack.pop()
                    # 创建合并后的字典
                    # 保留两个字典的引用，在代码生成时处理合并
                    merged = {
                        'type': 'DictMerge',
                        'dict1': dict1,
                        'dict2': dict2,
                        'lineno': instr.starts_line
                    }
                    stack.append(merged)

            # [关键修复] CALL_FUNCTION_EX - Python 3.11+ 的扩展函数调用
            elif opname == 'CALL_FUNCTION_EX':
                # 处理 *args 和 **kwargs
                flags = instr.arg if instr.arg is not None else 0
                kwargs_dict = None
                args_obj = None
                
                # 如果设置了 CALL_FUNCTION_EX 标志，先弹出 kwargs
                if flags & 1:
                    if stack:
                        kwargs_dict = stack.pop()
                
                # 弹出 args（可能是元组、Name或其他类型）
                if stack:
                    args_obj = stack.pop()
                
                # 弹出函数对象
                if stack:
                    func = stack.pop()
                    # 跳过 PUSH_NULL
                    while func and func.get('type') == 'PUSH_NULL':
                        if stack:
                            func = stack.pop()
                        else:
                            func = None
                            break
                    
                    if func:
                        # 处理args和kwargs
                        args = []
                        kwargs = []
                        
                        # 处理args_obj
                        if args_obj:
                            if args_obj.get('type') == 'Tuple':
                                args = args_obj.get('elts', [])
                            elif args_obj.get('type') in ('Name', 'Constant'):
                                args = [{'type': 'Starred', 'value': args_obj}]
                        
                        # 处理kwargs_dict
                        if kwargs_dict:
                            if kwargs_dict.get('type') == 'DictMerge':
                                dict2 = kwargs_dict.get('dict2')
                                if dict2 and dict2.get('type') == 'Name':
                                    kwargs = [{'type': 'KeywordStarred', 'value': dict2}]
                            elif kwargs_dict.get('type') == 'Name':
                                kwargs = [{'type': 'KeywordStarred', 'value': kwargs_dict}]
                        
                        call_node = {
                            'type': 'Call',
                            'func': func,
                            'args': args,
                            'lineno': instr.starts_line
                        }
                        if kwargs:
                            call_node['kwargs'] = kwargs
                        
                        stack.append(call_node)

            # [关键修复] 构建常量键字典 (Python 3.11+)
            elif opname == 'BUILD_CONST_KEY_MAP':
                count = instr.arg if instr.arg is not None else 0
                # 最后一个元素是包含所有键的元组
                if stack:
                    keys_tuple = stack.pop()
                    keys = []
                    if keys_tuple.get('type') == 'Constant' and isinstance(keys_tuple.get('value'), (tuple, list)):
                        for key in keys_tuple.get('value'):
                            keys.append({'type': 'Constant', 'value': key})
                    # 弹出值（顺序与键相反）
                    values = []
                    for _ in range(count):
                        if stack:
                            values.insert(0, stack.pop())
                    stack.append({
                        'type': 'Dict',
                        'keys': keys,
                        'values': values,
                        'lineno': instr.starts_line
                    })

            # [关键修复] 构建元组
            elif opname == 'BUILD_TUPLE':
                count = instr.arg if instr.arg is not None else 0
                elts = []
                for _ in range(count):
                    if stack:
                        elts.insert(0, stack.pop())
                stack.append({
                    'type': 'Tuple',
                    'elts': elts,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # [关键修复] 构建列表
            elif opname == 'BUILD_LIST':
                count = instr.arg if instr.arg is not None else 0
                elts = []
                for _ in range(count):
                    if stack:
                        elts.insert(0, stack.pop())
                stack.append({
                    'type': 'List',
                    'elts': elts,
                    'ctx': 'Load',
                    'lineno': instr.starts_line
                })

            # [关键修复] LIST_EXTEND 指令 - Python 3.11+ 的列表扩展
            elif opname == 'LIST_EXTEND':
                if len(stack) >= 2:
                    # 弹出要扩展的可迭代对象
                    iterable = stack.pop()
                    # 弹出列表对象
                    list_obj = stack.pop()
                    # 如果列表是空的，且可迭代对象是元组，直接创建列表
                    if list_obj.get('type') == 'List' and not list_obj.get('elts'):
                        if iterable.get('type') == 'Constant' and isinstance(iterable.get('value'), tuple):
                            stack.append({
                                'type': 'List',
                                'elts': [{'type': 'Constant', 'value': v, 'lineno': instr.starts_line} for v in iterable['value']],
                                'ctx': 'Load',
                                'lineno': instr.starts_line
                            })
                        else:
                            # 对于其他情况，直接返回可迭代对象
                            stack.append(iterable)
                    else:
                        # 列表已有元素，扩展它
                        if iterable.get('type') == 'Constant' and isinstance(iterable.get('value'), tuple):
                            list_obj['elts'].extend([{'type': 'Constant', 'value': v, 'lineno': instr.starts_line} for v in iterable['value']])
                        stack.append(list_obj)

            # [关键修复] 构建集合
            elif opname == 'BUILD_SET':
                count = instr.arg if instr.arg is not None else 0
                elts = []
                for _ in range(count):
                    if stack:
                        elts.insert(0, stack.pop())
                stack.append({
                    'type': 'Set',
                    'elts': elts,
                    'lineno': instr.starts_line
                })

            # [关键修复] SET_UPDATE - Python 3.11+ 的集合更新指令
            elif opname == 'SET_UPDATE':
                # SET_UPDATE用于将可迭代对象的元素添加到集合中
                # 栈状态: [set, iterable] -> [updated_set]
                if len(stack) >= 2:
                    iterable = stack.pop()
                    set_obj = stack.pop()
                    # 将可迭代对象的元素添加到集合中
                    if set_obj and set_obj.get('type') == 'Set':
                        if iterable and iterable.get('type') in ('Tuple', 'List'):
                            # 展开iterable的元素到集合中
                            elts = set_obj.get('elts', [])
                            iterable_elts = iterable.get('elts', [])
                            set_obj['elts'] = elts + iterable_elts
                        elif iterable and iterable.get('type') == 'Constant':
                            # 如果iterable是常量（如frozenset），尝试展开其元素
                            const_val = iterable.get('value')
                            if isinstance(const_val, frozenset):
                                # 将frozenset的元素添加到集合中
                                elts = set_obj.get('elts', [])
                                for item in const_val:
                                    elts.append({
                                        'type': 'Constant',
                                        'value': item,
                                        'lineno': instr.starts_line
                                    })
                                set_obj['elts'] = elts
                        # 将更新后的集合压回栈
                        stack.append(set_obj)
                    else:
                        # 如果set_obj不是Set类型，创建一个包含两者的表达式
                        stack.append({
                            'type': 'BinOp',
                            'op': '|',  # 集合并集
                            'left': set_obj,
                            'right': iterable,
                            'lineno': instr.starts_line
                        })

            # [关键修复] f-string 格式化值
            elif opname == 'FORMAT_VALUE':
                flags = instr.arg if instr.arg is not None else 0
                
                # [关键修复] 处理格式说明符（format spec）
                # flags & 4 表示有格式说明符
                # 栈顺序：[..., value, format_spec]（如果flags & 4）
                format_spec = None
                if flags & 4 and len(stack) >= 2:
                    # 先弹出格式说明符
                    format_spec_node = stack.pop()
                    if format_spec_node.get('type') == 'Constant':
                        # 将格式说明符保持为Constant节点，以便ast_converter正确处理
                        format_spec = format_spec_node
                
                if stack:
                    # 弹出值
                    value = stack.pop()
                    
                    conversion = None
                    if flags == 1:
                        conversion = '!r'
                    elif flags == 2:
                        conversion = '!s'
                    elif flags == 3:
                        conversion = '!a'
                    
                    formatted_value = {
                        'type': 'FormattedValue',
                        'value': value,
                        'conversion': conversion,
                        'format_spec': format_spec,
                        'lineno': instr.starts_line
                    }
                    
                    # [关键修复] 压入FormattedValue，不自动包装为JoinedStr
                    # BUILD_STRING指令会处理多个部分的组合
                    # 对于简单的f-string，在STORE_NAME/STORE_FAST时检查并包装
                    stack.append(formatted_value)

            # [关键修复] 构建 f-string
            elif opname == 'BUILD_STRING':
                count = instr.arg if instr.arg is not None else 0
                parts = []
                for _ in range(count):
                    if stack:
                        part = stack.pop()
                        # [关键修复] 跳过null值（来自PUSH_NULL）
                        if (isinstance(part, dict) and 
                            part.get('type') == 'Constant' and 
                            part.get('value') is None):
                            # 如果栈中还有值，继续弹出
                            if stack:
                                part = stack.pop()
                                parts.insert(0, part)
                        else:
                            parts.insert(0, part)
                stack.append({
                    'type': 'JoinedStr',
                    'values': parts,
                    'lineno': instr.starts_line
                })

            # [关键修复] 创建函数对象
            elif opname == 'MAKE_FUNCTION':
                if stack:
                    # MAKE_FUNCTION flags (Python 3.11+):
                    # 0x01 (1): 有位置参数默认值 (tuple)
                    # 0x02 (2): 有关键字-only参数默认值 (dict)
                    # 0x04 (4): 有注解
                    # 0x08 (8): 有闭包
                    flags = instr.arg if instr.arg is not None else 0
                    
                    # 打印栈顶元素
                    if stack:
                        pass  # print(f"[DEBUG] Stack top: {stack[-1]}")
                    
                    # 弹出code对象 (栈顶)
                    code_value = stack.pop()
                    pass  # print(f"[DEBUG] Popped code_value: {code_value}")
                    
                    # [关键修复] 从CodeObject中提取实际的code对象
                    if isinstance(code_value, dict) and code_value.get('type') == 'CodeObject':
                        actual_code = code_value.get('code')
                    elif isinstance(code_value, types.CodeType):
                        actual_code = code_value
                    else:
                        actual_code = None
                    
                    # [关键修复] 处理默认值和注解 - 注意弹出顺序与压入顺序相反
                    # 栈布局(从底到顶): [位置默认值, 关键字-only默认值, 注解元组, 闭包元组, code]
                    kw_defaults = None  # flags & 2
                    pos_defaults = None  # flags & 1
                    annotations = None  # flags & 4
                    closure = None  # flags & 8
                    
                    # flags & 8: 有闭包，从栈中弹出闭包元组
                    if flags & 8:
                        if stack:
                            closure = stack.pop()
                    
                    # flags & 4: 有注解，从栈中弹出注解元组
                    if flags & 4:
                        if stack:
                            annotations = stack.pop()
                    
                    # flags & 2: 有关键字-only参数默认值，从栈中弹出
                    if flags & 2:
                        if stack:
                            kw_defaults = stack.pop()
                    
                    # flags & 1: 有位置参数默认值，从栈中弹出
                    if flags & 1:
                        if stack:
                            pos_defaults = stack.pop()
                    
                    # 标记这是一个函数对象，包含默认值和注解信息
                    func_obj = {
                        'type': 'FunctionObject',
                        'code': actual_code,
                        'lineno': instr.starts_line
                    }
                    if pos_defaults:
                        func_obj['defaults'] = pos_defaults
                    if kw_defaults:
                        func_obj['kw_defaults'] = kw_defaults
                    if annotations:
                        func_obj['annotations'] = annotations
                    if closure:
                        func_obj['closure'] = closure
                    
                    stack.append(func_obj)

            # [关键修复] Python 3.11+ PRECALL 指令 - 预调用，不执行实际操作
            elif opname == 'PRECALL':
                # PRECALL 只是预调用指令，不改变栈状态
                # 但在某些情况下，PRECALL 后面跟着 CALL，需要确保栈状态正确
                pass

            # [关键修复] Python 3.11+ CALL 指令 - 函数调用
            elif opname == 'CALL':
                argc = instr.arg if instr.arg is not None else 0
                args = []
                kwargs = []
                
                # 从栈中弹出参数
                for _ in range(argc):
                    if stack:
                        args.insert(0, stack.pop())
                
                # 弹出函数对象
                if stack:
                    func = stack.pop()
                    
                    # [关键修复] 处理 PUSH_NULL 标记
                    while func and func.get('type') == 'PUSH_NULL':
                        if stack:
                            func = stack.pop()
                        else:
                            func = None
                            break
                    
                    # [关键修复] 检查是否是推导式调用
                    # 推导式调用的特点：argc=0且func是FunctionObject（推导式函数）
                    if argc == 0 and func and func.get('type') == 'FunctionObject':
                        code_value = func.get('code')
                        
                        # 支持多种code存储格式
                        if isinstance(code_value, types.CodeType):
                            code_obj = code_value
                        elif isinstance(code_value, dict):
                            if code_value.get('type') == 'CodeObject':
                                code_obj = code_value.get('code')
                            elif code_value.get('type') == 'Constant':
                                code_obj = code_value.get('value')
                            else:
                                code_obj = None
                        else:
                            code_obj = None
                        
                        if code_obj and hasattr(code_obj, 'co_name'):
                            comp_name = code_obj.co_name
                            if comp_name in ('<listcomp>', '<setcomp>', '<dictcomp>', '<genexpr>'):
                                # 推导式调用的栈布局: [FunctionObject, null, iter_obj]
                                # iter_obj在栈顶，需要找到它
                                iter_obj = None
                                if stack:
                                    # 栈顶应该是迭代对象
                                    candidate = stack[-1]
                                    # 跳过null值
                                    if candidate.get('type') == 'Constant' and candidate.get('value') is None:
                                        # 弹出null
                                        stack.pop()
                                        # 再次检查栈顶
                                        if stack:
                                            iter_obj = stack.pop()
                                    else:
                                        iter_obj = stack.pop()
                                
                                if not iter_obj:
                                    iter_obj = {'type': 'Name', 'id': 'range', 'ctx': 'Load', 'lineno': instr.starts_line}
                                
                                # 递归反编译推导式 code 对象
                                comp_ast = self._decompile_comprehension(code_obj, iter_obj)
                                if comp_ast:
                                    stack.append(comp_ast)
                                else:
                                    # 推导式反编译失败，回退到普通Call
                                    if func:
                                        stack.append({
                                            'type': 'Call',
                                            'func': func,
                                            'args': args,
                                            'kwargs': kwargs,
                                            'lineno': instr.starts_line
                                        })
                            else:
                                # 不是推导式，创建普通Call
                                if func:
                                    stack.append({
                                        'type': 'Call',
                                        'func': func,
                                        'args': args,
                                        'kwargs': kwargs,
                                        'lineno': instr.starts_line
                                    })
                        else:
                            # 不是FunctionObject，创建普通Call
                            if func:
                                stack.append({
                                    'type': 'Call',
                                    'func': func,
                                    'args': args,
                                    'kwargs': kwargs,
                                    'lineno': instr.starts_line
                                })
                    else:
                        # 不是推导式调用，创建普通Call
                        if func:
                            stack.append({
                                'type': 'Call',
                                'func': func,
                                'args': args,
                                'kwargs': kwargs,
                                'lineno': instr.starts_line
                            })

            # [关键修复] STORE_ATTR - 属性赋值，如 self.name = value
            # 字节码: LOAD value, LOAD obj, STORE_ATTR attr
            # 栈状态: [value, obj] -> 先弹出obj，再弹出value
            elif opname == 'STORE_ATTR':
                if len(stack) >= 2:
                    obj = stack.pop()     # 先弹出对象（self）- 栈顶
                    value = stack.pop()   # 后弹出值（name）- 次栈顶
                    statements.append({
                        'type': 'Assign',
                        'targets': [{
                            'type': 'Attribute',
                            'value': obj,
                            'attr': instr.argval,
                            'ctx': 'Store',
                            'lineno': instr.starts_line
                        }],
                        'value': value,
                        'lineno': instr.starts_line
                    })

            # POP_TOP - 弹出栈顶值
            elif opname == 'POP_TOP':
                if stack:
                    value = stack.pop()
                    # [关键修复] 如果弹出的是函数调用结果或 Await 表达式，生成表达式语句
                    if value and value.get('type') in ('Call', 'Await'):
                        statements.append({
                            'type': 'Expr',
                            'value': value,
                            'lineno': instr.starts_line
                        })

            # Yield指令
            elif opname in ('YIELD_VALUE', 'YIELD'):
                # [关键修复] 检查当前是否在异步函数中
                # 异步函数中的 YIELD_VALUE 是 await 的内部实现，不应该生成 yield 语句
                is_async_func = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_COROUTINE = 128 (0x80), CO_ITERABLE_COROUTINE = 256 (0x100)
                    is_async_func = bool(self.cfg.code.co_flags & 0x80) or bool(self.cfg.code.co_flags & 0x100)
                
                if not is_async_func:
                    if stack:
                        value = stack.pop()
                        statements.append({
                            'type': 'Yield',
                            'value': value,
                            'lineno': instr.starts_line
                        })
                    else:
                        statements.append({
                            'type': 'Yield',
                            'value': None,
                            'lineno': instr.starts_line
                        })

            # RETURN_GENERATOR - Python 3.11+ 生成器返回，忽略
            elif opname == 'RETURN_GENERATOR':
                # 生成器没有实际的返回语句，忽略此指令
                pass
            
            # [关键修复] JUMP_FORWARD - 可能是break或continue
            elif opname == 'JUMP_FORWARD':
                # 检查跳转目标是否在循环外（break）或循环头（continue）
                jump_target = instr.offset + 2 + instr.arg * 2
                
                # [关键修复] 使用self.current_block而不是block
                current_block = self.current_block
                
                # 查找包含当前块的循环
                current_loop = None
                if current_block:
                    for struct in self.structures:
                        if isinstance(struct, LoopStructure):
                            if struct.header_block and hasattr(struct, 'body_blocks'):
                                body_blocks = set(struct.body_blocks) if isinstance(struct.body_blocks, list) else struct.body_blocks
                                # [关键修复] 检查块是否在循环体内，或者是否可以通过前驱链到达循环
                                if (current_block in body_blocks or 
                                    current_block == struct.header_block or
                                    self._is_block_in_loop(current_block, struct)):
                                    current_loop = struct
                                    break
                
                if current_loop:
                    # [关键修复] 获取循环的最大偏移量（循环体的结束）
                    loop_end_offset = 0
                    if current_loop.body_blocks:
                        for b in current_loop.body_blocks:
                            if b.end_offset > loop_end_offset:
                                loop_end_offset = b.end_offset

                    # [关键修复] 对于while循环，使用exit_block作为循环结束的判断依据
                    # 因为break应该跳转到exit_block，而不只是跳出body_blocks
                    if hasattr(current_loop, 'exit_block') and current_loop.exit_block:
                        exit_offset = current_loop.exit_block.start_offset
                        # 使用exit_block和body_blocks结束偏移量的较大值
                        loop_end_offset = max(loop_end_offset, exit_offset)

                    # 检查跳转目标
                    header_offset = current_loop.header_block.start_offset if current_loop.header_block else 0

                    # [关键修复] 如果跳转目标在循环体之后，是break
                    # 如果跳转目标是循环头部，可能是continue
                    if jump_target > loop_end_offset:
                        # break：跳出循环
                        statements.append({
                            'type': 'Break',
                            'lineno': instr.starts_line
                        })
                    elif abs(jump_target - header_offset) < 10:
                        # [关键修复] 可能是continue，但需要进一步检查
                        # 只有当当前块是if body块且只有JUMP_FORWARD一条指令时，才是显式的continue
                        is_explicit_continue = False
                        if current_block:
                            # 检查是否是if body块
                            is_if_body_block = False
                            for struct in self.structures:
                                if isinstance(struct, IfStructure):
                                    if hasattr(struct, 'then_body') and current_block in struct.then_body:
                                        is_if_body_block = True
                                        break
                                    if hasattr(struct, 'else_body') and current_block in struct.else_body:
                                        is_if_body_block = True
                                        break
                            
                            if is_if_body_block:
                                # 检查块中是否只有JUMP_FORWARD一条有效指令
                                block_instrs = current_block.instructions if hasattr(current_block, 'instructions') else []
                                non_control_instr_count = 0
                                for bi in block_instrs:
                                    if bi.opname not in ('RESUME', 'CACHE', 'NOP'):
                                        non_control_instr_count += 1
                                
                                # 如果块中只有JUMP_FORWARD一条指令，才是显式的continue
                                if non_control_instr_count == 1:  # 只有JUMP_FORWARD
                                    is_explicit_continue = True
                        
                        if is_explicit_continue:
                            statements.append({
                                'type': 'Continue',
                                'lineno': instr.starts_line
                            })
            
            # [关键修复] JUMP_BACKWARD - 可能是continue，也可能是for循环的正常迭代
            elif opname == 'JUMP_BACKWARD':
                # [关键修复] 检查当前是否在循环体内
                # 如果在循环体内且有其他有效指令，JUMP_BACKWARD是显式的continue
                # 如果块中只有JUMP_BACKWARD，这是for循环的正常迭代，不生成continue
                current_block = self.current_block
                is_continue = False
                
                if current_block and self._loop_depth > 0:
                    # [关键修复] 检查当前块是否是if语句的then分支或else分支中的块
                    is_if_body_block = False
                    for struct in self.structures:
                        if isinstance(struct, IfStructure):
                            if hasattr(struct, 'then_body') and current_block in struct.then_body:
                                is_if_body_block = True
                                break
                            if hasattr(struct, 'else_body') and current_block in struct.else_body:
                                is_if_body_block = True
                                break
                    
                    # [关键修复] 生成continue的条件：
                    # 1. 只有当块是if body块，且块中只有JUMP_BACKWARD一条指令时，才可能是显式的continue
                    # 2. 但即使满足条件1，如果块在嵌套循环中，也不应该生成continue（那是循环的正常迭代）
                    # 3. 真正的显式continue应该只在非嵌套循环的if body中出现
                    if is_if_body_block:
                        # 检查块中是否只有JUMP_BACKWARD一条有效指令
                        block_instrs = current_block.instructions if hasattr(current_block, 'instructions') else []
                        non_control_instr_count = 0
                        for bi in block_instrs:
                            # 只统计非控制流指令（排除RESUME, CACHE, NOP等）
                            if bi.opname not in ('RESUME', 'CACHE', 'NOP'):
                                non_control_instr_count += 1
                        
                        # [关键修复] 只有当块中只有JUMP_BACKWARD一条指令，且loop_depth==1（只在最外层循环）时，才是显式的continue
                        # 如果loop_depth>1，说明在嵌套循环中，JUMP_BACKWARD是内层循环的正常迭代
                        if non_control_instr_count == 1 and self._loop_depth == 1:  # 只有JUMP_BACKWARD且在最外层循环
                            is_continue = True
                
                # 如果确定是continue，生成continue语句
                if is_continue:
                    statements.append({
                        'type': 'Continue',
                        'lineno': instr.starts_line
                    })

            # 返回指令
            elif opname == 'RETURN_CONST':
                # [关键修复] 检查当前是否在函数内部（模块级别不应该有return）
                is_module_level = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_name'):
                    is_module_level = (self.cfg.code.co_name == '<module>')
                
                # 模块级别的return不应该生成
                if is_module_level:
                    continue
                
                # 检查是否是生成器函数
                is_generator = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_GENERATOR 标志：1 << 5 (32)
                    is_generator = bool(self.cfg.code.co_flags & 32)
                
                # 生成器函数不应该有return语句
                if not is_generator:
                    statements.append({
                        'type': 'Return',
                        'value': {
                            'type': 'Constant',
                            'value': instr.argval,
                            'lineno': instr.starts_line
                        },
                        'lineno': instr.starts_line
                    })

            elif opname == 'RETURN_VALUE':
                # [关键修复] 如果已经生成了return语句，跳过
                if self._has_return_generated:
                    continue
                
                # [关键修复] 检查当前是否在函数内部（模块级别不应该有return）
                is_module_level = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_name'):
                    is_module_level = (self.cfg.code.co_name == '<module>')
                
                # [关键修复] 检查是否是break语句（在循环体内的模块级别return）
                # break语句的特征：在循环体内，返回None（LOAD_CONST None, RETURN_VALUE）
                is_break = False
                if is_module_level and self._loop_depth > 0:
                    # 检查栈顶是否是None（LOAD_CONST None）
                    returns_none = False
                    if len(stack) > 0:
                        top = stack[-1]
                        if top.get('type') == 'Constant' and top.get('value') is None:
                            returns_none = True
                    
                    # 检查是否在if语句内部（break通常在if语句中）
                    in_if_body = False
                    for struct in self.structures:
                        if isinstance(struct, IfStructure):
                            if hasattr(struct, 'then_body') and self.current_block in struct.then_body:
                                in_if_body = True
                                break
                            if hasattr(struct, 'else_body') and self.current_block in struct.else_body:
                                in_if_body = True
                                break
                    
                    # 如果在循环体内且返回None，且不在函数内，则是break
                    if returns_none:
                        is_break = True
                
                # 模块级别的return不应该生成（除非是break语句）
                if is_module_level and not is_break:
                    continue
                
                # [关键修复] 如果是break语句，生成break
                if is_break:
                    statements.append({
                        'type': 'Break',
                        'lineno': instr.starts_line
                    })
                    continue
                
                # 检查是否是生成器函数
                is_generator = False
                if hasattr(self.cfg, 'code') and hasattr(self.cfg.code, 'co_flags'):
                    # CO_GENERATOR 标志：1 << 5 (32)
                    is_generator = bool(self.cfg.code.co_flags & 32)
                
                # 生成器函数不应该有return语句
                if not is_generator:
                    if stack:
                        value = stack.pop()
                        # [关键修复] 如果栈中有 BoolOpPending，需要合并为 BoolOp
                        # 找到 BoolOpPending 和右操作数
                        boolop_pending = None
                        right_value = None
                        
                        if value.get('type') == 'BoolOpPending':
                            boolop_pending = value
                            # 右操作数是栈顶的下一个值
                            if stack:
                                right_value = stack.pop()
                        elif value.get('type') != 'BoolOpPending' and stack:
                            # 弹出的是右操作数，需要找到 BoolOpPending
                            right_value = value
                            # 在栈中查找 BoolOpPending
                            for i in range(len(stack) - 1, -1, -1):
                                if stack[i].get('type') == 'BoolOpPending':
                                    boolop_pending = stack.pop(i)
                                    break
                        
                        if boolop_pending and right_value:
                            value = {
                                'type': 'BoolOp',
                                'op': boolop_pending['op'],
                                'values': [boolop_pending['left'], right_value],
                                'lineno': boolop_pending.get('lineno')
                            }
                        statements.append({
                            'type': 'Return',
                            'value': value,
                            'lineno': instr.starts_line
                        })
                        # [关键修复] 标记已经生成了return语句
                        self._has_return_generated = True
                    else:
                        # [关键修复] 栈为空时，生成 return None
                        statements.append({
                            'type': 'Return',
                            'value': {'type': 'Constant', 'value': None, 'lineno': instr.starts_line},
                            'lineno': instr.starts_line
                        })
                        # [关键修复] 标记已经生成了return语句
                        self._has_return_generated = True

        # [关键修复] 如果栈中有 BoolOpPending，保留所有非 BoolOpPending 的表达式在栈中
        # 这些表达式是逻辑操作的右操作数，不应该被转换为 Expr 语句
        # 注意：BoolOpPending 的合并在 RETURN_VALUE 处理时进行
        has_boolop_pending = any(e.get('type') == 'BoolOpPending' for e in stack)
        
        # 处理栈中剩余的表达式
        i = 0
        while i < len(stack):
            expr = stack[i]
            
            # [关键修复] 跳过不应该作为表达式出现的类型
            if expr.get('type') in ('FunctionObject', 'Constant'):
                stack.pop(i)
                continue
            
            # [关键修复] Raise 和 Reraise 应该作为语句处理，不是表达式
            if expr.get('type') == 'Raise':
                statements.append({
                    'type': 'Raise',
                    'exc': expr.get('exc'),
                    'lineno': expr.get('lineno')
                })
                stack.pop(i)
                continue
            
            if expr.get('type') == 'Reraise':
                statements.append({
                    'type': 'Raise',
                    'exc': None,
                    'lineno': expr.get('lineno')
                })
                stack.pop(i)
                continue
            
            # [关键修复] 跳过简单的常量值（如 'Alice', 25, None 等）
            if expr.get('type') == 'Constant' and expr.get('value') in (None, True, False):
                stack.pop(i)
                continue
            
            # [关键修复] 如果有 BoolOpPending，保留所有表达式在栈中（包括 BoolOpPending 和右操作数）
            if has_boolop_pending:
                # 这些表达式是逻辑操作的一部分，保留在栈中供 RETURN_VALUE 处理
                i += 1
                continue
            
            # [关键修复] 如果是 Await 表达式，保留在栈中供后续的 STORE_FAST 处理
            # 这在异步函数中很重要，await 表达式的值需要赋给变量
            # 但是，如果这是函数的最后一个表达式（后面没有 STORE_FAST），则作为 Expr 语句处理
            if expr.get('type') == 'Await':
                # 检查是否是函数的最后一个表达式
                # 通过检查最后一条指令是否是 RETURN_VALUE 或 RETURN_CONST
                is_last_expr = False
                if instructions:
                    last_instr = instructions[-1]
                    if last_instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        is_last_expr = True
                
                if is_last_expr:
                    # 作为表达式语句处理
                    statements.append({
                        'type': 'Expr',
                        'value': expr,
                        'lineno': instr.starts_line if instr else None
                    })
                    stack.pop(i)
                    continue
                else:
                    # 保留在栈中供后续的 STORE_FAST 处理
                    i += 1
                    continue
            
            # 转换为 Expr 语句并从栈中移除
            statements.append({
                'type': 'Expr',
                'value': expr,
                'lineno': instr.starts_line if instr else None
            })
            stack.pop(i)

        # [关键修复] 保存解包状态到实例变量
        self._unpack_state = unpack_state
        # [关键修复] 将局部变量stack赋值给self.stack，以便其他代码可以访问
        self.stack = stack
        
        return statements

    def _is_block_in_loop(self, block: BasicBlock, loop: LoopStructure) -> bool:
        """
        检查块是否在循环体内（通过前驱链检查）
        
        Args:
            block: 要检查的块
            loop: 循环结构
            
        Returns:
            如果块在循环体内返回True
        """
        if not loop.header_block:
            return False
        
        # 检查块是否可以通过前驱链到达循环头部
        visited = set()
        worklist = [block]
        
        while worklist:
            current = worklist.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            # 如果到达循环头部，说明块在循环体内
            if current == loop.header_block:
                return True
            
            # 继续检查前驱
            for pred in current.predecessors:
                if pred not in visited:
                    worklist.append(pred)
        
        return False
    
    def _extract_condition_v2(self, block: BasicBlock, initial_stack: Optional[List[Dict[str, Any]]] = None, 
                               is_not_condition: bool = False) -> Dict[str, Any]:
        """提取条件表达式（改进版）
        
        Args:
            block: 基本块
            initial_stack: 初始栈状态，用于链式比较的后续条件块
            is_not_condition: 是否是not条件（如not c）
        """
        # 查找条件跳转指令
        jump_idx = -1
        jump_instr = None
        for i, instr in enumerate(block.instructions):
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE',
                # [关键修复] 支持复合条件的短路求值指令
                'JUMP_IF_TRUE_OR_POP', 'JUMP_IF_FALSE_OR_POP',
                # [关键修复] 支持None检查指令
                'POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_FORWARD_IF_NOT_NONE',
                'POP_JUMP_BACKWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'
            ):
                jump_idx = i
                jump_instr = instr
                # 条件在跳转指令之前
                condition_instrs = block.instructions[:i]
                
                # [关键修复] 处理 POP_JUMP_*_IF_NONE / POP_JUMP_*_IF_NOT_NONE 指令
                # 这些指令表示 is None / is not None 比较
                if instr.opname in ('POP_JUMP_FORWARD_IF_NONE', 'POP_JUMP_BACKWARD_IF_NONE',
                                   'POP_JUMP_FORWARD_IF_NOT_NONE', 'POP_JUMP_BACKWARD_IF_NOT_NONE'):
                    # 重建条件表达式（应该是加载变量的指令）
                    expr = self.expr_reconstructor.reconstruct(condition_instrs, initial_stack)
                    if expr:
                        # 构建 is None / is not None 比较
                        # [关键修复] 跳转指令语义与条件相反：
                        # POP_JUMP_*_IF_NOT_NONE 表示 "如果不是None则跳转"，对应 if x is None
                        # POP_JUMP_*_IF_NONE 表示 "如果是None则跳转"，对应 if x is not None
                        is_not_none = 'NOT_NONE' not in instr.opname
                        compare_expr = {
                            'type': 'Compare',
                            'left': expr,
                            'ops': ['is not' if is_not_none else 'is'],
                            'comparators': [{
                                'type': 'Constant',
                                'value': None,
                                'lineno': instr.starts_line
                            }],
                            'lineno': instr.starts_line
                        }
                        return compare_expr
                else:
                    # [关键修复] 传递初始栈状态给reconstruct（用于链式比较）
                    expr = self.expr_reconstructor.reconstruct(condition_instrs, initial_stack=initial_stack)
                    if expr:
                        # [关键修复] 如果是not条件，包装在UnaryOp中
                        if is_not_condition:
                            expr = {
                                'type': 'UnaryOp',
                                'op': 'not',
                                'operand': expr
                            }
                        # [关键修复] 检查表达式是否为常量（如True, False, 0, 100等）
                    # 即使是常量，也应该返回常量值，而不是占位符
                    # 这样可以确保 if True: x = 1 这样的语句能够正确生成if结构
                    return expr
        
        # [关键修复] 如果无法重建条件表达式，或者重建的是常量，返回占位符
        if jump_instr:
            # 检查跳转目标，尝试推断条件
            if hasattr(jump_instr, 'argval') and jump_instr.argval is not None:
                target_offset = jump_instr.argval
                # 返回一个占位符
                placeholder = {
                    'type': 'Name',
                    'id': f'<condition_{target_offset}>',
                    'ctx': 'Load',
                    'lineno': jump_instr.starts_line
                }
                return placeholder
        
        # [关键修复] 如果块中有比较操作，尝试提取比较表达式
        for instr in block.instructions:
            if instr.opname == 'COMPARE_OP':
                # 尝试重建比较表达式
                compare_idx = block.instructions.index(instr)
                compare_instrs = block.instructions[:compare_idx+1]
                expr = self.expr_reconstructor.reconstruct(compare_instrs)
                if expr:
                    return expr

        # [关键修复] 对于没有跳转指令的块，尝试重建所有指令
        # 这可能是复合条件的最后一部分（如 not flag）
        expr = self.expr_reconstructor.reconstruct(block.instructions)
        if expr:
            return expr

        # 默认返回一个占位符而不是True
        return {'type': 'Name', 'id': '<unknown_condition>', 'ctx': 'Load', 'lineno': None}
    
    def _extract_iterator_v2(self, block: BasicBlock) -> Dict[str, Any]:
        """提取迭代器表达式（改进版）"""
        # 查找FOR_ITER指令
        for i, instr in enumerate(block.instructions):
            if instr.opname in ('FOR_ITER', 'FOR_ITER_RANGE'):
                # 迭代器在FOR_ITER指令之前（在同一基本块中）
                iterator_instrs = block.instructions[:i]
                expr = self.expr_reconstructor.reconstruct(iterator_instrs)
                if expr:
                    return expr

                # 如果在当前块中没有找到，尝试在前驱块中查找
                # 前驱块应该包含 GET_ITER 和迭代器表达式
                for pred in block.predecessors:
                    # 查找 GET_ITER 指令
                    for j, pred_instr in enumerate(pred.instructions):
                        if pred_instr.opname == 'GET_ITER':
                            # 迭代器表达式在 GET_ITER 之前
                            iter_instrs = pred.instructions[:j]
                            expr = self.expr_reconstructor.reconstruct(iter_instrs)
                            if expr:
                                return expr

        return {'type': 'Name', 'id': '<iterator>', 'ctx': 'Load', 'lineno': None}

    def _extract_loop_target(self, block: BasicBlock, body_blocks: List[BasicBlock]) -> Dict[str, Any]:
        """提取循环目标变量"""
        # [关键修复] 首先检查是否有 UNPACK_SEQUENCE 指令（表示多个迭代变量，如 for i, item in enumerate(data)）
        unpack_count = 0
        store_vars = []

        # 在当前块中查找 UNPACK_SEQUENCE 和 STORE_FAST 指令
        for i, instr in enumerate(block.instructions):
            if instr.opname == 'UNPACK_SEQUENCE':
                unpack_count = instr.argval  # 解包的数量（如 2 表示两个变量）
                # 收集 UNPACK_SEQUENCE 之后的 STORE_FAST 指令
                for j in range(i + 1, len(block.instructions)):
                    next_instr = block.instructions[j]
                    if next_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                        store_vars.append({
                            'type': 'Name',
                            'id': next_instr.argval,
                            'ctx': 'Store',
                            'lineno': next_instr.starts_line
                        })
                    elif next_instr.opname not in ('NOP', 'CACHE', 'RESUME', 'EXTENDED_ARG'):
                        # 遇到非存储指令，停止收集
                        break
                break

        # 如果找到了多个变量（UNPACK_SEQUENCE），返回元组形式
        if unpack_count > 1 and len(store_vars) >= unpack_count:
            return {
                'type': 'Tuple',
                'elts': store_vars[:unpack_count],
                'ctx': 'Store',
                'lineno': store_vars[0].get('lineno') if store_vars else None
            }

        # [原有逻辑] 首先在当前块（header_block）中查找 STORE 指令
        for instr in block.instructions:
            if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                return {
                    'type': 'Name',
                    'id': instr.argval,
                    'ctx': 'Store',
                    'lineno': instr.starts_line
                }

        # 如果在 header_block 中没有找到，在循环体块中查找
        # [关键修复] 找到 header 之后的第一个包含 STORE_FAST 的块
        # 按块的偏移量排序，只考虑 offset > header.offset 的块
        sorted_body_blocks = sorted([b for b in body_blocks if b != block and b.start_offset > block.start_offset],
                                    key=lambda b: b.start_offset)

        for body_block in sorted_body_blocks:
            # [关键修复] 同样检查 body_block 中的 UNPACK_SEQUENCE
            for i, instr in enumerate(body_block.instructions):
                if instr.opname == 'UNPACK_SEQUENCE':
                    unpack_count = instr.argval
                    store_vars = []
                    for j in range(i + 1, len(body_block.instructions)):
                        next_instr = body_block.instructions[j]
                        if next_instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                            store_vars.append({
                                'type': 'Name',
                                'id': next_instr.argval,
                                'ctx': 'Store',
                                'lineno': next_instr.starts_line
                            })
                        elif next_instr.opname not in ('NOP', 'CACHE', 'RESUME', 'EXTENDED_ARG'):
                            break
                    if unpack_count > 1 and len(store_vars) >= unpack_count:
                        return {
                            'type': 'Tuple',
                            'elts': store_vars[:unpack_count],
                            'ctx': 'Store',
                            'lineno': store_vars[0].get('lineno') if store_vars else None
                        }
                    break

            for instr in body_block.instructions:
                if instr.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL'):
                    return {
                        'type': 'Name',
                        'id': instr.argval,
                        'ctx': 'Store',
                        'lineno': instr.starts_line
                    }
            # [关键修复] 只在第一个符合条件的 body_block 中查找
            break

        return {'type': 'Name', 'id': '<target>', 'ctx': 'Store', 'lineno': None}
    
    def _get_block_line(self, block: BasicBlock) -> Optional[int]:
        """获取基本块的行号"""
        for instr in block.instructions:
            if instr.starts_line:
                return instr.starts_line
        return None

    def _generate_condition_from_block(self, block: BasicBlock) -> Optional[Dict[str, Any]]:
        """
        从基本块生成条件表达式
        
        查找块中的POP_JUMP_IF_*指令，并提取条件表达式
        """
        # 找到条件跳转指令的位置
        jump_index = None
        for i, instr in enumerate(block.instructions):
            if instr.opname in (
                'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'
            ):
                jump_index = i
                break

        if jump_index is not None:
            # 提取条件（从块开头到跳转指令）
            condition_instrs = block.instructions[:jump_index]
            return self.expr_reconstructor.reconstruct(condition_instrs)

        return None

    def _get_unprocessed_blocks(self) -> List[BasicBlock]:
        """获取未处理的基本块"""
        unprocessed = []
        all_blocks = self.cfg.get_blocks_in_order()
        for b in all_blocks:
            if b not in self.generated_blocks:
                # [关键修复] 检查块是否属于TRY_EXCEPT结构（包括清理代码块）
                # 通过检查structured_analyzer的block_to_structure
                is_try_except_block = False
                if hasattr(self.structured_analyzer, 'block_to_structure'):
                    # [关键修复] 使用块ID比较，而不是对象引用
                    block_to_structure_ids = {block.id: struct for block, struct in self.structured_analyzer.block_to_structure.items()}
                    if b.id in block_to_structure_ids:
                        struct = block_to_structure_ids[b.id]
                        if struct.struct_type == ControlStructureType.TRY_EXCEPT:
                            is_try_except_block = True
                
                # [关键修复] 检查块是否属于IfStructure的entry_block、then_body或else_body
                # 这些块应该由IfStructure处理，不应该作为未处理块
                is_if_structure_block = False
                for struct in self.structures:
                    if isinstance(struct, IfStructure):
                        # [关键修复] 使用块ID比较，而不是对象引用
                        entry_block_id = struct.entry_block.id if struct.entry_block else None
                        then_body_ids = {tb.id for tb in struct.then_body}
                        else_body_ids = {eb.id for eb in struct.else_body}
                        if b.id == entry_block_id or b.id in then_body_ids or b.id in else_body_ids:
                            is_if_structure_block = True
                            print(f"[DEBUG] _get_unprocessed_blocks: Block {b.start_offset} is part of IfStructure {struct.entry_block.start_offset}")
                            break
                
                # [关键修复] 检查块是否属于LoopStructure的body_blocks或else_body
                # 这些块应该由LoopStructure处理，不应该作为未处理块
                is_loop_structure_block = False
                for struct in self.structures:
                    if isinstance(struct, LoopStructure):
                        # [关键修复] 使用块ID比较，而不是对象引用
                        if hasattr(struct, 'body_blocks'):
                            body_block_ids = {bb.id for bb in struct.body_blocks}
                            if b.id in body_block_ids:
                                is_loop_structure_block = True
                                break
                        if hasattr(struct, 'else_body'):
                            else_body_ids = {eb.id for eb in struct.else_body}
                            if b.id in else_body_ids:
                                is_loop_structure_block = True
                                break
                
                # [关键修复] 检查块是否属于TryExceptStructure的finally_body或except_handlers
                # 这些块应该由TryExceptStructure处理，不应该作为未处理块
                is_try_finally_block = False
                for struct in self.structures:
                    if isinstance(struct, TryExceptStructure):
                        # [关键修复] 首先检查块是否属于except_handlers
                        # 这些块包含异常处理代码和清理代码，优先级最高
                        if hasattr(struct, 'except_handlers'):
                            for handler_info in struct.except_handlers:
                                if len(handler_info) == 3:
                                    _, _, handler_blocks = handler_info
                                else:
                                    _, handler_blocks = handler_info
                                # [关键修复] 使用块ID比较，而不是对象引用
                                handler_block_ids = {hb.id for hb in handler_blocks}
                                if b.id in handler_block_ids:
                                    is_try_finally_block = True
                                    # [关键修复] 标记为已处理
                                    self.generated_blocks.add(b)
                                    break
                            if is_try_finally_block:
                                break
                        
                        # [关键修复] 然后检查块是否属于finally_body
                        if hasattr(struct, 'finally_body') and struct.finally_body:
                            # [关键修复] 使用块ID比较
                            finally_block_ids = {fb.id for fb in struct.finally_body}
                            if b.id in finally_block_ids:
                                is_try_finally_block = True
                                # [关键修复] 标记为已处理
                                self.generated_blocks.add(b)
                                break
                        
                        # [关键修复] 最后检查块是否是异常处理清理代码块
                        # 这些块包含POP_EXCEPT, RERAISE等指令
                        for instr in b.instructions:
                            if instr.opname in ('POP_EXCEPT', 'RERAISE', 'COPY', 'PUSH_EXC_INFO'):
                                if b not in self.generated_blocks:
                                    is_try_finally_block = True
                                    # [关键修复] 标记为已处理，防止被当作独立代码块处理
                                    self.generated_blocks.add(b)
                                    break
                        if is_try_finally_block:
                            break
                
                # [关键修复] 检查块是否是条件块（包含POP_JUMP_IF_*指令）
                # 这些块应该由IfStructure处理，不应该作为未处理块
                is_condition_block = False
                for instr in b.instructions:
                    if instr.opname in (
                        'POP_JUMP_IF_TRUE', 'POP_JUMP_IF_FALSE',
                        'POP_JUMP_FORWARD_IF_TRUE', 'POP_JUMP_FORWARD_IF_FALSE',
                        'POP_JUMP_BACKWARD_IF_TRUE', 'POP_JUMP_BACKWARD_IF_FALSE'
                    ):
                        is_condition_block = True
                        break
                
                # [关键修复] 检查块是否是WithStructure的后继块
                # 这些块包含with语句的清理代码（如LOAD_CONST None, RETURN_VALUE）
                # 不应该被当作未处理块处理
                is_with_successor_block = False
                for struct in self.structures:
                    if isinstance(struct, WithStructure):
                        if hasattr(struct, 'entry_block') and struct.entry_block:
                            successor_ids = {succ.id for succ in struct.entry_block.successors}
                            if b.id in successor_ids:
                                # [关键修复] 检查块是否是with语句的清理代码块
                                # 清理代码块的特征：
                                # 1. 包含RETURN_VALUE
                                # 2. 只包含清理相关指令（LOAD_CONST, PRECALL, CALL, POP_TOP, NOP, POP_EXCEPT, COPY, RERAISE等）
                                # 3. 不包含用户代码（如LOAD_FAST, LOAD_GLOBAL等）
                                has_meaningful_code = False
                                has_return = False
                                cleanup_opnames = {
                                    'LOAD_CONST', 'PRECALL', 'CALL', 'POP_TOP', 'NOP',
                                    'POP_EXCEPT', 'COPY', 'RERAISE', 'PUSH_EXC_INFO',
                                    'WITH_EXCEPT_START', 'CHECK_EXC_MATCH', 'POP_JUMP_FORWARD_IF_TRUE',
                                    'POP_JUMP_FORWARD_IF_FALSE', 'JUMP_FORWARD', 'JUMP_ABSOLUTE',
                                    'EXTENDED_ARG'
                                }
                                for instr in b.instructions:
                                    if instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                                        has_return = True
                                    elif instr.opname not in cleanup_opnames:
                                        # 包含有意义的代码（如LOAD_FAST, LOAD_GLOBAL等），不是清理代码块
                                        has_meaningful_code = True
                                        break
                                
                                # 只有当块包含RETURN_VALUE且不包含有意义的代码时，才是清理代码块
                                if has_return and not has_meaningful_code:
                                    is_with_successor_block = True
                                    # [关键修复] 标记为已处理
                                    self.generated_blocks.add(b)
                                    break
                
                # [关键修复] 检查块是否是控制流语句（break/continue/return）
                # 这些块应该由循环或if结构处理，不应该作为未处理块
                # [关键修复] 但是包含RETURN_VALUE的函数退出块需要被处理
                is_control_flow_block = False
                is_return_block = False
                for instr in b.instructions:
                    if instr.opname in ('JUMP_FORWARD', 'JUMP_ABSOLUTE', 'JUMP_BACKWARD'):
                        if len(b.instructions) <= 2:
                            is_control_flow_block = True
                            break
                    elif instr.opname in ('RETURN_VALUE', 'RETURN_CONST'):
                        # [关键修复] 标记为return块，但不要排除它
                        is_return_block = True
                        break
                
                # [关键修复] 包含RETURN_VALUE的块（函数退出块）需要被处理
                # 但是如果是WithStructure的后继块，则跳过
                if is_return_block and not is_with_successor_block:
                    unprocessed.append(b)
                elif not is_try_except_block and not is_if_structure_block and not is_loop_structure_block and not is_try_finally_block and not is_condition_block and not is_control_flow_block and not is_with_successor_block:
                    unprocessed.append(b)
        
        return unprocessed

    def _get_binary_op(self, opname: str) -> str:
        """获取二元操作符"""
        op_map = {
            'BINARY_ADD': '+',
            'BINARY_SUBTRACT': '-',
            'BINARY_MULTIPLY': '*',
            'BINARY_DIVIDE': '/',
            'BINARY_TRUE_DIVIDE': '/',
            'BINARY_FLOOR_DIVIDE': '//',
            'BINARY_MODULO': '%',
            'BINARY_POWER': '**',
            'BINARY_LSHIFT': '<<',
            'BINARY_RSHIFT': '>>',
            'BINARY_AND': '&',
            'BINARY_OR': '|',
            'BINARY_XOR': '^',
            'INPLACE_ADD': '+=',
            'INPLACE_SUBTRACT': '-=',
            'INPLACE_MULTIPLY': '*=',
        }
        return op_map.get(opname, '+')

    def _get_binary_op_from_arg(self, arg) -> str:
        """从 BINARY_OP 参数获取操作符 (Python 3.11+)"""
        # [关键修复] 通过实际测试Python 3.11得到的正确映射
        # 基于字节码观察:
        # 13: +=, 15: //=, 18: *=, 19: %=, 23: -=
        op_map = {
            # 普通二元操作 (0-12)
            0: '+',      # NB_ADD
            1: '&',      # NB_AND
            2: '//',     # NB_FLOOR_DIVIDE
            3: '<<',     # NB_LSHIFT
            4: '@',      # NB_MATRIX_MULTIPLY
            5: '*',      # NB_MULTIPLY
            6: '%',      # NB_REMAINDER
            7: '|',      # NB_OR
            8: '**',     # NB_POWER
            9: '>>',     # NB_RSHIFT
            10: '-',     # NB_SUBTRACT
            11: '/',     # NB_TRUE_DIVIDE
            12: '^',     # NB_XOR
            # Inplace 操作 (13-25) - 基于实际字节码观察
            13: '+=',    # 观察确认
            14: '&=',    # 推测
            15: '//=',   # 观察确认
            16: '<<=',   # 推测
            17: '@=',    # 推测
            18: '*=',    # 观察确认
            19: '%=',    # 观察确认
            20: '|=',    # 推测
            21: '**=',   # 推测
            22: '>>=',   # 推测
            23: '-=',    # 观察确认
            24: '/=',    # 推测
            25: '^=',    # 推测
        }

        if isinstance(arg, int):
            return op_map.get(arg, '+')
        elif isinstance(arg, str):
            try:
                num = int(arg.split()[0])
                return op_map.get(num, '+')
            except (ValueError, IndexError):
                pass
        return '+'

    def _get_unary_op(self, opname: str) -> str:
        """获取一元操作符"""
        op_map = {
            'UNARY_POSITIVE': '+',
            'UNARY_NEGATIVE': '-',
            'UNARY_NOT': 'not',
            'UNARY_INVERT': '~',
        }
        return op_map.get(opname, '+')

    def _get_compare_op(self, arg) -> str:
        """获取比较操作符"""
        op_map = {
            0: '<',    # Py_LT
            1: '<=',   # Py_LE
            2: '==',   # Py_EQ
            3: '!=',   # Py_NE
            4: '>',    # Py_GT
            5: '>=',   # Py_GE
            6: 'in',   # Py_IN
            7: 'not in',  # Py_NOT_IN
            8: 'is',   # Py_IS
            9: 'is not',  # Py_IS_NOT
        }
        # 字符串到整数的映射
        str_to_int = {
            '<': 0, '<=': 1, '==': 2, '!=': 3,
            '>': 4, '>=': 5, 'in': 6, 'not in': 7,
            'is': 8, 'is not': 9
        }
        if isinstance(arg, int):
            return op_map.get(arg, '==')
        elif isinstance(arg, str):
            # 首先检查是否是直接的运算符字符串
            if arg in str_to_int:
                return arg
            # 处理字符串形式，如 '4 (>)'
            try:
                num = int(arg.split()[0])
                return op_map.get(num, '==')
            except (ValueError, IndexError):
                pass
        return '=='


def generate_ast_v2(cfg: ControlFlowGraph) -> Dict[str, Any]:
    """便捷函数：从控制流图生成AST（改进版）"""
    generator = ASTGeneratorV2(cfg)
    return generator.generate()
