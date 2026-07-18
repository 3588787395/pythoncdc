import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestAdv04RaiseFrom(ExhaustiveTestCase):
    # raise-from（raise X from Y）
    SOURCE_CODE = """if c:
    raise E() from e"""
    REGION_TYPE = "IF_REGION"

    def test_decompile(self):
        self.verify_decompilation()
