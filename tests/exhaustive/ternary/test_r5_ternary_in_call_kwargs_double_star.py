import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR5TernaryInCallKwargsDoubleStar(ExhaustiveTestCase):
    """Bug R5-14: ternary 作为函数调用 **kwargs 展开 — 字节码不一致。

    原始: f(**(d if c else e))
    缺陷: ternary 作为 **kwargs 展开参数时，BUILD_MAP + KW_NAMES + CALL
         在 merge_block 中消费 ternary 结果作为 kwargs dict。
         R4 已通过显式 key=value kwargs 场景（test_r4_ternary_in_call_kwargs）。
         R5 用 **(ternary) 双星展开形式（dict 解包）重测，分离根因。
         期望：Call(func=f, kwargs=IfExp) 正确归约。
    """
    SOURCE_CODE = """f(**(d if c else e))"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
