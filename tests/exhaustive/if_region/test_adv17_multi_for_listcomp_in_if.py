import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17MultiForListcompInIf(ExhaustiveTestCase):
    # if 体内多 for 子句 listcomp 赋值（无 filter）：
    # if c:
    #     r = [i * j for i in range(3) for j in range(3)]
    # 字节码 BUILD_LIST + 多层 FOR_ITER + LIST_APPEND
    # / 反编译器在 if body 内多 for listcomp 时易把第二个 for 错写为
    # 嵌套 listcomp，或丢失某个 for 子句的迭代变量。
    SOURCE_CODE = """if c:
    r = [i * j for i in range(3) for j in range(3)]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
