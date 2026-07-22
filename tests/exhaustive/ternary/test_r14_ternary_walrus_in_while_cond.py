import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryWalrusInWhileCond(ExhaustiveTestCase):
    """Bug R14 (new): while (n := (a if c else b)) > 0: pass — while 条件 walrus + ternary。

    原始:
        while (n := (a if c else b)) > 0:
            pass
    缺陷: while 条件是 walrus 表达式，walrus 表达式 value 是 ternary。R2 已测过
         walrus_in_cond (if 条件 walrus ternary)。R14 测 while 变体：while
         polling 循环 + walrus + ternary 三层嵌套，merge 块栈顶先经 STORE_NAME n
         (walrus) 再经 COMPARE_OP + POP_JUMP_IF_FALSE 跳回 while 顶。
    """
    SOURCE_CODE = """while (n := (a if c else b)) > 0:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
