import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryStrFormatFieldAccess(ExhaustiveTestCase):
    """Bug R15 (new): "{0.x}".format(a if c else b) — str.format field access。

    原始:
        "{0.x}".format(a if c else b)
    缺陷: ternary 作为 str.format 单参数（不带括号），格式串含字段访问 {0.x}。
         cond_block preload 含 LOAD_CONST "{0.x}" + LOAD_ATTR format，ternary
         merge 块栈顶由 PRECALL + CALL 1 消费。验证 str 字面量 .format
         (ternary) 单参数变体（无 sibling）。
    """
    SOURCE_CODE = '''"{0.x}".format(a if c else b)
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
