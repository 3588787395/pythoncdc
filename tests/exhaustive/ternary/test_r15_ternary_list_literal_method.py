import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryListLiteralMethod(ExhaustiveTestCase):
    """Bug R15 (new): [].append((a if c else b)) — list literal obj.method。

    原始:
        [].append((a if c else b))
    缺陷: ternary 作为 list literal [].append() 的参数。cond_block preload 含
         BUILD_LIST 0 + LOAD_METHOD append，ternary merge 块栈顶由 PRECALL +
         CALL 1 消费。验证 list literal obj + LOAD_METHOD + ternary 模式。
    """
    SOURCE_CODE = """[].append((a if c else b))
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
