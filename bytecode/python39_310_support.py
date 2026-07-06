#!/usr/bin/env python3
"""
Python 3.9/3.10 字节码兼容层
支持 Python 3.9 和 3.10 的字节码解析
"""

import sys
from typing import Dict, List, Optional, Tuple


class Python39Opcodes:
    """Python 3.9 字节码操作码定义"""
    
    def __init__(self):
        self.opcodes = self._build_opcode_table()
        self.python_version = "3.9"
    
    def _build_opcode_table(self) -> Dict[str, int]:
        """构建Python 3.9操作码表"""
        return {
            # 基本操作 (0-99)
            'POP_TOP': 1,
            'ROT_TWO': 2,
            'ROT_THREE': 3,
            'DUP_TOP': 4,
            'DUP_TOP_TWO': 5,
            'NOP': 9,
            'UNARY_POSITIVE': 10,
            'UNARY_NEGATIVE': 11,
            'UNARY_NOT': 12,
            'UNARY_INVERT': 15,
            'BINARY_MATRIX_MULTIPLY': 16,
            'INPLACE_MATRIX_MULTIPLY': 17,
            'BINARY_POWER': 19,
            'BINARY_MULTIPLY': 20,
            'BINARY_MODULO': 22,
            'BINARY_ADD': 23,
            'BINARY_SUBTRACT': 24,
            'BINARY_SUBSCR': 25,
            'BINARY_FLOOR_DIVIDE': 26,
            'BINARY_TRUE_DIVIDE': 27,
            'INPLACE_FLOOR_DIVIDE': 28,
            'INPLACE_TRUE_DIVIDE': 29,
            'GET_LEN': 30,
            'MATCH_MAPPING': 31,
            'MATCH_SEQUENCE': 32,
            'MATCH_KEYS': 33,
            'PUSH_EXC_INFO': 35,
            'CHECK_EXC_MATCH': 36,
            'CHECK_EG_MATCH': 37,
            'WITH_EXCEPT_START': 49,
            'GET_ITER': 68,
            'GET_YIELD_FROM_ITER': 69,
            'LOAD_BUILD_CLASS': 71,
            'LOAD_ASSERTION_ERROR': 74,
            'RETURN_GENERATOR': 75,
            'LIST_TO_TUPLE': 82,
            'IS_OP': 87,
            'CONTAINS_OP': 88,
            'CHECK_IMPORT_STARRED': 90,
            'JUMP_FORWARD': 110,
            'POP_JUMP_IF_TRUE': 114,
            'POP_JUMP_IF_FALSE': 115,
            'POP_JUMP_IF_NONE': 116,
            'POP_JUMP_IF_NOT_NONE': 117,
            'LOAD_GLOBAL': 116,
            'IS_OP': 87,
            'CONTAINS_OP': 88,
            
            # 加载和存储操作 (100-199)
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
            'JUMP_IF_TRUE_OR_POP': 112,
            'JUMP_IF_FALSE_OR_POP': 113,
            'POP_JUMP_IF_TRUE': 114,
            'POP_JUMP_IF_FALSE': 115,
            'LOAD_GLOBAL': 116,
            'IS_OP': 87,
            'CONTAINS_OP': 88,
            'DICT_MERGE': 95,
            'MAP_ADD': 96,
            'CALL_FUNCTION_EX': 94,
            'KW_NAMES': 96,
            'CALL_FUNCTION_KW': 142,
            'CALL_FUNCTION_EX': 94,
            'LOAD_METHOD': 160,
            'CALL_METHOD': 161,
            'LOAD_ASSERTION_ERROR': 74,
            
            # 函数操作 (200-299)
            'MAKE_FUNCTION': 132,
            'BUILD_SLICE': 133,
            'LOAD_CLOSURE': 136,
            'LOAD_DEREF': 137,
            'STORE_DEREF': 138,
            'DELETE_DEREF': 139,
            'MAKE_CLOSURE': 140,
            'BUILD_CONST_KEY_MAP': 151,
            'LOAD_CLOSURE': 136,
            'BUILD_STRING': 152,
            'BUILD_TUPLE_UNPACK': 153,
            'BUILD_TUPLE_UNPACK_WITH_CALL': 154,
            'BUILD_LIST_UNPACK': 155,
            'BUILD_MAP_UNPACK': 156,
            'BUILD_MAP_UNPACK_WITH_CALL': 157,
            'BUILD_SET_UNPACK': 157,
            'BUILD_SET_UNPACK_WITH_CALL': 158,
            'SETUP_ASYNC_WITH': 166,
            'SETUP_FINALLY': 122,
            'SETUP_EXCEPT': 121,
            'POP_BLOCK': 87,
            'POP_EXCEPT': 89,
            'RERAISE': 119,
            'SWAP': 91,
            'SETUP_WITH': 143,
            'RESUME': 122,
            
            # 异常处理
            'SETUP_FINALLY': 122,
            'SETUP_EXCEPT': 121,
            'POP_BLOCK': 87,
            'POP_EXCEPT': 89,
            'RERAISE': 119,
            'END_FINALLY': 88,
            'POP_EXCEPT': 89,
            
            # 异步操作
            'SETUP_ASYNC_WITH': 166,
            'GET_AITER': 50,
            'GET_ANEXT': 51,
            'BEFORE_ASYNC_WITH': 52,
            'END_ASYNC_FOR': 54,
            
            # 特殊操作
            'JUMP_IF_NOT_EXC_MATCH': 122,
            'ROT_N': 94,
            'COPY_DICT_ITEMS': 95,
            'BUILD_STRING': 152,
            'LIST_EXTEND': 102,
            'SET_UPDATE': 103,
            'DICT_MERGE': 95,
            'MAP_ADD': 96,
        }


