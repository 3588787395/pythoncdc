def test():
    import os
    token = ''
    if os.path.exists('/tmp/token'):
        with open('/tmp/token', 'r') as f:
            token = f.read()
    return token
