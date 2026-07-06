def test():
    data = {'snapshot': {'price': 100}}
    result = data.get('data', {}).get('snapshot', {}).get('price', 0)
    return result
