#!/usr/bin/env python3
"""
模式注册表 - 统一管理所有反编译模式

用于注册、查找和管理各种 Python 字节码模式
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

class PatternType(Enum):
    """模式类型枚举"""
    CONTROL_FLOW = "control_flow"      # 控制流模式
    EXPRESSION = "expression"          # 表达式模式
    FUNCTION_CLASS = "function_class"  # 函数与类模式
    OTHER = "other"                    # 其他模式

class PatternPriority(Enum):
    """模式优先级枚举"""
    HIGH = 1      # 高优先级（先匹配）
    NORMAL = 2    # 普通优先级
    LOW = 3       # 低优先级（后匹配）

@dataclass
class Pattern:
    """模式数据类"""
    name: str                           # 模式名称
    pattern_type: PatternType           # 模式类型
    priority: PatternPriority           # 模式优先级
    description: str                    # 模式描述
    doc_file: str                       # 文档文件路径
    
    # 识别参数
    key_opcodes: List[int]              # 关键操作码
    required_context: List[str]         # 必需的上下文参数
    
    # 处理函数
    identify_func: Callable             # 识别函数
    create_node_func: Callable          # 创建 AST 节点函数
    
    # 测试用例
    test_cases: List[Dict[str, Any]]    # 测试用例列表
    
    # 修复历史
    fix_history: List[Dict[str, str]]   # 修复历史

class PatternRegistry:
    """模式注册表类"""
    
    def __init__(self):
        self.patterns: Dict[str, Pattern] = {}
        self.patterns_by_type: Dict[PatternType, List[str]] = {
            pattern_type: [] for pattern_type in PatternType
        }
        self.patterns_by_opcode: Dict[int, List[str]] = {}
    
    def register(self, pattern: Pattern):
        """注册模式"""
        self.patterns[pattern.name] = pattern
        
        # 按类型索引
        self.patterns_by_type[pattern.pattern_type].append(pattern.name)
        
        # 按操作码索引
        for opcode in pattern.key_opcodes:
            if opcode not in self.patterns_by_opcode:
                self.patterns_by_opcode[opcode] = []
            self.patterns_by_opcode[opcode].append(pattern.name)
    
    def get_pattern(self, name: str) -> Optional[Pattern]:
        """获取模式"""
        return self.patterns.get(name)
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """按类型获取模式"""
        names = self.patterns_by_type.get(pattern_type, [])
        return [self.patterns[name] for name in names if name in self.patterns]
    
    def get_patterns_by_opcode(self, opcode: int) -> List[Pattern]:
        """按操作码获取模式"""
        names = self.patterns_by_opcode.get(opcode, [])
        return [self.patterns[name] for name in names if name in self.patterns]
    
    def match_pattern(self, instruction, context) -> Optional[Pattern]:
        """匹配模式"""
        # 获取可能的模式
        candidates = self.get_patterns_by_opcode(instruction.opcode)
        
        # 按优先级排序
        candidates.sort(key=lambda p: p.priority.value)
        
        # 尝试匹配
        for pattern in candidates:
            if pattern.identify_func(instruction, context):
                return pattern
        
        return None
    
    def list_all_patterns(self) -> List[str]:
        """列出所有模式"""
        return list(self.patterns.keys())
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """获取模式统计信息"""
        stats = {
            "total_patterns": len(self.patterns),
            "by_type": {},
            "by_priority": {}
        }
        
        for pattern_type in PatternType:
            stats["by_type"][pattern_type.value] = len(
                self.patterns_by_type[pattern_type]
            )
        
        for pattern in self.patterns.values():
            priority = pattern.priority.name
            stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1
        
        return stats


# 全局模式注册表实例
_registry = PatternRegistry()

def register_pattern(pattern: Pattern):
    """注册模式到全局注册表"""
    _registry.register(pattern)

def get_pattern(name: str) -> Optional[Pattern]:
    """从全局注册表获取模式"""
    return _registry.get_pattern(name)

def match_pattern(instruction, context) -> Optional[Pattern]:
    """在全局注册表中匹配模式"""
    return _registry.match_pattern(instruction, context)

def get_all_patterns() -> List[str]:
    """获取全局注册表中所有模式"""
    return _registry.list_all_patterns()

def get_pattern_stats() -> Dict[str, Any]:
    """获取全局注册表统计信息"""
    return _registry.get_pattern_statistics()


# 预定义的操作码（Python 3.11+）
class Opcode:
    """Python 3.11+ 操作码"""
    POP_JUMP_FORWARD_IF_FALSE = 108
    POP_JUMP_FORWARD_IF_TRUE = 109
    JUMP_FORWARD = 110
    JUMP_BACKWARD = 111
    FOR_ITER = 100
    PUSH_EXC_INFO = 1
    POP_EXCEPT = 2
    RERAISE = 3
    BINARY_OP = 122
    COMPARE_OP = 107


# 示例：注册 If 模式
if __name__ == "__main__":
    # 创建 If 模式
    if_pattern = Pattern(
        name="If-Elif-Else",
        pattern_type=PatternType.CONTROL_FLOW,
        priority=PatternPriority.HIGH,
        description="If-elif-else 条件分支结构",
        doc_file="patterns/docs/if_pattern.md",
        key_opcodes=[Opcode.POP_JUMP_FORWARD_IF_FALSE, Opcode.POP_JUMP_FORWARD_IF_TRUE],
        required_context=["instructions", "current_offset", "stack"],
        identify_func=lambda instr, ctx: instr.opcode in [
            Opcode.POP_JUMP_FORWARD_IF_FALSE, 
            Opcode.POP_JUMP_FORWARD_IF_TRUE
        ],
        create_node_func=lambda instr, ctx: None,  # 实际实现
        test_cases=[
            {"name": "简单 If", "source": "if x > 0: pass"},
            {"name": "If-Else", "source": "if x > 0: pass\nelse: pass"},
        ],
        fix_history=[
            {
                "date": "2026-03-01",
                "issue": "if_body_end 计算错误",
                "solution": "使用 JUMP_FORWARD 目标",
                "result": "通过"
            }
        ]
    )
    
    # 注册模式
    register_pattern(if_pattern)
    
    # 打印统计信息
    print("模式注册表统计:")
    stats = get_pattern_stats()
    print(f"  总模式数: {stats['total_patterns']}")
    print(f"  按类型: {stats['by_type']}")
    print(f"  按优先级: {stats['by_priority']}")
