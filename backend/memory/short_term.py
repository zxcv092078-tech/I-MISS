"""
memory/short_term.py —— 短期记忆(当前对话的上下文)

设计思路:
- 用一个字典 {用户ID: [消息列表]} 存每个人的聊天历史
- "用户ID"很重要:不同用户的记忆要分开,不然A和B的聊天会串到一起
- 现在存在内存里(程序变量),重启程序就没了 —— 这是刻意的简化,
  先把"记忆怎么用"的逻辑跑通,以后想持久化,
  只需要把这个文件里的存取方式换成Redis/数据库,
  外面调用它的代码(main.py)完全不用改。这就是"分层"的好处。

为什么要限制历史长度?
大模型是按"字数"(token)收费和限制输入长度的,
如果历史无限累加,会越聊越贵、最后甚至超出模型上限报错。
所以要么限制"最近N轮",要么定期做摘要(这是长期记忆要解决的事)。
"""

# key: user_id (str)  value: 消息列表,格式跟llm.py要的一致
_conversations: dict[str, list[dict]] = {}

# 最多保留多少轮对话(1轮 = 用户1句 + 机器人1句 = 2条消息)
MAX_TURNS = 10


def get_history(user_id: str) -> list[dict]:
    """取出某个用户当前的对话历史,没有就返回空列表"""
    return _conversations.get(user_id, [])


def add_message(user_id: str, role: str, content: str):
    """
    往某个用户的历史里追加一条消息
    role: "user" 或 "assistant"
    """
    if user_id not in _conversations:
        _conversations[user_id] = []

    _conversations[user_id].append({"role": role, "content": content})

    # 超过最大轮数,把最早的对话丢掉(只留最近的)
    # MAX_TURNS * 2 是因为一轮包含user+assistant两条消息
    max_messages = MAX_TURNS * 2
    if len(_conversations[user_id]) > max_messages:
        _conversations[user_id] = _conversations[user_id][-max_messages:]


def clear_history(user_id: str):
    """清空某个用户的记忆,比如用户发/reset命令时调用"""
    _conversations[user_id] = []
