import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17ComplexIfElifNested(ExhaustiveTestCase):
    # if/elif 中嵌套 if/else 复杂结构：
    # if a:
    #     if b:
    #         x = 1
    #     else:
    #         x = 2
    # elif c:
    #     if d:
    #         x = 3
    # 字节码多层 POP_JUMP_IF_FALSE / 外层 elif 跳转 + 内层 if/else 跳转
    # / 反编译器在 if body 内嵌套 if/else + 外层 elif 组合时易丢失内层 else
    # 或错把内层 if 提升到与外层 elif 同级。
    SOURCE_CODE = """if a:
    if b:
        x = 1
    else:
        x = 2
elif c:
    if d:
        x = 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
