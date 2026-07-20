import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchClassWildcardPosInIf(ExhaustiveTestCase):
    # if 体内 match 类模式带通配符位置参数（_）：
    # if c:
    #     match p:
    #         case Point(_, _):
    #             pass
    #         case _:
    #             pass
    # 字节码 MATCH_CLASS 2 / 反编译器在 if body 内
    # match 类模式带 _ 通配符位置参数时的结构归约。
    SOURCE_CODE = """if c:
    match p:
        case Point(_, _):
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
