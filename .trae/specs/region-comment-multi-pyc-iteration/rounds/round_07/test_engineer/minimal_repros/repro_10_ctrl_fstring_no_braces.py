# NO-DEFECT 控制：f-string 仅含 FormattedValue，无字面花括号（Pattern G 不触发）
DEFAULT_PORT = 8080
s = f'port={DEFAULT_PORT!s}, done\n'
print(s)
# NO-DEFECT
