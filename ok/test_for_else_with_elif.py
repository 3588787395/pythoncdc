def func(lines):
    all_stocks_list = []
    for line in lines:
        all_stocks_list.append(line.strip('\n'))
    else:
        if isinstance(lines, str):
            lines = [lines]
        elif isinstance(lines, list):
            pass
        else:
            return {}
    return all_stocks_list
