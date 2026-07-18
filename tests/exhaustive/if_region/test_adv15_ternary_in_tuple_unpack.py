import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryInTupleUnpack(ExhaustiveTestCase):
    # if 体内元组解包赋值，右值为两个三元组成的元组：
    # if c:
    #     a, b = (1 if x else 2), (3 if y else 4)
    # 字节码 LOAD_NAME c / 含三元 merge_block（cond=x 选择 1 / 2）
    # / 含三元 merge_block（cond=y 选择 3 / 4）/ BUILD_TUPLE 2
    # / SWAP / STORE_NAME a / STORE_NAME b。反编译器在处理两个
    # 三元 merge 与 BUILD_TUPLE + UNPACK 的归约时出错，将第一个
    # 三元变为独立语句（POP_TOP），第二个三元仅赋给 a，b 的赋值
    # 丢失，元组解包结构完全被破坏。
    SOURCE_CODE = """if c:
    a, b = (1 if x else 2), (3 if y else 4)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
