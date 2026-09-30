## core/cfg/region_analyzer.py
_identify_loop_regions                               L3782   识别条件:True 归约:True AST映射:True C1C2C3:False doclen:5057
_identify_try_except_regions                         L7603   识别条件:True 归约:True AST映射:True C1C2C3:False doclen:5687
_identify_empty_body_finally_regions                 L9016   识别条件:True 归约:True AST映射:False C1C2C3:False doclen:1987
_identify_with_regions                               L12282  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:6463
_identify_match_regions                              L12920  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:4397
_identify_nested_match_regions                       L14044  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:4516
_identify_assert_regions                             L14799  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:6936
_identify_chained_compare_regions                    L15495  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:4805
_identify_conditional_regions                        L15981  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:7036
_identify_ternary_regions                            L20515  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:6898
_identify_boolop_regions                             L23420  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:8219
_identify_sequence_regions                           L27519  识别条件:True 归约:True AST映射:True C1C2C3:False doclen:4384
## core/cfg/region_ast_generator.py (识别相关)

# 缺口结论（round76 基线，2026-09-30）
- 三要素（识别条件/归约/AST映射）：12/12 基本齐全；唯一缺口 _identify_empty_body_finally_regions 缺「AST 映射」段
- C1/C2/C3 不变式声明：0/12 —— 本规范新要求，修复工程师触及任一方法时必须补写
- region_ast_generator.py 无 _identify_* 方法（生成器方法另行在触及时按三要素+不变式声明补写）
