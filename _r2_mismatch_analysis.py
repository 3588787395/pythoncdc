import sys, os, json, marshal, types, dis
sys.path.insert(0, 'F:/Downloads/pythoncdc-main')
from testqouter.round1.base import compare_bytecode

def extract(co):
    r = {}
    r[co.co_name or '<module>'] = co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r.update(extract(c))
    return r

files = [
    ('future_contract_info', 'site-packages/fly/common/future_contract_info.pyc'),
    ('common_func_iqd', 'site-packages/IQData/utils/common_func.pyc'),
    ('strategy', 'site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc'),
    ('load_daily', 'site-packages/fly/dumpload/load_daily.pyc'),
    ('common_func_iqc', 'site-packages/IQCommon/util/common_func.pyc'),
    ('finance_ds', 'site-packages/IQData/plugins/plugin_system_local_finance/finance_data_source.pyc'),
    ('matcher', 'site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc'),
    ('asset_mixin', 'site-packages/IQEngine/data/asset_mixin.pyc'),
    ('future_param', 'site-packages/fly/common/future_param.pyc'),
    ('persist', 'site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc'),
    ('default_event', 'site-packages/IQEngine/plugins/plugin_system_event_source/default_event_source.pyc'),
    ('itn', 'site-packages/fly/oauthenticator/itn.pyc'),
    ('realtime_event', 'site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc'),
    ('oauth2', 'site-packages/fly/oauthenticator/oauth2.pyc'),
]

base = 'F:/Downloads/pythoncdc-main/'
for label, f in files:
    pyc = base + f
    ok = pyc.replace('.pyc', 'OK.py')
    if not os.path.exists(pyc) or not os.path.exists(ok):
        print(label + ': files not found')
        continue
    with open(pyc, 'rb') as fh:
        fh.read(16)
        orig = marshal.load(fh)
    import py_compile
    try:
        cf = py_compile.compile(ok, doraise=True, quiet=2)
        if cf is None:
            import importlib.util
            cf = importlib.util.cache_from_source(ok)
        with open(cf, 'rb') as fh:
            fh.read(16)
            decomp = marshal.load(fh)
    except:
        print(label + ': compile error')
        continue
    om = extract(orig)
    dm = extract(decomp)
    common = sorted(set(om.keys()) & set(dm.keys()))
    for name in common:
        cmp = compare_bytecode(om[name], dm[name])
        if not cmp.get('match') and not cmp.get('jump_only'):
            td = cmp.get('true_diffs', [])
            jd = cmp.get('jump_diffs', [])
            oc = cmp.get('orig_count', 0)
            dc = cmp.get('decomp_count', 0)
            print(label + ': ' + name + ' orig=' + str(oc) + ' decomp=' + str(dc) + ' jd=' + str(len(jd)) + ' td=' + str(len(td)))
            if td:
                t = td[0]
                idx = t.get('index', 0)
                oo = t.get('orig_op', '')
                do = t.get('decomp_op', '')
                print('  first_td: idx=' + str(idx) + ' orig=' + oo + ' decomp=' + do)
