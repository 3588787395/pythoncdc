import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19TryExceptElseFinallyInIfBody(ExhaustiveTestCase):
    # if body 内含完整 try-except-else-finally 四子句：
    # def f(x):
    #     if x > 0:
    #         result = None
    #         try:
    #             r = risky(x)
    #         except ValueError as e:
    #             result = ('err', e)
    #         else:
    #             result = ('ok', r)
    #         finally:
    #             cleanup(result)
    #         return result
    #     return None
    # 字节码 SETUP_FINALLY / SETUP_EXCEPT / PUSH_EXC_INFO / RERAISE
    # / 反编译器在 if body 内完整 4 子句 try 时易丢失 else 或 finally 子句。
    SOURCE_CODE = """def f(x):
    if x > 0:
        result = None
        try:
            r = risky(x)
        except ValueError as e:
            result = ('err', e)
        else:
            result = ('ok', r)
        finally:
            cleanup(result)
        return result
    return None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
