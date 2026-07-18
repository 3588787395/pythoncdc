import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16NestedWalrusChain(ExhaustiveTestCase):
    # 三层嵌套 walrus 直接作 if 条件：
    # if (x := (y := (z := a))):
    #     pass
    # 字节码 LOAD_NAME a / COPY / STORE_NAME z / COPY / STORE_NAME y /
    # COPY / STORE_NAME x / POP_JUMP_IF_FALSE。
    # 嵌套 walrus 的多个 COPY/STORE 链在归约时易错乱绑定顺序。
    SOURCE_CODE = """if (x := (y := (z := a))):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
