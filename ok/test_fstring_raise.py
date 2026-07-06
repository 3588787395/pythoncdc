"""测试f-string在raise中的使用"""

def test_fstring_raise():
    try:
        response = {'code': 1, 'msg': 'Error'}
        if response.get('code') != 0:
            raise ValueError(f"API error: {response.get('msg')}")
        return response.get('data')
    except ValueError as e:
        print(f'Value error: {e}')
        raise
    except Exception as e:
        print(f'Unexpected error: {e}')
        raise
    finally:
        print('Finally')
