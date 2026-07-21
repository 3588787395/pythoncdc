import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernaryZipArgs(ExhaustiveTestCase):
    """Bug R15 (new): zip((a if c else b), y) — zip 双参数，首个是 parenthesized ternary。

    原始:
        zip((a if c else b), y)
    缺陷: ternary 作为 zip 第一位置参数（带括号），y 作为第二位置参数。
         cond_block preload 含 PUSH_NULL + LOAD zip，ternary merge 块栈顶与
         LOAD y 一起 PRECALL + CALL 2。验证 zip 内置函数 + ternary 多参数归约。
    """
    SOURCE_CODE = """zip((a if c else b), y)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
