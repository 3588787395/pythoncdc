# -*- coding: utf-8 -*-
"""R16-A 13 UNCONFIRMED 探针：entry-steal 形状再往里塞一层 for。

「从最内层到最外层识别区域」原则下，外层 LoopRegion 应当在 IfRegion 之前就被归约，
理论上臂内子区域的消费顺序与深度无关；但也正因内层先归约，内层 try 可能已在
Loop 的臂收集里被合法发射 ⇒ 该形状可能天然不触发。

语料里**没有**已知的同类受害函数（`D:/Temp/r15_strict_all.txt` 的 DEFECT 行里
带 for 宿主的 only 是 IQEngine/utils/logger/handlers.pyc perform_rollover，
而 round15 的 r15a_10 已证它与本家族无关），故标 UNCONFIRMED：
实测应为 MATCH；若 MISMATCH 则记 REVIVED 并需扩大候选谓词的宿主范围。
"""


def check_shape_inside_for(items):
    out = []
    for v in items:
        if isinstance(v, str):
            try:
                valid = int(v) > 0 and int(v) < 100
            except ValueError:
                valid = False
            out.append(valid)
    return out
