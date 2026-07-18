import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14TernaryInSetLiteral(ExhaustiveTestCase):
    # 三元作集合字面量元素：
    # if {a if c else b, d}:
    #     pass
    # 字节码含三元 merge_block（cond=c 选择 a / b），与 LOAD_NAME d
    # / BUILD_SET 2 / POP_JUMP_IF_FALSE。
    # 三元结果与普通元素一起构成 set，整个 set 作 if 条件。
    SOURCE_CODE = """if {a if c else b, d}:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
