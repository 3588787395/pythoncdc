def repro_08(data, fields, arr):
    try:
        for f in fields:
            for i in range(10):
                try:
                    arr[f][i] = data[f][i]
                except:
                    pass
        else:
            arr['price'] = arr['close']
            return arr
    except Exception as e:
        log(e)
