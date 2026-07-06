"""测试ValueError handler的最小实例"""

def test_value_error():
    try:
        x = 1 / 0
    except ValueError as e:
        print(f'Value error: {e}')
        raise
