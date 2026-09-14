# Checklist

> 目标：site-packages 全量 47 个 partial pyc 反编译 100% 成功，字节码完全匹配
> 基线：355/402 OK (88.3%)，47 partial，156 个函数字节码不一致
> 验证脚本：scripts/pyc_batch_verify.py
> 禁止修改反编译生成的 OK.py 文件

## Round 01

- [ ] C1.1 strategy.pyc 反编译成功，所有函数字节码完全匹配
- [ ] C1.2 同目录生成 strategyOK.py 文件
- [ ] C1.3 pyc_index.json 中该文件 bytecode_match_rate=1.0, decompile_status="ok"
- [ ] C1.4 10+ 最小复现实例全部通过
- [ ] C1.5 quotation.pyc 回归验证通过（字节码无退化）
- [ ] C1.6 已 commit + push `spr-r24:`
- [ ] C1.7 修复符合区域归约算法 4 原则，无反模式新增

## Round 02

- [ ] C2.1 load_daily.pyc 反编译成功，所有函数字节码完全匹配
- [ ] C2.2 同目录生成 load_dailyOK.py 文件
- [ ] C2.3 pyc_index.json 更新
- [ ] C2.4 10+ 复现实例 + quotation.pyc + R01 回归通过
- [ ] C2.5 已 commit + push `spr-r25:`
- [ ] C2.6 无反模式新增

## Round 03

- [ ] C3.1 finance_data_source.pyc 反编译成功，字节码完全匹配
- [ ] C3.2 生成 finance_data_sourceOK.py + pyc_index.json 更新
- [ ] C3.3 10+ 复现实例 + quotation.pyc + R01-R02 回归通过
- [ ] C3.4 已 commit + push `spr-r26:`
- [ ] C3.5 无反模式新增

## Round 04

- [ ] C4.1 function.pyc 反编译成功，字节码完全匹配
- [ ] C4.2 生成 functionOK.py + pyc_index.json 更新
- [ ] C4.3 10+ 复现实例 + quotation.pyc + R01-R03 回归通过
- [ ] C4.4 已 commit + push `spr-r27:`
- [ ] C4.5 无反模式新增

## Round 05

- [ ] C5.1 matcher.pyc 反编译成功，字节码完全匹配
- [ ] C5.2 生成 matcherOK.py + pyc_index.json 更新
- [ ] C5.3 10+ 复现实例 + quotation.pyc + R01-R04 回归通过
- [ ] C5.4 已 commit + push `spr-r28:`
- [ ] C5.5 无反模式新增

## Round 06

- [ ] C6.1 asset_mixin.pyc 反编译成功，字节码完全匹配
- [ ] C6.2 生成 asset_mixinOK.py + pyc_index.json 更新
- [ ] C6.3 10+ 复现实例 + quotation.pyc + R01-R05 回归通过
- [ ] C6.4 已 commit + push `spr-r29:`
- [ ] C6.5 无反模式新增

## Round 07

- [ ] C7.1 future_param.pyc 反编译成功，字节码完全匹配
- [ ] C7.2 生成 future_paramOK.py + pyc_index.json 更新
- [ ] C7.3 10+ 复现实例 + quotation.pyc + R01-R06 回归通过
- [ ] C7.4 已 commit + push `spr-r30:`
- [ ] C7.5 无反模式新增

## Round 08

- [ ] C8.1 instance.pyc 反编译成功，字节码完全匹配
- [ ] C8.2 生成 instanceOK.py + pyc_index.json 更新
- [ ] C8.3 10+ 复现实例 + quotation.pyc + R01-R07 回归通过
- [ ] C8.4 已 commit + push `spr-r31:`
- [ ] C8.5 无反模式新增

## Round 09

- [ ] C9.1 __init__.pyc 反编译成功，字节码完全匹配
- [ ] C9.2 生成 __init__OK.py + pyc_index.json 更新
- [ ] C9.3 10+ 复现实例 + quotation.pyc + R01-R08 回归通过
- [ ] C9.4 已 commit + push `spr-r32:`
- [ ] C9.5 无反模式新增

## Round 10

- [ ] C10.1 logger.pyc 反编译成功，字节码完全匹配
- [ ] C10.2 生成 loggerOK.py + pyc_index.json 更新
- [ ] C10.3 10+ 复现实例 + quotation.pyc + R01-R09 回归通过
- [ ] C10.4 已 commit + push `spr-r33:`
- [ ] C10.5 无反模式新增

## 最终验证

- [ ] F1 10 轮全部完成，每轮至少一个 pyc 转为 OK
- [ ] F2 OK 数量从 355 增至至少 365
- [ ] F3 所有 10 个修复的 pyc 字节码完全匹配
- [ ] F4 区域归约算法 4 原则 FULLY COMPLIANT
- [ ] F5 quotation.pyc 始终无退化
- [ ] F6 无反模式新增（`_fix_`/`_patch_`/`_merge_` 前缀 0 新增）
- [ ] F7 累计成功率 >= 99%
