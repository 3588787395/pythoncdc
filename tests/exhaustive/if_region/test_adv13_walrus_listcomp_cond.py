import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13WalrusListcompCond(ExhaustiveTestCase):
    # if 条件中 walrus 绑定列表推导式结果：
    # if (x := [i for i in range(10) if i > 5]):
    #     pass
    # 字节码含 BUILD_LIST 4 + LOAD_CONST (code object) + MAKE_FUNCTION
    # 后接 GET_ITER + FOR_ITER + 列表构造循环 + STORE_NAME x，最后 POP_JUMP_IF_FALSE。
    SOURCE_CODE = """if (x := [i for i in range(10) if i > 5]):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
