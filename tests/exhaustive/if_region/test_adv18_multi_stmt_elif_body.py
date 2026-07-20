import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18MultiStmtElifBody(ExhaustiveTestCase):
    # if-elif-else body 内含多条语句（赋值 + 调用 + 赋值）：
    # def f(x):
    #     if x > 0:
    #         a = 1
    #         b = 2
    #         c = a + b
    #     elif x < 0:
    #         a = -1
    #         b = -2
    #         c = a + b
    #     else:
    #         a = 0
    #         b = 0
    #         c = 0
    #     return c
    # 字节码多 STORE_FAST + BINARY_OP + RETURN / 反编译器在 if body 内含
    # 多条赋值语句时易把第二条 STORE_FAST 后的语句错挂到 if body 外。
    SOURCE_CODE = """def f(x):
    if x > 0:
        a = 1
        b = 2
        c = a + b
    elif x < 0:
        a = -1
        b = -2
        c = a + b
    else:
        a = 0
        b = 0
        c = 0
    return c"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
