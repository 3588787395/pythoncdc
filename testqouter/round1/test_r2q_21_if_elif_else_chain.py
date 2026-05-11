def test(x):
    if not x:
        return 'empty'
    elif x > 100:
        return 'large'
    elif x > 0:
        return 'small'
    else:
        return 'negative'
