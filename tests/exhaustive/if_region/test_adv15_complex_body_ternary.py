import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15ComplexBodyTernary(ExhaustiveTestCase):
    # if 体内多条语句中夹有三元赋值，后续语句丢失：
    # if c:
    #     a = 1
    #     b = a if x else 2
    #     c = b + 1
    # 字节码在 if body 内顺序执行三条 STORE_NAME。反编译器在处理
    # 第二条（b = a if x else 2）的三元 merge 时，错误地将后续
    # 的 c = b + 1 语句丢弃，仅保留前两条赋值。第三条语句的
    # BINARY_OP + STORE_NAME c 完全从反编译输出中消失。
    SOURCE_CODE = """if c:
    a = 1
    b = a if x else 2
    c = b + 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
