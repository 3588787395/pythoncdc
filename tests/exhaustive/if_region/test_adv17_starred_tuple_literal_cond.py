import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17StarredTupleLiteralCond(ExhaustiveTestCase):
    # 双星号解包 tuple 字面量作 if 条件：
    # if (*a, *b):
    #     pass
    # 字节码 BUILD_TUPLE_UNPACK_WITH_CALL / BUILD_TUPLE + POP_JUMP_IF_FALSE
    # / 反编译器在 if 条件中处理 (*a, *b) 这种纯星号解包 tuple 字面量时
    # 易错识别为函数调用 *args，或丢失星号标记变为 (a, b)。
    SOURCE_CODE = """if (*a, *b):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
