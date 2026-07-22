import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv20UnionTypeAnnInIfBody(ExhaustiveTestCase):
    # if-elif-else body 内含 PEP 604 union 类型注解 + ann-assign：
    # def f(flag, x):
    #     if flag == 'int':
    #         value: int | None = x
    #         return value or 0
    #     elif flag == 'list':
    #         items: list[int] | None = [x]
    #         return items[0]
    #     else:
    #         result: dict[str, int | float] = {'a': x, 'b': x + 0.5}
    #         return result
    # 字节码 LOAD_CONST int / LOAD_CONST None / BINARY_OP 0 / STORE_NAME value
    # / 反编译器在 if-elif-else 三分支都含 PEP 604 union 类型注解时易丢失类型注解。
    SOURCE_CODE = """def f(flag, x):
    if flag == 'int':
        value: int | None = x
        return value or 0
    elif flag == 'list':
        items: list[int] | None = [x]
        return items[0]
    else:
        result: dict[str, int | float] = {'a': x, 'b': x + 0.5}
        return result"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
