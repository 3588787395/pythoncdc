# Source Generated with Decompyle++ (Python version)
# File: r76_10_dead_return_shift.pyc (Python 3.11)

def f(frequency):
    try:
        if frequency in ('1m', '5m', '15m'):
            raise ValueError('minute freq')
        elif frequency in ('30m', '60m'):
            raise ValueError('hour freq')
        elif frequency in ('1d', '1w') or Exception:
            pass
        else:
            return None
    except Exception as e:
        log(str(e))
        return None
