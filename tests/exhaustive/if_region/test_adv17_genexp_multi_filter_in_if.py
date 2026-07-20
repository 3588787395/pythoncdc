import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17GenexpMultiFilterInIf(ExhaustiveTestCase):
    # if 体内 genexp 多 filter 调用：
    # if c:
    #     r = sum(i for i in range(10) if i > 5 if i < 8)
    # 字节码 GEN_START + FOR_ITER + 多 POP_JUMP_IF_FALSE 链 + GEN_RETURN
    # / 反编译器在 if body 内多 filter genexp 时易把第二个 if 误归并到
    # 第一个 if 的条件，或丢失某个 filter 的 POP_JUMP_IF_FALSE。
    SOURCE_CODE = """if c:
    r = sum(i for i in range(10) if i > 5 if i < 8)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
