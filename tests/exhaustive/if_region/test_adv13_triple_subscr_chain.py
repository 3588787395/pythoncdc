import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13TripleSubscrChain(ExhaustiveTestCase):
    # if 条件中三层 BINARY_SUBSCR 链 + 比较：
    # if d[a][b][c] > 0:
    #     pass
    # 字节码 LOAD_NAME d / LOAD_NAME a / BINARY_SUBSCR
    # / LOAD_NAME b / BINARY_SUBSCR
    # / LOAD_NAME c / BINARY_SUBSCR
    # / LOAD_CONST 0 / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # 多层 BINARY_SUBSCR 在 if 条件中的栈归约尚未充分测试。
    SOURCE_CODE = """if d[a][b][c] > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
