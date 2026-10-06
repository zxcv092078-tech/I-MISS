"""
server.py —— 后端服务入口

跟之前Telegram版本的区别:
之前是"Telegram平台推消息过来,我们处理完发回Telegram",
现在是"手机App发HTTP请求过来,我们处理完把结果返回给App"。
处理逻辑(调大模型、读写记忆)完全没变,只是换了个"收发消息"的方式。

FastAPI 是Python写HTTP接口最常用的框架,
它会帮你监听一个端口(默认8000),
App 通过网络请求这个地址,就能拿到回复。
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm import chat, chat_with_image
from tts import synthesize
from stt import transcribe
from persona import SYSTEM_PROMPT
from memory.short_term import get_history, add_message, clear_history

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS:允许手机App(跑在不同的"来源")访问这个后端接口
# 因为是私人App不对外公开,这里先设成允许所有来源,图个方便;
# 如果以后要挂公网,建议改成只允许你App的具体域名
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """
    App发过来的请求体格式,FastAPI会自动校验:
    如果App发的数据格式不对(比如少了message字段),会自动报错提示,
    不用你自己手写校验逻辑。
    """
    user_id: str      # 用来区分不同用户的记忆,私人app固定传一个值就行,比如"me"
    message: str       # 用户发的这句话
    image_base64: str | None = None   # 可选:拍照/选图后传来的base64图片数据(不带data:前缀)
    image_mime: str | None = "image/jpeg"


class ChatResponse(BaseModel):
    reply: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    App每次发消息,会调用这个接口: POST /chat
    请求体例: {"user_id": "me", "message": "在干嘛呀"}
    返回例:   {"reply": "在想你呀,怎么样,想我了没"}
    """
    logger.info(f"[{req.user_id}] 收到: {req.message}")

    history = get_history(req.user_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": req.message},
    ]

    reply_text = (
        chat_with_image(messages, req.image_base64, req.image_mime)
        if req.image_base64
        else chat(messages)
    )
    logger.info(f"[{req.user_id}] 回复: {reply_text}")

    add_message(req.user_id, "user", req.message)
    add_message(req.user_id, "assistant", reply_text)

    return ChatResponse(reply=reply_text)


class TTSRequest(BaseModel):
    text: str


class TTSResponse(BaseModel):
    audio_base64: str


class VoiceChatRequest(BaseModel):
    user_id: str
    audio_base64: str  # 用户录的语音,base64编码


class VoiceChatResponse(BaseModel):
    user_text: str       # 识别出用户说了什么(用于聊天气泡显示)
    reply_text: str       # 她的文字回复
    reply_audio_base64: str  # 她的语音回复


@app.post("/voice-chat", response_model=VoiceChatResponse)
async def voice_chat_endpoint(req: VoiceChatRequest):
    """
    微信式语音消息的完整流程:
    1. 语音转文字(STT)
    2. 文字走正常的对话逻辑(带记忆)
    3. 回复文字转语音(TTS)
    一次请求返回所有结果,App拿到后既能显示文字气泡,也能播放语音。
    """
    logger.info(f"[{req.user_id}] 收到语音消息,开始识别...")
    user_text = transcribe(req.audio_base64)
    logger.info(f"[{req.user_id}] 识别结果: {user_text}")

    history = get_history(req.user_id)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
        {"role": "user", "content": user_text},
    ]
    reply_text = chat(messages)

    add_message(req.user_id, "user", user_text)
    add_message(req.user_id, "assistant", reply_text)

    reply_audio = synthesize(reply_text)

    return VoiceChatResponse(
        user_text=user_text,
        reply_text=reply_text,
        reply_audio_base64=reply_audio,
    )


@app.post("/tts", response_model=TTSResponse)
async def tts_endpoint(req: TTSRequest):
    """
    App拿到文字回复之后,可以再单独调这个接口把文字转成语音。
    分开成两个接口(而不是/chat直接返回语音)是为了让流程更灵活:
    App可以先显示文字气泡,语音生成慢一点也不影响文字先出来。
    """
    logger.info(f"[TTS] 合成: {req.text[:20]}...")
    audio_b64 = synthesize(req.text)
    return TTSResponse(audio_base64=audio_b64)


@app.post("/reset")
async def reset_endpoint(user_id: str):
    """清空某个用户的记忆,App里可以做个"重置对话"按钮调用这个"""
    clear_history(user_id)
    return {"status": "ok"}


@app.get("/health")
async def health_check():
    """简单的存活检测接口,方便App启动时先探测后端是否在线"""
    return {"status": "running"}


# 启动方式(终端里跑):
#   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
#
# --host 0.0.0.0 很重要:表示监听所有网卡,
# 这样手机(跟电脑在同一个WiFi下)才能连到电脑上跑的这个服务。
# 如果只写默认的127.0.0.1,只有电脑自己能访问,手机连不上。