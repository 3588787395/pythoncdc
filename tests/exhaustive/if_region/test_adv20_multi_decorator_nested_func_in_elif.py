import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20MultiDecoratorNestedFuncInElif(ExhaustiveTestCase):
    # elif body 内含多装饰器 + 嵌套函数 + 闭包修改：
    # def deco1(fn):
    #     def w(*a, **k):
    #         return fn(*a, **k) + 1
    #     return w
    # def deco2(fn):
    #     def w(*a, **k):
    #         return fn(*a, **k) * 2
    #     return w
    # def f(flag):
    #     if flag == 'a':
    #         return 'a'
    #     elif flag == 'b':
    #         @deco1
    #         @deco2
    #         def calc(x):
    #             base = 10
    #             def inner(y):
    #                 nonlocal base
    #                 base = base + y
    #                 return base
    #             return inner(x)
    #         return calc(5)
    #     else:
    #         return 'none'
    # 字节码 LOAD_NAME deco1 / LOAD_NAME deco2 / MAKE_FUNCTION / CALL
    # / 反编译器在 elif body 内多装饰器 + 嵌套函数 + nonlocal 修改时易丢失装饰器顺序。
    SOURCE_CODE = """def deco1(fn):
    def w(*a, **k):
        return fn(*a, **k) + 1
    return w
def deco2(fn):
    def w(*a, **k):
        return fn(*a, **k) * 2
    return w
def f(flag):
    if flag == 'a':
        return 'a'
    elif flag == 'b':
        @deco1
        @deco2
        def calc(x):
            base = 10
            def inner(y):
                nonlocal base
                base = base + y
                return base
            return inner(x)
        return calc(5)
    else:
        return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
