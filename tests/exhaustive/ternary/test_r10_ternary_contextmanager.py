import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR10TernaryContextmanager(ExhaustiveTestCase):
    """Bug R10: contextlib.contextmanager + ternary in body — 字节码不一致。

    原始:
        from contextlib import contextmanager
        @contextmanager
        def f():
            yield (a if c else b)
    缺陷: @contextmanager 装饰器 + yield (ternary) body。yield (ternary) 的
         merge 块含 YIELD_VALUE + cleanup（POP_TOP）。@contextmanager 调用
         栈帧 PUSH_NULL + LOAD_NAME contextmanager + LOAD_CONST code +
         MAKE_FUNCTION + PRECALL + CALL + STORE_NAME f。R9 已测 yield (ternary)
         + 后续语句；R10 测 @contextmanager 装饰器变体，验证 decorator 调用
         与 yield ternary merge 块的归属冲突。依「父引用子入口」：
         @contextmanager Call 通过 MAKE_FUNCTION 之后的 CALL 引用 yield
         ternary 子节点作为函数 body 的一部分。
    """
    SOURCE_CODE = """from contextlib import contextmanager
@contextmanager
def f():
    yield (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
