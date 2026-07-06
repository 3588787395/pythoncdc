def test():
    with open('nonexistent.txt', 'r') as f:
        content = f.read()
    return content
