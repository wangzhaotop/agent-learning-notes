import llm_client

RAW = """周三 修了个登录的bug 改了两行
周四 开会讨论知识库项目 说下周要出方案
周五 帮新同事配环境 搞了一下午
本周 还看了点MCP的资料"""

STEPS = [
    ("整理员", "你是周报整理员。把碎片流水账整理成 3-5 条要点,每条一行,只输出要点。"),
    ("撰写员", "你是周报撰写员。把要点扩写成正式周报,分「本周工作」「下周计划」两节,书面语。"),
    ("精简员", "你是精简员。把周报压缩到 150 字以内,保留全部关键信息,只输出周报。"),
]

text = RAW
for name, prompt in STEPS:
    text, _ = llm_client.chat([
        {"role": "system", "content": prompt},
        {"role": "user", "content": text}
    ])
    print(f"=== {name} ===\n{text}\n")

print(llm_client.bill())
