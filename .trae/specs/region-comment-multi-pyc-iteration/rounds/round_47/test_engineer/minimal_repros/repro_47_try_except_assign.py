def func(result_list):
    try:
        result_list.append(1)
    except Exception:
        result_list = []
    return result_list
