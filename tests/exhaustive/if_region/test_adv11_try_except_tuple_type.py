import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv11TryExceptTupleType(ExhaustiveTestCase):
    # if 体内 try/except 元组类型 except (A, B):
    SOURCE_CODE = """if c:
    try:
        x
    except (A, B):
        pass"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
