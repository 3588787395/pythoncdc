import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19TryExceptElseInIfBody(ExhaustiveTestCase):
    # if body 内含 try-except-else 三子句（无 finally）+ 后续 if-elif：
    # def f(x):
    #     if x > 0:
    #         result = None
    #         try:
    #             r = process(x)
    #         except ValueError:
    #             r = -1
    #         else:
    #             r = r + 1
    #         if r > 100:
    #             return 'big'
    #         elif r > 0:
    #             return 'small'
    #     return 'none'
    # 字节码 SETUP_EXCEPT / PUSH_EXC_INFO / POP_EXCEPT / RERAISE
    # / 反编译器在 if body 内 try-except-else + 后续 if-elif 时易丢失 else 子句或后续代码。
    SOURCE_CODE = """def f(x):
    if x > 0:
        result = None
        try:
            r = process(x)
        except ValueError:
            r = -1
        else:
            r = r + 1
        if r > 100:
            return 'big'
        elif r > 0:
            return 'small'
    return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
