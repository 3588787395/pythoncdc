"""Condition shapes a patch detector classifies as test patterns.

Targets ObjectivePatchDetector._extract_test_pattern (isinstance over
ast.Compare / ast.BoolOp / ast.Attribute / ast.Call) and the matching tests in
core/cfg/patch_detector.py.
"""


class Target:
    def __init__(self):
        self.attr = 1
        self.other = 0

    def method(self):
        return 2


def pj_entry(obj, other, fn):
    """Zero-arg-callable entry: attribute compare, boolop and call tests."""
    if obj.attr == 1:
        out = "cmp"
    elif obj.attr and other.other:
        out = "boolop"
    elif fn():
        out = "call"
    else:
        out = "none"
    return out, obj.method


def pj_entry_attr(obj):
    """Zero-arg-callable entry: attribute-valued tests only."""
    if obj.attr:
        return 1
    if not obj.other:
        return 2
    return 3


def pj_entry_compare(obj, other):
    """Zero-arg-callable entry: chained comparisons and identity tests."""
    if 0 < obj.attr < other.other:
        return "chain"
    if obj.attr is not None and obj.other is not None:
        return "identity"
    return "plain"


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    t = Target()
    return pj_entry(t, t, t.method), pj_entry_attr(t), pj_entry_compare(t, t)

def main():
    t = Target()
    return pj_entry(t, t, t.method), pj_entry_attr(t), pj_entry_compare(t, t)


if __name__ == "__main__":
    main()
