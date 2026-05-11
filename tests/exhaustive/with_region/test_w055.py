import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW055(ExhaustiveTestCase):
    SOURCE_CODE = "with redirect_stdout(io.StringIO()):\n    print('hello')"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
