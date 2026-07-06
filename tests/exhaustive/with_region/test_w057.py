import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW057(ExhaustiveTestCase):
    SOURCE_CODE = 'with MyContext() as ctx:\n    x = ctx.value'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
