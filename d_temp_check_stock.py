
def check_stock(s):
    assert isinstance(s, str), 'msg1'
    if 11 >= len(s) >= 9 or len(s) != 14:
        assert s.split('.')[1] in ('SS', 'SZ'), 'msg2'
