def test(data):
    s = data.split('.')
    suffix = s[1] if len(s) > 1 else ''
    if suffix in ('SS', 'SZ', 'CCFX', 'XDCE', 'XSGE', 'XZCE', 'XBHS', 'XINE'):
        return True
    return False
