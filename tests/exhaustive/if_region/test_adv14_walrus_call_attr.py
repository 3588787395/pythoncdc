import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv14WalrusCallAttr(ExhaustiveTestCase):
    # walrus 绑定 call 结果后取属性参与比较：
    # if (x := f(a, b)).field > 0:
    #     pass
    # 字节码 LOAD_NAME f / LOAD_NAME a / LOAD_NAME b / CALL_FUNCTION 2
    # / COPY / STORE_NAME x / LOAD_ATTR field / LOAD_CONST 0
    # / COMPARE_OP > / POP_JUMP_IF_FALSE。
    # walrus 绑定的 CALL 结果需要先 STORE 再 LOAD_ATTR，栈上 COPY 与
    # 后续 LOAD_ATTR 的归约顺序容易出错。
    SOURCE_CODE = """if (x := f(a, b)).field > 0:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
