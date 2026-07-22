import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryLambdaMultiDefault(ExhaustiveTestCase):
    """Bug R16 (new): lambda x=(a if c else b), y=2: x — lambda multi-default ternary。

    原始:
        f = lambda x=(a if c else b), y=2: x
    缺陷: lambda 含两个默认参数，第一个默认值是 ternary。cond_block preload
         含 LOAD_CONST lambda code + BUILD_TUPLE 2 (defaults tuple) +
         MAKE_FUNCTION 1。R13 lambda_default 已测过单 ternary default，
         R16 测多 default + ternary 变体。
    """
    SOURCE_CODE = """f = lambda x=(a if c else b), y=2: x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
