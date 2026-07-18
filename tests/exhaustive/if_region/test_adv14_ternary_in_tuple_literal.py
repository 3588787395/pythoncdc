import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14TernaryInTupleLiteral(ExhaustiveTestCase):
    # 三元作元组字面量元素，整个元组作条件：
    # if (a if c else b, d):
    #     pass
    # 字节码含三元 merge_block（cond=c 选择 a / b），与 LOAD_NAME d
    # / BUILD_TUPLE 2 / POP_JUMP_IF_FALSE。
    # 三元结果与普通元素一起构成 tuple，整个 tuple 作 if 条件。
    SOURCE_CODE = """if (a if c else b, d):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
