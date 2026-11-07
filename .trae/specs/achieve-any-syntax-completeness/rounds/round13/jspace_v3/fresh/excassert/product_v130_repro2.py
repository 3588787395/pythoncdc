# Source Generated with Decompyle++ (Python version)
# File: E1_assert_not_in_handler.pyc (Python 3.11)

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
        raise TypeError('bad')
