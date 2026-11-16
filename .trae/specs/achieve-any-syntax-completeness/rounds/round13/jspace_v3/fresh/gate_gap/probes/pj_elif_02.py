"""Elif chains whose arms hold try / match / raise / return."""


def pj_entry(v):
    """Zero-arg-callable entry: elif chain with try and match arms."""
    if v == 1:
        try:
            out = 1 / v
        except ZeroDivisionError:
            out = None
        finally:
            out = out or 0
    elif v == 2:
        match v:
            case 2:
                out = "two"
            case _:
                out = "other"
    elif v == 3:
        out = {"k": v}
    else:
        raise ValueError("unsupported")
    return out


def pj_entry_raise(v):
    """Zero-arg-callable entry: elif chain that re-raises in one arm."""
    if v < 0:
        raise ValueError(v)
    elif v == 0:
        return 0
    elif v < 10:
        return v * 2
    return v


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return pj_entry(2), pj_entry_raise(1)

def main():
    return pj_entry(2), pj_entry_raise(1)


if __name__ == "__main__":
    main()
