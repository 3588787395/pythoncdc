# -*- coding: utf-8 -*-
"""第二轮变体：try 包裹范围 / NOP / staticmethod / 类内方法 逐项逼近。"""
import dis
import os
import subprocess
import sys

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
PYEXE = r"D:/Python/python.exe"

VARIANTS = {
    # A2: try 从 acquire 前开始包住全部（与异常表 4->550 一致）
    "A2_try_wraps_all": '''
def f(algo, datalist):
    try:
        algo.tmporders.write_lock.acquire()
        tmporders = algo.tmporders.get_instance()
        dict_map = algo._dict_map.get_instance()
        for order_item in datalist:
            entrust_no = order_item['entrust_no']
            if entrust_no in dict_map:
                order_id = dict_map[entrust_no]
                try:
                    order_obj = tmporders[order_id]
                except BaseException:
                    system_log.error(get_traceback_message())
                    order_obj = algo.create_order_object(order_id, order_item)
                order_obj.status = int(order_item['status'])
                tmporders[order_id] = order_obj
        algo.tmporders.set_instance(tmporders)
    finally:
        algo.tmporders.write_lock.release()
''',
    # A3: 类内 staticmethod + try 包裹全部
    "A3_static_method": '''
class PtradeAccount:
    @staticmethod
    def order_response_order_update(algo, datalist):
        try:
            algo.tmporders.write_lock.acquire()
            tmporders = algo.tmporders.get_instance()
            dict_map = algo._dict_map.get_instance()
            for order_item in datalist:
                entrust_no = order_item['entrust_no']
                if entrust_no in dict_map:
                    order_id = dict_map[entrust_no]
                    try:
                        order_obj = tmporders[order_id]
                    except BaseException:
                        system_log.error(get_traceback_message())
                        order_obj = algo.create_order_object(order_id, order_item)
                    order_obj.status = int(order_item['status'])
                    tmporders[order_id] = order_obj
            algo.tmporders.set_instance(tmporders)
        finally:
            algo.tmporders.write_lock.release()
''',
    # A4: 模拟 NOP：try 块首加 pass? (pass 不产生 NOP, 用其他方式——循环内 try 首行 NOP 无法直接生成，先测 for-else 版本)
    "A4_for_else": '''
def f(algo, datalist):
    try:
        algo.tmporders.write_lock.acquire()
        tmporders = algo.tmporders.get_instance()
        dict_map = algo._dict_map.get_instance()
        for order_item in datalist:
            entrust_no = order_item['entrust_no']
            if entrust_no in dict_map:
                order_id = dict_map[entrust_no]
                try:
                    order_obj = tmporders[order_id]
                except BaseException:
                    system_log.error(get_traceback_message())
                    order_obj = algo.create_order_object(order_id, order_item)
                order_obj.status = int(order_item['status'])
                tmporders[order_id] = order_obj
        else:
            algo.tmporders.set_instance(tmporders)
    finally:
        algo.tmporders.write_lock.release()
''',
}

WORK = os.path.join(ROOT, ".trae", "specs", "region-based-pyc-decompile-iteration",
                    "rounds", "round_32", "test_engineer", "variant_work")
os.makedirs(WORK, exist_ok=True)

CODE_TEMPLATE = '''
import sys
sys.path.insert(0, r"@ROOT@")
from scripts import pyc_batch_verify as pbv
pyc = r"@PYC@"
single = pbv.decompile_single(pyc)
if not single["success"]:
    print("DECOMPILE-FAILED", single.get("error"))
else:
    d = pbv.bytecode_diff(pyc, single["ok_py_path"])
    if d.get("error"):
        print("DIFF-ERROR", d["error"])
    else:
        print("matched %s/%s rate=%.4f" % (d["matched_functions"], d["total_functions"], d["match_rate"]))
        for f in (d.get("mismatches") or []):
            fd = f.get("first_diff") or {}
            print("  MISMATCH %s orig=%s decomp=%s first=%s vs %s" % (
                f.get("name"), f.get("orig_count"), f.get("decomp_count"),
                fd.get("orig"), fd.get("decomp")))
'''

for name, src in VARIANTS.items():
    py = os.path.join(WORK, name + ".py")
    pyc = os.path.join(WORK, name + ".pyc")
    with open(py, "w", encoding="utf-8") as fh:
        fh.write(src)
    r = subprocess.run([PYEXE, "-c",
                        "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2])",
                        py, pyc], capture_output=True, text=True)
    if r.returncode != 0:
        print(name, "COMPILE-FAIL", r.stderr[-300:])
        continue
    r = subprocess.run([PYEXE, "-c", CODE_TEMPLATE.replace("@ROOT@", ROOT).replace("@PYC@", pyc)],
                       capture_output=True, text=True, cwd=ROOT)
    out = (r.stdout + r.stderr).strip().replace("\n", " | ")
    print("%-24s %s" % (name, out[:400]))

# 附带确认：3.11 中 NOP 的来源
probe = os.path.join(WORK, "nop_probe.py")
with open(probe, "w") as fh:
    fh.write("try:\n    pass\nfinally:\n    pass\n")
import marshal
r = subprocess.run([PYEXE, "-c", "import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2])", probe, probe + ".pyc"], capture_output=True, text=True)
with open(probe + ".pyc", "rb") as fh:
    fh.read(16)
    code = marshal.load(fh)
print("NOP probe (try/finally):", [i.opname for i in dis.get_instructions(code)])
