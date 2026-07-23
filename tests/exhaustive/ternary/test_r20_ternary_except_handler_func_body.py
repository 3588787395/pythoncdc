import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR20TernaryExceptHandlerFuncBody(ExhaustiveTestCase):
    """Bug R20-16: 函数内 try (非空 body) + except (ternary) as e — 函数作用域 + 非空 try body 触发。

    原始:
        def f():
            try:
                x = 1
            except (A if c else B) as e:
                pass
    缺陷: except handler 的异常类型是 ternary，带 as 别名，位于函数内且 try body
         非空 (x = 1)。R14 except_as_type 测过模块级 try: pass + except (ternary) as e
         (空 try body，模块级，该用例通过)。本用例函数作用域 (STORE_FAST/DELETE_FAST
         for e) + 非空 try body (LOAD_CONST/RETURN_VALUE 在 PUSH_EXC_INFO 之前) 触发：
         ternary merge 块的 CHECK_EXC_MATCH + STORE_FAST e + POP_EXCEPT + 清理链
         (RERAISE/COPY/POP_EXCEPT) 与 try body 末尾 RETURN_VALUE 的归属冲突，
         反编译额外生成 `del e` 且 except handler 字节码重排，嵌套 code object
         指令数不匹配 (25 vs 24)。
    """
    SOURCE_CODE = """def f():
    try:
        x = 1
    except (A if c else B) as e:
        pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
