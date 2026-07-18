import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14MultidimTupleSlice(ExhaustiveTestCase):
    # 多维切片（tuple key）：
    # if d[a:b, c:d] > 0:
    #     pass
    # 字节码 LOAD_NAME d / LOAD_NAME a / LOAD_NAME b / BUILD_SLICE 2
    # / LOAD_NAME c / LOAD_NAME d / BUILD_SLICE 2
    # / BUILD_TUPLE 2 / BINARY_SUBSCR / LOAD_CONST 0
    # / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # 多维切片通过 BUILD_TUPLE 包装多个 slice 作为 subscr 的 key。
    SOURCE_CODE = """if d[a:b, c:d] > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
