import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest


class TestW01_SimpleWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(text):
    f = StringIO(text)
    with f as file_obj:
        content = file_obj.read()
    return content
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestW02_WithNoAs(ControlFlowCompletenessTest):
    SOURCE_CODE = """
import contextlib

@contextlib.contextmanager
def dummy_ctx():
    yield 42

def test_func():
    with dummy_ctx():
        pass
    return "done"
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestW03_MultiContextWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(text1, text2):
    with StringIO(text1) as f1, StringIO(text2) as f2:
        content1 = f1.read()
        content2 = f2.read()
    return content1 + content2
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestW04_NestedWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(text1, text2):
    with StringIO(text1) as f1:
        with StringIO(text2) as f2:
            combined = f1.read() + f2.read()
    return combined
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestW05_WithInnerTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(text):
    with StringIO(text) as f:
        try:
            content = f.read()
        except IOError:
            content = ""
    return content
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestW06_TryInnerWith(ControlFlowCompletenessTest):
    SOURCE_CODE = """
from io import StringIO

def test_func(text):
    content = None
    try:
        with StringIO(text) as f:
            content = f.read()
    except IOError:
        content = "default"
    return content
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())
