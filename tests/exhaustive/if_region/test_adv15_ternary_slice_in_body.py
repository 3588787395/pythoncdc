import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernarySliceInBody(ExhaustiveTestCase):
    # if 体内切片的下界和上界均为三元表达式：
    # if c:
    #     x = lst[a if p else q:b if r else s]
    # 字节码 LOAD_NAME lst / 含三元 merge_block（cond=p 选择 a / q）
    # / 含三元 merge_block（cond=r 选择 b / s）/ BUILD_SLICE 2
    # / BINARY_SUBSCR / STORE_NAME x。反编译器未能将两个三元 merge
    # 归约到 BUILD_SLICE 的栈位，导致切片结构丢失，两个三元各自
    # 变为独立语句，且 x 的赋值变为仅取第二个三元的结果。
    SOURCE_CODE = """if c:
    x = lst[a if p else q:b if r else s]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
