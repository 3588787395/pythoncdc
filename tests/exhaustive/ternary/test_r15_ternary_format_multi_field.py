import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryFormatMultiField(ExhaustiveTestCase):
    """Bug R15 (new): "{} {}".format((a if c else b), x) — str.format 多字段。

    原始:
        "{} {}".format((a if c else b), x)
    缺陷: ternary 作为 str.format 第一位置参数（带括号），后跟 x 作为第二参数。
         cond_block preload 含 LOAD_CONST "{} {}" + LOAD_ATTR format，ternary
         merge 块栈顶与 LOAD x 一起 PRECALL + CALL 2。R4 已测 str.format 双
         ternary 双参数，R15 测单 ternary + sibling Name 变体。
    """
    SOURCE_CODE = '''"{} {}".format((a if c else b), x)
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
