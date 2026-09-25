import io,os,sys,hashlib,py_compile,importlib.util as iu
sys.path.insert(0,r'F:/Downloads/pythoncdc-main'); os.chdir(r'F:/Downloads/pythoncdc-main')
sys.stdout.reconfigure(encoding='utf-8')
import pycdc
_s=iu.spec_from_file_location('pbv', r'F:/Downloads/pythoncdc-main/scripts/pyc_batch_verify.py')
pbv=iu.module_from_spec(_s); _s.loader.exec_module(pbv)
V = {}
V['v1'] = '''
def p(datetime_list, freq, frequency, dts):
    offset = int(freq) // 5 if int(freq) // 5 else 1
    datetime_list = datetime_list[offset:]
    if datetime_list and int(frequency[:-1]) >= 5:
        del datetime_list[0]
    if dts[-1] in datetime_list:
        datetime_list.append(dts[-1])
    return datetime_list
'''
V['v2'] = '''
def p(datetime_list, freq, frequency, dts):
    offset = int(freq) // 5 if int(freq) // 5 else 1
    datetime_list = datetime_list[offset:]
    if datetime_list and int(frequency[:-1]) >= 5:
        del datetime_list[0]
    if dts[-1] in datetime_list:
        datetime_list.append(dts[-1])
    datetime_list = list(set(datetime_list))
    datetime_list.sort()
    x = datetime_list[0] if datetime_list else 0
    return (x, datetime_list)
'''
V['v3'] = V['v1'].replace('    if dts[-1] in datetime_list:', '    if dts[0] in datetime_list:').replace('datetime_list.append(dts[-1])','datetime_list.append(dts[0])')
for k,src in V.items():
    py='synth/%s.py'%k; io.open(py,'w',encoding='utf-8').write(src)
    pyc='synth/%s.pyc'%k; py_compile.compile(py,cfile=pyc,doraise=True)
    txt=pycdc.decompile_pyc(os.path.abspath(pyc))
    out='synth/%sOK.py'%k; io.open(out,'w',encoding='utf-8').write(txt)
    r=pbv.bytecode_diff(os.path.abspath(pyc), out)
    print('%-4s landed %s/%s %s'%(k,r['matched_functions'],r['total_functions'],
        [[m['name'],m['orig_count'],m['decomp_count'],m['jump_diffs'],m['true_diffs']] for m in r['mismatches']]))
