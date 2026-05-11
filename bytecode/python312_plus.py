#!/usr/bin/env python3
"""
Python 3.12+ 字节码兼容层
支持 Python 3.12 和 3.13 的字节码解析
"""

import sys
from typing import Dict, List, Optional, Tuple


class Python312Opcodes:
    """Python 3.12 字节码操作码定义"""
    
    def __init__(self):
        self.opcodes = self._build_opcode_table()
        self.python_version = "3.12"
    
    def _build_opcode_table(self) -> Dict[str, int]:
        """构建Python 3.12操作码表"""
        return {
            # 基本操作 (0-99)
            'CACHE': 0,
            'POP_TOP': 1,
            'PUSH_NULL': 2,
            'NOP': 9,
            'UNARY_POSITIVE': 10,
            'UNARY_NEGATIVE': 11,
            'UNARY_NOT': 12,
            'UNARY_INVERT': 15,
            'BINARY_SUBSCR': 25,
            'GET_LEN': 30,
            'MATCH_MAPPING': 31,
            'MATCH_SEQUENCE': 32,
            'MATCH_KEYS': 33,
            'PUSH_EXC_INFO': 35,
            'CHECK_EXC_MATCH': 36,
            'CHECK_EG_MATCH': 37,
            'WITH_EXCEPT_START': 49,
            'GET_AITER': 50,
            'GET_ANEXT': 51,
            'BEFORE_ASYNC_WITH': 52,
            'BEFORE_WITH': 53,
            'END_ASYNC_FOR': 54,
            'STORE_SUBSCR': 60,
            'DELETE_SUBSCR': 61,
            'GET_ITER': 68,
            'GET_YIELD_FROM_ITER': 69,
            'PRINT_EXPR': 70,
            'LOAD_BUILD_CLASS': 71,
            'LOAD_ASSERTION_ERROR': 74,
            'RETURN_GENERATOR': 75,
            'LIST_TO_TUPLE': 82,
            'RETURN_VALUE': 83,
            'IMPORT_STAR': 84,
            'SETUP_ANNOTATIONS': 85,
            'YIELD_VALUE': 86,
            'ASYNC_GEN_WRAP': 87,
            'PREP_RERAISE_STAR': 88,
            'POP_EXCEPT': 89,
            
            # Python 3.12 新增操作码 (90-150)
            'STORE_NAME_A': 90,
            'DELETE_NAME_A': 91,
            'UNPACK_SEQUENCE_A': 92,
            'FOR_ITER_A': 93,
            'UNPACK_EX_A': 94,
            'STORE_ATTR_A': 95,
            'DELETE_ATTR_A': 96,
            'STORE_GLOBAL_A': 97,
            'DELETE_GLOBAL_A': 98,
            'SWAP_A': 99,
            'LOAD_CONST_A': 100,
            'LOAD_NAME_A': 101,
            'BUILD_TUPLE_A': 102,
            'BUILD_LIST_A': 103,
            'BUILD_SET_A': 104,
            'BUILD_MAP_A': 105,
            'LOAD_ATTR_A': 106,
            'COMPARE_OP_A': 107,
            'IMPORT_NAME_A': 108,
            'IMPORT_FROM_A': 109,
            'JUMP_FORWARD_A': 110,
            'JUMP_IF_FALSE_OR_POP_A': 111,
            'JUMP_IF_TRUE_OR_POP_A': 112,
            'POP_JUMP_FORWARD_IF_FALSE_A': 114,
            'POP_JUMP_FORWARD_IF_TRUE_A': 115,
            'LOAD_GLOBAL_A': 116,
            'IS_OP_A': 117,
            'CONTAINS_OP_A': 118,
            'RERAISE_A': 119,
            'COPY_A': 120,
            'BINARY_OP_A': 122,
            'SEND_A': 123,
            'LOAD_FAST_A': 124,
            'STORE_FAST_A': 125,
            'DELETE_FAST_A': 126,
            'POP_JUMP_FORWARD_IF_NOT_NONE_A': 128,
            'POP_JUMP_FORWARD_IF_NONE_A': 129,
            'RAISE_VARARGS_A': 130,
            'GET_AWAITABLE_A': 131,
            'MAKE_FUNCTION_A': 132,
            'BUILD_SLICE_A': 133,
            'JUMP_BACKWARD_NO_INTERRUPT_A': 134,
            'MAKE_CELL_A': 135,
            'LOAD_CLOSURE_A': 136,
            'LOAD_DEREF_A': 137,
            'STORE_DEREF_A': 138,
            'DELETE_DEREF_A': 139,
            
            # Python 3.12 新增的操作码
            'BINARY_SLICE': 24,
            'STORE_SLICE': 62,
            'CALL_FUNCTION_EX': 140,
            'SETUP_FINALLY': 143,
            'SETUP_CLEANUP': 144,
            'POP_BLOCK': 145,
            'END_FINALLY': 146,
            'LOAD_METHOD': 1000,  # 方法调用优化
            'CALL_METHOD': 1001,
        }
    
    def get_opcode(self, opcode_value: int) -> str:
        """根据操作码值获取操作码名称"""
        for name, value in self.opcodes.items():
            if value == opcode_value:
                return name
        return f'UNKNOWN_{opcode_value}'
    
    def has_arg(self, opcode_value: int) -> bool:
        """检查操作码是否有参数"""
        return opcode_value >= 90


