"""复现R2-11: except handler中重复return"""
def test_except_repeat_return(data):
    try:
        for item in data:
            if item > 100:
                break
        else:
            return True
    except Exception as e:
        print(f'error: {e}')
        return False
    return False
