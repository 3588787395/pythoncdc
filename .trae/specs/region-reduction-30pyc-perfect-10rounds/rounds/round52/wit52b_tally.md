# R52-B 复现电池 `wit52b/`（12 例）逐臂结论

跑法（电池专用 runner，只编译+反编译+严格尺，不触碰 `core/`）：

```
python -X utf8 bat52b.py F:/Downloads/pythoncdc-main          D:/Temp/r52mine/wit52b   head    # 落地前
python -X utf8 bat52b.py D:/Temp/r52gate/mirr_c52ab           D:/Temp/r52mine/wit52b   c52ab   # 候选臂
```

逐例（`MISMATCH` 的缺陷消息逐字保留）：

| 复现体 | 形状 | 落地前 | 候选臂 R52-B |
|---|---|---|---|
| `r52b_01_join_after_chain` | `if a<b<c: x=2` 后接 `return x` | MISMATCH `w [seq_len] orig=17 decomp=19` | MATCH |
| `r52b_02_real_else_control` | 同形但**有真 else** | MATCH | MATCH |
| `r52b_03_chain_then_elif` | 比较链后接 `elif` | MATCH | MATCH |
| `r52b_04_negated_chain` | `if not (a<b<c):` | MATCH | MATCH |
| `r52b_05_value_context_sibling` | 链后接兄弟赋值再 `return` | MISMATCH `w [seq_len] orig=21 decomp=23` | MATCH |
| `r52b_06_chain_in_loop_body` | 链在 for 体内、体后还有语句 | MATCH | MATCH |
| `r52b_07_multi_statement_join` | 汇合块含多条语句 | MISMATCH `w [seq_len] orig=23 decomp=25` | MATCH |
| `r52b_08_two_chains_sequential` | 两条比较链前后相接 | MISMATCH `w [seq_len] orig=33 decomp=34` | MATCH |
| `r52b_09_chain_inside_or` | `if a<b<c or d:`（链嵌在 or 里） | MISMATCH `w [seq_len] orig=18 decomp=20` | **仍 MISMATCH**（同形残支，交下轮） |
| `r52b_10_chain_in_try` | 链在 try 体内 | MATCH | MATCH |
| `r52b_11_chain_then_fallout` | 链后接 `print` 隐式 return None | MISMATCH `w [seq_len] orig=21 decomp=23` | MATCH |
| `r52b_12_four_operand_chain` | `if a<b<c<d:` | MISMATCH `w [seq_len] orig=22 decomp=24` | MATCH |

计数：落地前 `MISMATCH=7 MATCH=5`；候选臂 `MISMATCH=1 MATCH=11`。
⇒ 7 个真实复现体中 6 个被 R52-B 修好，5 个阴性对照在两臂下均 MATCH（判据未过火），
1 个（`r52b_09`，比较链作为 `or` 的一元、汇合点由 boolop 自身的塌缩块承担）留作 Round 53 的入口。

`round16_sink` 金丝雀在落地核下仍为 15/15 MATCH（目录里的 `run_all.py` 是电池驱动脚本，不是复现体）。
`wit52/`（R51-A/R51-B 的 14 例）在落地核下 13/14，在合并臂 R52-A+R52-B 下 14/14（见 `g052_c52ab.log`）。
