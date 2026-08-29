"""Round 05 — G4 海象运算符下标/属性赋值最小复现集。

测试工程师交付物：构造 `target = (r := value)` 海象赋值（value 位置的海象，
目标为下标或属性）的 12 个最小复现，编译为 pyc，反编译回源码，并验证反编译
产物与原 pyc 字节码完全等价（opname + argval 序列一致），证明区域归约修复
对 G4 家族各变体闭合。

运行: D:/Python/python.exe make_repros.py
"""
import sys
import os
import dis
import types

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "minimal_repros")
os.makedirs(OUTDIR, exist_ok=True)

sys.path.insert(0, "F:/Downloads/pythoncdc-main")
from pycdc import decompile_pyc


# 每个复现： (编号, 函数名, 源码)。源码须为合法 3.11 模块，含至少一个 G4 海象赋值。
REPROS = [
    (1, "r01_simple_subscr",
     "def r01_simple_subscr(d, k, v):\n"
     "    d[k] = (r := v)\n"
     "    return r\n"),
    (2, "r02_subscr_call",
     "def r02_subscr_call(d, k):\n"
     "    d[k] = (r := make())\n"
     "    return r\n"
     "def make():\n"
     "    return 7\n"),
    (3, "r03_attr_simple",
     "def r03_attr_simple(obj, v):\n"
     "    obj.x = (r := v)\n"
     "    return r\n"),
    (4, "r04_attr_call",
     "def r04_attr_call(obj):\n"
     "    obj.x = (r := make())\n"
     "    return r\n"
     "def make():\n"
     "    return 7\n"),
    (5, "r05_subscr_computed_index",
     "def r05_subscr_computed_index(d, f):\n"
     "    d[f()] = (r := make())\n"
     "    return r\n"
     "def f():\n"
     "    return 0\n"
     "def make():\n"
     "    return 9\n"),
    (6, "r06_attr_subscr_container",
     "def r06_attr_subscr_container(self, k):\n"
     "    self.cache[k] = (r := make())\n"
     "    return r\n"
     "def make():\n"
     "    return 3\n"),
    (7, "r07_nested_subscr",
     "def r07_nested_subscr(a, b, c):\n"
     "    a[b][c] = (r := make())\n"
     "    return r\n"
     "def make():\n"
     "    return 1\n"),
    (8, "r08_binop_value",
     "def r08_binop_value(d, k, x, y):\n"
     "    d[k] = (r := x + y)\n"
     "    return r\n"),
    (9, "r09_method_value",
     "def r09_method_value(d, k, obj):\n"
     "    d[k] = (r := obj.method())\n"
     "    return r\n"),
    (10, "r10_except_handler",
     "def r10_except_handler(self, k):\n"
     "    try:\n"
     "        return self.d[k]\n"
     "    except KeyError:\n"
     "        self.d[k] = (r := make())\n"
     "        return r\n"
     "def make():\n"
     "    return 5\n"),
    (11, "r11_multilevel_attr",
     "def r11_multilevel_attr(o):\n"
     "    o.a.b = (r := make())\n"
     "    return r\n"
     "def make():\n"
     "    return 11\n"),
    (12, "r12_constant_value",
     "def r12_constant_value(d, k):\n"
     "    d[k] = (r := 42)\n"
     "    return r\n"),
]


def _func_code_from_source(source, func_name):
    """编译源码，取出指定函数的 code object（含嵌套定义的同名函数只取顶层）。"""
    mod = compile(source, "<orig>", "exec")
    funcs = {}
    for const in mod.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == func_name:
            funcs[const.co_name] = const
    return funcs.get(func_name)


def _dis_tuple(co):
    """返回 (opname, argval) 序列，忽略行号。"""
    seq = []
    for ins in dis.get_instructions(co):
        seq.append((ins.opname, ins.argval))
    return seq


def verify_bytecode(orig_co, decompiled_source, func_name):
    """反编译源码重新编译后，比较目标函数的 (opname, argval) 序列。"""
    mod2 = compile(decompiled_source, "<decomp>", "exec")
    co2 = None
    for const in mod2.co_consts:
        if isinstance(const, types.CodeType) and const.co_name == func_name:
            co2 = const
            break
    if co2 is None:
        return False, "recompiled module has no function %s" % func_name
    a = _dis_tuple(orig_co)
    b = _dis_tuple(co2)
    if a == b:
        return True, "bytecode identical (%d instrs)" % len(a)
    # 找首个差异
    for i in range(min(len(a), len(b))):
        if a[i] != b[i]:
            return False, "mismatch at instr %d: orig=%s decomp=%s" % (i, a[i], b[i])
    return False, "length differs orig=%d decomp=%d" % (len(a), len(b))


def main():
    passed = 0
    total = len(REPROS)
    for num, fname, src in REPROS:
        py_path = os.path.join(OUTDIR, "repro_%02d_%s.py" % (num, fname))
        with open(py_path, "w", encoding="utf-8") as f:
            f.write(src)
        # 编译源码为 pyc（内存 code object 即可，无需落盘）
        orig_co = _func_code_from_source(src, fname)
        if orig_co is None:
            print("[%02d] FAIL: cannot find orig func %s" % (num, fname))
            continue
        # 反编译：把源码编译成 pyc 字节后交给 pycdc（pycdc 接受 pyc 路径，
        # 这里直接复用 decompile_pyc 需要一个 .pyc 文件，故落盘 pyc）
        import py_compile
        pyc_path = py_path + "c"
        py_compile.compile(py_path, cfile=pyc_path, doraise=True, quiet=2)
        try:
            decompiled = decompile_pyc(pyc_path, use_cfg=True)
        except Exception as e:  # noqa
            print("[%02d] FAIL decompile: %s" % (num, e))
            continue
        dec_path = os.path.join(OUTDIR, "repro_%02d_%s_decompiled.py" % (num, fname))
        with open(dec_path, "w", encoding="utf-8") as f:
            f.write(decompiled)
        # 校验反编译产物包含海象（修复目标），且不包含 buggy 的 `target[None] =`
        has_walrus = "(%s :=" % ("r ") in decompiled or "(r:=" in decompiled
        has_buggy = "None] =" in decompiled or "[None] =" in decompiled
        ok, msg = verify_bytecode(orig_co, decompiled, fname)
        status = "PASS" if (ok and not has_buggy) else "FAIL"
        if ok and not has_buggy:
            passed += 1
        print("[%02d] %s %s | walrus=%s buggy=%s | %s" %
              (num, status, fname, has_walrus, has_buggy, msg))
    print("\n=== G4 repro result: %d/%d passed ===" % (passed, total))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
