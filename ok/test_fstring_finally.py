"""测试f-string在finally中的使用"""

def test_fstring_finally():
    context = None
    socket = None
    try:
        context = 1
        socket = 2
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
        if socket:
            socket.close()
        if context:
            context.term()
