# Source Generated with Decompyle++ (Python version)
# File: r3_a05_method_host.pyc (Python 3.11)

class C:
    def m(self, a):
        o = mk(a)
        if o is None:
            return None
        elif not is_trade():
            if o.symbol[:2] in ('11', '12'):
                info = 'CB'
            else:
                info = 'STK'
            LOG.info(info)
        return o.order_id
