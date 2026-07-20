import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv18YieldInIfBody(ExhaustiveTestCase):
    # if body 内含 yield 表达式（生成器）：
    # def gen():
    #     if cond:
    #         yield 1
    #         yield 2
    #     yield 3
    # 字节码 RESUME + YIELD_VALUE 在 if body 内 / 反编译器在 if body 内
    # 处理 yield 时易把 yield 后的语句错挂到 if body 外或丢失 yield。
    SOURCE_CODE = """def gen():
    if cond:
        yield 1
        yield 2
    yield 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
