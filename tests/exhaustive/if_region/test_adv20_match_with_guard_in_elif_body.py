import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20MatchWithGuardInElifBody(ExhaustiveTestCase):
    # elif body 内含 match + 多 case + guard + class pattern：
    # def f(flag, point):
    #     if flag == 'simple':
    #         return 'simple'
    #     elif flag == 'match':
    #         match point:
    #             case Point(x=0, y=0):
    #                 return 'origin'
    #             case Point(x=x, y=y) if x == y:
    #                 return 'diagonal'
    #             case Point(x=x, y=_) if x > 0:
    #                 return 'right'
    #             case _:
    #                 return 'other'
    #     else:
    #         return 'none'
    # 字节码 MATCH_CLASS / MATCH_MAPPING / COMPARE_OP guard
    # / 反编译器在 elif body 内 match + guard + class pattern 时易丢失 guard 或 case。
    SOURCE_CODE = """def f(flag, point):
    if flag == 'simple':
        return 'simple'
    elif flag == 'match':
        match point:
            case Point(x=0, y=0):
                return 'origin'
            case Point(x=x, y=y) if x == y:
                return 'diagonal'
            case Point(x=x, y=_) if x > 0:
                return 'right'
            case _:
                return 'other'
    else:
        return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
