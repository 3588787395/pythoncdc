def r9lo_01_ortail_neg(self, items, trading_dt):
    de_listed = set()
    for o in items:
        i = self.data_proxy.get_assets(o)
        if not i or not (i.delisted_date > trading_dt):
            de_listed.add(o)
    if de_listed:
        self.publish(de_listed)
    return de_listed
