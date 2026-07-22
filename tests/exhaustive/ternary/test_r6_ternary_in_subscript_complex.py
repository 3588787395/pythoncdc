import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryInSubscriptComplex(ExhaustiveTestCase):
    """Bug R6: 多个 ternary 在嵌套 subscript 赋值中 — 字节码不一致。

    原始: x[a if c else b][d if e else f] = 1
    缺陷: 嵌套 subscript 赋值，两层 subscript index 均为 ternary。期望
         两个 TernaryRegion 均正确归约并被同一 SubscriptStore 引用；
         当前疑似 STORE_SUBSCR 出口与多个 TernaryRegion merge 块共享。
    """
    SOURCE_CODE = """x[a if c else b][d if e else f] = 1"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
