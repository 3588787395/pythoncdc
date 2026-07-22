import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18RaiseFromComplexInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 raise-from 复杂形式：
    # def f(x):
    #     if x > 0:
    #         raise ValueError('positive') from RuntimeError('orig_pos')
    #     elif x < 0:
    #         raise ValueError('negative') from RuntimeError('orig_neg')
    #     else:
    #         raise ValueError('zero') from RuntimeError('orig_zero')
    # 字节码 LOAD_ASSERTION_ERROR? No, RAISE_VARARGS 1 + LOAD_NAME + CALL
    # + RAISE_VARARGS 3 / 反编译器在 if-elif-else 三个分支都含 raise from
    # 时易丢失 from 子句或错把 raise 提升到外层。
    SOURCE_CODE = """def f(x):
    if x > 0:
        raise ValueError('positive') from RuntimeError('orig_pos')
    elif x < 0:
        raise ValueError('negative') from RuntimeError('orig_neg')
    else:
        raise ValueError('zero') from RuntimeError('orig_zero')"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
