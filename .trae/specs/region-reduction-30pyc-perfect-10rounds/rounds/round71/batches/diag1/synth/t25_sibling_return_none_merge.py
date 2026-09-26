# F-THENOVER (oauth2 OAuthCallbackHandler.post / HSIDOAuthCallbackHandler.post):
# `return None` guards in sibling branches compile to adjacent return-None blocks;
# decompiler merges/reorders them so the guard's jump re-targets (A@534 -> 638 vs
# B -> 642, delta +4).
def post(user, cgroupmode, set_cgroup_config, spawn_single_user):
    if user is None:
        return None
    if user.spawner:
        if user.spawn_pending:
            return None
        status = user.spawner.poll()
        if status is not None:
            spawn_single_user(user)
            if cgroupmode == '1':
                set_cgroup_config()
                return None
            else:
                return None
    else:
        spawn_single_user(user)
        if cgroupmode == '1':
            set_cgroup_config()
            return None
        else:
            return None
    return None
