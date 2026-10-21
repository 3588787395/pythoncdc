#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L3 §7 汇总：把探针读数整理成「族 / 构型 / 判定 / 失败单元」表（供报告引用）。"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

LOG = ".trae/specs/attack-completeness-claims/rounds/round5/logs/l3_probes_l3final.json"

META = {
    "l3_g1_r2_boolop_ternary_while.py": ("R2", "BoolOp 左操作数为三元 + while 宿主 / and-or 交替链尾三元"),
    "l3_g2_r3_assert_try_else.py": ("R3", "assert 位于 try-else 体 / handler 内 raise-from"),
    "l3_g3_r4_await_asyncwith_finally.py": ("R4", "await 在 async-with 体内与 finally 内 / await 在 for 体"),
    "l3_g4_r5_match_mapping_star_guard.py": ("R5", "mapping+**rest+sequence(star)+guard / mapping 守卫"),
    "l3_g5_r6_handler_continue.py": ("R6", "handler 内 continue（for / while）"),
    "l3_g5b_r6_handler_continue_matrix.py": ("R6", "handler continue 2×2（for/while × 裸/带前置语句）"),
    "l3_g5c_r6_handler_continue_observable.py": ("R6", "handler continue 丢弃的**执行级可观测**变体（handler 内 i+=2）"),
    "l3_g6_r7_del_ternary_slice.py": ("R7", "del/augassign 的 slice 边界为三元（含 step）"),
    "l3_g7_r8_finally_conditional_return.py": ("R8", "finally 体含条件 return"),
    "l3_g7b_r8_finally_sideeffect.py": ("R8", "finally 体含副作用 / 嵌套 finally"),
    "l3_g7c_r8_finally_sideeffect_return.py": ("R8", "finally 体同时含副作用与 return（副本重复可观测）"),
    "l3_g7d_r8_finally_sideeffect_observable.py": ("R8", "finally 副本重复的**执行级可观测**变体（返回该列表）"),
    "l3_o1_overlay_six.py": ("OVERLAY-a", "if×for×try×match×with×async 深度≥3"),
    "l3_o2_overlay_boolop_ternary_await.py": ("OVERLAY-b", "BoolOp + 三元 + await 同一条件式"),
    "l3_o3_overlay_loopelse_break_finally.py": ("OVERLAY-c", "for-else + break + finally + handler"),
    "l3_o4_overlay_matchguard_with_comp.py": ("OVERLAY-d", "match guard + with + 推导式"),
    "l3_o5_overlay_augassign_del_slice.py": ("OVERLAY-e", "augassign + delete + slice + return"),
    "l3_o6_overlay_match_in_with_after.py": ("OVERLAY-d'", "match × with（with 在 for 内）⇒ match 之后同体语句丢失"),
    "l3_b142_nested_finally_copy.py": ("B142", "嵌套 finally 副本归属 / 内层 finally 含条件段"),
    "l3_b143_break_in_finally.py": ("B143", "finally 内 break（单层 for）"),
    "l3_b143b_break_in_finally_shapes.py": ("B143", "finally 内 break 五形态枚举"),
}


def main():
    with open(LOG, encoding="utf-8") as f:
        data = json.load(f)
    print("| 探针 | 族 | 构型 | 文件判定 | 单元 | 失败单元 |")
    print("|---|---|---|---|---|---|")
    for r in data["probes"]:
        fam, desc = META.get(r["name"], ("?", "?"))
        fails = [x.replace("***<module>.", "").replace(": Failure: ", " → ") for x in (r.get("failures") or [])]
        print("| `%s` | %s | %s | %s | %s/%s | %s |" % (
            r["name"].replace(".py", ""), fam, desc, r.get("status"),
            r.get("units_success"), r.get("units_total"),
            "; ".join(fails) if fails else "—"))
    tot = sum(r.get("units_total") or 0 for r in data["probes"])
    ok = sum(r.get("units_success") or 0 for r in data["probes"])
    nf = sum(1 for r in data["probes"] if r.get("status") != "success")
    print()
    print("总计：探针 %d / 单元 %d/%d / 非 success 文件 %d" % (len(data["probes"]), ok, tot, nf))


if __name__ == "__main__":
    main()
