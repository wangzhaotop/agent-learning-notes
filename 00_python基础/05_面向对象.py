from abc import ABC, abstractmethod
from dataclasses import dataclass


# ========== 1. 类与封装:__init__ / self / 访问控制 ==========
class BaseTool(ABC):
    """所有工具的父类——阶段 4 手册里的工具注册器就是这套套路"""

    description = "我是工具类"

    def __init__(self):
        self._calls = 0

    @property
    def calls(self):
        return self._calls

    @abstractmethod
    def run(self, ars: str) -> str:
        """抽象方法:子类不实现,实例化直接报错——Python 版的 abstract / interface"""

    def invoke(self, arg: str) -> str:
        """模板方法:计数、日志等公共逻辑封在父类,子类只管 run——这就是封装"""
        self._calls += 1
        print(f"[{self.__class__.__name__}]第{self.calls}次被调用了")
        return self.run(arg)


class EchoTool(BaseTool):

    def run(self, ars: str) -> str:
        return f"echo:{ars}"


class UpperTool(BaseTool):
    def run(self, args: str) -> str:
        return args.upper()


class ReadFileTool(BaseTool):
    def __init__(self, encoding: str = "utf-8"):
        super().__init__()  # 不写这行,父类 __init__ 不会自动执行,_calls 就没初始化
        self.__encoding = encoding  # __双下划线:被改写成 _ReadFileTool__encoding,外部摸不到

    def run(self, args: str) -> str:
        with open(args, encoding=self.__encoding) as f:  # open 的细节第 9 课讲
            return f.read()


# ========== 2. 多态:鸭子类型 ==========
# Java:先定 interface Tool,各实现类 implements;
# Python:不看血统看行为——只要"有 run 方法",就能塞进同一个列表循环调用
tools = [EchoTool(), UpperTool()]  # ReadFileTool 要读真文件,第 9 课学完再回头调它
for t in tools:
    print(t.invoke("hello"))  # 同一句 invoke,各自落到自己的 run(动态绑定)

print(tools[0].calls, tools[1].calls)


# ========== 3. dataclass:一行顶 Java 的 record / Lombok @Data ==========
@dataclass
class AgentConfig:
    model: str
    max_steps: int = 5
    temperature: float = 0.7

    @classmethod
    def cheap(cls):            # @classmethod = Java 的静态工厂方法,cls 就是本类
        return cls(model="deepseek-flash",temperature=0.2)



cfg = AgentConfig(model="glm-4")
print(cfg)                               # 自动生成 __repr__,不用手写 toString
print(cfg == AgentConfig(model="glm-4")) # 自动生成 __eq__,按字段比——True
print(AgentConfig.cheap())
