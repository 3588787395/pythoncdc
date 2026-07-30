"""repro_10: 综合 — for + if + if + continue 兄弟 + break（get_str_data 完整形态）。

测试 aspect: 完整复现 get_str_data instr_diff@179 的形态：
- for j in range(len(is_all_nan))  循环
- if is_all_nan[j] == True:        外层 if（false→break 路径）
  - if j == len(is_all_nan) - 1:   内层 if（无 else，false→回边）
    - data_is_nan = 1              STORE_FAST 赋值
  - continue                       兄弟语句（两分支均→回边）
- not_nan_icount = j               else 分支
- break                            退出循环

反编译器需正确生成 continue 兄弟语句，不可将外层+内层 if 条件合并为
`if A and B:`（会改变内层 if false 分支跳转目标：回边→post-loop = continue→break）。
"""


def get_str_data_repro(is_all_nan):
    data_is_nan = 0
    not_nan_icount = 0
    for j in range(len(is_all_nan)):
        if is_all_nan[j] == True:
            if j == len(is_all_nan) - 1:
                data_is_nan = 1
            continue
        not_nan_icount = j
        break
    return (data_is_nan, not_nan_icount)
