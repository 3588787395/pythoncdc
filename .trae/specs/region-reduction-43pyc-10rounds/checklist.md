# Checklist

> 目标：site-packages 全量 pyc 反编译 100% 成功，字节码完全匹配
> 当前状态：359/402 OK (89.3%)，42 partial，1 failed

## Round 01 — IQCommon/common/main.pyc

- [ ] C01.1 IQCommon/common/main.pyc 反编译成功，字节码完全匹配
- [ ] C01.2 同目录生成 mainOK.py 文件
- [ ] C01.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C01.4 10+ 最小复现实例全部通过
- [ ] C01.5 既有测试矩阵无退化
- [ ] C01.6 已 commit + push `rr43-r01:`
- [ ] C01.7 无反模式新增
- [ ] C01.8 quotation.pyc 回归验证通过

## Round 02 — IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc

- [ ] C02.1 strategy.pyc 反编译成功，字节码完全匹配
- [ ] C02.2 同目录生成 strategyOK.py 文件
- [ ] C02.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C02.4 10+ 最小复现实例全部通过
- [ ] C02.5 既有测试矩阵无退化
- [ ] C02.6 已 commit + push `rr43-r02:`
- [ ] C02.7 无反模式新增
- [ ] C02.8 quotation.pyc 回归验证通过

## Round 03 — IQEngine/plugins/plugin_system_trade/function.pyc

- [ ] C03.1 function.pyc 反编译成功，字节码完全匹配
- [ ] C03.2 同目录生成 functionOK.py 文件
- [ ] C03.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C03.4 10+ 最小复现实例全部通过
- [ ] C03.5 既有测试矩阵无退化
- [ ] C03.6 已 commit + push `rr43-r03:`
- [ ] C03.7 无反模式新增
- [ ] C03.8 quotation.pyc 回归验证通过

## Round 04 — fly/dumpload/load_daily.pyc

- [ ] C04.1 load_daily.pyc 反编译成功，字节码完全匹配
- [ ] C04.2 同目录生成 load_dailyOK.py 文件
- [ ] C04.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C04.4 10+ 最小复现实例全部通过
- [ ] C04.5 既有测试矩阵无退化
- [ ] C04.6 已 commit + push `rr43-r04:`
- [ ] C04.7 无反模式新增
- [ ] C04.8 quotation.pyc 回归验证通过

## Round 05 — IQData/plugins/plugin_system_local_finance/finance_data_source.pyc

- [ ] C05.1 finance_data_source.pyc 反编译成功，字节码完全匹配
- [ ] C05.2 同目录生成 finance_data_sourceOK.py 文件
- [ ] C05.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C05.4 10+ 最小复现实例全部通过
- [ ] C05.5 既有测试矩阵无退化
- [ ] C05.6 已 commit + push `rr43-r05:`
- [ ] C05.7 无反模式新增
- [ ] C05.8 quotation.pyc 回归验证通过

## Round 06 — IQEngine/plugins/plugin_system_matcher/matcher.pyc

- [ ] C06.1 matcher.pyc 反编译成功，字节码完全匹配
- [ ] C06.2 同目录生成 matcherOK.py 文件
- [ ] C06.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C06.4 10+ 最小复现实例全部通过
- [ ] C06.5 既有测试矩阵无退化
- [ ] C06.6 已 commit + push `rr43-r06:`
- [ ] C06.7 无反模式新增
- [ ] C06.8 quotation.pyc 回归验证通过

## Round 07 — IQEngine/data/asset_mixin.pyc

- [ ] C07.1 asset_mixin.pyc 反编译成功，字节码完全匹配
- [ ] C07.2 同目录生成 asset_mixinOK.py 文件
- [ ] C07.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C07.4 10+ 最小复现实例全部通过
- [ ] C07.5 既有测试矩阵无退化
- [ ] C07.6 已 commit + push `rr43-r07:`
- [ ] C07.7 无反模式新增
- [ ] C07.8 quotation.pyc 回归验证通过

## Round 08 — fly/common/future_param.pyc

- [ ] C08.1 future_param.pyc 反编译成功，字节码完全匹配
- [ ] C08.2 同目录生成 future_paramOK.py 文件
- [ ] C08.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C08.4 10+ 最小复现实例全部通过
- [ ] C08.5 既有测试矩阵无退化
- [ ] C08.6 已 commit + push `rr43-r08:`
- [ ] C08.7 无反模式新增
- [ ] C08.8 quotation.pyc 回归验证通过

## Round 09 — IQEngine/plugins/plugin_system_persist/__init__.pyc

- [ ] C09.1 __init__.pyc 反编译成功，字节码完全匹配
- [ ] C09.2 同目录生成 __init__OK.py 文件
- [ ] C09.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C09.4 10+ 最小复现实例全部通过
- [ ] C09.5 既有测试矩阵无退化
- [ ] C09.6 已 commit + push `rr43-r09:`
- [ ] C09.7 无反模式新增
- [ ] C09.8 quotation.pyc 回归验证通过

## Round 10 — fly/logger.pyc

- [ ] C10.1 fly/logger.pyc 反编译成功，字节码完全匹配
- [ ] C10.2 同目录生成 loggerOK.py 文件
- [ ] C10.3 pyc_index.json 中该文件状态更新为 "ok"
- [ ] C10.4 10+ 最小复现实例全部通过
- [ ] C10.5 既有测试矩阵无退化
- [ ] C10.6 已 commit + push `rr43-r10:`
- [ ] C10.7 无反模式新增
- [ ] C10.8 quotation.pyc 回归验证通过

## 最终验证

- [ ] F1 10 轮全部完成，每轮至少一个 pyc 转为 OK
- [ ] F2 OK 数量从 359 增至至少 369
- [ ] F3 所有修复的 pyc 字节码完全匹配
- [ ] F4 区域归约算法 4 原则 FULLY COMPLIANT
- [ ] F5 quotation.pyc 保持 100% 匹配
