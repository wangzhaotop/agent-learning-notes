import sys


# ========== 1. for 循环的本质:iter() + next() + StopIteration ==========
nums = [10, 20, 30]

it = iter(nums)                  # 1) for 先向列表要一个迭代器:nums.__iter__()
while True:
    try:
        n = next(it)             # 2) 每轮调 next(it) 拿下一个:it.__next__()
        print(n)
    except StopIteration:        # 3) 拿完了,迭代器抛 StopIteration,for 悄悄接住并结束
        break
print("--- for 的真身就是这样 ---")


# ========== 2. 可迭代 Iterable vs 迭代器 Iterator(面试第一高频) ==========
# Iterable(可迭代):实现了 __iter__      —— 能被 for,能被 iter()
# Iterator(迭代器):实现了 __iter__ + __next__ —— 能被 next() 一个一个吐
nums2 = [1, 2, 3]
print(hasattr(nums2, "__iter__"), hasattr(nums2, "__next__"))   # True False → 列表只是"可迭代"
it2 = iter(nums2)
print(hasattr(it2, "__iter__"), hasattr(it2, "__next__"))       # True True → 这才是迭代器


# 记忆:list 是一整箱书,迭代器是从箱里取书的那只手
# 关系:iter(可迭代) → 迭代器;迭代器一定是可迭代的,反之不成立

# 迭代器是一次性的(面试常见坑):
it3 = iter([1, 2, 3])
print(list(it3))                 # [1, 2, 3]
print(list(it3))                 # [] —— 耗尽了!而 list(nums2) 随时能再来一遍

# ========== 3. 生成器:自己造迭代器最省事的写法 ==========
def countdown(n):
    print("开始")
    while n > 0:
        yield n                  # 在这里"暂停",把 n 交出去;下次 next 从这一行继续
        n -= 1
    print("结束")

print("调用 countdown(3):函数体一行都没执行(惰性!)")
gen = countdown(3)
print(next(gen))                 # 这一瞬才打印"开始",吐出 3
print(next(gen))                 # 从 yield 处继续,吐出 2
print(next(gen))                 # 1
# print(next(gen))               # 再要:先打印"结束",然后 StopIteration

for x in countdown(3):           # for 会替你接住 StopIteration
    print("for:", x)

# ========== 4. 生成器表达式 vs 列表推导:() 惰性,[] 立即 ==========
squares_list = [x * x for x in range(1_000_000)]   # 立刻全算完,整块占内存
squares_gen = (x * x for x in range(1_000_000))    # 只是个"公式",几乎不占内存
print(sys.getsizeof(squares_list))                 # 八百多万字节
print(sys.getsizeof(squares_gen))                  # 一百字节上下
print(sum(x * x for x in range(100)))              # 边产生边消费的场景,天生一对


# ========== 5. 实战:无限序列 / 大文件流式处理 / yield from ==========
def fib():
    a, b = 0, 1
    while True:                  # 无限!但没人 next 它就不算,零压力
        yield a
        a, b = b, a + b


f = fib()
print([next(f) for _ in range(10)])


def read_large(path):
    with open(path, encoding="utf-8") as fp:   # 文件操作第 9 课讲
        for line in fp:          # 文件对象本身就是迭代器:一行一行读,10GB 也不撑爆内存
            yield line.strip()


def chain(a, b):
    yield from a                 # 委托:把另一个可迭代对象整个"接进来"
    yield from b


print(list(chain([1, 2], "ab"))) # [1, 2, 'a', 'b']


# ========== 6. 让自己的类也能 for(面试会问) ==========
class Countdown:
    def __init__(self, n):
        self.n = n

    def __iter__(self):          # for 每次开始,都来这要一个"新的手"
        return iter(range(self.n, 0, -1))
        # 也可以用生成器实现:yield from range(self.n, 0, -1)


print(list(Countdown(5)))        # [5, 4, 3, 2, 1]