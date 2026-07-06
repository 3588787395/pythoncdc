#!/usr/bin/env python3
"""
字节码模块初始化
提供统一的字节码分析入口
"""

from bytecode.bytecode_ops import opcode_to_name, Opcode
from bytecode.unified_analyzer import (
    UnifiedBytecodeAnalyzer,
    Instruction,
    create_analyzer
)

# 简化的xdis支持实现
class XdisBytecodeAnalyzer:
    """简化的xdis分析器"""
    def __init__(self):
        self.xdis_available = False
    
    def analyze(self, code_obj):
        return {'error': 'xdis not available', 'source': 'xdis'}

class XdisInstruction:
    """简化的xdis指令"""
    def __init__(self, offset, opcode, opname, arg=None):
        self.offset = offset
        self.opcode = opcode
        self.opname = opname
        self.arg = arg

def check_xdis_available():
    """检查xdis是否可用"""
    return False

def get_supported_versions():
    """获取支持的版本"""
    return []

def create_xdis_analyzer():
    """创建xdis分析器"""
    return XdisBytecodeAnalyzer()

def get_xdis_status():
    """获取xdis状态"""
    return {'available': False, 'version': None}

# 简化的性能模块实现
class BytecodeParser:
    """简化的字节码解析器"""
    def __init__(self):
        pass
    
    def parse(self, code_obj):
        return []

class OptimizedBytecodeAnalyzer:
    """简化的优化分析器"""
    def __init__(self):
        pass
    
    def analyze(self, code_obj):
        return {}

__all__ = [
    # 字节码操作码
    'Opcode',
    'opcode_to_name',
    
    # 统一分析器
    'UnifiedBytecodeAnalyzer',
    'Instruction',
    'create_analyzer',
    
    # xdis支持
    'XdisBytecodeAnalyzer',
    'XdisInstruction',
    'check_xdis_available',
    'get_supported_versions',
    'create_xdis_analyzer',
    'get_xdis_status',
    
    # 性能优化
    'BytecodeParser',
    'OptimizedBytecodeAnalyzer',
]

__version__ = "1.0.0"