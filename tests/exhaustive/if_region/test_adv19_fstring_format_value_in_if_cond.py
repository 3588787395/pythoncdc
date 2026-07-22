import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv19FstringFormatValueInIfCond(ExhaustiveTestCase):
    # if-elif 条件含 f-string format value + 调用结果比较：
    # def f(x):
    #     if f'{x:.2f}' == '0.00':
    #         return 'zero_str'
    #     elif f'{x!r}' == "'nan'":
    #         return 'nan_str'
    #     elif f'{x:>10}' == '         1':
    #         return 'right_aligned'
    #     else:
    #         return 'other'
    # 字节码 FORMAT_VALUE / LOAD_CONST / COMPARE_OP
    # / 反编译器在 if-elif 条件含 f-string format spec + 多种 conversion 时易归约错乱。
    SOURCE_CODE = """def f(x):
    if f'{x:.2f}' == '0.00':
        return 'zero_str'
    elif f'{x!r}' == "'nan'":
        return 'nan_str'
    elif f'{x:>10}' == '         1':
        return 'right_aligned'
    else:
        return 'other'"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
