import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14WalrusTernarySubscr(ExhaustiveTestCase):
    # walrus 绑定三元结果后取 subscr：
    # if (x := a if c else b)[0] > 0:
    #     pass
    # 字节码含三元 merge_block（cond=c 选择 a / b），结果 COPY 给 walrus
    # 绑定 STORE_NAME x，再 LOAD_CONST 0 / BINARY_SUBSCR / LOAD_CONST 0
    # / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # walrus + ternary + subscr 三层组合在 if 条件中的栈归约。
    SOURCE_CODE = """if (x := a if c else b)[0] > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
