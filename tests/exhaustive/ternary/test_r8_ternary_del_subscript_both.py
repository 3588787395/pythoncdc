import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryDelSubscriptBoth(ExhaustiveTestCase):
    """Bug R8: del obj[ternary] 双 ternary 同块（base 与 key 都是 ternary）— 字节码不一致。

    原始:
        del (a if c1 else b)[x if c2 else y]
    缺陷: del 的 subscript 目标 base 与 key 都是 ternary。R7-04 已知
         `del obj[a if c else b]`（key 是 ternary）失败。R8 测 base 与
         key 都是 ternary 的极端变体：两个 ternary 的 entry/merge 块
         与 DELETE_SUBSCR 的栈消费 [obj, key] 顺序冲突，可能完全丢失
         del 结构或退化为多个表达式泄漏。
    """
    SOURCE_CODE = """del (a if c1 else b)[x if c2 else y]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
