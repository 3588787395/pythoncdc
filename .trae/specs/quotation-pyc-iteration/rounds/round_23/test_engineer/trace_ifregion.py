"""R23-N2 调试：追踪 convert_to_list 中所有 IfRegion 处理"""
import sys
sys.path.insert(0, '/workspace')

import core.cfg.region_ast_generator as rag_mod

# 找到处理 IfRegion 的方法
for attr_name in sorted(dir(rag_mod.RegionASTGenerator)):
    if 'if' in attr_name.lower() and ('region' in attr_name.lower() or 'condition' in attr_name.lower() or 'build' in attr_name.lower()):
        print(f"Method: {attr_name}")

# 找 _build_condition* 方法
print("\n=== _build_condition* methods ===")
for attr_name in sorted(dir(rag_mod.RegionASTGenerator)):
    if attr_name.startswith('_build') and 'condition' in attr_name.lower():
        print(f"  {attr_name}")

# 找 IfRegion 相关方法
print("\n=== IfRegion methods ===")
for attr_name in sorted(dir(rag_mod.RegionASTGenerator)):
    if 'ifregion' in attr_name.lower() or '_if_' in attr_name.lower():
        print(f"  {attr_name}")
