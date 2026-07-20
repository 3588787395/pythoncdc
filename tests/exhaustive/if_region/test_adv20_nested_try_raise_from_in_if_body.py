import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20NestedTryRaiseFromInIfBody(ExhaustiveTestCase):
    # if body 内含嵌套 try-except + raise from + finally：
    # def f(flag, x):
    #     if flag:
    #         try:
    #             try:
    #                 if x < 0:
    #                     raise ValueError('neg')
    #                 return x
    #             except ValueError as e:
    #                 raise RuntimeError('inner') from e
    #         except RuntimeError as e2:
    #             return str(e2)
    #     return 0
    # 字节码 PUSH_EXC_INFO / RERAISE / RAISE_VARARGS / CALL __cause__
    # / 反编译器在 if body 内嵌套 try + raise from 时易丢失 from 子句或 finally。
    SOURCE_CODE = """def f(flag, x):
    if flag:
        try:
            try:
                if x < 0:
                    raise ValueError('neg')
                return x
            except ValueError as e:
                raise RuntimeError('inner') from e
        except RuntimeError as e2:
            return str(e2)
    return 0"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
