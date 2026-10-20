# [B70e-V3R5] g4b ground truth dis vs decompiled-recompiled dis
import dis, importlib.util, sys, py_compile, os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(BASE, '..', '..', '..', '..', '..'))
STAGE = os.path.normpath(os.path.join(BASE, '..', '..', 'test_repros', 'round5'))

def load_code_from_pyc(pyc):
    import marshal
    with open(pyc, 'rb') as fh:
        data = fh.read()
    return marshal.loads(data[16:])

def dis_mod(code, out):
    lines = []
    for const in code.co_consts:
        if hasattr(const, 'co_code'):
            lines.append('=' * 20 + ' ' + const.co_name + ' ' + '=' * 20)
            lines.extend(dis.Bytecode(const).dis().splitlines())
    lines.append('=' * 20 + ' <module> ' + '=' * 20)
    lines.extend(dis.Bytecode(code).dis().splitlines())
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines))

src_pyc = os.path.join(REPO, 'test_repros', 'round5', 'rec1_synth_g4b_b70_whiletrue_with.pyc')
code = load_code_from_pyc(src_pyc)
dis_mod(code, os.path.join(BASE, '_r5_b70e_g4b_src_dis.txt'))

ok = os.path.join(STAGE, 'rec1_g4b_rec1_synth_g4b_b70_whiletrue_withOK.py')
with open(ok, 'r', encoding='utf-8') as fh:
    txt = fh.read()
comp = compile(txt, 'g4b_ok', 'exec')
dis_mod(comp, os.path.join(BASE, '_r5_b70e_g4b_ok_dis.txt'))
print('done')
