import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv15AsyncWithMultiAs(ExhaustiveTestCase):
    # async with 多上下文管理器（含 as 绑定）在 if 体内：
    # async def f():
    #     if c:
    #         async with a as x, b as y:
    #             z = 1
    # 字节码含两组 BEFORE_ASYNC_WITH / SETUP_ASYNC_WITH，反编译器
    # 在多 ctx + as 绑定时错乱：as 绑定的变量名互换、body 被替换为
    # break、并在末尾追加多余的 None 表达式。
    SOURCE_CODE = """async def f():
    if c:
        async with a as x, b as y:
            z = 1"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
