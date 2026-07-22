import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR14TernaryExceptAsType(ExhaustiveTestCase):
    """Bug R14 (new): except (a if c else b) as e: pass — except 类型是 ternary + as 别名。

    原始:
        try:
            pass
        except (a if c else b) as e:
            pass
    缺陷: except handler 的异常类型是 ternary，且使用 as 别名。R4 try_handler_type
         已测 except (ternary) 不带 as 别名。R14 测带 as 变体：ternary merge 块栈顶
         经 CHECK_EXC_MATCH + STORE_NAME e (as 别名) 消费链。带 as 别名时
         STORE_NAME e 与 ternary region 后续块归属可能冲突。
    """
    SOURCE_CODE = """try:
    pass
except (a if c else b) as e:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
