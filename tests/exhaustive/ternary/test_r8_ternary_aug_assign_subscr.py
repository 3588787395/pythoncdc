import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryAugAssignSubscr(ExhaustiveTestCase):
    """Bug R8: subscr augassign rhs 是 ternary — 字节码不一致。

    原始:
        d[k] += (a if c else b)
    缺陷: subscript 的 augassign 右值是 ternary。R3/R6 已测过
         ternary augassign 简单变量变体。R8 测 subscr target 变体：
         COPY 2 + COPY 2 + BINARY_SUBSCR 模板与 ternary merge 块的
         BINARY_OP + SWAP + STORE_SUBSCR 栈顺序可能冲突。
    """
    SOURCE_CODE = """d[k] += (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
