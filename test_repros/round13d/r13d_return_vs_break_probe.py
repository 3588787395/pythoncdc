"""Round 13d 探针组 B：循环内的 `return` 被降级为 `break`（R13-W2-D）。

真实受害函数（三处，均为「只差 1 个函数」文件，delta=-1）：
  IQEngine/core/plugin_manager.pyc        PluginManager.set_engine      194/193
  IQData/manager/plugin_manager.pyc       PluginManager.set_engine      184/183
  IQEngine/plugins/plugin_system_control/__init__.pyc  AccountPlugin._terminate  43/42

行为后果：原始在该分支 `return`（函数结束），产物写成 `break`（跳出循环后
继续执行循环之后的语句）—— 控制流被改，不是字节码洁癖。

判据与 A 组相同：源码 -> 3.11.7 pyc -> 项目反编译器 -> OK.py -> 重编 -> 严格逐指令对照。
期望列 MISMATCH = 已知缺陷复现；MATCH = 负对照（证明不是「循环里的 return」一律误报）。
"""
import io
import os
import py_compile
import sys

ROOT = 'F:/Downloads/pythoncdc-main'
sys.path.insert(0, ROOT)

from scripts import pyc_batch_verify as pbv             # noqa: E402
from _r10_strict_check import strict_compare, _load_map  # noqa: E402

WORK = 'D:/Temp/r13dB'

SHAPES = [
    # --- 实测修正：裸 return 在「循环内有后续语句」时被正确处理，期望 MATCH ---
    ('p1_bare_return_after_loop', 'MATCH', '''
def g(xs):
    for x in xs:
        if x:
            return
    cleanup()
'''),
    # --- 真触发条件：return 紧跟在一条「值被丢弃」的语句之后 ---
    # p2: del（DELETE_SUBSCR 后跟 LOAD_CONST None; POP_TOP）+ return，= set_engine 原形
    ('p2_del_then_return_in_loop', 'MATCH', '''
def g(xs):
    for i, x in enumerate(xs):
        if not x:
            del xs[i]
            return
    finish(xs)
'''),
    # p3: return 带值 -> 实测不触发
    ('p3_return_value_in_loop', 'MATCH', '''
def g(xs):
    for x in xs:
        if x:
            return x
    return 0
'''),
    # p4: 方法调用语句（CALL 后 POP_TOP）+ return，= _terminate 原形
    ('p4_call_then_return_in_loop', 'MATCH', '''
def g(xs):
    for x in xs:
        if x:
            x.close()
            return
    cleanup()
'''),
    # p5: 赋值语句 + return（赋值不留 POP_TOP）-> 探针用于切分「POP_TOP 必要与否」
    ('p5_assign_then_return_in_loop', 'MATCH', '''
def g(xs):
    for x in xs:
        if x:
            y = 1
            return
    cleanup()
'''),
    # p6: 两条表达式语句 + return -> 探边界：只吞最后一个还是整段
    ('p6_two_calls_then_return_in_loop', 'MATCH', '''
def g(xs):
    for x in xs:
        if x:
            x.a()
            x.b()
            return
    cleanup()
'''),
    # p7: return 前一条是 POP_TOP 型语句，但 return 在循环外 -> 必须 MATCH
    ('n7_call_return_outside_loop', 'MATCH', '''
def g(xs):
    for x in xs:
        x.close()
    return
'''),
    # n1: 真的是 break —— 必须保持 MATCH
    ('n1_real_break', 'MATCH', '''
def g(xs):
    for x in xs:
        if x:
            break
    cleanup()
'''),
    # n2: 循环内 return 且循环是函数末尾 —— 必须保持 MATCH
    ('n2_return_at_loop_end_of_body', 'MATCH', '''
def g(xs):
    for x in xs:
        if x:
            return
'''),
    # n3: return 在循环外的 if 里 —— 必须保持 MATCH
    ('n3_return_in_bare_if', 'MATCH', '''
def g(xs):
    if xs:
        return
    cleanup()
'''),
]



def run_one(sid, expect, src):
    os.makedirs(WORK, exist_ok=True)
    py = os.path.join(WORK, sid + '.py')
    io.open(py, 'w', encoding='utf-8', newline='\n').write(src.lstrip('\n'))
    pyc = os.path.join(WORK, sid + '.pyc')
    py_compile.compile(py, cfile=pyc, doraise=True, quiet=2)
    out = os.path.join(WORK, sid + 'OUT.py')
    res = pbv.decompile_single(pyc, ok_py_path=out)
    if not res.get('success'):
        return sid, 'DECOMPILE-FAIL', res.get('error'), ''
    try:
        dec = py_compile.compile(out, doraise=True, quiet=2,
                                 cfile=os.path.join(WORK, sid + '_dec.pyc'))
    except Exception as e:
        return sid, 'COMPILE-FAIL', str(e), res['source']
    om, dm = _load_map(pyc), _load_map(dec)
    key = [k for k in om if k.endswith('g')][0]
    kind, msg, _ = strict_compare(om[key], dm[key])
    got = 'MATCH' if kind is None else 'MISMATCH'
    body = res['source'][res['source'].find('def g'):]
    return sid, got, ('%s %s' % (kind, msg)) if kind else 'ok', body


def main():
    print('== Round 13d B 组：return 被降级为 break ==')
    fails = 0
    unknown = []
    for sid, expect, src in SHAPES:
        _s, got, detail, body = run_one(sid, expect, src)
        if expect == 'UNKNOWN':
            unknown.append((sid, got, detail))
            print('  [MEAS] %-34s 实测=%-9s %s' % (sid, got, detail))
            if got == 'MISMATCH':
                for l in body.splitlines():
                    print('        | ' + l)
            continue
        ok = (got == expect)
        fails += 0 if ok else 1
        print('  [%s] %-34s expect=%-8s got=%-9s %s' %
              ('PASS' if ok else 'FAIL', sid, expect, got, detail))
        if got == 'MISMATCH':
            for l in body.splitlines():
                print('        | ' + l)
    print('== %d/%d PASS，测量项 %d ==' % (len(SHAPES) - len(unknown) - fails,
                                           len(SHAPES) - len(unknown), len(unknown)))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
