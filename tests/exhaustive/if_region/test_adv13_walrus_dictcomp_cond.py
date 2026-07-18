import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13WalrusDictcompCond(ExhaustiveTestCase):
    # if 条件中 walrus 绑定字典推导式结果：
    # if (x := {k: v for k, v in items}):
    #     pass
    # 字节码 BUILD_MAP 0 + LOAD_CONST <dictcomp code object> + MAKE_FUNCTION
    # + GET_ITER + FOR_ITER + UNPACK_SEQUENCE 2 / STORE_FAST k / STORE_FAST v
    # / MAP_ADD 循环 / COPY / STORE_NAME x / POP_JUMP_IF_FALSE。
    SOURCE_CODE = """if (x := {k: v for k, v in items}):
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
