import json
from pathlib import Path


# ========== 1. 写:永远 with open,永远 encoding="utf-8" ==========
with open("demo.txt", "w", encoding="utf-8") as f:      # w = 覆盖写(没有就创建)
    f.write("第一行\n")
    f.writelines(["第二行\n", "第三行\n"])               # writelines 不会帮你加换行

with open("demo.txt", "a", encoding="utf-8") as f:      # a = 追加(文件不存在也会创建)
    f.write("第四行(追加的)\n")


# ========== 2. 读的三种姿势 ==========
with open("demo.txt", encoding="utf-8") as f:
    whole = f.read()                 # 姿势 1:整个读成一个大字符串(小文件用)
print(whole)

with open("demo.txt", encoding="utf-8") as f:
    lines = f.readlines()            # 姿势 2:读成"行列表"(文件大会爆内存,慎用)
print(lines)

with open("demo.txt", encoding="utf-8") as f:
    for line in f:                   # 姿势 3(最推荐):文件对象是迭代器,一行一行读——第 8 课!
        print(repr(line))            # 每行末尾带着 \n,处理前常要 strip()


# ========== 3. JSON:阶段 1 会话存盘、阶段 3 向量库持久化,核心就这两段 ==========
data = {"model": "glm-4", "history": [{"role": "user", "content": "你好"}]}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)   # ensure_ascii=False:中文原样存,不转 \uXXXX

with open("data.json", encoding="utf-8") as f:
    loaded = json.load(f)

print(loaded["model"], loaded["history"][0]["content"])


# ========== 4. pathlib:现代路径写法,会用即可 ==========
p = Path("demo.txt")
print(p.read_text(encoding="utf-8").splitlines()[0])   # 小文件一步读完

q = Path(".") / "sub" / "data.json"                     # 用 / 拼路径,自动跨平台
print(q)

print(sorted(x.name for x in Path(".").glob("*.json"))) # 列当前目录的 json 文件名