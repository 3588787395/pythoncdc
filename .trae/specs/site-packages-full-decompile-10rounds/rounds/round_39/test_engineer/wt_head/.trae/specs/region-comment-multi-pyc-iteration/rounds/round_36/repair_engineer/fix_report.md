# R36 修复工程师报告

## 修复概要

### Fix: 推导式 iter 属性访问误判为方法调用
**文件**: `core/cfg/code_generator.py`
**修复位置**: 
1. `_generate_comprehensions_from_dict` 行 4957-4959（dict 路径）
2. `_generate_comprehensions` 行 5343-5350（ASTComprehension 路径）

**根因**: 代码生成器在推导式 `iter` 字段为 `Attribute` 类型时，错误添加 `()` 使其变成方法调用。
```python
# 修复前（bug）:
iter_code = self._generate_annotation_from_dict(iter_obj) + '()'
# 修复后:
iter_code = self._generate_expression(iter_obj, 0)
```

**算法依据**: 区域归约算法要求 AST 映射唯一且正确。`Attribute` 类型表示属性访问（`self.orders`），不应被渲染为方法调用（`self.orders()`）。如果属性确实是方法调用（如 `data.values()`），`iter` 字段应为 `Call` 类型（`func=Attribute, args=[]`），而非裸 `Attribute` 类型。

## 回归测试结果
- 累计匹配率: 84.03% → **84.16%** (+0.13%, +9 matched functions)
- OK 文件: 218 → **220** (+2)
- Partial: 184 → **182** (-2)
- Failed: 0

## 残留不一致
- Pattern SA（语句顺序差异）: ~15 函数 in trade_live_broker.pyc
- 其他 partial 文件的深层缺陷待逐个修复
