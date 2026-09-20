"""Round 10 回归用例。

Round 10 做的是【把尺子本身修正】，因此本文件同时承担两件事：
  1. 判定尺子的自证：证明「编译器版本差异」与「真缺陷」能被分开判定；
  2. 已修 / 未修缺陷的清单化自检。

第 1 件的证据（本文件 `--evidence` 段会复跑）：
  * 同一份源码 `sum(x for x in y if a and b)`，CPython 3.11.7 生成的
    genexpr 是 `POP_JUMP_BACKWARD_IF_FALSE -> 循环头`；
    而 site-packages 里的 pyc 是 `POP_JUMP_FORWARD_IF_FALSE -> JUMP_BACKWARD 桩
    -> 循环头`。两者**指令序列逐位相同、只有假出口形态不同**。
    => 这是 CPython 3.11 小版本的代码生成差异，不是反编译器的缺陷。
  * 「函数末尾隐式 return None」的组数差异则**是**真缺陷：同一份源码，
    `return None` 写在内层 if 体内（3 组）与提升到外层 if 体（2 组）在 3.11.7
    上截然不同 —— 反编译器生成了后者，原始 pyc 是前者。

  旧的 Round 9 严格口径把第 1 类也算成缺陷，得出「36 个假 ok」的结论 ——
  那是尺子错了，不是程序错了。本文件用的是修正后的口径
  （`_r10_strict_check.py`）：跳转按「追踪无条件跳转桩后的终点指令」比较，
  方向（FORWARD/BACKWARD）归一化；非跳转指令仍必须逐位相同。

用例（对真实 pyc 断言，而不是对 synthetic 片段）：
  D  exception.__exit__ 的 return None 归属（已修，官方 + 真实共 3 个副本）
  E  cgroup_utils 的 try 体末尾隐式 return None 重复（未修）
  F  crypto_utils.aes_encrypt 的 isinstance 守卫被外层条件链吞并（未修）

用法：
  python test_repro/round10_regressions.py            # 跑用例
  python test_repro/round10_regressions.py --evidence # 只跑尺子自证
"""
import dis
import importlib.util
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

_spec = importlib.util.spec_from_file_location(
    '_r10_strict_check', str(ROOT / '_r10_strict_check.py'))
_r10 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_r10)

# 旧尺子（Round 9）用于对照：它把编译器版本差异也判成缺陷。
_r9 = None
_r9_path = ROOT / '_r9_strict_check.py'
if _r9_path.exists():
    _s9 = importlib.util.spec_from_file_location('_r9_strict_check', str(_r9_path))
    _r9 = importlib.util.module_from_spec(_s9)
    _s9.loader.exec_module(_r9)


# ---------------------------------------------------------------- 尺子自证

NOISE = ('NOP', 'CACHE', 'PRECALL', 'EXTENDED_ARG')


def _find(code, name):
    for k in code.co_consts:
        if hasattr(k, 'co_name'):
            if k.co_name == name:
                return k
            r = _find(k, name)
            if r is not None:
                return r
    return None


def _ops(code):
    return [(i.opname, i.argrepr) for i in dis.get_instructions(code)
            if i.opname not in NOISE]


