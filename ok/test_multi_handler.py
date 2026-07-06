"""测试多个handler和finally的最小实例"""

def test_multi_handler():
    try:
        x = 1 / 0
    except ValueError as e:
        print(f'Value error: {e}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        raise
    finally:
        print('Finally')
