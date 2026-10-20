import os, hashlib

def h(p):
    if not os.path.exists(p):
        return "MISSING"
    return hashlib.sha1(open(p, "rb").read()).hexdigest()[:12]

pairs = [
    ("base_u", r"site-packages/IQEngine/utils/__init__OK.py"),
    ("base_c", r"site-packages/IQData/plugins/plugin_system_client_db/client_dbOK.py"),
    ("cur_u", r"site-packages/IQEngine/utils/__init__OK.py"),
    ("cur_c", r"site-packages/IQData/plugins/plugin_system_client_db/client_dbOK.py"),
]
for a, b in pairs:
    ap = r"d:/Temp/opencode/" + a + ".py"
    print(a, "exists=%s" % os.path.exists(ap), "same=%s" % (h(ap) == h(b)), h(ap), h(b))