class Python310Opcodes:
    """Python 3.10 字节码操作码定义"""
    
    def __init__(self):
        self.opcodes = self._build_opcode_table()
        self.python_version = "3.10"
    
    def _build_opcode_table(self) -> Dict[str, int]:
        """构建Python 3.10操作码表"""
        python39_table = Python39Opcodes().opcodes
        
        # 基于Python 3.9，添加3.10特有的操作码
        python310_additions = {
            # 新增操作码
            'COLLECT_GENERATOR_STACK': 173,
            'END_ASYNC_FOR': 54,
            'LIST_APPEND': 145,
            'SET_ADD': 146,
            'MAP_ADD': 146,
            'IS_OP': 87,
            'CONTAINS_OP': 88,
            'JUMP_IF_NOT_EXC_MATCH': 122,
            'CHECK_IMPORT_STARRED': 90,
            'POP_JUMP_IF_NOT_NONE': 116,
            'POP_JUMP_IF_NONE': 117,
            'LOAD_GLOBAL': 116,
            
            # 优化的操作码
            'RESUME': 122,
            'LOAD_CLOSURE': 136,
            'LOAD_DEREF': 137,
            'STORE_DEREF': 138,
            'DELETE_DEREF': 139,
            'MAKE_CLOSURE': 140,
            'BUILD_CONST_KEY_MAP': 151,
            'BUILD_STRING': 152,
            'BUILD_TUPLE_UNPACK': 153,
            'BUILD_TUPLE_UNPACK_WITH_CALL': 154,
            'BUILD_LIST_UNPACK': 155,
            'BUILD_MAP_UNPACK': 156,
            'BUILD_MAP_UNPACK_WITH_CALL': 157,
            'BUILD_SET_UNPACK': 157,
            'BUILD_SET_UNPACK_WITH_CALL': 158,
            'SETUP_ASYNC_WITH': 166,
        }
        
        # 合并表格
        result = python39_table.copy()
        result.update(python310_additions)
        
        return result


class VersionCompatibilityManager:
    """版本兼容性管理器"""
    
    def __init__(self):
        self.supported_versions = {
            (3, 9): Python39Opcodes(),
            (3, 10): Python310Opcodes(),
            (3, 11): None,  # 使用xdis
            (3, 12): None,  # 使用python312_plus.py
        }
    
    def get_opcode_handler(self, version: Tuple[int, int]):
        """获取对应版本的字节码处理器"""
        if version in self.supported_versions:
            return self.supported_versions[version]
        else:
            # 回退到系统版本或最接近版本
            major, minor = version
            if minor > 10:
                # 对于3.11+，使用系统版本
                return None
            else:
                # 对于3.9以下，回退到3.9
                return Python39Opcodes()
    
    def is_version_supported(self, version: Tuple[int, int]) -> bool:
        """检查版本是否支持"""
        return version in self.supported_versions
    
    def get_version_info(self) -> Dict[str, str]:
        """获取支持的版本信息"""
        info = {}
        for version, handler in self.supported_versions.items():
            if handler:
                info[f"{version[0]}.{version[1]}"] = handler.python_version
            else:
                info[f"{version[0]}.{version[1]}"] = "system"
        return info


def get_python39_310_support():
    """获取Python 3.9/3.10支持"""
    return VersionCompatibilityManager()


if __name__ == "__main__":
    # 测试版本支持
    manager = get_python39_310_support()
    
    print("Python 3.9/3.10 字节码支持测试")
    print("=" * 40)
    
    # 测试版本信息
    version_info = manager.get_version_info()
    print("支持的版本:")
    for version, desc in version_info.items():
        print(f"  Python {version}: {desc}")
    print()
    
    # 测试操作码获取
    for version_tuple in [(3, 9), (3, 10)]:
        if manager.is_version_supported(version_tuple):
            handler = manager.get_opcode_handler(version_tuple)
            if handler:
                print(f"Python {version_tuple[0]}.{version_tuple[1]} 操作码数量: {len(handler.opcodes)}")
                
                # 测试一些关键操作码
                test_opcodes = ['LOAD_CONST', 'LOAD_GLOBAL', 'CALL_FUNCTION', 'RETURN_VALUE', 'POP_TOP']
                for opcode_name in test_opcodes:
                    if opcode_name in handler.opcodes:
                        print(f"  {opcode_name}: {handler.opcodes[opcode_name]}")
            print()