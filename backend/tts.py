"""
tts.py —— 文字转语音(她的"声音")

⚠️ 重要提醒:下面的接口地址和模型名是按SiliconFlow平台的通用格式写的,
但我没能找到100%可靠的官方文档确认细节(网上搜到的很多是转载的低质量内容)。
在正式用之前,请你:
1. 登录 cloud.siliconflow.cn
2. 左侧菜单找"语音合成",进去看真实的接口示例代码(平台通常会自动生成一段可以直接复制的Python代码)
3. 对照下面这个函数,把URL和model名字改成平台实际给出的那个

这是"占位实现"——用平台自带的默认音色先让语音功能跑起来,
等你后面找到/训练好专属声音克隆模型(比如GPT-SoVITS、CosyVoice),
只需要改这一个文件里的调用方式,其他代码(server.py、App里的播放逻辑)完全不用动。
"""

import os
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

TTS_API_KEY = os.getenv("LLM_API_KEY")  # 先复用同一个SiliconFlow的key
TTS_BASE_URL = os.getenv("TTS_BASE_URL", "https://api.siliconflow.cn/v1/audio/speech")
TTS_MODEL = os.getenv("TTS_MODEL", "MOSS-TTSD-v0.5") # ⚠️ 请对照控制台确认这个模型名是否正确
TTS_VOICE = os.getenv("TTS_VOICE", "anna")  # 默认音色,平台通常有几个内置音色可选


def synthesize(text: str) -> str:
    """
    把文字转成语音,返回base64编码的音频数据(方便直接塞进JSON传给App)。
    如果这里报错,大概率是URL/model名字跟平台实际的对不上,去控制台核对一下。
    """
    response = requests.post(
        TTS_BASE_URL,
        headers={
            "Authorization": f"Bearer {TTS_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": TTS_MODEL,
            "input": text,
            "voice": TTS_VOICE,
            "response_format": "mp3",
        },
        timeout=30,
    )
    response.raise_for_status()  # 请求失败时会在这里抛出异常,方便看到具体错误
    audio_bytes = response.content
    return base64.b64encode(audio_bytes).decode("utf-8")
