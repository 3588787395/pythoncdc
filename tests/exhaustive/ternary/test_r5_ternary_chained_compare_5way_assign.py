import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryChainedCompare5WayAssign(ExhaustiveTestCase):
    """Bug R5-03: ternary 在 5-term chained compare 中段 + 赋值 — 字节码不一致。

    原始: r = 0 < (a if c else b) < 10 < 100 < 1000
    缺陷: R4-03 4-term 已知限制的极端扩展。5-term chained compare 需要多次
         COPY 2 + COMPARE_OP 链。期望：IfRegion 渲染 `r = 0 < ... < 1000` 赋值，
         当前疑似渲染为 `if (...): pass`（与 R4-03 同根因）。
    """
    SOURCE_CODE = """r = 0 < (a if c else b) < 10 < 100 < 1000"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
