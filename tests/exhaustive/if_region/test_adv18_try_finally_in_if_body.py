import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18TryFinallyInIfBody(ExhaustiveTestCase):
    # if body 内含 try-finally（无 except）嵌套 + if-elif：
    # def f(x):
    #     if x > 0:
    #         try:
    #             r = compute(x)
    #         finally:
    #             cleanup()
    #         if r > 100:
    #             return 'big'
    #         elif r > 10:
    #             return 'mid'
    #     return 'small'
    # 字节码 SETUP_FINALLY + POP_BLOCK + CALL_FINALLY / 反编译器在 if body
    # 内 try-finally 后再嵌套 if-elif 时易把第二个 if 错挂到 finally body。
    SOURCE_CODE = """def f(x):
    if x > 0:
        try:
            r = compute(x)
        finally:
            cleanup()
        if r > 100:
            return 'big'
        elif r > 10:
            return 'mid'
    return 'small'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
