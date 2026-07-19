import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv17TryExceptStarInIf(ExhaustiveTestCase):
    # if 体内 try/except* 异常组处理（Python 3.11+）：
    # if c:
    #     try:
    #         x = 1
    #     except* Exception:
    #         y = 2
    # 字节码 SETUP_FINALLY + CHECK_EG_MATCH + PUSH_EXC_INFO + POP_EXCEPT
    # / 反编译器在 if body 内处理 except* 时易把 except* 误识别为普通 except，
    # 或丢失 except* 的 ExceptionGroup 包装结构。
    SOURCE_CODE = """if c:
    try:
        x = 1
    except* Exception:
        y = 2"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
