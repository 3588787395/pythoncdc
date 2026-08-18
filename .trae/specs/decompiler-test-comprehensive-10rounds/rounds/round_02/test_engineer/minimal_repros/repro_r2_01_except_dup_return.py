"""复现R2-01: except块中return False被重复生成"""
def test_except_duplicate_return(data):
    try:
        for item in data:
            if item > 100:
                break
            elif item < 0:
                continue
            else:
                continue
        else:
            return True
    except Exception as e:
        print(f'error: {e}')
        return False
        return False
    return False
