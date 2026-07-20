import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17ElseNestedIfElse(ExhaustiveTestCase):
    # if 的 else 分支内嵌套 if/else：
    # if a:
    #     x = 1
    # else:
    #     if b:
    #         y = 2
    #     else:
    #         z = 3
    # 字节码外层 POP_JUMP_IF_FALSE 跳到 else / else 内再嵌套 POP_JUMP_IF_FALSE
    # / 反编译器在 else body 内识别嵌套 if/else 时易将内层 else 误归到外层。
    SOURCE_CODE = """if a:
    x = 1
else:
    if b:
        y = 2
    else:
        z = 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
