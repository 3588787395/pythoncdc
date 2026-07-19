import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17ForIfElifElseFlow(ExhaustiveTestCase):
    # for 循环内 if/elif/else 配合 break/continue/return：
    # def f():
    #     for i in range(10):
    #         if i > 5:
    #             break
    #         elif i < 3:
    #             continue
    #         else:
    #             return i
    # 字节码 FOR_ITER + POP_JUMP_IF_FALSE 链 + BREAK/CONTINUE/RETURN
    # / 反编译器在 for body 内 if/elif/else + 三种 flow control 组合时
    # 易把 elif 误识别为单独 if，或把 return 提升到 for 外。
    SOURCE_CODE = """def f():
    for i in range(10):
        if i > 5:
            break
        elif i < 3:
            continue
        else:
            return i"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
