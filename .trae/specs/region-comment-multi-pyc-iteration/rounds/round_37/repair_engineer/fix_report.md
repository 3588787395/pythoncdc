# R37 修复工程师报告

## 分析概要

### 常见不匹配模式分析（Top 10 文件，219 个不匹配函数）

| 模式 | 出现次数 | 描述 |
|------|---------|------|
| LOAD_FAST vs LOAD_GLOBAL | 47 | 变量作用域解析错误 |
| LOAD_FAST vs LOAD_FAST | 24 | 变量名错误（参数顺序） |
| LOAD_ATTR vs LOAD_CONST | 19 | 属性访问 vs 常量加载（语句顺序） |
| LOAD_CONST vs LOAD_FAST | 19 | 常量 vs 局部变量（语句顺序） |
| POP_JUMP_*_IF_*_NONE vs same | 36 | 跳转目标差异（已部分修复） |
| LOAD_METHOD vs LOAD_FAST | 17 | 方法调用 vs 局部变量（语句顺序） |
| LOAD_GLOBAL vs RETURN_VALUE | 12 | 语句顺序严重错位 |
| PUSH_EXC_INFO vs RETURN_VALUE | 12 | try-except 块生成问题 |

### 根因分类
1. **语句顺序错位**（~60%）：反编译器生成的语句顺序与原始字节码不一致，导致级联 diff
2. **变量作用域错误**（~25%）：LOAD_FAST/LOAD_GLOBAL 混淆
3. **try-except 块问题**（~10%）：PUSH_EXC_INFO/RETURN_VALUE 顺序
4. **其他**（~5%）

## 回归测试结果
- 累计匹配率: 84.16% → **84.27%** (+0.11%, +7 matched)
- OK 文件: 220 → **221** (+1)
- Partial: 182 → **181** (-1)

## 后续优先级
1. R38: 修复 try-except 块中 PUSH_EXC_INFO/RETURN_VALUE 顺序问题
2. R39: 修复 if-elif 链中语句顺序错位
3. R40: 修复变量作用域解析（LOAD_FAST vs LOAD_GLOBAL）
