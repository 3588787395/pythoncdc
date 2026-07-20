import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchOrPatternInIf(ExhaustiveTestCase):
    # if 体内 match 语句带 or 模式：
    # if c:
    #     match x:
    #         case 1 | 2:
    #             pass
    #         case _:
    #             pass
    # 字节码 PUSH_NULL / LOAD_NAME c / POP_JUMP_IF_FALSE / LOAD_NAME x /
    # MATCH_CLASS ... / 反编译器在 if body 内 match + or pattern 时的结构归约。
    # match 语句作为 if body 的子语句的反编译。
    SOURCE_CODE = """if c:
    match x:
        case 1 | 2:
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
