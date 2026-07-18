import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13DictcompDirectCond(ExhaustiveTestCase):
    # if 条件中直接使用字典推导式：
    # if {k: v for k, v in items}:
    #     pass
    # 字节码 BUILD_MAP 0 + LOAD_CONST <dictcomp code object> + MAKE_FUNCTION
    # + GET_ITER + FOR_ITER + UNPACK_SEQUENCE 2 / STORE_FAST k / STORE_FAST v
    # / MAP_ADD 循环。嵌套 code object 内含 UNPACK_SEQUENCE 与 MAP_ADD。
    SOURCE_CODE = """if {k: v for k, v in items}:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
