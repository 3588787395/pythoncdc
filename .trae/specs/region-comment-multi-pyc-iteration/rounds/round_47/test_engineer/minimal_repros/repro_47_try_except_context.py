def func(handler):
    result_list = []
    if handler:
        try:
            result_list.append(handler.id)
        except Exception:
            result_list = []
    return result_list
