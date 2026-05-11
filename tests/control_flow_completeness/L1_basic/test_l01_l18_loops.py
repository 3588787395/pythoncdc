import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))

from tests.control_flow_completeness.base import ControlFlowCompletenessTest


# For循环系列 (L01-L09)

class TestL01_SimpleFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    result = []
    for item in items:
        result.append(item)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL02_ForBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items, target):
    result = []
    for item in items:
        if item == target:
            break
        result.append(item)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL03_ForContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    result = []
    for item in items:
        if item <= 0:
            continue
        result.append(item * 2)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL04_ForElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    for item in items:
        if item < 0:
            break
    else:
        return "completed normally"
    return "broken out"
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL05_ForBreakElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    found = False
    for item in items:
        if item == 999:
            found = True
            break
    else:
        found = False
    return found
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL06_ForEnumerate(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(items):
    result = []
    for i, value in enumerate(items):
        result.append((i, value))
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL07_ForZip(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(list1, list2):
    result = []
    for a, b in zip(list1, list2):
        result.append(a + b)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL08_ForDict(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(d):
    keys = []
    values = []
    for k in d.keys():
        keys.append(k)
    for v in d.values():
        values.append(v)
    return keys, values
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL09_ForRange(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    total = 0
    for i in range(n):
        total += i
    return total
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# While循环系列 (L10-L14)

class TestL10_SimpleWhile(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    result = []
    i = 0
    while i < n:
        result.append(i)
        i += 1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL11_WhileBreak(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(limit):
    i = 0
    while True:
        if i >= limit:
            break
        i += 1
    return i
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL12_WhileContinue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    result = []
    i = 0
    while i < n:
        i += 1
        if i % 2 == 0:
            continue
        result.append(i)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL13_WhileElse(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(n):
    count = 0
    while count < n:
        if count == 999:
            break
        count += 1
    else:
        return "normal exit"
    return "break exit"
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL14_WhileTrue(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(data):
    result = []
    i = 0
    while True:
        if i >= len(data):
            break
        result.append(data[i])
        i += 1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


# 嵌套循环 (L15-L18)

class TestL15_NestedForFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(matrix):
    result = []
    for row in matrix:
        for val in row:
            result.append(val)
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL16_NestedForWhile(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(groups):
    all_items = []
    for group in groups:
        i = 0
        while i < len(group):
            all_items.append(group[i])
            i += 1
    return all_items
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL17_NestedWhileFor(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(list_of_lists):
    result = []
    idx = 0
    while idx < len(list_of_lists):
        for item in list_of_lists[idx]:
            result.append(item)
        idx += 1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())


class TestL18_NestedWhileWhile(ControlFlowCompletenessTest):
    SOURCE_CODE = """
def test_func(grid):
    result = []
    i = 0
    while i < len(grid):
        j = 0
        while j < len(grid[i]):
            result.append(grid[i][j])
            j += 1
        i += 1
    return result
"""

    def test_bytecode_equivalence(self):
        self.assertTrue(self.verify_bytecode_equivalence())

    def test_syntax_valid(self):
        self.assertTrue(self.verify_syntax_valid())
