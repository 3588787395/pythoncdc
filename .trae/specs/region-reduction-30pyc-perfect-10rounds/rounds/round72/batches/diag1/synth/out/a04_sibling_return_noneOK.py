# Source Generated with Decompyle++ (Python version)
# File: a04_sibling_return_none.pyc (Python 3.11)

def post(user, cgroupmode, set_cgroup_config, spawn_single_user):
    if user is None:
        return None
    elif user.spawner:
        if user.spawn_pending:
            return None
        else:
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
