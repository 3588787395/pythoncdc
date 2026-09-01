import sys, marshal, types, os
sys.path.insert(0, r'F:\Downloads\pythoncdc-main')
from core.cfg.cfg_builder import build_cfg
from core.cfg.region_analyzer import RegionAnalyzer
from core.cfg.region_ast_generator import RegionASTGenerator

pyc = r'F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_system_trade\trade_live_broker.pyc'
with open(pyc, 'rb') as f:
    f.read(16)
    top = marshal.load(f)

def find_code(co, name):
    if co.co_name == name: return co
    for c in co.co_consts:
        if isinstance(c, types.CodeType):
            r = find_code(c, name)
            if r: return r
    return None

co = find_code(top, '_process_order')
cfg = build_cfg(co)
ra = RegionAnalyzer(cfg, co)
ra.analyze()
gen = RegionASTGenerator(cfg, co, ra)
result = gen.generate()
stmts = result.get('body', [])

def _s(node):
    if not isinstance(node, dict): return repr(node)[:60]
    t = node.get('type','?')
    if t == 'Name': return node.get('id','?')
    if t == 'Constant': return repr(node.get('value',''))[:40]
    if t == 'Call': 
        f = node.get('func',{})
        return 'Call(%s)' % _s(f)
    if t == 'Attribute': return '%s.%s' % (_s(node.get('value',{})), node.get('attr','?'))
    if t == 'IfExp': return '(%s if %s else %s)' % (_s(node.get('body',{})), _s(node.get('test',{})), _s(node.get('orelse',{})))
    if t == 'Compare': return '%s %s %s' % (_s(node.get('left',{})), node.get('ops',[('?',)])[0][0] if node.get('ops') else '?', _s(node.get('comparators',[{}])[0]) if node.get('comparators') else '?')
    if t == 'JoinedStr': return 'fstr'
    if t == 'BoolOp': return 'BoolOp(%s)' % node.get('op','?')
    if t == 'BinOp': return 'BinOp'
    if t == 'Subscript': return 'Subscr'
    return t

def dump(stmts, indent=0):
    for s in stmts:
        if isinstance(s, str):
            print(' '*indent + 'STR: ' + s[:80])
            continue
        if not isinstance(s, dict):
            print(' '*indent + repr(s)[:80])
            continue
        t = s.get('type','?')
        if t == 'Assign':
            tgt = s.get('targets',[{}])[0].get('id','?')
            val = s.get('value',{})
            vt = val.get('type','?')
            if vt == 'IfExp':
                test = val.get('test',{})
                body = val.get('body',{})
                orelse = val.get('orelse',{})
                print(' '*indent + 'Assign %s = IfExp(test=%s, body=%s, orelse=%s)' % (tgt, _s(test), _s(body), _s(orelse)))
            elif vt == 'Call':
                func = val.get('func',{})
                print(' '*indent + 'Assign %s = Call(%s, args=%d)' % (tgt, _s(func), len(val.get('args',[]))))
            elif vt == 'Name':
                print(' '*indent + 'Assign %s = Name(%s)' % (tgt, val.get('id','?')))
            elif vt == 'Constant':
                print(' '*indent + 'Assign %s = %s' % (tgt, repr(val.get('value',''))[:40]))
            else:
                print(' '*indent + 'Assign %s = %s' % (tgt, vt))
        elif t == 'Expr':
            val = s.get('value',{})
            vt = val.get('type','?')
            if vt == 'Call':
                func = val.get('func',{})
                print(' '*indent + 'Expr(Call(%s, args=%d))' % (_s(func), len(val.get('args',[]))))
            elif vt == 'IfExp':
                print(' '*indent + 'Expr(IfExp(test=%s, body=%s, orelse=%s))' % (_s(val.get('test',{})), _s(val.get('body',{})), _s(val.get('orelse',{}))))
            else:
                print(' '*indent + 'Expr(%s)' % vt)
        elif t == 'If':
            test = s.get('test',{})
            print(' '*indent + 'If(test=%s):' % _s(test))
            dump(s.get('body',[]), indent+2)
            orelse = s.get('orelse',[])
            if orelse:
                print(' '*indent + 'Else:')
                dump(orelse, indent+2)
        elif t == 'Try':
            print(' '*indent + 'Try:')
            dump(s.get('body',[]), indent+2)
            for h in s.get('handlers',[]):
                print(' '*indent + 'Except:')
                dump(h.get('body',[]), indent+2)
        elif t == 'Return':
            val = s.get('value',{})
            print(' '*indent + 'Return(%s)' % _s(val))
        elif t == 'For':
            print(' '*indent + 'For:')
            dump(s.get('body',[]), indent+2)
        elif t == 'While':
            print(' '*indent + 'While:')
            dump(s.get('body',[]), indent+2)
        elif t == 'Pass':
            print(' '*indent + 'Pass')
        else:
            print(' '*indent + t)

dump(stmts)
