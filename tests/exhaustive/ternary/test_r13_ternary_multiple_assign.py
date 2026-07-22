import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR13TernaryMultipleAssign(ExhaustiveTestCase):
    """Bug R13 (new): x = y = (a if c else b) — multiple assignment ternary。

    原始:
        x = y = (a if c else b)
    缺陷: ternary 作为 multiple assignment (x = y = expr) 的右值。
         字节码：TERNARY merge 后 SWAP 2 + STORE_NAME y + STORE_NAME x
         （两个 STORE_NAME 共享同一 expr 栈顶）。R2 已测 ternary_in_multi_target
         （test_r2_ternary_in_multi_target_assign），R13 重测相同模式作为基线
         验证 R12 修复无退化。
    """
    SOURCE_CODE = """x = y = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
