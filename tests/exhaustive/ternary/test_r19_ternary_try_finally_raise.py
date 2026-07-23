import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR19TernaryTryFinallyRaise(ExhaustiveTestCase):
    """Bug R19-01: try-finally 的 finally 体含 raise E(ternary) — ternary 作 raise 调用参数位于 finally 清理块。

    原始:
        def f():
            try:
                x = 1
            finally:
                raise E(a if c else b)
    缺陷: finally 清理块内 raise E(a if c else b) —— ternary 是 raise 调用
         E(...) 的位置参数，且整体位于 try-finally 的 finally 异常清理路径中。
         R14 finally_body 测过 `finally: x = (ternary)` (assign)，R14 raise_arg
         测过 `raise E(ternary)` (非 finally 上下文)。本用例 finally 块的
         PUSH_EXC_INFO + POP_EXCEPT + RERAISE 清理链与 ternary merge 块的
         PRECALL+CALL+RAISE_VARARGS 消费链归属冲突，反编译把 raise 误移入 try
         体并退化为 `try: ... raise E(a if c else b) except: pass`。
    """
    SOURCE_CODE = """def f():
    try:
        x = 1
    finally:
        raise E(a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
