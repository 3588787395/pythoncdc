def test(url, params, request_times):
    returndata = None
    try:
        response = {'json': lambda: None}
        returndata = response['json']()
    except Exception as x:
        if request_times <= 1:
            request_times += 1
            returndata = test(url, params, request_times)
        elif isinstance(x, ValueError):
            error_info = str(x)
            print(error_info)
        else:
            print('unknown error')
    return returndata
