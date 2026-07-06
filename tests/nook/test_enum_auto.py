"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务4.3

描述:
    测试 Enum.auto() 的正确还原

当前问题:
    - Enum.auto() 可能被还原为方法调用而非自动编号

期望输出:
    应正确输出 RED = auto() 形式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本 Enum with auto
TEST_ENUM_AUTO_BASIC = DecompileTestCase(
    name="enum_auto_basic",
    source_code='''
from enum import Enum, auto

class Color(Enum):
    RED = auto()
    GREEN = auto()
    BLUE = auto()
'''.strip(),
    expected_patterns=["class Color(Enum):", "RED = auto()", "GREEN = auto()", "BLUE = auto()"]
)

# 测试用例2: Enum with mixed values
TEST_ENUM_MIXED = DecompileTestCase(
    name="enum_mixed",
    source_code='''
from enum import Enum, auto

class Status(Enum):
    PENDING = 1
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = -1
'''.strip(),
    expected_patterns=["PENDING = 1", "RUNNING = auto()", "COMPLETED = auto()", "FAILED = -1"]
)

# 测试用例3: IntEnum
TEST_INTENUM = DecompileTestCase(
    name="intenum",
    source_code='''
from enum import IntEnum, auto

class Priority(IntEnum):
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
'''.strip(),
    expected_patterns=["class Priority(IntEnum):", "LOW = auto()", "HIGH = auto()"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("ENUM AUTO 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_ENUM_AUTO_BASIC.source_code, "enum_auto_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_ENUM_AUTO_BASIC, TEST_ENUM_MIXED, TEST_INTENUM]:
        success = test.run()
        print(test.get_report())
        print()
