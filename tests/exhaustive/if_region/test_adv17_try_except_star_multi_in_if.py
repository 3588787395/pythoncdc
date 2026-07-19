import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17TryExceptStarMultiInIf(ExhaustiveTestCase):
    # if 体内 try/except* 多个异常组分支（Python 3.11+）：
    # if c:
    #     try:
    #         x = 1
    #     except* TypeError as e:
    #         y = 2
    #     except* ValueError:
    #         z = 3
    # 字节码 CHECK_EG_MATCH 链 + PUSH_EXC_INFO + POP_EXCEPT + 多 RERAISE
    # / 反编译器在 if body 内处理多 except* 分支时易把第二个 except* 丢失，
    # 或把 as 绑定错误地泄露到外层作用域。
    SOURCE_CODE = """if c:
    try:
        x = 1
    except* TypeError as e:
        y = 2
    except* ValueError:
        z = 3"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
