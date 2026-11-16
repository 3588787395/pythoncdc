"""Dict-AST carrier for match / try / yield / lambda statement arms."""


def pj_entry(v):
    """Zero-arg-callable entry: match statement over dict and tuple literals."""
    table = {1: "one", 2: "two"}
    match v:
        case {1: name}:
            return {"hit": name}
        case (a, b):
            return {"pair": [a, b]}
        case 0:
            return {}
        case _:
            return table


def pj_entry_try(fn):
    """Zero-arg-callable entry: try/except/else/finally with dict bodies."""
    try:
        out = {"step": "try"}
        fn(out)
    except (ValueError, KeyError):
        out = {"step": "except"}
    else:
        out = dict(out, step="else")
    finally:
        out = dict(out, step="finally")
    return out


def pj_entry_yield(ns=(1, -2, 0)):
    """Zero-arg entry: generator with yield / yield-from style arms."""
    for n in ns:
        if n > 0:
            yield {"sign": "+", "n": n}
        elif n < 0:
            yield {"sign": "-", "n": -n}
        else:
            yield {}


def pj_entry_lambda():
    """Zero-arg entry: lambdas kept in a dict literal."""
    fns = {"bump": lambda x: x + 1, "flip": lambda y: -y if y else 0}
    return fns["bump"](1), fns["flip"](0)


def main():
    return (pj_entry(1), pj_entry_try(dict), list(pj_entry_yield()),
            pj_entry_lambda())


if __name__ == "__main__":
    main()
