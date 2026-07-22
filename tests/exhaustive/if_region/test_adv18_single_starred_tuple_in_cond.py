import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18SingleStarredTupleInCond(ExhaustiveTestCase):
    # if 条件含单星号 tuple `(*a,)`：
    # if (*a,):
    #     r = 1
    # else:
    #     r = 2
    # 字节码 BUILD_TUPLE_UNPACK_WITH_CALL / BUILD_TUPLE 1 + POP_JUMP_IF_FALSE
    # / 反编译器在 if 条件中处理 (*a,) 单星号 tuple 时易错识别为 *args 调用
    # 或丢失星号标记变为 (a,)。
    SOURCE_CODE = """if (*a,):
    r = 1
else:
    r = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
