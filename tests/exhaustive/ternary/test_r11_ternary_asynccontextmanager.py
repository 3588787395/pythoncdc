import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR11TernaryAsyncContextManager(ExhaustiveTestCase):
    """Bug R11 (new): contextlib.asynccontextmanager + ternary in body.

    原始:
        from contextlib import asynccontextmanager
        @asynccontextmanager
        async def cm():
            x = (a if c else b)
            yield x
    缺陷: @asynccontextmanager 装饰器装饰 async generator，body 内 ternary
         赋值 + yield。@asynccontextmanager 调用栈 PUSH_NULL + LOAD_NAME
         asynccontextmanager + LOAD_CONST cm_code + MAKE_FUNCTION + PRECALL +
         CALL + STORE_NAME cm。cm 的 code object 含 RETURN_GENERATOR +
         GET_AWAITABLE + YIELD_VALUE + ternary merge STORE_FAST x。可能暴露
         async gen + ternary + yield 三重路径的归约冲突。
    """
    SOURCE_CODE = """from contextlib import asynccontextmanager
@asynccontextmanager
async def cm():
    x = (a if c else b)
    yield x
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
