"""Round 29 — 最小复现：dict 字面量中夹带三元表达式时前序键值对丢失。

原始字节码形态（Python 3.11）：
    BUILD_MAP 0
    LOAD_CONST 'a'; ...; MAP_ADD 1        <- 无跳转块内
    ...
    LOAD_CONST 'd'; <三元: POP_JUMP_FORWARD_IF_NONE ...>; MAP_ADD 1   <- 引入跳转
    ...
"""
import os
import sys
import dis
import types
import marshal
import py_compile
import importlib.util

ROOT = r'F:\Downloads\pythoncdc-main'
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# CPython 3.11 仅当 dict 字面量 >= 16 对时才改用 BUILD_MAP 0 + MAP_ADD 序列
# （更少则整体折叠为常量 dict），故这里必须构造 >= 16 对才能复现。
_TERNARY_AT = 7  # 三元表达式所在的键值对下标（对应真实 order.pyc 的 futures_direction）


def _build_src():
    parts = []
    for i in range(17):
        if i == _TERNARY_AT:
            parts.append("            'k%02d': self._a%02d if self._a%02d is not None else None,"
                         % (i, i, i))
        else:
            parts.append("            'k%02d': self._a%02d," % (i, i))
    return ('class A(object):\n'
            '    def save(self):\n'
            '        return {\n' + '\n'.join(parts) + '\n        }\n')


SRC = _build_src()


def norm(co):
    out = []
    for ins in dis.get_instructions(co):
        if 'JUMP' in ins.opname or ins.opname == 'FOR_ITER':
            out.append((ins.opname, '<J>'))
        else:
            out.append((ins.opname, ins.argval))
    return out


def main():
    src_path = os.path.join(HERE, '_rd29_dict_ternary.py')
    pyc_path = os.path.join(HERE, '_rd29_dict_ternary.pyc')
    open(src_path, 'w', encoding='utf-8').write(SRC)
    try:
        py_compile.compile(src_path, pyc_path, doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)

        from pycdc import decompile_pyc
        with open(pyc_path, 'rb') as f:
            f.read(16)
            orig = marshal.load(f)

        def find(co, name, out):
            for c in co.co_consts:
                if isinstance(c, types.CodeType):
                    if c.co_name == name:
                        out.append(c)
                    find(c, name, out)

        o = []
        find(orig, 'save', o)
        oco = o[0]
        oins = list(dis.get_instructions(oco))
        n_map_add = sum(1 for x in oins if x.opname == 'MAP_ADD')
        print('原始 save(): %d 条指令, %d 个 MAP_ADD（即 %d 个键值对）'
              % (len(oins), n_map_add, n_map_add))

        src = decompile_pyc(pyc_path, use_cfg=True)
        i = src.find('def save(')
        print('--- 反编译结果 ---')
        print(src[i:i + 400] if i >= 0 else 'NOT FOUND')

        try:
            re_mod = compile(src, '<decomp>', 'exec')
        except SyntaxError as e:
            print('=== DIFF: 重编译失败 SyntaxError:', e)
            return
        r = []
        find(re_mod, 'save', r)
        if not r:
            print('=== DIFF: 重编译后找不到 save')
            return
        rins = list(dis.get_instructions(r[0]))
        n2 = sum(1 for x in rins if x.opname == 'MAP_ADD')
        print('重编译 save(): %d 条指令, %d 个 MAP_ADD' % (len(rins), n2))

        a, b = norm(oco), norm(r[0])
        if a == b:
            print('=== BYTE-IDENTICAL ===')
        else:
            print('=== DIFF (前 8 处) ===')
            shown = 0
            for i in range(max(len(a), len(b))):
                x = a[i] if i < len(a) else None
                y = b[i] if i < len(b) else None
                if x != y:
                    print('  %3d A:%s B:%s' % (i, x, y))
                    shown += 1
                    if shown >= 8:
                        break
    finally:
        for p in (src_path, pyc_path):
            try:
                os.remove(p)
            except OSError:
                pass


if __name__ == '__main__':
    main()
