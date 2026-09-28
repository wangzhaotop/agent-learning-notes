import time
from concurrent.futures import ThreadPoolExecutor

import llm_client

DRAFT = "星链公司新规定:年假可以随时休,不需要审批,休完为止。"

REVIEWERS = [
    ("事实核查", "你是事实核查员。对照公司真实制度(年假 10 天起、需 OA 审批),只列出草稿与制度不符之处。"),
    ("合规审查", "你是合规专员。指出这段话可能误导员工的地方(比如让人以为不用审批),只列问题。"),
    ("文字评审", "你是文案评审。指出这段话的表达问题(歧义、缺上下文、太武断),只列问题。"),
]


def review(name, prompt):
    t0 = time.time()
    reply, _ = llm_client.chat([
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"评审这段文字:\n{DRAFT}"}
    ])
    return name, reply, time.time() - t0


if __name__ == '__main__':
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(review, n, p) for n, p in REVIEWERS]
        results = [f.result() for f in futures]
    for name, reply, seconds in results:
        print(f"=== {name}({seconds:.1f}s)==\n{reply}\n")
    print(f"并行总耗时 {time.time() - t0}s")
    print(llm_client.bill())
