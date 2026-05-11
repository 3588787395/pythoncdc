"""测试复杂的try块"""

def test_complex_try():
    context = None
    socket = None
    try:
        import os
        context = 1
        socket = 2
        response = 3
        if response != 0:
            raise ValueError("Error")
        return response
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
