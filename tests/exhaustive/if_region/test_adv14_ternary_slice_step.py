import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14TernarySliceStep(ExhaustiveTestCase):
    # 三元作切片的 step：
    # if a[1:10:(b if c else 2)] > 0:
    #     pass
    # 字节码 LOAD_NAME a / LOAD_CONST 1 / LOAD_CONST 10
    # / 含三元 merge_block（cond=c 选择 b / LOAD_CONST 2）/ BUILD_SLICE 3
    # / BINARY_SUBSCR / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # 三元作切片的 step，反编译器需正确合并到切片内。
    SOURCE_CODE = """if a[1:10:(b if c else 2)] > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
