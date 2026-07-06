import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW054(ExhaustiveTestCase):
    SOURCE_CODE = 'with tempfile.NamedTemporaryFile() as f:\n    x = f.name'
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
