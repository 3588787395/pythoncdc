import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInSubscriptSlice(ExhaustiveTestCase):
    """Bug R5-15: ternary 在 subscript slice 上界 — 字节码不一致。

    原始: x[1:(a if c else b)]
    缺陷: ternary 作为 slice 上界时，BUILD_SLICE 在 merge_block 中消费
         ternary 结果作为 slice upper。R1 已通过简单 slice 场景
         （test_r1_ternary_in_slice）。R5 用显式 slice lower=1 + ternary upper
         形式重测。期望：Subscript(slice=Slice(lower=1, upper=IfExp)) 正确归约。
    """
    SOURCE_CODE = """x[1:(a if c else b)]"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
