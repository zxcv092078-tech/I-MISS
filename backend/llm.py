"""
llm.py —— 封装"调用大模型"这一件事

为什么单独拆一个文件?
因为以后你可能会换模型(GPT换成Claude,换成国产模型),
只要这个文件里的 chat() 函数"输入messages,返回文字"这个接口不变,
外面 main.py 完全不用动。这是"解耦"的思路,以后维护会轻松很多。
"""

import os
from dotenv import load_dotenv
from openai import OpenAI  # 这里用OpenAI SDK做示例,因为很多国产模型也兼容这套接口

# 加载同目录下的 .env 文件里的环境变量。
# 这样在VSCode里直接点"运行"/调试,也能读到密钥,
# 不用依赖终端里手动 export 过(那种方式VSCode的运行按钮读不到)。
load_dotenv()

# 从环境变量读取密钥,不要把密钥写死在代码里(会泄露/被盗刷)
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("LLM_MODEL", "gpt-4o-mini")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def chat(messages: list[dict]) -> str:
    """
    messages 是一个列表,格式类似:
    [
        {"role": "system", "content": "你是一个..."},
        {"role": "user", "content": "你好"},
    ]
    这个结构是行业通用格式(OpenAI定的,现在大家基本都跟这个)。

    返回值:模型生成的纯文字回复
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.8,  # 越高越"随性",越低越"严谨",陪伴类机器人建议0.7~0.9
        max_tokens=500,
    )
    return response.choices[0].message.content


def chat_with_image(messages: list[dict], image_base64: str, image_mime: str = "image/jpeg") -> str:
    """
    跟chat()类似,但最后一条用户消息会附带一张图片。
    image_base64: 图片的base64编码字符串(不带data:前缀那部分)
    image_mime: 图片格式,比如 "image/jpeg" 或 "image/png"

    这里用的是OpenAI通用的"多模态消息"格式:
    content不再是纯文字字符串,而是一个数组,里面混着文字块和图片块。
    支持视觉理解的模型(比如Kimi-K2.6)才能看懂这种格式,
    不支持视觉的模型会报错或者直接忽略图片。
    """
    # 把最后一条user消息改造成带图片的格式
    messages = messages.copy()
    last_msg = messages[-1]
    messages[-1] = {
        "role": "user",
        "content": [
            {"type": "text", "text": last_msg["content"]},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{image_mime};base64,{image_base64}"},
            },
        ],
    }

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.8,
        max_tokens=500,
    )
    return response.choices[0].message.content


# ---- 换成其他模型API时怎么改 ----
# 如果用国产模型(比如通义千问、Kimi、DeepSeek),
# 它们大多也提供"兼容OpenAI格式"的接口,
# 你只需要改 LLM_BASE_URL 和 LLM_MODEL 这两个环境变量,代码不用动。
#
# 如果用Anthropic的Claude原生SDK(不走兼容层),
# 需要把上面client换成 anthropic.Anthropic(),
# 并把 messages 里的 system 单独拎出来传,
# 因为Claude原生API的system是单独参数,不放在messages列表里。
# 需要的话我可以单独给你写一版。
