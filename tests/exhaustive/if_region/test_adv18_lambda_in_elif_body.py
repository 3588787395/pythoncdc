import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18LambdaInElifBody(ExhaustiveTestCase):
    # if-elif-else body 内含 lambda + 多参数 + 默认值：
    # def f(mode):
    #     if mode == 1:
    #         fn = lambda x, y=10: x + y
    #     elif mode == 2:
    #         fn = lambda *args, **kwargs: sum(args) + sum(kwargs.values())
    #     else:
    #         fn = lambda x: x * 2
    #     return fn(5)
    # 字节码 LOAD_CONST <code> / LOAD_CONST 'x' / MAKE_FUNCTION / 反编译器
    # 在 if body 内含 lambda + 复杂参数（*args, **kwargs, 默认值）时易丢失
    # 参数绑定或错把 lambda body 提升到 if body 外。
    SOURCE_CODE = """def f(mode):
    if mode == 1:
        fn = lambda x, y=10: x + y
    elif mode == 2:
        fn = lambda *args, **kwargs: sum(args) + sum(kwargs.values())
    else:
        fn = lambda x: x * 2
    return fn(5)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
