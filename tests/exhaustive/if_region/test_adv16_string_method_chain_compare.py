import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16StringMethodChainCompare(ExhaustiveTestCase):
    # 字符串字面量方法调用 + 字符串字面量比较：
    # if "abc".upper() == "ABC":
    #     pass
    # 字节码 LOAD_CONST "abc" / LOAD_METHOD upper / PRECALL/CALL /
    # LOAD_CONST "ABC" / COMPARE_OP == / POP_JUMP_IF_FALSE。
    # 反编译器在字符串字面量作 method receiver 时易丢失方法调用。
    SOURCE_CODE = """if "abc".upper() == "ABC":
    pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
