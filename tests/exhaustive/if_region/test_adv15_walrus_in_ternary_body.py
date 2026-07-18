import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15WalrusInTernaryBody(ExhaustiveTestCase):
    # if 体内赋值右值为 walrus 绑定三元结果后参与二元运算：
    # if c:
    #     x = (y := a if p else b) + 1
    # 字节码 LOAD_NAME c / 含三元 merge_block（cond=p 选择 a / b）
    # / COPY / STORE_NAME y / LOAD_CONST 1 / BINARY_OP +
    # / STORE_NAME x。反编译器在归约 walrus COPY + STORE_NAME y
    # 与三元 merge 时出错，将 + 1 / STORE_NAME x 后续部分丢弃，
    # 仅保留 y = (a if p else b)，x 的赋值和加法运算完全消失。
    SOURCE_CODE = """if c:
    x = (y := a if p else b) + 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
