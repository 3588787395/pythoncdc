import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestN05TryInFor_a_IndexError(ExhaustiveTestCase):
    SOURCE_CODE = """for a in range(10):
    try:
        pass
    except IndexError:
        continue"""
    REGION_TYPE = "NESTED"

    def test_decompile(self):
        self.verify_decompilation()
