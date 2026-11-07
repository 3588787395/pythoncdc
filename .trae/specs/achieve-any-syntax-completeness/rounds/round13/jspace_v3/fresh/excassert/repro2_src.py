def er(x, _isfinite):
    try:
        return x.as_integer_ratio()
    except AttributeError:
        pass
    except (OverflowError, ValueError):
        assert not _isfinite(x)
        return (x, None)
    try:
        return (x.numerator, x.denominator)
    except AttributeError:
        raise TypeError("bad")
