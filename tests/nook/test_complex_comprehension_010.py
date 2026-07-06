# 复杂推导式测试
# 嵌套列表推导式
nested_list = [[i * j for j in range(3)] for i in range(4)]

# 带条件的字典推导式
dict_comp = {k: v for k, v in [(1, 'a'), (2, 'b'), (3, 'c')] if k > 1}

# 复杂集合推导式
set_comp = {x * y for x in range(5) for y in range(5) if x != y}

# 生成器推导式
sum_of_squares = sum(x ** 2 for x in range(100))

# 嵌套推导式函数
def matrix_transpose(matrix):
    return [[row[i] for row in matrix] for i in range(len(matrix[0]))]
