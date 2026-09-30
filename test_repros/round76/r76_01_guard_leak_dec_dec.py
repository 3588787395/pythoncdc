# Source Generated with Decompyle++ (Python version)
# File: r76_01_guard_leak_dec.pyc (Python 3.11)

def f(fields, frequency):
    log('enter', frequency)
    candle = None
    check(frequency)
    if fields is not None:
        if not isinstance(fields, list):
            error('get_price bad fields 1')
            error('get_price bad fields 2')
        assert isinstance(fields, list), 'fields must be list'
        for field in fields:
            if field not in ('open', 'close'):
                error('unknown field')
                raise AssertionError('unknown field')
    if frequency.find('w') > -1:
        candle = 7
    return candle
