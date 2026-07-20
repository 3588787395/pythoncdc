import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18NestedIfElifElseWithReturnMix(ExhaustiveTestCase):
    # if-elif-else 中混合 return 和 fallthrough + 嵌套 if-else：
    # def f(x, y):
    #     if x > 0:
    #         if y > 0:
    #             return 1
    #         return 2
    #     elif x < 0:
    #         return 3
    #     else:
    #         return 4
    # 字节码多层 POP_JUMP_IF_FALSE + RETURN + JUMP_FORWARD / 反编译器
    # 在 if body 内嵌套 if-else + early return 而 elif body 只 return 时
    # 易丢失内层 if 的 else 分支或错挂 return。
    SOURCE_CODE = """def f(x, y):
    if x > 0:
        if y > 0:
            return 1
        return 2
    elif x < 0:
        return 3
    else:
        return 4"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
