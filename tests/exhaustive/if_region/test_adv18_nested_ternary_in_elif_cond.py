import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18NestedTernaryInElifCond(ExhaustiveTestCase):
    # if-elif 链条件含嵌套 ternary 表达式：
    # def f(x):
    #     if (1 if x else 2) > 0:
    #         r = 'a'
    #     elif (3 if x else 4) < 5:
    #         r = 'b'
    #     else:
    #         r = 'c'
    #     return r
    # 字节码 POP_JUMP_IF_FALSE + 嵌套 ternary 的 SL + ROT / 反编译器在
    # if-elif 链条件含嵌套 ternary 时易把 ternary 退化为内嵌 if-else。
    SOURCE_CODE = """def f(x):
    if (1 if x else 2) > 0:
        r = 'a'
    elif (3 if x else 4) < 5:
        r = 'b'
    else:
        r = 'c'
    return r"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
