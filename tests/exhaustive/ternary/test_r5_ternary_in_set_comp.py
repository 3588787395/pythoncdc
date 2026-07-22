import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInSetComp(ExhaustiveTestCase):
    """Bug R5-20: setcomp 含 ternary element — 字节码不一致。

    原始: s = {a if c else b for i in range(10)}
    缺陷: ternary 作为 setcomp element 时，SET_ADD 在内嵌 code object 的
         merge_block 中消费 ternary 结果。R2 已通过 set element 场景
         （test_r2_ternary_in_set）但非 setcomp 形式。R5 用 setcomp 形式重测。
         期望：SetComp(elt=IfExp) 正确归约。
    """
    SOURCE_CODE = """s = {a if c else b for i in range(10)}"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