class Python313Opcodes(Python312Opcodes):
    """Python 3.13 字节码操作码定义"""
    
    def __init__(self):
        super().__init__()
        self.opcodes.update(self._build_313_opcodes())
        self.python_version = "3.13"
    
    def _build_313_opcodes(self) -> Dict[str, int]:
        """构建Python 3.13操作码表"""
        return {
            # Python 3.13 新增操作码
            'CALL_INTRINSIC_1': 146,
            'CALL_INTRINSIC_2': 147,
            'LOAD_LOCALS': 148,
            'POP_JUMP_BACKWARD_IF_NOT_NONE': 149,
            'POP_JUMP_FORWARD_IF_NOT_NONE': 150,
            'POP_JUMP_BACKWARD_IF_NONE': 151,
            'POP_JUMP_FORWARD_IF_NONE': 152,
            'SETUP_NOT_EXCEPT': 153,
            'JUMP_BACKWARD': 154,
            
            # Python 3.13 移除的操作码 (不再使用)
            # STORE_NAME, LOAD_NAME 等被 _A 版本替代
        }


class PythonVersionDetector:
    """Python版本检测器"""
    
    VERSION_MAP = {
        (3, 12): Python312Opcodes,
        (3, 13): Python313Opcodes,
    }
    
    def __init__(self):
        self._opcode_cache = {}
    
    def detect_from_code_obj(self, code_obj) -> Tuple[str, object]:
        """
        从代码对象检测Python版本
        
        参数:
            code_obj: 代码对象
            
        返回:
            (版本字符串, 操作码表实例)
        """
        version_info = sys.version_info[:2]
        
        if version_info >= (3, 13):
            return "3.13", Python313Opcodes()
        elif version_info >= (3, 12):
            return "3.12", Python312Opcodes()
        else:
            return f"{version_info[0]}.{version_info[1]}", None
    
    def detect_from_bytecode(self, bytecode: bytes) -> Optional[str]:
        """
        从字节码检测Python版本
        
        参数:
            bytecode: 原始字节码
            
        返回:
            版本字符串或None
        """
        if len(bytecode) < 16:
            return None
        
        try:
            if sys.version_info >= (3, 11):
                if hasattr(bytecode, 'co_exceptiontable'):
                    if len(bytecode.co_exceptiontable) > 0:
                        table = bytecode.co_exceptiontable
                        if len(table) % 8 == 0:
                            return "3.11+"
                        elif len(table) % 4 == 0:
                            return "3.12+"
        except Exception:
            pass
        
        return None
    
    def get_opcodes(self, version: str) -> Optional[object]:
        """
        获取指定版本的操作码表
        
        参数:
            version: 版本字符串 (如 "3.12", "3.13")
            
        返回:
            操作码表实例
        """
        if version in self._opcode_cache:
            return self._opcode_cache[version]
        
        major, minor = int(version.split('.')[0]), int(version.split('.')[1])
        
        if (major, minor) in self.VERSION_MAP:
            opcodes = self.VERSION_MAP[(major, minor)]()
            self._opcode_cache[version] = opcodes
            return opcodes
        
        return None


def get_python_version() -> Tuple[int, int]:
    """获取当前Python版本"""
    return sys.version_info[:2]


def is_python_312_or_higher() -> bool:
    """检查是否Python 3.12或更高版本"""
    return sys.version_info >= (3, 12)


def is_python_313_or_higher() -> bool:
    """检查是否Python 3.13或更高版本"""
    return sys.version_info >= (3, 13)


if __name__ == "__main__":
    print("Python版本检测测试")
    print(f"当前版本: {sys.version}")
    
    detector = PythonVersionDetector()
    version, opcodes = detector.detect_from_code_obj(None)
    print(f"检测版本: {version}")
    
    if opcodes:
        print(f"操作码数量: {len(opcodes.opcodes)}")
        print(f"Python版本: {opcodes.python_version}")
