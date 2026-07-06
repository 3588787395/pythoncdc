"""测试try块中的return值"""

def test_return_in_try():
    try:
        x = 1 / 0
        return x
    except ZeroDivisionError as e:
        print(f'Error: {e}')
        raise
    finally:
        print('Finally')
