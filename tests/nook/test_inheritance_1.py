"""
测试状态: ⚠️ 部分
优先级: P1
相关任务: 任务4.x

描述:
    测试类继承相关语法

当前问题:
    - 复杂继承关系可能处理不正确

期望输出:
    应正确输出 class Child(Parent): 语法
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tests.other.test_utils import DecompileTestCase, disassemble_code


# 测试用例1: 单继承
TEST_SINGLE_INHERITANCE = DecompileTestCase(
    name="single_inheritance",
    source_code='''
class Animal:
    def speak(self):
        return "sound"

class Dog(Animal):
    def speak(self):
        return "woof"
'''.strip(),
    expected_patterns=["class Animal:", "class Dog(Animal):", "def speak(self)"]
)

# 测试用例2: 多继承
TEST_MULTIPLE_INHERITANCE = DecompileTestCase(
    name="multiple_inheritance",
    source_code='''
class Flyer:
    def fly(self):
        return "flying"

class Swimmer:
    def swim(self):
        return "swimming"

class Duck(Flyer, Swimmer):
    pass
'''.strip(),
    expected_patterns=["class Flyer:", "class Swimmer:", "class Duck(Flyer, Swimmer):"]
)

# 测试用例3: 继承内置类型
TEST_BUILTIN_INHERITANCE = DecompileTestCase(
    name="builtin_inheritance",
    source_code='''
class MyList(list):
    def first(self):
        return self[0] if self else None

class MyDict(dict):
    def get_or_default(self, key, default):
        return self.get(key, default)
'''.strip(),
    expected_patterns=["class MyList(list):", "class MyDict(dict):"]
)

# 测试用例4: 抽象基类
TEST_ABC_INHERITANCE = DecompileTestCase(
    name="abc_inheritance",
    source_code='''
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass

class Rectangle(Shape):
    def __init__(self, w, h):
        self.w = w
        self.h = h
    
    def area(self):
        return self.w * self.h
'''.strip(),
    expected_patterns=["class Shape(ABC):", "@abstractmethod", "class Rectangle(Shape):"]
)


if __name__ == "__main__":
    print("=" * 60)
    print("类继承字节码示例")
    print("=" * 60)
    disassemble_code(TEST_SINGLE_INHERITANCE.source_code, "single_inheritance")
    
    print("\n" + "=" * 60)
    print("运行测试")
    print("=" * 60)
    
    for test in [TEST_SINGLE_INHERITANCE, TEST_MULTIPLE_INHERITANCE, 
                 TEST_BUILTIN_INHERITANCE, TEST_ABC_INHERITANCE]:
        success = test.run()
        print(test.get_report())
        print()
