import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW061(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f', 'a') as f:\n    f.write('appended')"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
