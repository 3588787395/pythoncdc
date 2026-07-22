import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19DictUnpackInIfCond(ExhaustiveTestCase):
    # if 条件含 dict unpacking `{**d, 'a': 1}` + 长度比较 + elif 链：
    # def f(d):
    #     if len({**d, 'a': 1, 'b': 2}) > 3:
    #         return 'big'
    #     elif len({**d, 'x': 0}) == 2:
    #         return 'small'
    #     elif 'a' in {**d, 'a': 1}:
    #         return 'has_a'
    #     else:
    #         return 'none'
    # 字节码 BUILD_MAP / DICT_UPDATE / LOAD_CONST / COMPARE_OP
    # / 反编译器在 if-elif 条件含 dict unpacking 时易丢失 **d 或合并 dict 字面量错乱。
    SOURCE_CODE = """def f(d):
    if len({**d, 'a': 1, 'b': 2}) > 3:
        return 'big'
    elif len({**d, 'x': 0}) == 2:
        return 'small'
    elif 'a' in {**d, 'a': 1}:
        return 'has_a'
    else:
        return 'none'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
