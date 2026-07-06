#!/usr/bin/env python3
"""
测试用例管理系统

用于管理、组织和执行测试用例
"""

import json
import hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class TestStatus(Enum):
    """测试状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PENDING = "pending"

class TestTag(Enum):
    """测试标签枚举"""
    SIMPLE = "simple"           # 简单测试
    COMPLEX = "complex"         # 复杂测试
    BOUNDARY = "boundary"       # 边界测试
    REGRESSION = "regression"   # 回归测试
    PERFORMANCE = "performance" # 性能测试

@dataclass
class TestCase:
    """测试用例数据类"""
    name: str                           # 测试用例名称
    pattern_type: str                   # 所属模式类型
    source_code: str                    # 源代码
    expected_output: Optional[str] = None      # 期望的输出（可选）
    expected_ast: Optional[Dict] = None        # 期望的 AST 结构（可选）
    tags: List[str] = None              # 标签列表
    description: str = ""               # 测试描述
    created_at: str = ""                # 创建时间
    updated_at: str = ""                # 更新时间
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TestCase':
        """从字典创建"""
        return cls(**data)
    
    def get_id(self) -> str:
        """生成唯一ID"""
        content = f"{self.name}:{self.pattern_type}:{self.source_code}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

@dataclass
class TestResult:
    """测试结果数据类"""
    test_id: str                        # 测试用例ID
    test_name: str                      # 测试名称
    pattern_type: str                   # 模式类型
    status: TestStatus                  # 测试状态
    duration_ms: float                  # 执行时间（毫秒）
    actual_output: Optional[str] = None        # 实际输出
    error_message: Optional[str] = None        # 错误信息
    diff: Optional[str] = None                 # 差异信息
    timestamp: str = ""                 # 测试时间
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'pattern_type': self.pattern_type,
            'status': self.status.value,
            'duration_ms': self.duration_ms,
            'actual_output': self.actual_output,
            'error_message': self.error_message,
            'diff': self.diff,
            'timestamp': self.timestamp
        }

class TestCaseManager:
    """测试用例管理器"""
    
    def __init__(self, test_cases_file: str = "test_cases.json"):
        self.test_cases_file = test_cases_file
        self.test_cases: Dict[str, TestCase] = {}
        self.load_test_cases()
    
    def load_test_cases(self):
        """加载测试用例"""
        try:
            with open(self.test_cases_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    test_case = TestCase.from_dict(item)
                    self.test_cases[test_case.get_id()] = test_case
        except FileNotFoundError:
            # 文件不存在，创建空的管理器
            pass
    
    def save_test_cases(self):
        """保存测试用例"""
        data = [tc.to_dict() for tc in self.test_cases.values()]
        with open(self.test_cases_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_test_case(self, test_case: TestCase) -> str:
        """添加测试用例"""
        test_id = test_case.get_id()
        self.test_cases[test_id] = test_case
        self.save_test_cases()
        return test_id
    
    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """获取测试用例"""
        return self.test_cases.get(test_id)
    
    def remove_test_case(self, test_id: str) -> bool:
        """删除测试用例"""
        if test_id in self.test_cases:
            del self.test_cases[test_id]
            self.save_test_cases()
            return True
        return False
    
    def get_test_cases_by_pattern(self, pattern_type: str) -> List[TestCase]:
        """按模式类型获取测试用例"""
        return [tc for tc in self.test_cases.values() if tc.pattern_type == pattern_type]
    
    def get_test_cases_by_tag(self, tag: str) -> List[TestCase]:
        """按标签获取测试用例"""
        return [tc for tc in self.test_cases.values() if tag in tc.tags]
    
    def get_all_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        return list(self.test_cases.values())
    
    def get_test_case_count(self) -> int:
        """获取测试用例数量"""
        return len(self.test_cases)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = {
            'total': len(self.test_cases),
            'by_pattern': {},
            'by_tag': {}
        }
        
        for tc in self.test_cases.values():
            # 按模式统计
            stats['by_pattern'][tc.pattern_type] = stats['by_pattern'].get(tc.pattern_type, 0) + 1
            
            # 按标签统计
            for tag in tc.tags:
                stats['by_tag'][tag] = stats['by_tag'].get(tag, 0) + 1
        
        return stats

# 预定义的测试用例库 - 使用有效的Python代码
DEFAULT_TEST_CASES = [
    TestCase(
        name="test_if_simple",
        pattern_type="If-Elif-Else",
        source_code="""x = 5
