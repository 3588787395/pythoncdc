#!/usr/bin/env python3
"""
Python 3.11 字节码支持层
支持 Python 3.11 的字节码解析和反编译
"""

import sys
from typing import Dict, List, Optional, Tuple


class Python311Opcodes:
    """Python 3.11 字节码操作码定义"""
    
    def __init__(self):
        self.opcodes = self._build_opcode_table()
        self.python_version = "3.11"
    
    def _build_opcode_table(self) -> Dict[str, int]:
        """构建Python 3.11操作码表"""
        return {
            # 基本操作 (0-99)
            'CACHE': 0,
            'POP_TOP': 1,
            'ROT_TWO': 2,
            'ROT_THREE': 3,
            'DUP_TOP': 4,
            'DUP_TOP_TWO': 5,
            'ROT_FOUR': 6,
            'NOP': 9,
            'UNARY_POSITIVE': 10,
            'UNARY_NEGATIVE': 11,
            'UNARY_NOT': 12,
            'UNARY_INVERT': 13,
            
            # 二元运算 (20-39)
            'BINARY_SUBSCR': 25,
            'BINARY_ADD': 23,
            'BINARY_AND': 14,
            'BINARY_FLOOR_DIVIDE': 26,
            'BINARY_LSHIFT': 25,
            'BINARY_MATRIX_MULTIPLY': 17,
            'BINARY_MODULO': 22,
            'BINARY_MULTIPLY': 20,
            'BINARY_OR': 16,
            'BINARY_POWER': 19,
            'BINARY_RSHIFT': 26,
            'BINARY_SUBTRACT': 24,
            'BINARY_TRUE_DIVIDE': 21,
            'BINARY_XOR': 15,
            'BINARY_OP': 122,  # Python 3.11 新增统一二元运算符
            
            # 比较和控制流 (100-139)
            'GET_LEN': 30,
            'MATCH_MAPPING': 31,
            'MATCH_SEQUENCE': 32,
            'MATCH_KEYS': 33,
            'PUSH_EXC_INFO': 35,
            'CHECK_EXC_MATCH': 36,
            'CHECK_EG_MATCH': 37,
            'WITH_EXCEPT_START': 49,
            'GET_ITER': 77,
            'GET_YIELD_FROM_ITER': 69,
            'PRINT_EXPR': 70,
            'LOAD_BUILD_CLASS': 71,
            'YIELD_FROM': 72,
            'GET_AWAITABLE': 73,
            'LOAD_ASSERTION_ERROR': 74,
            'RETURN_GENERATOR': 75,
            'LIST_TO_TUPLE': 82,
            'RETURN_VALUE': 120,
            'IMPORT_STAR': 99,
            'SETUP_ANNOTATIONS': 85,
            'YIELD_VALUE': 86,
            'ASYNC_GEN_WRAP': 87,
            'PREP_RERAISE_STAR': 88,
            'STORE_NAME': 90,
            'DELETE_NAME': 91,
            'UNPACK_SEQUENCE': 92,
            'FOR_ITER': 93,
            'UNPACK_EX': 94,
            'STORE_ATTR': 95,
            'DELETE_ATTR': 96,
            'STORE_GLOBAL': 97,
            'DELETE_GLOBAL': 98,
            'LOAD_CONST': 100,
            'LOAD_NAME': 101,
            'BUILD_TUPLE': 102,
            'BUILD_LIST': 103,
            'BUILD_SET': 104,
            'BUILD_MAP': 105,
            'LOAD_ATTR': 106,
            'COMPARE_OP': 107,
            'IMPORT_NAME': 108,
            'IMPORT_FROM': 109,
            'JUMP_FORWARD': 110,
            'JUMP_IF_FALSE_OR_POP': 111,
            'JUMP_IF_TRUE_OR_POP': 112,
            'POP_JUMP_IF_FALSE': 113,
            'POP_JUMP_IF_TRUE': 114,
            'LOAD_GLOBAL': 116,
            'IS_OP': 117,
            'CONTAINS_OP': 118,
            'RERAISE': 119,
            'COPY': 120,
            'SWAP': 121,
            'STORE_SUBSCR': 60,
            'DELETE_SUBSCR': 61,
            'RAISE_VARARGS': 130,
            'MAKE_FUNCTION': 132,
            'BUILD_SLICE': 133,
            'LOAD_METHOD': 160,
            'CALL_METHOD': 161,
            'CALL_METHOD_KW': 162,  # Python 3.11 新增带关键字参数调用方法
            'CALL_FUNCTION': 171,
            'CALL_FUNCTION_KW': 142,
            'CALL_FUNCTION_EX': 143,
            'MAKE_CLOSURE': 134,
            'LOAD_DEREF': 135,
            'STORE_DEREF': 136,
            'DELETE_DEREF': 137,
            'JUMP_ABSOLUTE': 113,
            'POP_JUMP_FORWARD_IF_FALSE': 114,
            'POP_JUMP_FORWARD_IF_TRUE': 115,
            'POP_JUMP_BACKWARD_IF_FALSE': 119,
            'POP_JUMP_BACKWARD_IF_TRUE': 120,
            'POP_JUMP_FORWARD_IF_NOT_NONE': 122,
            'POP_JUMP_BACKWARD_IF_NOT_NONE': 123,
            'POP_JUMP_FORWARD_IF_NONE': 124,
            'POP_JUMP_BACKWARD_IF_NONE': 125,
            'SEND': 126,  # Python 3.11 新增
            'BEFORE_WITH': 127,
            'RETURN_CONST': 128,  # Python 3.11 新增
            'IMPORT_STAR': 129,
            'LOAD_SUPER_ATTR': 131,  # Python 3.11 新增
            'LOAD_FAST_CHECK': 138,  # Python 3.11 新增
            'SET_ADD': 139,
            'LIST_APPEND': 140,
            'MAP_ADD': 141,
            
            # Python 3.11 特有的新指令
            'RESUME': 151,  # Python 3.11 新增，用于调试和异常处理
            'PUSH_NULL': 3,   # Python 3.11 新增，用于函数调用
            'PRECALL': 166,   # Python 3.11 新增，用于函数调用前准备
            'KW_NAMES': 167,  # Python 3.11 新增，用于关键字参数
            'INSTRUMENTED_LOAD_NAME': 172,      # 仪器化指令
            'INSTRUMENTED_LOAD_GLOBAL': 173,    # 仪器化指令
            'INSTRUMENTED_LOAD_FAST': 174,      # 仪器化指令
            'INSTRUMENTED_STORE_FAST': 175,     # 仪器化指令
            'INSTRUMENTED_LOAD_CONST': 176,     # 仪器化指令
            'INSTRUMENTED_RETURN_VALUE': 177,   # 仪器化指令
            'INSTRUMENTED_FOR_ITER': 178,       # 仪器化指令
            'INSTRUMENTED_POP_JUMP_IF_FALSE': 179,  # 仪器化指令
            'INSTRUMENTED_RESUME': 180,         # 仪器化指令
        }
    
    def get_opcode(self, opcode_value: int) -> str:
        """根据操作码值获取操作码名称"""
        for name, value in self.opcodes.items():
            if value == opcode_value:
                return name
        return f'UNKNOWN_{opcode_value}'
    
    def has_arg(self, opcode_value: int) -> bool:
        """检查操作码是否有参数"""
        # Python 3.11 中，操作码 >= 90 的通常有参数
        # 但也有一些特殊情况
        special_cases = {
            1, 2, 3, 4, 5, 6, 9, 10, 11, 12, 13,  # 无参数指令
        }
        
        if opcode_value in special_cases:
            return False
        
        # 一般规则：>= 90 有参数
        return opcode_value >= 90


