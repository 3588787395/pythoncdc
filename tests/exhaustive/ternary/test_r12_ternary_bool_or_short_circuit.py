import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryBoolOrShortCircuit(ExhaustiveTestCase):
    """Bug R12 (new): x or (a if c else b) — bool op 短路消费 ternary。

    原始:
        r = x or (a if c else b)
    缺陷: ternary 在 or 短路右侧。CPython 编译 `x or (ternary)` 为：
         LOAD x, COPY 1, POP_JUMP_IF_TRUE -> exit, POP_TOP, <ternary>,
         exit: STORE r
         ternary 的 cond_block 之前还有 COPY 1 + POP_JUMP_IF_TRUE + POP_TOP
         （or 短路基础设施）。ternary 识别可能误吞 or 短路块或反之。
         R2 已测 ternary 在 bool op 链 (test_r2_ternary_with_boolop)，
         R12 测 x or (ternary) 单 or 短路变体。
    """
    SOURCE_CODE = """r = x or (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
