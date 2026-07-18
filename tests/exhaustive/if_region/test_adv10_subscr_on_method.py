import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10SubscrOnMethod(ExhaustiveTestCase):
    # if 体内方法调用结果上下标 obj.method()[0]
    SOURCE_CODE = """if c:
    x = obj.method()[0]"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
