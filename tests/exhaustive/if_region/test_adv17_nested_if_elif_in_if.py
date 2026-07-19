import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17NestedIfElifInIf(ExhaustiveTestCase):
    # if 体内嵌套 if/elif 结构：
    # if a:
    #     if b:
    #         x = 1
    #     elif c:
    #         x = 2
    # 字节码 POP_JUMP_IF_FALSE 链 + 内层 elif 跳转 / 反编译器在
    # if body 内识别内层 elif 时易与外层 if 的 fallthrough 混淆。
    SOURCE_CODE = """if a:
    if b:
        x = 1
    elif c:
        x = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
