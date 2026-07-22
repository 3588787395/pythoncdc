import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryWhileCondComplexBody(ExhaustiveTestCase):
    """Bug R6: ternary 在 while 条件中 + 复杂 body (break/continue) — 字节码不一致。

    原始:
        while (a if c else b):
            if x:
                break
            continue
    缺陷: R5-07 已识别 while(ternary) + break 为已知限制。R6 用 break +
         continue 复合 body 加重复杂度，期望暴露 while-ternary 与
         break/continue 跳转指令交互的额外问题。
    """
    SOURCE_CODE = """while (a if c else b):
    if x:
        break
    continue
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
