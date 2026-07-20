import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryListcompComplex(ExhaustiveTestCase):
    """Bug R6: ternary 在 listcomp + filter 中 — 字节码不一致。

    原始: z = [a if c else b for x in ys if x > 0]
    缺陷: listcomp 中 ternary 作为 element + if filter。期望 listcomp
         code object 内部 ternary 正确归约；当前疑似 listcomp filter 的
         POP_JUMP_IF_FALSE 与 ternary cond 的 POP_JUMP_IF_FALSE 共享块。
    """
    SOURCE_CODE = """z = [a if c else b for x in ys if x > 0]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
