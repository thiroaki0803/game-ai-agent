"""Enumを管理するモジュール"""

from enum import Enum


class MessageType(str, Enum):
    """websocketでやり取りする際のタイプを指定"""

    INITIALIZATION = "initialization"
    CHAT = "chat"
    ANSWER = "answer"
    RESULT = "result"


class GameType(str, Enum):
    """実行するゲームのタイプを指定"""

    TWO_TRUTH_A_LIE = "two_truth_a_lie"


class LLMType(str, Enum):
    """Agentで利用するLLMのタイプを指定"""

    OPEN_AI = "openai"
    OLLAMA = "olamma"
