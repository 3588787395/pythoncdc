import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest


class TestE01_TryExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = float('inf')
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE02_TryMultiExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(op, a, b):
    try:
        if op == '+':
            result = a + b
        elif op == '/':
            result = a / b
        else:
            raise ValueError("Unknown op")
    except ZeroDivisionError:
        result = 0
    except ValueError:
        result = -1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE03_TryExceptElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(d, key):
    try:
        value = d[key]
    except KeyError:
        value = "default"
    else:
        value = f"found: {value}"
    return value
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE04_TryFinally(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    cleanup_done = False
    try:
        result = "operation"
    finally:
        cleanup_done = True
    return result, cleanup_done
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE05_TryExceptFinally(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(d, key):
    result = None
    try:
        result = d[key]
    except KeyError:
        result = None
    finally:
        pass
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE06_FullCombination(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(d, key):
    try:
        value = d[key]
    except KeyError:
        value = "missing"
    else:
        value = str(value).upper()
    finally:
        pass
    return value
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE07_ExceptAs(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x):
    try:
        result = int(x)
    except ValueError as e:
        result = f"error: {e}"
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE08_BareExcept(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    try:
        result = risky_operation()
    except:
        result = "something went wrong"
    return result

def risky_operation():
    return 42
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE09_NestedTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func():
    try:
        try:
            inner_result = 10 / 0
        except ZeroDivisionError:
            inner_result = 0
    except Exception:
        outer_result = -1
    else:
        outer_result = inner_result
    return outer_result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE10_TryWithLoop(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    result = []
    try:
        for item in items:
            result.append(item * 2)
    except Exception:
        result = []
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE11_LoopWithTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(strings):
    results = []
    for s in strings:
        try:
            val = int(s)
        except ValueError:
            val = 0
        results.append(val)
    return results
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE12_TryWithIf(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(x, y):
    try:
        if y != 0:
            result = x / y
        else:
            result = 0
    except Exception:
        result = -1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestE13_IfWithTry(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(flag, data):
    if flag:
        try:
            result = process(data)
        except Exception:
            result = None
    else:
        result = default_value()
    return result

def process(x):
    return x * 2

def default_value():
    return 0
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())
