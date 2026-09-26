# F-ASSERT (base.OverNightOrder.__init__): chained-compare asserts inside a try are
# lowered to `if not cond: pass` + `raise AssertionError` (LOAD_ASSERTION_ERROR 2 -> 0),
# which turns the following statements into unreachable code that CPython deletes
# (188 -> 165 instructions).
def init_time(time_value, log):
    try:
        if isinstance(time_value, str):
            if ':' in time_value:
                h, m = time_value.split(':')[:2]
                h = int(h) if h else 0
                m = int(m) if m else 0
            else:
                m = int(time_value[-2:])
                h = int(time_value[:-2])
        else:
            h, m = divmod(int(time_value), 100)
        assert 0 <= h < 24
        assert 0 <= m < 60
        order_time = (h * 60 + m) * 60
        return order_time
    except (AttributeError, ValueError, AssertionError):
        log.error('bad time')
        raise ValueError('time error')
