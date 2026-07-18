import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv08DictUnpackInCall(ExhaustiveTestCase):
    # if 体内调用含双 dict 解包 f(**a, **b)
    SOURCE_CODE = """if c:
    f(**a, **b)"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
