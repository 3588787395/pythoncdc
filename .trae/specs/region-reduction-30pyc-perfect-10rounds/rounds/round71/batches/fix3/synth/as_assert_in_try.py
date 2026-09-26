# F-ASSERT / positive: chained-compare asserts inside a try. The condition block of
# each assert has an extra successor -- the except handler entry of the enclosing
# try -- which must not be counted when probing for LOAD_ASSERTION_ERROR.
def window(hour, minute, log):
    try:
        h = int(hour)
        m = int(minute)
        assert 0 <= h < 24
        assert 0 <= m < 60
        return h * 60 + m
    except (TypeError, ValueError, AssertionError):
        log.error('bad time')
        raise ValueError('time error')
