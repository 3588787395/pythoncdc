# 循环中的推导式测试
# 测试for循环中的推导
results = []
for i in range(3):
    row = [i * j for j in range(3)]
    results.append(row)
