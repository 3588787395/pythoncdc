import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14TernarySliceOperand(ExhaustiveTestCase):
    # 三元作切片操作数（左值 base）：
    # if (a if c else b)[0:5] > 0:
    #     pass
    # 字节码含三元 merge_block（cond=c 选择 a / b），结果作 BINARY_SUBSCR
    # 的 base，LOAD_CONST 0 / LOAD_CONST 5 / BUILD_SLICE 2 / BINARY_SUBSCR
    # / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # 三元结果作为切片的 base，反编译器需正确合并。
    SOURCE_CODE = """if (a if c else b)[0:5] > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
