"""第 4 课演示壳:orchestrator-workers 模式。
可复用逻辑都在 orchestrator.py —— 数字开头的文件不能被 import,
所以 04_ 前缀文件里只留演示代码,第 6 课从模块导入"""
from concurrent.futures import ThreadPoolExecutor

import llm_client
from orchestrator import plan, worker, synthesize

if __name__ == "__main__":
    topic = "公司要不要引入 AI 客服?"
    subs = plan(topic)
    print(f"主管拆出 {len(subs)} 个子任务:", *subs, sep="\n  - ")

    with ThreadPoolExecutor(max_workers=4) as pool:
        pairs = list(pool.map(worker, subs))

    print("\n=== 最终报告 ===")
    print(synthesize(topic, pairs))
    print("\n" + llm_client.bill())