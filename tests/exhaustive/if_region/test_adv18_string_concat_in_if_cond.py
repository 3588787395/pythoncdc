import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18StringConcatInIfCond(ExhaustiveTestCase):
    # if 条件含字符串拼接 `+` 与比较：
    # if 'a' + 'b' + 'c' == 'abc':
    #     r = 1
    # elif 'x' + 'y' == 'xy':
    #     r = 2
    # else:
    #     r = 3
    # 字节码 LOAD_CONST 'a' / LOAD_CONST 'b' / BINARY_OP + / LOAD_CONST 'c' /
    # BINARY_OP + / COMPARE_OP == / POP_JUMP_IF_FALSE / 反编译器在 if 条件中
    # 含多个字符串拼接时易把 BINARY_OP + 误归到 STORE_NAME。
    SOURCE_CODE = """if 'a' + 'b' + 'c' == 'abc':
    r = 1
elif 'x' + 'y' == 'xy':
    r = 2
else:
    r = 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
