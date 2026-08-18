"""复现R2-06: 嵌套try-except中内层try的else块识别"""
def test_nested_try_else(data):
    result = []
    for item in data:
        try:
            try:
                converted = int(item)
                result.append(converted)
            except ValueError:
                result.append(0)
            print(f'done: {item}')
        except Exception as e:
            result.append(-1)
    else:
        return result
