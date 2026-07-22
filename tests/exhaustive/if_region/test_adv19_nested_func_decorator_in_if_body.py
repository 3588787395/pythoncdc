import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19NestedFuncDecoratorInIfBody(ExhaustiveTestCase):
    # if body 内含嵌套 def + 装饰器 + 调用：
    # def deco(fn):
    #     def wrap(*a, **k):
    #         return fn(*a, **k) + 1
    #     return wrap
    # def f(flag):
    #     if flag:
    #         @deco
    #         def calc(x):
    #             return x * 2
    #         return calc(10)
    #     return 0
    # 字节码 LOAD_NAME deco / MAKE_FUNCTION / CALL / STORE_NAME
    # / 反编译器在 if body 内 @decorator + 嵌套 def + 调用时易丢失装饰器。
    SOURCE_CODE = """def deco(fn):
    def wrap(*a, **k):
        return fn(*a, **k) + 1
    return wrap
def f(flag):
    if flag:
        @deco
        def calc(x):
            return x * 2
        return calc(10)
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
