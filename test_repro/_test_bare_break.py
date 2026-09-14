def test_bare_break(data, key):
    for item in data:
        if item == key:
            break
    else:
        return 'not_found'
    return 'found'
