"""毕业考参考实现 · 文件统计工具包

对一个 .py 文件做统计,专题 5-9 五课考点一次合练:
- 第 5 课:BaseStat 抽象基类 + 两个子类,多态地塞进同一个列表
- 第 6 课:@repeat(times=3) 带参数装饰器(三层套娃)
- 第 7 课:自定义异常 StatsError,工具边界全捕获,程序不崩
- 第 8 课:read_lines 生成器逐行产出,不把文件整个读进内存
- 第 9 课:with open 读文件 + json.dump 写结果

用法:python 10_final.py [目标文件]      # 缺省统计 08_迭代器和生成器.py
"""

import functools
import json
import sys
import time
from abc import ABC, abstractmethod

TARGET = sys.argv[1] if len(sys.argv) > 1 else "08_迭代器和生成器.py"
RESULT_FILE = "result.json"


# ========== 第 7 课:自定义异常 ==========
class StatsError(Exception):
    """统计失败(如空文件)——自己起名,语义比 ValueError 这类自带异常更明确"""


# ========== 第 8+9 课:逐行生成器 ==========
def read_lines(path: str):
    """生成器:调用时一行都不读,第一次 next() 才打开文件——10GB 也不撑爆内存"""
    with open(path, encoding="utf-8") as f:
        for line in f:              # 文件对象本身就是迭代器:一行一行读
            yield line.rstrip("\n")


# ========== 第 5 课:抽象基类 + 多态 ==========
class BaseStat(ABC):
    name = "base"                        # 类属性:子类各自覆盖

    def __init__(self):
        self._calls = 0                  # _单下划线:受保护的君子协定

    @property
    def calls(self) -> int:              # @property = Java 的 getter
        return self._calls

    @abstractmethod
    def run(self, lines) -> dict:
        """子类必须实现:接收"行的可迭代对象",返回统计结果 dict"""

    def invoke(self, lines) -> dict:     # 模板方法:计数、日志等公共逻辑封在父类
        self._calls += 1
        print(f"[{self.name}] 第 {self._calls} 次统计开始")
        result = self.run(lines)
        print(f"[{self.name}] 统计完成,累计被调用 {self.calls} 次")
        return result


class WordCountStat(BaseStat):
    """词频 top 3:小写 + 按空白切分,不管标点"""

    name = "word_count"

    def run(self, lines) -> dict:
        counts = {}
        for line in lines:
            for word in line.lower().split():
                counts[word] = counts.get(word, 0) + 1   # EAFP 之外的正路:dict.get 带默认值
        top3 = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:3]
        return {
            "distinct_words": len(counts),
            "top3": [{"word": w, "count": c} for w, c in top3],
        }


class LongestLineStat(BaseStat):
    """最长的一行及其长度;空文件主动抛 StatsError"""

    name = "longest_line"

    def run(self, lines) -> dict:
        longest = None
        for line in lines:
            if longest is None or len(line) > len(longest):
                longest = line
        if longest is None:              # 一次 for 都没进来 = 空文件
            raise StatsError("空文件:一行都没有")
        return {"length": len(longest), "line": longest}


# ========== 第 6 课:带参数的装饰器,三层套娃 ==========
def repeat(times: int):                          # 第 1 层:收装饰器自己的参数
    def decorator(func):                         # 第 2 层:收函数(普通装饰器本体)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):            # 第 3 层:真正干活
            result = None
            for i in range(1, times + 1):
                t0 = time.perf_counter()
                result = func(*args, **kwargs)
                print(f">>> 第 {i}/{times} 遍耗时 {time.perf_counter() - t0:.4f}s")
            return result
        return wrapper
    return decorator


# 两个不同的子类塞进同一个列表,循环调用同一个 invoke——多态(第 5 课)
STATS = [WordCountStat(), LongestLineStat()]


@repeat(times=3)
def run_all():
    results = {}
    for stat in STATS:
        try:
            # 生成器是一次性的(第 8 课):每个工具各发一只"新手"。
            # 把同一个生成器喂给两个工具,第二个只能拿到空。
            results[stat.name] = stat.invoke(read_lines(TARGET))
        except StatsError as e:                  # 空文件:友好提示,不崩
            print(f"  [{stat.name}] 统计失败:{e}")
            results[stat.name] = {"error": str(e)}
        except FileNotFoundError:                # 文件不存在:友好提示,不崩
            print(f"  [{stat.name}] 文件不存在:{TARGET}")
            results[stat.name] = {"error": f"文件不存在:{TARGET}"}

    # 第 9 课:结果落盘,中文原样存
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"结果已写入 {RESULT_FILE}")
    return results


if __name__ == "__main__":
    run_all()
