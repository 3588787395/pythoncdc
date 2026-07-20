import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR2TernaryInStoreSubscr(ExhaustiveTestCase):
    """Bug R2-20: ternary 作为 STORE_SUBSCR 的索引 — 字节码不一致。

    原始: lst[a if cond else 0] = value
    缺陷: ternary 作为 STORE_SUBSCR 的索引时，lst 在 ternary entry 之前被加载,
         value 在 ternary merge 之后被加载，然后 STORE_SUBSCR 同时消费三者。
         反编译器可能丢失整体结构。
    """
    SOURCE_CODE = """lst[a if cond else 0] = value"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
