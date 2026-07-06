"""测试三个handler和finally的最小实例"""

def test_three_handlers_finally():
    try:
        x = 1 / 0
    except ZeroDivisionError as e:
        print(f'ZeroDivisionError: {e}')
        raise
    except ValueError as e:
        print(f'Value error: {e}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        raise
    finally:
        print('Finally')
