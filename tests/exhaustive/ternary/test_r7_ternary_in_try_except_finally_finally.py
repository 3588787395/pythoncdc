import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInTryExceptFinallyFinally(ExhaustiveTestCase):
    """Bug R7: try-except-finally 中 finally ternary — 字节码不一致。

    原始:
        try:
            pass
        except E:
            pass
        finally:
            y = a if c else b
    缺陷: try-except-finally 三段结构，finally 块包含 ternary 赋值。
         R7-05 已测纯 try-finally + ternary in finally（try-finally
         被错误反编译为 try-except + ternary 重复）。R7 测 try-except-finally
         变体：except 块存在使异常处理路径更复杂，finally 块的 ternary
         归约可能与 R7-05 退化模式不同。
    """
    SOURCE_CODE = """try:
    pass
except E:
    pass
finally:
    y = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
