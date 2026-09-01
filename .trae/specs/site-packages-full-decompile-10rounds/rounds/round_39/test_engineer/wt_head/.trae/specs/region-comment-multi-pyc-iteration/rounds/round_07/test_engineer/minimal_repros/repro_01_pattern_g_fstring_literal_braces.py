# DEFECT-REPRO Pattern G: f-string 字面常量部分含 { } 未转义为 {{ }}
# 期望：反编译产物 f'...{{}}...{DEFAULT_PORT!s}...'；缺陷时输出 { } 导致语法错误
DEFAULT_PORT = 8080
s = f'port={DEFAULT_PORT!s}, cfg={{}}, done\n'
print(s)
# DEFECT-REPRO
