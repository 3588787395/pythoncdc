import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from tests.exhaustive.base import ExhaustiveTestCase


class TestB27FromImport_os_path(ExhaustiveTestCase):
    SOURCE_CODE = """from os import path"""
    REGION_TYPE = "BASIC"

    def test_decompile(self):
        self.verify_decompilation()
