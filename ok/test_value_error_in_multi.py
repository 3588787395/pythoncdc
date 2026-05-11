"""测试多个handler中的ValueError handler"""

def test_value_error_in_multi():
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
