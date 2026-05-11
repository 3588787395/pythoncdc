#!/usr/bin/env python3
"""
统一字节码分析器
整合所有字节码分析功能到统一框架
"""

import sys
import os
import time
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass

from bytecode.bytecode_ops import opcode_to_name

# 性能模块已删除，使用简单实现替代
class CacheManager:
    """简单的缓存管理器"""
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        return self.cache.get(key)
    
    def set(self, key, value):
        self.cache[key] = value

class PerformanceMonitor:
    """简单的性能监控器"""
    def __init__(self):
        self.stats = {}
    
    def start_timer(self, name):
        self.stats[name] = {'start': time.time()}
    
    def stop_timer(self, name):
        if name in self.stats:
            self.stats[name]['end'] = time.time()
    
    def get_duration(self, name):
        if name in self.stats and 'end' in self.stats[name]:
            return self.stats[name]['end'] - self.stats[name]['start']
        return 0
    
    def measure(self, name):
        """性能测量装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                self.start_timer(name)
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    self.stop_timer(name)
            return wrapper
        return decorator


@dataclass
class Instruction:
    """指令数据类"""
    offset: int
    opcode: int
    opname: str
    arg: int = 0
    argval: Any = None
    
    def __repr__(self) -> str:
        return f"<Instruction {self.opname} at offset {self.offset}>"


class UnifiedBytecodeAnalyzer:
    """
    统一字节码分析器
    
    整合以下功能：
    - 字节码操作码定义
    - xdis库集成
    - 性能优化
    - 多版本支持
    """
    
    def __init__(self, python_version: Optional[Tuple[int, int]] = None, use_cache: bool = True):
        """
        初始化统一字节码分析器
        
        Args:
            python_version: Python版本，如(3, 11)
            use_cache: 是否使用缓存
        """
        self.python_version = python_version or sys.version_info[:2]
        self._cache = CacheManager() if use_cache else None
        self._monitor = PerformanceMonitor()
        self._xdis_available = self._check_xdis()
    
    def _check_xdis(self) -> bool:
        """检查xdis是否可用"""
        try:
            import xdis
            self._xdis_module = xdis
            return True
        except ImportError:
            self._xdis_module = None
            return False
    
    def analyze_code_object(self, code_obj) -> Dict[str, Any]:
        """
        分析代码对象
        
        Args:
            code_obj: Python代码对象
            
        Returns:
            分析结果字典
        """
        if self._xdis_available:
            return self._analyze_with_xdis(code_obj)
        else:
            return self._analyze_native(code_obj)
    
    @PerformanceMonitor().measure("xdis_analysis")
    def _analyze_with_xdis(self, code_obj) -> Dict[str, Any]:
        """使用xdis分析代码对象"""
        from xdis import Bytecode
        from xdis.version_info import version_tuple_to_str
        
        try:
            from xdis.opcodes import opcode_311, opcode_310, opcode_39, opcode_38, opcode_37
            
            if self.python_version >= (3, 13):
                from xdis.opcodes import opcode_313
                opc = opcode_313
            elif self.python_version >= (3, 12):
                from xdis.opcodes import opcode_312
                opc = opcode_312
            elif self.python_version >= (3, 11):
                opc = opcode_311
            elif self.python_version >= (3, 10):
                opc = opcode_310
            elif self.python_version >= (3, 9):
                opc = opcode_39
            elif self.python_version >= (3, 8):
                opc = opcode_38
            else:
                opc = opcode_37
            
            bytecode = Bytecode(code_obj, opc)
            instructions = list(bytecode)
            
            return {
                'source': 'xdis',
                'python_version': version_tuple_to_str(self.python_version),
                'argcount': code_obj.co_argcount,
                'nlocals': code_obj.co_nlocals,
                'stacksize': code_obj.co_stacksize,
                'flags': code_obj.co_flags,
                'bytecode_size': len(code_obj.co_code),
                'instruction_count': len(instructions),
                'const_count': len(code_obj.co_consts),
                'name_count': len(code_obj.co_names),
                'instructions': [self._inst_to_dict(inst) for inst in instructions]
            }
            
        except Exception as e:
            return {'error': str(e), 'source': 'xdis'}
    
    def _inst_to_dict(self, inst) -> Dict[str, Any]:
        """将指令转换为字典"""
        return {
            'offset': inst.offset,
            'opcode': inst.opcode,
            'opname': inst.opname,
            'arg': getattr(inst, 'arg', 0),
            'argval': str(getattr(inst, 'argval', None))
        }
    
    @PerformanceMonitor().measure("native_analysis")
    def _analyze_native(self, code_obj) -> Dict[str, Any]:
        """使用原生方法分析代码对象"""
        bytecode = code_obj.co_code
        instructions = []
        
        i = 0
        while i < len(bytecode):
            opcode = bytecode[i]
            
            if opcode >= 90 and i + 2 < len(bytecode):
                arg = bytecode[i + 1] | (bytecode[i + 2] << 8)
                size = 3
            else:
                arg = 0
                size = 1
            
            opname = opcode_to_name(opcode)
            
            instructions.append(Instruction(
                offset=i,
                opcode=opcode,
                opname=opname,
                arg=arg
            ))
            
            i += size
        
        return {
            'source': 'native',
            'python_version': f"{self.python_version[0]}.{self.python_version[1]}",
            'argcount': code_obj.co_argcount,
            'nlocals': code_obj.co_nlocals,
            'stacksize': code_obj.co_stacksize,
            'flags': code_obj.co_flags,
            'bytecode_size': len(bytecode),
            'instruction_count': len(instructions),
            'const_count': len(code_obj.co_consts),
            'name_count': len(code_obj.co_names),
            'instructions': [
                {
                    'offset': inst.offset,
                    'opcode': inst.opcode,
                    'opname': inst.opname,
                    'arg': inst.arg
                }
                for inst in instructions
            ]
        }
    
    def get_instructions(self, code_obj) -> List[Instruction]:
        """
        获取代码对象的指令列表
        
        Args:
            code_obj: Python代码对象
            
        Returns:
            Instruction列表
        """
        if self._xdis_available:
            from xdis import Bytecode
            from xdis.opcodes import opcode_311
            
            bytecode = Bytecode(code_obj, opcode_311)
            return [
                Instruction(
                    offset=inst.offset,
                    opcode=inst.opcode,
                    opname=inst.opname,
                    arg=getattr(inst, 'arg', 0),
                    argval=getattr(inst, 'argval', None)
                )
                for inst in bytecode
            ]
        else:
            bytecode = code_obj.co_code
            instructions = []
            i = 0
            while i < len(bytecode):
                opcode = bytecode[i]
                if opcode >= 90 and i + 2 < len(bytecode):
                    arg = bytecode[i + 1] | (bytecode[i + 2] << 8)
                    size = 3
                else:
                    arg = 0
                    size = 1
                
                opname = opcode_to_name(opcode)
                instructions.append(Instruction(
                    offset=i,
                    opcode=opcode,
                    opname=opname,
                    arg=arg
                ))
                i += size
            
            return instructions
    
    def get_summary(self, code_obj) -> str:
        """
        获取代码对象的摘要信息
        
        Args:
            code_obj: Python代码对象
            
        Returns:
            格式化的摘要信息
        """
        result = self.analyze_code_object(code_obj)
        
        if 'error' in result:
            return f"Error: {result['error']}"
        
        lines = [
            f"Python版本: {result['python_version']}",
            f"数据来源: {result['source']}",
            f"参数数量: {result['argcount']}",
            f"局部变量数: {result['nlocals']}",
            f"栈大小: {result['stacksize']}",
            f"字节码大小: {result['bytecode_size']} 字节",
            f"指令数量: {result['instruction_count']}",
            f"常量数量: {result['const_count']}",
            f"名称数量: {result['name_count']}",
        ]
        
        return '\n'.join(lines)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return self._monitor.get_stats()


def create_analyzer(python_version: Tuple[int, int] = None, use_cache: bool = True) -> UnifiedBytecodeAnalyzer:
    """
    创建统一字节码分析器
    
    Args:
        python_version: Python版本
        use_cache: 是否使用缓存
        
    Returns:
        UnifiedBytecodeAnalyzer实例
    """
    return UnifiedBytecodeAnalyzer(python_version, use_cache)


if __name__ == "__main__":
    print("统一字节码分析器测试")
    print("=" * 50)
    print(f"Python版本: {sys.version}")
    print()
    
    def sample_function():
        x = 10
        y = 20
        if x > y:
            return x
        else:
            return y
    
    code_obj = sample_function.__code__
    analyzer = create_analyzer()
    
    print("分析结果:")
    print(analyzer.get_summary(code_obj))
    
    print("\n指令列表 (前5条):")
    for inst in analyzer.get_instructions(code_obj)[:5]:
        print(f"  {inst}")
    
    print("\n性能统计:")
    analyzer._monitor.print_stats()
