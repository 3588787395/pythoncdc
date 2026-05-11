# Test f-string formatting
v = "20240101"
temp_time = f"{v[0:4]}-{v[4:6]}-{v[6:8]} {v[8:10]}:{v[10:12]}:{v[12:14]}"
print(temp_time)