import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16MatchMappingPatternInIf(ExhaustiveTestCase):
    # if 体内 match 映射模式带 **rest：
    # if c:
    #     match d:
    #         case {"k": v, **rest}:
    #             pass
    #         case _:
    #             pass
    # 字节码 MATCH_MAPPING / 反编译器在 if body 内
    # match 映射模式 + **rest 时的结构归约。
    SOURCE_CODE = """if c:
    match d:
        case {"k": v, **rest}:
            pass
        case _:
            pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
