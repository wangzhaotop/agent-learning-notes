"""路由决策模型"""

from pydantic import BaseModel, Field, ValidationError

import llm_client


class Route(BaseModel):
    category: str = Field(description="必须取值:leave(考勤假期)/it(IT问题)/dev(研发规范)/other(其他)")
    reason: str = Field(description="一句话判断依据")


ROUTES = {
    "leave": "你是考勤假期专员,精通公司年假病假调休制度,只回答考勤假期问题,简洁。",
    "it": "你是 IT 支持专员,精通公司 VPN/账号/设备流程,只回答 IT 问题,简洁。",
    "dev": "你是研发规范专员,精通公司分支/评审/发布/值班规范,只回答研发规范问题,简洁。",
    "other": "你是通用助手。这个问题不在你的专长范围,诚实说明不确定,禁止编造。",
}


def route(question):
    """轻量分类:一次小调用+检验失败兜底"""
    raw, _ = llm_client.chat(
        [
            {"role": "system", "content": "你是问题分类器。只输出一个 JSON 对象,字段定义:\n"
                                          f"{Route.model_json_schema()}"
             },
            {
                "role": "user", "content": question
            }
        ],
        response_format={"type": "json_object"}
    )
    try:
        return Route.model_validate_json(raw)
    except ValidationError:
        return Route(category="other", reason="分类失败,走兜底")


def answer(question):
    r = route(question)
    print(f"返回的格式:{r}")
    print(f"(路由->{r.category} | {r.reason})")
    reply, _ = llm_client.chat([
        {"role": "system", "content": ROUTES[r.category]},
        {"role": "user", "content": question},
    ])
    return reply


if __name__ == '__main__':
    for q in ["年假最多能攒几天?", "VPN 连不上怎么办?",
              "MR 超过 3 天没处理会怎样?", "今天天气怎么样?"]:
        print(f"\n你:{q}")
        print(f"AI:{answer(q)}")
    print("\n" + llm_client.bill())
