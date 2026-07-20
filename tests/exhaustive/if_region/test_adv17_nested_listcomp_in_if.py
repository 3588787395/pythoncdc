import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17NestedListcompInIf(ExhaustiveTestCase):
    # if 体内嵌套 listcomp 赋值（无 walrus）：
    # if c:
    #     r = [[i for i in range(j)] for j in range(3)]
    # 字节码 BUILD_LIST + FOR_ITER 嵌套 + LIST_APPEND 双层
    # / 反编译器在 if body 内嵌套 listcomp 时易把内层 listcomp 错写为
    # 单层多 for listcomp，或丢失内层的 BUILD_LIST 边界。
    SOURCE_CODE = """if c:
    r = [[i for i in range(j)] for j in range(3)]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
