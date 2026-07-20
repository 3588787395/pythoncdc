import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17WithTryNestedInIf(ExhaustiveTestCase):
    # if 体内 with 内嵌 try/except：
    # if c:
    #     with a() as x:
    #         try:
    #             y = x.value
    #         except Exception:
    #             y = None
    # 字节码 BEFORE_WITH + SETUP_WITH + SETUP_FINALLY 双层套嵌
    # / 反编译器在 if body 内 with + try 嵌套时易把 except 错挂到 with
    # 的 cleanup 路径上，或丢失 with 的 as 绑定。
    SOURCE_CODE = """if c:
    with a() as x:
        try:
            y = x.value
        except Exception:
            y = None"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
