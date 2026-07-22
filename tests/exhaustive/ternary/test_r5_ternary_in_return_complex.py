import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInReturnComplex(ExhaustiveTestCase):
    """Bug R5-18: return listcomp 含 ternary element — 字节码不一致。

    原始:
        def f():
            return [a if c else b for i in range(10)]
    缺陷: ternary 作为 listcomp element 时，LIST_APPEND 在内嵌 code object
         的 merge_block 中消费 ternary 结果。R2 已通过简单 listcomp 场景
         （test_r2_ternary_in_listcomp）。R5 用 return listcomp 形式加重
         嵌套 code object 复杂度。期望：Return(ListComp(elt=IfExp)) 正确归约。
    """
    SOURCE_CODE = """def f():
    return [a if c else b for i in range(10)]
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
