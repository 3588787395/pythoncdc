import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW058(ExhaustiveTestCase):
    SOURCE_CODE = 'async def f():\n    async with ctx as v:\n        x = v'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
