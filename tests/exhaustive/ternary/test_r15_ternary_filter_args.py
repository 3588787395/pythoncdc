import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryFilterArgs(ExhaustiveTestCase):
    """Bug R15 (new): filter(f, (a if c else b)) — filter 双参数，第二是 ternary。

    原始:
        filter(f, (a if c else b))
    缺陷: ternary 作为 filter 第二位置参数（带括号），f 作为第一位置参数。
         cond_block preload 含 PUSH_NULL + LOAD filter + LOAD f，ternary merge
         块栈顶由 PRECALL + CALL 2 消费。与 map 同模式但 filter 是不同内置。
    """
    SOURCE_CODE = """filter(f, (a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
