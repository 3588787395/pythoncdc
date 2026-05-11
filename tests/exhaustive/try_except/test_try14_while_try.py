import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestTry14WhileTry(ExhaustiveTestCase):
    SOURCE_CODE = """while running:
    try:
        tick()
    except ConnectionError:
        reconnect()"""
    REGION_TYPE = "TRY_EXCEPT"

    def test_decompile(self):
        self.verify_decompilation()
