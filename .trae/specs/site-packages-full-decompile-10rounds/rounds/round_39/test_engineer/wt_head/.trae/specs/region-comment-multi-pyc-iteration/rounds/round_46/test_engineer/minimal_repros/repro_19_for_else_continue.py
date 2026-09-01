def func(kwargs):
    new_kwargs = {}
    for side in ("sell", "buy"):
        avg = 0
        for key in ("_old", "_today"):
            key = side + key
            amount = int(kwargs.get(key + "_amount", 0))
            if amount > 0:
                price = float(kwargs.get(key + "_price", 0))
                if price <= 0:
                    price = 0
                avg = (avg + price) / 2 if avg else price
            continue
        new_kwargs[side + "_avg"] = avg
    else:
        if new_kwargs:
            return new_kwargs
        else:
            raise ValueError("error")
