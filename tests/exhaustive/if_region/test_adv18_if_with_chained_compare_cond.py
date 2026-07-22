import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18IfWithChainedCompareCond(ExhaustiveTestCase):
    # if-elif 链条件都含链式比较 + walrus：
    # def f(x):
    #     if 0 < x < 10:
    #         r = 'low'
    #     elif 10 <= x <= 50:
    #         r = 'mid'
    #     elif 50 < x < 100:
    #         r = 'high'
    #     else:
    #         r = 'out'
    #     return r
    # 字节码 COMPARE_OP + POP_JUMP_IF_FALSE 链 / 反编译器在 if-elif 链中
    # 每个分支都含链式比较时易把链式比较错识别为多个独立 if。
    SOURCE_CODE = """def f(x):
    if 0 < x < 10:
        r = 'low'
    elif 10 <= x <= 50:
        r = 'mid'
    elif 50 < x < 100:
        r = 'high'
    else:
        r = 'out'
    return r"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
