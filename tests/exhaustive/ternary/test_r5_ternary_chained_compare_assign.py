import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryChainedCompareAssign(ExhaustiveTestCase):
    """Bug R5-01: ternary 在 3-term chained compare 中段 + 赋值 — 字节码不一致。

    原始: r = 0 < (a if c else b) < 10
    缺陷: R4-03 已识别 4-term chained compare 为已知限制（表达式已正确构建
         但 IfRegion 渲染为 if-语句而非赋值）。R5 用 3-term 简化场景重测，
         分离 chained compare 中段 ternary + STORE_NAME(r) 赋值的根因。
         期望：IfRegion 应识别 merge_block 的 STORE_NAME(r) 触发 Assign
         而非 if 语句；当前疑似未识别。
    """
    SOURCE_CODE = """r = 0 < (a if c else b) < 10"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
