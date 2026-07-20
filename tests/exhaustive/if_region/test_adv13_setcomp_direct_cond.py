import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13SetcompDirectCond(ExhaustiveTestCase):
    # if 条件中直接使用集合推导式（含 filter）：
    # if {x for x in y if x > 0}:
    #     pass
    # 字节码含 BUILD_SET 0 + LOAD_CONST <setcomp code object> + MAKE_FUNCTION
    # + GET_ITER + FOR_ITER + LOAD_FAST x / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE
    # / SET_ADD 循环。filter (if x > 0) 在嵌套 code object 中体现为 COMPARE_OP + 条件跳转。
    SOURCE_CODE = """if {x for x in y if x > 0}:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
