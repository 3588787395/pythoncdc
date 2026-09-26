# F-CROSS (flytools set_userid_containerid_dict): try/except with if/else where
# the else-arm `return None` and the function-tail implicit `return None` are two
# identical teardown blocks; the decompiler wires the loop-exit to the tail block
# and the else to the other (crossed edges vs orig).
cid = {}


def popen(cmd):
    return ['x']


def set_userid_containerid_dict():
    global cid
    dockerlist = []
    try:
        dockerlist = popen('docker ps -a -q').readlines()
        if len(dockerlist) > 0:
            tmplist = popen("docker inspect -f x $(docker ps -a -q)").readlines()
            for data in tmplist:
                tmp = data[9:-1].split(':')
                cid[tmp[0]] = tmp[1]
        else:
            return None
    except Exception as e:
        print(get_traceback_message())
        return None


def get_traceback_message():
    return 'tb'
