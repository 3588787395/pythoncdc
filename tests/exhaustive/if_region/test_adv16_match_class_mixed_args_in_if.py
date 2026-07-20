import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchClassMixedArgsInIf(ExhaustiveTestCase):
    # if 体内 match 类模式带混合位置 + 关键字参数：
    # if c:
    #     match p:
    #         case Point(1, y=2):
    #             pass
    #         case _:
    #             pass
    # 字节码 MATCH_CLASS / 反编译器在 if body 内
    # match 类模式混合 positional + keyword args 时的结构归约。
    SOURCE_CODE = """if c:
    match p:
        case Point(1, y=2):
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
