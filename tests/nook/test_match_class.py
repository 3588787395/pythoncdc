"""
测试状态: ❌ 失败
优先级: P0
相关任务: 任务1.2

描述:
    测试 match/case 的类模式匹配
    使用 MATCH_CLASS 字节码指令

当前问题:
    - 完全不支持 MATCH_CLASS 指令
    - 无法识别 Point(x=0, y=0) 这样的类模式

期望输出:
    应包含 case Point(x=0, y=0): 这样的类模式匹配
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 基本类模式
TEST_MATCH_CLASS_BASIC = DecompileTestCase(
    name="match_class_basic",
    source_code='''
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

point = Point(0, 0)

match point:
    case Point(x=0, y=0):
        result = "origin"
    case Point(x=x, y=0):
        result = "on x-axis"
    case Point(x=0, y=y):
        result = "on y-axis"
    case Point():
        result = "other point"
'''.strip(),
    expected_patterns=["match", "case Point(x=0, y=0):", "case Point():", "result"]
)

# 测试用例2: 带位置参数的类模式
TEST_MATCH_CLASS_POSITIONAL = DecompileTestCase(
    name="match_class_positional",
    source_code='''
class Point:
    __match_args__ = ("x", "y")
    def __init__(self, x, y):
        self.x = x
        self.y = y

match point:
    case Point(0, 0):
        result = "origin"
    case Point(x, 0):
        result = f"on x-axis at {x}"
    case Point(0, y):
        result = f"on y-axis at {y}"
    case Point(x, y):
        result = f"point at ({x}, {y})"
'''.strip(),
    expected_patterns=["match", "case Point(0, 0):", "case Point(x, y):", "result"]
)

# 测试用例3: 嵌套类模式
TEST_MATCH_CLASS_NESTED = DecompileTestCase(
    name="match_class_nested",
    source_code='''
class Line:
    def __init__(self, start, end):
        self.start = start
        self.end = end

match line:
    case Line(Point(0, 0), Point(x, y)):
        result = "line from origin"
    case Line(Point(x1, y1), Point(x2, y2)):
        result = f"line from ({x1}, {y1}) to ({x2}, {y2})"
'''.strip(),
    expected_patterns=["match", "case Line(", "Point(0, 0)", "result"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("MATCH_CLASS 字节码示例")
    print("=" * 60)
    disassemble_code(TEST_MATCH_CLASS_BASIC.source_code, "match_class_basic")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_MATCH_CLASS_BASIC, TEST_MATCH_CLASS_POSITIONAL, TEST_MATCH_CLASS_NESTED]:
        success = test.run()
        print(test.get_report())
        print()
