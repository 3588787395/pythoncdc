import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18LongElifChain5(ExhaustiveTestCase):
    # 5-elif 长链（共 6 分支 + else）：
    # def f(x):
    #     if x == 1:
    #         r = 'a'
    #     elif x == 2:
    #         r = 'b'
    #     elif x == 3:
    #         r = 'c'
    #     elif x == 4:
    #         r = 'd'
    #     elif x == 5:
    #         r = 'e'
    #     elif x == 6:
    #         r = 'f'
    #     else:
    #         r = 'z'
    # 字节码 6 个 POP_JUMP_IF_FALSE + JUMP_FORWARD 链 / 反编译器在长 elif
    # 链（>4 个 elif）时可能在第 5+ 个 elif 处退化为独立 if 或丢失 else。
    SOURCE_CODE = """def f(x):
    if x == 1:
        r = 'a'
    elif x == 2:
        r = 'b'
    elif x == 3:
        r = 'c'
    elif x == 4:
        r = 'd'
    elif x == 5:
        r = 'e'
    elif x == 6:
        r = 'f'
    else:
        r = 'z'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
