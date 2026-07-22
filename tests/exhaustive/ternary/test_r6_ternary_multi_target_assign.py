import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR6TernaryMultiTargetAssign(ExhaustiveTestCase):
    """Bug R6: ternary 在多目标赋值中 — 字节码不一致。

    原始: x = y = a if c else b
    缺陷: 多目标赋值 (x = y = ...) 在字节码中产生多个 STORE_NAME 指令，
         期望 ternary merge 块正确识别多 STORE 链；当前疑似只识别第一个
         STORE_x，丢失 STORE_y。
    """
    SOURCE_CODE = """x = y = a if c else b"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
