def nested_except_with_continue(data_list):
    for item in data_list:
        try:
            result = process(item)
            if result is None:
                continue
        except ValueError:
            continue
        return result
    return None

def process(x):
    return x
