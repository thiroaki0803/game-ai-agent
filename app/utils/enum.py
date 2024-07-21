"""Enumを管理するモジュール"""

from enum import Enum


class MessageType(str, Enum):
    """websocketでやり取りする際のタイプを指定"""

    INITIALIZATION = "initialization"
    CHAT = "chat"


class GameType(str, Enum):
    """実行するゲームのタイプを指定"""

    TOW_TRUTH_A_LIE = "tow_truth_a_lie"


class LLMType(str, Enum):
    """Agentで利用するLLMのタイプを指定"""

    OPEN_AI = "openai"
    OLLAMA = "olamma"
