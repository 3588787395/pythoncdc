def test(s):
    if not isinstance(s, str):
        pass
    assert isinstance(s, str), '请使用字符串'
    return s.split('.')[1]
