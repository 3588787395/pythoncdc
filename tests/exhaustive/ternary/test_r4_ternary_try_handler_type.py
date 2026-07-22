import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR4TernaryTryHandlerType(ExhaustiveTestCase):
    """Bug R4-05: ternary 作为 except handler 异常类型（带 as 子句）— 字节码不一致。

    原始:
        try:
            pass
        except (E1 if cond else E2) as e:
            pass
    缺陷: ternary 作为 except handler 的异常类型时（带 as e 绑定），
         DUP_TOP + COMPARE_OP 链消费 ternary 结果，STORE_NAME 消费异常实例。
         反编译器可能丢失 except handler 结构或 ternary 结构。
         R3 已识别为已知限制（R3-08），R4 增加 as e 绑定以加重上下文。
    """
    SOURCE_CODE = """try:
    pass
except (E1 if cond else E2) as e:
    pass
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
