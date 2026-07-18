import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv13TernaryInListcompCond(ExhaustiveTestCase):
    # if 条件中列表推导式内部包含三元表达式作为元素：
    # if [a if c else b for x in y]:
    #     pass
    # 字节码 BUILD_LIST 0 + LOAD_CONST <listcomp code object> + MAKE_FUNCTION
    # + GET_ITER + FOR_ITER + LOAD_NAME c / POP_JUMP_IF_FALSE / LOAD_NAME a
    # / JUMP / LOAD_NAME b / LIST_APPEND 循环。
    # 三元在嵌套 listcomp code object 内部，反编译器需正确重建 ternary 元素。
    SOURCE_CODE = """if [a if c else b for x in y]:
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
