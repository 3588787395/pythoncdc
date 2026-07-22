import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19LambdaIifeInIfCond(ExhaustiveTestCase):
    # if 条件含 lambda 立即调用 (IIFE) + 与常量比较：
    # def f(y):
    #     if (lambda x: x > 0)(y) and (lambda x: x < 100)(y):
    #         return 'valid'
    #     elif (lambda x: x == 0)(y):
    #         return 'zero'
    #     else:
    #         return 'invalid'
    # 字节码 LOAD_CONST <code> / MAKE_FUNCTION / PRECALL / CALL / COMPARE_OP
    # / 反编译器在 if 条件含 lambda IIFE + boolop + elif 链时易丢失 lambda 调用。
    SOURCE_CODE = """def f(y):
    if (lambda x: x > 0)(y) and (lambda x: x < 100)(y):
        return 'valid'
    elif (lambda x: x == 0)(y):
        return 'zero'
    else:
        return 'invalid'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
