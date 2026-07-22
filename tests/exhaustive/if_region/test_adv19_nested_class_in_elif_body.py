import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19NestedClassInElifBody(ExhaustiveTestCase):
    # elif body 内含 class 定义 + 继承 + super 调用（R18 只测 if body 内 class）：
    # def f(x):
    #     if x > 0:
    #         return 'pos'
    #     elif x == 0:
    #         class Animal(Base):
    #             def __init__(self, name):
    #                 super().__init__()
    #                 self.name = name
    #             def speak(self):
    #                 return self.name
    #         return Animal('cat').speak()
    #     else:
    #         return 'neg'
    # 字节码 LOAD_BUILD_CLASS / LOAD_GLOBAL Base / MAKE_FUNCTION / CALL
    # / 反编译器在 elif body 内 class + 继承 + super 时易结构错乱。
    SOURCE_CODE = """def f(x):
    if x > 0:
        return 'pos'
    elif x == 0:
        class Animal(Base):
            def __init__(self, name):
                super().__init__()
                self.name = name
            def speak(self):
                return self.name
        return Animal('cat').speak()
    else:
        return 'neg'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
