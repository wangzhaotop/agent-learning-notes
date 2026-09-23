import functools
import random
import time


# ========== 1. 高阶函数:函数和 int、str 一样,是个可以传来传去的值 ==========
def apply(func, x):  # 函数当参数——Java 8 的 Function<T, R>
    return func(x)


print(apply(str.upper, "abc"))
print(apply(lambda s: s * 2, "ab"))

words = ["banana", "Fig", "apple"]
print(sorted(words))
print(sorted(words, key=str.lower))
print(sorted(words, key=len, reverse=True))


# ========== 2. 闭包:内层函数"记住"外层函数的变量 ==========
def make_counter():
    count = 0

    def inc(step: int = 1) -> int:
        nonlocal count
        count += step
        return count

    return inc


counter = make_counter()
print(counter(), counter(), counter(10))
print(counter.__closure__)


# ========== 3. 装饰器 = 接收函数、返回新函数的高阶函数 + @ 语法糖 ==========
def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        print(f"{func.__name__} 耗时 {time.perf_counter() - t0:.4f}s")
        return result

    return wrapper


@timed
def slow_sum(n: int) -> int:
    """求 0..n-1 的和"""
    return sum(range(n))


print(slow_sum(10_000_000))
print(slow_sum.__name__)  # slow_sum,不是 wrapper——wraps 的功劳


# ========== 4. 带参数的装饰器:再包一层,一共三层 ==========
def retry(times: int):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_err = None
            for i in range(1,1 + times):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_err = e
                    print(f"  第 {i}/{times} 次失败:{e}")
            raise RuntimeError(f"重试 {times} 次仍失败") from last_err

        return wrapper

    return decorator


@retry(times=3)
def flaky_api()->str:
    """模拟一个成功率约 30% 的接口"""
    if random.random() < 0.7:
        raise ConnectionError("网络抖动")
    return "调用成功"

try:
    print(flaky_api())
except RuntimeError as e:
    print(f"最终失败:{e}")

