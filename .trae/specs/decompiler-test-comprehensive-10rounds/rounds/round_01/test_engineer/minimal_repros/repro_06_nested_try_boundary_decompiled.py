# Source Generated with Decompyle++ (Python version)
# File: repro_06_nested_try_boundary.pyc (Python 3.11)

__doc__ = '复现06: 嵌套try-except中内层try块边界识别错误'
def nested_try(data):
    result = {'valid': [], 'errors': []}
    for item in data:
        try:
            pass
        except ValueError:
            result['errors'].append(f'fail: {item}')
            print(f'done: {item}')
            return result
            converted = int(item)
            result['valid'].append(converted)
            continue
        except Exception as e:
            result['errors'].append(f'outer: {e}')
        finally:
            pass
