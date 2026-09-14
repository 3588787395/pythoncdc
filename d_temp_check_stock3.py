
def check_stock(s):
    assert isinstance(s, str), 'msg1'
    assert 11 >= len(s) >= 9 or len(s) != 14, 'msg2'
    assert s.split('.')[1] in ('SS', 'SZ'), 'msg3'
