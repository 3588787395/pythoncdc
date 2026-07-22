import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18TryExceptInElifBody(ExhaustiveTestCase):
    # if-elif-else 三个分支都含 try/except + as e：
    # def f(x):
    #     if x > 0:
    #         try:
    #             r = op_pos(x)
    #         except ValueError as e:
    #             r = str(e)
    #     elif x < 0:
    #         try:
    #             r = op_neg(x)
    #         except ValueError as e:
    #             r = str(e)
    #     else:
    #         r = 0
    #     return r
    # 字节码 SETUP_FINALLY + PUSH_EXC_INFO + CHECK_EXC_MATCH + STORE_FAST e
    # / 反编译器在 if-elif 链中每个分支都含 try/except + as e 时易把
    # 第二个 except 错挂到外层 if。
    SOURCE_CODE = """def f(x):
    if x > 0:
        try:
            r = op_pos(x)
        except ValueError as e:
            r = str(e)
    elif x < 0:
        try:
            r = op_neg(x)
        except ValueError as e:
            r = str(e)
    else:
        r = 0
    return r"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
