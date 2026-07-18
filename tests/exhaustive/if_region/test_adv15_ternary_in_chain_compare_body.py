import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15TernaryInChainCompareBody(ExhaustiveTestCase):
    # if 体内链式比较的中间操作数为三元表达式：
    # if c:
    #     z = 0 < (a if p else b) < 10
    # 字节码 LOAD_CONST 0 / 含三元 merge_block（cond=p 选择 a / b）
    # / SWAP / COPY / COMPARE_OP < / JUMP_IF_FALSE_OR_POP
    # / LOAD_CONST 10 / COMPARE_OP < / SWAP / POP_TOP / STORE_NAME z。
    # 反编译器未能将三元 merge 归约到链式比较的中间栈位，导致
    # 链式比较结构丢失，三元变为独立语句，10 也变为独立表达式
    # 语句，z 的赋值完全消失。
    SOURCE_CODE = """if c:
    z = 0 < (a if p else b) < 10"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
