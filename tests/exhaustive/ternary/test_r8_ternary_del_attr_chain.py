import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryDelAttrChain(ExhaustiveTestCase):
    """Bug R8: del obj[ternary].attr — ternary 作为 del subscript 后链式 attr — 字节码不一致。

    原始:
        del obj[a if c else b].attr
    缺陷: del 的目标是 obj[ternary].attr 链式访问。R7-04 已知
         `del obj[ternary]` 失败。R8 测链式 attr 变体：DELETE_ATTR
         在 merge_block 消费 LOAD_ATTR，前者消费 obj[ternary] 的
         BINARY_SUBSCR 结果，三元 merge 块与 DELETE_ATTR 的栈消费
         顺序可能冲突。
    """
    SOURCE_CODE = """del obj[a if c else b].attr
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
