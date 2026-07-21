import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestR8TernaryAnnAssign(ExhaustiveTestCase):
    """Bug R8: AnnAssign value 是 ternary — 字节码不一致。

    原始:
        y: int = (a if c else b)
    缺陷: AnnAssign (带类型注解的赋值) 的 value 是 ternary。
         AnnAssign 在字节码层是 SETUP_ANNOTATIONS + LOAD_NAME int +
         LOAD_NAME __annotations__ + LOAD_CONST 'y' + STORE_SUBSCR，
         随后正常 LOAD ternary + STORE y。ternary merge 块的 STORE y
         与 AnnAssign 的注解存储路径独立，但注解存储块可能与 ternary
         entry 共享导致归属冲突。
    """
    SOURCE_CODE = """y: int = (a if c else b)
"""
    REGION_TYPE = "TERNARY"

    def test_decompile(self):
        self.verify_decompilation()
