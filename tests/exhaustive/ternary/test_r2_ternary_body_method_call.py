import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryBodyMethodCall(ExhaustiveTestCase):
    """Bug R2-40: ternary body/orelse 是方法调用 — 字节码不一致。

    原始: x = obj.method() if cond else other
    缺陷: ternary body 是方法调用 obj.method() 时，true_value_block 含
         LOAD_NAME obj + LOAD_METHOD + PRECALL + CALL 序列。
         _is_single_expression_block 应允许此模式。
    """
    SOURCE_CODE = """x = obj.method() if cond else other"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
