# F-THENOVER (flytools.ProcessWrite.set_userid_containerid_dict): two guards whose
# bodies are `return None` compile to adjacent return blocks with distinct targets
# (A -> 310, B -> 314); decompiler merges/re-targets them.
def set_userid_containerid_dict(d, uid, cid, extra):
    if not uid:
        d = {}
        return None
    if not cid:
        return None
    for k in list(d):
        if k not in extra:
            del d[k]
    return d
