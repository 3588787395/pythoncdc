import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR16TernaryWalrusSubscrIdx(ExhaustiveTestCase):
    """Bug R16 (new): x[(n := a if c else b)] — walrus in subscript with ternary。

    原始:
        x[(n := a if c else b)]
    缺陷: walrus 表达式捕获 ternary 结果作为 subscript 索引。
         cond_block 含 LOAD x + COPY + STORE_NAME n + ternary merge 块
         + BINARY_SUBSCR 消费链。R8 walrus_assign 已测 walrus(ternary)
         在赋值上下文，R16 测 walrus(ternary) 作为 subscript 索引。
    """
    SOURCE_CODE = """x[(n := a if c else b)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
