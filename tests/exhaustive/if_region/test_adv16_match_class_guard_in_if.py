import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchClassGuardInIf(ExhaustiveTestCase):
    # if 体内 match 类模式 + guard：
    # if c:
    #     match p:
    #         case Point(x=1, y=2) if z:
    #             pass
    #         case _:
    #             pass
    # 字节码 MATCH_CLASS + LOAD_NAME z / POP_JUMP_IF_FALSE / 反编译器
    # 在 if body 内 match 类模式 + guard 时的嵌套结构归约。
    SOURCE_CODE = """if c:
    match p:
        case Point(x=1, y=2) if z:
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
