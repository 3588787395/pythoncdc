"""Deep elif chains whose arms hold break / continue / while / for."""


def pj_entry(v, ns=(1, 2, 3)):
    """Zero-arg-callable entry: six-arm elif chain, loop arms inside."""
    if v == 1:
        out = []
        for n in ns:
            if n > 1:
                break
            out.append(n)
    elif v == 2:
        out = []
        for n in ns:
            if n == 2:
                continue
            out.append(n)
    elif v == 3:
        out = 0
        while out < 3:
            out += 1
    elif v == 4:
        out = list(ns)
    elif v == 5:
        out = [n for n in ns if n]
    else:
        out = None
    return out


def pj_entry_nested(v):
    """Zero-arg-callable entry: elif inside elif (nested chain)."""
    if v > 0:
        if v > 10:
            return "big"
        elif v > 5:
            return "mid"
        elif v > 1:
            return "small"
        else:
            return "unit"
    elif v == 0:
        return "zero"
    return "neg"


def pj_entry_default():
    """Zero-arg defaulted entry (J input_model.calls driver)."""
    return pj_entry(1), pj_entry_nested(2)

def main():
    return pj_entry(1), pj_entry_nested(2)


if __name__ == "__main__":
    main()
