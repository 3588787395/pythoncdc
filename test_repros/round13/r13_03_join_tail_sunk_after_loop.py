# -*- coding: utf-8 -*-
"""R13-C 复现（有 else 臂变体，delta=-1）：if/elif/else 链中**唯一能落空到链尾**的臂
以可落空子区域（for/while/with/try/无 else 的 if）结束，链后共享语句被吸入该臂。

实测（run_all.py，严格尺子）：seq_len 19 -> 18，少一条 JUMP_FORWARD。
产物形态（实测输出）：
    if c: return 1
    elif r:
        for d in r: x = x + d
        x = 7          <<< 链后语句被吸进 elif 臂
        return None
    else:  return 2
原始语义「链尾无条件执行」被改成「仅当 elif 成立才执行」—— 控制流被改，非布局问题。

对应真实目标（本轮基线里报 seq_len -1 / +2 的那一族）：
  IQCommon/util/backtest_info_utils.pyc  <module>.creat_sheet1   [seq_diff] #958
      orig=('<JUMP>','JUMP') decomp=("'row'",'LOAD_FAST')  —— 链尾 `row += 1` 被吸进分支
  IQEngine/plugins/plugin_fly_data/fly_api/setting_api.pyc  <module>.set_parameters
      [seq_diff] #111 同族
  （drift 记录：2026-09-20 21:0x 实测这两个 pyc **已翻正**（creat_sheet1 1655->1655 MATCH、
   set_parameters 170->170 MATCH），因为并发进行的 R13-A3 修复改的是**循环体内**那一个
   子形态（臂含 continue → NCPD 退化为循环头）。本文件复现的是**函数体层**子形态，
   严格尺子下仍然 MISMATCH，见 r13_23/24/25 三个负对照划出的边界。）

归约层证据见 test_repros/round13/ANALYSIS.md 的 R13-C 节。
"""


def g(c, r, x):
    if c:
        return 1
    elif r:
        for d in r:
            x = x + d
    else:
        return 2
    x = 7
