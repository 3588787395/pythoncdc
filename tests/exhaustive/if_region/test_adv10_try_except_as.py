import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv10TryExceptAs(ExhaustiveTestCase):
    # if 体内 try/except with as binding
    SOURCE_CODE = """if c:
    try:
        x = f()
    except ValueError as e:
        x = e"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
