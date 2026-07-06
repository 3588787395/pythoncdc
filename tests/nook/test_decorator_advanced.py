"""
测试状态: ⚠️ 部分
优先级: P2
相关任务: 任务4.1

描述:
    测试高级装饰器特性

当前问题:
    - 多装饰器函数可能只处理最后一个装饰器
    - 带参数装饰器可能处理不正确

期望输出:
    应正确输出装饰器栈
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 多装饰器
TEST_MULTIPLE_DECORATORS = DecompileTestCase(
    name="multiple_decorators",
    source_code='''
@decorator1
@decorator2
@decorator3
def func():
    pass
'''.strip(),
    expected_patterns=["@decorator1", "@decorator2", "@decorator3", "def func():"]
)

# 测试用例2: 带参数装饰器
TEST_DECORATOR_WITH_ARGS = DecompileTestCase(
    name="decorator_with_args",
    source_code='''
@decorator(arg1, arg2="value")
def func():
    pass
'''.strip(),
    expected_patterns=['@decorator(arg1, arg2="value")', "def func():"]
)

# 测试用例3: 类装饰器
TEST_CLASS_DECORATOR = DecompileTestCase(
    name="class_decorator",
    source_code='''
@dataclass
class Person:
    name: str
    age: int
'''.strip(),
    expected_patterns=["@dataclass", "class Person:", "name: str", "age: int"]
)

# 测试用例4: 方法装饰器
TEST_METHOD_DECORATOR = DecompileTestCase(
    name="method_decorator",
    source_code='''
class MyClass:
    @staticmethod
    def static_method():
        pass
    
    @classmethod
    def class_method(cls):
        pass
'''.strip(),
    expected_patterns=["@staticmethod", "def static_method():", "@classmethod", "def class_method(cls):"]
)

# 测试用例5: 嵌套装饰器
TEST_NESTED_DECORATOR = DecompileTestCase(
    name="nested_decorator",
    source_code='''
@outer(inner(arg))
def func():
    pass
'''.strip(),
    expected_patterns=["@outer(inner(arg))", "def func():"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("高级装饰器字节码示例")
    print("=" * 60)
    disassemble_code(TEST_MULTIPLE_DECORATORS.source_code, "multiple_decorators")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_MULTIPLE_DECORATORS, TEST_DECORATOR_WITH_ARGS, TEST_CLASS_DECORATOR,
                 TEST_METHOD_DECORATOR, TEST_NESTED_DECORATOR]:
        success = test.run()
        print(test.get_report())
        print()
