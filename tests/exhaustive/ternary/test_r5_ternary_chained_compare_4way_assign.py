import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryChainedCompare4WayAssign(ExhaustiveTestCase):
    """Bug R5-02: ternary 在 4-term chained compare 中段 + 赋值（R4-03 复现）。

    原始: r = 0 < (a if c else b) < 10 < 100
    缺陷: R4-03 已识别为已知限制：chained compare 表达式已正确构建为
         `0 < IfExp < 10 < 100`，但 IfRegion 仍渲染为 `if (...): pass` 而非 `r = ...`。
         需调整 IfRegion chained compare + Assign 边界（STORE_NAME(r) 应触发 Assign）。
         R5 用变量名 c 替代 cond 重测以确认 R4-03 仍未修复。
    """
    SOURCE_CODE = """r = 0 < (a if c else b) < 10 < 100"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
