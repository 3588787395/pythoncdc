import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR15TernarySubscriptOnConstant(ExhaustiveTestCase):
    """Bug R15 (new): "abc"[a if c else b] — subscript on str constant with ternary index。

    原始:
        "abc"[a if c else b]
    缺陷: ternary 作为 subscript 索引，被 subscript 的对象是 str 字面量 "abc"。
         cond_block preload 含 LOAD_CONST "abc"，ternary merge 块栈顶作为
         BINARY_SUBSCR 的索引。R4 ternary_in_subscript_slice 已测切片变体，
         R15 测常量 subscript obj + ternary index 变体。
    """
    SOURCE_CODE = '''"abc"[a if c else b]
'''
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
