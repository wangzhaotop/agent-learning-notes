"""第 6 课:同一个问题,单 prompt vs 编排,放上天平比一比"""
from concurrent.futures import ThreadPoolExecutor

import llm_client
from orchestrator import plan, worker, synthesize

TOPIC = "公司要不要引入 AI 客服?"

# 方案 A:单 prompt 直接问
a, _ = llm_client.chat([
    {"role": "system", "content": "你是调研顾问。就这个主题写一份短报告:结论先行,分点陈述。"},
    {"role": "user", "content": TOPIC},
])
print(f"=== 方案 A(单 prompt)==\n{a}\n")

# 方案 B:编排(先记下账本快照,事后算差值)
before = dict(llm_client.BILL)
subs = plan(TOPIC)
with ThreadPoolExecutor(max_workers=4) as pool:
    pairs = list(pool.map(worker, subs))
b = synthesize(TOPIC, pairs)
print(f"=== 方案 B(编排)==\n{b}\n")

# 结账:方案 B 的额外花销
after = llm_client.BILL
used_in = after["in"] - before["in"]
used_out = after["out"] - before["out"]
print(f"方案 B 额外花销:{after['calls'] - before['calls']} 次调用 | "
      f"输入 {used_in} tok | 输出 {used_out} tok")
print("方案 A 只花了 1 次调用 —— 算算倍数,再诚实回答:报告质量真的值这个差价吗?")
print(llm_client.bill())
