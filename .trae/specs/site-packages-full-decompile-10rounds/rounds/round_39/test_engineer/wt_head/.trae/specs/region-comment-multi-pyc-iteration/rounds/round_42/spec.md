# R42 Spec Round — COPY_FREE_VARS/MAKE_CELL 噪声过滤 + PUSH_EXC_INFO 根因分析

## 修复概述

### Fix: 添加 COPY_FREE_VARS 和 MAKE_CELL 到噪声过滤集 (base.py)
- **问题**: `testqouter/round1/base.py` 的 `_filter_noise_instrs` 函数未过滤
  Python 3.11 的 `COPY_FREE_VARS` 和 `MAKE_CELL` 指令。
- **影响**: `COPY_FREE_VARS` 在反编译代码中缺失（16 个函数），导致后续所有指令
  偏移 1 位，产生级联假阳性 true_diffs。`MAKE_CELL` 也有类似问题。
- **修复**: 将 `COPY_FREE_VARS` 和 `MAKE_CELL` 添加到 `_NOISE_OPS` 集合。
  这两个指令都是编译器自动生成的闭包相关指令，无语义效果：
  - `COPY_FREE_VARS`: 将自由变量从外层作用域复制到函数的 cell 数组
  - `MAKE_CELL`: 为嵌套函数引用的变量创建 cell 对象
  实际闭包访问通过 `LOAD_DEREF`/`STORE_DEREF`/`LOAD_CLOSURE` 完成，仍被比较。
- **效果**: 修复了指令对齐，但匹配率维持 86.67%（受影响函数有其他底层真实差异）。

## 全量分析结果

### PUSH_EXC_INFO 模式分析 (74 次出现，最大系统性问题)
- **根因**: try-except 区域重建不完整，except handler body 中的语句丢失。
- **典型案例**: `klinedata.pyc` 的 `get_kline_by_date_new` 函数：
  - 原始 except 块包含 `system_log.error(f'获取数据异常: {error_info}')` 调用
  - 反编译结果完全丢失了这行代码
  - 导致后续 24 条指令全部错位

### LOAD_GLOBAL->LOAD_FAST 模式分析 (50→59 次出现)
- **根因**: 不是作用域问题，而是指令错位——某处缺少/多余语句导致后续 LOAD_GLOBAL
  与 LOAD_FAST 在相同位置被比较。
- **受影响文件**: strategy.pyc (10 个函数)、klinedata.pyc (4 个函数) 等

### SAME_OP:LOAD_CONST 模式分析 (44 次出现)
- **根因**: 全部是真实语义差异，包括：
  - 导入名差异 (`read_config` vs `FlyDataSource`)
  - 默认参数值差异 (`True` vs `None`)
  - 名称重整差异 (`__load_table_names` vs `_BaseDatabase__load_table_names`)
  - SQL 字符串差异

## 验证结果
- 批量验证: 5735/6617 = 86.67%（与 R41 一致）
- OK 文件: 229 / Partial: 173 / Failed: 0
- 回归测试: 待确认

## 方法注释模板 (6/4 节)
### base.py - _filter_noise_instrs 方法
- **修改说明 (6/4)**:
  - 前 4 行（修改概要）: R42 将 COPY_FREE_VARS 和 MAKE_CELL 添加到 _NOISE_OPS
    集合，过滤 Python 3.11 编译器自动生成的闭包相关指令，防止其在字节码
    比较中引起指令对齐错位。
  - 后 4 行（技术依据）: COPY_FREE_VARS 复制自由变量到函数 cell 数组（函数入口），
    MAKE_CELL 为变量创建 cell 对象（模块级）。两者均由编译器闭包分析自动生成，
    无语义效果。实际闭包访问通过 LOAD_DEREF/STORE_DEREF/LOAD_CLOSURE 完成，
    这些指令仍被比较，不丢失语义检查。
