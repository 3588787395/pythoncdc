import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20LambdaWithClosureInIfBody(ExhaustiveTestCase):
    # if body 内含 lambda 捕获外部变量 + 多层闭包 + 立即调用：
    # def f(flag, base):
    #     if flag:
    #         multiplier = 3
    #         adder = lambda x: lambda y: x + y * multiplier
    #         inner = adder(base)
    #         return inner(10)
    #     return 0
    # 字节码 MAKE_FUNCTION / LOAD_CLOSURE / LOAD_DEREF / CALL
    # / 反编译器在 if body 内嵌套 lambda 闭包捕获时易丢失外层闭包变量。
    SOURCE_CODE = """def f(flag, base):
    if flag:
        multiplier = 3
        adder = lambda x: lambda y: x + y * multiplier
        inner = adder(base)
        return inner(10)
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
