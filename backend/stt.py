import os
import base64
import tempfile
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
STT_BASE_URL = os.getenv("STT_BASE_URL", "https://api.siliconflow.cn/v1")
STT_MODEL = os.getenv("STT_MODEL", "FunAudioLLM/SenseVoiceSmall")  # ⚠️ 请对照控制台确认

client = OpenAI(api_key=API_KEY, base_url=STT_BASE_URL)


def transcribe(audio_base64: str) -> str:
    """
    输入:录音的base64编码
    输出:识别出的文字
    """
    audio_bytes = base64.b64decode(audio_base64)

    # OpenAI格式的语音识别接口要求传一个文件对象,不能直接传bytes,
    # 所以先落地成临时文件再传进去
    with tempfile.NamedTemporaryFile(suffix=".m4a", delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        with open(tmp.name, "rb") as f:
            result = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=f,
            )
    return result.text