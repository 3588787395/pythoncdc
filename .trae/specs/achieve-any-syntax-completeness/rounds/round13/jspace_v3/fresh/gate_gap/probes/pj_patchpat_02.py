"""Patch-shaped guards: attribute/call tests wrapped in equality arms."""


class Widget:
    def __init__(self):
        self.flag = True
        self.value = 3

    def enabled(self):
        return self.flag


def pj_entry(w, registry):
    """Zero-arg-callable entry: ``if`` arms over attribute and call tests."""
    if w.enabled():
        w.value = 4
    elif w.flag == 1:
        w.value = 5
    elif registry.get("k", 0) and w.value:
        w.value = 6
    return w.value


def pj_entry_nested(w):
    """Zero-arg-callable entry: nested attribute tests inside a boolop."""
    if (w.flag and w.value > 1) or (not w.flag and w.value == 0):
        return "mixed"
    if hasattr(w, "flag") and getattr(w, "value", 0):
        return "reflective"
    return "plain"


def main():
    return pj_entry(Widget(), {}), pj_entry_nested(Widget())


if __name__ == "__main__":
    main()
