import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13SliceEqSliceCompare(ExhaustiveTestCase):
    # if 条件中两个切片相等比较：
    # if d[a:b] == d[c:d]:
    #     pass
    # 字节码 LOAD_NAME d / LOAD_NAME a / LOAD_NAME b / BUILD_SLICE 2
    # / LOAD_NAME d / LOAD_NAME c / LOAD_NAME d / BUILD_SLICE 2
    # / COMPARE_OP == / POP_JUMP_IF_FALSE。
    # 两个 BUILD_SLICE 在 if 条件中需正确归约为切片字面量并参与 COMPARE_OP。
    SOURCE_CODE = """if d[a:b] == d[c:d]:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
