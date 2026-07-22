import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryBytesModFormat(ExhaustiveTestCase):
    """Bug R15 (new): b"%s" % (a if c else b) — bytes % 格式化。

    原始:
        b"%s" % (a if c else b)
    缺陷: ternary 作为 bytes % 格式化的参数。R2 已测 str % 格式化，R15 测
         bytes % 变体。cond_block preload 含 LOAD_CONST b"%s"，ternary merge
         块栈顶由 BINARY_OP(%) 消费。
    """
    SOURCE_CODE = '''b"%s" % (a if c else b)
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
