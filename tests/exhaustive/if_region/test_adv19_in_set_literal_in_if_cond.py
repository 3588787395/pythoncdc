import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19InSetLiteralInIfCond(ExhaustiveTestCase):
    # if-elif-else 条件含 `in` set literal / frozenset + 多重 in：
    # def f(x):
    #     if x in {1, 2, 3, 5, 8}:
    #         return 'fib'
    #     elif x in {10, 20, 30}:
    #         return 'tens'
    #     elif x in frozenset({100, 200}):
    #         return 'hundreds'
    #     else:
    #         return 'other'
    # 字节码 BUILD_SET / LOAD_CONST (frozenset) / CONTAINS_OP
    # / 反编译器在 if-elif 条件含 set literal + 多重 in 时易归约错乱。
    SOURCE_CODE = """def f(x):
    if x in {1, 2, 3, 5, 8}:
        return 'fib'
    elif x in {10, 20, 30}:
        return 'tens'
    elif x in frozenset({100, 200}):
        return 'hundreds'
    else:
        return 'other'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
