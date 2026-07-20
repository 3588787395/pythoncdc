import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchGuardInIf(ExhaustiveTestCase):
    # if 体内 match 带 guard（case 后跟 if 守卫）：
    # if c:
    #     match x:
    #         case 1 if y > 0:
    #             pass
    #         case _:
    #             pass
    # 字节码 MATCH / POP_JUMP_IF_FALSE / LOAD_NAME y / LOAD_CONST 0 /
    # COMPARE_OP > / POP_JUMP_IF_FALSE / 反编译器在 if body 内
    # match + guard 时的嵌套控制流归约。
    SOURCE_CODE = """if c:
    match x:
        case 1 if y > 0:
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
