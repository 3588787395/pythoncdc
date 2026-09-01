# DEFECT-REPRO Pattern G: 字面花括号紧邻 FormattedValue 前后
name = 'x'
s = f'{{start}}{name!s}{{end}}\n'
print(s)
# DEFECT-REPRO
