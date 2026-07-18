import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15AsyncWithPass(ExhaustiveTestCase):
    # async with 在 if 体内且 body 仅 pass：
    # async def f():
    #     if c:
    #         async with x: pass
    # 字节码 LOAD_NAME x / BEFORE_ASYNC_WITH / SETUP_ASYNC_WITH
    # / POP_TOP / POP_BLOCK / ... 反编译器将 pass 错误地
    # 还原为 break，导致产出 'break' outside loop 的非法语法。
    SOURCE_CODE = """async def f():
    if c:
        async with x: pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
