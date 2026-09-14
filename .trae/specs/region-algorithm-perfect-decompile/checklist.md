# Checklist

> 目标：site-packages 全量 58 个 partial pyc 反编译 100% 成功，字节码完全匹配
> 基线：344/402 OK (85.6%)，58 partial，317 个函数字节码不一致
> 核心失败模式：try/except 内嵌套结构边界错误(150)、for/while 与 try 交互错位(166)、recomp_shorter(153)、recomp_longer(103)、same_length_diff(47)、async 函数语句丢失(7)、missing_func(14)

## Round 01

- [ ] C1.1 jq_trans_module.pyc 反编译成功，所有函数字节码完全匹配
- [ ] C1.2 同目录生成 jq_trans_moduleOK.py 文件
- [ ] C1.3 pyc_index.json 中该文件 bytecode_match_rate=1.0, decompile_status="ok"
- [ ] C1.4 10+ 最小复现实例全部通过
- [ ] C1.5 quotation.pyc 回归验证通过（字节码无退化）
- [ ] C1.6 已 commit + push `spr-r01:`
- [ ] C1.7 修复符合区域归约算法 4 原则，无反模式新增（`_fix_`/`_patch_`/`_merge_` 前缀 0 新增）
- [ ] C1.8 受影响方法的 docstring 已更新（6 节/4 节模板）

## Round 02

- [ ] C2.1 flytools.pyc 反编译成功，所有函数字节码完全匹配
- [ ] C2.2 同目录生成 flytoolsOK.py 文件
- [ ] C2.3 pyc_index.json 中该文件 bytecode_match_rate=1.0, decompile_status="ok"
- [ ] C2.4 10+ 最小复现实例全部通过
- [ ] C2.5 quotation.pyc + jq_trans_module.pyc 回归验证通过
- [ ] C2.6 已 commit + push `spr-r02:`
- [ ] C2.7 无反模式新增
- [ ] C2.8 受影响方法的 docstring 已更新

## Round 03

- [ ] C3.1 db_base.pyc 反编译成功，所有函数字节码完全匹配
- [ ] C3.2 同目录生成 db_baseOK.py 文件
- [ ] C3.3 pyc_index.json 中该文件 bytecode_match_rate=1.0, decompile_status="ok"
- [ ] C3.4 10+ 最小复现实例全部通过
- [ ] C3.5 quotation.pyc + R01-R02 回归验证通过
- [ ] C3.6 已 commit + push `spr-r03:`
- [ ] C3.7 无反模式新增
- [ ] C3.8 受影响方法的 docstring 已更新

## Round 04

- [ ] C4.1 function.pyc 反编译成功，所有函数字节码完全匹配
- [ ] C4.2 同目录生成 functionOK.py 文件
- [ ] C4.3 pyc_index.json 更新
- [ ] C4.4 10+ 复现实例 + quotation.pyc + R01-R03 回归通过
- [ ] C4.5 已 commit + push `spr-r04:`
- [ ] C4.6 无反模式新增 + docstring 更新

## Round 05

- [ ] C5.1 strategy.pyc 反编译成功，所有函数字节码完全匹配
- [ ] C5.2 同目录生成 strategyOK.py 文件
- [ ] C5.3 pyc_index.json 更新
- [ ] C5.4 10+ 复现实例 + quotation.pyc + R01-R04 回归通过
- [ ] C5.5 已 commit + push `spr-r05:`
- [ ] C5.6 无反模式新增 + docstring 更新

## Round 06

- [ ] C6.1 matcher.pyc 反编译成功，字节码完全匹配
- [ ] C6.2 生成 matcherOK.py + pyc_index.json 更新
- [ ] C6.3 10+ 复现实例 + quotation.pyc + R01-R05 回归通过
- [ ] C6.4 已 commit + push `spr-r06:`
- [ ] C6.5 无反模式新增 + docstring 更新

## Round 07

- [ ] C7.1 main.pyc 反编译成功，字节码完全匹配
- [ ] C7.2 生成 mainOK.py + pyc_index.json 更新
- [ ] C7.3 10+ 复现实例 + quotation.pyc + R01-R06 回归通过
- [ ] C7.4 已 commit + push `spr-r07:`
- [ ] C7.5 无反模式新增 + docstring 更新

## Round 08

- [ ] C8.1 interface.pyc 反编译成功，字节码完全匹配
- [ ] C8.2 生成 interfaceOK.py + pyc_index.json 更新
- [ ] C8.3 10+ 复现实例 + quotation.pyc + R01-R07 回归通过
- [ ] C8.4 已 commit + push `spr-r08:`
- [ ] C8.5 无反模式新增 + docstring 更新

## Round 09

- [ ] C9.1 quote.pyc 反编译成功，字节码完全匹配
- [ ] C9.2 生成 quoteOK.py + pyc_index.json 更新
- [ ] C9.3 10+ 复现实例 + quotation.pyc + R01-R08 回归通过
- [ ] C9.4 已 commit + push `spr-r09:`
- [ ] C9.5 无反模式新增 + docstring 更新

## Round 10

- [ ] C10.1 replace_utils.pyc 反编译成功，字节码完全匹配
- [ ] C10.2 生成 replace_utilsOK.py + pyc_index.json 更新
- [ ] C10.3 10+ 复现实例 + quotation.pyc + R01-R09 回归通过
- [ ] C10.4 已 commit + push `spr-r10:`
- [ ] C10.5 无反模式新增 + docstring 更新

## 最终验证

- [ ] F1 10 轮全部完成，每轮至少一个 pyc 转为 OK
- [ ] F2 OK 数量从 344 增至至少 354
- [ ] F3 所有 10 个修复的 pyc 字节码完全匹配
- [ ] F4 区域归约算法 4 原则 FULLY COMPLIANT
- [ ] F5 quotation.pyc 始终无退化
- [ ] F6 所有受影响方法 docstring 符合 6 节/4 节模板
- [ ] F7 无反模式新增（`_fix_`/`_patch_`/`_merge_` 前缀 0 新增）
