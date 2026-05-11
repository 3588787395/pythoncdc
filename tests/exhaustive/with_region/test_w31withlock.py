import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestW31WithLock(ExhaustiveTestCase):
    SOURCE_CODE = """import threading
lock = threading.Lock()
with lock:
    pass"""
    REGION_TYPE = "WITH_REGION"

    def test_decompile(self):
        self.verify_decompilation()
