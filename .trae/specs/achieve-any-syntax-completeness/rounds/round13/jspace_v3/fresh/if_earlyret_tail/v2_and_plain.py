def f(epoch):
    if isinstance(epoch, int) and epoch >= 0:
        return epoch
    msg = f'got {epoch}'
    raise ValueError(msg)
