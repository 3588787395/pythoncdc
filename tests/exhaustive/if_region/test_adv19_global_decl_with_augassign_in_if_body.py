import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19GlobalDeclWithAugassignInIfBody(ExhaustiveTestCase):
    # if body 内含 global 声明 + augassign + 后续读取：
    # x = 10
    # def f(flag):
    #     if flag:
    #         global x
    #         x += 5
    #         x = x * 2
    #         return x
    #     return -1
    # 字节码 LOAD_GLOBAL / STORE_GLOBAL / BINARY_OP
    # / 反编译器在 if body 内 global 声明 + 多次赋值时易丢失 global 声明或赋值。
    SOURCE_CODE = """x = 10
def f(flag):
    if flag:
        global x
        x += 5
        x = x * 2
        return x
    return -1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
