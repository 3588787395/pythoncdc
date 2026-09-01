
class Store:
    def set_one(self, d, key_obj, val):
        # container=attr, index=attr (the fly_api shape)
        self.instance_dict[key_obj.__name__] = val
        # simple triple
        d[key_obj] = val
        # container=attr, index=simple
        self.buf[k] = val
        # container=simple, index=attr
        m[key_obj.name] = val
        return d
