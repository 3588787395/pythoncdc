def outer(e):
    def convert(cls):
        body = {}
        body["_n_"] = member_names = []
        body["_m_"] = member_map = {}
        body["_t_"] = member_type = e.t
        for k, v in cls.__dict__.items():
            member_names.append(k)
            member_map[k] = v
        return member_type
    return convert
