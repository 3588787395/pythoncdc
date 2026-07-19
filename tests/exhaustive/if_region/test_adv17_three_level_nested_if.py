import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17ThreeLevelNestedIf(ExhaustiveTestCase):
    # if 体内三层嵌套 if（无 else 分支）：
    # if a:
    #     if b:
    #         if c:
    #             x = 1
    # 字节码多层 POP_JUMP_IF_FALSE / 反编译器在 if body 内
    # 处理连续多层无 else 的 if 嵌套时易错把内层 if 提升或合并。
    SOURCE_CODE = """if a:
    if b:
        if c:
            x = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