class Python311InstructionAnalyzer:
    """Python 3.11 指令分析器"""
    
    def __init__(self):
        self.opcodes = Python311Opcodes()
        self.instruction_handlers = self._build_instruction_handlers()
    
    def _build_instruction_handlers(self) -> Dict[str, callable]:
        """构建指令处理函数映射"""
        return {
            # 控制流指令
            'RESUME': self._handle_resume,
            'JUMP_FORWARD': self._handle_jump_forward,
            'JUMP_ABSOLUTE': self._handle_jump_absolute,
            'POP_JUMP_IF_FALSE': self._handle_pop_jump_if_false,
            'POP_JUMP_IF_TRUE': self._handle_pop_jump_if_true,
            'FOR_ITER': self._handle_for_iter,
            'RETURN_VALUE': self._handle_return_value,
            'YIELD_VALUE': self._handle_yield_value,
            'YIELD_FROM': self._handle_yield_from,
            
            # 数据加载指令
            'LOAD_CONST': self._handle_load_const,
            'LOAD_NAME': self._handle_load_name,
            'LOAD_GLOBAL': self._handle_load_global,
            'LOAD_FAST': self._handle_load_fast,
            'LOAD_ATTR': self._handle_load_attr,
            'LOAD_METHOD': self._handle_load_method,
            'LOAD_DEREF': self._handle_load_deref,
            'PUSH_NULL': self._handle_push_null,
            
            # 数据存储指令
            'STORE_NAME': self._handle_store_name,
            'STORE_GLOBAL': self._handle_store_global,
            'STORE_FAST': self._handle_store_fast,
            'STORE_ATTR': self._handle_store_attr,
            'STORE_SUBSCR': self._handle_store_subscr,
            
            # 函数调用指令
            'PRECALL': self._handle_precall,
            'CALL_FUNCTION': self._handle_call_function,
            'CALL_METHOD': self._handle_call_method,
            'CALL_METHOD_KW': self._handle_call_method_kw,
            'MAKE_FUNCTION': self._handle_make_function,
            
            # 运算指令
            'BINARY_ADD': self._handle_binary_add,
            'BINARY_SUBTRACT': self._handle_binary_subtract,
            'BINARY_MULTIPLY': self._handle_binary_multiply,
            'BINARY_POWER': self._handle_binary_power,
            'BINARY_OP': self._handle_binary_op,
            
            # 其他指令
            'COMPARE_OP': self._handle_compare_op,
            'BUILD_LIST': self._handle_build_list,
            'BUILD_TUPLE': self._handle_build_tuple,
            'BUILD_MAP': self._handle_build_map,
            'KW_NAMES': self._handle_kw_names,
            'SEND': self._handle_send,
        }
    
    def analyze_bytecode(self, bytecode: bytes, code_obj=None) -> List[Dict]:
        """分析Python 3.11字节码"""
        instructions = []
        i = 0
        while i < len(bytecode):
            if i >= len(bytecode):
                break
                
            opcode = bytecode[i]
            operand = 0
            
            # Python 3.11 使用16位操作码，每个指令占2字节
            if i + 1 < len(bytecode):
                operand = bytecode[i + 1]
            
            opcode_name = self.opcodes.get_opcode(opcode)
            
            # 创建指令分析结果
            instruction = {
                'position': i,
                'opcode': opcode,
                'opcode_name': opcode_name,
                'operand': operand,
                'has_arg': self.opcodes.has_arg(opcode),
                'description': self._get_opcode_description(opcode_name)
            }
            
            # 如果有处理函数，则应用
            if opcode_name in self.instruction_handlers:
                handler = self.instruction_handlers[opcode_name]
                try:
                    handler_result = handler(instruction, code_obj)
                    if handler_result:
                        instruction.update(handler_result)
                except Exception as e:
                    instruction['handler_error'] = str(e)
            
            instructions.append(instruction)
            
            # Python 3.11 中每个指令占2字节
            i += 2
        
        return instructions
    
    def _get_opcode_description(self, opcode_name: str) -> str:
        """获取操作码描述"""
        descriptions = {
            'RESUME': '标记执行点，用于调试和异常处理',
            'PUSH_NULL': '推送NULL值到栈上，用于函数调用',
            'PRECALL': '函数调用前的准备工作',
            'KW_NAMES': '存储关键字参数名',
            'LOAD_CONST': '加载常量值',
            'LOAD_NAME': '加载变量名',
            'STORE_NAME': '存储变量名',
            'CALL_FUNCTION': '调用函数',
            'CALL_METHOD': '调用方法',
            'CALL_METHOD_KW': '带关键字参数调用方法',
            'BINARY_OP': '统一的二元运算符操作',
            'SEND': '用于生成器和协程操作',
            'RETURN_VALUE': '返回函数值',
        }
        return descriptions.get(opcode_name, '未知操作')
    
    # 控制流指令处理器
    def _handle_resume(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理RESUME指令"""
        return {
            'category': 'control_flow',
            'purpose': '标记执行点，用于调试和异常处理',
            'python_version': '3.11+',
            'semantic_meaning': '不直接影响源代码结构，主要用于运行时'
        }
    
    def _handle_push_null(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理PUSH_NULL指令"""
        return {
            'category': 'stack_operation',
            'purpose': '在函数调用前推送NULL值到栈上',
            'python_version': '3.11+',
            'semantic_meaning': '内部栈操作，不影响源代码表示'
        }
    
    def _handle_precall(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理PRECALL指令"""
        return {
            'category': 'function_call',
            'purpose': '函数调用前的准备工作',
            'python_version': '3.11+',
            'arg_count': instruction['operand'],
            'semantic_meaning': '准备函数调用环境'
        }
    
    def _handle_kw_names(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理KW_NAMES指令"""
        if code_obj and instruction['operand'] < len(code_obj.co_consts):
            kw_names_tuple = code_obj.co_consts[instruction['operand']]
            if isinstance(kw_names_tuple, tuple):
                return {
                    'category': 'function_call',
                    'purpose': '存储关键字参数名',
                    'python_version': '3.11+',
                    'keyword_names': list(kw_names_tuple),
                    'semantic_meaning': '标识函数调用中的关键字参数'
                }
        return {
            'category': 'function_call',
            'purpose': '存储关键字参数名',
            'python_version': '3.11+',
            'semantic_meaning': '标识函数调用中的关键字参数'
        }
    
    def _handle_binary_op(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理BINARY_OP指令"""
        binary_ops = [
            '+', '-', '*', '@', '/', '//', '%', '**', '<<', '>>', 
            '&', '^', '|', '==', '!=', '<', '<=', '>', '>=', 'in', 
            'not in', 'is', 'is not', 'BAD'
        ]
        op_index = instruction['operand']
        if op_index < len(binary_ops):
            return {
                'category': 'arithmetic_logic',
                'purpose': '统一的二元运算符操作',
                'python_version': '3.11+',
                'operator': binary_ops[op_index],
                'semantic_meaning': f'执行{binary_ops[op_index]}运算'
            }
        return {
            'category': 'arithmetic_logic',
            'purpose': '统一的二元运算符操作',
            'python_version': '3.11+',
            'operator': 'unknown',
            'semantic_meaning': '执行二元运算'
        }
    
    def _handle_send(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理SEND指令"""
        return {
            'category': 'coroutine_generator',
            'purpose': '生成器和协程操作',
            'python_version': '3.11+',
            'semantic_meaning': '用于生成器.send()或协程操作'
        }
    
    # 数据加载指令处理器
    def _handle_load_const(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理LOAD_CONST指令"""
        if code_obj and instruction['operand'] < len(code_obj.co_consts):
            const_value = code_obj.co_consts[instruction['operand']]
            return {
                'category': 'data_load',
                'purpose': '加载常量值',
                'value': const_value,
                'type': type(const_value).__name__,
                'semantic_meaning': f'加载常量 {repr(const_value)}'
            }
        return {
            'category': 'data_load',
            'purpose': '加载常量值',
            'semantic_meaning': '加载常量'
        }
    
    def _handle_load_name(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理LOAD_NAME指令"""
        if code_obj and instruction['operand'] < len(code_obj.co_names):
            name = code_obj.co_names[instruction['operand']]
            return {
                'category': 'data_load',
                'purpose': '加载变量名',
                'variable_name': name,
                'semantic_meaning': f'加载变量 {name}'
            }
        return {
            'category': 'data_load',
            'purpose': '加载变量名',
            'semantic_meaning': '加载变量'
        }
    
    # 函数调用指令处理器
    def _handle_call_function(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理CALL_FUNCTION指令"""
        return {
            'category': 'function_call',
            'purpose': '调用函数',
            'arg_count': instruction['operand'],
            'semantic_meaning': f'调用函数，传递 {instruction["operand"]} 个参数'
        }
    
    def _handle_call_method(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理CALL_METHOD指令"""
        return {
            'category': 'function_call',
            'purpose': '调用方法',
            'arg_count': instruction['operand'],
            'semantic_meaning': f'调用方法，传递 {instruction["operand"]} 个参数'
        }
    
    def _handle_call_method_kw(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理CALL_METHOD_KW指令"""
        return {
            'category': 'function_call',
            'purpose': '带关键字参数调用方法',
            'python_version': '3.11+',
            'arg_count': instruction['operand'],
            'semantic_meaning': f'带关键字参数调用方法，传递 {instruction["operand"]} 个参数'
        }
    
    # 运算指令处理器
    def _handle_binary_add(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理BINARY_ADD指令"""
        return {
            'category': 'arithmetic_logic',
            'purpose': '执行加法运算',
            'operator': '+',
            'semantic_meaning': '执行加法运算'
        }
    
    def _handle_binary_subtract(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理BINARY_SUBTRACT指令"""
        return {
            'category': 'arithmetic_logic',
            'purpose': '执行减法运算',
            'operator': '-',
            'semantic_meaning': '执行减法运算'
        }
    
    def _handle_binary_multiply(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理BINARY_MULTIPLY指令"""
        return {
            'category': 'arithmetic_logic',
            'purpose': '执行乘法运算',
            'operator': '*',
            'semantic_meaning': '执行乘法运算'
        }
    
    def _handle_binary_power(self, instruction: dict, code_obj) -> Optional[dict]:
        """处理BINARY_POWER指令"""
        return {
            'category': 'arithmetic_logic',
            'purpose': '执行幂运算',
            'operator': '**',
            'semantic_meaning': '执行幂运算'
        }


def get_python311_analyzer():
    """获取Python 3.11分析器实例"""
    return Python311InstructionAnalyzer()


if __name__ == "__main__":
    # 测试代码
    analyzer = get_python311_analyzer()
    print(f"Python 3.11 操作码总数: {len(analyzer.opcodes.opcodes)}")
    print("部分操作码示例:")
    sample_opcodes = ['RESUME', 'PUSH_NULL', 'PRECALL', 'KW_NAMES', 'BINARY_OP', 'SEND', 'CALL_METHOD', 'CALL_METHOD_KW']
    for opcode in sample_opcodes:
        if opcode in analyzer.opcodes.opcodes:
            print(f"  {opcode}: {analyzer.opcodes.opcodes[opcode]}")