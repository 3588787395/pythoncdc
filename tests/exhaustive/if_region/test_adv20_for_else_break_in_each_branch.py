import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20ForElseBreakInEachBranch(ExhaustiveTestCase):
    # if-elif-else 三分支各自含 for-else + break 组合：
    # def f(flag, items):
    #     if flag == 'a':
    #         for x in items:
    #             if x > 0:
    #                 break
    #         else:
    #             return 'no_pos'
    #         return x
    #     elif flag == 'b':
    #         for y in items:
    #             if y < 0:
    #                 break
    #         else:
    #             return 'no_neg'
    #         return y
    #     else:
    #         for z in items:
    #             if z == 0:
    #                 break
    #         else:
    #             return 'no_zero'
    #         return z
    # 字节码 FOR_ITER / POP_JUMP_IF_FALSE / JUMP_BACKWARD
    # / 反编译器在 if-elif-else 三分支都含 for-else-break 时易丢失 else 子句。
    SOURCE_CODE = """def f(flag, items):
    if flag == 'a':
        for x in items:
            if x > 0:
                break
        else:
            return 'no_pos'
        return x
    elif flag == 'b':
        for y in items:
            if y < 0:
                break
        else:
            return 'no_neg'
        return y
    else:
        for z in items:
            if z == 0:
                break
        else:
            return 'no_zero'
        return z"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
