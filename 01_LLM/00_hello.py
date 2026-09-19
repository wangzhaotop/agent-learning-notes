import os

from dotenv import load_dotenv
from openai import OpenAI


# 先读取目录下的.env文件 一些大模型的关键信息在里面
load_dotenv()


#1 建立客户端的连接 
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL")
)


MODEL = os.environ.get("MODEL_NAME")

resposnes = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role":"user","content":"你好 介绍下你自己"}
    ]
)

reply = resposnes.choices[0].message.content
print(reply)

