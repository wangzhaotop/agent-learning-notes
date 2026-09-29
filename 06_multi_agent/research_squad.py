"""把本阶段所以模式组合成系统"""

import threading
from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel, Field, ValidationError

import llm_client
from orchestrator import plan, worker, synthesize

MAX_CALLS = 20  # 安全带:总 LLM 调用上限
MAX_EVAL_ROUNDS = 2  # 评审打回上限
MAX_WORKERS = 4

RUBRIC = ("评审标准:1)第一句就给出明确结论;"
          "2)正文至少分三节;"
          "3)结尾有遗留问题或下一步;"
          "4)至少用到两路子任务材料里的关键事实。")


class Verdict(BaseModel):
    passing: bool = Field(description="是否通过全部评审标准")
    issues: str = Field(description="不通过时逐条列出问题;通过时为空数组")


class BudgetExceeded(Exception):
    """总调用上限用尽一触发强制收尾"""


_real_chat = llm_client.chat


def _guarded_chat(messages, **kwargs):
    if llm_client.BILL['calls'] >= MAX_CALLS:
        raise BudgetExceeded(f"总调用上限{MAX_CALLS} 次已用完")
    return _real_chat(messages, **kwargs)


llm_client.chat = _guarded_chat

# ===== 1. 主管:拆解 + Pydantic 校验 + 自动重试 =====
FALLBACK_SUBS = ["这个主题的核心争议或目标是什么?",
                 "现状和主要痛点有哪些?",
                 "有哪些可选的改进方案?"]


def plan_with_retry(topic, retry=2):
    last_err, last_ok = None, None
    for _ in range(1 + retry):
        try:
            subs = plan(topic)
        except ValidationError as e:
            last_err = f"Schema 不合格:{e.errors()[0]['msg']}"
            continue
        last_ok = subs
        if 3 <= len(subs) <= 5:
            return subs
        last_err = f"数量不合格:{len(subs)}(要求 3-5)"
    # 跳出循环表示都不满足 进行兜底
    print(f"拆解重试耗尽:{last_err}--降级处理")
    return last_ok or FALLBACK_SUBS


# ===== 2. 工人:单路失败不炸全局 =====
def worker_safe(sub):
    try:
        return worker(sub)
    except BudgetExceeded:
        raise
    except Exception as e:
        return (sub, f"(该子任务失败:{e})")


# ===== 3. 评审 + 按意见重写 =====
def evaluate(report):
    raw, _ = llm_client.chat(
        [
            {"role": "system",
             "content": f"你是苛刻的评审员,{RUBRIC}\n 只输出JSON,字段定义:\n{Verdict.model_json_schema()}"},
            {"role": "user", "content": report}
        ],
        response_format={"type": "json_object"}
    )
    try:
        return Verdict.model_validate_json(raw)
    except ValidationError:
        return Verdict(passing=False, issues=["评审输出不合格"])


def rewrite(report, issues):
    text, _ = llm_client.chat(
        [
            {"role": "system", "content": "你是报告撰写员。按评审意见修改,保持整体结构,只输出修改后的完整报告。"},
            {"role": "user", "content": f"原报告:\n{report}\n\n评审意见:\n" + "\n".join(f"- {i}" for i in issues)},
        ]
    )
    return text


# ===== 强制收尾:不再调 LLM,有什么交什么 =====
def forced_wrap_up(pairs, reviews, report=None, reason=""):
    lines = [f"【强制收尾:{reason}】", ""]
    if report:
        lines += ["【已完成报告(未通过终审)】", report, ""]
    lines.append("【已收集材料(未经汇总,人工跟进用)】")
    lines += [f"[{s}] {r[:200]}" for s, r in pairs]
    if reviews:
        lines.append("【评审记录】")
        lines += [f"第 {i} 轮:{'通过' if v.passing else v.issues}" for i, v in reviews]
    return "\n".join(lines), reviews


def run(topic):

    reviews = []

    # 1.拆解
    subs = plan_with_retry(topic)
    print(f"主管拆出{len(subs)}个子任务:", *subs, sep="\n - ")

    # 2.并行执行
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        pairs = list(pool.map(worker_safe, subs))

    # 3.汇总
    try:
        report = synthesize(topic, pairs)
    except BudgetExceeded:
        forced_wrap_up(pairs, reviews, reason="汇总阶段预算耗尽")

    # 4.评审循环
    for round_i in range(1, MAX_EVAL_ROUNDS + 1):
        try:
            v = evaluate(report)
        except BudgetExceeded:
            return forced_wrap_up(pairs, reviews, report=report, reason="评审阶段预算耗尽")
        reviews.append((round_i, v))
        print(f"--- 评审第 {round_i} 轮:{'✅ 通过' if v.passing else v.issues} ---")
        if v.passing:
            return report, reviews
        if round_i == MAX_EVAL_ROUNDS:
            break
        try:
            report = rewrite(report, v.issues)  # 最后一轮的意见不再重写,直接变遗留问题
        except BudgetExceeded:
            return forced_wrap_up(pairs, reviews, report=report, reason="重写阶段预算耗尽")

    # 打回次数用尽:最后一次评审意见 = 遗留问题,如实附在报告上
    last_issues = reviews[-1][1].issues
    report += ("\n\n【遗留问题(评审未完全通过,需人工跟进)】\n"
               + "\n".join(f"- {i}" for i in last_issues))
    return report, reviews

if __name__ == '__main__':
    TOPIC = "评估公司班车制度的改进空间"
    run(TOPIC)
