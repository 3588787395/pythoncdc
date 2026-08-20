# Repro 7: multiple nested try-except blocks in for loop
data = [1, 'a', -5, 200]
result = {'valid': [], 'errors': [], 'count': 0}
for item in data:
    try:
        if isinstance(item, str):
            try:
                converted = int(item)
                result['valid'].append(converted)
            except ValueError:
                result['errors'].append(f'convert error: {item}')
                continue
        else:
            converted = item
        result['count'] += 1
        try:
            if converted > 100:
                result['valid'].append(converted // 10)
            elif converted < 0:
                result['valid'].append(abs(converted))
            else:
                result['valid'].append(converted * 2)
        except Exception as e:
            result['errors'].append(f'value error: {e}')
    except Exception as e:
        result['errors'].append(f'outer error: {e}')
    finally:
        print(f'processed: {item}')