if x > 0:
    result = 'positive'""",
        tags=["simple"],
        description="简单 if 语句"
    ),
    TestCase(
        name="test_if_else",
        pattern_type="If-Elif-Else",
        source_code="""x = 5
if x > 0:
    result = 'positive'
else:
    result = 'non-positive'""",
        tags=["simple"],
        description="if-else 语句"
    ),
    TestCase(
        name="test_try_except_simple",
        pattern_type="Try-Except",
        source_code="""try:
    result = 10 / 0
except ZeroDivisionError:
    result = 'error'""",
        tags=["simple"],
        description="简单 try-except"
    ),
    TestCase(
        name="test_try_except_in_for",
        pattern_type="Try-Except",
        source_code="""result = 0
for i in range(1, 5):
    try:
        result += 10 // i
    except:
        pass""",
        tags=["complex", "regression"],
        description="for 循环内的 try-except（关键修复测试）"
    ),
    TestCase(
        name="test_for_simple",
        pattern_type="For-Loop",
        source_code="""result = 0
for i in range(5):
    result += i""",
        tags=["simple"],
        description="简单 for 循环"
    ),
    TestCase(
        name="test_augassign_simple",
        pattern_type="AugAssign",
        source_code="""x = 0
x += 1""",
        tags=["simple"],
        description="简单复合赋值"
    ),
    TestCase(
        name="test_list_comprehension",
        pattern_type="Comprehension",
        source_code="""squares = [x**2 for x in range(10)]""",
        tags=["simple"],
        description="列表推导式"
    ),
    TestCase(
        name="test_function_def",
        pattern_type="FunctionDef",
        source_code="""def test():
    return 42""",
        tags=["simple"],
        description="简单函数定义"
    ),
    TestCase(
        name="test_class_def",
        pattern_type="ClassDef",
        source_code="""class MyClass:
    pass""",
        tags=["simple"],
        description="简单类定义"
    ),
    TestCase(
        name="test_break_in_for",
        pattern_type="BreakContinue",
        source_code="""for i in range(10):
    if i == 5:
        break""",
        tags=["simple"],
        description="for 循环中的 break"
    ),
    TestCase(
        name="test_return_value",
        pattern_type="Return",
        source_code="""def test():
    return 42""",
        tags=["simple"],
        description="return 带值"
    ),
    TestCase(
        name="test_lambda_simple",
        pattern_type="Lambda",
        source_code="""f = lambda x: x + 1""",
        tags=["simple"],
        description="简单 lambda"
    ),
    TestCase(
        name="test_decorator",
        pattern_type="Decorator",
        source_code="""def decorator(f):
    return f

@decorator
def func():
    pass""",
        tags=["simple"],
        description="装饰器"
    ),
    TestCase(
        name="test_import",
        pattern_type="Import",
        source_code="""import os""",
        tags=["simple"],
        description="import 语句"
    ),
    TestCase(
        name="test_global",
        pattern_type="GlobalNonlocal",
        source_code="""x = 0
def func():
    global x
    x = 10""",
        tags=["simple"],
        description="global 声明"
    ),
]

def initialize_test_cases():
    """初始化默认测试用例"""
    manager = TestCaseManager()
    
    # 添加默认测试用例
    for test_case in DEFAULT_TEST_CASES:
        manager.add_test_case(test_case)
    
    print(f"已初始化 {len(DEFAULT_TEST_CASES)} 个测试用例")
    return manager

if __name__ == "__main__":
    # 初始化测试用例
    manager = initialize_test_cases()
    
    # 打印统计信息
    stats = manager.get_statistics()
    print("\n测试用例统计:")
    print(f"  总计: {stats['total']}")
    print(f"  按模式: {stats['by_pattern']}")
    print(f"  按标签: {stats['by_tag']}")
