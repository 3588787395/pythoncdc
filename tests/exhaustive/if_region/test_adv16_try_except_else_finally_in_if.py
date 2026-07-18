import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv16TryExceptElseFinallyInIf(ExhaustiveTestCase):
    # if 体内完整 try/except/else/finally：
    # if c:
    #     try:
    #         x = 1
    #     except Exception:
    #         pass
    #     else:
    #         y = 2
    #     finally:
    #         cleanup()
    # 字节码多个 SETUP_FINALLY / POP_BLOCK / 反编译器在 if body 内
    # 完整 try/except/else/finally 嵌套时的结构归约。
    SOURCE_CODE = """if c:
    try:
        x = 1
    except Exception:
        pass
    else:
        y = 2
    finally:
        cleanup()"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
