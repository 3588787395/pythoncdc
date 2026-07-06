def test(s):
    if not isinstance(s, str):
        pass
    assert isinstance(s, str), '请输入字符串'
    assert len(s) >= 9, '长度不足'
    assert '.' in s, '缺少分隔符'
    return True
