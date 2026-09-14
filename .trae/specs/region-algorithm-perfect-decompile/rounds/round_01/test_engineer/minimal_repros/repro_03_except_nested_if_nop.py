def h(data, info):
    try:
        params = eval(data)
        stock = params[0]
    except:
        if ')' not in data.split(',')[0]:
            stock = data.split(',')[0]
        else:
            stock = data
    return stock
