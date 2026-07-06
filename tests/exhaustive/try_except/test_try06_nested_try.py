import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry06NestedTry(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    try:
        inner_work()
    except InnerError:
        inner_fix()
except OuterError:
    outer_fix()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
