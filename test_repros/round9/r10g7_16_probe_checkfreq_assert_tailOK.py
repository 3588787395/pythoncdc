# Source Generated with Decompyle++ (Python version)
# File: r10g7_16_probe_checkfreq_assert_tail.pyc (Python 3.11)

def r10g7_16_probe_checkfreq_assert_tail(self, n, log):
    try:
        if n == 'w':
            tmp = 1
        else:
            tmp = int(n)
        assert tmp > 0, 'bad'
    except BaseException:
        log.error('bad')
        raise AssertionError('bad')
    return None
