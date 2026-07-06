import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry16MultiNested(ExhaustiveTestCase):
    SOURCE_CODE = """try:
    try:
        level2()
    except Error2:
        try:
            level3_recover()
        except Error3:
            deep_fix()
except Error1:
    top_fix()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
