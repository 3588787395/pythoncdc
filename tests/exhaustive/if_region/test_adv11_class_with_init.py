import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11ClassWithInit(ExhaustiveTestCase):
    # if 体内 class 定义带 __init__ 方法
    SOURCE_CODE = """if c:
    class C:
        def __init__(self, x):
            self.x = x
        def get(self):
            return self.x"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
