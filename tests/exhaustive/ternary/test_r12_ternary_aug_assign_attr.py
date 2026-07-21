import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR12TernaryAugAssignAttr(ExhaustiveTestCase):
    """Bug R12 (new): x.attr += (a if c else b) — STORE_ATTR augassign rhs ternary。

    原始:
        x.attr += (a if c else b)
    缺陷: ternary 作为 augmented attribute assign 的右值。cond_block 前缀
         含 target 复制模板 LOAD x + COPY 1 + LOAD_ATTR attr（attr 形式），
         merge_block 含 BINARY_OP(+=) + SWAP 2 + STORE_ATTR。R8 已测过
         subscr 变体 (test_r8_ternary_aug_assign_subscr)；R12 测 attr 变体：
         attr 形式只有 1 个 SWAP，与 subscr 的 2 个 SWAP 不同。
    """
    SOURCE_CODE = """x.attr += (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
