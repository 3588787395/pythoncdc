import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19ChainedInCheckInIfCond(ExhaustiveTestCase):
    # if-elif-else 条件含 3 项 in 检查链 + 比较 + elif：
    # def f(x, a, b, c):
    #     if x in a and x in b and x in c:
    #         return 'in_all'
    #     elif x in a or x in b:
    #         return 'in_ab'
    #     elif x not in c:
    #         return 'not_in_c'
    #     else:
    #         return 'none'
    # 字节码 CONTAINS_OP / POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE
    # / 反编译器在 3 项 in 链 + not in + elif 链时易归约错乱。
    SOURCE_CODE = """def f(x, a, b, c):
    if x in a and x in b and x in c:
        return 'in_all'
    elif x in a or x in b:
        return 'in_ab'
    elif x not in c:
        return 'not_in_c'
    else:
        return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
