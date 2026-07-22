import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR7TernaryInWhileElse(ExhaustiveTestCase):
    """Bug R7: while-else 中 ternary 赋值（带 break 上下文）— 字节码不一致。

    原始:
        while x:
            if y:
                break
        else:
            z = a if c else b
    缺陷: while-else + break 结构中，else 块只在循环正常退出（无 break）
         时执行，其中包含 ternary 赋值。R6 已测简单 while-else + ternary
         (test_r6_ternary_while_else_ternary)。R7 加入 break 上下文，
         使 else 块的入口（JUMP_FORWARD 跳过 else vs 跳入 else）与
         ternary entry 的归属关系更复杂。
    """
    SOURCE_CODE = """while x:
    if y:
        break
else:
    z = a if c else b
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
