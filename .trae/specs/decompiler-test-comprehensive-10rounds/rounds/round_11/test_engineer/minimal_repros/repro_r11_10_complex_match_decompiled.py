# Source Generated with Decompyle++ (Python version)
# File: repro_r11_10_complex_match.pyc (Python 3.11)

data = [1, 'a', -5, 200, 'abc']
result = {'valid_data': [], 'errors': [], 'processed_count': 0}
for item in data:
    try:
        if isinstance(item, str):
            try:
                converted = int(item)
                result['valid_data'].append(converted)
            except ValueError:
                result['errors'].append(f'string convert failed: {item}')
        else:
            converted = item
        print(f'processed item: {item}')
        continue
        print(f'processing item: {item}')
        result['processed_count'] += 1
        try:
            if converted > 100:
                result['valid_data'].append(converted // 10)
            elif converted < 0:
                result['valid_data'].append(abs(converted))
            else:
                result['valid_data'].append(converted * 2)
        except Exception as e:
            result['errors'].append(f'value error: {e}')
    except Exception as e:
        result['errors'].append(f'outer error: {e}')
    finally:
        pass
