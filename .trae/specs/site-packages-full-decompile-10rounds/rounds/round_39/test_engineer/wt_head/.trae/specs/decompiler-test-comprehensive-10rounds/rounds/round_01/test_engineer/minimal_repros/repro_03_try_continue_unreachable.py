"""复现03: try-except-finally + for-continue结构中continue后代码被错误保留"""
def process(data):
    result = {'count': 0}
    for item in data:
        try:
            converted = int(item)
            result['count'] += 1
            continue
            result['count'] += 1  # 不可达代码
        except Exception as e:
            result['errors'] = str(e)
        finally:
            pass
    else:
        return result
