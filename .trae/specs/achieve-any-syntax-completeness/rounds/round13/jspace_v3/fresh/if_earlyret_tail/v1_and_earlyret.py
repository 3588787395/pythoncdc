def f(value):
    epoch = value or 0
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    msg = f'got {epoch}'
    raise ValueError(msg)
