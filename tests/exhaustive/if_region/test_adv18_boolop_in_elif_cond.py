import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18BoolopInElifCond(ExhaustiveTestCase):
    # if-elif 链条件含 3+ 项 boolop（and/or）：
    # def f(a, b, c, d):
    #     if a and b and c:
    #         r = 1
    #     elif a or b or c or d:
    #         r = 2
    #     elif a and not b:
    #         r = 3
    #     else:
    #         r = 4
    #     return r
    # 字节码 JUMP_IF_FALSE_OR_POP / JUMP_IF_TRUE_OR_POP 链 + POP_JUMP_IF_FALSE
    # / 反编译器在 if-elif 链每个分支都含 3+ 项 boolop 时易把 boolop 错挂到 if 外。
    SOURCE_CODE = """def f(a, b, c, d):
    if a and b and c:
        r = 1
    elif a or b or c or d:
        r = 2
    elif a and not b:
        r = 3
    else:
        r = 4
    return r"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
