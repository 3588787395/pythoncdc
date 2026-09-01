"""复现06: 嵌套try-except中内层try块边界识别错误"""
def nested_try(data):
    result = {'valid': [], 'errors': []}
    for item in data:
        try:
            try:
                converted = int(item)
                result['valid'].append(converted)
            except ValueError:
                result['errors'].append(f'fail: {item}')
            print(f'done: {item}')
            continue
        except Exception as e:
            result['errors'].append(f'outer: {e}')
        finally:
            pass
    else:
        return result
