import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19NestedIfElifInEachBranch(ExhaustiveTestCase):
    # if-elif-else 三分支各自含嵌套 if-elif-else：
    # def f(x, y):
    #     if x > 0:
    #         if y > 0:
    #             return 'pos_pos'
    #         elif y < 0:
    #             return 'pos_neg'
    #         else:
    #             return 'pos_zero'
    #     elif x < 0:
    #         if y > 0:
    #             return 'neg_pos'
    #         elif y < 0:
    #             return 'neg_neg'
    #         else:
    #             return 'neg_zero'
    #     else:
    #         if y > 0:
    #             return 'zero_pos'
    #         elif y < 0:
    #             return 'zero_neg'
    #         else:
    #             return 'zero_zero'
    # 字节码 POP_JUMP_IF_FALSE / JUMP_FORWARD / POP_JUMP_IF_TRUE
    # / 反编译器在 if-elif-else 三分支各自嵌套 if-elif-else 时易结构错乱。
    SOURCE_CODE = """def f(x, y):
    if x > 0:
        if y > 0:
            return 'pos_pos'
        elif y < 0:
            return 'pos_neg'
        else:
            return 'pos_zero'
    elif x < 0:
        if y > 0:
            return 'neg_pos'
        elif y < 0:
            return 'neg_neg'
        else:
            return 'neg_zero'
    else:
        if y > 0:
            return 'zero_pos'
        elif y < 0:
            return 'zero_neg'
        else:
            return 'zero_zero'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
