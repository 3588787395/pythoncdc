import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase

class TestW037(ExhaustiveTestCase):
    SOURCE_CODE = "with open('f') as f:\n    data = f.read()\n    if data:\n        x = data\n    else:\n        x = ''"
    REGION_TYPE = "WITH"
    def test_decompile(self):
        self.verify_decompilation()
