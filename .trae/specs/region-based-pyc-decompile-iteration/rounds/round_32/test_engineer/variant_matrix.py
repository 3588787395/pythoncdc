# -*- coding: utf-8 -*-
"""变体矩阵：定位哪个结构要素导致 for 循环体丢失。"""
import subprocess
import sys
import os

ROOT = r"F:\Downloads\pythoncdc-main"
sys.path.insert(0, ROOT)
PYEXE = r"D:/Python/python.exe"

VARIANTS = {
    # A: order_response 结构：for + 循环内 try/except + 整体 try/finally
    "A_finally_inner_try": '''
def f(algo, datalist):
    algo.tmporders.write_lock.acquire()
    tmporders = algo.tmporders.get_instance()
    dict_map = algo._dict_map.get_instance()
    try:
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
    # B: trade 结构：for + if/elif 链 + 整体 try/finally
    "B_finally_elifchain": '''
def f(algo, datalist):
    algo.tmporders.write_lock.acquire()
    tmporders = algo.tmporders.get_instance()
    dict_map = algo._dict_map.get_instance()
    try:
        for order_item in datalist:
            entrust_no = order_item['entrust_no']
            if entrust_no in dict_map:
                order_id = dict_map[entrust_no]
                if order_id in tmporders:
                    order_obj = tmporders[order_id]
                else:
                    order_obj = algo.create_order_object(order_id, order_item)
                status = int(order_item['status'])
                if status in {5, 6}:
                    order_obj.filled = order_obj.filled + order_item['business_amount']
                elif status == 9:
                    order_obj.filled = 0
                else:
                    order_obj.filled += order_item['business_amount']
                order_obj.status = status
                tmporders[order_id] = order_obj
        algo.tmporders.set_instance(tmporders)
    finally:
        algo.tmporders.write_lock.release()
''',
    # C: for + 循环内 try/except，无 finally
    "C_nofinally_inner_try": '''
def f(algo, datalist):
    tmporders = algo.tmporders.get_instance()
    dict_map = algo._dict_map.get_instance()
    for order_item in datalist:
        entrust_no = order_item['entrust_no']
        if entrust_no in dict_map:
            order_id = dict_map[entrust_no]
            try:
                order_obj = tmporders[order_id]
            except BaseException:
                order_obj = algo.create_order_object(order_id, order_item)
            order_obj.status = int(order_item['status'])
            tmporders[order_id] = order_obj
    algo.tmporders.set_instance(tmporders)
''',
    # D: for + if/elif 链，无 finally
    "D_nofinally_elifchain": '''
def f(algo, datalist):
    tmporders = algo.tmporders.get_instance()
    dict_map = algo._dict_map.get_instance()
    for order_item in datalist:
        entrust_no = order_item['entrust_no']
        if entrust_no in dict_map:
            order_id = dict_map[entrust_no]
            if order_id in tmporders:
                order_obj = tmporders[order_id]
            else:
                order_obj = algo.create_order_object(order_id, order_item)
            status = int(order_item['status'])
            if status in {5, 6}:
                order_obj.filled = order_obj.filled + order_item['business_amount']
            elif status == 9:
                order_obj.filled = 0
            else:
                order_obj.filled += order_item['business_amount']
            order_obj.status = status
            tmporders[order_id] = order_obj
    algo.tmporders.set_instance(tmporders)
''',
    # E: 仅 try/finally + 纯 for 空转（无循环体复杂结构）
    "E_finally_plain_for": '''
def f(algo, datalist):
    tmporders = algo.tmporders.get_instance()
    try:
        for order_item in datalist:
            pass
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
    r = subprocess.run([PYEXE, "-c", CODE_TEMPLATE.replace("@ROOT@", ROOT).replace("@PYC@", pyc)], capture_output=True, text=True, cwd=ROOT)
    out = (r.stdout + r.stderr).strip().replace("\n", " | ")
    print("%-24s %s" % (name, out[:400]))