def evidence():
    """证明 genexpr 的 F/B 差异是编译器版本差异，而 return None 组数不是。"""
    ok = True

    # --- 1) genexpr 假出口形态 -------------------------------------------
    src = ('class E:\n    BUY = 1\n'
           'def f(y):\n'
           '    return sum(o.x for o in y if o.d == E.BUY and o.e == 2)\n')
    new_gen = _find(compile(src, '<new>', 'exec'), '<genexpr>')
    new_ops = _ops(new_gen)
    new_fw = sum(1 for op, _ in new_ops if op == 'POP_JUMP_FORWARD_IF_FALSE')
    new_bw = sum(1 for op, _ in new_ops if op == 'POP_JUMP_BACKWARD_IF_FALSE')
    print('[证据1] 3.11.7 对本机源码生成的 genexpr 假出口：'
          'FORWARD=%d BACKWARD=%d' % (new_fw, new_bw))
    if new_bw < 2 or new_fw != 0:
        print('        !! 本机 3.11.7 的形态与预期（全 BACKWARD）不符')
        ok = False

    old_pyc = ROOT / 'site-packages/IQEngine/plugins/plugin_system_accounts/position_model/option_position.pyc'
    if old_pyc.exists():
        import marshal
        with open(old_pyc, 'rb') as f:
            f.read(16)
            old_mod = marshal.load(f)
        g = _find(_find(old_mod, 'buy_open_order_amount'), '<genexpr>')
        old_ops = _ops(g)
        old_fw = sum(1 for op, _ in old_ops if op == 'POP_JUMP_FORWARD_IF_FALSE')
        old_bw = sum(1 for op, _ in old_ops if op == 'POP_JUMP_BACKWARD_IF_FALSE')
        print('[证据1] site-packages 里同一形态 genexpr 的假出口：'
              'FORWARD=%d BACKWARD=%d' % (old_fw, old_bw))
        if old_fw == 0:
            print('        !! 该 pyc 的形态与预期不符')
            ok = False
        # 非跳转指令序列的比较不在此处做（源码文本无法逐字重建），
        # 改用两把尺子对同一 pyc 的判定来证明：旧尺子把版本差异当缺陷，
        # 新尺子把它归一化掉。
        if _r9 is not None:
            r_old = _r9.check_pyc(str(old_pyc))
            r_new = _r10.check_pyc(str(old_pyc))
            o_ok = (r_old['ok'] == r_old['functions']) if (r_old and 'error' not in r_old) else None
            n_ok = (r_new['ok'] == r_new['functions']) if (r_new and 'error' not in r_new) else None
            print('[证据1] 旧尺子(_r9)判定=%-10s 新尺子(_r10)判定=%s'
                  % ('一致' if o_ok else '有缺陷', '一致' if n_ok else '有缺陷'))
            if o_ok is not False or n_ok is not True:
                print('        !! 预期是「旧尺子判缺陷、新尺子判一致」')
                ok = False
    else:
        print('[证据1] 跳过（样本 pyc 不存在）')

    # --- 2) 隐式 return None 的组数 ---------------------------------------
    def count_ret_none(code):
        ops = [op for op, _ in _ops(code)]
        return sum(1 for i in range(len(ops) - 1)
                   if ops[i] == 'LOAD_CONST' and ops[i + 1] == 'RETURN_VALUE')

    body_inner = ('def f(self, v):\n'
                  '    if v is not None:\n'
                  "        x = getattr(v, 'A', 'B')\n"
                  '        if self.force or x == 1:\n'
                  "            setattr(v, 'C', self.d)\n"
                  '            return None\n'
                  '    else:\n'
                  '        return None\n')
    body_outer = ('def f(self, v):\n'
                  '    if v is not None:\n'
                  "        x = getattr(v, 'A', 'B')\n"
                  '        if self.force or x == 1:\n'
                  "            setattr(v, 'C', self.d)\n"
                  '        return None\n'
                  '    else:\n'
                  '        return None\n')
    n_in = count_ret_none(compile(body_inner, '<i>', 'exec').co_consts[0])
    n_out = count_ret_none(compile(body_outer, '<o>', 'exec').co_consts[0])
    print('[证据2] return None 写在内层 if 体内：%d 组；提升到外层 if 体：%d 组'
          % (n_in, n_out))
    if not (n_in == 3 and n_out == 2):
        print('        !! 与预期（3 / 2）不符，证据失效')
        ok = False
    print('[证据2] 原始 pyc 的 __exit__ 是 3 组 -> 它属于「内层写法」，'
          '反编译器原先输出「外层写法」即为真缺陷。')
    return ok


# ------------------------------------------------------------------ 用例

CASES = [
    # (名称, 相对路径, known_unfixed)
    ('D  exception.__exit__ 的 return None 归属（已修）',
     'site-packages/IQCommon/exception.pyc', False),
    ('D2 IQData/utils/exception.pyc（已修，同族副本）',
     'site-packages/IQData/utils/exception.pyc', False),
    ('D3 IQEngine/utils/exception.pyc（已修，同族副本）',
     'site-packages/IQEngine/utils/exception.pyc', False),
    ('E  cgroup_utils try 体末尾隐式 return None 重复（未修）',
     'site-packages/IQCommon/util/cgroup_utils.pyc', True),
    ('F  crypto_utils 的 isinstance 守卫被外层条件链吞并（未修）',
     'site-packages/IQCommon/util/crypto_utils.pyc', True),
]


def main():
    if '--evidence' in sys.argv:
        return 0 if evidence() else 1
    evidence()
    print()
    bad = 0
    for name, rel, known_unfixed in CASES:
        p = ROOT / rel
        if not p.exists():
            print('[SKIP] %s（文件不存在）' % name)
            continue
        r = _r10.check_pyc(str(p))
        if r is None:
            print('[SKIP] %s（缺少 OK.py）' % name)
            continue
        if 'error' in r:
            print('[ERR ] %s: %s' % (name, r['error']))
            bad += 1
            continue
        fixed = (r['ok'] == r['functions'])
        if known_unfixed:
            tag = 'FIXED' if fixed else 'KNOWN-UNFIXED'
        else:
            tag = 'PASS' if fixed else 'FAIL'
            if not fixed:
                bad += 1
        print('[%s] %s  (%d/%d)' % (tag, name, r['ok'], r['functions']))
        for nm, kind, msg in r['bad'][:4]:
            print('          - %s: [%s] %s' % (nm, kind, msg))
    print('\n失败用例数（不含已知未修）: %d' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
