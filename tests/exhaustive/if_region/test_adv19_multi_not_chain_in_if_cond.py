import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19MultiNotChainInIfCond(ExhaustiveTestCase):
    # if-elif-else 条件含 4 项 not 链：
    # def f(a, b, c, d):
    #     if not a and not b and not c and not d:
    #         return 'all_false'
    #     elif not a or not b or not c:
    #         return 'some_false'
    #     elif a and b and c and d:
    #         return 'all_true'
    #     else:
    #         return 'mixed'
    # 字节码 UNARY_NOT / POP_JUMP_IF_FALSE / POP_JUMP_IF_TRUE (短路)
    # / 反编译器在 4 项 not 链 + 4 项 and 链 + elif 链时易归约错乱。
    SOURCE_CODE = """def f(a, b, c, d):
    if not a and not b and not c and not d:
        return 'all_false'
    elif not a or not b or not c:
        return 'some_false'
    elif a and b and c and d:
        return 'all_true'
    else:
        return 'mixed'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
