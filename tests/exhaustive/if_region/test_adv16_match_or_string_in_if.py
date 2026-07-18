import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchOrStringInIf(ExhaustiveTestCase):
    # if 体内 match 字符串字面量 or 模式：
    # if c:
    #     match s:
    #         case "a" | "b":
    #             pass
    #         case _:
    #             pass
    # 字节码 LOAD_NAME s / 多个 COMPARE_OP == / POP_JUMP_IF_TRUE / 反编译器
    # 在 if body 内 match 字符串字面量 or 模式时的结构归约。
    SOURCE_CODE = """if c:
    match s:
        case "a" | "b":
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
