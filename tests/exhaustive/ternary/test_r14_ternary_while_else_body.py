import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryWhileElseBody(ExhaustiveTestCase):
    """Bug R14 (new): while else: y = (a if c else b) — while-else 体含 ternary。

    原始:
        while x:
            pass
        else:
            y = (a if c else b)
    缺陷: while 循环的 else 块体含 ternary 赋值。R7 while_else 测过 while-else
         + ternary。R14 重测确认 R13 修复无退化，并测 while-else body 中 ternary
         直接赋值变体：while polling 结束后 JUMP_FORWARD 到 else 块，ternary region
         在 else 块入口可能与 while-loop region 边界冲突。
    """
    SOURCE_CODE = """while x:
    pass
else:
    y = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
