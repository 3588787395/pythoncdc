import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryGenexpComplex(ExhaustiveTestCase):
    """Bug R6: ternary 在 genexp + filter 中 — 字节码不一致。

    原始: z = list(a if c else b for x in ys if x > 0)
    缺陷: genexp 中 ternary 作为 element + if filter。期望 genexp
         code object 内部 ternary 正确归约；当前疑似 genexp 的
         YIELD_VALUE 与 ternary merge 块交互产生归属冲突。
    """
    SOURCE_CODE = """z = list(a if c else b for x in ys if x > 0)"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
