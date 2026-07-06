"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务4.1

描述:
    测试 @property 描述符的完整支持

当前问题:
    - @property.setter 装饰器可能被错误分解
    - @property.deleter 可能不被识别

期望输出:
    应正确输出 @property, @x.setter, @x.deleter
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: property + setter + deleter
TEST_PROPERTY_FULL = DecompileTestCase(
    name="property_full",
    source_code='''
class MyClass:
    def __init__(self):
        self._value = None

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val

    @value.deleter
    def value(self):
        del self._value
'''.strip(),
    expected_patterns=["@property", "@value.setter", "@value.deleter", "def value"]
)

# 测试用例2: 多个property
TEST_PROPERTY_MULTIPLE = DecompileTestCase(
    name="property_multiple",
    source_code='''
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value

    @property
    def area(self):
        return self._width * self._height
'''.strip(),
    expected_patterns=["@property", "@width.setter", "@height.setter", "def area"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("PROPERTY 描述符字节码示例")
    print("=" * 60)
    disassemble_code(TEST_PROPERTY_FULL.source_code, "property_full")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_PROPERTY_FULL, TEST_PROPERTY_MULTIPLE]:
        success = test.run()
        print(test.get_report())
        print()
