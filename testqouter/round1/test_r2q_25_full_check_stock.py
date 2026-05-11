def test(s):
    if isinstance(s, str):
        pass
    assert isinstance(s, str), '请使用字符串表示标的代码'
    if 11 <= len(s) >= 9:
        pass
    assert 11 <= len(s) >= 9, '请输入正确的标的代码'
    suffix = s.split('.')[1] if '.' in s else ''
    assert suffix in ('SS', 'SZ', 'CCFX', 'XDCE', 'XSGE', 'XZCE', 'XBHS', 'XINE'), '请输入标的代码以正确后缀结尾'
    return True
