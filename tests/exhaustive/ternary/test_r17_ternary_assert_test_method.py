import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR17TernaryAssertTestMethod(ExhaustiveTestCase):
    """Bug R17-11: assert (a if c else b).method() — assert test is ternary with method call。

    原始:
        assert (a if c else b).method()
    缺陷: assert 语句的 test 表达式是 ternary.method()。ternary 的 merge 块
         栈顶经 LOAD_METHOD method + PRECALL + CALL 后作为 assert test。
         AssertRegion 的 LOAD_ASSERTION_ERROR 块与 TernaryRegion 的 merge 块
         协调失败，反编译用 LOAD_NAME 替代 LOAD_ASSERTION_ERROR，字节码
         操作码不匹配 (LOAD_ASSERTION_ERROR vs LOAD_NAME)。
    """
    SOURCE_CODE = """assert (a if c else b).method()
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
