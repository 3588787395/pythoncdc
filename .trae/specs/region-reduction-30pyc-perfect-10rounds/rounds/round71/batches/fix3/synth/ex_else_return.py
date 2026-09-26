# F-EXCTABLE / positive: try + except + else + finally where the else clause ends
# with a return. The else blocks are protected by the finally, not by the except
# handler, so the region analyzer must still recognise them as ast.Try.orelse.
def boot(config):
    try:
        value = load(config)
    except LookupError:
        value = None
    else:
        print('loaded')
        return value
    finally:
        done()
    return None


def load(cfg):
    return cfg['k']


def done():
    pass
