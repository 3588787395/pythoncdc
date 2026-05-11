"""测试真实的ValueError handler"""

def test_value_error_real(x):
    try:
        if x < 0:
            raise ValueError("Negative")
        return x
    except ValueError as e:
        print(f'Value error: {e}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        raise
