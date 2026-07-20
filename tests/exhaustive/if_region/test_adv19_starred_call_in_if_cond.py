import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19StarredCallInIfCond(ExhaustiveTestCase):
    # if-elif 条件含 *args / **kwargs 函数调用 + 比较结果：
    # def f(args, kwargs):
    #     if process(*args, **kwargs) > 0:
    #         return 'pos'
    #     elif process(*args, **kwargs) == 0:
    #         return 'zero'
    #     elif process(*args, **kwargs) < 0:
    #         return 'neg'
    #     else:
    #         return 'nan'
    # 字节码 LOAD_FAST / DICT_MERGE / LIST_EXTEND / KW_NAMES / CALL
    # / 反编译器在 if-elif 条件含 *args/**kwargs 时易丢失 star unpacking。
    SOURCE_CODE = """def f(args, kwargs):
    if process(*args, **kwargs) > 0:
        return 'pos'
    elif process(*args, **kwargs) == 0:
        return 'zero'
    elif process(*args, **kwargs) < 0:
        return 'neg'
    else:
        return 'nan'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
