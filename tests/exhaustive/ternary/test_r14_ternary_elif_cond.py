import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryElifCond(ExhaustiveTestCase):
    """Bug R14 (new): if x: pass elif (a if c else b): pass — elif 条件是 ternary。

    原始:
        if x:
            pass
        elif (a if c else b):
            pass
    缺陷: elif 条件本身是 ternary。ternary merge 块的栈顶输出作为 elif 分支条件
         （POP_JUMP_IF_FALSE 跳过 elif body）。R3 测过 ternary_in_cond (if 条件
         是 ternary)，R3 测过 ternary_while_cond (while 条件是 ternary)。R14 测
         elif 变体：elif 分支入口前的 ternary merge 块与 IfRegion 的 elif 链结构
         可能出现归属冲突。
    """
    SOURCE_CODE = """if x:
    pass
elif (a if c else b):
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
