# -*- coding: utf-8 -*-
"""Round 63 batch 4 最小复现：IF_ELIF_CHAIN 祖先区域内、嵌套 if/else 的 **else 臂**
三元 return 语句被整块吞掉。

形状（对应 IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc
:: HistoryDataSource.get_price 的 L466-L470）：

  · 外层 `if len(arr) == 0:` 的两条内层臂都以 return 终止 ⇒ 区域分析器把后续代码
    并成该 if 的 else（region_type = IF_ELIF_CHAIN）；
  · 内层 `if flag == '1d': return A if key is None else A[key]` 的 else 臂是
    `return B if key is None else B[key]`（独立 TernaryRegion）；
  · 该 TernaryRegion 的 entry 落在 IF_ELIF_CHAIN 祖先的 **blocks 全集**里，
    但不等于祖先 entry ⇒ `_generate_region` 的 should_skip 守卫整块让位，
    else 臂语句发射为 None ⇒ 丢失 `return B ...`。

阴性对照 negative_pair_no_elif_chain：外层 if 的后继不再是 elif 链
（then 臂不终止于 return），同形状的 else 臂三元在 landed 态就是正确的，
证明丢失只在 IF_ELIF_CHAIN 祖先下发生。

用法（在 diag4 工作区，ROOT 已指向本代理私有镜像）:
  python -X utf8 -m py_compile test_repros/round63_b4/r63b4_tern_in_elif_chain.py
  python -X utf8 h62.py run --arm=landed --list=<该 .pyc 绝对路径的单行清单> \
         --out=dump/r63b4_landed.jsonl
  python -X utf8 h62.py run --arm=c1     --list=<同上>  --out=dump/r63b4_c1.jsonl
  python -X utf8 D:/Temp/opencode/r63gate/cmp_arms.py dump/r63b4_landed.jsonl \
         dump/r63b4_c1.jsonl landed c1
"""

A = 'day-array'
B = 'bar-array'


def pick(arr, flag, key, mode):
    if len(arr) == 0:
        if flag == '1d':
            return A if key is None else A[key]
        return B if key is None else B[key]
    if mode is not None:
        return arr if key is None else arr[key]
    return arr


def negative_pair_no_elif_chain(arr, flag, key, mode):
    # 外层 then 臂以 `total += 1` 结尾（不终止），故不构成 elif 链；
    # 同形状的 else 臂三元在 landed 态即可正确发射（阴性对照）。
    total = 0
    if len(arr) == 0:
        if flag == '1d':
            total += 1
        total += 2
    if mode is not None:
        return arr if key is None else arr[key]
    return total
