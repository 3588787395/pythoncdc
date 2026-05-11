"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务4.2

描述:
    测试 dataclass 的正确还原

当前问题:
    - dataclass装饰器参数可能丢失
    - field()默认工厂可能不被正确还原
    - 内部属性可能泄漏

期望输出:
    应正确输出 @dataclass 和 field() 定义
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本 dataclass
TEST_DATACLASS_BASIC = DecompileTestCase(
    name="dataclass_basic",
    source_code='''
from dataclasses import dataclass

@dataclass
class Person:
    name: str
    age: int = 0
'''.strip(),
    expected_patterns=["@dataclass", "class Person:", "name: str", "age: int = 0"]
)

# 测试用例2: dataclass with field
TEST_DATACLASS_FIELD = DecompileTestCase(
    name="dataclass_field",
    source_code='''
from dataclasses import dataclass, field

@dataclass
class Config:
    name: str
    values: list = field(default_factory=list)
    enabled: bool = field(default=True)
    metadata: dict = field(default_factory=dict, repr=False)
'''.strip(),
    expected_patterns=["@dataclass", "field(default_factory=list)", "field(default=True)"]
)

# 测试用例3: dataclass with parameters
TEST_DATACLASS_PARAMS = DecompileTestCase(
    name="dataclass_params",
    source_code='''
from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Point:
    x: float
    y: float
'''.strip(),
    expected_patterns=["@dataclass(frozen=True, order=True)", "class Point:", "x: float"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("DATACLASS 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_DATACLASS_BASIC.source_code, "dataclass_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_DATACLASS_BASIC, TEST_DATACLASS_FIELD, TEST_DATACLASS_PARAMS]:
        success = test.run()
        print(test.get_report())
        print()
