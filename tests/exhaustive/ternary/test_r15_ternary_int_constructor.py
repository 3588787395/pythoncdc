import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryIntConstructor(ExhaustiveTestCase):
    """Bug R15 (new): int((a if c else b)) — int constructor 单 ternary 参数。

    原始:
        int((a if c else b))
    缺陷: ternary 作为内置 int() 的单参数（带括号）。cond_block preload 含
         PUSH_NULL + LOAD int，ternary merge 块栈顶由 PRECALL + CALL 1 消费。
         验证 int 内置构造函数 + ternary 单参数归约路径。
    """
    SOURCE_CODE = """int((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
